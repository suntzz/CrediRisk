"""Entrega 2 - Experimentos para reducir la Log Loss de la MLP (seleccion SOLO en Validacion).

Cada experimento se entrena con las semillas 42, 1 y 7 (las mismas de la Fase 4) y se compara de
forma pareada contra la referencia A3 (PLE16 + ReLU [64,32,16], Fase 4), re-entrenada aqui (R0).
Se registran por semilla: mejor epoca, epocas entrenadas, duracion, Log Loss de Train y Validacion,
AUC y Brier; por experimento: el ensamble de semillas y el bootstrap pareado contra la referencia.
Las predicciones de Test NO se guardan ni se examinan en esta etapa.

Uso: python src/entrega2_run.py --block R [--only R1_ple12,R2_ple24] [--seeds 42,1,7]
"""
import argparse
import json
import time

import numpy as np
import pandas as pd
from tensorflow import keras

from phase4_common import C, get_data, metrics, paired_bootstrap, train_mlp
from phase4_run_nn import BLOCKS as P4_BLOCKS

E2 = C.ARTIFACTS / "entrega2"
E2.mkdir(parents=True, exist_ok=True)
OUT = C.REPORTS / "entrega2_resultados.csv"
REF = "R0_A3_ref"

A3 = P4_BLOCKS["A"]["A3_ple16_relu"]  # enc=ple, n_bins=16, [64,32,16] relu, drop .15, Adam 5e-4, bs 128


def a3(**kw):
    """Configuracion A3 con cambios aislados (un factor por experimento)."""
    return {**A3, **kw}


EXPERIMENTS = {
    # R: representacion de variables numericas (hipotesis H1-H4 del informe)
    "R": {
        REF: (a3(), "Referencia: A3 de Fase 4 (PLE 16 tramos por cuantiles)"),
        "R1_ple12": (a3(n_bins=12), "H1: numero de tramos intermedio entre 8 y 16"),
        "R2_ple24": (a3(n_bins=24), "H1: mas tramos captan saltos mas finos (p.ej. tasa ~55%)"),
        "R3_pletree16": (a3(enc="ple_tree"), "H2: tramos guiados por el target (arbol por variable, min 500 obs/hoja)"),
        "R4_ple16_nanzero": (a3(enc_kw={"nan_zero": True}), "H3: no codificar la mediana imputada en el bloque PLE"),
        "R5_plr_base_s005": (a3(enc="base", periodic={"k": 16, "sigma": 0.05, "d": 16}), "H4: embedding periodico PLR (sigma 0.05) en lugar de PLE"),
        "R6_plr_base_s03": (a3(enc="base", periodic={"k": 16, "sigma": 0.3, "d": 16}), "H4: embedding periodico PLR (sigma 0.3) en lugar de PLE"),
    },
    # O: optimizacion / regularizacion sobre A3 (hipotesis H5-H7)
    "O": {
        "O1_ema09": (a3(ema=0.9), "H5: EMA de pesos reduce la varianza del punto de parada"),
        "O2_ema09_lr2e4": (a3(ema=0.9, lr=2e-4), "H5: EMA + lr menor (A3 converge en ~12 epocas)"),
        "O3_layernorm": (a3(layernorm=True), "H6: LayerNorm estabiliza el entrenamiento con 268 entradas"),
        "O4_adamw_wd3e2": (a3(wd=3e-2), "H7: weight decay desacoplado aislado (sin cambiar dropout)"),
    },
    # K: arquitectura (hipotesis H8)
    "K": {
        "K1_resnet_ple16": (a3(resnet={"d": 64, "blocks": 2, "d_hidden": 128}), "H8: ResNet tabular con LayerNorm"),
    },
    # S: reduccion de varianza por numero de semillas (H9). Correr con --seeds SEEDS20.
    "S": {
        "S1_A3_x20": (a3(), "H9: deep ensemble de A3 (puro) con 20 semillas"),
        "S2_C4_x20": (P4_BLOCKS["C"]["C4_ple16_elu_d30_bs512"], "H9: deep ensemble de C4 (puro, ELU) con 20 semillas"),
        "S3_E3_x20": (P4_BLOCKS["E"]["E3_ple16_elu_d30_distill05"], "H9 (via hibrida): E3 destilada desde LightGBM, 20 semillas"),
    },
}
# Semillas de Fase 4 (42,1,7,21,2026,3,11,13,17,19) + 10 primos adicionales fijados de antemano
SEEDS20 = "42,1,7,21,2026,3,11,13,17,19,23,29,31,37,41,43,47,53,59,61"


def run(name, cfg, desc, block, seeds, ref_val):
    data = get_data(cfg.get("enc", "base"), cfg.get("n_bins", 16), **cfg.get("enc_kw", {}))
    rows, pvs, ptrs = [], [], []
    for s in seeds:
        t0 = time.time()
        pv, _pt_no_usado, ep, model = train_mlp(data, cfg, s)
        ptr = model.predict(data["X_tr"], batch_size=8192, verbose=0).ravel()
        n_ep = len(model.history.history["loss"])
        keras.backend.clear_session()
        mv, mtr = metrics(data["y_va"], pv), metrics(data["y_tr"], ptr)
        pvs.append(pv)
        ptrs.append(ptr)
        rows.append(dict(
            bloque=block, experimento=name, nivel="semilla", semilla=s, n_modelos=1,
            n_features=data["X_tr"].shape[1], mejor_epoca=ep, epocas_entrenadas=n_ep,
            duracion_s=round(time.time() - t0, 1), train_LogLoss=mtr["LogLoss"],
            val_LogLoss=mv["LogLoss"], val_AUC=mv["AUC"], val_Brier=mv["Brier"],
            hipotesis=desc, config=json.dumps(cfg),
        ))
        print(f"  {name} s={s} ep={ep}/{n_ep} trainLL={mtr['LogLoss']:.5f} valLL={mv['LogLoss']:.5f} "
              f"AUC={mv['AUC']:.5f} ({rows[-1]['duracion_s']}s)", flush=True)
    pv_e, ptr_e = np.mean(pvs, 0), np.mean(ptrs, 0)
    mv, mtr = metrics(data["y_va"], pv_e), metrics(data["y_tr"], ptr_e)
    ens = dict(
        bloque=block, experimento=name, nivel="ensamble", semilla="+".join(map(str, seeds)),
        n_modelos=len(seeds), n_features=data["X_tr"].shape[1],
        duracion_s=round(sum(r["duracion_s"] for r in rows), 1), train_LogLoss=mtr["LogLoss"],
        val_LogLoss=mv["LogLoss"], val_AUC=mv["AUC"], val_Brier=mv["Brier"],
        val_LL_media_semillas=np.mean([r["val_LogLoss"] for r in rows]),
        val_LL_std_semillas=np.std([r["val_LogLoss"] for r in rows]),
        hipotesis=desc, config=json.dumps(cfg),
    )
    if ref_val is not None and name != REF:
        d, lo, hi, p = paired_bootstrap(data["y_va"], pv_e, ref_val.mean(0))
        ens.update(dLL_vs_ref=d, IC95_lo=lo, IC95_hi=hi, p_boot_dLL_ge0=p)
        # diferencia por semilla emparejada (misma semilla, mismo orden)
        per_seed = [metrics(data["y_va"], a)["LogLoss"] - metrics(data["y_va"], b)["LogLoss"]
                    for a, b in zip(pvs, ref_val)]
        ens["dLL_semillas_mejoran"] = f"{sum(x < 0 for x in per_seed)}/{len(per_seed)}"
    np.savez_compressed(E2 / f"preds_{name}.npz", val=np.array(pvs, dtype="float32"),
                        seeds=np.array(seeds))
    print(f"==> {name}: valLL ens={mv['LogLoss']:.5f} media/semilla={ens['val_LL_media_semillas']:.5f}"
          f"±{ens['val_LL_std_semillas']:.5f} trainLL ens={mtr['LogLoss']:.5f}"
          + (f" dLL={ens['dLL_vs_ref']:+.5f} [{ens['IC95_lo']:+.5f},{ens['IC95_hi']:+.5f}]"
             f" semillas mejoran {ens['dLL_semillas_mejoran']}" if "dLL_vs_ref" in ens else ""),
          flush=True)
    return rows + [ens]


def save(new_rows, names):
    df = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame()
    if len(df):
        df = df[~df.experimento.isin(names)]
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df.to_csv(OUT, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", required=True, choices=list(EXPERIMENTS))
    ap.add_argument("--only", default="")
    ap.add_argument("--seeds", default="42,1,7")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")]
    exps = EXPERIMENTS[a.block]
    if a.only:
        exps = {k: v for k, v in exps.items() if k in a.only.split(",")}
    ref_file = E2 / f"preds_{REF}.npz"
    for name, (cfg, desc) in exps.items():
        ref_val = np.load(ref_file)["val"] if ref_file.exists() else None
        save(run(name, cfg, desc, a.block, seeds, ref_val), [name])


if __name__ == "__main__":
    main()
