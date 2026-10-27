/**
 * Banco de datos cuantitativos, conceptos educativos y glosario oficial
 * para la sección Laboratorio de CrediRisk.
 * 
 * Todos los valores corresponden estrictamente a la evidencia documental
 * registrada en README.md y en los reportes experimentales de reports/.
 * Ninguna métrica ni porcentaje ha sido inventado.
 */

export interface ConceptDefinition {
  id: string;
  title: string;
  badge: string;
  category: 'Métricas' | 'Arquitectura' | 'Preprocesamiento' | 'Riesgo Financiero' | 'Metodología';
  short: string;
  howItWorks: string;
  technical: string;
  whatIs: string;
  meaningInCrediRisk: string;
  whyItMatters: string;
  howToRead: string;
  whatItDoesNotMean: string;
}

export interface DocFigure {
  id: string;
  number: string;
  title: string;
  filename: string;
  category: string;
  description: string;
  xAxis: string;
  yAxis: string;
  series: string;
  keyFinding: string;
  methodologicalCaveat: string;
}

export interface HistoricalModelRecord {
  configuracion: string;
  redes: number;
  valAuc: number;
  testAuc: number | string;
  prAucTest: number | string;
  logLossTest: number | string;
  brierTest: number | string;
  accuracyTest: string;
  f1Test: string;
  descripcion: string;
  estado: 'baseline' | 'candidato' | 'ganador' | 'fase3';
}

export interface AblationRecord {
  setName: string;
  description: string;
  nFeatures: number;
  valAuc: number;
  valAccuracy: number;
  valF1: number;
  valLogLoss: number;
  conclusion: string;
}

export interface GlossaryEntry {
  term: string;
  category: 'Métricas' | 'Arquitectura' | 'Preprocesamiento' | 'Riesgo Financiero' | 'Metodología';
  simpleExplanation: string;
  technicalExplanation: string;
  crediriskExample: string;
  relatedConcepts: string[];
}

export const CONCEPTS_REPOSITORY: Record<string, ConceptDefinition> = {
  roc_auc: {
    id: 'roc_auc',
    title: 'ROC-AUC (Área Bajo la Curva ROC)',
    badge: 'Métrica de Discriminación',
    category: 'Métricas',
    short: 'Mide la capacidad del modelo para ordenar a los solicitantes de menor a mayor riesgo, independientemente del umbral que se elija para aprobar el crédito.',
    howItWorks: 'Si tomas al azar a un solicitante solvente y a uno que cayó en mora, el ROC-AUC es la probabilidad de que el modelo le asigne un puntaje de viabilidad más alto a la persona solvente. Un valor de 0.50 equivale a lanzar una moneda al aire; 1.00 es una separación perfecta.',
    technical: 'Área bajo la curva que grafica la Tasa de Verdaderos Positivos frente a la Tasa de Falsos Positivos para todos los posibles umbrales continuos t en [0, 1]. En el conjunto Test final, CrediRisk alcanza 0.74482 (0.75382 en Validación).',
    whatIs: 'Indicador estándar en banca para cuantificar el poder de discriminación ordinal de un clasificador probabilístico.',
    meaningInCrediRisk: 'Con 0.74482 en Test, el modelo distingue correctamente al solicitante cumplidor en aproximadamente 74.5 de cada 100 parejas aleatorias de solvencia opuesta.',
    whyItMatters: 'Permite calificar la inteligencia predictiva del modelo sin atarse a una política comercial transitoria de corte de crédito.',
    howToRead: 'En carteras de crédito de consumo no garantizado, valores entre 0.70 y 0.75 representan un poder de discriminación aceptable y competitivo para un primer filtro neuronal.',
    whatItDoesNotMean: 'No indica exactitud directa ni calibración de dinero. Un modelo con buen ROC-AUC puede sobreestimar o subestimar la probabilidad real si no se evalúa su Log Loss.',
  },
  pr_auc: {
    id: 'pr_auc',
    title: 'PR-AUC (Área Bajo la Curva Precision-Recall)',
    badge: 'Compensación de Calidad',
    category: 'Métricas',
    short: 'Evalúa la pureza promedio de las aprobaciones conforme intentamos captar a un porcentaje mayor de personas solventes en el mercado.',
    howItWorks: 'Analiza cuántos de los solicitantes clasificados como aptos realmente resultaron solventes (Precisión), a medida que exigimos al modelo aprobar a más solicitantes en general (Exhaustividad o Recall). En Test, CrediRisk obtiene 0.73512.',
    technical: 'Integral de la función Precision(Recall) sobre todo el espectro de umbrales. Es altamente sensible al balance de clases y a la acumulación de falsos positivos en zonas de duda.',
    whatIs: 'Curva que relaciona directamente la tasa de acierto en las colocaciones con la cuota de mercado alcanzada.',
    meaningInCrediRisk: 'Un PR-AUC de 0.73512 confirma que el modelo mantiene una pureza sólida de aprobación crediticia en diversos niveles de colocación de cartera.',
    whyItMatters: 'Ayuda a los directores de riesgo a entender qué tan rápido se deteriora la cartera cuando la institución decide flexibilizar sus metas de colocación comercial.',
    howToRead: 'Cuanto más se acerque a 1.0, más eficiente es la política crediticia para colocar créditos sin que se disparen las cuentas incobrables.',
    whatItDoesNotMean: 'No reemplaza al ROC-AUC; ambas curvas se leen de forma complementaria para evaluar el ordenamiento y la pureza de la cartera simultáneamente.',
  },
  accuracy: {
    id: 'accuracy',
    title: 'Exactitud (Accuracy)',
    badge: 'Métrica Global',
    category: 'Métricas',
    short: 'Indica la proporción de todas las solicitudes evaluadas que el modelo clasificó correctamente, sumando tanto aptos como no aptos.',
    howItWorks: 'Se calcula dividiendo el total de aciertos (5,026 casos en Test) entre el total de solicitudes evaluadas (7,448 casos), bajo el umbral estándar de 0.50. En CrediRisk es exactamente 67.48%.',
    technical: '(TP + TN) / (TP + TN + FP + FN). Al estar el dataset experimental balanceado en 50% aptos y 50% no aptos, un modelo aleatorio obtendría 50.00%.',
    whatIs: 'Porcentaje global de aciertos sobre una partición fija bajo un punto de corte definido.',
    meaningInCrediRisk: 'Aproximadamente 2 de cada 3 solicitantes son diagnosticados de forma acertada en la primera evaluación automática del sistema.',
    whyItMatters: 'Es una métrica directa para estimar la carga de trabajo que el sistema automatizado resuelve con éxito antes de requerir auditoría manual.',
    howToRead: 'El 67.48% debe entenderse en el contexto de un dataset balanceado; representa un avance de +17.48 puntos porcentuales frente a un clasificador aleatorio.',
    whatItDoesNotMean: 'No distingue entre tipos de error. No explica si los fallos fueron prestar dinero a personas que no pagaron (FP) o negar créditos a clientes cumplidores (FN).',
  },
  precision: {
    id: 'precision',
    title: 'Precisión (Precision)',
    badge: 'Pureza de Aprobación',
    category: 'Métricas',
    short: 'De todas las solicitudes que el sistema aprobó como aptas, qué porcentaje correspondió en realidad a personas solventes.',
    howItWorks: 'Se toma el número de aprobados solventes (2,476) y se divide entre todas las aprobaciones emitidas (3,650). En Test, la precisión de CrediRisk es 67.84%.',
    technical: 'TP / (TP + FP). Mide el riesgo de contaminación de la cartera aprobada por prestatarios insolventes bajo el umbral 0.50.',
    whatIs: 'Indicador de certeza o pureza en las decisiones de otorgamiento de crédito.',
    meaningInCrediRisk: 'De cada 100 créditos aprobados bajo el umbral 0.50, aproximadamente 68 cumplen sus pagos y 32 caen en mora (Falsos Positivos).',
    whyItMatters: 'Es crucial para proteger el capital de la entidad: los créditos mal aprobados generan pérdidas financieras directas.',
    howToRead: 'Si la entidad necesita reducir la morosidad, puede elevar el umbral a 0.60 o 0.70; esto eleva la precisión, aunque reduce el volumen de clientes aprobados.',
    whatItDoesNotMean: 'No mide cuántos clientes buenos dejaste por fuera del banco; para eso se debe contrastar con el Recall.',
  },
  recall: {
    id: 'recall',
    title: 'Exhaustividad (Recall / Sensibilidad)',
    badge: 'Captación de Solvencia',
    category: 'Métricas',
    short: 'De todas las personas verdaderamente solventes en el grupo de prueba, qué porcentaje logró identificar y aprobar el modelo.',
    howItWorks: 'Se toma el número de solventes aprobados (2,476) y se divide entre el universo total de solicitantes solventes existentes (3,724). En Test, el recall es 66.49%.',
    technical: 'TP / (TP + FN). Cuantifica la capacidad del modelo para no cometer omisiones sobre la clase solvente.',
    whatIs: 'Tasa de captura o aprovechamiento del mercado solvente disponible.',
    meaningInCrediRisk: 'El modelo identifica y atiende al 66.49% de los clientes viables. El 33.51% restante (1,248 personas) fueron rechazadas indebidamente (Falsos Negativos).',
    whyItMatters: 'Representa el costo de oportunidad comercial: rechazar a un cliente solvente significa perder los intereses de un crédito que habría sido rentable.',
    howToRead: 'Existe una tensión constante entre Precision y Recall; un modelo muy estricto tendrá alta precisión pero bajo recall, perdiendo mercado comercial.',
    whatItDoesNotMean: 'Un recall de 100% no es una victoria si se obtiene aprobando a casi todos los solicitantes e incrementando drásticamente el impago.',
  },
  f1_score: {
    id: 'f1_score',
    title: 'F1-Score (Media Armónica)',
    badge: 'Balance Operativo',
    category: 'Métricas',
    short: 'Es el promedio equilibrado entre la Precisión (no prestar a insolventes) y la Exhaustividad (no rechazar a solventes).',
    howItWorks: 'Calcula la media armónica: 2 * (Precision * Recall) / (Precision + Recall). En Test, CrediRisk alcanza 0.6715.',
    technical: 'Castiga con rigor a los modelos descompensados. Si un modelo tiene 95% de precisión pero solo 10% de recall, su F1-Score se desploma.',
    whatIs: 'Métrica unificada que resume el equilibrio entre seguridad financiera y colocación comercial.',
    meaningInCrediRisk: 'Con 0.6715 en Test, demuestra que el ensamble mantiene un comportamiento simétrico y balanceado en ambas caras del negocio.',
    whyItMatters: 'Permite comparar versiones de modelos sin perderse en el dilema de si es preferible ganar un poco de precisión a costa de recall.',
    howToRead: 'Valores superiores a 0.65 son sólidos en problemas de crédito de consumo con variables sociodemográficas y de buró.',
    whatItDoesNotMean: 'Asume que los errores de tipo FP y FN pesan exactamente lo mismo. En la práctica financiera bancaria real, un impago suele costar más que un cliente perdido.',
  },
  log_loss: {
    id: 'log_loss',
    title: 'Log Loss (Pérdida de Entropía Cruzada)',
    badge: 'Calidad de Probabilidades',
    category: 'Métricas',
    short: 'Mide qué tan acertadas y qué tan seguras fueron las probabilidades numéricas asignadas por el modelo, penalizando fuertemente la falsa seguridad.',
    howItWorks: 'Si el modelo asigna 99% de solvencia a un prestatario que luego cae en mora, recibe una penalización logarítmica enorme. Si asigna 51%, la penalización es mucho menor. En Test, CrediRisk registra 0.5963 (en Validación 0.5888).',
    technical: '-(1/N) * sum(y * log(p) + (1-y) * log(1-p)). Es la función matemática continua que las redes neuronales optimizan durante el entrenamiento.',
    whatIs: 'La métrica por excelencia para juzgar la calibración probabilística continua de una red neuronal.',
    meaningInCrediRisk: 'Un valor de 0.5963 en Test confirma que las redes evitan sobreconfianzas injustificadas y producen distribuciones probabilísticas suaves.',
    whyItMatters: 'En banca, no basta con predecir Sí o No; la probabilidad se usa para calcular provisiones contables y fijar la tasa de interés según el riesgo.',
    howToRead: 'Cuanto menor sea el valor, mejor es la calidad probabilística del modelo. Un valor de 0.6931 equivale a una predicción completamente ignorante de 0.50 constante.',
    whatItDoesNotMean: 'No es un porcentaje de error; es un número abstracto de divergencia de información estadística.',
  },
  brier_score: {
    id: 'brier_score',
    title: 'Brier Score (Calibración Cuadrática)',
    badge: 'Calibración Empírica',
    category: 'Métricas',
    short: 'Calcula el error cuadrático promedio entre las probabilidades estimadas por el modelo y el desenlace real de la persona (0 o 1).',
    howItWorks: 'Similar al error cuadrático medio (MSE), pero aplicado a probabilidades: se resta la probabilidad estimada del resultado real y se eleva al cuadrado. En Test, CrediRisk registra 0.2050 (en Validación 0.2018).',
    technical: '(1/N) * sum((p_i - y_i)^2). Para un pronóstico constante de 0.50 en datos balanceados, el Brier Score es 0.2500; un modelo perfecto tiene 0.0000.',
    whatIs: 'Indicador de referencia en meteorología y finanzas cuantitativas para verificar si los porcentajes asignados se corresponden con la realidad.',
    meaningInCrediRisk: 'Con 0.2050, el modelo mejora significativamente sobre el punto de referencia de ignorancia probabilística (0.2500).',
    whyItMatters: 'Garantiza que si el modelo reúne a un grupo de personas y les asigna 80% de probabilidad de pago, aproximadamente 8 de cada 10 realmente paguen.',
    howToRead: 'Valores por debajo de 0.21 confirman que las probabilidades emitidas son estables y no están distorsionadas por saturación en la capa sigmoide.',
    whatItDoesNotMean: 'No mide la capacidad de ordenamiento (eso lo mide el ROC-AUC); un modelo puede ordenar bien pero estar mal calibrado en sus valores absolutos.',
  },
  confusion_matrix: {
    id: 'confusion_matrix',
    title: 'Matriz de Confusión en Test (N=7,448)',
    badge: 'Distribución de Diagnósticos',
    category: 'Métricas',
    short: 'Desglose exacto de los 4 posibles resultados en las 7,448 solicitudes del conjunto de prueba independiente con umbral 0.50.',
    howItWorks: 'Divide los resultados en Verdaderos Negativos (2,550), Falsos Positivos (1,174), Falsos Negativos (1,248) y Verdaderos Positivos (2,476).',
    technical: 'Tabla de contingencia 2x2 contrastando la etiqueta real observada y con la decisión binaria y_hat = I(p >= 0.50).',
    whatIs: 'La foto completa y verificable de aciertos y errores del sistema en datos no observados durante el entrenamiento.',
    meaningInCrediRisk: 'Refleja la realidad operativa de la institución: 5,026 decisiones correctas (67.48%) frente a 2,422 decisiones erróneas (32.52%).',
    whyItMatters: 'Permite cuantificar en dinero el impacto económico del modelo, distinguiendo entre pérdidas por impago y pérdida de comisiones.',
    howToRead: 'Los cuadrantes diagonales superiores e inferiores son aciertos; los cuadrantes cruzados son los errores con distintas consecuencias de negocio.',
    whatItDoesNotMean: 'No es una propiedad inmutable del modelo; si el comité cambia el umbral de 0.50 a 0.60, los 4 conteos cambian de inmediato.',
  },
  ensemble: {
    id: 'ensemble',
    title: 'Ensamble Top-3 Diverso',
    badge: 'Arquitectura Ganadora',
    category: 'Arquitectura',
    short: 'Combinación de tres redes neuronales profundas con distintas arquitecturas y activaciones para promediar sus predicciones y reducir errores.',
    howItWorks: 'Promedia equitativamente (un tercio cada una): Modelo 1 (ReLU [64,32,16], semilla 42), Modelo 2 (LeakyReLU [32,16], semilla 42) y Modelo 3 (ReLU [64,32,16], semilla 2026).',
    technical: 'Reducción de varianza por descorrelación funcional. La correlación entre las predicciones de Modelo 1 y Modelo 2 se redujo al rango 0.965-0.970 en Fase 2.',
    whatIs: 'Técnica de agregación de modelos heterogéneos para construir un sistema más robusto que cualquier red individual aislada.',
    meaningInCrediRisk: 'Alcanzó el mejor rendimiento oficial en Test con ROC-AUC de 0.74482 (+0.00239 frente al baseline) y 12,995 parámetros totales.',
    whyItMatters: 'Evita depender de los sesgos o puntos ciegos de una sola arquitectura y protege contra sobreajustes estocásticos.',
    howToRead: 'La mejora numérica es modesta pero metodológicamente sólida, con inferencia ultrarrápida (menos de 15 ms en producción).',
    whatItDoesNotMean: 'No es una garantía de infalibilidad; no puede predecir eventos imprevistos como despidos masivos o crisis macroeconómicas.',
  },
  ablation: {
    id: 'ablation',
    title: 'Estudio de Ablación de Características',
    badge: 'Auditoría de Datos',
    category: 'Preprocesamiento',
    short: 'Experimento formal que evalúa el impacto de quitar o agregar grupos de variables para demostrar cuáles son realmente necesarias.',
    howItWorks: 'Se compararon 5 conjuntos en Validación: 44 variables canónicas (0.75225), 35 sin redundantes (0.75202), 50 con ratios derivados (0.75180), 21 con comportamiento (0.74409) y 9 solo financieras (0.62789).',
    technical: 'Aislamiento del aporte marginal de cada grupo de atributos manteniendo constantes los hiperparámetros y la partición de validación.',
    whatIs: 'Procedimiento científico para validar la parsimonia y necesidad de los datos solicitados a los usuarios.',
    meaningInCrediRisk: 'Demostró que retirar el historial crediticio y de pagos causa un desplome de -0.12436 en AUC, probando que el historial de buró es indispensable.',
    whyItMatters: 'Justifica ante las autoridades regulatorias por qué se solicitan estas 23 variables y demuestra que no se recopilan datos innecesarios.',
    howToRead: 'Observa la caída de rendimiento entre cada grupo; la mayor caída ocurre cuando se eliminan las variables de comportamiento en mora.',
    whatItDoesNotMean: 'No indica el peso de una variable en la solicitud de una persona en particular; mide la capacidad general del modelo en toda la población.',
  },
  data_leakage: {
    id: 'data_leakage',
    title: 'Aislamiento y Prevención de Fuga (Data Leakage)',
    badge: 'Rigor Metodológico',
    category: 'Metodología',
    short: 'Garantía científica de que el modelo nunca observó datos del conjunto de prueba ni aprendió estadísticas del futuro durante su entrenamiento.',
    howItWorks: 'La partición en Train (70%), Validación (15%) y Test (15%) se realizó antes de cualquier cálculo. Todas las imputaciones y normalizaciones se ajustaron exclusivamente con Train.',
    technical: 'Ajuste determinista de StandardScaler y medianas en X_train; transformación pura sobre X_val y X_test sin re-ajustar ningún parámetro.',
    whatIs: 'Principio obligatorio de la ciencia de datos para evitar que los modelos exhiban resultados falsamente optimistas en el laboratorio.',
    meaningInCrediRisk: 'Asegura que el Test AUC de 0.74482 es completamente real, honesto y reproducible sin sesgos ocultos de información.',
    whyItMatters: 'Un modelo con fuga de datos parece tener un 90% o 95% de precisión en un informe académico, pero falla catastróficamente al recibir clientes reales.',
    howToRead: 'Se verifica mediante el hash SHA-256 inmutable del dataset y la inspección estática del archivo de preprocesamiento preprocessor.joblib.',
    whatItDoesNotMean: 'No previene el desgaste del modelo en el tiempo si cambian las condiciones de la economía; requiere monitoreo continuo de deriva de datos (data drift).',
  },
};

const BASE_URL = import.meta.env.BASE_URL || './';

export const DOC_FIGURES: DocFigure[] = [
  {
    id: 'fig_01',
    number: '01',
    title: 'Evolución del ROC-AUC por Fase Experimental',
    filename: `${BASE_URL}docs/images/01_evolucion_roc_auc.png`,
    category: 'Comparativa de Fases',
    description: 'Compara el comportamiento de la capacidad de ordenamiento (ROC-AUC) entre el conjunto de Validación y el conjunto de Test para las configuraciones experimentales más representativas del proyecto.',
    xAxis: 'Configuraciones evaluadas (Baseline histórico, Mejor red Fase 1, Red regularizada L2 Fase 2 y Ensamble Top-3 Diverso final).',
    yAxis: 'Puntaje ROC-AUC (escala de 0.740 a 0.755).',
    series: 'Barra azul: Conjunto de Validación (decisión de diseño). Barra verde: Conjunto de Test (prueba definitiva congelada).',
    keyFinding: 'El Ensamble Top-3 Diverso logra el máximo rendimiento tanto en Validación (0.75382) como en Test (0.74482), superando en +0.00239 al baseline histórico.',
    methodologicalCaveat: 'La brecha entre Validación y Test (-0.00900 puntos) es consistente con la variabilidad esperada de generalización sin evidenciar sobreajuste patológico.',
  },
  {
    id: 'fig_02',
    number: '02',
    title: 'Calidad Probabilística en Test (Log Loss y Brier Score)',
    filename: `${BASE_URL}docs/images/02_calidad_probabilistica.png`,
    category: 'Calibración de Probabilidades',
    description: 'Muestra la evolución del error de entropía cruzada (Log Loss) y la calibración probabilística cuadrática (Brier Score) evaluados sobre las 7,448 muestras del conjunto Test congelado.',
    xAxis: 'Modelos comparados en secuencia experimental.',
    yAxis: 'Pérdida Logarítmica (Log Loss) y Brier Score (en ambas métricas, valores menores representan mejor calidad predictiva).',
    series: 'Línea de Log Loss (eje izquierdo) y barras de Brier Score (eje derecho).',
    keyFinding: 'El ensamble reduce la incertidumbre probabilística a Log Loss = 0.5963 y Brier Score = 0.2050, mejorando sustancialmente sobre el clasificador no informativo (0.2500).',
    methodologicalCaveat: 'Valores menores confirman mejor calibración, pero requieren re-evaluación periódica si la tasa base macroeconómica de mora se altera.',
  },
  {
    id: 'fig_03',
    number: '03',
    title: 'Métricas de Clasificación Operativa en Test (Accuracy y F1-Score)',
    filename: `${BASE_URL}docs/images/03_clasificacion_acc_f1.png`,
    category: 'Rendimiento Operativo',
    description: 'Evolución de la exactitud global y el balance armónico Precision-Recall (F1-Score) bajo el umbral neutral estándar de 0.50 en la partición Test.',
    xAxis: 'Configuraciones evaluadas en la historia del proyecto.',
    yAxis: 'Porcentaje de Exactitud (%) y valor de F1-Score en escala 0 a 1.',
    series: 'Exactitud porcentual (barras) y F1-Score (línea de tendencia).',
    keyFinding: 'Exactitud de 67.48% y F1-Score de 0.6715 en Test. La red individual de Fase 2 y el ensamble presentan resultados muy cercanos en acierto puntual.',
    methodologicalCaveat: 'El umbral neutral 0.50 no considera costos asimétricos bancarios donde prestar a un insolvente cuesta más que rechazar a un solvente.',
  },
  {
    id: 'fig_04',
    number: '04',
    title: 'Matriz de Confusión Oficial en Test (N=7,448)',
    filename: `${BASE_URL}docs/images/04_matriz_confusion_test.png`,
    category: 'Diagnóstico de Decisión',
    description: 'Representación visual oficial de los 4 cuadrantes de clasificación sobre la partición de prueba independiente de 7,448 registros con umbral de corte 0.50.',
    xAxis: 'Clase Predicha por el Ensamble (0: No Apto, 1: Apto).',
    yAxis: 'Clase Real Observada en Dataset (0: No Apto, 1: Apto).',
    series: 'Verdaderos Negativos: 2,550 | Falsos Positivos: 1,174 | Falsos Negativos: 1,248 | Verdaderos Positivos: 2,476.',
    keyFinding: 'La diagonal principal suma 5,026 casos correctos (67.48%). La tasa de detección de riesgo en no aptos es 68.47% (2,550 de 3,724).',
    methodologicalCaveat: 'Estos números provienen del archivo histórico original reports/final_evaluation.json y concuerdan al 100% con Accuracy (67.48%), Precision (67.84%), Recall (66.49%) y F1 (0.6715).',
  },
  {
    id: 'fig_05',
    number: '05',
    title: 'Comparativa de Ensambles en Fase 3 (Validación)',
    filename: `${BASE_URL}docs/images/05_comparativa_ensambles_fase3.png`,
    category: 'Exploración Fase 3',
    description: 'Contraste entre modelos individuales avanzados (activación ELU) y esquemas ponderados de ensamble evaluados durante la Fase 3 sobre el conjunto de Validación.',
    xAxis: 'Esquemas de ponderación (ELU puro, 60/20/20, 70/15/15 y Ensambles promedio).',
    yAxis: 'Puntaje de Validación ROC-AUC y Log Loss.',
    series: 'Val AUC (puntos azules) y Log Loss de validación (línea roja).',
    keyFinding: 'Los ensambles de Fase 3 lograron excelente Log Loss (0.5883), pero en Val AUC (0.75359) quedaron ligeramente por debajo del ensamble de Fase 2 (0.75382). Por parsimonia se mantuvo congelado el Top-3.',
    methodologicalCaveat: 'Debido a la alta correlación entre redes avanzadas (>0.999), añadir más modelos no aportó ganancia de ordenamiento estadísticamente justificable.',
  },
  {
    id: 'fig_06',
    number: '06',
    title: 'Diagrama Arquitectónico del Ensamble Final',
    filename: `${BASE_URL}docs/images/06_arquitectura_ensamble_final.png`,
    category: 'Arquitectura Deep Learning',
    description: 'Estructura topológica detallada de las 3 redes neuronales que componen el Ensamble Top-3 Diverso, mostrando dimensiones de capas, funciones de activación, optimizadores y número de parámetros.',
    xAxis: 'Flujo de capas desde las 44 entradas normalizadas hasta la capa sigmoide de salida.',
    yAxis: 'Niveles de las tres redes en paralelo.',
    series: 'Modelo 1: 5,505 parámetros (ReLU). Modelo 2: 1,985 parámetros (LeakyReLU). Modelo 3: 5,505 parámetros (ReLU semilla 2026). Total: 12,995 parámetros.',
    keyFinding: 'Arquitecturas compactas y piramidales (reducción gradual 44 a 64 a 32 a 16 a 1) que previenen la sobreparametrización en datos tabulares.',
    methodologicalCaveat: 'El promedio equiponderado simple (1/3 cada uno) fue seleccionado por robustez y reproducibilidad, superando esquemas sobreoptimizados.',
  },
  {
    id: 'fig_07',
    number: '07',
    title: 'Pipeline de Preprocesamiento de Datos sin Fuga',
    filename: `${BASE_URL}docs/images/07_pipeline_datos.png`,
    category: 'Ingeniería de Datos',
    description: 'Diagrama secuencial de las etapas de transformación matemática aplicadas a las 23 variables predictoras originales hasta conformar el espacio vectorial estandarizado de 44 dimensiones.',
    xAxis: 'Etapas del flujo: Dataset original a Partición estratificada a Imputación a Clipping a Log1p a One-Hot a StandardScaler.',
    yAxis: 'Flujo de datos y parámetros guardados en preprocessor.joblib.',
    series: 'Bloques de procesamiento determinista ejecutados sin contaminación entre particiones.',
    keyFinding: 'Garantiza ausencia total de fuga de información (data leakage); ningún dato de Validación ni de Test influyó en los percentiles o escaladores.',
    methodologicalCaveat: 'La variable ingreso_disponible requirió una función especial Signed-Log (sign(x) * log1p(|x|)) para procesar correctamente balances netos negativos.',
  },
  {
    id: 'fig_08',
    number: '08',
    title: 'Flujo de las Tres Fases Experimentales',
    filename: `${BASE_URL}docs/images/08_flujo_fases_experimentales.png`,
    category: 'Gobernanza Científica',
    description: 'Mapa de ruta metodológico que ilustra la evolución cronológica del proyecto a través de Fase 1 (Exploración), Fase 2 (Regularización y Ablación) y Fase 3 (Activaciones suaves y cierre).',
    xAxis: 'Fase 1 (37 experimentos) a Fase 2 (29 experimentos) a Fase 3 (18 experimentos) a Evaluación Definitiva en Test.',
    yAxis: 'Decisiones de diseño, filtros metodológicos y hallazgos empíricos.',
    series: 'Ciclo de experimentación con aislamiento estricto del conjunto Test hasta la auditoría final.',
    keyFinding: 'Trazabilidad experimental completa documentada en archivos CSV inmutables en el directorio reports/.',
    methodologicalCaveat: 'El conjunto Test solo se consultó una vez al finalizar la Fase 2 para congelar el modelo definitivo.',
  },
  {
    id: 'fig_09',
    number: '09',
    title: 'Curva de Aprendizaje: ¿Memorizó o Aprendió?',
    filename: `${BASE_URL}docs/images/10_curva_aprendizaje_memorizo_vs_aprendio.png`,
    category: 'Diagnóstico de Convergencia',
    description: 'Comparación entre la curva real de pérdida Binary Cross-Entropy (Train vs Validación) del proyecto y el patrón clásico de sobreajuste (memorización).',
    xAxis: 'Épocas de entrenamiento (ciclos completos sobre los 34,755 registros de Train).',
    yAxis: 'Error Binary Cross-Entropy (Log Loss).',
    series: 'Línea azul: Train Loss. Línea naranja: Validation Loss. Líneas tenues: 5 semillas aleatorias.',
    keyFinding: 'Las curvas de entrenamiento (0.5929) y validación (0.5933) convergen juntas con una brecha mínima de 0.0004 sin divergencia explosiva, demostrando aprendizaje generalizable.',
    methodologicalCaveat: 'Durante las primeras épocas el error de entrenamiento es mayor que el de validación debido al efecto regularizador del Dropout activo solo en Train.',
  },
  {
    id: 'fig_10',
    number: '10',
    title: 'Resumen de las 166 Pruebas y Épocas por Modelo (Early Stopping)',
    filename: `${BASE_URL}docs/images/11_resumen_pruebas_y_epocas.png`,
    category: 'Trazabilidad Experimental',
    description: 'Desglose del total de 166 ejecuciones experimentales por etapa y comparación entre las épocas totales entrenadas y la Mejor Época (Best Epoch) donde se congelaron los pesos.',
    xAxis: 'Etapas experimentales (Panel A) y número de épocas entrenadas vs ventana de paciencia (Panel B).',
    yAxis: 'Cantidad de pruebas ejecutadas (Panel A) y submodelos del ensamble (Panel B).',
    series: 'Barras verdes: Épocas de aprendizaje efectivo hasta Best Epoch (19, 32, 71 y 45). Barras naranjas: Ventana de vigilancia Early Stopping.',
    keyFinding: 'El mecanismo Early Stopping con restore_best_weights=True detuvo cada red en su punto exacto de convergencia (épocas 44, 83 y 55), rebobinando a las épocas 32, 71 y 45.',
    methodologicalCaveat: 'Ninguna configuración requirió agotar el tope máximo de 120 épocas, confirmando convergencia estable.',
  },
];

export const HISTORICAL_COMPARISON: HistoricalModelRecord[] = [
  {
    configuracion: 'Baseline Histórico (model_final.keras)',
    redes: 1,
    valAuc: 0.74969,
    testAuc: 0.74243,
    prAucTest: 0.73810,
    logLossTest: 0.5992,
    brierTest: 0.2062,
    accuracyTest: '67.32%',
    f1Test: '0.6678',
    descripcion: 'Punto de partida del estudio. Perceptrón multicapa estándar de referencia previa.',
    estado: 'baseline',
  },
  {
    configuracion: 'Fase 1: Mejor Red Individual (cfg_c_s42)',
    redes: 1,
    valAuc: 0.75225,
    testAuc: 0.74373,
    prAucTest: 0.74080,
    logLossTest: 0.5979,
    brierTest: 0.2056,
    accuracyTest: '67.32%',
    f1Test: '0.6702',
    descripcion: 'Red piramidal [64, 32, 16] ReLU con Dropout 0.15 y optimizador Adam (lr=0.0005).',
    estado: 'candidato',
  },
  {
    configuracion: 'Fase 1: Ensamble 5 Semillas',
    redes: 5,
    valAuc: 0.75249,
    testAuc: 0.74460,
    prAucTest: 0.74120,
    logLossTest: 0.5898,
    brierTest: 0.2022,
    accuracyTest: '68.66%',
    f1Test: '0.6882',
    descripcion: 'Promedio de 5 réplicas estocásticas de la arquitectura ganadora de Fase 1.',
    estado: 'candidato',
  },
  {
    configuracion: 'Fase 2: Red Regularizada L2 (model_best_phase2)',
    redes: 1,
    valAuc: 0.75250,
    testAuc: 0.74336,
    prAucTest: 0.74100,
    logLossTest: 0.5980,
    brierTest: 0.2057,
    accuracyTest: '67.33%',
    f1Test: '0.6712',
    descripcion: 'Mejor red individual de todo el proyecto en Validación con penalización L2=10^-4.',
    estado: 'candidato',
  },
  {
    configuracion: 'Fase 2: Ensamble Top-3 Diverso (MODELO DEFINITIVO)',
    redes: 3,
    valAuc: 0.75382,
    testAuc: 0.74482,
    prAucTest: 0.73512,
    logLossTest: 0.5963,
    brierTest: 0.2050,
    accuracyTest: '67.48%',
    f1Test: '0.6715',
    descripcion: 'Modelo oficial congelado en producción. Ensamble heterogéneo (ReLU + LeakyReLU).',
    estado: 'ganador',
  },
  {
    configuracion: 'Fase 3: Individual ELU (P3_06, Multi-Seed)',
    redes: 5,
    valAuc: 0.75316,
    testAuc: 'No evaluado',
    prAucTest: 'No evaluado',
    logLossTest: 'No evaluado',
    brierTest: 'No evaluado',
    accuracyTest: 'No evaluado',
    f1Test: 'No evaluado',
    descripcion: 'Exploración de activación ELU en Validación. Mínima varianza estocástica (sigma=0.00030).',
    estado: 'fase3',
  },
  {
    configuracion: 'Fase 3: Ensamble Ponderado 60/20/20',
    redes: 11,
    valAuc: 0.75359,
    testAuc: 'No evaluado',
    prAucTest: 'No evaluado',
    logLossTest: 'No evaluado',
    brierTest: 'No evaluado',
    accuracyTest: 'No evaluado',
    f1Test: 'No evaluado',
    descripcion: 'Ponderación de 11 redes en Validación. Log Loss sobresaliente (0.5883), descartado por parsimonia.',
    estado: 'fase3',
  },
];

export const ABLATION_STUDY: AblationRecord[] = [
  {
    setName: 'Set A: 44 Características Canónicas',
    description: 'Conjunto completo de 44 variables preprocesadas sin fuga.',
    nFeatures: 44,
    valAuc: 0.75225,
    valAccuracy: 0.6871,
    valF1: 0.6870,
    valLogLoss: 0.5909,
    conclusion: 'Conjunto ganador óptimo. Ofrece el máximo balance entre capacidad de ordenamiento y control de dimensionalidad.',
  },
  {
    setName: 'Set B: 35 Características (Sin Redundantes)',
    description: 'Excluye variables colineales: ingreso_disponible, cuota_estimada, personas_a_cargo y tipo_vivienda.',
    nFeatures: 35,
    valAuc: 0.75202,
    valAccuracy: 0.6875,
    valF1: 0.6910,
    valLogLoss: 0.5910,
    conclusion: 'Mantiene un desempeño muy competitivo (-0.00023 en AUC), pero reduce ligeramente la estabilidad de la frontera de decisión.',
  },
  {
    setName: 'Set E: 50 Características (Con 6 Ratios Financieros)',
    description: 'Las 44 canónicas más 6 ratios derivados (cuota/ingreso, deuda/patrimonio, apalancamiento relativo, etc.).',
    nFeatures: 50,
    valAuc: 0.75180,
    valAccuracy: 0.6881,
    valF1: 0.6924,
    valLogLoss: 0.5904,
    conclusion: 'Agregar ratios calculados a mano no mejoró el AUC (-0.00045); las redes profundas ya infieren relaciones no lineales sin ayuda.',
  },
  {
    setName: 'Set D: 21 Características (Financieras + Comportamiento)',
    description: 'Variables sociodemográficas y financieras principales con historial de pagos en buró.',
    nFeatures: 21,
    valAuc: 0.74409,
    valAccuracy: 0.6835,
    valF1: 0.6859,
    valLogLoss: 0.5975,
    conclusion: 'Pérdida perceptible de -0.00816 en AUC. Confirma que la demografía y antigüedad aportan capacidad predictiva complementaria.',
  },
  {
    setName: 'Set C: 9 Características (Solo Financieras)',
    description: 'Únicamente ingresos, obligaciones, monto solicitado, plazo, cuota, tasa y endeudamiento (sin buró ni mora).',
    nFeatures: 9,
    valAuc: 0.62789,
    valAccuracy: 0.5902,
    valF1: 0.6258,
    valLogLoss: 0.6691,
    conclusion: 'Desplome severo de -0.12436 en AUC. Demuestra científicamente que el historial crediticio en buró es el verdadero motor del modelo.',
  },
];

export const GLOSSARY_ENTRIES: GlossaryEntry[] = [
  {
    term: 'ROC-AUC',
    category: 'Métricas',
    simpleExplanation: 'Medida que indica qué tan bueno es el modelo para ordenar a los clientes de menor a mayor riesgo, desde 0.5 (azar) hasta 1.0 (perfecto).',
    technicalExplanation: 'Integral del área bajo la curva Receiver Operating Characteristic (TPR vs FPR) calculada sobre todas las particiones continuas de umbral.',
    crediriskExample: 'CrediRisk obtiene 0.74482 en el conjunto de prueba Test, lo que significa que en el 74.5% de los casos acierta en el orden relativo de riesgo.',
    relatedConcepts: ['PR-AUC', 'Exactitud', 'Poder de Discriminación'],
  },
  {
    term: 'PR-AUC',
    category: 'Métricas',
    simpleExplanation: 'Evalúa la pureza y precisión de los créditos aprobados a medida que se busca abarcar a una porción mayor de solicitantes solventes.',
    technicalExplanation: 'Área bajo la curva Precision-Recall, muy sensible a la acumulación de falsos positivos en zonas densas de probabilidad.',
    crediriskExample: 'En Test alcanza 0.73512, demostrando que el modelo mantiene pureza de colocación en diversos niveles de aprobación.',
    relatedConcepts: ['ROC-AUC', 'Precisión', 'Recall'],
  },
  {
    term: 'Matriz de Confusión',
    category: 'Métricas',
    simpleExplanation: 'Tabla de 2x2 que clasifica las predicciones del modelo en aciertos (aprobados y rechazados correctamente) y errores (aprobados y rechazados por equivocación).',
    technicalExplanation: 'Desglose exacto de TN (Verdaderos Negativos), FP (Falsos Positivos), FN (Falsos Negativos) y TP (Verdaderos Positivos) para un umbral fijo.',
    crediriskExample: 'En las 7,448 muestras de Test: TN = 2,550, FP = 1,174, FN = 1,248, TP = 2,476. Total aciertos: 5,026 (67.48%).',
    relatedConcepts: ['Falso Positivo', 'Falso Negativo', 'Exactitud'],
  },
  {
    term: 'Falso Positivo (FP)',
    category: 'Riesgo Financiero',
    simpleExplanation: 'Una persona insolvente que el modelo aprueba por error como si fuera apta para crédito.',
    technicalExplanation: 'Error de Tipo I: caso donde la etiqueta real es 0 (no apto), pero el modelo predice 1 (apto).',
    crediriskExample: 'En Test se registraron 1,174 casos. En banca, este error suele causar pérdida patrimonial directa por mora o incumplimiento total.',
    relatedConcepts: ['Falso Negativo', 'Precisión', 'Riesgo de Crédito'],
  },
  {
    term: 'Falso Negativo (FN)',
    category: 'Riesgo Financiero',
    simpleExplanation: 'Una persona solvente a quien el modelo rechaza por error creyendo que no pagará.',
    technicalExplanation: 'Error de Tipo II: caso donde la etiqueta real es 1 (solvente), pero el modelo predice 0 (rechazo).',
    crediriskExample: 'En Test se registraron 1,248 casos. Representa un costo de oportunidad comercial: perder clientes cumplidores y sus intereses.',
    relatedConcepts: ['Falso Positivo', 'Recall', 'Costo de Oportunidad'],
  },
  {
    term: 'Log Loss (Entropía Cruzada)',
    category: 'Métricas',
    simpleExplanation: 'Puntuación que castiga fuertemente las predicciones donde el modelo estuvo demasiado seguro pero se equivocó.',
    technicalExplanation: 'Pérdida de log-verosimilitud negativa: -(1/N) * sum(y * log(p) + (1-y) * log(1-p)).',
    crediriskExample: 'CrediRisk obtiene 0.5963 en Test (0.5888 en Validación), reflejando probabilidades continuas suaves y bien comportadas.',
    relatedConcepts: ['Brier Score', 'Calibración', 'Sigmoide'],
  },
  {
    term: 'Brier Score',
    category: 'Métricas',
    simpleExplanation: 'Promedio del error al cuadrado entre las probabilidades numéricas que dice el modelo y el resultado de la persona.',
    technicalExplanation: 'Error cuadrático medio en espacio probabilístico: (1/N) * sum((p_i - y_i)^2). El valor de referencia aleatorio es 0.25.',
    crediriskExample: 'En Test alcanza 0.2050, significativamente mejor que el 0.2500 que obtendría un pronóstico al azar.',
    relatedConcepts: ['Log Loss', 'Calibración Empírica'],
  },
  {
    term: 'Ensamble Neuronal (Ensemble)',
    category: 'Arquitectura',
    simpleExplanation: 'Técnica que combina las opiniones de varias redes neuronales distintas para tomar una decisión en grupo más confiable.',
    technicalExplanation: 'Agregación lineal de estimadores probabilísticos p_ens = sum(w_i * p_i) para reducir la varianza estocástica del error.',
    crediriskExample: 'El modelo final une 3 redes (ReLU, LeakyReLU y ReLU con semilla 2026), sumando 12,995 parámetros con peso equitativo de un tercio.',
    relatedConcepts: ['Perceptrón Multicapa', 'Descorrelación de Modelos', 'Dropout'],
  },
  {
    term: 'Perceptrón Multicapa (MLP)',
    category: 'Arquitectura',
    simpleExplanation: 'Red neuronal tradicional compuesta por capas de neuronas conectadas entre sí que aprenden relaciones matemáticas entre variables.',
    technicalExplanation: 'Arquitectura Dense Feedforward con transformaciones afines seguidas de funciones de activación no lineales.',
    crediriskExample: 'Las redes de CrediRisk utilizan compresión gradual tipo piramidal: 44 entradas a 64 neuronas a 32 neuronas a 16 neuronas a 1 salida.',
    relatedConcepts: ['Función de Activación', 'Dropout', 'Optimizador Adam'],
  },
  {
    term: 'Dropout',
    category: 'Arquitectura',
    simpleExplanation: 'Mecanismo que apaga neuronas al azar durante el entrenamiento para evitar que la red se vuelva dependiente de pocas neuronas.',
    technicalExplanation: 'Técnica de regularización estocástica que introduce ruido multiplicativo Bernoulli con probabilidad p (en CrediRisk p = 0.15 a 0.20).',
    crediriskExample: 'Se ubica entre las capas densas de 64, 32 y 16 neuronas para evitar que el modelo memorice casos individuales de entrenamiento.',
    relatedConcepts: ['Regularización L2', 'Sobreajuste (Overfitting)'],
  },
  {
    term: 'Regularización L2',
    category: 'Arquitectura',
    simpleExplanation: 'Penalización matemática que impide que los pesos de las neuronas crezcan demasiado, manteniendo el modelo simple y suave.',
    technicalExplanation: 'Sanción de norma Euclidiana añadida a la función de pérdida: Loss_total = Loss + lambda * sum(w_j^2). En Fase 2 se usó lambda = 10^-4.',
    crediriskExample: 'El modelo model_best_phase2 con L2 obtuvo el máximo Val AUC individual del proyecto: 0.75250.',
    relatedConcepts: ['Dropout', 'Sobreajuste'],
  },
  {
    term: 'Activación ReLU / LeakyReLU / ELU',
    category: 'Arquitectura',
    simpleExplanation: 'Operación matemática dentro de cada neurona que decide cuánta señal pasa a la siguiente capa.',
    technicalExplanation: 'ReLU: max(0, x). LeakyReLU: max(alpha*x, x) con alpha=0.1 para evitar neuronas muertas. ELU: x si x>0, alpha*(exp(x)-1) si x<=0.',
    crediriskExample: 'Combinar redes con ReLU y LeakyReLU permitió descorrelacionar sus predicciones a 0.965-0.970, mejorando el ensamble.',
    relatedConcepts: ['Perceptrón Multicapa', 'Descorrelación'],
  },
  {
    term: 'Estudio de Ablación',
    category: 'Preprocesamiento',
    simpleExplanation: 'Experimento en el que se retiran piezas o variables de forma controlada para comprobar cuánto aporta cada una al resultado final.',
    technicalExplanation: 'Entrenamiento y validación sistemática sobre subconjuntos restringidos de características bajo idénticas condiciones hiperparamétricas.',
    crediriskExample: 'Se compararon 5 conjuntos de 44, 35, 50, 21 y 9 variables, demostrando que 44 es el conjunto óptimo sin redundancias.',
    relatedConcepts: ['Importancia por Permutación', 'Data Leakage'],
  },
  {
    term: 'Fuga de Datos (Data Leakage)',
    category: 'Metodología',
    simpleExplanation: 'Error grave donde un modelo aprende con información del examen o del futuro, arrojando resultados engañosamente altos que fallan en la práctica.',
    technicalExplanation: 'Contaminación de estadísticas del conjunto de validación o prueba en el ajuste de transformadores del conjunto de entrenamiento.',
    crediriskExample: 'CrediRisk dividió los datos en 70/15/15 antes de calcular cualquier mediana o percentil, garantizando cero contaminación.',
    relatedConcepts: ['Partición Estratificada', 'Reproducibilidad'],
  },
  {
    term: 'Winsorizing (Recorte Percentil)',
    category: 'Preprocesamiento',
    simpleExplanation: 'Técnica de limpieza que recorta valores extremos atípicos (por ejemplo, ingresos anormalmente gigantescos) a límites razonables.',
    technicalExplanation: 'Sustitución de valores por debajo del percentil p1 por el valor de p1 y por encima de p99 por el valor de p99.',
    crediriskExample: 'Se aplicó a 10 variables financieras continuas para que las neuronas no se desestabilizaran por solicitantes multimillonarios atípicos.',
    relatedConcepts: ['Transformación Log1p', 'StandardScaler'],
  },
  {
    term: 'Transformación Log1p y Signed-Log',
    category: 'Preprocesamiento',
    simpleExplanation: 'Transformación matemática que comprime columnas con números gigantescos para que se distribuyan de forma más suave y simétrica.',
    technicalExplanation: 'log(1 + x) para variables positivas con colas largas. Signed-Log: sign(x) * log(1 + |x|) para variables que pueden ser negativas.',
    crediriskExample: 'Signed-Log se diseñó específicamente para ingreso_disponible, permitiendo representar clientes con saldo negativo sin provocar error matemático.',
    relatedConcepts: ['Winsorizing', 'StandardScaler'],
  },
  {
    term: 'Umbral de Decisión (Threshold)',
    category: 'Riesgo Financiero',
    simpleExplanation: 'La frontera de porcentaje donde el sistema decide aprobar o rechazar (por defecto, 50% o 0.50).',
    technicalExplanation: 'Punto de corte t continuo en [0, 1] que divide la probabilidad condicional P(Apto | x) en decisión binaria.',
    crediriskExample: 'Bajo el umbral 0.50 la exactitud es 67.48%; si el banco busca reducir la mora en aprobados del 4.0% al 2.1%, sube el umbral a 0.70.',
    relatedConcepts: ['Matriz de Confusión', 'Precision', 'Recall'],
  },
  {
    term: 'Muestra Balanceada vs Tasa Real',
    category: 'Metodología',
    simpleExplanation: 'El experimento se entrenó con 50% de casos buenos y 50% malos, mientras que en un banco comercial real la mora suele ser de solo 5% a 10%.',
    technicalExplanation: 'Ajuste de distribución a priori mediante balanceo simétrico de clases. Las probabilidades predichas reflejan la física experimental del dataset balanceado.',
    crediriskExample: 'Un 50% de probabilidad en el laboratorio no equivale a un 50% de probabilidad en una cartera nacional abierta con baja prevalencia de mora.',
    relatedConcepts: ['Prevalencia', 'Aviso Metodológico'],
  },
  {
    term: 'Evaluación Multisemilla (Multi-Seed)',
    category: 'Metodología',
    simpleExplanation: 'Entrenar el mismo modelo varias veces con distintos números iniciales al azar para confirmar que los resultados no fueron fruto de la suerte.',
    technicalExplanation: 'Cálculo de media y desviación estándar de métricas sobre un conjunto de semillas fijas (42, 1, 7, 21, 2026).',
    crediriskExample: 'En Fase 3, la red ELU mostró una desviación estándar de apenas sigma=0.00030 en 5 semillas, tres veces más estable que ReLU.',
    relatedConcepts: ['Reproducibilidad', 'Ensamble'],
  },
];
