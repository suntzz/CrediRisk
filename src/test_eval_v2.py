"""Mirada ÚNICA a la prueba vieja (7.448 filas): producción vs final v2.

Se corre una sola vez, con el modelo ya escogido. Nada se decide con esto.
Uso: python src/test_eval_v2.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
import cv_protocol as P
import model_v2

df = pd.read_csv(C.DATA_CSV, encoding="utf-8-sig")
y_all = df[C.TARGET].to_numpy("float32")
_, _, te = P.split_indices(y_all)
dt, y = df.iloc[te].reset_index(drop=True), y_all[te]
assert len(dt) == 7448

rng = np.random.default_rng(P.CV_SEED)
perm = dt.copy()
perm[P.SCORE_COL] = rng.permutation(perm[P.SCORE_COL].to_numpy())
vac = dt.copy()
vac[P.SCORE_COL] = np.nan
variants = {"normal": dt, "score_permutado": perm, "score_vacio": vac}

# Producción, tal cual (solo lectura de artefactos)
from tensorflow import keras
pre = joblib.load(C.ARTIFACTS / "preprocessor.joblib")
man = json.loads((C.ARTIFACTS / "production_manifest.json").read_text())
nets = [keras.models.load_model(C.ARTIFACTS / m["file"]) for m in man["models"]]
hgb = joblib.load(C.ARTIFACTS / "hybrid_hgb.joblib")


def prod_predict(d):
    X = pre.transform(d)
    neural = np.mean([m.predict(X, verbose=0, batch_size=8192).ravel() for m in nets], axis=0)
    return 0.65 * hgb.predict_proba(X)[:, 1] + 0.35 * neural


model = model_v2.load()
pp = {k: prod_predict(d) for k, d in variants.items()}
pf = {k: model.predict_proba(d) for k, d in variants.items()}


def dep(p):
    a, ap = P.fast_auc(y, p["normal"]), P.fast_auc(y, p["score_permutado"])
    return 100 * (a - ap) / (a - 0.5)


rows = []
prods = dt["linea_negocio"].to_numpy()
for seg, m in [("GLOBAL", np.ones(len(y), bool))] + [(s, prods == s) for s in ("Cash loans", "Revolving loans")]:
    b = P.paired_bootstrap(y[m], pp["normal"][m], pf["normal"][m], n_boot=1000)
    rows.append({"segmento": seg, "n": int(m.sum()), "auc_produccion": P.fast_auc(y[m], pp["normal"][m]),
                 "auc_final": P.fast_auc(y[m], pf["normal"][m]), "diff": b["diff"], "ci_low": b["ci_low"],
                 "ci_high": b["ci_high"], "significativo": b["significant"]})
rows.append({"segmento": "Dependencia del score (%)", "n": len(y), "auc_produccion": dep(pp), "auc_final": dep(pf)})
rows.append({"segmento": "AUC con score ausente", "n": len(y), "auc_produccion": P.fast_auc(y, pp["score_vacio"]),
             "auc_final": P.fast_auc(y, pf["score_vacio"])})
out = pd.DataFrame(rows)
out.to_csv(C.REPORTS / "final_v2_test.csv", index=False)

res_p = C.REPORTS / "v2_resumen.csv"
res = pd.read_csv(res_p)
res = res[res.metrica != "auc_prueba"]
res = pd.concat([res, pd.DataFrame([{"metrica": "auc_prueba", "antes": rows[0]["auc_produccion"], "despues": rows[0]["auc_final"]}])])
res.to_csv(res_p, index=False)
pd.set_option("display.width", 200)
print(out.round(5).to_string(index=False))
