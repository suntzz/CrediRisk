import React, { useState } from 'react';
import { CheckCircle2, FileSpreadsheet } from 'lucide-react';

export const ExperimentalTimelineView: React.FC = () => {
  const [selectedPhase, setSelectedPhase] = useState<1 | 2 | 3>(2);

  const phases = [
    {
      num: 1,
      title: 'Fase 1: Línea Base y Exploración Inicial',
      badge: '37 Experimentos Controlados',
      objective: 'Reproducir la metodología de referencia, fijar una línea base verificable y explorar sistemáticamente arquitecturas de 1 a 5 capas densas.',
      development: 'Se exploraron tasas de aprendizaje (0.0001 a 0.003), dropout (0.10 a 0.30) e introducción de Batch Normalization sobre partición de Validación.',
      findings: [
        'Batch Normalization degradó el poder de discriminación en datos tabulares con minilotes de 128 (Val AUC cayó a 0.7493 frente a 0.7523).',
        'Se identificó una topología óptima en 3 capas con compresión piramidal gradual: 44 a 64 a 32 a 16 a 1 (5,505 parámetros, ReLU, Adam lr=0.0005, Dropout 0.15).',
        'La mejor red individual (cfg_c_s42) alcanzó Val AUC = 0.75225 y Test AUC = 0.74373.',
      ],
      evidence: 'reports/experiments.csv · reports/comparativa_modelos.csv',
      color: 'from-blue-500/20 to-transparent',
    },
    {
      num: 2,
      title: 'Fase 2: Regularización y Ensambles Diversos',
      badge: '25 Experimentos · Modelo Ganador',
      objective: 'Abordar el sobreajuste residual, verificar la necesidad de variables mediante ablación formal y reducir la correlación entre redes.',
      development: 'Se implementó penalización L2 (10^-4), estudio de ablación con 5 subconjuntos y ensamble heterogéneo con activación LeakyReLU (alpha=0.1).',
      findings: [
        'La red regularizada con L2 alcanzó el máximo Val AUC individual del proyecto: 0.75250 (model_best_phase2.keras).',
        'El estudio de ablación confirmó que las 44 variables canónicas son el conjunto óptimo frente a 35, 50, 21 y 9 características.',
        'La correlación entre la red ReLU y la red LeakyReLU descendió a 0.965-0.970, permitiendo que el Ensamble Top-3 ganara el proyecto con Test AUC = 0.74482.',
      ],
      evidence: 'reports/ablation_study.csv · reports/experiments_phase2.csv · reports/ensemble_validation_phase2.csv',
      color: 'from-emerald-500/20 to-transparent',
    },
    {
      num: 3,
      title: 'Fase 3: Nuevas Activaciones y Multisemilla',
      badge: '12 Experimentos · Cierre Metodológico',
      objective: 'Explorar funciones de activación suaves (ELU, GELU), optimización desacoplada (AdamW) y combinaciones ponderadas multisemilla.',
      development: 'Se entrenaron 12 experimentos y se evaluaron 5 semillas obligatorias (42, 1, 7, 21, 2026) junto con 10 esquemas ponderados de ensamble.',
      findings: [
        'La red ELU (P3_06) demostró la menor varianza estocástica del estudio (desviación estándar sigma = 0.00030, tres veces menor que ReLU).',
        'El ensamble 60/20/20 logró excelente Log Loss (0.5883) y Brier Score (0.2017) en Validación, con Val AUC = 0.75359.',
        'Por criterio de parsimonia operativa (3 redes frente a 11 redes) y congruencia histórica, se decidió congelar el Ensamble Top-3 como modelo final.',
      ],
      evidence: 'reports/experiments_phase3.csv · reports/multiseed_phase3_summary.csv · reports/ensemble_validation_phase3.csv',
      color: 'from-purple-500/20 to-transparent',
    },
  ];

  const current = phases.find((p) => p.num === selectedPhase) || phases[1];

  return (
    <div className="bg-[#0B1220] p-6 sm:p-7 rounded-2xl border border-white/10 shadow-lg space-y-6">
      {/* Encabezado */}
      <div className="border-b border-white/10 pb-4">
        <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-blue-400 block mb-1">
          Evolución Científica
        </span>
        <h2 className="text-base sm:text-lg font-display font-bold text-white tracking-tight">
          Proceso Experimental en Tres Fases Secuenciales
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Principio de aislamiento estricto: todas las decisiones de diseño e hiperparámetros se tomaron exclusivamente sobre el conjunto de Validación, manteniendo el conjunto Test congelado.
        </p>
      </div>

      {/* Selector de Fases */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {phases.map((p) => {
          const isSelected = selectedPhase === p.num;

          return (
            <button
              key={p.num}
              type="button"
              onClick={() => setSelectedPhase(p.num as 1 | 2 | 3)}
              className={`p-4 rounded-xl border text-left transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                isSelected
                  ? 'border-blue-500 bg-blue-600/20 ring-1 ring-blue-500 shadow-md'
                  : 'border-white/5 bg-white/5 hover:bg-white/10'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-white/10 text-slate-300">
                  FASE {p.num}
                </span>
                {p.num === 2 && (
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    Ganador
                  </span>
                )}
              </div>
              <h3 className="text-sm font-sans font-bold text-white">
                {p.title.split(':')[1] || p.title}
              </h3>
              <p className="text-[11px] text-slate-400 font-mono mt-1">
                {p.badge}
              </p>
            </button>
          );
        })}
      </div>

      {/* Detalle de la Fase Seleccionada */}
      <div className="p-5 rounded-xl bg-white/5 border border-white/10 space-y-4 text-xs animate-in fade-in duration-150">
        <div className="border-b border-white/10 pb-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 font-mono font-bold text-xs">
              FASE {current.num}
            </span>
            <strong className="text-sm text-white font-sans">{current.title}</strong>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            {current.badge}
          </span>
        </div>

        {/* Objetivo y Desarrollo */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-slate-300">
          <div className="p-3.5 rounded-lg bg-slate-950/60 border border-white/5 space-y-1">
            <span className="text-blue-400 font-sans font-bold block text-[11px] uppercase tracking-wider">
              Objetivo Científico:
            </span>
            <p className="leading-relaxed">{current.objective}</p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-950/60 border border-white/5 space-y-1">
            <span className="text-blue-400 font-sans font-bold block text-[11px] uppercase tracking-wider">
              Desarrollo Metodológico:
            </span>
            <p className="leading-relaxed">{current.development}</p>
          </div>
        </div>

        {/* Hallazgos Clave */}
        <div className="space-y-2">
          <span className="text-slate-200 font-sans font-bold block text-[11px] uppercase tracking-wider">
            Hallazgos Empíricos Confirmados:
          </span>
          <div className="space-y-1.5 font-mono text-[11px]">
            {current.findings.map((finding, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-slate-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{finding}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Evidencia Documental */}
        <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-slate-400">
          <div className="flex items-center space-x-1.5">
            <FileSpreadsheet className="w-3.5 h-3.5 text-slate-500" />
            <span>Evidencia: {current.evidence}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
