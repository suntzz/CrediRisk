"""Entrena y promueve el híbrido neuronal + HistGradientBoosting validado."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from phase4_product_training import metric_row, product_thresholds, split_indices
from predict import load_model_and_preprocessor


PHASE = "phase7_hybrid"
HGB_WEIGHT = 0.65
HGB_CONFIG = {
    "max_iter": 450, "learning_rate": 0.04, "max_leaf_nodes": 31,
    "min_samples_leaf": 40, "l2_regularization": 3.0, "early_stopping": True,
    "validation_fraction": 0.12, "n_iter_no_change": 25, "random_state": 42,
}


def neural_probabilities(models, X):
    return np.mean([model.predict(X, verbose=0, batch_size=4096).ravel() for model in models], axis=0)


def metrics(y, p):
    return {
        "auc": float(roc_auc_score(y, p)), "pr_auc": float(average_precision_score(y, p)),
        "log_loss": float(log_loss(y, p)), "brier": float(brier_score_loss(y, p)), **metric_row(y, p, 0.5),
    }


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    d = np.load(C.ARTIFACTS / "splits.npz")
    X_train, y_train, X_val, y_val, X_test, y_test = (d[key] for key in ("X_train", "y_train", "X_val", "y_val", "X_test", "y_test"))
    _, neural_models = load_model_and_preprocessor(use_ensemble=True)
    hgb = HistGradientBoostingClassifier(**HGB_CONFIG).fit(X_train, y_train)
    hgb_path = C.ARTIFACTS / "hybrid_hgb.joblib"
    joblib.dump(hgb, hgb_path)
    p_neural_val = neural_probabilities(neural_models, X_val)
    p_hgb_val = hgb.predict_proba(X_val)[:, 1]
    p_hybrid_val = HGB_WEIGHT * p_hgb_val + (1.0 - HGB_WEIGHT) * p_neural_val
    rows = [
        {"candidate": "ensemble_neural", **metrics(y_val, p_neural_val)},
        {"candidate": "hist_gradient_boosting", **metrics(y_val, p_hgb_val)},
        {"candidate": "hybrid_65_hgb_35_neural", **metrics(y_val, p_hybrid_val)},
    ]
    C.REPORTS.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(C.REPORTS / f"{PHASE}_validation.csv", index=False)
    df = pd.read_csv(C.DATA_CSV, encoding="utf-8-sig")
    _, val_idx, test_idx = split_indices(df[C.TARGET].to_numpy("float32"))
    thresholds, _ = product_thresholds(df.iloc[val_idx]["linea_negocio"].reset_index(drop=True), y_val, p_hybrid_val)
    p_hybrid_test = HGB_WEIGHT * hgb.predict_proba(X_test)[:, 1] + (1.0 - HGB_WEIGHT) * neural_probabilities(neural_models, X_test)
    test_rows = [{"linea_negocio": "GLOBAL", "n_test": len(y_test), **metrics(y_test, p_hybrid_test)}]
    products_test = df.iloc[test_idx]["linea_negocio"].to_numpy()
    for product, setting in thresholds.items():
        mask = products_test == product
        test_rows.append({"linea_negocio": product, "n_test": int(mask.sum()), **metric_row(y_test[mask], p_hybrid_test[mask], setting["threshold"])})
    pd.DataFrame(test_rows).to_csv(C.REPORTS / f"{PHASE}_test.csv", index=False)
    policy = {
        "version": 3, "status": "validated", "phase": PHASE, "selected_candidate": "hybrid_65_hgb_35_neural",
        "selection_split": "validation", "objective": "balanced_accuracy", "default_threshold": float(C.THRESHOLD),
        "thresholds": thresholds, "unsupported_products": {"Mortgage loans": "No hay registros etiquetados de crédito hipotecario en el dataset actual."},
        "test_metrics_file": f"reports/{PHASE}_test.csv",
    }
    write_json(C.ARTIFACTS / "product_threshold_policy.json", policy)
    neural_manifest = json.loads((C.ARTIFACTS / "ensemble_manifest.json").read_text(encoding="utf-8"))
    manifest = {
        "ensemble_name": "CrediRisk_Hybrid_HGB_Neural", "source_candidate": "hybrid_65_hgb_35_neural",
        "weights": "0.65 HistGradientBoosting + 0.35 Ensemble Top-3", "models": neural_manifest["models"],
        "hybrid": {"hgb_model_file": "hybrid_hgb.joblib", "hgb_weight": HGB_WEIGHT, "config": HGB_CONFIG, "n_iter": int(hgb.n_iter_)},
    }
    write_json(C.ARTIFACTS / "production_manifest.json", manifest)
    write_json(C.REPORTS / f"{PHASE}_policy.json", policy)
    write_json(C.REPORTS / f"{PHASE}_summary.json", {"validation": rows, "test": test_rows, "manifest": manifest})
    print(f"Híbrido promovido; HGB iteraciones: {hgb.n_iter_}")


if __name__ == "__main__":
    main()
