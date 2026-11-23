"""Protocolo de evaluación: validación cruzada estratificada repetida sobre train+val.

Por qué existe: el conjunto de prueba ya se consultó con muchos candidatos y la
validación se usó a la vez para parada temprana, selección, pesos y umbrales.
Aquí cada candidato se mide con predicciones fuera de pliegue (OOF):

- 5 pliegues x 3 repeticiones sobre train+val (la prueba vieja NO se toca).
- Estratificado por objetivo x linea_negocio.
- El preprocesador se ajusta dentro de cada pliegue, solo con sus filas de entrenamiento.
- Las redes paran temprano contra un apartado interno del pliegue, nunca contra
  las filas donde se van a medir.
- Diferencias entre candidatos con bootstrap pareado.
- Dependencia del score: AUC al permutar score_crediticio y al dejarlo vacío.

Uso:
    python src/cv_protocol.py baseline            # híbrido actual, tal cual
    python src/cv_protocol.py compare A B         # bootstrap pareado entre dos corridas guardadas
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from preprocess import Preprocessor

CV_DIR = C.ARTIFACTS / "cv"
N_SPLITS, N_REPEATS, CV_SEED = 5, int(os.environ.get("CV_REPEATS", 3)), 20261123
INNER_VAL_FRAC = 0.15
SCORE_COL = "score_crediticio"
PRODUCT_COL = "linea_negocio"

# Copia literal de la configuración en producción (phase7 + train_ensembles).
HGB_WEIGHT = 0.65
HGB_CONFIG = {
    "max_iter": 450, "learning_rate": 0.04, "max_leaf_nodes": 31,
    "min_samples_leaf": 40, "l2_regularization": 3.0, "early_stopping": True,
    "validation_fraction": 0.12, "n_iter_no_change": 25, "random_state": 42,
}
MLP_SPECS = (
    {"name": "m1", "layers": [64, 32, 16], "activation": "relu", "dropout": 0.15,
     "dropout_layers": "first_two", "lr": 0.0005, "seed": 42, "monitor": "val_auc", "mode": "max"},
    {"name": "m2", "layers": [32, 16], "activation": "leaky_relu", "dropout": 0.15,
     "dropout_layers": "all_except_last", "lr": 0.0005, "seed": 42, "monitor": "val_auc", "mode": "max"},
    {"name": "m3", "layers": [64, 32, 16], "activation": "relu", "dropout": 0.20,
     "dropout_layers": "first_two", "lr": 0.001, "seed": 2026, "monitor": "val_loss", "mode": "min"},
)


# ---------------------------------------------------------------- datos

def split_indices(y: np.ndarray):
    """Misma partición que preprocess.main() y phase4 (semilla 42, 70/15/15)."""
    idx = np.arange(len(y))
    tr, tmp = train_test_split(idx, test_size=C.VAL_FRAC + C.TEST_FRAC, stratify=y, random_state=C.SPLIT_SEED)
    va, te = train_test_split(tmp, test_size=C.TEST_FRAC / (C.VAL_FRAC + C.TEST_FRAC), stratify=y[tmp], random_state=C.SPLIT_SEED)
    return tr, va, te


def load_dev():
    """Devuelve (df_dev, y_dev, dev_idx). La prueba vieja queda fuera, congelada."""
    df = pd.read_csv(C.DATA_CSV, encoding="utf-8-sig")
    y = df[C.TARGET].to_numpy("float32")
    tr, va, _ = split_indices(y)
    dev_idx = np.sort(np.concatenate([tr, va]))
    df_dev = df.iloc[dev_idx].reset_index(drop=True)
    # Comprobación de fuga: el complemento exacto del objetivo nunca es variable.
    assert "INCUMPLIO_PAGO" in C.DROP_COLS and C.TARGET not in Preprocessor().fit(df_dev.head(2000)).feature_names
    return df_dev, y[dev_idx], dev_idx


def folds(df_dev: pd.DataFrame, y: np.ndarray):
    strata = pd.Series(y.astype(int).astype(str)) + "|" + df_dev[PRODUCT_COL].astype(str)
    for rep in range(N_REPEATS):
        skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=CV_SEED + rep)
        for k, (tr, te) in enumerate(skf.split(np.zeros(len(y)), strata)):
            yield rep, k, tr, te


# ---------------------------------------------------------------- métricas

def fast_auc(y: np.ndarray, p: np.ndarray) -> float:
    r = rankdata(p)
    n1 = y.sum()
    n0 = len(y) - n1
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def paired_bootstrap(y, p_a, p_b, n_boot=2000, seed=0):
    """Diferencia de AUC (b - a) con intervalo al 95 %, remuestreando las mismas filas."""
    # p_a y p_b tienen forma (repeticiones, n): la diferencia se calcula por
    # repetición y se promedia. Promediar antes las predicciones regalaría un
    # ensamble de 3 al modelo más inestable y sesgaría la comparación.
    p_a, p_b = np.atleast_2d(p_a), np.atleast_2d(p_b)
    rng = np.random.default_rng(seed)
    n = len(y)

    def diff(s):
        return float(np.mean([fast_auc(y[s], b[s]) - fast_auc(y[s], a[s]) for a, b in zip(p_a, p_b)]))

    diffs = np.array([diff(rng.integers(0, n, n)) for _ in range(n_boot)])
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"diff": diff(np.arange(n)), "ci_low": float(lo), "ci_high": float(hi),
            "significant": bool(lo > 0 or hi < 0)}


def summarize(y, products, oof: dict[str, np.ndarray], fold_id: np.ndarray) -> pd.DataFrame:
    """oof[nombre] tiene forma (repeticiones, n). Una fila por componente y segmento."""
    rows = []
    segments = {"GLOBAL": np.ones(len(y), bool)}
    for prod in sorted(pd.unique(products)):
        segments[prod] = products == prod
    for name, P in oof.items():
        for seg, mask in segments.items():
            per_fold = [fast_auc(y[mask & (fold_id[r] == k)], P[r][mask & (fold_id[r] == k)])
                        for r in range(P.shape[0]) for k in range(N_SPLITS)]
            per_rep = [fast_auc(y[mask], P[r][mask]) for r in range(P.shape[0])]
            p_mean = P.mean(axis=0)
            rows.append({
                "componente": name, "segmento": seg, "n": int(mask.sum()),
                "auc_oof": float(np.mean(per_rep)), "auc_sd_repeticiones": float(np.std(per_rep)),
                "auc_pliegue_media": float(np.mean(per_fold)), "auc_pliegue_sd": float(np.std(per_fold)),
                "auc_pliegue_min": float(np.min(per_fold)), "auc_pliegue_max": float(np.max(per_fold)),
                "pr_auc": float(average_precision_score(y[mask], p_mean[mask])),
                "brier": float(brier_score_loss(y[mask], p_mean[mask])),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- candidato: híbrido actual

def baseline_candidate(df_tr, y_tr, variants: dict[str, pd.DataFrame], seed_offset: int):
    """Híbrido en producción, sin cambios: preprocesador actual, HGB + 3 redes, 0,65/0,35.

    `variants` son versiones de las filas de medición (normal, score permutado...).
    Devuelve {variante: {componente: probabilidades}}.
    """
    from tensorflow import keras
    from experiments import build_custom_model

    pre = Preprocessor().fit(df_tr)
    X_tr = pre.transform(df_tr)
    X_var = {name: pre.transform(d) for name, d in variants.items()}

    hgb = HistGradientBoostingClassifier(**HGB_CONFIG).fit(X_tr, y_tr)
    out = {name: {"hgb": hgb.predict_proba(X)[:, 1]} for name, X in X_var.items()}

    fit_i, es_i = train_test_split(np.arange(len(y_tr)), test_size=INNER_VAL_FRAC, stratify=y_tr, random_state=C.SPLIT_SEED)
    for spec in MLP_SPECS:
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
            out[name][spec["name"]] = model.predict(X, verbose=0, batch_size=8192).ravel()

    for name in out:
        neural = np.mean([out[name][s["name"]] for s in MLP_SPECS], axis=0)
        out[name]["neural"] = neural
        out[name]["hybrid"] = HGB_WEIGHT * out[name]["hgb"] + (1 - HGB_WEIGHT) * neural
    return out


CANDIDATES = {"baseline": baseline_candidate}


# ---------------------------------------------------------------- corrida

def run(candidate_name: str):
    candidate = CANDIDATES[candidate_name]
    CV_DIR.mkdir(parents=True, exist_ok=True)
    df_dev, y, dev_idx = load_dev()
    n = len(y)
    products = df_dev[PRODUCT_COL].to_numpy()
    fold_id = np.full((N_REPEATS, n), -1, dtype=np.int8)
    store: dict[str, dict[str, np.ndarray]] = {}
    t0 = time.time()

    for rep, k, tr, te in folds(df_dev, y):
        fold_id[rep, te] = k
        df_te = df_dev.iloc[te]
        rng = np.random.default_rng(CV_SEED + 100 * rep + k)
        perm = df_te.copy()
        perm[SCORE_COL] = rng.permutation(perm[SCORE_COL].to_numpy())
        sin = df_te.copy()
        sin[SCORE_COL] = np.nan
        variants = {"normal": df_te, "score_permutado": perm, "score_vacio": sin}
        result = candidate(df_dev.iloc[tr], y[tr], variants, seed_offset=1000 * rep + k)
        for variant, comps in result.items():
            for comp, p in comps.items():
                store.setdefault(variant, {}).setdefault(comp, np.full((N_REPEATS, n), np.nan, dtype=np.float32))[rep, te] = p
        auc = fast_auc(y[te], result["normal"]["hybrid"]) if "hybrid" in result["normal"] else float("nan")
        print(f"rep {rep + 1}/{N_REPEATS} pliegue {k + 1}/{N_SPLITS}  AUC híbrido {auc:.5f}  ({time.time() - t0:.0f}s)", flush=True)

    np.savez_compressed(
        CV_DIR / f"{candidate_name}_oof.npz", y=y, dev_idx=dev_idx, fold_id=fold_id, products=products,
        **{f"{variant}__{comp}": P for variant, comps in store.items() for comp, P in comps.items()},
    )

    summary = summarize(y, products, store["normal"], fold_id)
    summary.to_csv(C.REPORTS / f"cv_{candidate_name}_resumen.csv", index=False)

    # Dependencia del score, medida sobre el modelo real (no sobre model_final.keras).
    dep_rows = []
    for comp in store["normal"]:
        base = np.mean([fast_auc(y, store["normal"][comp][r]) for r in range(N_REPEATS)])
        perm_auc = np.mean([fast_auc(y, store["score_permutado"][comp][r]) for r in range(N_REPEATS)])
        vac_auc = np.mean([fast_auc(y, store["score_vacio"][comp][r]) for r in range(N_REPEATS)])
        dep_rows.append({
            "componente": comp, "auc": base, "auc_score_permutado": perm_auc, "auc_score_vacio": vac_auc,
            "caida_al_permutar": base - perm_auc, "caida_al_vaciar": base - vac_auc,
            # Parte del poder discriminante (AUC - 0,5) que se pierde sin el score.
            "dependencia_pct": 100 * (base - perm_auc) / (base - 0.5),
        })
    dep = pd.DataFrame(dep_rows)
    dep.to_csv(C.REPORTS / f"cv_{candidate_name}_dependencia_score.csv", index=False)

    meta = {
        "candidato": candidate_name, "filas_dev": int(n), "pliegues": N_SPLITS, "repeticiones": N_REPEATS,
        "semilla_cv": CV_SEED, "segundos": round(time.time() - t0),
        "nota": "La prueba vieja (7.448 filas) no se usa en este protocolo.",
    }
    (C.REPORTS / f"cv_{candidate_name}_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.set_option("display.width", 200)
    print("\n=== RESUMEN (fuera de pliegue) ===")
    print(summary.round(5).to_string(index=False))
    print("\n=== DEPENDENCIA DEL SCORE ===")
    print(dep.round(5).to_string(index=False))


def compare(a: str, b: str, comp_a="hybrid", comp_b="hybrid"):
    da, db = np.load(CV_DIR / f"{a}_oof.npz", allow_pickle=True), np.load(CV_DIR / f"{b}_oof.npz", allow_pickle=True)
    assert np.array_equal(da["dev_idx"], db["dev_idx"]), "Las corridas no usan las mismas filas."
    y, products = da["y"], da["products"]
    pa, pb = da[f"normal__{comp_a}"], db[f"normal__{comp_b}"]
    rows = [{"segmento": "GLOBAL", **paired_bootstrap(y, pa, pb, n_boot=1000)}]
    for prod in sorted(pd.unique(products)):
        m = products == prod
        rows.append({"segmento": prod, **paired_bootstrap(y[m], pa[:, m], pb[:, m], n_boot=1000)})
    out = pd.DataFrame(rows)
    out.to_csv(C.REPORTS / f"cv_compara_{a}_{comp_a}__{b}_{comp_b}.csv", index=False)
    print(out.round(5).to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "compare":
        compare(*sys.argv[2:])
    else:
        run(sys.argv[1] if len(sys.argv) > 1 else "baseline")
