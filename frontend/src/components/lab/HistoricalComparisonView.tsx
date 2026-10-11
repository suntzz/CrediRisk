import React, { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { HISTORICAL_COMPARISON } from './labData';
import { ConceptTrigger } from './ConceptExplainerModal';

interface HistoricalComparisonViewProps {
  onOpenExplainer: (key: string) => void;
}

export const HistoricalComparisonView: React.FC<HistoricalComparisonViewProps> = ({
  onOpenExplainer,
}) => {
  const [filterPhase, setFilterPhase] = useState<'all' | 'phase1' | 'phase2' | 'phase3'>('all');
  const [selectedModel, setSelectedModel] = useState<string>('Fase 2: Ensamble Top-3 Diverso (MODELO DEFINITIVO)');

  const filteredModels = HISTORICAL_COMPARISON.filter((m) => {
    if (filterPhase === 'phase1') return m.configuracion.includes('Fase 1') || m.configuracion.includes('Baseline');
    if (filterPhase === 'phase2') return m.configuracion.includes('Fase 2');
    if (filterPhase === 'phase3') return m.configuracion.includes('Fase 3');
    return true;
  });

  const selectedRecord = HISTORICAL_COMPARISON.find((m) => m.configuracion === selectedModel) || HISTORICAL_COMPARISON[4];

  return (
    <div className="bg-[#0B1220] p-6 sm:p-7 rounded-2xl border border-white/10 shadow-lg space-y-6">
      {/* Encabezado */}
      <div className="border-b border-white/10 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <h2 className="text-base sm:text-lg font-display font-bold text-white tracking-tight">
              Tabla Comparativa Histórica Consolidada
            </h2>
            <ConceptTrigger 
              conceptKey="roc_auc" 
              label="¿Qué es AUC?" 
              onOpenExplainer={onOpenExplainer} 
            />
          </div>
          <p className="text-xs text-slate-400">
            Registro cronológico contrastando el rendimiento en Validación y Test a lo largo de las 3 fases experimentales.
          </p>
        </div>

        {/* Filtro por Fase */}
        <div className="flex items-center space-x-1 bg-white/5 p-1 rounded-xl border border-white/10 shrink-0">
          {(
            [
              { id: 'all', label: 'Todas' },
              { id: 'phase1', label: 'Fase 1' },
              { id: 'phase2', label: 'Fase 2' },
              { id: 'phase3', label: 'Fase 3' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setFilterPhase(tab.id)}
              className={`px-3 py-1 text-xs font-mono font-bold rounded-lg transition-colors ${
                filterPhase === tab.id
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tabla Comparativa con resaltado */}
      <div className="overflow-x-auto rounded-xl border border-white/10 bg-slate-950/60">
        <table className="w-full text-xs text-left">
          <thead className="bg-white/5 border-b border-white/10 text-slate-400 font-mono text-[11px]">
            <tr>
              <th className="py-3 px-3.5 font-sans">Configuración Experimental</th>
              <th className="py-3 px-2 text-center">Redes</th>
              <th className="py-3 px-3">Val AUC</th>
              <th className="py-3 px-3">Test AUC</th>
              <th className="py-3 px-3">Log Loss (Test)</th>
              <th className="py-3 px-3">Brier (Test)</th>
              <th className="py-3 px-3">Exactitud</th>
              <th className="py-3 px-3">F1-Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-mono text-slate-300">
            {filteredModels.map((item) => {
              const isSelected = selectedModel === item.configuracion;
              const isWinner = item.estado === 'ganador';

              return (
                <tr
                  key={item.configuracion}
                  onClick={() => setSelectedModel(item.configuracion)}
                  className={`transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-blue-600/20 text-white font-semibold'
                      : 'hover:bg-white/5'
                  }`}
                >
                  <td className="py-3 px-3.5 font-sans">
                    <div className="flex items-center space-x-2">
                      {isWinner && (
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shrink-0" />
                      )}
                      <span className={isWinner ? 'font-bold text-white' : 'text-slate-200'}>
                        {item.configuracion}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-center text-slate-400">{item.redes}</td>
                  <td className="py-3 px-3 font-bold text-blue-400">{item.valAuc.toFixed(5)}</td>
                  <td className="py-3 px-3 font-bold">
                    {typeof item.testAuc === 'number' ? (
                      <span className={isWinner ? 'text-emerald-400' : 'text-slate-200'}>
                        {item.testAuc.toFixed(5)}
                      </span>
                    ) : (
                      <span className="text-slate-500 italic text-[11px]">{item.testAuc}</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-slate-400">
                    {typeof item.logLossTest === 'number' ? item.logLossTest.toFixed(4) : item.logLossTest}
                  </td>
                  <td className="py-3 px-3 text-slate-400">
                    {typeof item.brierTest === 'number' ? item.brierTest.toFixed(4) : item.brierTest}
                  </td>
                  <td className="py-3 px-3 text-slate-300">{item.accuracyTest}</td>
                  <td className="py-3 px-3 text-slate-300">{item.f1Test}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Tarjeta de Detalle del Modelo Seleccionado */}
      <div className="p-4 sm:p-5 rounded-xl bg-white/5 border border-white/10 space-y-3 text-xs">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-2">
          <strong className="text-white font-sans text-sm">
            {selectedRecord.configuracion}
          </strong>
          <span className="font-mono text-slate-400 text-[11px]">
            Número de Redes Neuronales Combinadas: {selectedRecord.redes}
          </span>
        </div>
        <p className="text-slate-300 leading-relaxed">
          {selectedRecord.descripcion}
        </p>
      </div>

      {/* Nota Crítica de Rigor y Significancia Estadística */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90 flex items-start space-x-3">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="block text-amber-300 font-sans font-semibold">
            Nota de Rigor Metodológico sobre Significancia Estadística:
          </strong>
          <p className="leading-relaxed">
            Las diferencias numéricas observadas (+0.00239 en Test AUC entre el Baseline de 0.74243 y el Ensamble Final de 0.74482) 
            son de magnitud modesta. En este proyecto no se ejecutaron pruebas formales de hipótesis (como el test pareado de DeLong 
            o remuestreo bootstrap), por lo que <strong>no es metodológicamente válido asegurar que la diferencia sea estadísticamente significativa</strong>.
            La ganancia se fundamenta principalmente en la reducción de varianza y la descorrelación de errores entre arquitecturas.
          </p>
        </div>
      </div>
    </div>
  );
};
