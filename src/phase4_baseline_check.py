"""Fase 4 - Paso 0: reproduce la Log Loss del modelo congelado y verifica los splits."""
import os
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score, brier_score_loss
from sklearn.model_selection import train_test_split
from tensorflow import keras

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

d = np.load(C.ARTIFACTS / "splits.npz")
df = pd.read_csv(C.DATA_CSV, encoding="utf-8-sig")
y = df[C.TARGET].to_numpy("float32")
idx = np.arange(len(df))
tr, tmp = train_test_split(idx, test_size=C.VAL_FRAC + C.TEST_FRAC, stratify=y, random_state=C.SPLIT_SEED)
va, te = train_test_split(tmp, test_size=C.TEST_FRAC / (C.VAL_FRAC + C.TEST_FRAC), stratify=y[tmp], random_state=C.SPLIT_SEED)
assert (te == d["idx_test"]).all(), "indices de test no coinciden"
assert (y[va] == d["y_val"]).all() and (y[tr] == d["y_train"]).all()
print("Splits reconstruidos OK:", len(tr), len(va), len(te), "prevalencia", y.mean().round(4))

models = ["cfg_c_s42", "cfg_b_leaky_s42", "cfg_base_s2026"]
pv, pt = [], []
for m in models:
    k = keras.models.load_model(C.ARTIFACTS / "ensemble_models" / f"{m}.keras")
    pv.append(k.predict(d["X_val"], verbose=0, batch_size=4096).ravel())
    pt.append(k.predict(d["X_test"], verbose=0, batch_size=4096).ravel())
    print(f"{m:18s} val LL={log_loss(d['y_val'], pv[-1]):.5f}  test LL={log_loss(d['y_test'], pt[-1]):.5f}")
pv, pt = np.mean(pv, 0), np.mean(pt, 0)
for name, yy, p in [("VAL", d["y_val"], pv), ("TEST", d["y_test"], pt)]:
    print(f"Ensemble_Top3_Diverso {name}: LL={log_loss(yy, p):.5f} AUC={roc_auc_score(yy, p):.5f} Brier={brier_score_loss(yy, p):.5f}")

print("\nResumen dataset:")
print(df.isna().mean().sort_values(ascending=False).head(10).round(3))
print(df.describe().T[["mean", "std", "min", "max"]].round(2))
print(df.nunique().sort_values())
