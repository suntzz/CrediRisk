"""Candidatos de mejora, medidos con el mismo protocolo que la línea base.

Uso:
    python src/cv_candidates.py hgb_lab

Cada candidato recibe (df_tr, y_tr, variantes, seed_offset) y devuelve
{variante: {componente: probabilidades}}. No toca artefactos de producción.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
import cv_protocol as P

SCORE = P.SCORE_COL

HGB_A = dict(P.HGB_CONFIG)  # el de producción
HGB_B = {
    "max_iter": 2000, "learning_rate": 0.02, "max_leaf_nodes": 15, "min_samples_leaf": 80,
    "l2_regularization": 5.0, "max_features": 0.6, "early_stopping": True,
    "validation_fraction": 0.12, "n_iter_no_change": 60, "random_state": 42,
}


def add_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Razones calculadas solo con columnas del dataset común. Ninguna usa el score."""
    d = df.copy()
    ing = d["ingreso_mensual"].where(d["ingreso_mensual"] > 0)
    cuota = d["cuota_estimada"].where(d["cuota_estimada"] > 0)
    monto = d["monto_solicitado"].where(d["monto_solicitado"] > 0)
    d["r_monto_ingreso"] = d["monto_solicitado"] / ing
    d["r_cuota_ingreso"] = d["cuota_estimada"] / ing
    d["r_saldo_ingreso"] = d["saldo_total_creditos"] / ing
    d["r_obligaciones_ingreso"] = d["obligaciones_mensuales"] / ing
    d["r_monto_cuota"] = d["monto_solicitado"] / cuota           # plazo efectivo
    d["r_costo_total"] = d["cuota_estimada"] * d["plazo_meses"] / monto
    d["r_saldo_monto"] = d["saldo_total_creditos"] / monto
    d["r_mora_por_credito"] = d["numero_cuotas_mora"] / (d["numero_creditos_activos"] + 1)
    d["r_creditos_por_anio"] = d["numero_creditos_activos"] / (d["antiguedad_cliente_anios"] + 1)
    d["r_ingreso_por_persona"] = d["ingreso_mensual"] / (d["personas_a_cargo"].fillna(0) + 1)
    d["edad_inicio_laboral"] = d["edad"] - d["antiguedad_laboral_anios"]
    d["r_antiguedad_edad"] = d["antiguedad_laboral_anios"] / d["edad"]
    d["n_vacios"] = df.drop(columns=[c for c in C.DROP_COLS + [C.TARGET] if c in df]).isna().sum(axis=1)
    return d.replace([np.inf, -np.inf], np.nan)


class RawFrame:
    """Variables crudas para el HGB: NaN nativo y categóricas nativas (sin escalar ni imputar)."""

    def __init__(self, ratios: bool, drop: tuple[str, ...] = ()):
        self.ratios, self.drop = ratios, drop

    def fit(self, df):
        self.cats = {c: sorted(df[c].dropna().unique()) for c in C.CAT_COLS}
        return self

    def transform(self, df):
        d = add_ratios(df) if self.ratios else df.copy()
        d = d.drop(columns=[c for c in C.DROP_COLS + [C.TARGET] + list(self.drop) if c in d])
        for c, cats in self.cats.items():
            d[c] = pd.Categorical(d[c].where(d[c].isin(cats)), categories=cats)  # categoría no vista -> NaN
        return d


def _hgb(config, seed=42, mono_score=False):
    kw = dict(config, random_state=seed, categorical_features="from_dtype")
    if mono_score:
        kw["monotonic_cst"] = {SCORE: 1}  # más score nunca baja la probabilidad de APTO
    return HistGradientBoostingClassifier(**kw)


def hgb_lab(df_tr, y_tr, variants, seed_offset):
    out = {name: {} for name in variants}

    def fit_predict(label, frame, model_factory, seeds=(42,)):
        frame.fit(df_tr)
        X_tr = frame.transform(df_tr)
        models = [model_factory(s + seed_offset).fit(X_tr, y_tr) for s in seeds]
        for name, d in variants.items():
            X = frame.transform(d)
            out[name][label] = np.mean([m.predict_proba(X)[:, 1] for m in models], axis=0)

    fit_predict("crudo_A", RawFrame(False), lambda s: _hgb(HGB_A, s))
    fit_predict("razones_A", RawFrame(True), lambda s: _hgb(HGB_A, s))
    fit_predict("razones_B", RawFrame(True), lambda s: _hgb(HGB_B, s))
    fit_predict("razones_B_mono", RawFrame(True), lambda s: _hgb(HGB_B, s, mono_score=True))
    fit_predict("razones_B_3sem", RawFrame(True), lambda s: _hgb(HGB_B, s), seeds=(42, 7, 2026))
    fit_predict("sin_score_B", RawFrame(True, drop=(SCORE,)), lambda s: _hgb(HGB_B, s))
    return out


class PreprocessorV2:
    """Preprocesador corregido para las redes.

    Diferencias con preprocess.Preprocessor:
    - la mediana de imputación se calcula DESPUÉS de recorte y logaritmo (el
      original la calculaba antes y la aplicaba después, lo que mandaba los
      vacíos de cuatro variables a un valor absurdo);
    - bandera de vacío para toda variable con vacíos, incluido el score;
    - razones entre variables;
    - `drop` permite construir la rama sin score.
    """

    def __init__(self, ratios: bool = True, drop: tuple[str, ...] = ()):
        self.ratios, self.drop = ratios, drop

    def _frame(self, df):
        d = add_ratios(df) if self.ratios else df.copy()
        d = d.drop(columns=[c for c in C.DROP_COLS + [C.TARGET] + list(self.drop) if c in d])
        for col, rare in C.RARE_TO_OTRO.items():
            d[col] = d[col].replace({r: "Otro" for r in rare})
        return d

    def _numeric(self, d):
        x = d[self.num].clip(self.lo, self.hi, axis=1)
        x[self.log] = np.sign(x[self.log]) * np.log1p(x[self.log].abs())
        return x

    def fit(self, df):
        d = self._frame(df)
        self.num = [c for c in d.columns if c not in C.CAT_COLS]
        self.flag = [c for c in self.num if d[c].isna().mean() > 0.005]
        self.log = [c for c in self.num if c in C.SKEW_COLS + C.SIGNED_LOG_COLS or c.startswith("r_")]
        self.lo, self.hi = d[self.num].quantile(0.01), d[self.num].quantile(0.99)
        self.median = self._numeric(d).median()  # en la misma escala en que se aplica
        self.dummy_cols = list(pd.get_dummies(d[C.CAT_COLS], dtype=float).columns)
        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler().fit(self._matrix(d))
        self.feature_names = self.num + [c + "_nan" for c in self.flag] + self.dummy_cols
        return self

    def _matrix(self, d):
        x = self._numeric(d).fillna(self.median)
        flags = d[self.flag].isna().astype(float)
        dummies = pd.get_dummies(d[C.CAT_COLS], dtype=float).reindex(columns=self.dummy_cols, fill_value=0.0)
        return np.hstack([x.to_numpy(float), flags.to_numpy(float), dummies.to_numpy(float)])

    def transform(self, df):
        return self.scaler.transform(self._matrix(self._frame(df))).astype("float32")


def _train_mlps(X_tr, y_tr, X_var: dict, seed_offset: int, prefix: str, out: dict):
    """Las mismas tres redes de producción, sin cambiar arquitectura ni entrenamiento."""
    from sklearn.model_selection import train_test_split
    from tensorflow import keras
    from experiments import build_custom_model

    fit_i, es_i = train_test_split(np.arange(len(y_tr)), test_size=P.INNER_VAL_FRAC, stratify=y_tr, random_state=C.SPLIT_SEED)
    for spec in P.MLP_SPECS:
        keras.backend.clear_session()
        keras.utils.set_random_seed(spec["seed"] + seed_offset)
        model = build_custom_model(
            n_features=X_tr.shape[1], layers=spec["layers"], activation=spec["activation"],
            dropout_rate=spec["dropout"], dropout_layers=spec["dropout_layers"], learning_rate=spec["lr"],
        )
        callbacks = [
            keras.callbacks.EarlyStopping(monitor=spec["monitor"], mode=spec["mode"], patience=12, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(monitor=spec["monitor"], mode=spec["mode"], factor=0.5, patience=5, min_lr=1e-5),
        ]
        model.fit(X_tr[fit_i], y_tr[fit_i], validation_data=(X_tr[es_i], y_tr[es_i]),
                  epochs=80, batch_size=128, callbacks=callbacks, verbose=0)
        for name, X in X_var.items():
            out[name][prefix + spec["name"]] = model.predict(X, verbose=0, batch_size=8192).ravel()
    for name in X_var:
        out[name][prefix + "neural"] = np.mean([out[name][prefix + s["name"]] for s in P.MLP_SPECS], axis=0)


def mlp_v2(df_tr, y_tr, variants, seed_offset):
    """Redes con el preprocesador corregido: solo el arreglo, arreglo + razones, y rama sin score."""
    out = {name: {} for name in variants}
    for prefix, pre in (
        ("v2_", PreprocessorV2(ratios=True)),
        ("ns_", PreprocessorV2(ratios=True, drop=(SCORE,))),
    ):
        pre.fit(df_tr)
        _train_mlps(pre.transform(df_tr), y_tr, {n: pre.transform(d) for n, d in variants.items()}, seed_offset, prefix, out)
    return out


HGB_C = dict(HGB_B, learning_rate=0.01, max_leaf_nodes=7, min_samples_leaf=100, max_iter=5000, n_iter_no_change=120)
HGB_D = dict(HGB_B, learning_rate=0.03, max_leaf_nodes=31, min_samples_leaf=150, l2_regularization=10.0, max_features=0.5)
KNN_COLS = [SCORE, "r_monto_cuota", "r_cuota_ingreso", "edad", "antiguedad_laboral_anios"]


class KnnFrame(RawFrame):
    """RawFrame + tasa de aptos entre los vecinos más parecidos (calculada solo con train).

    Para las filas de entrenamiento el vecino más cercano es la propia fila y se
    descarta, así la variable no ve su propia etiqueta.
    """

    def __init__(self, ks=(100, 500)):
        super().__init__(True)
        self.ks = ks

    def _z(self, df):
        x = add_ratios(df)[KNN_COLS]
        return ((x.fillna(self.med) - self.mu) / self.sd).clip(-4, 4).to_numpy()

    def fit_y(self, df, y):
        from sklearn.neighbors import NearestNeighbors
        super().fit(df)
        x = add_ratios(df)[KNN_COLS]
        self.med, self.mu, self.sd = x.median(), x.mean(), x.std()
        self.y = y
        self.nn = NearestNeighbors(n_neighbors=max(self.ks) + 1).fit(self._z(df))
        return self

    def transform(self, df, is_train=False):
        d = super().transform(df)
        idx = self.nn.kneighbors(self._z(df), return_distance=False)
        idx = idx[:, 1:] if is_train else idx[:, :-1]
        for k in self.ks:
            d[f"knn_{k}"] = self.y[idx[:, :k]].mean(axis=1)
        return d


def hgb_lab2(df_tr, y_tr, variants, seed_offset):
    """¿Hay techo por encima de 0,762? Más semillas, otras formas del árbol, vecinos y curva de aprendizaje."""
    out = {name: {} for name in variants}
    frame = RawFrame(True).fit(df_tr)
    X_tr = frame.transform(df_tr)
    X_var = {n: frame.transform(d) for n, d in variants.items()}

    def run(label, config, seeds, rows=None):
        Xt, yt = (X_tr, y_tr) if rows is None else (X_tr.iloc[rows], y_tr[rows])
        models = [_hgb(config, s + seed_offset).fit(Xt, yt) for s in seeds]
        for n, X in X_var.items():
            out[n][label] = np.mean([m.predict_proba(X)[:, 1] for m in models], axis=0)

    run("B_6sem", HGB_B, (42, 7, 2026, 1, 21, 99))
    run("C_fino_3sem", HGB_C, (42, 7, 2026))
    run("D_ancho_3sem", HGB_D, (42, 7, 2026))
    half = np.random.default_rng(seed_offset).permutation(len(y_tr))[: len(y_tr) // 2]
    run("B_mitad_datos_3sem", HGB_B, (42, 7, 2026), rows=half)

    knn = KnnFrame().fit_y(df_tr, y_tr)
    Xk = knn.transform(df_tr, is_train=True)
    models = [_hgb(HGB_B, s + seed_offset).fit(Xk, y_tr) for s in (42, 7, 2026)]
    for n, d in variants.items():
        Xv = knn.transform(d)
        out[n]["B_vecinos_3sem"] = np.mean([m.predict_proba(Xv)[:, 1] for m in models], axis=0)
    for n in variants:
        out[n]["mezcla_BCD"] = (out[n]["B_6sem"] + out[n]["C_fino_3sem"] + out[n]["D_ancho_3sem"]) / 3
    return out


P.CANDIDATES["hgb_lab"] = hgb_lab
P.CANDIDATES["mlp_v2"] = mlp_v2
P.CANDIDATES["hgb_lab2"] = hgb_lab2


def mlp_fix(df_tr, y_tr, variants, seed_offset):
    """Solo el arreglo de imputación, sin razones: aísla cuánto aporta el arreglo a las redes."""
    out = {name: {} for name in variants}
    pre = PreprocessorV2(ratios=False).fit(df_tr)
    _train_mlps(pre.transform(df_tr), y_tr, {n: pre.transform(d) for n, d in variants.items()}, seed_offset, "fix_", out)
    return out


P.CANDIDATES["mlp_fix"] = mlp_fix

if __name__ == "__main__":
    P.run(sys.argv[1])
