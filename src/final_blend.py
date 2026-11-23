"""Elección del modelo final v2, todo sobre predicciones fuera de pliegue (clientes que el modelo no vio).

- Modelo con score  = w  * HGB nuevo + (1 - w)  * redes v2.
- Modelo sin score  = w2 * HGB sin score + (1 - w2) * redes sin score.
- Final             = lam * con_score + (1 - lam) * sin_score.

Las redes nuevas se corrieron con 1 sola repetición (5 pliegues), así que toda
mezcla usa la repetición 0 de cada corrida (mismos pliegues: se comprueba).

Uso: python src/final_blend.py
Salidas: reports/v2_*.csv, artifacts/v2/blend_choice.json, artifacts/v2/final_oof.npz
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from cv_protocol import CV_DIR, fast_auc, paired_bootstrap

OUT = C.ARTIFACTS / "v2"
NB = 200  # remuestreos del bootstrap pareado
GRID = np.round(np.arange(0, 1.0001, 0.05), 2)
VARIANTS = ("normal", "score_permutado", "score_vacio")


def load(name):
    p = CV_DIR / f"{name}_oof.npz"
    return np.load(p, allow_pickle=True) if p.exists() else None


base, lab = load("baseline"), load("hgb_lab")
v2, fix = load("mlp_v2"), load("mlp_fix")
y, products, fold0 = base["y"], base["products"], base["fold_id"][0]
for d in (lab, v2, fix):
    if d is not None:
        assert np.array_equal(d["dev_idx"], base["dev_idx"]) and np.array_equal(d["fold_id"][0], fold0), "pliegues distintos"


def comp(d, c, variant="normal"):
    """Repetición 0 de un componente; para modelos sin score las tres variantes coinciden."""
    return d[f"{variant}__{c}"][0].astype(float)


def mix(parts, variant):
    return sum(wt * comp(d, c, variant) for wt, d, c in parts if wt)


def auc(p):
    return fast_auc(y, p)


def dep(parts):
    a, ap = auc(mix(parts, "normal")), auc(mix(parts, "score_permutado"))
    return 100 * (a - ap) / (a - 0.5)


def boot(pa, pb, mask=None):
    m = np.ones(len(y), bool) if mask is None else mask
    return paired_bootstrap(y[m], pa[m], pb[m], n_boot=NB)


# ------------------------------------------------ redes disponibles
if v2 is not None:
    NET, NET_LABEL = (v2, "v2_neural"), "redes v2 (arreglo + razones)"
    NS = (v2, "ns_neural")
else:  # plan de contingencia: redes de producción, peso 0,10
    NET, NET_LABEL = (base, "neural"), "redes de producción"
    NS = None
if fix is not None and v2 is not None and auc(comp(fix, "fix_neural")) > auc(comp(v2, "v2_neural")):
    NET, NET_LABEL = (fix, "fix_neural"), "redes con solo el arreglo"
HGB = (lab, "razones_B_3sem")
HGB_NS = (lab, "sin_score_B")
PROD = [(0.65, base, "hgb"), (0.35, base, "neural")]
p_prod = mix(PROD, "normal")

# ------------------------------------------------ peso HGB/redes (con score)
rows = []
for w in GRID:
    parts = [(w, *HGB), (1 - w, *NET)]
    rows.append({"modelo": "con_score", "peso_hgb": w, "auc": auc(mix(parts, "normal")), "dependencia_pct": dep(parts)})
for w2 in GRID:
    parts = [(w2, *HGB_NS)] + ([(1 - w2, *NS)] if NS else [])
    if NS is None and w2 < 1:
        continue
    rows.append({"modelo": "sin_score", "peso_hgb": w2, "auc": auc(mix(parts, "normal")), "dependencia_pct": np.nan})
search = pd.DataFrame(rows)
search.to_csv(C.REPORTS / "v2_busqueda_pesos.csv", index=False)


def pick_weight(model, net_pair):
    s = search[search.modelo == model]
    if net_pair is None:
        return 1.0, None
    best = s.loc[s.auc.idxmax()]
    w = float(best.peso_hgb)
    note = None
    if w > 0.90:  # las redes conservan al menos 0,10
        hgb_pair = HGB if model == "con_score" else HGB_NS
        pb = mix([(0.9, *hgb_pair), (0.1, *net_pair)], "normal")
        pa = mix([(w, *hgb_pair), (1 - w, *net_pair)], "normal")
        b = boot(pa, pb)
        note = {"peso_optimo_libre": w, "diff_al_forzar_0.10_redes": b}
        w = 0.90
    return w, note


if v2 is None:
    W, note_w = 0.90, {"contingencia": "mlp_v2 no terminó; redes de producción con peso 0,10"}
else:
    W, note_w = pick_weight("con_score", NET)
W2, note_w2 = pick_weight("sin_score", NS)
WITH = [(W, *HGB), (1 - W, *NET)]
WITHOUT = [(W2, *HGB_NS)] + ([(1 - W2, *NS)] if NS and W2 < 1 else [])


def final_parts(lam):
    return [(lam * wt, d, c) for wt, d, c in WITH] + [((1 - lam) * wt, d, c) for wt, d, c in WITHOUT]


# ------------------------------------------------ curva AUC vs dependencia
LAMS = np.round(np.arange(1.0, 0.2999, -0.05), 2)
curve = []
for lam in LAMS:
    parts = final_parts(lam)
    curve.append({"peso_con_score": lam, "auc": auc(mix(parts, "normal")), "dependencia_pct": dep(parts),
                  "auc_score_vacio": auc(mix(parts, "score_vacio"))})
curve = pd.DataFrame(curve)
best_lam = float(curve.loc[curve.auc.idxmax(), "peso_con_score"])
p_best = mix(final_parts(best_lam), "normal")
for i, lam in enumerate(curve.peso_con_score):
    b = boot(p_best, mix(final_parts(lam), "normal"))
    curve.loc[i, ["diff_vs_mejor", "ci_low", "ci_high"]] = b["diff"], b["ci_low"], b["ci_high"]
    bp = boot(p_prod, mix(final_parts(lam), "normal"))
    curve.loc[i, ["diff_vs_prod", "prod_ci_low", "prod_ci_high"]] = bp["diff"], bp["ci_low"], bp["ci_high"]

dep_prod = dep(PROD)
ok = curve[(curve.ci_high >= 0) & (curve.prod_ci_low > 0) & (curve.dependencia_pct < dep_prod)]
if len(ok):
    LAM = float(ok.loc[ok.dependencia_pct.idxmin(), "peso_con_score"])
else:  # ningún punto cumple todo: el de mayor AUC
    LAM = best_lam
curve["elegido"] = curve.peso_con_score == LAM
curve.to_csv(C.REPORTS / "v2_curva_peso.csv", index=False)
p_final = mix(final_parts(LAM), "normal")

# ------------------------------------------------ peso propio para Revolving loans
rev = products == "Revolving loans"
rev_rows = []
for lam in LAMS:
    rev_rows.append({"peso_con_score": lam, "auc_revolving": fast_auc(y[rev], mix(final_parts(lam), "normal")[rev])})
rev_df = pd.DataFrame(rev_rows)
lam_rev = float(rev_df.loc[rev_df.auc_revolving.idxmax(), "peso_con_score"])
b_rev = boot(p_final, mix(final_parts(lam_rev), "normal"), mask=rev)
rev_df.to_csv(C.REPORTS / "v2_revolving_peso.csv", index=False)
LAM_REV = lam_rev if (b_rev["significant"] and b_rev["diff"] > 0) else None

# ------------------------------------------------ cascada (repetición 0, pasos encadenados)
steps = [("Producción (hoy)", PROD)]
if fix is not None:
    steps.append(("Redes: arreglo de imputación", [(0.65, base, "hgb"), (0.35, fix, "fix_neural")]))
if v2 is not None:
    steps.append(("Redes: + razones entre variables", [(0.65, base, "hgb"), (0.35, v2, "v2_neural")]))
net_now = steps[-1][1][1][1:]
steps += [
    ("Árbol sobre datos crudos", [(0.65, lab, "crudo_A"), (0.35, *net_now)]),
    ("Árbol: + razones", [(0.65, lab, "razones_A"), (0.35, *net_now)]),
    ("Árbol: más pequeño y lento", [(0.65, lab, "razones_B"), (0.35, *net_now)]),
    ("Árbol: 3 semillas", [(0.65, lab, "razones_B_3sem"), (0.35, *net_now)]),
]
if NET[1] != net_now[1]:
    steps.append(("Redes elegidas", [(0.65, *HGB), (0.35, *NET)]))
steps.append((f"Peso árbol/redes {W:.2f}/{1 - W:.2f}", WITH))
steps.append((f"Mezcla con modelo sin score (peso {LAM:.2f})", final_parts(LAM)))
cas, prev = [], None
for i, (label, parts) in enumerate(steps):
    p = mix(parts, "normal")
    r = {"paso": i, "etiqueta": label, "auc": auc(p), "dependencia_pct": dep(parts)}
    if prev is not None:
        b = boot(prev, p)
        r.update(aporte=b["diff"], ci_low=b["ci_low"], ci_high=b["ci_high"], significativo=b["significant"])
    cas.append(r)
    prev = p
cas.append({"paso": len(cas), "etiqueta": "Final", "auc": auc(p_final), "dependencia_pct": dep(final_parts(LAM))})
cas = pd.DataFrame(cas)
cas.to_csv(C.REPORTS / "v2_cascada.csv", index=False)

# ------------------------------------------------ comparaciones sueltas (punto 1 del encargo)
extra = []
def cmp(label, pa, pb, mask=None):
    b = boot(pa, pb, mask)
    extra.append({"comparacion": label, **b})
# 3 repeticiones donde no hay redes nuevas
extra.append({"comparacion": "Árbol 3 semillas vs 1 semilla (3 rep.)",
              **paired_bootstrap(y, lab["normal__razones_B"], lab["normal__razones_B_3sem"], n_boot=NB)})
extra.append({"comparacion": "Árbol nuevo vs híbrido de producción (3 rep.)",
              **paired_bootstrap(y, base["normal__hybrid"], lab["normal__razones_B_3sem"], n_boot=NB)})
extra.append({"comparacion": "Híbrido de producción vs su árbol solo (3 rep.)",
              **paired_bootstrap(y, base["normal__hgb"], base["normal__hybrid"], n_boot=NB)})
if fix is not None:
    cmp("Redes: arreglo vs producción", comp(base, "neural"), comp(fix, "fix_neural"))
if v2 is not None:
    cmp("Redes: arreglo+razones vs producción", comp(base, "neural"), comp(v2, "v2_neural"))
    cmp("Modelo con score: con redes vs árbol solo", comp(*HGB), mix(WITH, "normal"))
    cmp("Modelo sin score: con redes vs árbol solo", comp(*HGB_NS), mix(WITHOUT, "normal"))
cmp("Final vs producción", p_prod, p_final)
for prod in sorted(pd.unique(products)):
    cmp(f"Final vs producción · {prod}", p_prod, p_final, mask=products == prod)
pd.DataFrame(extra).to_csv(C.REPORTS / "v2_comparaciones.csv", index=False)

# ------------------------------------------------ resumen y artefactos
fin_b = boot(p_prod, p_final)
final_vac = auc(mix(final_parts(LAM), "score_vacio"))
res = pd.DataFrame([
    {"metrica": "auc_cv", "antes": auc(p_prod), "despues": auc(p_final)},
    {"metrica": "dependencia_pct", "antes": dep_prod, "despues": dep(final_parts(LAM))},
    {"metrica": "auc_score_vacio", "antes": auc(mix(PROD, "score_vacio")), "despues": final_vac},
    {"metrica": "auc_cv_ci_low", "antes": np.nan, "despues": fin_b["ci_low"]},
    {"metrica": "auc_cv_ci_high", "antes": np.nan, "despues": fin_b["ci_high"]},
])
res.to_csv(C.REPORTS / "v2_resumen.csv", index=False)

OUT.mkdir(parents=True, exist_ok=True)
choice = {
    "redes": NET_LABEL, "componente_redes": NET[1], "componente_redes_sin_score": NS[1] if NS else None,
    "peso_hgb_con_score": W, "peso_hgb_sin_score": W2, "peso_con_score": LAM,
    "peso_con_score_revolving": LAM_REV, "revolving_bootstrap": b_rev, "lam_revolving_mejor": lam_rev,
    "nota_peso_con_score": note_w, "nota_peso_sin_score": note_w2,
    "auc_oof_final": auc(p_final), "auc_oof_produccion": auc(p_prod), "diff_vs_produccion": fin_b,
    "dependencia_final_pct": dep(final_parts(LAM)), "dependencia_produccion_pct": dep_prod,
    "nota": "Repetición 0 de la validación cruzada 5 pliegues (las redes nuevas solo tienen 1 repetición).",
}
(OUT / "blend_choice.json").write_text(json.dumps(choice, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
np.savez_compressed(
    OUT / "final_oof.npz", y=y, products=products, fold_id=fold0, dev_idx=base["dev_idx"],
    **{f"final__{v}": mix(final_parts(LAM), v) for v in VARIANTS},
    **{f"prod__{v}": mix(PROD, v) for v in VARIANTS},
)
pd.set_option("display.width", 200)
print(search.pivot(index="peso_hgb", columns="modelo", values="auc").round(5).to_string())
print(curve.round(4).to_string(index=False))
print(cas.round(5).to_string(index=False))
print(pd.DataFrame(extra).round(5).to_string(index=False))
print(json.dumps(choice, ensure_ascii=False, indent=1, default=float))
