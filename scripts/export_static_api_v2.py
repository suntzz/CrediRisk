#!/usr/bin/env python3
"""
Exporta el modelo v2 (artifacts/v2) a `frontend/public/api-static/model_bundle_v2.json`
para que la web en GitHub Pages prediga con él dentro del navegador.

El bundle contiene: las razones entre variables, los 6 árboles HistGradientBoosting
(5 con score + 1 sin score) con sus divisiones categóricas, los dos preprocesadores
de las redes, las 6 redes, el calibrador isotónico y la política por costo.

Uso: python scripts/export_static_api_v2.py [--paridad N]
     --paridad N guarda además N filas reales con la predicción de Python para comparar
     contra la inferencia del navegador (frontend/scripts/paridad_v2.mjs).
"""
import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import config as C  # noqa: E402
import model_v2  # noqa: E402


def export_keras_model(model):
    """Misma serialización que scripts/export_static_api.py (Dense y LeakyReLU; Dropout no actúa al predecir)."""
    layers_out = []
    for layer in model.layers:
        cls_name = layer.__class__.__name__
        cfg = layer.get_config()
        if cls_name == "Dense":
            W, b = layer.get_weights()
            layers_out.append({"type": "Dense", "activation": cfg.get("activation", "linear"),
                               "W": [[round(float(v), 7) for v in row] for row in W.tolist()],
                               "b": [round(float(v), 7) for v in b.tolist()]})
        elif cls_name == "LeakyReLU":
            layers_out.append({"type": "LeakyReLU", "negative_slope": float(cfg.get("negative_slope", 0.1))})
        elif cls_name not in ("InputLayer", "Dropout"):
            raise ValueError(f"Capa no soportada en el navegador: {cls_name}")
    return layers_out

OUT_DIR = ROOT / "frontend" / "public" / "api-static"


def r(v, d=9):
    """Número apto para JSON: NaN -> null; ±inf -> ±1e308 (mismo resultado al comparar)."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    v = float(v)
    if np.isinf(v):
        return 1e308 if v > 0 else -1e308
    return v if d is None else round(v, d)


def export_hgb(model):
    """Árbol con divisiones numéricas y categóricas, en el orden interno de sklearn
    (primero las categóricas codificadas, luego las numéricas)."""
    pre = model._preprocessor
    names = list(model.feature_names_in_)
    cat_mask = np.asarray(model.is_categorical_)
    order = [n for n, c in zip(names, cat_mask) if c] + [n for n, c in zip(names, cat_mask) if not c]
    cats = {n: list(map(str, c)) for n, c in zip([n for n, c in zip(names, cat_mask) if c],
                                                  pre.named_transformers_["encoder"].categories_)}
    trees = []
    for (pred,) in model._predictors:
        bits = pred.raw_left_cat_bitsets.tolist()
        trees.append([
            [int(n["is_leaf"]), int(n["feature_idx"]), r(n["num_threshold"], None), int(n["left"]), int(n["right"]),
             int(n["missing_go_to_left"]), r(n["value"]), int(n["is_categorical"]),
             bits[int(n["bitset_idx"])] if n["is_categorical"] and not n["is_leaf"] else 0]
            for n in pred.nodes
        ])
    return {"features": order, "categories": cats, "baseline": float(model._baseline_prediction[0, 0]), "trees": trees}


def export_pre(pre):
    return {
        "num": list(pre.num), "flag": list(pre.flag), "log": list(pre.log),
        "lo": {k: r(v) for k, v in pre.lo.items()}, "hi": {k: r(v) for k, v in pre.hi.items()},
        "median": {k: r(v) for k, v in pre.median.items()},
        "dummy_cols": list(pre.dummy_cols),
        "mean": [r(v) for v in pre.scaler.mean_], "scale": [r(v) for v in pre.scaler.scale_],
    }


def export_comparacion():
    """Cifras de la comparación viejo vs nuevo para la web, leídas de reports/."""
    rep = ROOT / "reports"
    res = pd.read_csv(rep / "v2_resumen.csv").set_index("metrica")
    test = pd.read_csv(rep / "final_v2_test.csv").set_index("segmento")
    sub = pd.read_csv(rep / "stress_subgrupos.csv")
    cal = pd.read_csv(rep / "stress_calibracion.csv").set_index("modelo")["ece"]
    prod = sub[sub.grupo == "Producto"].set_index("segmento")
    fila = lambda nombre, a, b, fmt="auc": {"nombre": nombre, "viejo": float(a), "nuevo": float(b), "formato": fmt}
    out = {
        "resultados": [
            fila("AUC en validación cruzada", res.loc["auc_cv", "antes"], res.loc["auc_cv", "despues"]),
            fila("AUC en la prueba apartada", test.loc["GLOBAL", "auc_produccion"], test.loc["GLOBAL", "auc_final"]),
            fila("AUC en efectivo", prod.loc["Cash loans", "auc_produccion"], prod.loc["Cash loans", "auc_final"]),
            fila("AUC en rotativo", prod.loc["Revolving loans", "auc_produccion"], prod.loc["Revolving loans", "auc_final"]),
            fila("Dependencia del score", res.loc["dependencia_pct", "antes"], res.loc["dependencia_pct", "despues"], "pct_menor"),
            fila("AUC si falta el score", res.loc["auc_score_vacio", "antes"], res.loc["auc_score_vacio", "despues"]),
            fila("Error de calibración (ECE)", cal["Producción"], cal["Final calibrado"], "menor"),
        ],
        "mejora_cv": {"diff": float(res.loc["auc_cv", "despues"] - res.loc["auc_cv", "antes"]),
                      "ci_low": float(res.loc["auc_cv_ci_low", "despues"]), "ci_high": float(res.loc["auc_cv_ci_high", "despues"])},
        "cambios": [
            ["Peso árbol / redes", "0,65 / 0,35, fijado a mano", "0,90 / 0,10, buscado en validación cruzada"],
            ["Datos que ve el árbol", "imputados, escalados y one-hot", "crudos + 12 razones entre variables"],
            ["Árbol", "31 hojas, tasa 0,04, 1 semilla", "15 hojas, tasa 0,02, 5 semillas"],
            ["Vacíos en las redes", "mediana fuera de escala (error)", "mediana en escala logarítmica"],
            ["Modelo sin score", "no", "15 % de la mezcla"],
            ["Umbral", "exactitud en datos 50/50", "por costo, calibrado, mora real 8,07 %"],
        ],
    }
    (OUT_DIR / "comparacion_v2.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ {OUT_DIR / 'comparacion_v2.json'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paridad", type=int, default=0)
    args = ap.parse_args()

    m = model_v2.load()
    cal = joblib.load(model_v2.V2 / "calibrador_isotonico.joblib")
    pol = json.loads((model_v2.V2 / "product_threshold_policy.json").read_text(encoding="utf-8"))
    man = json.loads((model_v2.V2 / "manifest.json").read_text(encoding="utf-8"))
    ch = m.choice
    ratio_cols = {"r_monto_ingreso", "r_cuota_ingreso", "r_saldo_ingreso", "r_obligaciones_ingreso", "r_monto_cuota",
                  "r_costo_total", "r_saldo_monto", "r_mora_por_credito", "r_creditos_por_anio",
                  "r_ingreso_por_persona", "edad_inicio_laboral", "r_antiguedad_edad", "n_vacios"}

    bundle = {
        "version": "v2",
        "input_cols": [c for c in m.hgbs[0].feature_names_in_ if c not in ratio_cols],
        "cat_cols": list(C.CAT_COLS),
        "rare_to_otro": {k: list(v) for k, v in C.RARE_TO_OTRO.items()},
        "weights": {"hgb_con_score": ch["peso_hgb_con_score"], "hgb_sin_score": ch["peso_hgb_sin_score"],
                    "con_score": ch["peso_con_score"]},
        "hgb": [export_hgb(h) for h in m.hgbs],
        "hgb_sin_score": [export_hgb(h) for h in m.hgbs_ns],
        "pre_redes": export_pre(m.net_pre["redes"]),
        "pre_redes_sin_score": export_pre(m.net_pre["redes_sin_score"]),
        "redes": [export_keras_model(n) for n in m._nets("redes")],
        "redes_sin_score": [export_keras_model(n) for n in m._nets("redes_sin_score")],
        "calibrador": {"x": [r(v) for v in cal.X_thresholds_], "y": [r(v) for v in cal.y_thresholds_]},
        "politica": {
            "productos_permitidos": pol["productos_permitidos"], "productos_bloqueados": pol["productos_bloqueados"],
            "mora_real": pol["mora_real_supuesta"], "proporcion_aptos": pol["proporcion_aptos_entrenamiento"],
            "costo_por_defecto": pol["costo_por_defecto"], "umbrales": pol["umbrales_p_apto_real"],
        },
        "metricas": {"auc_cv": man.get("auc_oof"), "manifest": {k: man[k] for k in ("nombre", "formula") if k in man}},
    }
    out = OUT_DIR / "model_bundle_v2.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"✓ {out} ({out.stat().st_size / 1e6:.1f} MB)")

    export_comparacion()

    if args.paridad:
        df = pd.read_csv(C.DATA_CSV,
                         encoding="utf-8-sig")
        df = df.sample(args.paridad, random_state=7).reset_index(drop=True)
        comps = m.components(df)
        p = m.predict_proba(df, comps)
        filas = json.loads(df.drop(columns=[c for c in C.DROP_COLS + [C.TARGET] if c in df]).to_json(orient="records"))
        ref = {"filas": filas, "p": p.tolist(), "p_cal": cal.predict(p).tolist(),
               **{k: v.tolist() for k, v in comps.items()}}
        dest = ROOT / "frontend" / "scripts" / "paridad_v2_ref.json"
        dest.parent.mkdir(exist_ok=True)
        dest.write_text(json.dumps(ref), encoding="utf-8")
        print(f"✓ referencia de paridad: {dest}")


if __name__ == "__main__":
    main()
