"""Fase 4 - Bloque NN: barrido de configuraciones orientado a minimizar la Log Loss en Validacion.

Cada configuracion se entrena con varias semillas; se reporta la Log Loss media por semilla y
la del promedio de semillas (ensamble). Las predicciones de Test se guardan pero NO se miran
aqui: solo `phase4_final.py` las evalua, una vez elegida la configuracion final en Validacion.

Uso: python src/phase4_run_nn.py --block A
"""
import argparse
import json
import time

import numpy as np
import pandas as pd
from tensorflow import keras

from phase4_common import P4, C, get_data, metrics, train_mlp

BASE = dict(hidden=(64, 32, 16), act="relu", dropout=0.15, lr=5e-4, batch=128)

BLOCKS = {
    # A: efecto de la codificacion de entrada con la arquitectura del proyecto
    "A": {
        "A1_base_relu": dict(enc="base", **BASE),
        "A2_qt_relu": dict(enc="qt", **BASE),
        "A3_ple16_relu": dict(enc="ple", n_bins=16, **BASE),
        "A4_ple8_relu": dict(enc="ple", n_bins=8, **BASE),
    },
    # C: PLE converge en ~12 epocas -> mas regularizacion (dropout, weight decay, lr, batch)
    "C": {
        "C1_ple16_d30_wd": dict(enc="ple", n_bins=16, hidden=(64, 32, 16), act="relu", dropout=0.3, lr=3e-4, batch=256, wd=1e-2, drop_last=True),
        "C2_ple16_128x64_d40_in10": dict(enc="ple", n_bins=16, hidden=(128, 64), act="relu", dropout=0.4, input_dropout=0.1, lr=3e-4, batch=256, wd=1e-2, drop_last=True),
        "C3_ple16_32x16_d20": dict(enc="ple", n_bins=16, hidden=(32, 16), act="relu", dropout=0.2, lr=3e-4, batch=256, wd=1e-2, drop_last=True),
        "C4_ple16_elu_d30_bs512": dict(enc="ple", n_bins=16, hidden=(64, 32, 16), act="elu", dropout=0.3, lr=5e-4, batch=512, wd=3e-2, drop_last=True),
        "C5_ple32_128x64_d40_in10": dict(enc="ple", n_bins=32, hidden=(128, 64), act="relu", dropout=0.4, input_dropout=0.1, lr=3e-4, batch=256, wd=1e-2, drop_last=True),
    },
    # D: la brecha con GBDT son interacciones de a pares -> rama Cross (DCN-v2) y embeddings por variable
    "D": {
        "D1_ple16_cross2": dict(enc="ple", n_bins=16, cross=2, **BASE),
        "D2_ple16_elu_cross2_bs512": dict(enc="ple", n_bins=16, cross=2, hidden=(64, 32, 16), act="elu", dropout=0.3, lr=5e-4, batch=512, wd=3e-2, drop_last=True),
        "D3_ple16_emb8": dict(enc="ple", n_bins=16, emb_dim=8, **BASE),
        "D4_ple16_emb8_cross2": dict(enc="ple", n_bins=16, emb_dim=8, cross=2, hidden=(64, 32, 16), act="relu", dropout=0.15, lr=5e-4, batch=256, wd=1e-2),
        "D5_base_cross3": dict(enc="base", cross=3, **BASE),
    },
    # E: destilacion desde LightGBM (OOF sobre Train); el modelo desplegado sigue siendo un MLP
    "E": {
        "E1_ple16_distill05": dict(enc="ple", n_bins=16, distill=0.5, **BASE),
        "E2_ple16_distill10": dict(enc="ple", n_bins=16, distill=1.0, **BASE),
        "E3_ple16_elu_d30_distill05": dict(enc="ple", n_bins=16, distill=0.5, hidden=(64, 32, 16), act="elu", dropout=0.3, lr=5e-4, batch=512, wd=3e-2, drop_last=True),
        "E4_base_distill05": dict(enc="base", distill=0.5, **BASE),
    },
}


def run(name, cfg, seeds):
    data = get_data(cfg.get("enc", "base"), cfg.get("n_bins", 16))
    pvs, pts, rows = [], [], []
    t0 = time.time()
    for s in seeds:
        pv, pt, ep, model = train_mlp(data, cfg, s)
        keras.backend.clear_session()
        pvs.append(pv)
        pts.append(pt)
        m = metrics(data["y_va"], pv)
        rows.append(m["LogLoss"])
        print(f"  {name} seed={s} ep={ep} valLL={m['LogLoss']:.5f} valAUC={m['AUC']:.5f}", flush=True)
    pv_ens = np.mean(pvs, 0)
    me = metrics(data["y_va"], pv_ens)
    np.savez_compressed(P4 / f"preds_{name}.npz", val=np.array(pvs), test=np.array(pts), seeds=np.array(seeds))
    rec = dict(
        experimento=name,
        n_features=data["X_tr"].shape[1],
        config=json.dumps({k: v for k, v in cfg.items()}),
        seeds=len(seeds),
        val_LL_media_semilla=np.mean(rows),
        val_LL_std_semilla=np.std(rows),
        val_LL_ensamble=me["LogLoss"],
        val_AUC_ensamble=me["AUC"],
        val_Brier_ensamble=me["Brier"],
        tiempo_s=round(time.time() - t0, 1),
    )
    print(
        f"==> {name}: LL/semilla={rec['val_LL_media_semilla']:.5f}±{rec['val_LL_std_semilla']:.5f} "
        f"LL ens={me['LogLoss']:.5f} AUC ens={me['AUC']:.5f}",
        flush=True,
    )
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", required=True)
    ap.add_argument("--seeds", default="42,1,7")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")]
    exps = BLOCKS[a.block]
    if a.only:
        exps = {k: v for k, v in exps.items() if k in a.only.split(",")}
    out = C.REPORTS / "experiments_phase4_nn.csv"
    for name, cfg in exps.items():
        rec = run(name, cfg, seeds)
        df = pd.read_csv(out) if out.exists() else pd.DataFrame()
        df = df[df.get("experimento", pd.Series(dtype=str)) != name] if len(df) else df
        df = pd.concat([df, pd.DataFrame([rec])], ignore_index=True)
        df.sort_values("val_LL_ensamble").to_csv(out, index=False)


if __name__ == "__main__":
    main()
