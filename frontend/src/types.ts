export type ViewMode = 'home' | 'evaluator' | 'lab' | 'about';
export type ThemeMode = 'light' | 'dark' | 'system';
export type LabTab = 'summary' | 'metrics' | 'experiments' | 'architecture' | 'methodology' | 'glossary';

export interface ApplicantFormData {
  id_solicitud?: number;
  edad: number;
  estado_civil: string;
  personas_a_cargo: number;
  tipo_vivienda: string;

  ingreso_mensual: number;
  obligaciones_mensuales?: number;
  ingreso_disponible: number;
  monto_solicitado: number;
  plazo_meses: number;
  cuota_estimada: number;
  tasa_interes_ea: number;
  nivel_endeudamiento_pct: number;

  score_crediticio: number;
  numero_creditos_activos?: number;
  saldo_total_creditos?: number;
  numero_cuotas_mora?: number;
  dias_maximo_mora: number;
  porcentaje_pagos_oportunos?: number;

  antiguedad_laboral_anios?: number;
  patrimonio_indice: number;
  antiguedad_cliente_anios?: number;
  linea_negocio: string;
  tipo_contrato: string;

  model_type?: 'ensemble' | 'single';
}

export interface ApplicantFormState {
  id_solicitud?: number | '';
  edad: number | '';
  estado_civil: string;
  personas_a_cargo: number | '';
  tipo_vivienda: string;

  ingreso_mensual: number | '';
  obligaciones_mensuales?: number | '';
  ingreso_disponible: number | '';
  monto_solicitado: number | '';
  plazo_meses: number | '';
  cuota_estimada: number | '';
  tasa_interes_ea: number | '';
  nivel_endeudamiento_pct: number | '';

  score_crediticio: number | '';
  numero_creditos_activos?: number | '';
  saldo_total_creditos?: number | '';
  numero_cuotas_mora?: number | '';
  dias_maximo_mora: number | '';
  porcentaje_pagos_oportunos?: number | '';

  antiguedad_laboral_anios?: number | '';
  patrimonio_indice: number | '';
  antiguedad_cliente_anios?: number | '';
  linea_negocio: string;
  tipo_contrato: string;

  model_type?: 'ensemble' | 'single';
}

export const EMPTY_FORM_STATE: ApplicantFormState = {
  id_solicitud: '',
  edad: '',
  estado_civil: '',
  personas_a_cargo: '',
  tipo_vivienda: '',

  ingreso_mensual: '',
  obligaciones_mensuales: '',
  ingreso_disponible: '',
  monto_solicitado: '',
  plazo_meses: '',
  cuota_estimada: '',
  tasa_interes_ea: '',
  nivel_endeudamiento_pct: '',

  score_crediticio: '',
  numero_creditos_activos: '',
  saldo_total_creditos: '',
  numero_cuotas_mora: '',
  dias_maximo_mora: '',
  porcentaje_pagos_oportunos: '',

  antiguedad_laboral_anios: '',
  patrimonio_indice: '',
  antiguedad_cliente_anios: '',
  linea_negocio: '',
  tipo_contrato: '',

  model_type: 'ensemble',
};

export interface RiskFactor {
  variable: string;
  impacto: 'positivo' | 'neutro' | 'negativo';
  valor: string;
  detalle: string;
}

export interface PredictionResult {
  id_solicitud: number;
  resultado: 'APTO' | 'NO APTO';
  probabilidad_apto: number;
  probabilidad_no_apto: number;
  threshold: number;
  decision_rule: string;
  modelo_utilizado: {
    nombre: string;
    tipo: string;
    pesos: string;
  };
  factores_relevantes: RiskFactor[];
  disclaimer_academico: string;
}

export interface ExperimentPhase3 {
  id: string;
  familia: string;
  descripcion: string;
  arquitectura: string;
  parametros: number;
  activacion: string;
  lr: number;
  dropout: number;
  l2: number;
  optimizador: string;
  val_auc: number;
  val_loss: number;
  accuracy: number;
  f1: number;
  pr_auc: number;
  brier: number;
}

export interface MultiseedModel {
  modelo: string;
  mean_auc: number;
  std_auc: number;
  min_auc: number;
  max_auc: number;
  mean_loss: number;
  mean_f1: number;
  mean_acc: number;
}

export interface EnsembleValidationModel {
  nombre: string;
  peso_a: number;
  peso_b: number;
  peso_c: number;
  candidatos: string;
  val_auc: number;
  val_loss: number;
  accuracy: number;
  f1: number;
}

export interface SystemMetrics {
  evaluation: {
    modelo_final: string;
    test_auc: number;
    val_auc: number;
    test_pr_auc: number;
    test_log_loss: number;
    test_brier: number;
    test_accuracy: number;
    test_precision: number;
    test_recall: number;
    test_f1: number;
    threshold: number;
    n_train: number;
    n_val: number;
    n_test: number;
  };
  feature_importance_top10: Array<{
    variable: string;
    caida_auc: number;
    peso_relativo_pct: number;
  }>;
  confusion_matrix: {
    tn: number;
    fp: number;
    fn: number;
    tp: number;
    total_test: number;
  };
  experiments_phase3?: ExperimentPhase3[];
  multiseed_summary?: MultiseedModel[];
  ensemble_validation?: EnsembleValidationModel[];
  dataset_summary?: {
    archivo: string;
    sha256: string;
    bytes: number;
    permisos: string;
    total_registros: number;
    columnas_crudas: number;
    features_procesadas: number;
    train_n: number;
    val_n: number;
    test_n: number;
    balance_clases: string;
  };
}

export interface HealthStatus {
  status: string;
  service: string;
  dataset_verified_sha256: string;
  threshold: number;
  ensemble_available: boolean;
  single_model_available: boolean;
  models_in_ensemble: number;
}
