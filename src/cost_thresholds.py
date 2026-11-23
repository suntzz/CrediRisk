"""Umbrales por costo para el modelo final v2 (sobre clientes que el modelo no vio).

1. Calibra la probabilidad de APTO con regresión isotónica ajustada fuera de pliegue
   (cada pliegue se calibra con los otros cuatro).
2. Corrige a la mora real (8,07 %): el dataset está balanceado 50/50.
3. Aprobar si p(apto) real >= c / (1 + c), donde c = costo de un mal crédito aprobado
   en múltiplos de la ganancia de uno bueno (5, 10, 20). Es el umbral que maximiza
   la ganancia esperada si la probabilidad está bien calibrada.
4. Tasa de aprobación y mora entre aprobados a prevalencia real, con intervalo bootstrap.

Política v2 = lista de permitidos: solo Cash loans y Revolving loans; Mortgage loans bloqueado.
Uso: python src/cost_thresholds.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

PI_BAD = 0.0807
COSTS = (5, 10, 20)
ALLOWED = ("Cash loans", "Revolving loans")
OUT = C.ARTIFACTS / "v2"
NB = 300

d = np.load(OUT / "final_oof.npz", allow_pickle=True)
y, products, fold, p = d["y"], d["products"], d["fold_id"], d["final__normal"]


def iso():
    return IsotonicRegression(out_of_bounds="clip", y_min=1e-4, y_max=1 - 1e-4)


p_cal = np.empty_like(p)
for k in np.unique(fold):
    m = fold == k
    p_cal[m] = iso().fit(p[~m], y[~m]).predict(p[m])
calibrator = iso().fit(p, y)  # el que usa predict_v2

pi_s = y.mean()  # proporción de aptos en la muestra


def to_real(pc):
    odds = pc / (1 - pc) * ((1 - PI_BAD) / PI_BAD) / (pi_s / (1 - pi_s))
    return odds / (1 + odds)


p_real = to_real(p_cal)


def at_threshold(yy, pr, thr):
    """Reponderación a prevalencia real (misma lógica que evaluate.metrics_at_real_prevalence)."""
    ok = pr >= thr
    tpr = ok[yy == 1].mean() if (yy == 1).any() else 0.0
    fpr = ok[yy == 0].mean() if (yy == 0).any() else 0.0
    aprob = (1 - PI_BAD) * tpr + PI_BAD * fpr
    mora = PI_BAD * fpr / aprob if aprob > 0 else np.nan
    return aprob, mora


rng = np.random.default_rng(0)
rows = []
for prod in ALLOWED:
    m = products == prod
    yy, pr = y[m], p_real[m]
    for c in COSTS:
        thr = c / (1 + c)
        aprob, mora = at_threshold(yy, pr, thr)
        bs = np.array([at_threshold(yy[s], pr[s], thr) for s in (rng.integers(0, len(yy), len(yy)) for _ in range(NB))])
        gan = aprob * ((1 - mora) - mora * c)  # ganancia por solicitante, en unidades de un buen crédito
        rows.append({
            "producto": prod, "n": int(m.sum()), "costo_malo_vs_bueno": c, "umbral": thr,
            "tasa_aprobacion": aprob, "tasa_aprobacion_ci_low": np.nanpercentile(bs[:, 0], 2.5),
            "tasa_aprobacion_ci_high": np.nanpercentile(bs[:, 0], 97.5),
            "mora_aprobados": mora, "mora_aprobados_ci_low": np.nanpercentile(bs[:, 1], 2.5),
            "mora_aprobados_ci_high": np.nanpercentile(bs[:, 1], 97.5),
            "ganancia_por_solicitante": gan,
        })
tab = pd.DataFrame(rows)
tab.to_csv(C.REPORTS / "umbrales_por_costo.csv", index=False)

# Calibración: error esperado de calibración (10 bins) antes y después
def ece(yy, pp, bins=10):
    e = np.clip((pp * bins).astype(int), 0, bins - 1)
    return float(sum(abs(yy[e == b].mean() - pp[e == b].mean()) * (e == b).mean() for b in range(bins) if (e == b).any()))


cal_rows = [{"modelo": "Final sin calibrar", "ece": ece(y, p)}, {"modelo": "Final calibrado", "ece": ece(y, p_cal)}]
if "prod__normal" in d:
    cal_rows.insert(0, {"modelo": "Producción", "ece": ece(y, d["prod__normal"])})
pd.DataFrame(cal_rows).to_csv(C.REPORTS / "stress_calibracion.csv", index=False)

joblib.dump(calibrator, OUT / "calibrador_isotonico.joblib")
policy = {
    "version": "v2",
    "tipo": "lista_de_permitidos",
    "productos_permitidos": list(ALLOWED),
    "productos_bloqueados": ["Mortgage loans"],
    "regla": "aprobar si p_apto_real >= c/(1+c); p_apto_real = isotónica + corrección a mora real",
    "mora_real_supuesta": PI_BAD,
    "proporcion_aptos_entrenamiento": float(pi_s),
    "costo_por_defecto": 10,
    "umbrales_p_apto_real": {prod: {str(c): c / (1 + c) for c in COSTS} for prod in ALLOWED},
    "resultados_oof": tab.to_dict(orient="records"),
    "nota": "Mismo umbral teórico por producto; cambia la tasa de aprobación porque cambia la distribución de riesgo.",
}
(OUT / "product_threshold_policy.json").write_text(json.dumps(policy, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
pd.set_option("display.width", 200)
print(tab.round(4).to_string(index=False))
print(pd.DataFrame(cal_rows).round(4).to_string(index=False))
