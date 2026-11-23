"""Fase 5: búsqueda reproducible enfocada en generalización, no memorización.

La selección usa exclusivamente VALIDATION. TEST se consulta una vez, sólo para el
candidato ya congelado. Todas las épocas reales, pérdidas y brechas train/validation
quedan en los reportes generados.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from tensorflow import keras

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from experiments import build_custom_model
from phase4_product_training import metric_row, product_thresholds, split_indices
from predict import load_model_and_preprocessor


PHASE = "phase5_generalization"
MODEL_DIR = C.ARTIFACTS / PHASE
SEEDS = (42, 2026, 7)
CONFIGS = {
    "elu_regularized": {
        "description": "ELU compacto, L2 y dropout; la configuración más estable de Fase 3.",
        "layers": [64, 32, 16], "activation": "elu", "dropout": 0.15,
        "dropout_layers": "first_two", "l2": 1e-4, "lr": 5e-4, "noise": 0.0,
    },
    "elu_input_noise": {
        "description": "ELU con ruido gaussiano leve de entrada para reducir coadaptación.",
        "layers": [64, 32, 16], "activation": "elu", "dropout": 0.15,
        "dropout_layers": "first_two", "l2": 1e-4, "lr": 5e-4, "noise": 0.03,
    },
    "wide_elu_regularized": {
        "description": "Mayor capacidad con regularización reforzada; se acepta solo si generaliza.",
        "layers": [96, 48, 24], "activation": "elu", "dropout": 0.20,
        "dropout_layers": "first_two", "l2": 3e-4, "lr": 4e-4, "noise": 0.02,
    },
    "compact_gelu": {
        "description": "Red compacta GELU como control de menor varianza.",
        "layers": [48, 24, 12], "activation": "gelu", "dropout": 0.10,
        "dropout_layers": "first_two", "l2": 1e-4, "lr": 5e-4, "noise": 0.0,
    },
}


def probs(models, x):
    return np.mean([m.predict(x, verbose=0, batch_size=4096).ravel() for m in models], axis=0)


def load_or_train(name, cfg, seed, x_train, y_train, x_val, y_val):
    path = MODEL_DIR / name / f"seed_{seed}.keras"
    history_path = MODEL_DIR / name / f"seed_{seed}.json"
    if path.exists() and history_path.exists():
        return keras.models.load_model(path), json.loads(history_path.read_text())
    path.parent.mkdir(parents=True, exist_ok=True)
    keras.utils.set_random_seed(seed)
    model = build_custom_model(
        n_features=x_train.shape[1], layers=cfg["layers"], activation=cfg["activation"],
        dropout_rate=cfg["dropout"], dropout_layers=cfg["dropout_layers"], l2_reg=cfg["l2"],
        optimizer_name="Adam", learning_rate=cfg["lr"], input_noise_std=cfg["noise"],
    )
    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_auc", mode="max", patience=16, restore_best_weights=True, verbose=0),
        keras.callbacks.ReduceLROnPlateau(monitor="val_auc", mode="max", factor=0.5, patience=6, min_lr=1e-5, verbose=0),
    ]
    started = time.time()
    hist = model.fit(x_train, y_train, validation_data=(x_val, y_val), epochs=120, batch_size=128, callbacks=callbacks, verbose=0)
    best = int(np.argmax(hist.history["val_auc"]))
    summary = {
        "seed": seed, "epochs_trained": len(hist.history["loss"]), "best_epoch": best + 1,
        "best_val_auc": float(hist.history["val_auc"][best]), "best_train_loss": float(hist.history["loss"][best]),
        "best_val_loss": float(hist.history["val_loss"][best]), "loss_gap": float(hist.history["val_loss"][best] - hist.history["loss"][best]),
        "elapsed_seconds": round(time.time() - started, 2),
    }
    model.save(path)
    history_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return model, summary


def candidate_metrics(y, p):
    return {
        "auc": float(roc_auc_score(y, p)), "pr_auc": float(average_precision_score(y, p)),
        "log_loss": float(log_loss(y, p)), "brier": float(brier_score_loss(y, p)),
        **metric_row(y, p, 0.5),
    }


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    C.REPORTS.mkdir(exist_ok=True)
    d = np.load(C.ARTIFACTS / "splits.npz")
    x_train, y_train, x_val, y_val, x_test, y_test = (d[k] for k in ("X_train", "y_train", "X_val", "y_val", "X_test", "y_test"))
    df = pd.read_csv(C.DATA_CSV, encoding="utf-8-sig")
    _, val_idx, test_idx = split_indices(df[C.TARGET].to_numpy("float32"))
    product_val = df.iloc[val_idx]["linea_negocio"].reset_index(drop=True)
    product_test = df.iloc[test_idx]["linea_negocio"].reset_index(drop=True)

    _, baseline_models = load_model_and_preprocessor(use_ensemble=True)
    candidates = {"baseline_production": {"models": baseline_models, "histories": [], "config": None}}
    history_rows = []
    for name, cfg in CONFIGS.items():
        models, summaries = [], []
        for seed in SEEDS:
            print(f"Entrenando {name}, semilla {seed}...", flush=True)
            model, summary = load_or_train(name, cfg, seed, x_train, y_train, x_val, y_val)
            models.append(model)
            summaries.append(summary)
            history_rows.append({"candidate": name, **summary, **cfg})
        candidates[name] = {"models": models, "histories": summaries, "config": cfg}

    selection_rows, evaluated = [], {}
    for name, data in candidates.items():
        p = probs(data["models"], x_val)
        metrics = candidate_metrics(y_val, p)
        thresholds, product_rows = product_thresholds(product_val, y_val, p)
        evaluated[name] = {**data, "p_val": p, "metrics": metrics, "thresholds": thresholds}
        selection_rows.append({
            "candidate": name, **metrics,
            "mean_product_balanced_accuracy": float(np.mean([r["balanced_accuracy"] for r in product_rows])),
            "mean_best_epoch": float(np.mean([h["best_epoch"] for h in data["histories"]])) if data["histories"] else np.nan,
            "mean_loss_gap": float(np.mean([h["loss_gap"] for h in data["histories"]])) if data["histories"] else np.nan,
        })
    baseline = evaluated["baseline_production"]["metrics"]
    # Promoción prudente: mejor ranking y sin degradar calibración. La brecha de
    # generalización debe ser moderada para evitar elegir una red memorizada.
    eligible = []
    for name, data in evaluated.items():
        row = next(r for r in selection_rows if r["candidate"] == name)
        stable = np.isnan(row["mean_loss_gap"]) or row["mean_loss_gap"] <= 0.06
        if data["metrics"]["auc"] >= baseline["auc"] + 0.001 and data["metrics"]["brier"] <= baseline["brier"] + 0.001 and stable:
            eligible.append(name)
    selected_name = max(eligible, key=lambda n: (evaluated[n]["metrics"]["auc"], -evaluated[n]["metrics"]["brier"])) if eligible else "baseline_production"
    for row in selection_rows:
        row["eligible_for_promotion"] = row["candidate"] in eligible
        row["selected"] = row["candidate"] == selected_name
    pd.DataFrame(selection_rows).sort_values(["auc", "brier"], ascending=[False, True]).to_csv(C.REPORTS / f"{PHASE}_validation.csv", index=False)
    pd.DataFrame(history_rows).to_csv(C.REPORTS / f"{PHASE}_epochs.csv", index=False)

    selected = evaluated[selected_name]
    p_test = probs(selected["models"], x_test)
    test_rows = [{"linea_negocio": "GLOBAL", "n_test": len(y_test), **candidate_metrics(y_test, p_test)}]
    for product, cfg in selected["thresholds"].items():
        mask = product_test.to_numpy() == product
        test_rows.append({"linea_negocio": product, "n_test": int(mask.sum()), **metric_row(y_test[mask], p_test[mask], cfg["threshold"])})
    pd.DataFrame(test_rows).to_csv(C.REPORTS / f"{PHASE}_test.csv", index=False)

    policy = {
        "version": 2, "status": "validated", "phase": PHASE, "selected_candidate": selected_name,
        "selection_split": "validation", "objective": "balanced_accuracy", "default_threshold": float(C.THRESHOLD),
        "thresholds": selected["thresholds"],
        "unsupported_products": {"Mortgage loans": "No hay registros etiquetados de crédito hipotecario en el dataset actual."},
        "test_metrics_file": f"reports/{PHASE}_test.csv",
    }
    write_json(C.ARTIFACTS / "product_threshold_policy.json", policy)
    write_json(C.REPORTS / f"{PHASE}_policy.json", policy)
    if selected_name == "baseline_production":
        models = json.loads((C.ARTIFACTS / "ensemble_manifest.json").read_text(encoding="utf-8"))["models"]
    else:
        models = [{"file": str((MODEL_DIR / selected_name / f"seed_{seed}.keras").relative_to(C.ARTIFACTS)), "seed": seed, **selected["config"]} for seed in SEEDS]
    write_json(C.ARTIFACTS / "production_manifest.json", {"ensemble_name": f"CrediRisk_{PHASE}", "source_candidate": selected_name, "weights": "Promedio simple", "models": models})
    write_json(C.REPORTS / f"{PHASE}_summary.json", {"selected_candidate": selected_name, "baseline": baseline, "selected_validation": selected["metrics"], "policy": policy})
    print(f"Fase 5 completada; seleccionado: {selected_name}", flush=True)


if __name__ == "__main__":
    main()
