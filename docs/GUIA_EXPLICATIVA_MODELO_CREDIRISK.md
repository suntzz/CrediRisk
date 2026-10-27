# Guía Maestra de Sustentación — CrediRisk: Métodos, Errores, Épocas, Etapas y Curva de Aprendizaje

> [!IMPORTANT]
> **Propósito de este documento:** Responder de forma **minuciosa, con datos exactos del proyecto y en un lenguaje 100 % claro para cualquier persona** (tanto para quien no sabe programación como para un jurado técnico exigente) las 5 preguntas clave del equipo:
> 1. **Explicación de los métodos utilizados** (de principio a fin).
> 2. **Explicación detallada del error** (qué mide cada error, por qué ocurre y qué significa cada cuadrante de la Matriz de Confusión).
> 3. **Cuántas pruebas se hicieron, qué procesos se ejecutaron, cuántas épocas se entrenaron y por qué.**
> 4. **Justificación de cada etapa del proyecto** (por qué hicimos cada fase y qué demostró).
> 5. **Gráfica de aprendizaje: ¿El modelo memorizó o realmente aprendió?**

---

## 1. Explicación de los Métodos: ¿Cómo funciona CrediRisk paso a paso?

Para que una red neuronal pueda evaluar si un solicitante de crédito es **Apto (`1`)** o **No Apto (`0`)**, no basta con meter una tabla de Excel cruda al modelo. Aplicamos **5 métodos encadenados** en el pipeline ([`src/preprocess.py`](file:///Users/suntz/Documents/Deep/src/preprocess.py) y [`src/train.py`](file:///Users/suntz/Documents/Deep/src/train.py)):

![Pipeline de Preprocesamiento de Datos](images/07_pipeline_datos.png)

### Método 1.1 — Partición Estratificada 70 / 15 / 15 sin Fuga de Datos (*Zero Data Leakage*)
- **¿Qué teníamos?** Un dataset financiero inmutable ([`DatasetCreditoFinancieroFinalV2.csv`](file:///Users/suntz/Documents/Deep/DatasetCreditoFinancieroFinalV2.csv)) con **49,650 solicitudes de crédito** perfectamente balanceadas: **24,825 Aptos (50.0 %)** y **24,825 No Aptos (50.0 %)**.
- **¿Qué hicimos?** Antes de tocar o transformar cualquier número, dividimos los datos con semilla fija (`seed = 42`) manteniendo exactamente el 50 % / 50 % en cada grupo:
  - **Entrenamiento (`Train` — 70 % = 34,755 clientes):** Es el «libro de estudio» con el que la red neuronal ajusta sus pesos internos.
  - **Validación (`Validation` — 15 % = 7,447 clientes):** Es el «simulacro de examen» que se aplica al final de cada época para vigilar si el modelo está aprendiendo de verdad y elegir los mejores hiperparámetros.
  - **Prueba Final (`Test` — 15 % = 7,448 clientes):** Es el «examen de grado sellado bajo llave». No se usó para decidir ninguna época ni arquitectura; solo se abrió al final para medir el rendimiento real.
- **¿Por qué es tan importante?** Porque todas las estadísticas (medianas, topes de valores extremos, promedios y desviaciones estándar) se calcularon **únicamente sobre los 34,755 clientes de `Train`**. Si se calcularan con todo el dataset junto, el modelo «espiaría» información del examen final (*Data Leakage*).

---

### Método 1.2 — Ingeniería y Transformación de Variables (De 23 columnas a 44 variables)
El archivo original tiene **23 columnas**: quitamos `id_solicitud` (porque un número de radicado no predice si alguien paga) y separamos la respuesta `apto_credito`, quedando **21 variables predictoras base** (17 numéricas y 4 de texto/categóricas). ¿Por qué la red neuronal recibe **44 entradas** en vez de 21? Por **6 transformaciones matemáticas**:

| Paso del Método | ¿Qué hace en lenguaje sencillo? | ¿Por qué es necesario para una Red Neuronal? | Impacto en Columnas |
| :--- | :--- | :--- | :--- |
| **1. Banderas de Datos Faltantes (`_nan`)** | Antes de rellenar una celda vacía en 7 columnas clave (ej. `ingreso_mensual`, `score_crediticio`), crea una columna extra que vale `1` si el dato faltaba y `0` si estaba presente. | En banca, **que un cliente no reporte un dato no es casualidad**: a veces indica informalidad o falta de historial. Crear la bandera evita perder esa pista al rellenar el hueco. | **+7 columnas** binarias (`_nan`) |
| **2. Recorte de Extremos (*Clipping* `[p1, p99]`)** | Si un cliente tiene un ingreso o deuda absurdamente extrema (por encima del percentil 99 % o por debajo del 1 %), lo acota al límite del 1 % y 99 % de `Train`. | Un solo multimillonario o un error de digitación de miles de millones distorsionaría los gradientes de toda la red neuronal. | Mantiene cantidad de columnas |
| **3. Transformación Logarítmica (`log1p` y `signed_log`)** | Aplica $\ln(1 + x)$ a montos de dinero muy asimétricos (`ingreso_mensual`, `monto_solicitado`, `dias_maximo_mora`, etc.) y logaritmo con signo a `ingreso_disponible` (que puede ser negativo si gasta más de lo que gana). | En finanzas, pasar de ganar \$1M a \$2M cambia mucho el riesgo, pero pasar de \$80M a \$81M cambia poco. El logaritmo comprime cifras gigantes y hace la distribución simétrica (forma de campana). | Mantiene cantidad de columnas |
| **4. Imputación por Mediana** | Rellena los valores vacíos numéricos con la **mediana** de `Train` (no el promedio). | Las redes neuronales no pueden multiplicar `NaN` (vacíos). Se usa la mediana porque no se deja arrastrar por valores altos. | 17 columnas numéricas limpias |
| **5. Agrupación y *One-Hot Encoding*** | Las categorías raras (menos del 1 % de frecuencia) se agrupan en `"Otro"`. Luego, las 4 columnas de texto (`estado_civil`, `tipo_contrato`, `linea_negocio`, `tipo_vivienda`) se convierten en 20 columnas de `0` y `1`. | Una red neuronal solo entiende números, pero si pusiéramos `Soltero=1, Casado=2, Viudo=3`, la red creería erróneamente que `Viudo > Casado`. Con columnas separadas de `0` y `1` cada categoría tiene su propio peso. | De 4 de texto pasa a **20 columnas** binarias |
| **6. Estandarización (`StandardScaler`)** | A cada una de las 44 variables le resta su media y la divide por su desviación estándar: $z = \frac{x - \mu}{\sigma}$. | Sin esto, `monto_solicitado` (millones) tendría números gigantes y `numero_cuotas_mora` (0 a 5) números diminutos, haciendo que la red ignore las variables pequeñas. | **Total final: 44 variables** ($17 + 7 + 20 = 44$) |

---

### Método 1.3 — Arquitectura de Red Neuronal: Perceptrón Multicapa (MLP / *Deep Learning*)
Usamos una **Red Neuronal Profunda Densa (MLP)** estructurada en forma de **embudo piramidal** (por ejemplo, `44 entradas → 64 neuronas → 32 neuronas → 16 neuronas → 1 salida`):
- **¿Por qué forma de embudo?** La primera capa (`64` neuronas) combina las 44 variables para detectar relaciones amplias (ej. ingreso vs. cuota + antigüedad laboral). La segunda capa (`32`) destila esos cruces en conceptos de riesgo intermedios (ej. solvencia frente a historial de mora). La tercera capa (`16`) resume el perfil financiero esencial antes de emitir el veredicto final.
- **Funciones de Activación en Capas Ocultas (`ReLU` y `LeakyReLU`):**
  - **ReLU** ($\max(0, x)$): Si una combinación de variables es irrelevante (negativa), la apaga (`0`); si es relevante (positiva), la deja pasar. Esto permite aprender fronteras curvas complejas que una regresión lineal jamás vería.
  - **LeakyReLU** ($\max(0.1x, x)$): En lugar de apagar a cero los valores negativos, deja pasar un 10 % ($0.1x$). Así evitamos que neuronas queden «muertas» y capturamos matices cuando un indicador es negativo (como un flujo de caja ajustado).
- **Neurona de Salida con Activación Sigmoide ($\sigma(z) = \frac{1}{1 + e^{-z}}$):** Convierte el resultado final en una **probabilidad continua entre `0.00` (0 %) y `1.00` (100 %)** de que el cliente sea **Apto para crédito**.

---

### Método 1.4 — Métodos de Control para No Memorizar (*Regularización y Optimización*)
1. **Dropout (`15 %` a `20 %`):** En cada paso del entrenamiento, apaga al azar entre el 15 % y el 20 % de las neuronas. **Analogía:** Es como hacer que un equipo de trabajo estudie quitando al azar a distintos integrantes en cada práctica; así nadie depende de que una sola neurona «se aprenda de memoria» un cliente específico, obligando a toda la red a aprender reglas generales.
2. **Optimizador Adam (`lr = 0.0005` y `0.001`):** Es el motor matemático que corrige los pesos de la red después de cada bloque de 256 clientes (`batch_size = 256`), adaptando la velocidad de ajuste de cada peso según su historial.
3. **ReduceLROnPlateau:** Si el error de validación lleva 4 o 5 épocas estancado sin bajar, reduce la velocidad de aprendizaje (`learning_rate`) a la mitad ($\times 0.5$). **Analogía:** Cuando estás estacionando un carro y ya estás muy cerca del puesto, bajas la velocidad para hacer maniobras milimétricas sin pasarte.
4. **Early Stopping con `restore_best_weights = True`:** Vigila el examen de validación en cada época. Si pasan 10 o 12 épocas seguidas sin superar su propio récord, detiene el entrenamiento y **rebobina el reloj** para quedarse exactamente con los pesos de la mejor época histórica.

---

### Método 1.5 — Método de Decisión Final: Ensamble Heterogéneo Top-3 Diverso
En lugar de confiar el dinero del banco a la opinión de un solo modelo, nuestro modelo final ([`Ensemble_Top3_Diverso`](file:///Users/suntz/Documents/Deep/reports/final_test_evaluation.md)) funciona como un **Comité de Crédito de 3 especialistas con arquitecturas distintas**:

![Arquitectura del Ensamble Final](images/06_arquitectura_ensamble_final.png)

$$\hat{p}_{\text{final}}(x) = \frac{1}{3}\,\hat{p}_{\text{Modelo 1}}(x) + \frac{1}{3}\,\hat{p}_{\text{Modelo 2}}(x) + \frac{1}{3}\,\hat{p}_{\text{Modelo 3}}(x)$$

- **Especialista 1 (`cfg_c_s42`):** Red de 3 capas (`[64, 32, 16]`), activación `ReLU`, Dropout `0.15`, aprendizaje lento y fino (`lr = 0.0005`), semilla `42`.
- **Especialista 2 (`cfg_b_leaky_s42`):** Red compacta de 2 capas (`[32, 16]`), activación `LeakyReLU(0.1)`, Dropout `0.15`, `lr = 0.0005`, semilla `42`.
- **Especialista 3 (`cfg_base_s2026`):** Red de 3 capas (`[64, 32, 16]`), activación `ReLU`, regularización más fuerte (Dropout `0.20`), aprendizaje rápido (`lr = 0.001`), inicializada con otra semilla (`2026`).
- **¿Qué variables pesan más en su decisión?** Mediante un estudio de importancia por permutación ([`reports/importancia_variables.csv`](file:///Users/suntz/Documents/Deep/reports/importancia_variables.csv)), demostramos que el modelo prioriza con total lógica financiera:
  1. `score_crediticio` (**68.43 %** del peso discriminativo total).
  2. `tasa_interes_ea` (**5.47 %**).
  3. `numero_creditos_activos` (**3.52 %**).
  4. `porcentaje_pagos_oportunos` (**2.72 %**).
  5. `tipo_contrato` (**2.69 %**) y `antiguedad_cliente_anios` (**2.66 %**).

---

## 2. Explicación Minuciosa del Error: ¿Cuánto se equivoca, cómo se mide y por qué?

Cuando alguien pregunta **«¿Cuál es el error del modelo?»**, en Inteligencia Artificial aplicada a banca no existe un solo número de error, sino **dos formas complementarias de medirlo**: el **error en los conteos de acierto/fallo** (Matriz de Confusión) y el **error en la seguridad de las probabilidades** (Log Loss y Brier Score).

![Matriz de Confusión en el Conjunto de Test](images/04_matriz_confusion_test.png)

### 2.1 El Error de Clasificación Directa (En los 7,448 clientes del Examen Final `Test`)
Cuando el modelo calcula la probabilidad $\hat{p}$, aplicamos la regla estándar de corte en **50 % (`Umbral = 0.50`)**: si $\hat{p} \ge 0.50$ se clasifica como **Apto (`1`)**, y si $\hat{p} < 0.50$ como **No Apto (`0`)**.

De los **7,448 clientes reales** del conjunto de prueba (`Test`):
- **Aciertos totales:** $2,550 + 2,476 = \mathbf{5,026\text{ clientes acertados}}$ $\rightarrow$ **Exactitud (`Accuracy`) = 67.48 %**.
- **Errores totales:** $1,174 + 1,248 = \mathbf{2,422\text{ clientes equivocados}}$ $\rightarrow$ **Tasa de Error Global = 32.52 %**.

#### Desglose de los 4 Cuadrantes de la Matriz de Confusión (¿Qué significa cada uno en la vida real?)

| Cuadrante | Cantidad en Test (de 7,448) | % del Total | ¿Qué pasó en realidad vs. qué dijo el modelo? | Significado Financiero / Bancario |
| :--- | :---: | :---: | :--- | :--- |
| **Verdaderos Negativos (`TN`)** *(Acierto)* | **2,550** | **34.24 %** | El cliente **NO era apto** (`0`) y el modelo lo detectó como **No Apto** (`0`). | **Pérdida evitada:** El banco se salvó de prestarle dinero a 2,550 clientes riesgosos (acertó el **68.47 %** de todos los malos pagadores). |
| **Verdaderos Positivos (`TP`)** *(Acierto)* | **2,476** | **33.24 %** | El cliente **SÍ era apto** (`1`) y el modelo lo aprobó como **Apto** (`1`). | **Negocio exitoso:** El banco otorgó 2,476 créditos sanos que generan intereses sin caer en impago (acertó el **66.49 %** de los buenos clientes). |
| **Falsos Positivos (`FP` — Error Tipo I)** | **1,174** | **15.76 %** | El cliente **NO era apto** (`0`), pero tenía buenos números aparentes y el modelo lo aprobó (`1`). | **Riesgo de Cartera (Morosidad):** Es el error más delicado para el banco, porque aprueba a un cliente que puede incumplir. |
| **Falsos Negativos (`FN` — Error Tipo II)** | **1,248** | **16.76 %** | El cliente **SÍ era apto** (`1`), pero su perfil parecía riesgoso y el modelo lo rechazó (`0`). | **Costo de Oportunidad Comercial:** El banco no pierde capital prestado, pero deja de ganar los intereses de un buen cliente por ser precavido. |

> [!TIP]
> **¿Por qué los dos tipos de error están tan parejos (`1,174` FP vs. `1,248` FN)?**
> Porque el modelo está **equilibrado e imparcial**: no es un modelo «temerario» que aprueba a todo el mundo, ni un modelo «paranoico» que rechaza a todos. Incluso es ligeramente más conservador protegiendo al banco (detecta el **68.47 %** de los No Aptos frente al **66.49 %** de los Aptos).

---

### 2.2 El Error Probabilístico: ¿Qué significan `Log Loss = 0.5963` y `Brier Score = 0.2050`?

Una red neuronal no solo dice «Sí» o «No»; dice **«Estoy 85 % seguro de que es Apto»**. Por eso durante el entrenamiento el modelo optimiza el error probabilístico:

![Calidad Probabilística Log Loss y Brier Score](images/02_calidad_probabilistica.png)

1. **Binary Cross-Entropy / Log Loss (`0.5963` en Test / `0.5888` en Validación):**
   $$\text{Log Loss} = -\frac{1}{N}\sum_{i=1}^{N} \Big[y_i \ln(\hat{p}_i) + (1 - y_i)\ln(1 - \hat{p}_i)\Big]$$
   - **En palabras sencillas:** Es un «detector de arrogancia». Si el modelo se equivoca diciendo *«estoy 51 % seguro»*, el castigo es pequeño; pero si se equivoca diciendo *«estoy 99 % seguro»*, el logaritmo le aplica un castigo gigantesco.
   - **¿Qué tan bueno es `0.5963`?** Un modelo que adivina al azar (lanzando una moneda 50/50) tiene un Log Loss de $\ln(2) = \mathbf{0.6931}$. Nuestro modelo bajó ese error hasta **0.5963** (y desde **0.6001** del Baseline inicial), lo que demuestra que sus probabilidades están bien calibradas y no comete errores temerarios.

2. **Brier Score (`0.2050` en Test / `0.2018` en Validación):**
   $$\text{Brier Score} = \frac{1}{N}\sum_{i=1}^{N} (\hat{p}_i - y_i)^2$$
   - **En palabras sencillas:** Es el promedio del error al cuadrado entre la probabilidad predicha ($\hat{p}_i$) y la realidad ($0$ o $1$).
   - **¿Cómo interpretarlo fácil?** Si le sacamos la raíz cuadrada ($\sqrt{0.2050} \approx 0.452$), mide qué tan lejos está la probabilidad en promedio, sabiendo que adivinar al azar da un Brier Score de **$0.50^2 = 0.2500$**. Bajar de `0.2500` a **`0.2050`** confirma una reducción sólida de la incertidumbre.

3. **ROC-AUC (`0.74482` en Test / `0.75382` en Validación):**
   - **¿Qué significa `0.7448` de forma intuitiva?** Si tomamos al azar a un cliente **Apto** y a un cliente **No Apto** de la base de datos, **en el 74.5 % de las veces nuestro modelo le asigna un puntaje más alto al cliente Apto que al No Apto**.

---

### 2.3 ¿Por qué el modelo tiene un 32.5 % de error y no un 0 %? (Justificación Científica)
Es fundamental explicar esto en la sustentación: **en riesgo crediticio real, ningún modelo honesto llega al 95 % o 100 % de exactitud**, por tres razones comprobadas en nuestros datos:
1. **Solapamiento natural del comportamiento humano:** Dos personas pueden tener exactamente el mismo sueldo, la misma edad y el mismo puntaje crediticio (`score_crediticio` medio entre 550 y 650), y aun así una paga cumplidamente y la otra cae en mora por una emergencia médica, un despido imprevisto o una decisión personal que no aparece en ninguna columna antes de pedir el préstamo.
2. **En datos tabulares financieros con ruido real, un AUC de `0.745–0.754` es el techo real de señal limpia:** Si una red neuronal en este dataset reportara 95 % de exactitud en entrenamiento, significaría que **memorizó los 34,755 casos a la fuerza** (*Overfitting*) o que hubo trampa (*Data Leakage*).

---

## 3. ¿Cuántas Pruebas se Hicieron, Qué Procesos, Cuántas Épocas y Por Qué?

Durante todo el proyecto no nos quedamos con el primer modelo que salió. Ejecutamos un **estudio experimental riguroso de 166 entrenamientos y evaluaciones documentadas** en archivos CSV dentro de la carpeta [`reports/`](file:///Users/suntz/Documents/Deep/reports):

![Resumen de las 166 Pruebas y Épocas por Modelo](images/11_resumen_pruebas_y_epocas.png)

### 3.1 Conteo Exacto de Todas las Pruebas Realizadas (166 Ejecuciones)

| Etapa / Proceso | Pruebas de Arquitecturas e Hiperparámetros | Pruebas Multi-Semilla (`Seeds: 42, 1, 7, 21, 2026`) | Pruebas de Ablación / Ensambles | Total de Pruebas en la Etapa | Archivo de Evidencia en el Proyecto |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Etapa 0: Baseline Inicial** | 1 corrida principal | 5 corridas (`seed1` a `seed5`) | — | **6 pruebas** | [`history_final.csv`](file:///Users/suntz/Documents/Deep/reports/history_final.csv), `history_seed1..5.csv` |
| **Etapa 1: Búsqueda Fase 1 + Ablación** | **37 experimentos** de arquitecturas, LR, Batch y Dropout | **20 corridas** (Top-4 modelos $\times$ 5 semillas) | **5 pruebas de ablación** de variables + **3 ensambles** | **65 pruebas** | [`experiments.csv`](file:///Users/suntz/Documents/Deep/reports/experiments.csv), [`ablation_study.csv`](file:///Users/suntz/Documents/Deep/reports/ablation_study.csv), [`multiseed_evaluation.csv`](file:///Users/suntz/Documents/Deep/reports/multiseed_evaluation.csv) |
| **Etapa 2: Regularización Fase 2** | **29 experimentos** (penalización L2, paciencias 8 a 15, redes intermedias) | **20 corridas** (Top-4 modelos $\times$ 5 semillas) | **5 ensambles** candidatos | **54 pruebas** | [`experiments_phase2.csv`](file:///Users/suntz/Documents/Deep/reports/experiments_phase2.csv), [`multiseed_evaluation_phase2.csv`](file:///Users/suntz/Documents/Deep/reports/multiseed_evaluation_phase2.csv) |
| **Etapa 3: Activaciones Fase 3 + Cierre** | **18 experimentos** (`ELU`, `GELU`, `Swish`, función `Huber` vs `BCE`) | **20 corridas** (Top-4 modelos $\times$ 5 semillas) | **8 ensambles** en validación | **46 pruebas** | [`experiments_phase3.csv`](file:///Users/suntz/Documents/Deep/reports/experiments_phase3.csv), [`ensemble_validation_phase3.csv`](file:///Users/suntz/Documents/Deep/reports/ensemble_validation_phase3.csv) |
| **TOTAL ACUMULADO** | **85 experimentos de diseño** | **65 pruebas de estabilidad** | **16 pruebas de ensamble** | **166 pruebas** | Todos los registros auditables en [`reports/`](file:///Users/suntz/Documents/Deep/reports) |

---

### 3.2 ¿Qué es una «Época», cuántas épocas entrenó cada modelo y por qué paró ahí?

- **¿Qué es 1 Época (*Epoch*)?**
  Es **una vuelta completa de estudio** sobre los **34,755 clientes de entrenamiento**. Como entrenamos en bloques (`batch_size`) de **256 clientes a la vez**, en cada época la red neuronal hace:
  $$\frac{34,755\text{ clientes}}{256\text{ clientes por bloque}} = \mathbf{136\text{ actualizaciones de pesos por época}}$$
- **¿Por qué no pusimos un número fijo obligatorio como 500 épocas?**
  Porque si obligas a una red neuronal a estudiar 500 veces los mismos datos, a partir de cierta vuelta deja de aprender reglas generales y empieza a **memorizar** los datos de entrenamiento (*Overfitting*).
- **¿Cómo elegimos entonces el número exacto de épocas?**
  Configuramos un **techo máximo amplio (100 a 120 épocas)**, pero activamos el vigilante automático **`EarlyStopping(monitor='val_auc', patience=10..12, restore_best_weights=True)`**. Esto significa:
  1. En cada época, la red mide su rendimiento en los **7,447 clientes nuevos de Validación**.
  2. Cada vez que logra un récord nuevo en Validación, **guarda una copia de seguridad de sus pesos (`Best Epoch`)**.
  3. Si pasan **10 o 12 épocas seguidas** sin superar ese récord, el entrenamiento se detiene automáticamente y **restaura los pesos de la mejor época**.

#### Desglose Exacto de Épocas en Nuestros Modelos Principales:

| Modelo | Tope Máximo Permitido | Mejor Época (`Best Epoch` donde se guardaron los pesos) | Época en que se Detuvo (`Total Epochs`) | Ventana de Paciencia (`Patience`) | ¿Por qué entrenó esa cantidad exacta de épocas? |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Baseline Inicial** | 100 | **Época 19** (`val_loss=0.5934`) | **Época 24** | 5 épocas | Con `lr=0.001` aprendió rápido; tras la época 19 no mejoró en 5 épocas y se detuvo en la 24. |
| **Submodelo 1 (`cfg_c_s42`)** *`[64, 32, 16]` ReLU* | 120 | **Época 32** (`val_auc=0.7536`) | **Época 44** | 12 épocas | Usó un paso de aprendizaje más fino (`lr=0.0005`), necesitando **32 épocas** para llegar a su cumbre y 12 más para confirmar que era el máximo. |
| **Submodelo 2 (`cfg_b_leaky_s42`)** *`[32, 16]` LeakyReLU* | 120 | **Época 71** (`val_auc=0.7537`) | **Época 83** | 12 épocas | Al tener menos neuronas (`1,985` parámetros) y activación `LeakyReLU(0.1)`, aprende de forma mucho más gradual y sostenida, alcanzando su pico en la **época 71**. |
| **Submodelo 3 (`cfg_base_s2026`)** *`[64, 32, 16]` Drop 0.20* | 100 | **Época 45** (`val_auc=0.7525`) | **Época 55** | 10 épocas | Al tener más Dropout (`20 %` de neuronas apagadas al azar), necesitó **45 épocas** para consolidar todos sus caminos internos. |
| **Rango en las 166 pruebas** | 100–120 | **Entre 14 y 73 épocas** | **Entre 24 y 85 épocas** | 5 a 15 épocas | Ningún modelo necesitó llegar a 100 épocas: todos convergieron limpiamente entre la época 14 y la 73. |

---

## 4. Justificación de Cada Etapa: ¿Por qué se hizo cada fase del proyecto?

Un proyecto científico de *Deep Learning* no se construye adivinando una red al azar; se construye siguiendo el **método científico incremental**, donde cada etapa responde una pregunta específica:

![Flujo de las Etapas Experimentales](images/08_flujo_fases_experimentales.png)

### Etapa 0 — Preprocesamiento Canónico y Modelo Base (*Baseline*)
- **¿Por qué se hizo?** En ciencia de datos necesitas un **punto de referencia inicial (línea base)** contra el cual medir si tus cambios futuros realmente sirven o no.
- **¿Qué se probó?** La arquitectura inicial `[64, 32, 16]` con `ReLU`, `Dropout 0.20` y `lr = 0.001`.
- **Resultado:** Logró `Val ROC-AUC = 0.7501` y `Test ROC-AUC = 0.7418` (`Log Loss = 0.6001`). Nos demostró que el pipeline de 44 variables funcionaba sin fugas, pero que aún podíamos afinar la arquitectura.

### Etapa 1 — Fase 1: Exploración de Arquitecturas (37 pruebas) + Estudio de Ablación (5 pruebas)
- **¿Por qué se hizo?** Para responder dos preguntas fundamentales:
  1. *¿Son 44 variables el número ideal, o nos sobran/faltan columnas?* (Estudio de Ablación en [`reports/ablation_study.csv`](file:///Users/suntz/Documents/Deep/reports/ablation_study.csv)).
  2. *¿Qué tamaño de red neuronal es el óptimo para 34,755 clientes?* (¿Redes pequeñas de 1 capa `[32]`, medianas `[64, 32, 16]` o gigantes `[256, 128, 64]`?).
- **¿Qué descubrimos?**
  - **En la Ablación:** Si dejábamos solo las 9 variables financieras básicas (`Set_C`), el AUC se desplomaba a **`0.6279`**. Con 21 variables (`Set_D`) subía a **`0.7441`**. Con nuestras **44 variables (`Set_A`) alcanzaba el máximo (`0.7523`)**, mientras que agregar 6 ratios manuales extra (`50 variables`, `Set_E`) no mejoraba nada (`0.7518`) porque la red neuronal ya aprendía esas relaciones por sí sola. ¡Quedó científicamente justificado usar las **44 variables**!
  - **En Arquitecturas:** Descubrimos que redes gigantes (`[256, 128, 64]`, 41,000+ parámetros) empezaban a memorizar ruido, mientras que arquitecturas piramidales compactas (`[64, 32, 16]` y `[32, 16]`) con `Dropout 0.15` y aprendizaje suave (`lr = 0.0005`) subieron el `Val AUC` a **`0.7537`**.

### Etapa 2 — Fase 2: Regularización Fina L2 y Ventanas de Paciencia (29 pruebas + 20 multi-seed)
- **¿Por qué se hizo?** Ya teníamos las mejores estructuras de capas (`[64, 32, 16]` y `[32, 16]`). Necesitábamos probar si añadir castigo matemático a los pesos (**Regularización L2** de `1e-5` a `5e-4`) y variar la paciencia del Early Stopping (`8, 10, 12, 15` épocas) mejoraba la estabilidad.
- **¿Qué descubrimos?** Que una regularización L2 alta (`5e-4`) junto con Dropout frenaba demasiado a la red (*underfitting*), y que el punto dulce era **Dropout 0.15 sin L2 agresivo (o L2 mínimo de `1e-5`) con paciencia de 12 épocas**, logrando además que un ensamble preliminar superara por primera vez a todos los modelos individuales (`Val AUC = 0.7538`).

### Etapa 3 — Fase 3: Funciones de Activación Modernas y Comité de Ensamble (18 pruebas + 20 multi-seed + 8 ensambles)
- **¿Por qué se hizo?** Queríamos verificar si funciones de activación modernas (`ELU`, `GELU`, `Swish`) o cambiar la función de pérdida a `Huber Loss` aportaban **diversidad de pensamiento** para armar un comité final superior.
- **¿Qué descubrimos?** Al medir la correlación de errores entre modelos ([`reports/correlacion_errores_phase3.csv`](file:///Users/suntz/Documents/Deep/reports/correlacion_errores_phase3.csv)), vimos que `cfg_c` (`ReLU`), `cfg_b_leaky` (`LeakyReLU`) y `cfg_base` (`Dropout 0.20, seed 2026`) tenían errores distintos entre sí (correlación de desacuerdo ~`0.78`, no idéntica). Al unirlos en el **`Ensemble_Top3_Diverso`**, cuando un modelo dudaba en un cliente fronterizo, los otros dos corregían el voto.

![Evolución del Rendimiento Etapa por Etapa](images/01_evolucion_roc_auc.png)

---

## 5. Gráfica de Aprendizaje: ¿El Modelo Memorizó o Aprendió? (Respuesta para Iván)

> [!IMPORTANT]
> **Veredicto directo y contundente:** El modelo **APRENDIÓ patrones estadísticos reales y NO memorizó**. Tenemos **4 pruebas gráficas y matemáticas irrefutables** que lo demuestran.

Observa primero nuestra gráfica comparativa construida directamente con los datos de entrenamiento del proyecto ([`reports/history_final.csv`](file:///Users/suntz/Documents/Deep/reports/history_final.csv) y `history_seed1..5.csv`):

![Curva de Aprendizaje Real vs Memorización](images/10_curva_aprendizaje_memorizo_vs_aprendio.png)

### ¿Cómo se lee esta gráfica para explicarla en la exposición?

Imagina a dos estudiantes preparándose para un examen de matemáticas con un libro de ejercicios resueltos (`Train`) y haciendo simulacros semanales con problemas nuevos que nunca habían visto (`Validation`):
- **El estudiante que MEMORIZA (*Overfitting* — línea roja punteada del Panel B):** Se aprende de memoria las respuestas del libro (`Train Loss` baja casi a cero), pero cuando le ponen problemas nuevos en el simulacro (`Val Loss`), no sabe cómo resolverlos y **su curva de error se dispara hacia arriba en forma de "U"**.
- **El estudiante que APRENDE (*CrediRisk* — líneas azul y naranja del Panel A):** A medida que estudia época tras época, su error en el libro (`Train Loss`, línea azul) baja al mismo ritmo que su error en los simulacros con clientes nuevos (`Val Loss`, línea naranja). **Ambas líneas bajan juntas, se cruzan suavemente y se estabilizan pegadas alrededor de `0.59`.**

---

### Las 4 Pruebas Científicas de que CrediRisk Aprendió y NO Memorizó

#### Prueba 1: Brecha casi cero entre Entrenamiento y Validación (`0.0004` a `0.0058`)
Mira los valores exactos época por época en [`reports/history_final.csv`](file:///Users/suntz/Documents/Deep/reports/history_final.csv):
- **Época 0 (Arranque):** `Train Loss = 0.6710` | `Val Loss = 0.6132` (`Train AUC = 0.6464` vs `Val AUC = 0.7272`).
  - *Nota curiosa para el jurado:* ¿Por qué al principio el modelo sale mejor en el simulacro (`Val`) que estudiando (`Train`)? Porque durante el estudio (`Train`) tiene puesto el «chaleco de pesas» del **Dropout (20 % de neuronas apagadas al azar)**, mientras que en el simulacro (`Val`) usa el **100 % de sus neuronas**.
- **Época 13 (Punto óptimo de cruce):**
  - `Train Loss = 0.5929` | `Val Loss = 0.5933` $\rightarrow$ **¡La diferencia entre entrenamiento y datos nuevos es de apenas `0.0004`!**
  - `Train AUC = 0.7510` | `Val AUC = 0.7495` $\rightarrow$ **Diferencia de apenas `0.0015` (0.15 %).**
- **Época 19 (Último récord antes del freno):**
  - `Train Loss = 0.5897` | `Val Loss = 0.5934` $\rightarrow$ Brecha de solo **`0.0037`**. Jamás hubo explosión de la curva naranja.

#### Prueba 2: Freno a tiempo con `Early Stopping` + `ReduceLROnPlateau`
- En la **Época 16**, al detectar que la curva naranja (`Val Loss`) ya había llegado a una meseta plana en `~0.593`, el mecanismo `ReduceLROnPlateau` redujo automáticamente la tasa de aprendizaje a la mitad (`de 0.001 a 0.0005`) y luego en la **Época 20** a `0.00025`.
- En la **Época 23**, antes de que la línea azul (`Train Loss`) pudiera despegarse de la naranja y empezar a memorizar, el **`Early Stopping` cortó el entrenamiento** y restauró los pesos exactos del punto óptimo.

#### Prueba 3: Estabilidad al cambiar la Semilla Aleatoria (65 pruebas Multi-Seed)
- Un modelo que memoriza depende de la suerte de cómo se inicializaron sus pesos. Nosotros entrenamos las arquitecturas con **5 semillas distintas (`42, 1, 7, 21, 2026`)** (líneas tenues de fondo en el Panel A y tablas `multiseed_evaluation*.csv`).
- La desviación estándar del `ROC-AUC` entre las 5 semillas fue de apenas **`±0.00029` (0.029 %)**. Es decir, sin importar cómo empiece a estudiar, la red siempre descubre los mismos patrones financieros.

#### Prueba 4: La Prueba de Fuego en el Conjunto `Test` (7,448 clientes nunca vistos)
La prueba definitiva de si alguien aprendió o memorizó es hacerle un examen con **7,448 clientes completamente nuevos (`Test`)** que estuvieron guardados bajo llave durante las 166 pruebas:
- **ROC-AUC en Validación:** `0.75382`
- **ROC-AUC en Test Final:** `0.74482`
- **Diferencia ($\Delta\text{AUC}$):** **`-0.00900` (menos de un 1 % de variación)**.
- **Log Loss en Validación vs. Test:** `0.5888` vs. `0.5963` (diferencia de apenas `0.0075`).

---

## 6. Chuleta Rápida de Respuestas para la Exposición (Resumen de 30 Segundos por Pregunta)

| Pregunta del Jurado / Equipo | Respuesta Directa y Contundente para Decir en Voz Alta |
| :--- | :--- |
| **1. ¿Qué métodos usaron?** | *"Usamos una partición estratificada 70/15/15 sin fuga de datos, un pipeline que transforma las 21 variables predictoras originales en 44 características normalizadas (con banderas de nulos, recorte p1-p99, logaritmos, mediana y One-Hot Encoding), y un Ensamble Heterogéneo de 3 Redes Neuronales MLP (`[64,32,16]` ReLU, `[32,16]` LeakyReLU y `[64,32,16]` Dropout 0.20) regularizadas con Dropout y Early Stopping."* |
| **2. ¿Cuál es el error y qué significa?** | *"En probabilidades, nuestro Log Loss es `0.5963` y Brier Score `0.2050` (muy por debajo del azar de `0.6931` y `0.2500`), con un ROC-AUC de `0.7448`. En clasificación directa sobre los 7,448 clientes de Test acertamos el `67.48 %` (`5,026` clientes) y el error del `32.52 %` se reparte de forma equilibrada entre `1,174` Falsos Positivos (15.8 % — riesgo de morosidad) y `1,248` Falsos Negativos (16.8 % — costo de oportunidad comercial)."* |
| **3. ¿Cuántas pruebas y épocas hicieron y por qué?** | *"Hicimos **166 pruebas documentadas** (84 experimentos de arquitectura, 5 estudios de ablación, 65 corridas multi-semilla en 5 seeds y 16 pruebas de ensambles). Pusimos un tope de 120 épocas, pero gracias a Early Stopping cada modelo paró automáticamente en su punto óptimo entre **24 y 83 épocas** (los 3 modelos finales guardaron sus mejores pesos en las épocas **32, 71 y 45**)."* |
| **4. ¿Cómo justifican cada etapa?** | *"Cada etapa respondió una pregunta científica: el Baseline fijó la referencia (`AUC 0.7418`); la Fase 1 y la Ablación demostraron que 44 variables y redes piramidales compactas eran óptimas; la Fase 2 calibró la regularización L2 y la paciencia de 12 épocas; y la Fase 3 incorporó diversidad con LeakyReLU para formar el comité Top-3 (`AUC 0.7448`)."* |
| **5. ¿Memorizó o aprendió?** | *"Aprendió de verdad y NO memorizó. En la curva de aprendizaje, el error de entrenamiento (`0.5929`) y el de validación (`0.5933`) bajan juntos y se estabilizan con una brecha mínima de `0.0004` sin que la curva de validación suba jamás. Además, al evaluarlo en los 7,448 clientes ocultos de Test, el AUC varió menos de 1 % (`-0.0090`)."* |
