import type { ApplicantFormData } from '../types';

export type CurrencyMode = 'USD' | 'COP';

export interface ExchangeRateInfo {
  rate: number;
  base: string;
  target: string;
  source: string;
  date: string;
  is_fallback: boolean;
  cached?: boolean;
  isCustom?: boolean;
  lastUpdated?: string;
}

export const FALLBACK_EXCHANGE_RATE: ExchangeRateInfo = {
  rate: 4180.0,
  base: 'USD',
  target: 'COP',
  source: 'Tasa Referencial Oficial Documentada (Superfinanciera / Banco de la Republica)',
  date: '2026-10-11',
  is_fallback: true,
  cached: false,
  isCustom: false,
};

/**
 * Los unicos 6 campos que representan montos monetarios en el modelo y en el formulario.
 * Todos los demas campos (edad, plazos, tasas de interes %, puntajes, moras, anos) son NO monetarios.
 */
export const MONETARY_FIELDS: readonly (keyof ApplicantFormData)[] = [
  'ingreso_mensual',
  'obligaciones_mensuales',
  'ingreso_disponible',
  'monto_solicitado',
  'cuota_estimada',
  'saldo_total_creditos',
] as const;

const STORAGE_KEY_RATE = 'credirisk_exchange_rate_info';
const STORAGE_KEY_CUSTOM_RATE = 'credirisk_custom_exchange_rate';

/**
 * Convierte un monto en USD a su equivalente en COP.
 */
export function usdToCop(usd: number, rate: number): number {
  if (!usd || isNaN(usd) || usd < 0) return 0;
  return Math.round(usd * rate);
}

/**
 * Convierte un monto en COP a su equivalente en USD (unidad nativa del modelo).
 */
export function copToUsd(cop: number, rate: number): number {
  if (!cop || isNaN(cop) || cop < 0 || rate <= 0) return 0;
  return parseFloat((cop / rate).toFixed(2));
}

/**
 * Formatea un numero como pesos colombianos (COP).
 * Ejemplo: 1500000 -> "$ 1.500.000 COP"
 */
export function formatCOP(amount: number, options?: { showCode?: boolean }): string {
  const showCode = options?.showCode ?? true;
  const num = isNaN(amount) ? 0 : amount;
  const formatted = new Intl.NumberFormat('es-CO', {
    maximumFractionDigits: 0,
    minimumFractionDigits: 0,
  }).format(num);
  return showCode ? `$ ${formatted} COP` : `$ ${formatted}`;
}

/**
 * Formatea un numero como dolares estadounidenses (USD).
 * Ejemplo: 150000 -> "$ 150.000 USD" o con decimales si aplica
 */
export function formatUSD(
  amount: number,
  options?: { showCode?: boolean; decimals?: number }
): string {
  const showCode = options?.showCode ?? true;
  const decimals = options?.decimals ?? (Number.isInteger(amount) ? 0 : 2);
  const num = isNaN(amount) ? 0 : amount;
  const formatted = new Intl.NumberFormat('es-CO', {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  }).format(num);
  return showCode ? `$ ${formatted} USD` : `$ ${formatted}`;
}

/**
 * Formatea de acuerdo con la moneda seleccionada.
 */
export function formatCurrency(
  amount: number,
  currency: CurrencyMode,
  options?: { showCode?: boolean; decimals?: number }
): string {
  return currency === 'COP' ? formatCOP(amount, options) : formatUSD(amount, options);
}

/**
 * Parsea un texto ingresado por el usuario a un numero limpio.
 */
export function parseCurrencyInput(value: string | number): number {
  if (typeof value === 'number') return isNaN(value) ? 0 : Math.max(0, value);
  if (!value || typeof value !== 'string') return 0;

  // Remover simbolos de moneda, espacios y letras
  const cleaned = value.replace(/[^\d.,]/g, '').trim();
  if (!cleaned) return 0;

  // Manejar separadores comunes en formato es-CO (1.000.000,50 o 1000000.50)
  let normalized = cleaned;
  if (cleaned.includes('.') && cleaned.includes(',')) {
    // Miles con punto, decimal con coma
    normalized = cleaned.replace(/\./g, '').replace(',', '.');
  } else if (cleaned.includes(',') && !cleaned.includes('.')) {
    normalized = cleaned.replace(',', '.');
  }

  const parsed = parseFloat(normalized);
  return isNaN(parsed) ? 0 : Math.max(0, parsed);
}

/**
 * Transforma un objeto ApplicantFormData convirtiendo estrictamente sus 6 variables monetarias.
 * Garantiza que ningun campo no monetario se modifique.
 */
export function convertFormData(
  data: ApplicantFormData,
  fromCurrency: CurrencyMode,
  toCurrency: CurrencyMode,
  rate: number
): ApplicantFormData {
  if (fromCurrency === toCurrency || rate <= 0) {
    return { ...data };
  }

  const result = { ...data };
  for (const field of MONETARY_FIELDS) {
    const val = (data as any)[field];
    if (typeof val === 'number' && !isNaN(val)) {
      if (fromCurrency === 'USD' && toCurrency === 'COP') {
        (result as any)[field] = Math.round(val * rate);
      } else if (fromCurrency === 'COP' && toCurrency === 'USD') {
        (result as any)[field] = parseFloat((val / rate).toFixed(2));
      }
    }
  }

  return result;
}

/**
 * Normaliza el payload que se enviara a la API de prediccion del modelo de Deep Learning.
 * Si el usuario esta operando en COP, convierte las 6 variables monetarias a USD (escala base entrenada).
 * Si el usuario esta en USD, lo envia tal cual.
 */
export function normalizePayloadForModel(
  data: ApplicantFormData,
  currentCurrency: CurrencyMode,
  rate: number
): ApplicantFormData {
  if (currentCurrency === 'USD') {
    return { ...data };
  }
  return convertFormData(data, 'COP', 'USD', rate);
}

/**
 * Consulta la Tasa Representativa del Mercado (TRM).
 * Prioriza tasas manuales guardadas en localStorage si existen, o consulta el endpoint backend /api/exchange-rate.
 */
export async function fetchExchangeRate(): Promise<ExchangeRateInfo> {
  // 1. Verificar si hay tasa manual personalizada guardada
  try {
    const customStored = localStorage.getItem(STORAGE_KEY_CUSTOM_RATE);
    if (customStored) {
      const parsedCustom = JSON.parse(customStored);
      if (parsedCustom && typeof parsedCustom.rate === 'number' && parsedCustom.rate > 0) {
        return {
          ...parsedCustom,
          isCustom: true,
        };
      }
    }
  } catch {
    // Continuar si falla acceso a localStorage
  }

  // 2. Consultar endpoint backend /api/exchange-rate
  try {
    const res = await fetch('/api/exchange-rate');
    if (res.ok) {
      const data = await res.json();
      if (data && typeof data.rate === 'number' && data.rate > 0) {
        const rateInfo: ExchangeRateInfo = {
          rate: data.rate,
          base: data.base || 'USD',
          target: data.target || 'COP',
          source: data.source || 'Superintendencia Financiera de Colombia',
          date: data.date || new Date().toISOString().slice(0, 10),
          is_fallback: Boolean(data.is_fallback),
          cached: Boolean(data.cached),
          isCustom: false,
          lastUpdated: new Date().toLocaleTimeString('es-CO', {
            hour: '2-digit',
            minute: '2-digit',
          }),
        };
        try {
          localStorage.setItem(STORAGE_KEY_RATE, JSON.stringify(rateInfo));
        } catch {
          // Ignore storage quota
        }
        return rateInfo;
      }
    }
  } catch {
    // Continuar a fallback local si falla la red
  }

  // 3. Verificar cache previo en localStorage
  try {
    const cachedStored = localStorage.getItem(STORAGE_KEY_RATE);
    if (cachedStored) {
      const cached = JSON.parse(cachedStored);
      if (cached && typeof cached.rate === 'number' && cached.rate > 0) {
        return {
          ...cached,
          is_fallback: true,
          cached: true,
          isCustom: false,
        };
      }
    }
  } catch {
    // Fallback absoluto
  }

  return { ...FALLBACK_EXCHANGE_RATE };
}

/**
 * Guarda una tasa personalizada de simulacion.
 */
export function saveCustomRate(rate: number): ExchangeRateInfo {
  const customInfo: ExchangeRateInfo = {
    rate: Math.max(1, rate),
    base: 'USD',
    target: 'COP',
    source: 'Tasa Manual Personalizada de Simulacion',
    date: new Date().toISOString().slice(0, 10),
    is_fallback: false,
    isCustom: true,
    lastUpdated: new Date().toLocaleTimeString('es-CO', {
      hour: '2-digit',
      minute: '2-digit',
    }),
  };
  try {
    localStorage.setItem(STORAGE_KEY_CUSTOM_RATE, JSON.stringify(customInfo));
  } catch {
    // Ignore error
  }
  return customInfo;
}

/**
 * Elimina la tasa manual personalizada y regresa a la oficial.
 */
export function clearCustomRate(): void {
  try {
    localStorage.removeItem(STORAGE_KEY_CUSTOM_RATE);
  } catch {
    // Ignore error
  }
}
