"""Pruebas de estrés baratas, producción vs final v2, sobre clientes que el modelo no vio.

Todo sale de artifacts/v2/final_oof.npz (repetición 0 de la validación cruzada):
score ausente, score barajado, subgrupos (producto, deciles de score, terciles de
edad, tipo de contrato) y estabilidad entre pliegues. La calibración la escribe
cost_thresholds.py (reports/stress_calibracion.csv).
Uso: python src/stress_tests.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from cv_protocol import fast_auc, load_dev

d = np.load(C.ARTIFACTS / "v2" / "final_oof.npz", allow_pickle=True)
y, fold = d["y"], d["fold_id"]
df, y_dev, _ = load_dev()
assert np.array_equal(y, y_dev)

res = pd.DataFrame([
    {"prueba": label, "auc_produccion": fast_auc(y, d[f"prod__{v}"]), "auc_final": fast_auc(y, d[f"final__{v}"])}
    for label, v in (("Normal", "normal"), ("Score ausente", "score_vacio"), ("Score barajado", "score_permutado"))
])
res.to_csv(C.REPORTS / "stress_resumen.csv", index=False)

groups = {
    "Producto": df["linea_negocio"].astype(str),
    "Decil de score": pd.qcut(df["score_crediticio"], 10, labels=[f"D{i}" for i in range(1, 11)]).astype(str)
    .where(df["score_crediticio"].notna(), "Sin score"),
    "Edad": pd.qcut(df["edad"], 3, labels=["Joven", "Media", "Mayor"]).astype(str),
    "Tipo de contrato": df["tipo_contrato"].astype(str),
}
rows = []
for g, s in groups.items():
    for seg in sorted(s.unique(), key=lambda v: (len(v), v)):
        m = (s == seg).to_numpy()
        if m.sum() < 200 or len(np.unique(y[m])) < 2:
            continue
        rows.append({"grupo": g, "segmento": seg, "n": int(m.sum()),
                     "auc_produccion": fast_auc(y[m], d["prod__normal"][m]),
                     "auc_final": fast_auc(y[m], d["final__normal"][m])})
sub = pd.DataFrame(rows)
sub.to_csv(C.REPORTS / "stress_subgrupos.csv", index=False)

pl = pd.DataFrame([{"pliegue": int(k) + 1,
                    "auc_produccion": fast_auc(y[fold == k], d["prod__normal"][fold == k]),
                    "auc_final": fast_auc(y[fold == k], d["final__normal"][fold == k])} for k in np.unique(fold)])
pl["final_gana"] = pl.auc_final > pl.auc_produccion
pl.to_csv(C.REPORTS / "stress_pliegues.csv", index=False)

pd.set_option("display.width", 200)
print(res.round(4).to_string(index=False))
print(sub.round(4).to_string(index=False))
print(pl.round(4).to_string(index=False))
