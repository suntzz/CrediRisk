"""Prueba de balance de variables mediante feature dropout uniforme.

No inventa porcentajes de importancia. Todas las entradas procesadas reciben la
misma probabilidad de enmascaramiento al entrenar y se comparan en VALIDATION.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from tensorflow import keras

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from experiments import build_custom_model
from predict import load_model_and_preprocessor


PHASE = "phase6_feature_balance"
MODEL_DIR = C.ARTIFACTS / PHASE
RATES = (0.05, 0.10)
SPECS = (
    {"name": "m1", "layers": [64, 32, 16], "activation": "relu", "dropout": 0.15, "dropout_layers": "first_two", "lr": 0.0005, "seed": 42},
    {"name": "m2", "layers": [32, 16], "activation": "leaky_relu", "dropout": 0.15, "dropout_layers": "all_except_last", "lr": 0.0005, "seed": 42},
    {"name": "m3", "layers": [64, 32, 16], "activation": "relu", "dropout": 0.20, "dropout_layers": "first_two", "lr": 0.001, "seed": 2026},
)


def predict(models, x):
    return np.mean([model.predict(x, verbose=0, batch_size=4096).ravel() for model in models], axis=0)


def metrics(y, p):
    return {
        "auc": float(roc_auc_score(y, p)), "pr_auc": float(average_precision_score(y, p)),
        "log_loss": float(log_loss(y, p)), "brier": float(brier_score_loss(y, p)),
    }


def train_one(rate, spec, x_train, y_train, x_val, y_val):
    folder = MODEL_DIR / f"dropout_{int(rate * 100):02d}"
    model_path = folder / f"{spec['name']}.keras"
    meta_path = folder / f"{spec['name']}.json"
    if model_path.exists() and meta_path.exists():
        return keras.models.load_model(model_path), json.loads(meta_path.read_text(encoding="utf-8"))
    folder.mkdir(parents=True, exist_ok=True)
    keras.utils.set_random_seed(spec["seed"])
    model = build_custom_model(
        n_features=x_train.shape[1], layers=spec["layers"], activation=spec["activation"],
        dropout_rate=spec["dropout"], dropout_layers=spec["dropout_layers"],
        learning_rate=spec["lr"], input_feature_dropout=rate,
    )
    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_auc", mode="max", patience=16, restore_best_weights=True, verbose=0),
        keras.callbacks.ReduceLROnPlateau(monitor="val_auc", mode="max", factor=0.5, patience=6, min_lr=1e-5, verbose=0),
    ]
    start = time.time()
    hist = model.fit(x_train, y_train, validation_data=(x_val, y_val), epochs=120, batch_size=128, callbacks=callbacks, verbose=0)
    best = int(np.argmax(hist.history["val_auc"]))
    details = {
        "feature_dropout_rate": rate, "model": spec["name"], "seed": spec["seed"],
        "epochs_trained": len(hist.history["loss"]), "best_epoch": best + 1,
        "best_val_auc": float(hist.history["val_auc"][best]),
        "train_loss": float(hist.history["loss"][best]), "val_loss": float(hist.history["val_loss"][best]),
        "loss_gap": float(hist.history["val_loss"][best] - hist.history["loss"][best]),
        "seconds": round(time.time() - start, 2),
    }
    model.save(model_path)
    meta_path.write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")
    return model, details


def main():
    d = np.load(C.ARTIFACTS / "splits.npz")
    x_train, y_train, x_val, y_val = d["X_train"], d["y_train"], d["X_val"], d["y_val"]
    _, baseline = load_model_and_preprocessor(use_ensemble=True)
    base = metrics(y_val, predict(baseline, x_val))
    rows = [{"candidate": "baseline_production", "feature_dropout_rate": 0.0, **base, "selected": True}]
    epoch_rows = []
    for rate in RATES:
        models = []
        for spec in SPECS:
            print(f"Entrenando feature dropout {rate:.0%} {spec['name']}...", flush=True)
            model, detail = train_one(rate, spec, x_train, y_train, x_val, y_val)
            models.append(model)
            epoch_rows.append(detail)
        candidate = metrics(y_val, predict(models, x_val))
        # Un candidato solo podría promoverse si mejora AUC y no sacrifica la
        # calibración. Se registra el resultado sin alterar producción aquí.
        promote = candidate["auc"] >= base["auc"] + 0.001 and candidate["brier"] <= base["brier"] + 0.001
        rows.append({"candidate": f"uniform_feature_dropout_{int(rate * 100):02d}", "feature_dropout_rate": rate, **candidate, "selected": promote})
    C.REPORTS.mkdir(exist_ok=True)
    pd.DataFrame(rows).sort_values(["auc", "brier"], ascending=[False, True]).to_csv(C.REPORTS / f"{PHASE}_validation.csv", index=False)
    pd.DataFrame(epoch_rows).to_csv(C.REPORTS / f"{PHASE}_epochs.csv", index=False)
    summary = {"method": "uniform_feature_dropout", "selection_split": "validation", "baseline": base, "candidates": rows}
    (C.REPORTS / f"{PHASE}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    winner = next((row["candidate"] for row in rows if row["candidate"] != "baseline_production" and row["selected"]), "baseline_production")
    print(f"Fase 6 finalizada. Ganador según guardrail: {winner}", flush=True)


if __name__ == "__main__":
    main()
