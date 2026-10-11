import React, { useState } from 'react';
import { ABLATION_STUDY } from './labData';
import { ConceptTrigger } from './ConceptExplainerModal';

interface AblationStudyViewProps {
  onOpenExplainer: (key: string) => void;
}

export const AblationStudyView: React.FC<AblationStudyViewProps> = ({ onOpenExplainer }) => {
  const [selectedSet, setSelectedSet] = useState<string>('Set A: 44 Características Canónicas');

  const current = ABLATION_STUDY.find(s => s.setName === selectedSet) || ABLATION_STUDY[0];
  const maxAuc = 0.75225;

  return (
    <div className="bg-[#0B1220] p-6 sm:p-7 rounded-2xl border border-white/10 shadow-lg space-y-6">
      {/* Encabezado */}
      <div className="border-b border-white/10 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <h2 className="text-base sm:text-lg font-display font-bold text-white tracking-tight">
              Estudio Formal de Ablación de Características (Validación)
            </h2>
            <ConceptTrigger 
              conceptKey="ablation" 
              label="¿Qué es ablación?" 
              onOpenExplainer={onOpenExplainer} 
            />
          </div>
          <p className="text-xs text-slate-400">
            Aislamiento del aporte predictivo de cada grupo de variables sobre la partición de Validación (n=7,447).
          </p>
        </div>
        <div className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg shrink-0">
          Óptimo confirmado: 44 variables (Set A)
        </div>
      </div>

      {/* Selector de Conjuntos */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 font-mono text-xs">
        {ABLATION_STUDY.map((s) => {
          const isSelected = selectedSet === s.setName;
          const isWinner = s.setName.startsWith('Set A');
          const isDrastic = s.setName.startsWith('Set C');

          return (
            <button
              key={s.setName}
              type="button"
              onClick={() => setSelectedSet(s.setName)}
              className={`p-3 rounded-xl border text-left transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                isSelected
                  ? 'border-blue-500 bg-blue-600/20 ring-1 ring-blue-500 text-white'
                  : 'border-white/5 bg-white/5 hover:bg-white/10 text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-[11px] text-slate-400">
                  {s.nFeatures} Vars
                </span>
                {isWinner && (
                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    Óptimo
                  </span>
                )}
                {isDrastic && (
                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">
                    Caída
                  </span>
                )}
              </div>
              <div className="font-sans font-bold text-xs truncate text-white">
                {s.setName.split(':')[0]}
              </div>
              <div className="text-[11px] font-mono text-blue-400 mt-1">
                AUC: {s.valAuc.toFixed(5)}
              </div>
            </button>
          );
        })}
      </div>

      {/* Comparación Visual de Barras */}
      <div className="space-y-3 p-4 rounded-xl bg-slate-950/60 border border-white/5">
        <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block mb-2">
          Comparativa Visual del ROC-AUC en Validación (Escala Normalizada):
        </span>
        <div className="space-y-2.5 text-xs font-mono">
          {ABLATION_STUDY.map((item) => {
            const isCurrent = item.setName === selectedSet;
            const delta = (item.valAuc - maxAuc).toFixed(5);
            const pctWidth = Math.max(10, ((item.valAuc - 0.60) / (maxAuc - 0.60)) * 100);

            return (
              <div 
                key={item.setName}
                className={`p-2.5 rounded-lg border transition-all ${
                  isCurrent ? 'bg-white/10 border-blue-500/50' : 'bg-transparent border-transparent'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-sans font-medium text-slate-200">
                    {item.setName}
                  </span>
                  <div className="flex items-center space-x-3 font-mono">
                    <span className="text-white font-bold">{item.valAuc.toFixed(5)}</span>
                    <span className={`text-[11px] ${Number(delta) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {Number(delta) >= 0 ? 'Referencia' : delta}
                    </span>
                  </div>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-300 ${
                      item.setName.startsWith('Set A')
                        ? 'bg-emerald-500'
                        : item.setName.startsWith('Set C')
                        ? 'bg-rose-500'
                        : 'bg-blue-500'
                    }`}
                    style={{ width: `${pctWidth}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tarjeta de Conclusión del Conjunto Seleccionado */}
      <div className="p-4 sm:p-5 rounded-xl bg-white/5 border border-white/10 space-y-3 text-xs">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-2">
          <strong className="text-white font-sans text-sm">{current.setName}</strong>
          <span className="font-mono text-blue-400 font-bold">
            Val AUC: {current.valAuc.toFixed(5)} · Exactitud: {(current.valAccuracy * 100).toFixed(2)}% · Log Loss: {current.valLogLoss.toFixed(4)}
          </span>
        </div>

        <p className="text-slate-300 leading-relaxed text-xs">
          {current.description}
        </p>

        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-slate-200">
          <strong className="text-blue-300 font-sans block mb-0.5">Conclusión Científica:</strong>
          <p>{current.conclusion}</p>
        </div>
      </div>
    </div>
  );
};
