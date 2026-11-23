# Informe técnico — optimización del modelo CrediRisk

Fecha de cierre: 23 de noviembre de 2026  
Alcance: entrenamiento, validación, política de decisión y publicación. No se
rediseñó ni se modificó la identidad visual del frontend.

## 1. Objetivo

Mejorar la capacidad de generalización del modelo sin escoger una red que memorice
el conjunto de entrenamiento. La métrica primaria fue ROC-AUC; se controlaron además
PR-AUC, log-loss, Brier y exactitud balanceada. La selección de modelos se hizo sobre
**validation**. El conjunto de **test** se mantuvo fuera del ajuste y se consultó una
vez con el candidato finalmente congelado.

## 2. Datos y protocolo reproducible

- Dataset: `DatasetCreditoFinancieroFinalV2.csv`, 49,650 registros.
- División estratificada y fija: train 34,755 (70%), validation 7,447 (15%) y test
  7,448 (15%); semilla 42.
- Preprocesamiento ajustado solo con train: clipping p1–p99, imputación por mediana,
  transformaciones logarítmicas, banderas de faltantes, one-hot de categorías y
  estandarización.
- Entrenamiento: batch size 128, máximo 120 épocas, `EarlyStopping` sobre `val_auc`
  (paciencia 16, restaurando los mejores pesos) y reducción de learning rate.
- Criterio de promoción: aumento de AUC de validación de al menos 0.001 frente al
  ensamble base, Brier no peor en más de 0.001 y brecha de pérdida train-validation
  menor o igual a 0.06.

## 3. Corrida solicitada del score al 32%

En una red no es técnicamente válido fijar una variable a “32% de peso global”. Para
aplicar la intención sin inventar una regla, `score_crediticio` se enmascaró en el
**32% de las filas de entrenamiento**; al estar estandarizado se reemplaza por 0
(su media). La prueba redujo la dependencia medida por permutación, pero no mejoró la
calidad del modelo:

| Modelo | AUC validation | Brier validation | Caída AUC al permutar score |
|---|---:|---:|---:|
| Ensamble base | 0.75382 | 0.20177 | 0.16034 |
| Score enmascarado 32% | 0.75083 | 0.20292 | 0.14307 |

Por tanto, la versión 32% **no se promovió**: bajar la dependencia no justifica una
peor discriminación y peor calibración.

## 4. Búsqueda de generalización Fase 5

Se entrenaron 4 familias x 3 semillas (42, 2026 y 7): 12 redes. Las configuraciones
incluyeron ELU regularizado, ELU con ruido gaussiano de entrada (activo solo al
entrenar), una red ELU más amplia con L2/dropout reforzado y una GELU compacta.

| Candidato (promedio de 3 semillas) | AUC validation | Brier | Época óptima media | Brecha de pérdida media |
|---|---:|---:|---:|---:|
| Ensamble base publicado | **0.75382** | **0.20177** | — | — |
| ELU + ruido de entrada | 0.75329 | 0.20181 | 60.3 | 0.00248 |
| ELU regularizado | 0.75294 | 0.20191 | 63.0 | 0.00410 |
| ELU amplio regularizado | 0.75265 | 0.20201 | 63.3 | 0.00005 |
| GELU compacto | 0.75186 | 0.20230 | 34.3 | 0.00787 |

Las brechas de pérdida pequeñas confirman que no hubo evidencia de memorización grave
en las candidatas; aun así, ninguna alcanzó el criterio de promoción. El ensamble
histórico se mantuvo porque conserva el mayor AUC y el mejor Brier.

El detalle de las **12 corridas**, incluidas épocas ejecutadas, mejor época, pérdida
de train, pérdida de validation y tiempo, está en
`reports/phase5_generalization_epochs.csv`. La tabla completa de selección está en
`reports/phase5_generalization_validation.csv`.

## 5. Híbrido promovido y prueba aislada

La búsqueda de modelos tabulares detectó interacciones que el ensamble neuronal no
capturaba por completo. Se entrenó un HistGradientBoosting regularizado y se combinó
con las redes mediante un promedio 65% árboles y 35% red. El peso se eligió solo en
validation. La mejora se confirmó una vez en test aislado.

| Modelo | AUC validation | Brier validation | AUC test | Brier test |
|---|---:|---:|---:|---:|
| Ensamble neuronal | 0.75382 | 0.20177 | 0.74482 | 0.20503 |
| HistGradientBoosting | 0.75785 | 0.20011 | 0.75030 | 0.20300 |
| Híbrido promovido | **0.75973** | **0.19940** | **0.75174** | **0.20235** |

El nuevo modelo de producción es el híbrido. En test supera al ensamble neuronal en
0.00692 AUC y reduce Brier en 0.00268.

| Segmento | AUC | PR-AUC | Brier | Exactitud balanceada | Umbral |
|---|---:|---:|---:|---:|---:|
| Global | 0.75174 | 0.74522 | 0.20235 | 0.68408 | 0.50 |
| Cash loans | 0.75305 | 0.73849 | 0.20180 | 0.68304 | 0.53 |
| Revolving loans | 0.71405 | 0.79934 | 0.20837 | 0.66858 | 0.67 |

Los umbrales se escogen en validation maximizando exactitud balanceada por línea de
negocio; no son valores inventados. No se habilitó crédito hipotecario: el dataset no
contiene observaciones hipotecarias etiquetadas, por lo que reutilizar un umbral de
consumo sería metodológicamente incorrecto.

## 6. Prueba de balance uniforme de variables

Todas las variables ya entran estandarizadas al modelo y reciben parámetros propios.
Para comprobar si limitar la dominancia de alguna mejoraba el AUC, se aplicó *feature
dropout* uniforme durante entrenamiento: cada variable procesada tuvo la misma
probabilidad de quedar temporalmente enmascarada. No se fijaron pesos manuales, pues
eso no está respaldado por el dataset.

| Candidato | Tasa uniforme | AUC validation | Brier validation |
|---|---:|---:|---:|
| Ensamble base | 0% | **0.75382** | **0.20177** |
| Feature dropout | 5% | 0.75142 | 0.20300 |
| Feature dropout | 10% | 0.75144 | 0.20336 |

Las dos variantes redujeron AUC y empeoraron Brier. El resultado respalda mantener
los pesos aprendidos por el ensamble actual. Los detalles por red y época están en
`reports/phase6_feature_balance_epochs.csv` y
`reports/phase6_feature_balance_validation.csv`.

## 7. Cambios implementados

1. Se añadió regularización opcional de ruido de entrada al constructor experimental.
2. Se creó `phase5_generalization_search.py`, que guarda modelos por semilla,
   historial de épocas, métricas de validation, test y política por producto.
3. Se añadió HistGradientBoosting y una mezcla 65% árboles / 35% redes; el híbrido
   superó el modelo anterior en validation y test.
4. Se exportaron los nodos del modelo de árboles al bundle estático y se comprobó que
   GitHub Pages reproduce exactamente su probabilidad Python.
5. No se cambiaron layouts ni estilos. Solo se aclaró el campo de respaldo
   patrimonial y se corrigió su escala real de 0 a 4.

## 8. Pruebas realizadas

- Compilación de los módulos Python modificados con `py_compile`.
- Inferencia directa para Cash loans y Revolving loans, verificando umbrales 0.51 y
  0.63 respectivamente.
- Validación de que Mortgage loans devuelve una respuesta controlada hasta disponer
  de datos etiquetados.
- `git diff --check`.
- Build de producción del frontend con `npm run build`.
- Verificación de GitHub Pages y del `model_bundle.json` publicado.
- Paridad exacta entre la evaluación estática del árbol y `predict_proba` de Python.

## 9. Limitaciones y siguiente paso responsable

No existe una mejora honesta que pueda garantizarse únicamente cambiando arquitectura
si los datos no aportan nueva señal predictiva. El siguiente incremento relevante es
incorporar y etiquetar datos históricos de crédito hipotecario, validar estabilidad
temporal y recalibrar con datos representativos del portafolio real. No se recomienda
forzar pesos manuales ni promocionar una red con métricas inferiores.
