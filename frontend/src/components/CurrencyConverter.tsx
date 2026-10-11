import React, { useState } from 'react';
import {
  ArrowRightLeft,
  Settings2,
  RotateCcw,
  RefreshCw,
  Calendar,
  Sparkles,
} from 'lucide-react';
import type { CurrencyMode, ExchangeRateInfo } from '../services/currency';
import {
  formatCOP,
  formatCurrency,
  parseCurrencyInput,
  usdToCop,
  copToUsd,
  saveCustomRate,
  clearCustomRate,
  fetchExchangeRate,
} from '../services/currency';

interface CurrencyConverterProps {
  rateInfo: ExchangeRateInfo;
  onRateChange?: (newRate: ExchangeRateInfo) => void;
  onApplyToForm?: (amount: number, currency: CurrencyMode) => void;
  compact?: boolean;
  className?: string;
}

export const CurrencyConverter: React.FC<CurrencyConverterProps> = ({
  rateInfo,
  onRateChange,
  onApplyToForm,
  compact: _compact = false,
  className = '',
}) => {
  const [fromCurrency, setFromCurrency] = useState<CurrencyMode>('USD');
  const [rawAmount, setRawAmount] = useState<string>('1000');
  const [isEditingRate, setIsEditingRate] = useState<boolean>(false);
  const [customRateInput, setCustomRateInput] = useState<string>(() => rateInfo.rate.toString());
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const numericAmount = parseCurrencyInput(rawAmount);

  // Calculo bidireccional
  const convertedAmount =
    fromCurrency === 'USD'
      ? usdToCop(numericAmount, rateInfo.rate)
      : copToUsd(numericAmount, rateInfo.rate);

  const toCurrency: CurrencyMode = fromCurrency === 'USD' ? 'COP' : 'USD';

  // Intercambiar monedas de origen y destino
  const handleSwapCurrencies = () => {
    setFromCurrency(toCurrency);
    // Convertir el valor ingresado al equivalente actual para que la transicion sea natural
    setRawAmount(convertedAmount > 0 ? convertedAmount.toString() : '');
  };

  // Preset quick chips
  const usdPresets = [500, 1000, 5000, 10000, 50000];
  const copPresets = [2000000, 5000000, 20000000, 50000000, 100000000];
  const currentPresets = fromCurrency === 'USD' ? usdPresets : copPresets;

  // Actualizar tasa manual
  const handleApplyCustomRate = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseFloat(customRateInput);
    if (!isNaN(parsed) && parsed > 0) {
      const updated = saveCustomRate(parsed);
      if (onRateChange) onRateChange(updated);
      setIsEditingRate(false);
    }
  };

  // Restablecer tasa oficial
  const handleResetToOfficial = async () => {
    clearCustomRate();
    setIsRefreshing(true);
    try {
      const fresh = await fetchExchangeRate();
      if (onRateChange) onRateChange(fresh);
      setCustomRateInput(fresh.rate.toString());
    } finally {
      setIsRefreshing(false);
      setIsEditingRate(false);
    }
  };

  // Refrescar tasa desde API
  const handleRefreshRate = async () => {
    setIsRefreshing(true);
    try {
      const fresh = await fetchExchangeRate();
      if (onRateChange) onRateChange(fresh);
      setCustomRateInput(fresh.rate.toString());
    } finally {
      setIsRefreshing(false);
    }
  };

  // Tasa reciproca
  const reciprocalRate = rateInfo.rate > 0 ? (1 / rateInfo.rate).toFixed(6) : '0';

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-white/10 bg-slate-900/80 backdrop-blur-xl shadow-2xl transition-all duration-200 ${className}`}
    >
      {/* Glow ambiental superior */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-500 opacity-80" />

      {/* Cabecera del Convertidor */}
      <div className="px-5 py-4 border-b border-white/5 flex flex-wrap items-center justify-between gap-3 bg-white/[0.02]">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <ArrowRightLeft className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white tracking-wide flex items-center gap-1.5">
              Convertidor Oficial USD / COP
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                TRM en Vivo
              </span>
            </h4>
            <p className="text-[11px] text-slate-400">
              Conversion bidireccional precisa para evaluacion crediticia en Colombia
            </p>
          </div>
        </div>

        {/* Badge de Tasa y Acciones de Configuracion */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleRefreshRate}
            disabled={isRefreshing}
            title="Actualizar tasa desde fuente oficial"
            className="p-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
          <button
            type="button"
            onClick={() => {
              setCustomRateInput(rateInfo.rate.toString());
              setIsEditingRate(!isEditingRate);
            }}
            className={`px-2.5 py-1 text-xs rounded-lg border font-medium flex items-center space-x-1.5 transition-all ${
              rateInfo.isCustom
                ? 'bg-purple-500/20 border-purple-500/40 text-purple-200 hover:bg-purple-500/30'
                : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10 hover:text-white'
            }`}
          >
            <Settings2 className="w-3.5 h-3.5" />
            <span>{rateInfo.isCustom ? 'Tasa Personalizada' : 'Ajustar Tasa'}</span>
          </button>
        </div>
      </div>

      {/* Panel desplegable para edicion de tasa */}
      {isEditingRate && (
        <div className="px-5 py-3.5 bg-slate-950/70 border-b border-white/10 animate-in fade-in duration-150">
          <form onSubmit={handleApplyCustomRate} className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-xs font-semibold text-white block">
                  Simular Escenario Cambiario Personalizado
                </span>
                <span className="text-[11px] text-slate-400">
                  Ingresa una tasa TRM especifica para evaluar la sensibilidad del credito ante variaciones del dolar.
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">$</span>
                  <input
                    type="number"
                    step="0.01"
                    min="1"
                    value={customRateInput}
                    onChange={(e) => setCustomRateInput(e.target.value)}
                    placeholder="Ej. 4150.00"
                    className="w-32 pl-6 pr-3 py-1.5 text-xs rounded-lg bg-slate-900 border border-slate-700 text-white font-mono focus:border-cyan-500 focus:outline-none"
                  />
                </div>
                <button
                  type="submit"
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white shadow transition-colors"
                >
                  Aplicar
                </button>
                {rateInfo.isCustom && (
                  <button
                    type="button"
                    onClick={handleResetToOfficial}
                    className="px-2.5 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center space-x-1"
                    title="Restablecer a la tasa oficial"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Oficial</span>
                  </button>
                )}
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Cuerpo del Convertidor */}
      <div className="p-5 space-y-4">
        {/* Fila principal de conversion */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
          {/* Origen (Input) */}
          <div className="md:col-span-5 space-y-1.5">
            <div className="flex justify-between items-center text-xs">
              <label className="font-medium text-slate-300 flex items-center space-x-1.5">
                <span>Monto en {fromCurrency === 'USD' ? 'Dolares (USD)' : 'Pesos (COP)'}</span>
              </label>
              <span className="text-[11px] font-mono text-cyan-400/90 font-medium">
                {fromCurrency}
              </span>
            </div>
            <div className="relative">
              <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm font-semibold pointer-events-none">
                $
              </div>
              <input
                type="text"
                value={rawAmount}
                onChange={(e) => setRawAmount(e.target.value)}
                placeholder="0"
                className="w-full pl-8 pr-16 py-2.5 text-sm sm:text-base font-mono font-medium rounded-xl bg-slate-950/60 border border-slate-700/80 text-white placeholder-slate-500 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none transition-all shadow-inner"
              />
              <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400 pointer-events-none">
                {fromCurrency}
              </span>
            </div>
          </div>

          {/* Boton Swap Central */}
          <div className="md:col-span-2 flex justify-center py-1">
            <button
              type="button"
              onClick={handleSwapCurrencies}
              title="Invertir monedas de conversion"
              className="group p-2.5 rounded-full border border-white/10 bg-white/5 hover:bg-cyan-500/20 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-300 transition-all shadow-lg active:scale-95"
            >
              <ArrowRightLeft className="w-4 h-4 transition-transform group-hover:rotate-180 duration-300" />
            </button>
          </div>

          {/* Destino (Resultado) */}
          <div className="md:col-span-5 space-y-1.5">
            <div className="flex justify-between items-center text-xs">
              <span className="font-medium text-slate-300">
                Equivalente en {toCurrency === 'USD' ? 'Dolares (USD)' : 'Pesos (COP)'}
              </span>
              <span className="text-[11px] font-mono text-emerald-400/90 font-medium">
                {toCurrency}
              </span>
            </div>
            <div className="relative flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 shadow-inner">
              <span className="text-sm sm:text-base font-mono font-bold tracking-wide truncate">
                {formatCurrency(convertedAmount, toCurrency, { showCode: false })}
              </span>
              <span className="text-xs font-bold font-mono text-emerald-400/80 ml-2">
                {toCurrency}
              </span>
            </div>
          </div>
        </div>

        {/* Chips de montos rapidos */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[11px] text-slate-400 mr-1 font-medium">Accesos rapidos:</span>
          {currentPresets.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => setRawAmount(preset.toString())}
              className="px-2 py-0.5 text-[11px] font-mono rounded-md bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white transition-colors"
            >
              {fromCurrency === 'USD' ? `$${preset.toLocaleString('es-CO')}` : `$${(preset / 1000000).toFixed(0)}M`}
            </button>
          ))}
          {onApplyToForm && convertedAmount > 0 && (
            <button
              type="button"
              onClick={() => onApplyToForm(convertedAmount, toCurrency)}
              className="ml-auto px-2.5 py-0.5 text-[11px] font-medium rounded-md bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 transition-colors flex items-center space-x-1"
            >
              <Sparkles className="w-3 h-3" />
              <span>Usar en evaluador</span>
            </button>
          )}
        </div>

        {/* Footer Informativo de la TRM */}
        <div className="pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-y-2 gap-x-4 text-[11px] text-slate-400">
          <div className="flex items-center space-x-2">
            <div
              className={`w-2 h-2 rounded-full ${
                rateInfo.isCustom
                  ? 'bg-purple-400 animate-pulse'
                  : rateInfo.is_fallback
                  ? 'bg-amber-400'
                  : 'bg-emerald-400'
              }`}
            />
            <span className="font-medium text-slate-300">
              1 USD = {formatCOP(rateInfo.rate, { showCode: false })} COP
            </span>
            <span className="text-slate-500">·</span>
            <span className="font-mono text-slate-400">
              1 COP = ${reciprocalRate} USD
            </span>
          </div>

          <div className="flex items-center space-x-2 text-[10px]">
            <span className="text-slate-500">Fuente:</span>
            <span className="text-slate-300 font-medium truncate max-w-xs" title={rateInfo.source}>
              {rateInfo.source}
            </span>
            {rateInfo.date && (
              <>
                <span className="text-slate-500">|</span>
                <span className="text-slate-400 flex items-center gap-1 font-mono">
                  <Calendar className="w-3 h-3" />
                  {rateInfo.date}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
