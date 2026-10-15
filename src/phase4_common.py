"""Fase 4 - utilidades comunes: splits, codificaciones de entrada y entrenamiento de MLPs.

Objetivo de la fase: minimizar la Log Loss (entropia cruzada binaria) manteniendo el
mismo protocolo del proyecto: ajuste en Train, seleccion en Validacion, Test solo al final.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import QuantileTransformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from preprocess import Preprocessor

P4 = C.ARTIFACTS / "phase4"
P4.mkdir(parents=True, exist_ok=True)


def load_raw():
    """Dataset + indices de Train/Val/Test identicos a los de splits.npz."""
    df = pd.read_csv(C.DATA_CSV, encoding="utf-8-sig")
    y = df[C.TARGET].to_numpy("float32")
    idx = np.arange(len(df))
    tr, tmp = train_test_split(
        idx, test_size=C.VAL_FRAC + C.TEST_FRAC, stratify=y, random_state=C.SPLIT_SEED
    )
    va, te = train_test_split(
        tmp,
        test_size=C.TEST_FRAC / (C.VAL_FRAC + C.TEST_FRAC),
        stratify=y[tmp],
        random_state=C.SPLIT_SEED,
    )
    assert (te == np.load(C.ARTIFACTS / "splits.npz")["idx_test"]).all()
    return df, y, tr, va, te


def metrics(y, p):
    p = np.clip(p, 1e-7, 1 - 1e-7)
    yp = (p >= 0.5).astype(int)
    return {
        "LogLoss": log_loss(y, p),
        "AUC": roc_auc_score(y, p),
        "PR_AUC": average_precision_score(y, p),
        "Brier": brier_score_loss(y, p),
        "Accuracy": accuracy_score(y, yp),
        "F1": f1_score(y, yp),
    }


# ---------------------------------------------------------------------------
# Codificaciones de entrada (todas ajustadas SOLO con Train)
# ---------------------------------------------------------------------------
class Encoder:
    """kind:
    - "base": pipeline original del proyecto (clip p1-p99, log1p, mediana, StandardScaler).
    - "qt":   numericas -> QuantileTransformer(normal); flags y one-hot igual.
    - "ple":  Piecewise Linear Encoding (Gorishniy et al., 2022) de cada numerica en
              n_bins tramos por cuantiles + la numerica estandarizada original.
    """

    def __init__(self, kind="base", n_bins=16):
        self.kind, self.n_bins = kind, n_bins

    def fit(self, df_tr):
        self.pre = Preprocessor().fit(df_tr)
        clean = self.pre._clean(df_tr)
        self.base = [c for c in self.pre.num_cols if not c.endswith("_nan")]
        self.flags = [c for c in self.pre.num_cols if c.endswith("_nan")]
        num = self._num(clean)
        if self.kind == "qt":
            self.qt = QuantileTransformer(
                n_quantiles=1000, output_distribution="normal", subsample=10**9, random_state=0
            ).fit(num)
        if self.kind == "ple":
            self.edges = []
            for j in range(num.shape[1]):
                e = np.unique(np.quantile(num[:, j], np.linspace(0, 1, self.n_bins + 1)))
                self.edges.append(e)
        return self

    def _num(self, clean):
        """Numericas con clip + log del pipeline original y mediana, sin escalar."""
        d = clean.copy()
        d[self.base] = d[self.base].clip(self.pre.lo, self.pre.hi, axis=1)
        for c in C.SKEW_COLS:
            d[c] = np.log1p(d[c].clip(lower=0))
        for c in C.SIGNED_LOG_COLS:
            d[c] = np.sign(d[c]) * np.log1p(d[c].abs())
        d[self.base] = d[self.base].fillna(self.pre.median)
        return d[self.base].to_numpy(float)

    def transform(self, df):
        X0 = self.pre.transform(df)  # 44 columnas originales estandarizadas
        if self.kind == "base":
            return X0
        clean = self.pre._clean(df)
        num = self._num(clean)
        if self.kind == "qt":
            nb = len(self.base)
            Xq = self.qt.transform(num).astype("float32")
            return np.hstack([Xq, X0[:, nb:]]).astype("float32")
        if self.kind == "ple":
            blocks = [X0]
            self.slices, start = [], X0.shape[1]  # columnas PLE de cada variable
            for j, e in enumerate(self.edges):
                if len(e) <= 2:  # variable casi constante / binaria
                    continue
                lo, hi = e[:-1], e[1:]
                enc = np.clip((num[:, [j]] - lo) / (hi - lo), 0.0, 1.0)
                blocks.append(enc)
                self.slices.append((start, start + enc.shape[1]))
                start += enc.shape[1]
            return np.hstack(blocks).astype("float32")
        raise ValueError(self.kind)


_CACHE = {}


def get_data(kind="base", n_bins=16):
    key = (kind, n_bins)
    if key not in _CACHE:
        df, y, tr, va, te = load_raw()
        enc = Encoder(kind, n_bins).fit(df.iloc[tr])
        X = enc.transform(df)
        _CACHE[key] = dict(
            X_tr=X[tr], y_tr=y[tr], X_va=X[va], y_va=y[va], X_te=X[te], y_te=y[te], enc=enc
        )
    return _CACHE[key]


# ---------------------------------------------------------------------------
# MLP configurable
# ---------------------------------------------------------------------------
def train_mlp(data, cfg, seed, verbose=0):
    """Entrena un MLP con parada temprana sobre la BCE pura de validacion.

    Se usa weight decay desacoplado (AdamW) en lugar de L2 en la funcion de perdida para
    que `val_loss` sea exactamente la Log Loss (en Fases 2-3 la val_loss incluia el
    termino L2 y la parada temprana no optimizaba la metrica real).
    Devuelve (p_val, p_test, mejor_epoca).
    """
    import tensorflow as tf
    from tensorflow import keras

    keras.utils.set_random_seed(seed)
    act = cfg.get("act", "relu")
    hidden = cfg.get("hidden", (64, 32, 16))
    drop = cfg.get("dropout", 0.15)
    n_in = data["X_tr"].shape[1]

    inp = keras.Input(shape=(n_in,))
    x = inp
    if cfg.get("emb_dim"):
        # Embedding no lineal por variable: PLE_j -> Dense(emb_dim, relu) (MLP-PLE de Gorishniy)
        n0 = data["enc"].slices[0][0]
        parts = [inp[:, :n0]]
        for a, b in data["enc"].slices:
            sl = inp[:, a:b]
            parts.append(keras.layers.Dense(cfg["emb_dim"], activation="relu")(sl))
        x = keras.layers.Concatenate()(parts)
    if cfg.get("input_dropout", 0) > 0:
        x = keras.layers.Dropout(cfg["input_dropout"])(x)
    for i, u in enumerate(hidden):
        x = keras.layers.Dense(u, kernel_initializer="he_normal")(x)
        if cfg.get("batchnorm"):
            x = keras.layers.BatchNormalization()(x)
        x = keras.layers.Activation(act)(x)
        if drop > 0 and (i < len(hidden) - 1 or cfg.get("drop_last", False)):
            x = keras.layers.Dropout(drop)(x)
    if cfg.get("cross", 0):
        # Rama Cross (DCN-v2, Wang et al. 2021) sobre las 44 variables base estandarizadas:
        # x_{l+1} = x0 * (W x_l + b) + x_l  -> interacciones de a pares explicitas.
        x0 = inp[:, :44]
        xc = x0
        for _ in range(cfg["cross"]):
            w = keras.layers.Dense(44)(xc)
            xc = keras.layers.Add()([keras.layers.Multiply()([x0, w]), xc])
        if cfg.get("cross_dropout", 0) > 0:
            xc = keras.layers.Dropout(cfg["cross_dropout"])(xc)
        x = keras.layers.Concatenate()([x, xc])
    out = keras.layers.Dense(1, activation="sigmoid")(x)
    model = keras.Model(inp, out)

    lr = cfg.get("lr", 5e-4)
    epochs = cfg.get("epochs", 200)
    bs = cfg.get("batch", 128)
    wd = cfg.get("wd", 0.0)
    opt = keras.optimizers.AdamW(learning_rate=lr, weight_decay=wd) if wd else keras.optimizers.Adam(lr)
    # steps_per_execution agrupa pasos en una sola llamada al grafo (mismo algoritmo, menos overhead)
    model.compile(optimizer=opt, loss=keras.losses.BinaryCrossentropy(), steps_per_execution=64)

    cbs = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=cfg.get("patience", 15), restore_best_weights=True
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=cfg.get("rlr_patience", 5), min_lr=1e-6
        ),
    ]
    y_fit = data["y_tr"]
    if cfg.get("distill", 0) > 0:
        # Destilacion: objetivo = (1-a)*y + a*p_profesor(OOF). Val/ES siguen con etiquetas reales.
        a = cfg["distill"]
        y_fit = ((1 - a) * y_fit + a * np.load(P4 / "teacher_oof_train.npy")).astype("float32")
    h = model.fit(
        data["X_tr"],
        y_fit,
        validation_data=(data["X_va"], data["y_va"]),
        epochs=epochs,
        batch_size=bs,
        callbacks=cbs,
        verbose=verbose,
    )
    best_ep = int(np.argmin(h.history["val_loss"])) + 1
    pv = model.predict(data["X_va"], batch_size=8192, verbose=0).ravel()
    pt = model.predict(data["X_te"], batch_size=8192, verbose=0).ravel()
    return pv, pt, best_ep, model
