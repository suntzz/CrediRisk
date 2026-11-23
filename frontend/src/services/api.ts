import type { ApplicantFormData, HealthStatus, PredictionResult, RiskFactor, SystemMetrics } from '../types';
import { predictV2, type ModelBundleV2 } from './modelV2';

const API_BASE = '/api';
const STATIC_BASE = `${import.meta.env.BASE_URL || './'}api-static`;

// La inferencia del modelo v2 vive en ./modelV2.ts (ver scripts/export_static_api_v2.py).

let cachedBundleV2: ModelBundleV2 | null = null;

async function getModelBundleV2(): Promise<ModelBundleV2> {
  if (cachedBundleV2) return cachedBundleV2;
  const res = await fetch(`${STATIC_BASE}/model_bundle_v2.json`);
  if (!res.ok) {
    throw new Error(`No se pudo cargar el modelo v2 (${res.status})`);
  }
  cachedBundleV2 = (await res.json()) as ModelBundleV2;
  return cachedBundleV2;
}

export interface ComparacionV2 {
  resultados: { nombre: string; viejo: number; nuevo: number; formato: 'auc' | 'pct_menor' | 'menor' }[];
  mejora_cv: { diff: number; ci_low: number; ci_high: number };
  cambios: [string, string, string][];
}

export async function fetchComparacionV2(): Promise<ComparacionV2> {
  const res = await fetch(`${STATIC_BASE}/comparacion_v2.json`);
  if (!res.ok) throw new Error(`No se pudo cargar la comparación (${res.status})`);
  return res.json();
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

  // Inferencia en el navegador con el modelo v2 (GitHub Pages).
  const bundle = await getModelBundleV2();
  const product = String(data.linea_negocio ?? '');
  const r = predictV2(data as unknown as Record<string, unknown>, bundle);
  if (r.decision === 'BLOQUEADO' || r.umbral === null) {
    throw new Error(`La línea de crédito "${product}" no está disponible en la política v2 (solo efectivo y rotativo).`);
  }
  const threshold = r.umbral;
  const p = r.probAptoReal;

  return {
    id_solicitud: data.id_solicitud ?? 999001,
    resultado: r.decision,
    probabilidad_apto: Number(p.toFixed(4)),
    probabilidad_no_apto: Number((1 - p).toFixed(4)),
    threshold,
    decision_rule:
      `P(paga) >= ${threshold.toFixed(3)} para ${product}: un mal crédito cuesta ${r.costo} veces lo que deja uno bueno, ` +
      `así que aprobar conviene si P(paga) >= c/(1+c). P(paga) está calibrada y corregida a la mora real del ${(bundle.politica.mora_real * 100).toFixed(2)} %.`,
    modelo_utilizado: {
      nombre: 'CrediRisk v2 · Híbrido HGB + 3 redes, con y sin score',
      tipo: '0,85 × (0,90 árbol + 0,10 redes, con score) + 0,15 × (0,90 árbol + 0,10 redes, sin score), calibrado',
      pesos: '0.90 árboles / 0.10 redes; 85 % con score / 15 % sin score',
    },
    factores_relevantes: analyzeRiskFactors(data),
    disclaimer_academico:
      'Este sistema es un prototipo experimental con fines académicos y de investigación. ' +
      'El modelo v2 se entrenó con 42.202 registros balanceados (50 % aptos / 50 % no aptos); la probabilidad mostrada está corregida a la mora real del 8,07 %. ' +
      'Las predicciones reflejan patrones estadísticos multivariados de correlación y no constituyen un dictamen ' +
      'financiero vinculante ni establecen relaciones de causalidad crediticia.',
  };
}
