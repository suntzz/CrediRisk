"""Muestra el error de imputación del preprocesador de producción (src/preprocess.py).

La mediana se calculaba en escala original (fit, línea ~33) y se aplicaba DESPUÉS
de log1p (_matrix, línea ~48): un vacío recibía, en escala log, el número de la
mediana original (p. ej. 400000) en vez de log1p(400000) ≈ 12,9.

Solo lee el CSV y ajusta el Preprocessor viejo en memoria con el mismo split de
train que producción. No guarda modelos; escribe reports/v2_imputacion.csv.

    nice -n 5 ~/opt/credirisk-venv/bin/python scripts/imputacion_demo.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import config as C  # noqa: E402
from preprocess import Preprocessor  # noqa: E402  (no se ejecuta su main)


def main(out: Path = ROOT / "reports" / "v2_imputacion.csv"):
    df = pd.read_csv(C.DATA_CSV, encoding="utf-8-sig")
    y = df[C.TARGET].to_numpy("float32")
    idx = np.arange(len(df))
    tr, _ = train_test_split(idx, test_size=C.VAL_FRAC + C.TEST_FRAC,
                             stratify=y, random_state=C.SPLIT_SEED)
    pre = Preprocessor().fit(df.iloc[tr])
    train = pre._clean(df.iloc[tr])

    filas = []
    for c in list(C.SKEW_COLS) + list(C.SIGNED_LOG_COLS):
        if c not in train:
            continue
        x = train[c].clip(pre.lo[c], pre.hi[c])
        if c in C.SIGNED_LOG_COLS:
            xl = np.sign(x) * np.log1p(x.abs())
        else:
            xl = np.log1p(x.clip(lower=0))
        vacios = df[c].isna().mean() * 100
        if vacios == 0:
            continue  # sin vacíos el error no se activa
        filas.append({
            "variable": c,
            "pct_vacios": round(vacios, 2),
            "mediana_correcta_log": float(xl.median()),
            "valor_que_recibia": float(pre.median[c]),
            "p1_log": float(xl.quantile(0.01)),
            "p99_log": float(xl.quantile(0.99)),
        })
    res = pd.DataFrame(filas).sort_values("pct_vacios", ascending=False)
    res.to_csv(out, index=False)
    print(res.to_string(index=False))


if __name__ == "__main__":
    main()
