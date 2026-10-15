"""Fase 4 - Referencia GBDT (LightGBM) para acotar la Log Loss alcanzable en estos datos.

Hiperparametros: Optuna con validacion cruzada 5-fold SOLO sobre Train (Validacion queda
para la parada temprana final y la comparacion; Test no se toca).
"""
import json

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

from phase4_common import P4, C, load_raw, metrics

optuna.logging.set_verbosity(optuna.logging.WARNING)


def frame(df):
    X = df.drop(columns=[c for c in C.DROP_COLS + [C.TARGET] if c in df]).copy()
    for c in C.CAT_COLS:
        X[c] = X[c].astype("category")
    return X


def main(n_trials=40):
    df, y, tr, va, te = load_raw()
    X = frame(df)
    Xtr, Xva, Xte = X.iloc[tr], X.iloc[va], X.iloc[te]
    dtr = lgb.Dataset(Xtr, y[tr], free_raw_data=False)

    def objective(trial):
        params = dict(
            objective="binary",
            metric="binary_logloss",
            verbosity=-1,
            learning_rate=0.03,
            num_leaves=trial.suggest_int("num_leaves", 4, 64, log=True),
            min_child_samples=trial.suggest_int("min_child_samples", 20, 400, log=True),
            feature_fraction=trial.suggest_float("feature_fraction", 0.4, 1.0),
            bagging_fraction=trial.suggest_float("bagging_fraction", 0.5, 1.0),
            bagging_freq=1,
            lambda_l2=trial.suggest_float("lambda_l2", 1e-3, 30, log=True),
            min_split_gain=trial.suggest_float("min_split_gain", 0, 0.5),
            cat_smooth=trial.suggest_float("cat_smooth", 1, 50, log=True),
            seed=42,
            num_threads=4,
        )
        cv = lgb.cv(
            params, dtr, num_boost_round=3000, nfold=5, stratified=True, seed=42,
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )
        k = "valid binary_logloss-mean"
        trial.set_user_attr("n_rounds", len(cv[k]))
        return cv[k][-1]

    st = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    st.optimize(objective, n_trials=n_trials)
    best = st.best_params
    print("Mejor CV-LL (train 5-fold):", round(st.best_value, 5), best, flush=True)

    pvs, pts = [], []
    for s in (42, 1, 7, 21, 2026):
        params = dict(objective="binary", metric="binary_logloss", verbosity=-1, learning_rate=0.03,
                      bagging_freq=1, seed=s, num_threads=4, **best)
        m = lgb.train(params, dtr, num_boost_round=5000, valid_sets=[lgb.Dataset(Xva, y[va])],
                      callbacks=[lgb.early_stopping(200, verbose=False)])
        pvs.append(m.predict(Xva, num_iteration=m.best_iteration))
        pts.append(m.predict(Xte, num_iteration=m.best_iteration))
        print(f"  LGBM seed={s} iters={m.best_iteration} valLL={metrics(y[va], pvs[-1])['LogLoss']:.5f}", flush=True)
    me = metrics(y[va], np.mean(pvs, 0))
    print(f"==> LGBM ensamble 5 semillas: val LL={me['LogLoss']:.5f} AUC={me['AUC']:.5f}")
    np.savez_compressed(P4 / "preds_GBDT_lgbm.npz", val=np.array(pvs), test=np.array(pts))
    (P4 / "lgbm_best_params.json").write_text(json.dumps(dict(cv_logloss=st.best_value, **best), indent=2))
    imp = pd.Series(m.feature_importance("gain"), index=Xtr.columns).sort_values(ascending=False)
    imp.to_csv(C.REPORTS / "phase4_lgbm_importance_gain.csv", header=["gain"])


if __name__ == "__main__":
    main()
