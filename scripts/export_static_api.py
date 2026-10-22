#!/usr/bin/env python3
"""
Exporta los artefactos estáticos de la API (salud, métricas, ejemplo y pesos reales del
preprocesador y del ensamble neuronal Keras) a `frontend/public/api-static/` para que
la aplicación funcione al 100% en GitHub Pages sin requerir un servidor Python activo.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import config as C
from api import health_check, get_sample_applicant, get_metrics
from predict import load_model_and_preprocessor

OUT_DIR = ROOT / "frontend" / "public" / "api-static"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def export_keras_model(model):
    layers_out = []
    for layer in model.layers:
        cls_name = layer.__class__.__name__
        cfg = layer.get_config()
        if cls_name == "Dense":
            W, b = layer.get_weights()
            layers_out.append({
                "type": "Dense",
                "activation": cfg.get("activation", "linear"),
                "W": [[round(float(v), 7) for v in row] for row in W.tolist()],
                "b": [round(float(v), 7) for v in b.tolist()],
            })
        elif cls_name == "LeakyReLU":
            layers_out.append({
                "type": "LeakyReLU",
                "negative_slope": float(cfg.get("negative_slope", 0.1)),
            })
    return layers_out


def main():
    # 1. Health, Sample, Metrics
    (OUT_DIR / "health.json").write_text(json.dumps(health_check(), ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "sample.json").write_text(json.dumps(get_sample_applicant(), ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "metrics.json").write_text(json.dumps(get_metrics(), ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Preprocessor + Neural Network Ensemble & Single Model
    pre, ensemble_models = load_model_and_preprocessor(use_ensemble=True)
    _, single_model = load_model_and_preprocessor(use_ensemble=False)

    bundle = {
        "threshold": float(C.THRESHOLD),
        "preprocessor": {
            "drop_cols": list(C.DROP_COLS),
            "target": C.TARGET,
            "cat_cols": list(C.CAT_COLS),
            "flag_cols": list(C.FLAG_COLS),
            "skew_cols": list(C.SKEW_COLS),
            "signed_log_cols": list(C.SIGNED_LOG_COLS),
            "rare_to_otro": {k: list(v) for k, v in C.RARE_TO_OTRO.items()},
            "num_cols": list(pre.num_cols),
            "dummy_cols": list(pre.dummy_cols),
            "lo": {k: float(v) for k, v in pre.lo.to_dict().items()},
            "hi": {k: float(v) for k, v in pre.hi.to_dict().items()},
            "median": {k: float(v) for k, v in pre.median.to_dict().items()},
            "scaler_mean": [round(float(v), 8) for v in pre.scaler.mean_.tolist()],
            "scaler_scale": [round(float(v), 8) for v in pre.scaler.scale_.tolist()],
        },
        "ensemble_models": [export_keras_model(m) for m in ensemble_models],
        "single_model": export_keras_model(single_model),
    }

    (OUT_DIR / "model_bundle.json").write_text(
        json.dumps(bundle, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"✓ Exportados artefactos estáticos en {OUT_DIR}")


if __name__ == "__main__":
    main()
