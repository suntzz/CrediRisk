# Corrida solicitada — score crediticio al 32 %

## Qué significa “32 %” en una red neuronal

No es válido asignar un porcentaje fijo del peso total a una variable dentro de
una red: sus parámetros y activaciones no admiten esa interpretación global.
Para aplicar la solicitud de forma reproducible, se enmascaró `score_crediticio`
en exactamente el **32 %** de las filas de entrenamiento de cada una de las tres
redes del ensamble. Al estar estandarizada, el valor enmascarado es 0 (la media).

## Comparación en validation

| Candidato | AUC | Brier | Caída AUC al permutar score |
|---|---:|---:|---:|
| Ensamble histórico | 0.75382 | 0.20177 | 0.16034 |
| Enmascaramiento de score 32 % | 0.75083 | 0.20292 | 0.14307 |

La variante 32 % disminuyó la dependencia medida del score, pero también bajó el
poder de discriminación y empeoró la calibración. No pasó el guardrail de promoción
(pérdida de AUC mayor que 0.002), por lo cual la aplicación publicada conserva el
ensamble histórico, que ofrece el resultado más sólido con este dataset.

Los datos completos están en `phase4_score32_candidate_comparison.csv` y la política
de decisión por producto está en `phase4_score32_product_policy.json`.
