"""Fase 4 - Profesor para destilacion: predicciones out-of-fold (5-fold) de LightGBM sobre Train.

Cada fila de Train recibe la probabilidad de un modelo que NO la vio en entrenamiento, para
que las etiquetas suaves no filtren la etiqueta real. Val y Test no se usan aqui.
"""
import json

import lightgbm as lgb
import numpy as np
from sklearn.model_selection import StratifiedKFold

from phase4_common import P4, load_raw, metrics
from phase4_gbdt import frame


def main():
    best = json.loads((P4 / "lgbm_best_params.json").read_text())
    best.pop("cv_logloss")
    df, y, tr, va, te = load_raw()
    X = frame(df).iloc[tr]
    ytr = y[tr]
    oof = np.zeros(len(tr))
    for k, (a, b) in enumerate(StratifiedKFold(5, shuffle=True, random_state=42).split(X, ytr)):
        p = dict(objective="binary", verbosity=-1, learning_rate=0.03, bagging_freq=1, seed=42,
                 num_threads=4, feature_pre_filter=False, **best)
        # numero de arboles fijo (mediana de las corridas con parada temprana en Fase 4 ~1400)
        m = lgb.train(p, lgb.Dataset(X.iloc[a], ytr[a]), num_boost_round=1400)
        oof[b] = m.predict(X.iloc[b])
        print(f"fold {k}: LL={metrics(ytr[b], oof[b])['LogLoss']:.5f}", flush=True)
    print(f"OOF LL train={metrics(ytr, oof)['LogLoss']:.5f}")
    np.save(P4 / "teacher_oof_train.npy", oof.astype("float32"))


if __name__ == "__main__":
    main()
