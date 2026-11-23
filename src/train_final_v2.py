"""Entrena el modelo final v2 con train+val completo (42.202 filas) y lo guarda en artifacts/v2/.

Lee los pesos de artifacts/v2/blend_choice.json (salida de final_blend.py).
No toca ningún artefacto de producción.
Uso: python src/train_final_v2.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
import cv_protocol as P
from cv_candidates import HGB_B, PreprocessorV2, RawFrame, _hgb
from model_v2 import V2, FinalModelV2

HGB_SEEDS = (42, 7, 2026, 1, 21)


def train_mlps(pre, df, y, prefix):
    from sklearn.model_selection import train_test_split
    from tensorflow import keras
    from experiments import build_custom_model
    X = pre.transform(df)
    fit_i, es_i = train_test_split(np.arange(len(y)), test_size=P.INNER_VAL_FRAC, stratify=y, random_state=C.SPLIT_SEED)
    files = []
    for spec in P.MLP_SPECS:
        keras.backend.clear_session()
        keras.utils.set_random_seed(spec["seed"])
        m = build_custom_model(n_features=X.shape[1], layers=spec["layers"], activation=spec["activation"],
                               dropout_rate=spec["dropout"], dropout_layers=spec["dropout_layers"], learning_rate=spec["lr"])
        cb = [keras.callbacks.EarlyStopping(monitor=spec["monitor"], mode=spec["mode"], patience=12, restore_best_weights=True),
              keras.callbacks.ReduceLROnPlateau(monitor=spec["monitor"], mode=spec["mode"], factor=0.5, patience=5, min_lr=1e-5)]
        m.fit(X[fit_i], y[fit_i], validation_data=(X[es_i], y[es_i]), epochs=80, batch_size=128, callbacks=cb, verbose=0)
        f = f"{prefix}{spec['name']}.keras"
        m.save(V2 / f)
        files.append(f)
        print(f"  red {f} lista", flush=True)
    return files


def main():
    t0 = time.time()
    choice = json.loads((V2 / "blend_choice.json").read_text(encoding="utf-8"))
    df, y, _ = P.load_dev()
    model = FinalModelV2(choice)

    model.frame = RawFrame(True).fit(df)
    X = model.frame.transform(df)
    model.hgbs = [_hgb(HGB_B, s).fit(X, y) for s in HGB_SEEDS]
    print(f"HGB con score x{len(HGB_SEEDS)} ({time.time() - t0:.0f}s)", flush=True)
    model.frame_ns = RawFrame(True, drop=(P.SCORE_COL,)).fit(df)
    model.hgbs_ns = [_hgb(HGB_B, 42).fit(model.frame_ns.transform(df), y)]
    print(f"HGB sin score ({time.time() - t0:.0f}s)", flush=True)

    model.net_pre, model.net_files = {}, {}
    comp = choice["componente_redes"]
    if comp == "neural":  # contingencia: redes de producción tal cual (solo lectura)
        model.net_pre["redes"] = joblib.load(C.ARTIFACTS / "preprocessor.joblib")
        man = json.loads((C.ARTIFACTS / "production_manifest.json").read_text())
        model.net_files["redes"] = [str(Path("..") / m["file"]) for m in man["models"]]
    else:
        pre = PreprocessorV2(ratios=(comp != "fix_neural")).fit(df)
        model.net_pre["redes"] = pre
        model.net_files["redes"] = train_mlps(pre, df, y, "redes_")
    if choice.get("componente_redes_sin_score") and choice["peso_hgb_sin_score"] < 1:
        pre_ns = PreprocessorV2(ratios=True, drop=(P.SCORE_COL,)).fit(df)
        model.net_pre["redes_sin_score"] = pre_ns
        model.net_files["redes_sin_score"] = train_mlps(pre_ns, df, y, "redes_sin_score_")
    joblib.dump(model, V2 / "final_model.joblib")

    manifest = {
        "nombre": "CrediRisk híbrido v2",
        "arquitectura": "HistGradientBoosting + 3 redes MLP (cv_protocol.MLP_SPECS), con y sin score",
        "formula": "final = peso_con_score*(w*HGB + (1-w)*redes) + (1-peso_con_score)*(w2*HGB_sin_score + (1-w2)*redes_sin_score)",
        "peso_hgb_con_score_w": choice["peso_hgb_con_score"], "peso_hgb_sin_score_w2": choice["peso_hgb_sin_score"],
        "peso_con_score": choice["peso_con_score"], "peso_con_score_revolving": choice.get("peso_con_score_revolving"),
        "hgb_config": HGB_B, "hgb_semillas_con_score": list(HGB_SEEDS), "hgb_semillas_sin_score": [42],
        "redes": choice["redes"], "redes_specs": list(P.MLP_SPECS), "archivos_redes": model.net_files,
        "filas_entrenamiento": int(len(y)),
        "auc_validacion_cruzada": choice["auc_oof_final"], "auc_validacion_cruzada_produccion": choice["auc_oof_produccion"],
        "diferencia_vs_produccion_ic95": choice["diff_vs_produccion"],
        "dependencia_score_pct": choice["dependencia_final_pct"],
        "calibrador": "calibrador_isotonico.joblib", "politica": "product_threshold_policy.json",
        "nota": "AUC de validación cruzada sobre la repetición 0 (5 pliegues). En la validación cruzada el HGB con score usó 3 semillas; aquí 5.",
    }
    (V2 / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    print(f"Listo en {time.time() - t0:.0f}s -> {V2}")


if __name__ == "__main__":
    main()
