/**
 * Utilidades centralizadas para formateo y parseo numerico en pesos colombianos (COP).
 * Garantiza separacion estricta entre el valor numerico puro para calculos y su representacion visual.
 */

export const MONETARY_FIELDS = [
  'ingreso_mensual',
  'obligaciones_mensuales',
  'ingreso_disponible',
  'monto_solicitado',
  'cuota_estimada',
  'saldo_total_creditos',
] as const;

export type MonetaryField = typeof MONETARY_FIELDS[number];

/**
 * Parsea una cadena formateada con separadores de miles y la convierte a un numero puro.
 * Retorna null cuando el valor esta vacio o es invalido para no confundir campos vacios con el numero 0.
 * Ejemplo:
 *   "1.750.000" -> 1750000
 *   "0"         -> 0
 *   ""          -> null
 */
export function parseFormattedNumber(value: string | number | undefined | null): number | null {
  if (value === undefined || value === null || value === '') {
    return null;
  }
  if (typeof value === 'number') {
    return isNaN(value) ? null : value;
  }

  // Remover puntos de miles, espacios, simbolos de moneda
  const cleaned = value.replace(/[^\d]/g, '').trim();
  if (!cleaned) {
    return null;
  }

  const parsed = parseInt(cleaned, 10);
  return isNaN(parsed) ? null : parsed;
}

/**
 * Formatea un numero o texto numerico insertando puntos como separadores de miles
 * segun la convencion habitual en Colombia.
 * Ejemplos:
 *   1750000   -> "1.750.000"
 *   25000000  -> "25.000.000"
 *   150000    -> "150.000"
 *   500000000 -> "500.000.000"
 *   0         -> "0"
 *   ""        -> ""
 */
export function formatNumberCOP(value: number | string | undefined | null): string {
  if (value === undefined || value === null || value === '') {
    return '';
  }

  const num = typeof value === 'number' ? value : parseFormattedNumber(value);
  if (num === null || isNaN(num)) {
    return '';
  }

  // Redondear a entero para valores monetarios estándar en COP
  const rounded = Math.round(num);
  return rounded.toLocaleString('es-CO');
}

/**
 * Formatea un valor monetario para presentacion en tarjetas, certificados y resumenes.
 * Retorna '-' cuando el valor no ha sido registrado o esta vacio.
 * Ejemplo:
 *   1750000 -> "$ 1.750.000"
 *   0       -> "$ 0"
 *   ""      -> "-"
 */
export function formatCurrencyDisplay(
  value: number | string | undefined | null,
  options?: { showCode?: boolean }
): string {
  if (value === undefined || value === null || value === '') {
    return '-';
  }
  const formatted = formatNumberCOP(value);
  if (!formatted) {
    return '-';
  }
  return options?.showCode ? `$ ${formatted} COP` : `$ ${formatted}`;
}
