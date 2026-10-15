# Entrega 2: regla de seleccion y evaluacion final (pre-registro)

Redactado el 2026-10-14, despues de los bloques R, O y K y del analisis post hoc, y **antes de ver ningun
resultado del bloque S** (ensambles de 20 semillas). No se modifica despues de conocer esos resultados.

## Hechos que motivan la regla
* Ninguna tecnica aislada de los bloques R/O/K mejoro el ensamble de 3 semillas de A3 en Validacion.
* La calibracion post hoc, el promedio en logits y los pesos de ensamble no mejoraron con ajuste cruzado
  (`reports/entrega2_posthoc.csv`), por lo que los ensambles finales usan **promedio simple de probabilidades**.
* La ganancia del ensamble de 3 semillas sobre la red individual (≈0.003) indica alta varianza entre semillas.

## Candidatos (solo Validacion)
1. **Via neuronal pura** (sin profesor externo): la de menor Log Loss de Validacion entre
   `A3 x20`, `C4 x20` y `A3 x20 + C4 x20` (pesos iguales). Es una sola eleccion entre 3 opciones fijadas de antemano.
2. **Via hibrida** (destilacion desde LightGBM): `A3 x20 + E3 x20`. Solo se reporta en Validacion.

Referencia de comparacion en Validacion: `Ensemble_PLE_Fase4` (10 redes, Log Loss Val 0.58431,
predicciones en `artifacts/phase4/final_preds.npz`), mediante bootstrap pareado (2000 remuestreos).

## Evaluacion en Test (una sola vez)
* Se evalua en Test **unicamente** el candidato de la via neuronal pura, una vez, con
  `src/entrega2_final.py`. Motivo: es el resultado que falta para afirmar un modelo 100% red neuronal, y
  ese modelo nunca se evaluo en Test.
* La via hibrida no se evalua en Test en esta entrega, para no hacer comparaciones multiples sobre Test.
* Test ya se uso en la Fase 4 para evaluar `Ensemble_PLE_Fase4` y LightGBM, aunque no para seleccionar.
  Por tanto Test **ya no es una muestra totalmente virgen** para este proyecto, y el resultado de
  Entrega 2 en Test se presenta con esa salvedad.
* Comparaciones en Test: contra el baseline y contra `Ensemble_PLE_Fase4`, reutilizando sus
  predicciones ya calculadas en Fase 4 (no se re-evaluan esos modelos).

## Criterio de recomendacion
* El candidato puro se recomienda como modelo principal si su Log Loss de Validacion es menor que 0.58431.
  La mejora se califica como **robusta** solo si el IC 95% del bootstrap pareado en Validacion excluye 0.
* Si no es menor, se mantiene `Ensemble_PLE_Fase4` como mejor modelo registrado, y el candidato puro se
  documenta como la mejor alternativa sin profesor externo.
