"""Puntúa un CSV con el modelo final v2 y la política por costo.

Uso: python src/predict_v2.py data/ejemplo_lote.csv [--costo 10] [--salida reports/predicciones_v2.csv]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
import model_v2


def main():
    a = argparse.ArgumentParser()
    a.add_argument("csv")
    a.add_argument("--costo", type=int, default=10, choices=(5, 10, 20))
    a.add_argument("--salida", default=str(C.REPORTS / "predicciones_v2.csv"))
    args = a.parse_args()

    df = pd.read_csv(args.csv, encoding="utf-8-sig")
    model = model_v2.load()
    cal = joblib.load(model_v2.V2 / "calibrador_isotonico.joblib")
    pol = json.loads((model_v2.V2 / "product_threshold_policy.json").read_text(encoding="utf-8"))

    p = model.predict_proba(df)
    pc = cal.predict(p)
    pi_s, pi_bad = pol["proporcion_aptos_entrenamiento"], pol["mora_real_supuesta"]
    odds = pc / (1 - pc) * ((1 - pi_bad) / pi_bad) / (pi_s / (1 - pi_s))
    p_real = odds / (1 + odds)

    out = df[["id_solicitud"]].copy() if "id_solicitud" in df else pd.DataFrame({"id_solicitud": np.arange(1, len(df) + 1)})
    out["linea_negocio"] = df["linea_negocio"].to_numpy()
    out["puntaje_modelo"] = p.round(4)
    out["prob_apto_real"] = p_real.round(4)
    decision = []
    for prod, pr in zip(df["linea_negocio"], p_real):
        if prod not in pol["productos_permitidos"]:
            decision.append("NO DISPONIBLE (producto bloqueado)")
        else:
            thr = pol["umbrales_p_apto_real"][prod][str(args.costo)]
            decision.append("APROBAR" if pr >= thr else "RECHAZAR")
    out["decision"] = decision
    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.salida, index=False)
    print(out.head(20).to_string(index=False))
    print(f"\n{len(out)} filas -> {args.salida}")


if __name__ == "__main__":
    main()
