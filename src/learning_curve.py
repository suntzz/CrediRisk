"""¿Se puede llegar a 0,77 con estos datos? Curva de aprendizaje del árbol nuevo.

Una sola partición 80/20 de train+val (la prueba vieja no se toca). El árbol
(variables crudas + razones, config B, 3 semillas) se entrena con 25 %, 50 % y
100 % del 80 % y se mide en el mismo 20 %.
Uso: python src/learning_curve.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
import cv_protocol as P
from cv_candidates import HGB_B, RawFrame, _hgb

df, y, _ = P.load_dev()
tr, te = train_test_split(np.arange(len(y)), test_size=0.2, stratify=y, random_state=7)
frame = RawFrame(True).fit(df.iloc[tr])
Xtr, Xte = frame.transform(df.iloc[tr]), frame.transform(df.iloc[te])
rng = np.random.default_rng(0)
order = rng.permutation(len(tr))
rows = []
for frac in (0.25, 0.5, 1.0):
    idx = order[: int(frac * len(tr))]
    p = np.mean([_hgb(HGB_B, s).fit(Xtr.iloc[idx], y[tr][idx]).predict_proba(Xte)[:, 1] for s in (42, 7, 2026)], axis=0)
    rows.append({"fraccion_datos": frac, "filas_entrenamiento": len(idx), "auc": P.fast_auc(y[te], p)})
    print(rows[-1], flush=True)
out = pd.DataFrame(rows)
# Extrapolación honesta: ganancia al duplicar datos (50 % -> 100 %)
out["ganancia_al_duplicar"] = out.auc.diff()
out.to_csv(C.REPORTS / "v2_curva_aprendizaje.csv", index=False)
print(out.to_string(index=False))
