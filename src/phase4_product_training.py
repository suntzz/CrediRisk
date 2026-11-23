"""Fase 4: selección reproducible de regularización del score y umbrales por producto.

No modifica el dataset ni los modelos históricos. Compara el ensamble congelado
contra variantes que enmascaran parcialmente score_crediticio durante entrenamiento.
La selección se hace SOLO en validation; TEST se consulta una única vez al final.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from tensorflow import keras

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from experiments import build_custom_model
from predict import load_model_and_preprocessor


# Corrida solicitada: enmascara el score en exactamente el 32 % de las filas de
# entrenamiento. No equivale a asignar un peso fijo a una neurona (eso no es
# interpretable en una red), pero sí limita explícitamente su disponibilidad.
PHASE = "phase4_score32"
OUT_DIR = C.ARTIFACTS / PHASE
REPORT_PREFIX = C.REPORTS / PHASE
PRODUCTS = ("Cash loans", "Revolving loans")

# Las tres redes del ensamble vigente. Se conserva la diversidad que ya superó
# las fases 1-3; solo cambia la regularización de entrada durante entrenamiento.
MODEL_SPECS = (
    {"name": "m1", "layers": [64, 32, 16], "activation": "relu", "dropout": 0.15,
     "dropout_layers": "first_two", "optimizer": "Adam", "lr": 0.0005, "seed": 42},
    {"name": "m2", "layers": [32, 16], "activation": "leaky_relu", "dropout": 0.15,
     "dropout_layers": "all_except_last", "optimizer": "Adam", "lr": 0.0005, "seed": 42},
    {"name": "m3", "layers": [64, 32, 16], "activation": "relu", "dropout": 0.20,
     "dropout_layers": "first_two", "optimizer": "Adam", "lr": 0.001, "seed": 2026},
)
MASK_RATES = (0.32,)


def split_indices(y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    idx = np.arange(len(y))
    train_idx, temp_idx = train_test_split(
        idx, test_size=C.VAL_FRAC + C.TEST_FRAC, stratify=y, random_state=C.SPLIT_SEED
    )
    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=C.TEST_FRAC / (C.VAL_FRAC + C.TEST_FRAC),
        stratify=y[temp_idx],
        random_state=C.SPLIT_SEED,
    )
    return train_idx, val_idx, test_idx


def probabilities(models, X: np.ndarray) -> np.ndarray:
    return np.mean([m.predict(X, verbose=0, batch_size=4096).ravel() for m in models], axis=0)


def metric_row(y: np.ndarray, p: np.ndarray, threshold: float) -> dict[str, float]:
    pred = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    sensitivity = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return {
        "threshold": float(threshold), "auc": float(roc_auc_score(y, p)),
        "pr_auc": float(average_precision_score(y, p)), "log_loss": float(log_loss(y, p)),
        "brier": float(brier_score_loss(y, p)), "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)), "f1": float(f1_score(y, pred, zero_division=0)),
        "balanced_accuracy": float((sensitivity + specificity) / 2),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "approval_rate": float(pred.mean()),
    }


def select_threshold(y: np.ndarray, p: np.ndarray) -> tuple[float, dict[str, float]]:
    # Rejilla fijada antes de consultar test. Desempata por accuracy y luego por
    # el corte más conservador para no favorecer aprobaciones riesgosas por azar.
    candidates = [(round(float(t), 2), metric_row(y, p, float(t))) for t in np.arange(0.25, 0.751, 0.01)]
    threshold, metrics = max(candidates, key=lambda item: (
        item[1]["balanced_accuracy"], item[1]["accuracy"], item[0]
    ))
    return float(f"{threshold:.2f}"), metrics


def product_thresholds(products: pd.Series, y: np.ndarray, p: np.ndarray) -> tuple[dict, list[dict]]:
    policy, rows = {}, []
    for product in PRODUCTS:
        mask = products.to_numpy() == product
        if mask.sum() < 100 or np.unique(y[mask]).size < 2:
            raise ValueError(f"No hay suficientes registros de validación para {product}.")
        threshold, metrics = select_threshold(y[mask], p[mask])
        # `metric_row` conserva el valor de la rejilla para auditoría; la política
        # expone el corte normalizado a dos decimales.
        policy[product] = {"n_validation": int(mask.sum()), **metrics, "threshold": threshold}
        rows.append({"linea_negocio": product, **policy[product]})
    return policy, rows


def score_importance(models, X: np.ndarray, y: np.ndarray, column: int, repeats: int = 3) -> float:
    base = roc_auc_score(y, probabilities(models, X))
    rng = np.random.default_rng(20261123)
    drops = []
    for _ in range(repeats):
        shuffled = X.copy()
        shuffled[:, column] = shuffled[rng.permutation(len(shuffled)), column]
        drops.append(base - roc_auc_score(y, probabilities(models, shuffled)))
    return float(np.mean(drops))


def fit_masked_ensemble(X_train, y_train, X_val, y_val, mask_rate: float, score_column: int, candidate_dir: Path):
    candidate_dir.mkdir(parents=True, exist_ok=True)
    existing = [candidate_dir / f"{spec['name']}.keras" for spec in MODEL_SPECS]
    if all(path.exists() for path in existing):
        print(f"Reutilizando pesos ya entrenados para {candidate_dir.name}...", flush=True)
        return [keras.models.load_model(path) for path in existing]
    models = []
    for spec in MODEL_SPECS:
        keras.utils.set_random_seed(spec["seed"])
        # Cero es la media tras StandardScaler: simula score no disponible sin
        # inventar una puntuación extrema ni alterar el caso de inferencia real.
        X_fit = X_train.copy()
        rng = np.random.default_rng(10_000 + spec["seed"] + int(mask_rate * 1000))
        masked = rng.random(len(X_fit)) < mask_rate
        X_fit[masked, score_column] = 0.0
        model = build_custom_model(
            n_features=X_fit.shape[1], layers=spec["layers"], activation=spec["activation"],
            dropout_rate=spec["dropout"], dropout_layers=spec["dropout_layers"],
            optimizer_name=spec["optimizer"], learning_rate=spec["lr"],
        )
        callbacks = [
            keras.callbacks.EarlyStopping(monitor="val_auc", mode="max", patience=12, restore_best_weights=True, verbose=0),
            keras.callbacks.ReduceLROnPlateau(monitor="val_auc", mode="max", factor=0.5, patience=5, min_lr=1e-5, verbose=0),
        ]
        model.fit(X_fit, y_train, validation_data=(X_val, y_val), epochs=100, batch_size=128, callbacks=callbacks, verbose=0)
        filename = f"{spec['name']}.keras"
        model.save(candidate_dir / filename)
        models.append(model)
    return models


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    started = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    C.REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(C.DATA_CSV, encoding="utf-8-sig")
    y = df[C.TARGET].to_numpy("float32")
    train_idx, val_idx, test_idx = split_indices(y)
    pre = joblib.load(C.ARTIFACTS / "preprocessor.joblib")
    X = pre.transform(df)
    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    products_val = df.iloc[val_idx]["linea_negocio"].reset_index(drop=True)
    products_test = df.iloc[test_idx]["linea_negocio"].reset_index(drop=True)
    score_column = pre.feature_names.index("score_crediticio")

    baseline_pre, baseline_models = load_model_and_preprocessor(use_ensemble=True)
    del baseline_pre
    candidates = {"baseline_historico": baseline_models}
    for rate in MASK_RATES:
        name = f"score_mask_{int(rate * 100):02d}"
        print(f"Entrenando {name}...", flush=True)
        candidates[name] = fit_masked_ensemble(X_train, y_train, X_val, y_val, rate, score_column, OUT_DIR / name)

    rows, candidate_data = [], {}
    baseline_auc = None
    baseline_brier = None
    for name, models in candidates.items():
        p_val = probabilities(models, X_val)
        global_metrics = metric_row(y_val, p_val, 0.5)
        thresholds, threshold_rows = product_thresholds(products_val, y_val, p_val)
        score_drop = score_importance(models, X_val, y_val, score_column)
        data = {"models": models, "p_val": p_val, "metrics": global_metrics,
                "thresholds": thresholds, "score_auc_drop": score_drop}
        candidate_data[name] = data
        if name == "baseline_historico":
            baseline_auc, baseline_brier = global_metrics["auc"], global_metrics["brier"]
        rows.append({"candidate": name, **global_metrics, "score_auc_drop": score_drop,
                     "mean_product_balanced_accuracy": float(np.mean([r["balanced_accuracy"] for r in threshold_rows]))})

    # Guardrail: ningún candidato que degrade materialmente ranking o calibración
    # puede desplazar al ensamble histórico. Entre los aptos se prioriza AUC y Brier.
    eligible = [
        (name, data) for name, data in candidate_data.items()
        if data["metrics"]["auc"] >= baseline_auc - 0.002
        and data["metrics"]["brier"] <= baseline_brier + 0.002
    ]
    selected_name, selected = max(eligible, key=lambda item: (
        item[1]["metrics"]["auc"], -item[1]["metrics"]["brier"], -item[1]["score_auc_drop"]
    ))
    comparison = pd.DataFrame(rows).sort_values(["auc", "brier"], ascending=[False, True])
    comparison["eligible_for_promotion"] = comparison["candidate"].isin([name for name, _ in eligible])
    comparison["selected"] = comparison["candidate"].eq(selected_name)
    comparison.to_csv(REPORT_PREFIX.with_name(f"{PHASE}_candidate_comparison.csv"), index=False)

    # TEST se usa una sola vez, después de congelar candidato y umbrales.
    p_test = probabilities(selected["models"], X_test)
    test_rows = []
    for product, cfg in selected["thresholds"].items():
        mask = products_test.to_numpy() == product
        test_rows.append({"linea_negocio": product, "n_test": int(mask.sum()),
                          **metric_row(y_test[mask], p_test[mask], cfg["threshold"])} )
    test_rows.append({"linea_negocio": "GLOBAL", "n_test": int(len(y_test)), **metric_row(y_test, p_test, 0.5)})
    pd.DataFrame(test_rows).to_csv(REPORT_PREFIX.with_name(f"{PHASE}_product_test_metrics.csv"), index=False)

    policy = {
        "version": 1, "status": "validated", "phase": PHASE,
        "selected_candidate": selected_name, "selection_split": "validation",
        "objective": "balanced_accuracy", "default_threshold": float(C.THRESHOLD),
        "thresholds": selected["thresholds"],
        "unsupported_products": {"Mortgage loans": "No hay registros etiquetados de crédito hipotecario en el dataset actual."},
        "score_importance": {"method": "permutation_auc_drop_validation", "score_auc_drop": selected["score_auc_drop"]},
        "test_metrics_file": f"reports/{PHASE}_product_test_metrics.csv",
    }
    write_json(C.ARTIFACTS / "product_threshold_policy.json", policy)
    write_json(REPORT_PREFIX.with_name(f"{PHASE}_product_policy.json"), policy)

    # El manifiesto permite promover una variante sin destruir artifacts/ensemble_models.
    if selected_name != "baseline_historico":
        model_root = OUT_DIR / selected_name
        model_files = [{"file": str((model_root / f"{spec['name']}.keras").relative_to(C.ARTIFACTS)), **spec} for spec in MODEL_SPECS]
    else:
        model_files = json.loads((C.ARTIFACTS / "ensemble_manifest.json").read_text(encoding="utf-8"))["models"]
    production_manifest = {
        "ensemble_name": f"Ensemble_Top3_Diverso_{PHASE}", "source_candidate": selected_name,
        "weights": "Promedio aritmético simple (1/3 cada uno)", "models": model_files,
    }
    write_json(C.ARTIFACTS / "production_manifest.json", production_manifest)
    write_json(REPORT_PREFIX.with_name(f"{PHASE}_summary.json"), {
        "selected_candidate": selected_name, "baseline_auc": baseline_auc,
        "selected_val_auc": selected["metrics"]["auc"], "elapsed_seconds": round(time.time() - started, 1),
        "policy": policy,
    })
    print(f"Fase 4 finalizada. Candidato seleccionado: {selected_name}", flush=True)


if __name__ == "__main__":
    main()
