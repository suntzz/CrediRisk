"""Entrega 2 - Tecnicas post hoc sin re-entrenar: calibracion y forma de ensamblar.

Problema: ajustar una calibracion o unos pesos en Validacion y medirlos en esas mismas filas da una
mejora optimista. Por eso todo se estima con ajuste cruzado (10-fold estratificado DENTRO de
Validacion): los parametros se ajustan en 9 partes y se aplican a la parte excluida. Se reporta
tambien la version "in-sample" para mostrar el optimismo.

Uso: python src/entrega2_posthoc.py
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar
from sklearn.model_selection import StratifiedKFold

from phase4_common import C, P4, load_raw, metrics, paired_bootstrap

E2 = C.ARTIFACTS / "entrega2"
OUT = C.REPORTS / "entrega2_posthoc.csv"


def logit(p):
    p = np.clip(p, 1e-7, 1 - 1e-7)
    return np.log(p / (1 - p))


def sig(z):
    return 1 / (1 + np.exp(-z))


def ll(y, p):
    return metrics(y, p)["LogLoss"]


def fit_temperature(y, z):
    return minimize_scalar(lambda t: ll(y, sig(z / t)), bounds=(0.3, 3.0), method="bounded").x


def fit_platt(y, z):
    return minimize(lambda ab: ll(y, sig(ab[0] * z + ab[1])), x0=[1.0, 0.0], method="Nelder-Mead").x


def fit_weights(y, Z):
    """Pesos no negativos que suman 1 (softmax) sobre los logits de cada componente."""
    k = Z.shape[0]
    obj = lambda a: ll(y, sig(np.exp(a) @ Z / np.exp(a).sum()))  # noqa: E731
    a = minimize(obj, x0=np.zeros(k), method="Nelder-Mead").x
    return np.exp(a) / np.exp(a).sum()


def crossfit(y, transform_fit, transform_apply, n_splits=10, seed=0):
    """Devuelve predicciones fuera de pliegue dentro de Validacion."""
    out = np.zeros(len(y))
    for a, b in StratifiedKFold(n_splits, shuffle=True, random_state=seed).split(np.zeros(len(y)), y):
        theta = transform_fit(a)
        out[b] = transform_apply(theta, b)
    return out


def main():
    df, y, tr, va, te = load_raw()
    yv = y[va]
    comps = {  # predicciones individuales de Validacion (3 semillas por familia, Fase 4)
        "A3": np.load(P4 / "preds_A3_ple16_relu.npz")["val"],
        "C4": np.load(P4 / "preds_C4_ple16_elu_d30_bs512.npz")["val"],
        "E3": np.load(P4 / "preds_E3_ple16_elu_d30_distill05.npz")["val"],
    }
    rows = []

    def add(grupo, tecnica, p, ref, nota=""):
        m = metrics(yv, p)
        d, lo, hi, pv = paired_bootstrap(yv, p, ref)
        rows.append(dict(grupo=grupo, tecnica=tecnica, val_LogLoss=m["LogLoss"], val_AUC=m["AUC"],
                         val_Brier=m["Brier"], dLL_vs_sin_tecnica=d, IC95_lo=lo, IC95_hi=hi, nota=nota))
        print(f"{grupo:28s} {tecnica:42s} LL={m['LogLoss']:.5f} d={d:+.5f} [{lo:+.5f},{hi:+.5f}]")

    # 1. Promedio de probabilidades vs promedio de logits
    for name, P in [("A3 x3", comps["A3"]), ("A3+C4 x6 (puro)", np.r_[comps["A3"], comps["C4"]]),
                    ("A3+E3 x6 (destilado)", np.r_[comps["A3"], comps["E3"]])]:
        p_prob = P.mean(0)
        add(name, "promedio de probabilidades (referencia)", p_prob, p_prob)
        add(name, "promedio de logits", sig(logit(P).mean(0)), p_prob)

    # 2. Calibracion post hoc (temperature scaling y Platt), ajuste cruzado en Validacion
    for name, P in [("A3 x3", comps["A3"]), ("A3+C4 x6 (puro)", np.r_[comps["A3"], comps["C4"]])]:
        p = P.mean(0)
        z = logit(p)
        T = fit_temperature(yv, z)
        add(name, f"temperature scaling in-sample (T={T:.3f})", sig(z / T), p, "optimista: ajusta y evalua en las mismas filas")
        cf = crossfit(yv, lambda a: fit_temperature(yv[a], z[a]), lambda t, b: sig(z[b] / t))
        add(name, "temperature scaling ajuste cruzado 10-fold", cf, p)
        ab = fit_platt(yv, z)
        add(name, f"Platt in-sample (a={ab[0]:.3f}, b={ab[1]:+.3f})", sig(ab[0] * z + ab[1]), p, "optimista")
        cf = crossfit(yv, lambda a: fit_platt(yv[a], z[a]), lambda t, b: sig(t[0] * z[b] + t[1]))
        add(name, "Platt ajuste cruzado 10-fold", cf, p)

    # 3. Pesos del ensamble entre familias (logits), ajuste cruzado
    Z = np.stack([logit(comps["A3"]).mean(0), logit(comps["C4"]).mean(0)])
    p_eq = sig(Z.mean(0))
    w = fit_weights(yv, Z)
    add("A3+C4 (familias)", f"pesos in-sample w={np.round(w, 3).tolist()}", sig(w @ Z), p_eq, "optimista")
    cf = crossfit(yv, lambda a: fit_weights(yv[a], Z[:, a]), lambda w, b: sig(w @ Z[:, b]))
    add("A3+C4 (familias)", "pesos ajuste cruzado 10-fold (vs pesos iguales)", cf, p_eq)

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nGuardado en {OUT}")


if __name__ == "__main__":
    main()
