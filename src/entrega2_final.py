"""Entrega 2 - Seleccion (solo Validacion) y evaluacion final unica en Test, segun
reports/entrega2_preregistro.md.

1. Curva de Log Loss de Validacion vs numero de semillas (bloque S).
2. Candidato puro = menor Log Loss de Validacion entre A3 x20, C4 x20 y A3 x20 + C4 x20.
   Via hibrida (A3 x20 + E3 x20): solo Validacion.
3. Re-entrena el candidato puro, verifica que reproduce las predicciones de Validacion del
   bloque S, y guarda modelos + codificador + manifiesto en artifacts/entrega2/.
4. Evalua Test UNA vez y compara (bootstrap pareado) con el baseline y con Ensemble_PLE_Fase4
   reutilizando sus predicciones de Fase 4.

Uso: python src/entrega2_final.py
"""
import json

import joblib
import numpy as np
import pandas as pd
from tensorflow import keras

from entrega2_run import E2, EXPERIMENTS, SEEDS20
from phase4_common import C, P4, get_data, metrics, paired_bootstrap, train_mlp

SEEDS = [int(s) for s in SEEDS20.split(",")]
FAM = {"A3": "S1_A3_x20", "C4": "S2_C4_x20", "E3": "S3_E3_x20"}


def main():
    val = {k: np.load(E2 / f"preds_{v}.npz")["val"] for k, v in FAM.items()}
    data = get_data("ple", 16)
    yv, yt = data["y_va"], data["y_te"]
    p4 = np.load(P4 / "final_preds.npz")  # val_0/test_0 = baseline, val_1/test_1 = Ensemble_PLE_Fase4

    # 1. Curva por numero de semillas (Validacion)
    curve = []
    for fam, P in val.items():
        for m in range(1, len(SEEDS) + 1):
            curve.append(dict(familia=fam, n_semillas=m, val_LogLoss=metrics(yv, P[:m].mean(0))["LogLoss"]))
    for m in range(1, len(SEEDS) + 1):
        curve.append(dict(familia="A3+C4", n_semillas=m,
                          val_LogLoss=metrics(yv, np.r_[val["A3"][:m], val["C4"][:m]].mean(0))["LogLoss"]))
    curve = pd.DataFrame(curve)
    curve.to_csv(C.REPORTS / "entrega2_curva_semillas.csv", index=False)

    # 2. Seleccion pre-registrada (solo Validacion)
    opciones = {"A3 x20": ["A3"], "C4 x20": ["C4"], "A3 x20 + C4 x20": ["A3", "C4"]}
    ll_op = {k: metrics(yv, np.concatenate([val[f] for f in fams]).mean(0))["LogLoss"]
             for k, fams in opciones.items()}
    elegido = min(ll_op, key=ll_op.get)
    print("Opciones puras (Val):", {k: round(v, 5) for k, v in ll_op.items()}, "-> elegido:", elegido)
    p_hib = np.r_[val["A3"], val["E3"]].mean(0)

    # 3. Re-entrenamiento del candidato puro + guardado
    out_dir = E2 / "final_models"
    out_dir.mkdir(exist_ok=True)
    pvs, pts, files = [], [], []
    for fam in opciones[elegido]:
        name = FAM[fam]
        cfg = EXPERIMENTS["S"][name][0]
        for i, s in enumerate(SEEDS):
            pv, pt, ep, model = train_mlp(data, cfg, s)
            assert np.allclose(pv, val[fam][i], atol=1e-6), f"no reproduce {name} s={s}"
            files.append(f"final_models/{fam}_s{s}.keras")
            model.save(E2 / files[-1])
            keras.backend.clear_session()
            pvs.append(pv)
            pts.append(pt)
        print(f"  {fam}: {len(SEEDS)} redes re-entrenadas; reproducen Validacion del bloque S", flush=True)
    joblib.dump(data["enc"], E2 / "encoder_entrega2.joblib")
    (E2 / "final_manifest.json").write_text(json.dumps(dict(
        ensemble_name="Ensemble_PLE_Puro_E2", via="neuronal pura (sin profesor externo)",
        seleccion=f"{elegido} (menor Log Loss de Validacion entre {list(opciones)})",
        configs={FAM[f]: EXPERIMENTS["S"][FAM[f]][0] for f in opciones[elegido]}, seeds=SEEDS,
        models=files, encoder="encoder_entrega2.joblib",
        aggregation="media aritmetica de probabilidades", threshold=0.5), indent=2))
    p_v, p_t = np.mean(pvs, 0), np.mean(pts, 0)

    # 4. Evaluacion final (unica) en Test
    rows = []
    cands = [
        ("Baseline Ensemble_Top3_Diverso", "red (Fases 1-2)", p4["val_0"], p4["test_0"]),
        ("Ensemble_PLE_Fase4 (A3 x5 + E3 x5)", "red + destilacion LightGBM", p4["val_1"], p4["test_1"]),
        (f"Ensemble_PLE_Puro_E2 ({elegido})", "red neuronal pura", p_v, p_t),
        ("Hibrido E2: A3 x20 + E3 x20", "red + destilacion LightGBM", p_hib, None),
    ]
    for name, via, pv, pt in cands:
        r = dict(modelo=name, via=via, n_redes={0: 3, 1: 10, 2: len(pvs), 3: 40}[len(rows)])
        r.update({f"val_{k}": v for k, v in metrics(yv, pv).items()})
        for ref_name, ref in [("baseline", p4["val_0"]), ("fase4", p4["val_1"])]:
            d, lo, hi, _ = paired_bootstrap(yv, pv, ref)
            r.update({f"val_dLL_vs_{ref_name}": d, f"val_IC95_vs_{ref_name}": f"[{lo:+.5f}, {hi:+.5f}]"})
        if pt is not None:
            r.update({f"test_{k}": v for k, v in metrics(yt, pt).items()})
            for ref_name, ref in [("baseline", p4["test_0"]), ("fase4", p4["test_1"])]:
                d, lo, hi, _ = paired_bootstrap(yt, pt, ref)
                r.update({f"test_dLL_vs_{ref_name}": d, f"test_IC95_vs_{ref_name}": f"[{lo:+.5f}, {hi:+.5f}]"})
        rows.append(r)
    res = pd.DataFrame(rows)
    res.to_csv(C.REPORTS / "entrega2_final_test.csv", index=False)
    np.savez_compressed(E2 / "final_preds.npz", y_val=yv, y_test=yt, val=p_v, test=p_t, val_hibrido=p_hib)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(res.T.to_string())


if __name__ == "__main__":
    main()
