"""Fase 4 - Evaluacion final congelada en Test.

1. Re-entrena la configuracion NN ganadora (elegida solo en Validacion) con N semillas y
   guarda modelos + codificador en artifacts/phase4/.
2. Elige en Validacion el peso del blend NN+LightGBM (referencia hibrida).
3. Evalua UNA vez en Test: baseline congelado, NN Fase 4, LightGBM y blend.
4. Bootstrap pareado (2000 remuestreos) de la diferencia de Log Loss vs el baseline.

Uso: python src/phase4_final.py --configs A3_ple16_relu,E3_ple16_elu_d30_distill05 --seeds 5
"""
import argparse
import json

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from tensorflow import keras

from phase4_common import P4, C, get_data, metrics, train_mlp
from phase4_run_nn import BLOCKS

ALL = {k: v for b in BLOCKS.values() for k, v in b.items()}


def baseline_preds():
    d = np.load(C.ARTIFACTS / "splits.npz")
    pv, pt = [], []
    for m in ["cfg_c_s42", "cfg_b_leaky_s42", "cfg_base_s2026"]:
        k = keras.models.load_model(C.ARTIFACTS / "ensemble_models" / f"{m}.keras")
        pv.append(k.predict(d["X_val"], verbose=0, batch_size=8192).ravel())
        pt.append(k.predict(d["X_test"], verbose=0, batch_size=8192).ravel())
    return np.mean(pv, 0), np.mean(pt, 0)


def ll_vec(y, p):
    p = np.clip(p, 1e-7, 1 - 1e-7)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def logit(p):
    p = np.clip(p, 1e-7, 1 - 1e-7)
    return np.log(p / (1 - p))


def blend(p_nn, p_gb, w):
    """Promedio en espacio logit (mejor que en probabilidad para Log Loss)."""
    return 1 / (1 + np.exp(-((1 - w) * logit(p_nn) + w * logit(p_gb))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", required=True)
    ap.add_argument("--seeds", type=int, default=5)
    a = ap.parse_args()
    names = a.configs.split(",")
    cfgs = [ALL[n] for n in names]
    assert len({(c.get("enc"), c.get("n_bins", 16)) for c in cfgs}) == 1, "un solo codificador"
    data = get_data(cfgs[0].get("enc", "base"), cfgs[0].get("n_bins", 16))
    yv, yt = data["y_va"], data["y_te"]

    # 1. Re-entrenamiento multisemilla y guardado
    seeds = [42, 1, 7, 21, 2026, 3, 11, 13, 17, 19][: a.seeds]
    out_dir = P4 / "final_models"
    out_dir.mkdir(exist_ok=True)
    pvs, pts, files = [], [], []
    for name, cfg in zip(names, cfgs):
        for s in seeds:
            pv, pt, ep, model = train_mlp(data, cfg, s)
            files.append(f"final_models/{name}_s{s}.keras")
            model.save(P4 / files[-1])
            keras.backend.clear_session()
            pvs.append(pv)
            pts.append(pt)
            print(f"  {name} seed={s} ep={ep} valLL={metrics(yv, pv)['LogLoss']:.5f}", flush=True)
    joblib.dump(data["enc"], P4 / "encoder_phase4.joblib")
    (P4 / "final_manifest.json").write_text(json.dumps(
        dict(ensemble_name="Ensemble_PLE_Fase4", configs=dict(zip(names, cfgs)), seeds=seeds,
             models=files, encoder="encoder_phase4.joblib",
             aggregation="media aritmetica de probabilidades", threshold=0.5), indent=2))
    p_nn_v, p_nn_t = np.mean(pvs, 0), np.mean(pts, 0)

    # 2. Baseline y LightGBM
    p_b_v, p_b_t = baseline_preds()
    g = np.load(P4 / "preds_GBDT_lgbm.npz")
    p_g_v, p_g_t = g["val"].mean(0), g["test"].mean(0)
    w = minimize_scalar(lambda w: metrics(yv, blend(p_nn_v, p_g_v, w))["LogLoss"],
                        bounds=(0, 1), method="bounded").x
    print(f"Peso LightGBM en blend (elegido en Val): {w:.3f}")

    cands = {
        "Baseline Ensemble_Top3_Diverso (Fase 2)": (p_b_v, p_b_t),
        f"NN Fase 4: Ensemble_PLE_Fase4 ({len(pvs)} redes)": (p_nn_v, p_nn_t),
        "Referencia LightGBM x5 semillas": (p_g_v, p_g_t),
        f"Hibrido NN+LightGBM (w_gbdt={w:.2f})": (blend(p_nn_v, p_g_v, w), blend(p_nn_t, p_g_t, w)),
    }

    # 3. Evaluacion unica en Test + 4. bootstrap pareado
    rng = np.random.default_rng(2026)
    B = rng.integers(0, len(yt), size=(2000, len(yt)))
    base_l = ll_vec(yt, p_b_t)
    rows = []
    for i, (name, (pv, pt)) in enumerate(cands.items()):
        mv, mt = metrics(yv, pv), metrics(yt, pt)
        diff = ll_vec(yt, pt) - base_l
        boots = diff[B].mean(1) if i else np.full(1, np.nan)  # fila 0 = baseline (sin comparacion)
        rows.append({
            "modelo": name,
            **{f"val_{k}": round(v, 5) for k, v in mv.items()},
            **{f"test_{k}": round(v, 5) for k, v in mt.items()},
            "test_dLL_vs_baseline": round(diff.mean(), 5) if i else np.nan,
            "IC95_lo": round(np.percentile(boots, 2.5), 5),
            "IC95_hi": round(np.percentile(boots, 97.5), 5),
            "p_bootstrap(dLL>=0)": round(float((boots >= 0).mean()), 4) if i else np.nan,
        })
    res = pd.DataFrame(rows)
    res.to_csv(C.REPORTS / "phase4_final_test.csv", index=False)
    np.savez_compressed(P4 / "final_preds.npz", y_val=yv, y_test=yt,
                        **{f"val_{i}": v[0] for i, v in enumerate(cands.values())},
                        **{f"test_{i}": v[1] for i, v in enumerate(cands.values())})
    pd.set_option("display.width", 250)
    print(res[["modelo", "val_LogLoss", "test_LogLoss", "test_AUC", "test_Brier", "test_Accuracy",
               "test_dLL_vs_baseline", "IC95_lo", "IC95_hi"]].to_string(index=False))


if __name__ == "__main__":
    main()
