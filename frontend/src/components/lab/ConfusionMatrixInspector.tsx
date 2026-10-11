import React, { useState } from 'react';
import { Sliders } from 'lucide-react';
import { ConceptTrigger } from './ConceptExplainerModal';

interface ConfusionMatrixInspectorProps {
  cm: {
    tn: number;
    fp: number;
    fn: number;
    tp: number;
    total_test: number;
  };
  onOpenExplainer: (key: string) => void;
}

type QuadrantKey = 'tn' | 'fp' | 'fn' | 'tp';

export const ConfusionMatrixInspector: React.FC<ConfusionMatrixInspectorProps> = ({
  cm,
  onOpenExplainer,
}) => {
  const [selectedQuadrant, setSelectedQuadrant] = useState<QuadrantKey>('fp');
  const [simulatedThreshold, setSimulatedThreshold] = useState<'0.5' | '0.6' | '0.7'>('0.5');

  // Datos verificados del reporte histórico reports/final_evaluation.json (líneas 86-102)
  const thresholdScenarios = {
    '0.5': {
      threshold: 0.50,
      tasaAprobacion: 63.67, // % de solicitantes que reciben oferta
      moraAprobados: 4.00,    // % de impago dentro de la cartera aprobada
      malosDetectados: 68.47, // % de solicitantes insolventes detectados
      perfil: 'Neutral Equilibrado (Optimización Estadística)',
      descripcion: 'Punto de corte por defecto del proyecto. Maximiza el balance entre colocación y riesgo sin sesgar la probabilidad.',
    },
    '0.6': {
      threshold: 0.60,
      tasaAprobacion: 48.67,
      moraAprobados: 3.02,
      malosDetectados: 81.79,
      perfil: 'Conservador Moderado (Preferencia por Seguridad)',
      descripcion: 'Exige mayor certeza para aprobar. Reduce la morosidad al 3.02% a costa de rechazar a un 15% más de solicitantes.',
    },
    '0.7': {
      threshold: 0.70,
      tasaAprobacion: 28.79,
      moraAprobados: 2.07,
      malosDetectados: 92.62,
      perfil: 'Estricto Antirriesgo (Mitigación Extrema)',
      descripcion: 'Filtro de máxima exigencia. Detecta al 92.6% de los insolventes, pero reduce fuertemente la colocación comercial.',
    },
  };

  const total = cm.total_test || 7448;
  const tnPct = ((cm.tn / total) * 100).toFixed(2);
  const fpPct = ((cm.fp / total) * 100).toFixed(2);
  const fnPct = ((cm.fn / total) * 100).toFixed(2);
  const tpPct = ((cm.tp / total) * 100).toFixed(2);

  const quadrantDetails = {
    tn: {
      title: 'Verdaderos Negativos (TN)',
      count: cm.tn,
      pct: `${tnPct}% de la muestra Test`,
      badge: 'Decisión Correcta · Protección',
      badgeClass: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      boxClass: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
      financialMeaning: 'Solicitantes de alto riesgo clasificados correctamente como No Aptos.',
      businessImpact: 'Protección patrimonial directa: previene pérdidas de capital al no colocar dinero en perfiles con alta propensión al impago.',
      caution: 'En una muestra experimental balanceada (3,724 insolventes), el modelo detecta al 68.47% de los clientes riesgosos.',
    },
    fp: {
      title: 'Falsos Positivos (FP)',
      count: cm.fp,
      pct: `${fpPct}% de la muestra Test`,
      badge: 'Error de Tipo I · Riesgo de Pérdida',
      badgeClass: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
      boxClass: 'border-rose-500/40 bg-rose-500/10 text-rose-300',
      financialMeaning: 'Solicitantes de alto riesgo aprobados indebidamente como Aptos.',
      businessImpact: 'El error más costoso en banca: genera cartera vencida, costos de cobranza judicial y provisiones contables por deterioro de cartera.',
      caution: 'Representan 1,174 casos. Si el banco no puede absorber esta tasa de mora, la solución operativa consiste en subir el umbral de corte.',
    },
    fn: {
      title: 'Falsos Negativos (FN)',
      count: cm.fn,
      pct: `${fnPct}% de la muestra Test`,
      badge: 'Error de Tipo II · Costo de Oportunidad',
      badgeClass: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      boxClass: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
      financialMeaning: 'Solicitantes solventes rechazados indebidamente como No Aptos.',
      businessImpact: 'Costo de oportunidad comercial: la entidad deja de percibir margen de intermediación por intereses de clientes que habrían pagado cumplidamente.',
      caution: 'Son 1,248 casos viables perdidos. Para captarlos, el comité comercial suele implementar líneas con garantías adicionales o microcréditos escalonados.',
    },
    tp: {
      title: 'Verdaderos Positivos (TP)',
      count: cm.tp,
      pct: `${tpPct}% de la muestra Test`,
      badge: 'Decisión Correcta · Rentabilidad',
      badgeClass: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      boxClass: 'border-blue-500/40 bg-blue-500/10 text-blue-300',
      financialMeaning: 'Solicitantes solventes aprobados correctamente como Aptos.',
      businessImpact: 'Generación saludable de ingresos financieros: colocación exitosa que amortiza cuotas en tiempo y genera rentabilidad sostenible.',
      caution: 'Totalizan 2,476 solicitudes. Representan el 66.49% de todos los clientes solventes presentes en el conjunto de prueba.',
    },
  };

  const currentQuad = quadrantDetails[selectedQuadrant];
  const sim = thresholdScenarios[simulatedThreshold];

  return (
    <div className="bg-[#0B1220] p-6 sm:p-7 rounded-2xl border border-white/10 shadow-lg space-y-6">
      {/* Encabezado */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <h2 className="text-base sm:text-lg font-display font-bold text-white tracking-tight">
              Matriz de Confusión Oficial en Test (N={total.toLocaleString()})
            </h2>
            <ConceptTrigger 
              conceptKey="confusion_matrix" 
              label="¿Cómo leerla?" 
              onOpenExplainer={onOpenExplainer} 
            />
          </div>
          <p className="text-xs text-slate-400">
            Población de prueba no observada durante el entrenamiento bajo el umbral neutral 0.50.
          </p>
        </div>
        <div className="text-[11px] font-mono text-slate-300 bg-white/5 border border-white/10 px-3 py-1.5 rounded-lg shrink-0">
          Balance Test: 3,724 No Aptos / 3,724 Aptos (50/50)
        </div>
      </div>

      {/* Grid Interactivo de la Matriz 2x2 */}
      <div>
        <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-2 text-center">
          Haz clic en cualquier cuadrante para inspeccionar su impacto financiero
        </div>

        <div className="grid grid-cols-2 gap-3 max-w-2xl mx-auto font-mono">
          {/* Cuadrante TN */}
          <button
            type="button"
            onClick={() => setSelectedQuadrant('tn')}
            className={`p-4 rounded-xl border text-center transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
              selectedQuadrant === 'tn'
                ? 'border-emerald-500 bg-emerald-500/25 ring-2 ring-emerald-500/40 shadow-lg scale-[1.02]'
                : 'border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/15'
            }`}
          >
            <div className="text-[11px] uppercase font-bold text-emerald-400 tracking-wider">
              Verdaderos Negativos (TN)
            </div>
            <div className="text-2xl sm:text-3xl font-black text-white my-1">
              {cm.tn.toLocaleString()}
            </div>
            <div className="text-[11px] text-emerald-300">
              {tnPct}% del total · Acierto
            </div>
          </button>

          {/* Cuadrante FP */}
          <button
            type="button"
            onClick={() => setSelectedQuadrant('fp')}
            className={`p-4 rounded-xl border text-center transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-rose-500 ${
              selectedQuadrant === 'fp'
                ? 'border-rose-500 bg-rose-500/25 ring-2 ring-rose-500/40 shadow-lg scale-[1.02]'
                : 'border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/15'
            }`}
          >
            <div className="text-[11px] uppercase font-bold text-rose-400 tracking-wider">
              Falsos Positivos (FP)
            </div>
            <div className="text-2xl sm:text-3xl font-black text-white my-1">
              {cm.fp.toLocaleString()}
            </div>
            <div className="text-[11px] text-rose-300">
              {fpPct}% del total · Impago
            </div>
          </button>

          {/* Cuadrante FN */}
          <button
            type="button"
            onClick={() => setSelectedQuadrant('fn')}
            className={`p-4 rounded-xl border text-center transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-500 ${
              selectedQuadrant === 'fn'
                ? 'border-amber-500 bg-amber-500/25 ring-2 ring-amber-500/40 shadow-lg scale-[1.02]'
                : 'border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/15'
            }`}
          >
            <div className="text-[11px] uppercase font-bold text-amber-400 tracking-wider">
              Falsos Negativos (FN)
            </div>
            <div className="text-2xl sm:text-3xl font-black text-white my-1">
              {cm.fn.toLocaleString()}
            </div>
            <div className="text-[11px] text-amber-300">
              {fnPct}% del total · Oportunidad
            </div>
          </button>

          {/* Cuadrante TP */}
          <button
            type="button"
            onClick={() => setSelectedQuadrant('tp')}
            className={`p-4 rounded-xl border text-center transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              selectedQuadrant === 'tp'
                ? 'border-blue-500 bg-blue-500/25 ring-2 ring-blue-500/40 shadow-lg scale-[1.02]'
                : 'border-blue-500/30 bg-blue-500/10 hover:bg-blue-500/15'
            }`}
          >
            <div className="text-[11px] uppercase font-bold text-blue-400 tracking-wider">
              Verdaderos Positivos (TP)
            </div>
            <div className="text-2xl sm:text-3xl font-black text-white my-1">
              {cm.tp.toLocaleString()}
            </div>
            <div className="text-[11px] text-blue-300">
              {tpPct}% del total · Acierto
            </div>
          </button>
        </div>
      </div>

      {/* Tarjeta de Detalle del Cuadrante Seleccionado */}
      <div className="p-4 sm:p-5 rounded-xl bg-white/5 border border-white/10 space-y-3 text-xs animate-in fade-in duration-150">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-2.5">
          <div className="flex items-center space-x-2">
            <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full border ${currentQuad.badgeClass}`}>
              {currentQuad.badge}
            </span>
            <strong className="text-white text-sm font-sans">{currentQuad.title}</strong>
          </div>
          <span className="font-mono text-slate-300 font-bold">
            {currentQuad.count.toLocaleString()} solicitudes ({currentQuad.pct})
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          <div className="space-y-1">
            <span className="font-bold text-slate-200 block">Significado Financiero:</span>
            <p className="text-slate-400 leading-relaxed">{currentQuad.financialMeaning}</p>
          </div>
          <div className="space-y-1">
            <span className="font-bold text-slate-200 block">Impacto en el Negocio:</span>
            <p className="text-slate-400 leading-relaxed">{currentQuad.businessImpact}</p>
          </div>
        </div>

        <div className="pt-2 border-t border-white/5 text-[11px] text-slate-400 font-mono flex items-center space-x-1.5">
          <span className="text-blue-400 font-bold">Nota técnica:</span>
          <span>{currentQuad.caution}</span>
        </div>
      </div>

      {/* Simulador de Umbrales Operativos de Decisión */}
      <div className="p-4 sm:p-5 rounded-xl bg-slate-950/70 border border-white/10 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-blue-400" />
              <h3 className="font-sans font-bold text-sm text-white">
                Simulador de Umbrales de Decisión Bancaria (Sensibilidad vs Riesgo)
              </h3>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Datos verificados del estudio de prevalencia real (reports/final_evaluation.json) a tasa base 8%.
            </p>
          </div>

          {/* Selector de Umbral */}
          <div className="flex items-center space-x-1 bg-white/5 p-1 rounded-xl border border-white/10 shrink-0">
            {(['0.5', '0.6', '0.7'] as const).map((th) => (
              <button
                key={th}
                type="button"
                onClick={() => setSimulatedThreshold(th)}
                className={`px-3 py-1 text-xs font-mono font-bold rounded-lg transition-colors ${
                  simulatedThreshold === th
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Umbral {th}
              </button>
            ))}
          </div>
        </div>

        {/* Resumen del Escenario de Umbral */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-center">
          <div className="p-3 rounded-lg bg-white/5 border border-white/5">
            <span className="text-[10px] text-slate-400 block uppercase">Tasa de Aprobación</span>
            <div className="text-lg font-black text-white mt-0.5">{sim.tasaAprobacion.toFixed(2)}%</div>
            <span className="text-[10px] text-slate-500">Solicitudes aceptadas</span>
          </div>

          <div className="p-3 rounded-lg bg-white/5 border border-white/5">
            <span className="text-[10px] text-slate-400 block uppercase">Mora en Aprobados</span>
            <div className="text-lg font-black text-rose-400 mt-0.5">{sim.moraAprobados.toFixed(2)}%</div>
            <span className="text-[10px] text-slate-500">Cartera vencida esperada</span>
          </div>

          <div className="p-3 rounded-lg bg-white/5 border border-white/5">
            <span className="text-[10px] text-slate-400 block uppercase">Insolventes Detectados</span>
            <div className="text-lg font-black text-emerald-400 mt-0.5">{sim.malosDetectados.toFixed(2)}%</div>
            <span className="text-[10px] text-slate-500">Riesgo filtrado con éxito</span>
          </div>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed bg-blue-500/10 p-3 rounded-lg border border-blue-500/20">
          <strong className="text-blue-300 font-sans">{sim.perfil}:</strong> {sim.descripcion}
        </p>
      </div>
    </div>
  );
};
