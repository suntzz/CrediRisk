# Fase 4: Optimizacion orientada a minimizar la Log Loss

## Objetivo

Reducir la perdida de entropia cruzada binaria (Log Loss) del modelo congelado `Ensemble_Top3_Diverso`
(Test LL = 0.59631), manteniendo el protocolo del proyecto:

* Mismas particiones 70/15/15 (semilla 42). Los indices se reconstruyen y se verifican contra `artifacts/splits.npz`.
* Todo ajuste (codificadores, cuantiles, profesor de destilacion, hiperparametros de LightGBM) se calcula solo con Train.
* Seleccion de configuraciones exclusivamente en Validacion.
* Test se evaluo **una sola vez**, al final, con `src/phase4_final.py`.

## Cambio metodologico previo: parada temprana sobre la Log Loss real

En las Fases 2-3 la regularizacion L2 se aplicaba como `kernel_regularizer`, por lo que la `val_loss` que
monitoreaba la parada temprana incluia el termino de penalizacion (por eso los CSV de Fase 3 muestran
`Val_Loss` ~0.60 para redes cuya Log Loss real es ~0.590). En Fase 4 la regularizacion de pesos se aplica
como *weight decay* desacoplado (AdamW) y la `val_loss` monitoreada es exactamente la Log Loss.

## Diagnostico: de donde viene la perdida

Se uso LightGBM (hiperparametros elegidos con Optuna, 40 pruebas, CV 5-fold solo sobre Train) como
instrumento de diagnostico:

| Variante LightGBM | Log Loss Val | Lectura |
| :--- | :---: | :--- |
| Datos crudos | 0.5812 | Referencia |
| Mismas 44 variables preprocesadas que recibe la red | 0.5819 | El preprocesamiento original **no** pierde informacion relevante |
| Aditivo puro (sin interacciones) | 0.5847 | Equivale a la mejor red de Fase 4 |
| Interacciones de a pares (profundidad 2) | 0.5813 | Equivale al modelo completo |
| Red original Fase 1-3 (3 semillas) | 0.5908 | |

Conclusiones:

1. La mayor parte de la brecha de la red original (0.5908 → 0.5847) se debe a que el MLP con entradas
   estandarizadas no modela bien las **formas no lineales univariadas**. Ejemplo: la tasa de aptos frente a
   `tasa_interes_ea` es no monotona (≈0.61 en 48-55% EA, cae a ≈0.44 en 55-63% EA y a ≈0.31 por encima de 98%).
2. El resto (0.5847 → 0.5812) son interacciones de a pares **difusas** (ningun par aporta mas de ~4.5% de la
   ganancia; los mas relevantes combinan `tasa_interes_ea`, `score_crediticio`, `antiguedad_laboral_anios` y
   `porcentaje_pagos_oportunos`).

## Experimentos (Validacion, 3 semillas por configuracion: 42, 1, 7)

Detalle completo: [experiments_phase4_nn.csv](experiments_phase4_nn.csv). Todas usan `[64, 32, 16]` salvo indicacion.

| Bloque | Experimento | LL por semilla | LL ensamble 3 | AUC ensamble |
| :--- | :--- | :---: | :---: | :---: |
| A. Codificacion | A1 base (reproduccion del pipeline original) | 0.59234 | 0.59084 | 0.75180 |
| | A2 QuantileTransformer → normal | 0.59622 | 0.59425 | 0.74877 |
| | **A3 PLE 16 tramos** | 0.58823 | **0.58505** | 0.75717 |
| | A4 PLE 8 tramos | 0.58883 | 0.58631 | 0.75592 |
| C. Regularizacion sobre PLE | C1 dropout 0.3 + AdamW | 0.59068 | 0.58859 | 0.75555 |
| | C2 [128, 64] dropout 0.4 + input dropout | 0.58992 | 0.58901 | 0.75591 |
| | C3 [32, 16] | 0.58894 | 0.58631 | 0.75616 |
| | C4 ELU, dropout 0.3, batch 512, AdamW | 0.58685 | 0.58635 | 0.75610 |
| | C5 PLE 32 tramos, [128, 64] | 0.59029 | 0.58917 | 0.75626 |
| D. Interacciones explicitas | D1/D2 rama Cross DCN-v2 | 0.597-0.600 | 0.592 | 0.752 |
| | D3 embedding no lineal por variable (MLP-PLE) | 0.58963 | 0.58623 | 0.75574 |
| | D5 Cross sobre entrada base | 0.61305 | 0.59859 | 0.74553 |
| E. Destilacion desde LightGBM | E1 PLE, 50% etiqueta + 50% profesor | 0.58683 | 0.58544 | 0.75762 |
| | E2 PLE, 100% profesor | 0.58652 | 0.58618 | **0.75888** |
| | **E3 PLE + ELU + dropout 0.3 + destilacion 50%** | **0.58621** | 0.58596 | 0.75664 |
| | E4 base (sin PLE) + destilacion 50% | 0.59165 | 0.59088 | 0.75217 |

Lecturas:

* **PLE (Piecewise Linear Encoding, Gorishniy et al., 2022)** es el cambio de mayor impacto: cada variable
  numerica se representa ademas por 16 tramos definidos por cuantiles de Train, con codificacion lineal a
  trozos. Reduce la Log Loss del ensamble de 3 semillas de 0.5908 a 0.5851.
* Las redes PLE convergen en ~12 epocas. Regularizar mas (bloque C) mejora cada red individual pero reduce la
  diversidad entre semillas, por lo que el ensamble no mejora.
* Las capas Cross (DCN-v2) **empeoran** sistematicamente: los productos entre variables con colas pesadas
  generan alta varianza y sobreajuste temprano.
* **Destilacion de conocimiento**: entrenar contra `(1-a)·y + a·p_LightGBM`, donde `p_LightGBM` es la prediccion
  *out-of-fold* (5-fold) sobre Train, produce las mejores redes individuales. La parada temprana y todas las
  metricas siguen calculandose contra las etiquetas reales. El modelo desplegado sigue siendo 100% red neuronal.
  Sin PLE no aporta (E4), asi que no sustituye a la codificacion.
* Combinar mas de dos configuraciones mejora menos de 0.0002 en Validacion (ruido), por lo que se eligio la
  combinacion mas simple: A3 + E3.

## Modelo final de Fase 4: `Ensemble_PLE_Fase4`

* Codificador: pipeline original (44 variables) + PLE de 16 tramos para cada variable numerica = 268 entradas
  (`artifacts/phase4/encoder_phase4.joblib`).
* 10 redes: A3 (ReLU `[64, 32, 16]`, dropout 0.15, Adam 5e-4, batch 128) y E3 (ELU `[64, 32, 16]`, dropout 0.3,
  AdamW 5e-4 / wd 0.03, batch 512, destilacion 50%), cada una con las semillas 42, 1, 7, 21 y 2026.
* Agregacion: media aritmetica de probabilidades. Umbral 0.5 (igual que el baseline).
* Manifiesto: `artifacts/phase4/final_manifest.json`. Inferencia: `python src/predict.py --json data/ejemplo_solicitante.json --phase4`.

## Evaluacion final en Test (unica)

Fuente: [phase4_final_test.csv](phase4_final_test.csv). Δ = diferencia de Log Loss frente al baseline;
IC 95% por bootstrap pareado (2000 remuestreos de las 7,448 filas de Test).

| Modelo | LL Val | **LL Test** | Δ LL Test [IC 95%] | AUC Test | PR-AUC Test | Brier Test | Accuracy Test | F1 Test |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Baseline `Ensemble_Top3_Diverso` | 0.58885 | 0.59631 | — | 0.74482 | 0.73512 | 0.20503 | 67.48% | 0.6716 |
| **`Ensemble_PLE_Fase4` (solo redes)** | 0.58431 | **0.59293** | **−0.00338** [−0.00593, −0.00085] | 0.74842 | 0.73996 | 0.20362 | 68.22% | 0.6806 |
| Referencia LightGBM (5 semillas) | 0.58068 | 0.58894 | −0.00737 [−0.01089, −0.00367] | 0.75315 | 0.74557 | 0.20185 | 68.76% | 0.6898 |
| Hibrido red + LightGBM (peso 0.90 elegido en Val) | 0.58064 | 0.58892 | −0.00739 [−0.01078, −0.00384] | 0.75311 | 0.74544 | 0.20186 | 68.81% | 0.6903 |

* La mejora de la red de Fase 4 sobre el baseline es estadisticamente significativa (IC 95% no incluye 0;
  p bootstrap = 0.0045) y se acompaña de mejoras en todas las demas metricas.
* La mejora relativa de Val a Test se mantiene (−0.0045 en Val, −0.0034 en Test): la seleccion en Validacion
  produjo solo un optimismo leve.
* Si la restriccion de "solo redes neuronales" no es obligatoria, LightGBM duplica la reduccion de perdida
  (−0.0074). El hibrido asigna 90% del peso al GBDT y no mejora a LightGBM solo: en estos datos la red no
  aporta informacion que el GBDT no capture.

## Limitaciones

* Particion unica (sin validacion cruzada anidada), igual que en fases previas.
* Se evaluaron 18 configuraciones neuronales en Validacion; el leve aumento de la diferencia Val→Test es
  coherente con ese sesgo de seleccion.
* La destilacion hace que el entrenamiento de las redes E3 dependa de LightGBM (solo en entrenamiento, no en inferencia).
* Las redes se entrenaron en Windows (CPU, TensorFlow 2.18); los resultados pueden variar ligeramente en otra plataforma.

## Reproduccion

```bash
python src/phase4_baseline_check.py   # verifica splits y reproduce LL del baseline
python src/phase4_gbdt.py             # LightGBM + Optuna (CV en Train)
python src/phase4_teacher_oof.py      # profesor OOF para destilacion
python src/phase4_run_nn.py --block A # bloques A, C, D, E
python src/phase4_final.py --configs A3_ple16_relu,E3_ple16_elu_d30_distill05 --seeds 5
```
