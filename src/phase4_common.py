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
    - "ple_tree": PLE con tramos guiados por el target (Entrega 2): por cada variable, un arbol
              de decision de una sola variable ajustado en Train; sus hojas son los tramos.
    nan_zero (Entrega 2): el bloque PLE de una fila con dato ausente queda en 0 en lugar de
              codificar la mediana imputada.
    """

    def __init__(self, kind="base", n_bins=16, nan_zero=False, tree_min_leaf=500):
        self.kind, self.n_bins = kind, n_bins
        self.nan_zero, self.tree_min_leaf = nan_zero, tree_min_leaf

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
        if self.kind == "ple_tree":
            from sklearn.tree import DecisionTreeClassifier

            y = df_tr[C.TARGET].to_numpy()
            self.edges = []
            for j in range(num.shape[1]):
                t = DecisionTreeClassifier(
                    max_leaf_nodes=self.n_bins, min_samples_leaf=self.tree_min_leaf, random_state=0
                ).fit(num[:, [j]], y)
                thr = t.tree_.threshold[t.tree_.feature >= 0]
                self.edges.append(np.unique(np.r_[num[:, j].min(), thr, num[:, j].max()]))
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
        if self.kind in ("ple", "ple_tree"):
            miss = clean[self.base].isna().to_numpy()
            blocks = [X0]
            self.slices, start = [], X0.shape[1]  # columnas PLE de cada variable
            for j, e in enumerate(self.edges):
                if len(e) <= 2:  # variable casi constante / binaria
                    continue
                lo, hi = e[:-1], e[1:]
                enc = np.clip((num[:, [j]] - lo) / (hi - lo), 0.0, 1.0)
                if getattr(self, "nan_zero", False):  # codificadores de Fase 4 no tienen el atributo
                    enc[miss[:, j]] = 0.0
                blocks.append(enc)
                self.slices.append((start, start + enc.shape[1]))
                start += enc.shape[1]
            return np.hstack(blocks).astype("float32")
        raise ValueError(self.kind)


_CACHE = {}


def get_data(kind="base", n_bins=16, **enc_kw):
    key = (kind, n_bins, tuple(sorted(enc_kw.items())))
    if key not in _CACHE:
        df, y, tr, va, te = load_raw()
        enc = Encoder(kind, n_bins, **enc_kw).fit(df.iloc[tr])
        X = enc.transform(df)
        _CACHE[key] = dict(
            X_tr=X[tr], y_tr=y[tr], X_va=X[va], y_va=y[va], X_te=X[te], y_te=y[te], enc=enc
        )
    return _CACHE[key]


# ---------------------------------------------------------------------------
# Componentes de Entrega 2: embedding periodico (PLR) y EMA de pesos
# ---------------------------------------------------------------------------
def _keras_parts():
    """Define (una vez) las clases Keras; se crean tarde para no cargar TF al importar el modulo."""
    if "PeriodicEmbedding" in globals():
        return
    import keras
    from keras import ops

    @keras.saving.register_keras_serializable(package="credirisk")
    class PeriodicEmbedding(keras.layers.Layer):
        """PLR (Gorishniy et al., 2022): ReLU(Linear_j([sin(2*pi*c_j*x_j), cos(2*pi*c_j*x_j)])).
        Frecuencias c_j entrenables ~ N(0, sigma); una capa lineal propia por variable."""

        def __init__(self, k=16, sigma=0.1, d=16, **kw):
            super().__init__(**kw)
            self.k, self.sigma, self.d = k, sigma, d

        def build(self, shape):
            n = shape[-1]
            self.c = self.add_weight(shape=(n, self.k), name="freq",
                                     initializer=keras.initializers.RandomNormal(0.0, self.sigma))
            self.w = self.add_weight(shape=(n, 2 * self.k, self.d), name="w",
                                     initializer="glorot_uniform")
            self.b = self.add_weight(shape=(n, self.d), name="b", initializer="zeros")

        def call(self, x):
            v = 2 * np.pi * self.c[None] * x[..., None]  # (b, n, k)
            z = ops.concatenate([ops.sin(v), ops.cos(v)], axis=-1)  # (b, n, 2k)
            e = ops.relu(ops.einsum("bnk,nkd->bnd", z, self.w) + self.b)
            return ops.reshape(e, (-1, e.shape[1] * self.d))

        def get_config(self):
            return {**super().get_config(), "k": self.k, "sigma": self.sigma, "d": self.d}

    class WeightEMA(keras.callbacks.Callback):
        """Media movil exponencial de los pesos (Polyak averaging; cf. SWA, Izmailov et al. 2018).
        Se actualiza cada `steps_per_execution` pasos; al final de cada epoca evalua la Log Loss de
        Validacion con los pesos promediados (`val_ema_loss`) y al terminar deja los mejores."""

        def __init__(self, X_va, y_va, beta):
            super().__init__()
            self.X_va, self.y_va, self.beta = X_va, y_va, beta

        def on_train_begin(self, logs=None):
            self.ema = [w.copy() for w in self.model.get_weights()]
            self.best, self.best_w, self.best_epoch = np.inf, None, 0

        def on_train_batch_end(self, batch, logs=None):
            b = self.beta
            self.ema = [b * e + (1 - b) * w for e, w in zip(self.ema, self.model.get_weights())]

        def on_epoch_end(self, epoch, logs=None):
            cur = self.model.get_weights()
            self.model.set_weights(self.ema)
            p = self.model.predict(self.X_va, batch_size=8192, verbose=0).ravel()
            ll = log_loss(self.y_va, np.clip(p, 1e-7, 1 - 1e-7))
            logs["val_ema_loss"] = ll
            if ll < self.best:
                self.best, self.best_w, self.best_epoch = ll, [w.copy() for w in self.ema], epoch + 1
            self.model.set_weights(cur)

        def on_train_end(self, logs=None):
            self.model.set_weights(self.best_w)

    globals().update(PeriodicEmbedding=PeriodicEmbedding, WeightEMA=WeightEMA)


def paired_bootstrap(y, p_new, p_ref, n_boot=2000, seed=2026):
    """Diferencia media de Log Loss por observacion (nuevo - referencia) con IC 95% por bootstrap
    pareado (mismas filas remuestreadas para ambos modelos). Devuelve (media, lo, hi, P(d>=0))."""
    def ll(p):
        p = np.clip(p, 1e-7, 1 - 1e-7)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p))

    d = ll(p_new) - ll(p_ref)
    idx = np.random.default_rng(seed).integers(0, len(y), size=(n_boot, len(y)))
    b = d[idx].mean(1)
    return d.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5), float((b >= 0).mean())


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

    _keras_parts()
    inp = keras.Input(shape=(n_in,))
    x = inp
    if cfg.get("periodic"):
        # PLR sobre las numericas base (primeras columnas de X0); resto (flags, one-hot, PLE) igual
        n_num = len(data["enc"].base)
        emb = PeriodicEmbedding(**cfg["periodic"])(inp[:, :n_num])
        x = keras.layers.Concatenate()([emb, inp[:, n_num:]])
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
    if cfg.get("resnet"):
        # ResNet tabular (Gorishniy et al., 2021) con LayerNorm en lugar de BatchNorm
        # (BatchNorm degrado el AUC en la Fase 1 de este proyecto).
        r = cfg["resnet"]
        x = keras.layers.Dense(r["d"])(x)
        for _ in range(r["blocks"]):
            z = keras.layers.LayerNormalization()(x)
            z = keras.layers.Dense(r["d_hidden"], activation=act, kernel_initializer="he_normal")(z)
            z = keras.layers.Dropout(drop)(z)
            z = keras.layers.Dense(r["d"])(z)
            z = keras.layers.Dropout(r.get("drop_res", 0.0))(z)
            x = keras.layers.Add()([x, z])
        x = keras.layers.Activation(act)(keras.layers.LayerNormalization()(x))
        hidden = ()
    for i, u in enumerate(hidden):
        x = keras.layers.Dense(u, kernel_initializer="he_normal")(x)
        if cfg.get("batchnorm"):
            x = keras.layers.BatchNormalization()(x)
        if cfg.get("layernorm"):
            x = keras.layers.LayerNormalization()(x)
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

    ema = WeightEMA(data["X_va"], data["y_va"], cfg["ema"]) if cfg.get("ema") else None
    mon = "val_ema_loss" if ema else "val_loss"
    cbs = ([ema] if ema else []) + [  # EMA primero: escribe val_ema_loss antes de que lo lea ES
        keras.callbacks.EarlyStopping(
            monitor=mon, mode="min", patience=cfg.get("patience", 15), restore_best_weights=not ema
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor=mon, mode="min", factor=0.5, patience=cfg.get("rlr_patience", 5), min_lr=1e-6
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
    best_ep = ema.best_epoch if ema else int(np.argmin(h.history["val_loss"])) + 1
    pv = model.predict(data["X_va"], batch_size=8192, verbose=0).ravel()
    pt = model.predict(data["X_te"], batch_size=8192, verbose=0).ravel()
    return pv, pt, best_ep, model
