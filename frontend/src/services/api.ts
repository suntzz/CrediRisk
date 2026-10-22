import type { ApplicantFormData, HealthStatus, PredictionResult, RiskFactor, SystemMetrics } from '../types';

const API_BASE = '/api';
const STATIC_BASE = `${import.meta.env.BASE_URL || './'}api-static`;

interface DenseLayerSpec {
  type: 'Dense';
  activation: 'relu' | 'linear' | 'sigmoid';
  W: number[][];
  b: number[];
}

interface LeakyReLULayerSpec {
  type: 'LeakyReLU';
  negative_slope: number;
}

type LayerSpec = DenseLayerSpec | LeakyReLULayerSpec;

interface ModelBundle {
  threshold: number;
  preprocessor: {
    drop_cols: string[];
    target: string;
    cat_cols: string[];
    flag_cols: string[];
    skew_cols: string[];
    signed_log_cols: string[];
    rare_to_otro: Record<string, string[]>;
    num_cols: string[];
    dummy_cols: string[];
    lo: Record<string, number>;
    hi: Record<string, number>;
    median: Record<string, number>;
    scaler_mean: number[];
    scaler_scale: number[];
  };
  ensemble_models: LayerSpec[][];
  single_model: LayerSpec[];
}

let cachedBundle: ModelBundle | null = null;

async function getModelBundle(): Promise<ModelBundle> {
  if (cachedBundle) return cachedBundle;
  const res = await fetch(`${STATIC_BASE}/model_bundle.json`);
  if (!res.ok) {
    throw new Error(`No se pudo cargar el modelo estático (${res.status})`);
  }
  cachedBundle = (await res.json()) as ModelBundle;
  return cachedBundle;
}

function preprocessApplicant(data: ApplicantFormData, pre: ModelBundle['preprocessor']): number[] {
  const rec: Record<string, unknown> = { ...data };

  // 1. Reemplazar categorías raras por "Otro"
  const catValues: Record<string, string> = {};
  for (const col of pre.cat_cols) {
    let val = String(rec[col] ?? '');
    const rares = pre.rare_to_otro[col];
    if (rares && rares.includes(val)) {
      val = 'Otro';
    }
    catValues[col] = val;
  }

  // 2. Banderas _nan
  const nanFlags: Record<string, number> = {};
  for (const col of pre.flag_cols) {
    const raw = rec[col];
    const isMissing = raw === null || raw === undefined || raw === '' || Number.isNaN(Number(raw));
    nanFlags[`${col}_nan`] = isMissing ? 1.0 : 0.0;
  }

  // 3. Columnas numéricas con clip [lo, hi], log1p / signed_log y mediana para NaN
  const skewSet = new Set(pre.skew_cols);
  const signedLogSet = new Set(pre.signed_log_cols);
  const numVector: number[] = [];

  for (const col of pre.num_cols) {
    if (col.endsWith('_nan')) {
      numVector.push(nanFlags[col] ?? 0.0);
      continue;
    }
    const raw = rec[col];
    const isMissing = raw === null || raw === undefined || raw === '' || Number.isNaN(Number(raw));
    let val: number;
    if (isMissing) {
      val = pre.median[col] ?? 0.0;
    } else {
      val = Number(raw);
      const lo = pre.lo[col];
      const hi = pre.hi[col];
      if (lo !== undefined && val < lo) val = lo;
      if (hi !== undefined && val > hi) val = hi;
    }

    if (!isMissing) {
      if (skewSet.has(col)) {
        val = Math.log1p(Math.max(0, val));
      }
      if (signedLogSet.has(col)) {
        val = Math.sign(val) * Math.log1p(Math.abs(val));
      }
    } else {
      // Si era NaN, en pandas clip/log1p mantienen NaN y luego fillna(self.median) asigna self.median directo
      val = pre.median[col] ?? 0.0;
    }

    numVector.push(val);
  }

  // 4. Variables dummy one-hot en el mismo orden de pre.dummy_cols
  const dummyVector: number[] = [];
  for (const dCol of pre.dummy_cols) {
    let matched = 0.0;
    for (const catCol of pre.cat_cols) {
      const prefix = `${catCol}_`;
      if (dCol.startsWith(prefix)) {
        const expectedCat = dCol.slice(prefix.length);
        if (catValues[catCol] === expectedCat) {
          matched = 1.0;
        }
        break;
      }
    }
    dummyVector.push(matched);
  }

  // 5. Escalado estándar (StandardScaler)
  const rawFeatures = [...numVector, ...dummyVector];
  return rawFeatures.map((v, i) => (v - pre.scaler_mean[i]) / pre.scaler_scale[i]);
}

function forwardPass(xInput: number[], layers: LayerSpec[]): number {
  let a = [...xInput];
  for (const layer of layers) {
    if (layer.type === 'Dense') {
      const outDim = layer.b.length;
      const next: number[] = new Array(outDim);
      for (let j = 0; j < outDim; j++) {
        let sum = layer.b[j];
        for (let i = 0; i < a.length; i++) {
          sum += a[i] * layer.W[i][j];
        }
        if (layer.activation === 'relu') {
          next[j] = sum > 0 ? sum : 0;
        } else if (layer.activation === 'sigmoid') {
          next[j] = 1 / (1 + Math.exp(-sum));
        } else {
          next[j] = sum;
        }
      }
      a = next;
    } else if (layer.type === 'LeakyReLU') {
      const slope = layer.negative_slope;
      a = a.map((v) => (v > 0 ? v : slope * v));
    }
  }
  return a[0] ?? 0.5;
}

function analyzeRiskFactors(applicant: ApplicantFormData): RiskFactor[] {
  const factors: RiskFactor[] = [];

  const score = Number(applicant.score_crediticio ?? 0);
  if (score >= 680) {
    factors.push({
      variable: 'Score Crediticio',
      impacto: 'positivo',
      valor: `${score.toFixed(0)} pts`,
      detalle: 'Puntaje en rango alto (> 680 pts). Fuerte factor reductor de riesgo.',
    });
  } else if (score >= 550) {
    factors.push({
      variable: 'Score Crediticio',
      impacto: 'neutro',
      valor: `${score.toFixed(0)} pts`,
      detalle: 'Puntaje en rango moderado (550 - 680 pts). Cumple perfil estándar.',
    });
  } else {
    factors.push({
      variable: 'Score Crediticio',
      impacto: 'negativo',
      valor: `${score.toFixed(0)} pts`,
      detalle: 'Puntaje en rango bajo (< 550 pts). Principal factor de riesgo crediticio.',
    });
  }

  const diasMora = Number(applicant.dias_maximo_mora ?? 0);
  const cuotasMora = Number(applicant.numero_cuotas_mora ?? 0);
  if (diasMora === 0 && cuotasMora === 0) {
    factors.push({
      variable: 'Historial de Cumplimiento',
      impacto: 'positivo',
      valor: '0 días en mora',
      detalle: 'Sin registros de mora recientes ni cuotas vencidas.',
    });
  } else if (diasMora <= 30) {
    factors.push({
      variable: 'Historial de Cumplimiento',
      impacto: 'neutro',
      valor: `${diasMora.toFixed(0)} días de mora`,
      detalle: 'Mora menor histórica de corto plazo.',
    });
  } else {
    factors.push({
      variable: 'Historial de Cumplimiento',
      impacto: 'negativo',
      valor: `${diasMora.toFixed(0)} días de mora (${cuotasMora} cuotas)`,
      detalle: 'Mora severa o recurrente registrada.',
    });
  }

  if (applicant.porcentaje_pagos_oportunos !== null && applicant.porcentaje_pagos_oportunos !== undefined) {
    const pct = Number(applicant.porcentaje_pagos_oportunos);
    if (pct >= 95) {
      factors.push({
        variable: 'Pagos Oportunos',
        impacto: 'positivo',
        valor: `${pct.toFixed(1)}%`,
        detalle: 'Excelente puntualidad histórica de pago (> 95%).',
      });
    } else if (pct < 80) {
      factors.push({
        variable: 'Pagos Oportunos',
        impacto: 'negativo',
        valor: `${pct.toFixed(1)}%`,
        detalle: 'Porcentaje de pagos a tiempo inferior al 80%.',
      });
    }
  }

  const endeudamiento = Number(applicant.nivel_endeudamiento_pct ?? 0);
  if (endeudamiento > 60) {
    factors.push({
      variable: 'Nivel de Endeudamiento',
      impacto: 'negativo',
      valor: `${endeudamiento.toFixed(1)}%`,
      detalle: 'Endeudamiento elevado respecto al ingreso mensual.',
    });
  } else if (endeudamiento <= 35) {
    factors.push({
      variable: 'Nivel de Endeudamiento',
      impacto: 'positivo',
      valor: `${endeudamiento.toFixed(1)}%`,
      detalle: 'Nivel de endeudamiento conservador y saludable (< 35%).',
    });
  }

  const ingresoDisp = Number(applicant.ingreso_disponible ?? 0);
  const cuota = Number(applicant.cuota_estimada ?? 0);
  if (cuota > 0 && ingresoDisp < cuota) {
    const fmt = (n: number) => Math.trunc(n).toLocaleString('es-CO');
    factors.push({
      variable: 'Cobertura de Cuota',
      impacto: 'negativo',
      valor: `$${fmt(ingresoDisp)} disponible vs $${fmt(cuota)} cuota`,
      detalle: 'El ingreso mensual disponible es menor a la cuota estimada calculada.',
    });
  }

  return factors;
}

export async function fetchHealth(): Promise<HealthStatus> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) return await res.json();
  } catch {
    // Fallback a modo estático (GitHub Pages)
  }
  const fallback = await fetch(`${STATIC_BASE}/health.json`);
  if (!fallback.ok) {
    throw new Error(`Error ${fallback.status}: No se pudo verificar la salud del sistema`);
  }
  return fallback.json();
}

export async function fetchSampleApplicant(): Promise<ApplicantFormData> {
  try {
    const res = await fetch(`${API_BASE}/sample`);
    if (res.ok) return await res.json();
  } catch {
    // Fallback a modo estático (GitHub Pages)
  }
  const fallback = await fetch(`${STATIC_BASE}/sample.json`);
  if (!fallback.ok) {
    throw new Error(`Error ${fallback.status}: No se pudo cargar el solicitante de prueba`);
  }
  return fallback.json();
}

export async function fetchMetrics(): Promise<SystemMetrics> {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (res.ok) return await res.json();
  } catch {
    // Fallback a modo estático (GitHub Pages)
  }
  const fallback = await fetch(`${STATIC_BASE}/metrics.json`);
  if (!fallback.ok) {
    throw new Error(`Error ${fallback.status}: No se pudieron cargar las métricas`);
  }
  return fallback.json();
}

export async function predictApplicant(data: ApplicantFormData): Promise<PredictionResult> {
  try {
    const res = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Continuar con inferencia neuronal en navegador (GitHub Pages)
  }

  const bundle = await getModelBundle();
  const x = preprocessApplicant(data, bundle.preprocessor);
  const useEnsemble = (data.model_type ?? 'ensemble') === 'ensemble';

  let rawProb: number;
  if (useEnsemble) {
    const probs = bundle.ensemble_models.map((m) => forwardPass(x, m));
    rawProb = probs.reduce((acc, v) => acc + v, 0) / probs.length;
  } else {
    rawProb = forwardPass(x, bundle.single_model);
  }

  const probApto = Number(rawProb.toFixed(4));
  const probNoApto = Number((1.0 - rawProb).toFixed(4));
  const resultado = rawProb >= bundle.threshold ? 'APTO' : 'NO APTO';

  return {
    id_solicitud: data.id_solicitud ?? 999001,
    resultado,
    probabilidad_apto: probApto,
    probabilidad_no_apto: probNoApto,
    threshold: bundle.threshold,
    decision_rule: `P(APTO) >= ${bundle.threshold} => APTO, de lo contrario NO APTO`,
    modelo_utilizado: {
      nombre: useEnsemble ? 'Ensemble_Top3_Diverso' : 'Single_Best_Model (cfg_c_s42)',
      tipo: useEnsemble
        ? 'Ensamble de 3 redes neuronales con arquitecturas y activaciones heterogéneas'
        : 'Red neuronal profunda [64, 32, 16] ReLU',
      pesos: useEnsemble ? 'Ponderación aritmética equiponderada [1/3, 1/3, 1/3]' : '1.0',
    },
    factores_relevantes: analyzeRiskFactors(data),
    disclaimer_academico:
      'Este sistema es un prototipo experimental con fines académicos y de investigación. ' +
      'El modelo fue entrenado sobre un dataset balanceado (50% aptos / 50% no aptos) de 49,650 registros. ' +
      'Las predicciones reflejan patrones estadísticos multivariados de correlación y no constituyen un dictamen ' +
      'financiero vinculante ni establecen relaciones de causalidad crediticia.',
  };
}
