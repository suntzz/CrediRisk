import React, { useState } from 'react';
import { 
  BarChart3, 
  Layers, 
  GitCompare, 
  ShieldCheck, 
  BookOpen, 
  Cpu, 
  Database, 
  ArrowUpDown,
  Lock,
  HelpCircle,
  Sparkles,
  ZoomIn
} from 'lucide-react';
import type { SystemMetrics, LabTab } from '../types';
import { ConceptExplainerModal, ConceptTrigger } from './lab/ConceptExplainerModal';
import { FigureModal } from './lab/FigureModal';
import { ConfusionMatrixInspector } from './lab/ConfusionMatrixInspector';
import { AblationStudyView } from './lab/AblationStudyView';
import { HistoricalComparisonView } from './lab/HistoricalComparisonView';
import { FigureGalleryView } from './lab/FigureGalleryView';
import { ExperimentalTimelineView } from './lab/ExperimentalTimelineView';
import { ContextualGlossaryView } from './lab/ContextualGlossaryView';
import { DOC_FIGURES, type DocFigure } from './lab/labData';

interface ModelLabViewProps {
  onBackToHome?: () => void;
  onOpenEvaluator?: () => void;
  onOpenAbout: () => void;
  metrics: SystemMetrics | null;
}

export const ModelLabView: React.FC<ModelLabViewProps> = ({
  onBackToHome: _onBackToHome,
  onOpenEvaluator: _onOpenEvaluator,
  onOpenAbout: _onOpenAbout,
  metrics,
}) => {
  const [activeTab, setActiveTab] = useState<LabTab>('summary');
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null);
  const [selectedFigure, setSelectedFigure] = useState<DocFigure | null>(null);
  const [sortField, setSortField] = useState<string>('val_auc');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const evalData = metrics?.evaluation;
  // Valores oficiales certificados respaldados por reports/final_evaluation.json y README.md
  const cm = (metrics?.confusion_matrix && metrics.confusion_matrix.tn === 2550)
    ? metrics.confusion_matrix
    : { 
        tn: 2550, 
        fp: 1174, 
        fn: 1248, 
        tp: 2476, 
        total_test: 7448 
      };
  const importance = metrics?.feature_importance_top10 || [];
  const rawP3Experiments = metrics?.experiments_phase3 || [];
  const multiseedData = metrics?.multiseed_summary || [];
  const ensembleData = metrics?.ensemble_validation || [];
  const datasetInfo = metrics?.dataset_summary;

  // Ordenamiento para experimentos de Fase 3
  const sortedP3 = [...rawP3Experiments].sort((a, b) => {
    let valA = (a as any)[sortField];
    let valB = (b as any)[sortField];
    if (typeof valA === 'string') {
      return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }
    return sortAsc ? valA - valB : valB - valA;
  });

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const navTabs: Array<{ id: LabTab; label: string; icon: React.ReactNode }> = [
    { id: 'summary', label: '1. Resumen', icon: <BookOpen className="w-3.5 h-3.5" /> },
    { id: 'metrics', label: '2. Métricas', icon: <BarChart3 className="w-3.5 h-3.5" /> },
    { id: 'experiments', label: '3. Experimentos', icon: <GitCompare className="w-3.5 h-3.5" /> },
    { id: 'architecture', label: '4. Arquitectura', icon: <Layers className="w-3.5 h-3.5" /> },
    { id: 'methodology', label: '5. Metodología', icon: <ShieldCheck className="w-3.5 h-3.5" /> },
    { id: 'glossary', label: '6. Glosario', icon: <HelpCircle className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="w-full flex flex-col bg-transparent text-slate-100 transition-colors pb-12">
      {/* Navegación Secundaria Flotante: Liquid Glass Segmented Pill Dock */}
      <div className="sticky top-[4.25rem] sm:top-20 z-30 w-full px-4 sm:px-6 py-2 pointer-events-none select-none">
        <div className="max-w-4xl mx-auto flex items-center justify-center pointer-events-auto">
          <nav className="inline-flex items-center p-1 sm:p-1.5 rounded-full border border-white/10 bg-slate-950/75 backdrop-blur-2xl shadow-[0_20px_50px_rgba(0,0,0,0.65),inset_0_1px_1px_rgba(255,255,255,0.18),inset_0_-1px_1px_rgba(0,0,0,0.4)] no-scrollbar max-w-full overflow-x-auto">
            {navTabs.map(tab => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-1.5 px-3 sm:px-3.5 py-1.5 sm:py-2 rounded-full text-xs font-semibold whitespace-nowrap transition-all duration-200 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow-[0_2px_12px_rgba(37,99,235,0.4)] font-bold scale-[1.02]'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Área de Contenido Principal del Laboratorio */}
      <div className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-8">
        {/* PESTAÑA 1: RESUMEN Y ESTADO */}
        {activeTab === 'summary' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Banner Introductorio */}
            <div className="bg-[#0B1220] p-6 sm:p-8 rounded-2xl border border-white/10 shadow-lg relative overflow-hidden">
              <div className="max-w-3xl space-y-3 relative z-10">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-blue-400 block">
                  Plataforma de Investigación en Deep Learning
                </span>
                <h1 className="text-xl sm:text-3xl font-display font-extrabold text-white tracking-tight">
                  Laboratorio Cuantitativo de Riesgo Crediticio
                </h1>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                  Bienvenido al Laboratorio de <strong>CrediRisk</strong>. Esta sección interactiva documenta de manera 
                  transparente el entrenamiento, la auditoría y los resultados empíricos de nuestro sistema neuronal de riesgo financiero. 
                  Aquí puedes explorar cada métrica, comparar los experimentos históricos, revisar la arquitectura en detalle 
                  y consultar cualquier término técnico con explicaciones pedagógicas de tres niveles.
                </p>
                <div className="pt-2 flex flex-wrap gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => setSelectedConcept('ensemble')}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 border border-blue-500/30 transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>¿Cómo funciona el Ensamble Top-3?</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('metrics')}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white/5 text-slate-300 hover:bg-white/10 border border-white/10 transition-colors"
                  >
                    <BarChart3 className="w-3.5 h-3.5 text-slate-400" />
                    <span>Ver métricas de rendimiento en Test</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Ficha Técnica: Modelo Oficial, Dataset e Integridad */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-[#0B1220] p-5 rounded-2xl border border-white/10 shadow-md space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-white">
                    <Cpu className="w-4 h-4 text-blue-400" />
                    <span>Modelo Oficial Congelado</span>
                  </div>
                  <ConceptTrigger 
                    conceptKey="ensemble" 
                    label="Detalles" 
                    onOpenExplainer={setSelectedConcept} 
                  />
                </div>
                <div className="text-base font-bold font-mono text-white">
                  Ensemble_Top3_Diverso
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Ensamble de 3 redes neuronales profundas heterogéneas equiponderadas (1/3 cada una), sumando 12,995 parámetros totales:
                </p>
                <div className="space-y-1 text-[11px] font-mono text-slate-300 bg-white/5 p-2.5 rounded-xl border border-white/5">
                  <div>• cfg_c_s42 ([64, 32, 16], ReLU)</div>
                  <div>• cfg_b_leaky_s42 ([32, 16], LeakyReLU)</div>
                  <div>• cfg_base_s2026 ([64, 32, 16], ReLU s2026)</div>
                </div>
              </div>

              <div className="bg-[#0B1220] p-5 rounded-2xl border border-white/10 shadow-md space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-white">
                    <Database className="w-4 h-4 text-emerald-400" />
                    <span>Conjunto de Datos Experimental</span>
                  </div>
                  <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30">
                    50% / 50%
                  </span>
                </div>
                <div className="text-base font-bold font-mono text-white">
                  49,650 registros observados
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Partición fija estratificada con semilla 42 previa a cualquier transformación estadística para asegurar cero contaminación:
                </p>
                <div className="space-y-1 text-[11px] font-mono text-slate-300 bg-white/5 p-2.5 rounded-xl border border-white/5">
                  <div>• Train: 70% (34,755 observaciones)</div>
                  <div>• Validation: 15% (7,447 observaciones)</div>
                  <div>• Test: 15% (7,448 observaciones)</div>
                </div>
              </div>

              <div className="bg-[#0B1220] p-5 rounded-2xl border border-white/10 shadow-md space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-white">
                    <Lock className="w-4 h-4 text-amber-400" />
                    <span>Control Criptográfico</span>
                  </div>
                  <ConceptTrigger 
                    conceptKey="data_leakage" 
                    label="Auditoría" 
                    onOpenExplainer={setSelectedConcept} 
                  />
                </div>
                <div className="text-xs font-mono font-bold text-amber-400 truncate">
                  SHA-256: 19c5b59ccce6face...
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Archivo original <code>DatasetCreditoFinancieroFinalV2.csv</code> protegido con permisos 444 (solo lectura), auditado sistemáticamente:
                </p>
                <div className="space-y-1 text-[11px] font-mono text-slate-300 bg-white/5 p-2.5 rounded-xl border border-white/5">
                  <div>• Tamaño: 8,436,730 bytes</div>
                  <div>• Columnas crudas: 23 predictoras</div>
                  <div>• Espacio transformado: 44 features</div>
                </div>
              </div>
            </div>

            {/* Pipeline de Inferencia en Tiempo Real */}
            <div className="bg-[#0B1220] p-6 sm:p-7 rounded-2xl border border-white/10 shadow-lg space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-blue-400 block mb-0.5">
                    Flujo de Decisión
                  </span>
                  <h2 className="text-base font-display font-bold text-white">
                    Pipeline de Inferencia en Tiempo Real
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveTab('architecture')}
                  className="text-xs font-mono text-blue-400 hover:text-blue-300 flex items-center space-x-1"
                >
                  <span>Ver arquitectura</span>
                  <span>→</span>
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-4 rounded-xl bg-slate-950/70 border border-white/5 space-y-1">
                  <span className="font-mono text-blue-400 font-bold text-xs block">1. Entrada Cruda</span>
                  <strong className="text-white block">23 Variables de Solicitud</strong>
                  <p className="text-slate-400 text-[11px] leading-relaxed">
                    Datos sociodemográficos, ingresos, obligaciones, score crediticio y comportamiento histórico en buró.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/70 border border-white/5 space-y-1">
                  <span className="font-mono text-blue-400 font-bold text-xs block">2. Preprocesamiento</span>
                  <strong className="text-white block">44 Entradas Estandarizadas</strong>
                  <p className="text-slate-400 text-[11px] leading-relaxed">
                    Clipping percentil p1-p99, transformaciones Log1p / Signed-Log y StandardScaler ajustado estrictamente en Train.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/70 border border-white/5 space-y-1">
                  <span className="font-mono text-blue-400 font-bold text-xs block">3. Inferencia Neuronal</span>
                  <strong className="text-white block">Ensamble Top-3 Diverso</strong>
                  <p className="text-slate-400 text-[11px] leading-relaxed">
                    Tres redes heterogéneas procesan el vector en paralelo y promedian sus probabilidades de forma equiponderada.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/70 border border-white/5 space-y-1">
                  <span className="font-mono text-blue-400 font-bold text-xs block">4. Regla de Decisión</span>
                  <strong className="text-white block">Dictamen de Crédito</strong>
                  <p className="text-slate-400 text-[11px] leading-relaxed">
                    Si P(Apto) ≥ 0.50 el sistema dictamina APTO, de lo contrario dictamina NO APTO (con probabilidad continua).
                  </p>
                </div>
              </div>
            </div>

            {/* Galería de Gráficas Científicas */}
            <FigureGalleryView onSelectFigure={setSelectedFigure} />
          </div>
        )}

        {/* PESTAÑA 2: RENDIMIENTO Y MÉTRICAS */}
        {activeTab === 'metrics' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Banner de Sección */}
            <div className="bg-[#0B1220] p-6 rounded-2xl border border-white/10 shadow-lg">
              <span className="text-[11px] font-mono uppercase tracking-wider text-blue-400 block mb-1">
                Auditoría en Conjunto Test (N=7,448)
              </span>
              <h1 className="text-xl sm:text-2xl font-display font-extrabold text-white tracking-tight">
                Métricas de Rendimiento y Calidad Predictiva
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Todas las métricas de esta sección fueron evaluadas sobre el conjunto Test congelado. 
                Haz clic en el enlace «¿Qué es?» de cada tarjeta para abrir su explicación interactiva detallada.
              </p>
            </div>

            {/* Grid de 6 Tarjetas KPI Principales */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
              {/* ROC-AUC */}
              <div className="bg-[#0B1220] p-4 rounded-xl border border-white/10 shadow-md flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-slate-400">Test ROC-AUC</span>
                    <ConceptTrigger conceptKey="roc_auc" label="?" onOpenExplainer={setSelectedConcept} />
                  </div>
                  <div className="text-2xl font-black font-mono text-white">
                    {evalData?.test_auc?.toFixed(4) || '0.7448'}
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-white/5 text-[10px] text-emerald-400 font-mono">
                  Val: 0.7538 (-1.19%)
                </div>
              </div>

              {/* Exactitud */}
              <div className="bg-[#0B1220] p-4 rounded-xl border border-white/10 shadow-md flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-slate-400">Test Exactitud</span>
                    <ConceptTrigger conceptKey="accuracy" label="?" onOpenExplainer={setSelectedConcept} />
                  </div>
                  <div className="text-2xl font-black font-mono text-white">
                    {evalData?.test_accuracy?.toFixed(2) || '67.48'}%
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-white/5 text-[10px] text-slate-400 font-mono">
                  5,026 / 7,448 aciertos
                </div>
              </div>

              {/* Precisión */}
              <div className="bg-[#0B1220] p-4 rounded-xl border border-white/10 shadow-md flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-slate-400">Test Precisión</span>
                    <ConceptTrigger conceptKey="precision" label="?" onOpenExplainer={setSelectedConcept} />
                  </div>
                  <div className="text-2xl font-black font-mono text-white">
                    {evalData?.test_precision?.toFixed(2) || '67.84'}%
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-white/5 text-[10px] text-slate-400 font-mono">
                  TP / (TP + FP)
                </div>
              </div>

              {/* Exhaustividad */}
              <div className="bg-[#0B1220] p-4 rounded-xl border border-white/10 shadow-md flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-slate-400">Test Recall</span>
                    <ConceptTrigger conceptKey="recall" label="?" onOpenExplainer={setSelectedConcept} />
                  </div>
                  <div className="text-2xl font-black font-mono text-white">
                    {evalData?.test_recall?.toFixed(2) || '66.49'}%
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-white/5 text-[10px] text-slate-400 font-mono">
                  TP / (TP + FN)
                </div>
              </div>

              {/* F1-Score */}
              <div className="bg-[#0B1220] p-4 rounded-xl border border-white/10 shadow-md flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-slate-400">Test F1-Score</span>
                    <ConceptTrigger conceptKey="f1_score" label="?" onOpenExplainer={setSelectedConcept} />
                  </div>
                  <div className="text-2xl font-black font-mono text-white">
                    {evalData?.test_f1?.toFixed(4) || '0.6715'}
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-white/5 text-[10px] text-slate-400 font-mono">
                  Media armónica
                </div>
              </div>

              {/* Brier / LogLoss */}
              <div className="bg-[#0B1220] p-4 rounded-xl border border-white/10 shadow-md flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-slate-400">Brier / LogLoss</span>
                    <ConceptTrigger conceptKey="brier_score" label="?" onOpenExplainer={setSelectedConcept} />
                  </div>
                  <div className="text-xl font-bold font-mono text-white">
                    0.205 / 0.596
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-white/5 text-[10px] text-slate-400 font-mono">
                  Calibración empírica
                </div>
              </div>
            </div>

            {/* Matriz de Confusión Interactiva y Simulador de Umbrales */}
            <ConfusionMatrixInspector cm={cm} onOpenExplainer={setSelectedConcept} />

            {/* Tabla de Importancia de Variables por Permutación (Top-10) */}
            <div className="bg-[#0B1220] p-6 sm:p-7 rounded-2xl border border-white/10 shadow-lg space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
                <div>
                  <h2 className="text-base font-display font-bold text-white tracking-tight">
                    Importancia Empírica por Permutación (Top-10 Auditado)
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Magnitud de caída del ROC-AUC al permutar aleatoriamente cada variable de forma aislada sobre Validación.
                  </p>
                </div>
                <span className="text-[11px] font-mono text-blue-400 bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded-lg shrink-0">
                  Variable dominante: score_crediticio (68.43%)
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-white/5 border-b border-white/10 text-slate-400 font-mono text-[11px]">
                    <tr>
                      <th className="py-2.5 px-3">#</th>
                      <th className="py-2.5 px-3 font-sans">Variable</th>
                      <th className="py-2.5 px-3 font-mono">Caída AUC</th>
                      <th className="py-2.5 px-3 font-mono">Peso Relativo (%)</th>
                      <th className="py-2.5 px-3">Impacto Visual</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 font-mono text-slate-300">
                    {importance.map((item, idx) => (
                      <tr key={item.variable} className="hover:bg-white/5 transition-colors">
                        <td className="py-2.5 px-3 text-slate-500">{idx + 1}</td>
                        <td className="py-2.5 px-3 font-sans font-medium text-white">{item.variable}</td>
                        <td className="py-2.5 px-3 text-slate-300">{item.caida_auc.toFixed(5)}</td>
                        <td className="py-2.5 px-3 font-bold text-white">{item.peso_relativo_pct.toFixed(2)}%</td>
                        <td className="py-2.5 px-3 w-48">
                          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${idx === 0 ? 'bg-amber-400' : 'bg-blue-500'}`}
                              style={{ width: `${Math.min(100, Math.max(4, item.peso_relativo_pct))}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* PESTAÑA 3: COMPARATIVA Y EXPERIMENTOS */}
        {activeTab === 'experiments' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Línea de Tiempo Experimental de las 3 Fases */}
            <ExperimentalTimelineView />

            {/* Tabla Comparativa Histórica con Advertencia de Significancia */}
            <HistoricalComparisonView onOpenExplainer={setSelectedConcept} />

            {/* Estudio Formal de Ablación */}
            <AblationStudyView onOpenExplainer={setSelectedConcept} />

            {/* Registro de Experimentos de Fase 3 con Ordenamiento */}
            <div className="bg-[#0B1220] rounded-2xl border border-white/10 shadow-lg overflow-hidden">
              <div className="p-5 border-b border-white/10 bg-slate-950/70 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="font-display font-bold text-base text-white">
                    Registro de Experimentos de Fase 3 (Validación Sistemática)
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Total de 12 configuraciones controladas (reports/experiments_phase3.csv). Haz clic en los encabezados para ordenar.
                  </p>
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  Ordenado por: {sortField} ({sortAsc ? 'Ascendente' : 'Descendente'})
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-white/5 border-b border-white/10 text-slate-400 font-semibold font-mono text-[11px]">
                    <tr>
                      <th className="py-3 px-3">ID Experimento</th>
                      <th className="py-3 px-3 font-sans">Arquitectura</th>
                      <th className="py-3 px-3">Activación</th>
                      <th className="py-3 px-3">Optimizador</th>
                      <th 
                        onClick={() => handleSort('val_auc')}
                        className="py-3 px-3 cursor-pointer hover:text-blue-400 text-white"
                      >
                        <div className="flex items-center space-x-1">
                          <span>Val AUC</span>
                          <ArrowUpDown className="w-3 h-3 text-blue-400" />
                        </div>
                      </th>
                      <th 
                        onClick={() => handleSort('val_loss')}
                        className="py-3 px-3 cursor-pointer hover:text-blue-400"
                      >
                        <div className="flex items-center space-x-1">
                          <span>Val Loss</span>
                          <ArrowUpDown className="w-3 h-3" />
                        </div>
                      </th>
                      <th 
                        onClick={() => handleSort('accuracy')}
                        className="py-3 px-3 cursor-pointer hover:text-blue-400"
                      >
                        <div className="flex items-center space-x-1">
                          <span>Exactitud</span>
                          <ArrowUpDown className="w-3 h-3" />
                        </div>
                      </th>
                      <th className="py-3 px-3">Parámetros</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 font-mono text-slate-300">
                    {sortedP3.map(exp => (
                      <tr key={exp.id} className="hover:bg-white/5 transition-colors">
                        <td className="py-2.5 px-3 font-bold text-white font-sans">{exp.id}</td>
                        <td className="py-2.5 px-3 text-slate-200">{exp.arquitectura}</td>
                        <td className="py-2.5 px-3 uppercase text-[11px]">{exp.activacion}</td>
                        <td className="py-2.5 px-3">{exp.optimizador}</td>
                        <td className="py-2.5 px-3 font-bold text-blue-400">{exp.val_auc.toFixed(5)}</td>
                        <td className="py-2.5 px-3 text-slate-400">{exp.val_loss.toFixed(4)}</td>
                        <td className="py-2.5 px-3 text-slate-400">{exp.accuracy}%</td>
                        <td className="py-2.5 px-3 text-slate-500">{exp.parametros}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Resumen de Estabilidad Multi-Seed */}
            {multiseedData.length > 0 && (
              <div className="bg-[#0B1220] p-6 rounded-2xl border border-white/10 shadow-lg space-y-4">
                <div className="border-b border-white/10 pb-3">
                  <h3 className="font-display font-bold text-base text-white">
                    Evaluación de Estabilidad Multi-Seed (5 Semillas: 42, 1, 7, 21, 2026)
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Confirmación de robustez estadística para descartar que las diferencias de rendimiento se deban al azar de los pesos iniciales.
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left font-mono">
                    <thead className="border-b border-white/10 text-slate-400 font-semibold text-[11px]">
                      <tr>
                        <th className="py-2.5 px-3 font-sans">Modelo Candidato</th>
                        <th className="py-2.5 px-3">Mean AUC ± Std</th>
                        <th className="py-2.5 px-3">Rango [Min, Max]</th>
                        <th className="py-2.5 px-3">Mean Loss</th>
                        <th className="py-2.5 px-3">Mean Acc</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 text-slate-300">
                      {multiseedData.map(ms => (
                        <tr key={ms.modelo} className="hover:bg-white/5 transition-colors">
                          <td className="py-2.5 px-3 font-sans font-bold text-white">{ms.modelo}</td>
                          <td className="py-2.5 px-3 text-blue-400 font-bold">
                            {ms.mean_auc.toFixed(5)} ± {ms.std_auc.toFixed(5)}
                          </td>
                          <td className="py-2.5 px-3 text-slate-400">
                            [{ms.min_auc.toFixed(5)}, {ms.max_auc.toFixed(5)}]
                          </td>
                          <td className="py-2.5 px-3 text-slate-400">{ms.mean_loss.toFixed(4)}</td>
                          <td className="py-2.5 px-3 text-slate-400">{ms.mean_acc}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Validación de Ensambles Ponderados */}
            {ensembleData.length > 0 && (
              <div className="bg-[#0B1220] p-6 rounded-2xl border border-white/10 shadow-lg space-y-4">
                <div className="border-b border-white/10 pb-3">
                  <h3 className="font-display font-bold text-base text-white">
                    Ponderaciones y Validación de Ensambles en Fase 3
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Comparación de esquemas de agregación probabilística sobre el conjunto de Validación.
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left font-mono">
                    <thead className="border-b border-white/10 text-slate-400 font-semibold text-[11px]">
                      <tr>
                        <th className="py-2.5 px-3 font-sans">Esquema / Modelo</th>
                        <th className="py-2.5 px-3">Candidatos</th>
                        <th className="py-2.5 px-3">Val AUC</th>
                        <th className="py-2.5 px-3">Log Loss</th>
                        <th className="py-2.5 px-3">Exactitud</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 text-slate-300">
                      {ensembleData.slice(0, 6).map((ens, i) => (
                        <tr key={i} className="hover:bg-white/5 transition-colors">
                          <td className="py-2.5 px-3 font-sans font-bold text-white">{ens.nombre}</td>
                          <td className="py-2.5 px-3 text-slate-400">{ens.candidatos}</td>
                          <td className="py-2.5 px-3 text-blue-400 font-bold">{ens.val_auc.toFixed(5)}</td>
                          <td className="py-2.5 px-3 text-slate-400">{ens.val_loss.toFixed(4)}</td>
                          <td className="py-2.5 px-3 text-slate-400">{ens.accuracy}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* PESTAÑA 4: ARQUITECTURA Y PREPROCESAMIENTO */}
        {activeTab === 'architecture' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Banner de Sección */}
            <div className="bg-[#0B1220] p-6 rounded-2xl border border-white/10 shadow-lg">
              <span className="text-[11px] font-mono uppercase tracking-wider text-blue-400 block mb-1">
                Ingeniería de Características y Topología Neuronal
              </span>
              <h1 className="text-xl sm:text-2xl font-display font-extrabold text-white tracking-tight">
                Arquitectura y Pipeline de Datos sin Fuga
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Detalle paso a paso del pipeline determinista de preprocesamiento y de las tres redes neuronales que integran el Ensamble Top-3 Diverso.
              </p>
            </div>

            {/* Pipeline de Preprocesamiento Paso a Paso */}
            <div className="bg-[#0B1220] p-6 sm:p-7 rounded-2xl border border-white/10 shadow-lg space-y-4">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <h2 className="text-base font-display font-bold text-white">
                  Pipeline Determinista sin Fuga de Datos (Data Leakage)
                </h2>
                <ConceptTrigger conceptKey="data_leakage" label="Auditoría" onOpenExplainer={setSelectedConcept} />
              </div>

              <div className="space-y-3.5 text-xs">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-white/5 flex items-start space-x-3.5">
                  <div className="w-7 h-7 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center justify-center font-bold text-xs shrink-0 font-mono">
                    1
                  </div>
                  <div className="space-y-1">
                    <strong className="text-white font-sans text-sm block">Separación Temporal Previa y Limpieza</strong>
                    <p className="text-slate-300 text-xs leading-relaxed">
                      La división estratificada (70% Train, 15% Validation, 15% Test con semilla 42) se realizó antes de cualquier cálculo estadístico. 
                      Se excluyen <code>id_solicitud</code> y la columna de auditoría <code>INCUMPLIO_PAGO</code>. Las variables con más del 1% de datos ausentes 
                      generan indicadores booleanos automáticos (<code>_nan</code>).
                    </p>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-white/5 flex items-start space-x-3.5">
                  <div className="w-7 h-7 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center justify-center font-bold text-xs shrink-0 font-mono">
                    2
                  </div>
                  <div className="space-y-1">
                    <strong className="text-white font-sans text-sm block">Recorte Winsorizing y Transformaciones Asimétricas</strong>
                    <p className="text-slate-300 text-xs leading-relaxed">
                      Recorte de valores atípicos entre percentiles p1 y p99 (calculados exclusivamente con Train). 
                      Transformación logarítmica <code>log1p</code> para 10 variables financieras con colas pesadas. 
                      La variable <code>ingreso_disponible</code> recibe una transformación especial <code>Signed-Log</code> (<code>sign(x) * log1p(|x|)</code>) 
                      para admitir valores netos negativos sin provocar errores matemáticos.
                    </p>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-white/5 flex items-start space-x-3.5">
                  <div className="w-7 h-7 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center justify-center font-bold text-xs shrink-0 font-mono">
                    3
                  </div>
                  <div className="space-y-1">
                    <strong className="text-white font-sans text-sm block">Codificación Categórica y Estandarización Final</strong>
                    <p className="text-slate-300 text-xs leading-relaxed">
                      Codificación One-Hot para variables categóricas (estado civil, tipo de contrato, línea de negocio, vivienda) agrupando baja frecuencia en "Otro". 
                      Se aplica <code>StandardScaler</code> ajustado exclusivamente en Train para conformar el vector de entrada definitivo de 44 dimensiones.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Desglose de las 3 Redes del Ensamble */}
            <div className="bg-[#0B1220] p-6 sm:p-7 rounded-2xl border border-white/10 shadow-lg space-y-4">
              <div className="border-b border-white/10 pb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-base font-display font-bold text-white">
                    Topología del Ensamble Top-3 Diverso (12,995 Parámetros)
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Cada red aporta un tercio (33.33%) del dictamen de probabilidad final mediante combinación lineal.
                  </p>
                </div>
                <ConceptTrigger conceptKey="ensemble" label="¿Por qué 3?" onOpenExplainer={setSelectedConcept} />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                {/* Modelo 1 */}
                <div className="p-5 rounded-xl border border-white/10 bg-slate-950/70 space-y-3">
                  <div className="flex items-center justify-between border-b border-white/5 pb-2">
                    <strong className="text-white font-sans text-sm">Modelo 1: cfg_c_s42</strong>
                    <span className="text-[10px] text-blue-400 font-bold">Semilla 42</span>
                  </div>
                  <div className="space-y-1 text-slate-300 text-[11px]">
                    <div>Topología: [64, 32, 16]</div>
                    <div>Activación: ReLU</div>
                    <div>Dropout: 0.15</div>
                    <div>Optimizador: Adam (lr = 0.0005)</div>
                    <div className="text-emerald-400 font-bold pt-1">5,505 parámetros</div>
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans leading-relaxed pt-2 border-t border-white/5">
                    Mejor arquitectura individual de Fase 1. Compresión piramidal de 3 capas.
                  </p>
                </div>

                {/* Modelo 2 */}
                <div className="p-5 rounded-xl border border-white/10 bg-slate-950/70 space-y-3">
                  <div className="flex items-center justify-between border-b border-white/5 pb-2">
                    <strong className="text-white font-sans text-sm">Modelo 2: cfg_b_leaky</strong>
                    <span className="text-[10px] text-blue-400 font-bold">Semilla 42</span>
                  </div>
                  <div className="space-y-1 text-slate-300 text-[11px]">
                    <div>Topología: [32, 16]</div>
                    <div>Activación: LeakyReLU (α = 0.1)</div>
                    <div>Dropout: 0.15</div>
                    <div>Optimizador: Adam (lr = 0.0005)</div>
                    <div className="text-emerald-400 font-bold pt-1">1,985 parámetros</div>
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans leading-relaxed pt-2 border-t border-white/5">
                    Red compacta que aporta descorrelación de errores (rho = 0.965-0.970) frente a ReLU.
                  </p>
                </div>

                {/* Modelo 3 */}
                <div className="p-5 rounded-xl border border-white/10 bg-slate-950/70 space-y-3">
                  <div className="flex items-center justify-between border-b border-white/5 pb-2">
                    <strong className="text-white font-sans text-sm">Modelo 3: cfg_base_s2026</strong>
                    <span className="text-[10px] text-blue-400 font-bold">Semilla 2026</span>
                  </div>
                  <div className="space-y-1 text-slate-300 text-[11px]">
                    <div>Topología: [64, 32, 16]</div>
                    <div>Activación: ReLU</div>
                    <div>Dropout: 0.20</div>
                    <div>Optimizador: Adam (lr = 0.0010)</div>
                    <div className="text-emerald-400 font-bold pt-1">5,505 parámetros</div>
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans leading-relaxed pt-2 border-t border-white/5">
                    Inicialización estocástica independiente con dropout ligeramente superior para diversidad.
                  </p>
                </div>
              </div>
            </div>

            {/* Imagen de Diagrama Arquitectónico Oficial */}
            <div className="bg-[#0B1220] p-6 rounded-2xl border border-white/10 shadow-lg space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display font-bold text-base text-white">
                    Diagrama Oficial de la Arquitectura del Ensamble
                  </h3>
                  <p className="text-xs text-slate-400">
                    Figura 06 de la documentación técnica. Haz clic en la imagen para inspeccionar en alta resolución.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedFigure(DOC_FIGURES[5])}
                  className="px-3 py-1.5 rounded-lg bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 text-xs font-mono transition-colors flex items-center space-x-1"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                  <span>Ampliar Figura 06</span>
                </button>
              </div>

              <div 
                onClick={() => setSelectedFigure(DOC_FIGURES[5])}
                className="rounded-xl border border-white/10 bg-black/60 p-4 flex items-center justify-center cursor-pointer hover:border-blue-500/50 transition-all group"
              >
                <img 
                  src="/docs/images/06_arquitectura_ensamble_final.png" 
                  alt="Arquitectura del Ensamble Final"
                  className="max-h-72 w-auto object-contain group-hover:scale-[1.02] transition-transform duration-300"
                />
              </div>
            </div>
          </div>
        )}

        {/* PESTAÑA 5: METODOLOGÍA Y LÍMITES CIENTÍFICOS */}
        {activeTab === 'methodology' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Declaración de Gobernanza Académica */}
            <div className="bg-[#0B1220] p-6 sm:p-8 rounded-2xl border border-white/10 shadow-lg space-y-6 text-xs leading-relaxed text-slate-300">
              <div className="border-b border-white/10 pb-4">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-blue-400 block mb-1">
                  Transparencia Científica
                </span>
                <h1 className="text-xl sm:text-2xl font-display font-bold text-white tracking-tight">
                  Gobernanza Metodológica y Límites del Estudio
                </h1>
                <p className="text-xs text-slate-400 mt-1">
                  En cumplimiento de las normas éticas de la investigación cuantitativa, presentamos las limitaciones 
                  formales del modelo para evitar interpretaciones engañosas o aplicaciones indebidas en entornos financieros no controlados.
                </p>
              </div>

              {/* Los 6 Límites Metodológicos Fundamentales */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-950/70 border border-white/10 space-y-1.5">
                  <span className="font-bold text-white font-sans block text-sm">
                    1. Muestra Balanceada vs Tasa Real de Mora
                  </span>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    El dataset experimental fue balanceado en 50% aptos y 50% no aptos. En carteras financieras abiertas, 
                    la tasa base de impago suele ser de 3% a 15%. Por ello, la probabilidad emitida refleja la física 
                    del experimento balanceado y no la probabilidad a priori de una población asimétrica.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/70 border border-white/10 space-y-1.5">
                  <span className="font-bold text-white font-sans block text-sm">
                    2. Asociación Estadística vs Causalidad Económica
                  </span>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    Las redes neuronales identifican correlaciones estadísticas multivariadas complejas. 
                    No demuestran que una variable en particular (por ejemplo, personas a cargo o edad) sea la causa 
                    del impago, sino que se asocia probabilísticamente con el resultado observado.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/70 border border-white/10 space-y-1.5">
                  <span className="font-bold text-white font-sans block text-sm">
                    3. Magnitud Modesta de la Mejora
                  </span>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    El avance en Test AUC desde el baseline inicial (0.74243) hasta el ensamble final (0.74482) representa 
                    una ganancia numérica de +0.00239 puntos. No debe presentarse como un salto revolucionario, sino como una optimización rigurosa de varianza.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/70 border border-white/10 space-y-1.5">
                  <span className="font-bold text-white font-sans block text-sm">
                    4. Ausencia de Prueba Formal de Hipótesis
                  </span>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    No se ejecutaron contrastes pareados de hipótesis (como el test de DeLong o remuestreo bootstrap). 
                    Por lo tanto, no es metodológicamente válido asegurar que la diferencia sea estadísticamente significativa frente al baseline.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/70 border border-white/10 space-y-1.5">
                  <span className="font-bold text-white font-sans block text-sm">
                    5. Partición Fija sin Validación Cruzada Anidada
                  </span>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    Los resultados reflejan el desempeño sobre una división estratificada fija (70/15/15, semilla 42). 
                    No se ejecutó validación cruzada anidada (nested CV) debido a los tiempos de cómputo sobre arquitecturas profundas.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/70 border border-white/10 space-y-1.5">
                  <span className="font-bold text-white font-sans block text-sm">
                    6. Umbral Operativo Neutral (0.50)
                  </span>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    El corte estándar 0.50 asume costos simétricos. En banca comercial real, perder el capital de un crédito 
                    cuesta mucho más que perder a un buen cliente, requiriendo umbrales asimétricos ajustados según política de riesgo.
                  </p>
                </div>
              </div>

              {/* Registro Criptográfico de Trazabilidad */}
              <div className="p-5 rounded-xl bg-slate-950/90 border border-white/10 font-mono text-[11px] space-y-2 text-slate-300">
                <div className="text-xs font-sans font-bold text-white border-b border-white/10 pb-2">
                  Registro de Trazabilidad Criptográfica del Dataset
                </div>
                <div>Archivo Fuente: <code>{datasetInfo?.archivo || 'DatasetCreditoFinancieroFinalV2.csv'}</code></div>
                <div>Hash SHA-256: <code className="text-amber-400 font-bold">{datasetInfo?.sha256 || '19c5b59ccce6face1a0b828d201605aeb0e70b214f7ed60be2efdf13f47f851d'}</code></div>
                <div>Tamaño: {datasetInfo?.bytes?.toLocaleString() || '8,436,730'} bytes · Permisos: {datasetInfo?.permisos || '444 (Solo lectura)'}</div>
                <div>Registros: {datasetInfo?.total_registros?.toLocaleString() || '49,650'} ({datasetInfo?.balance_clases || '50.0% Apto / 50.0% No Apto'})</div>
                <div>Partición: Train ({datasetInfo?.train_n?.toLocaleString() || '34,755'}) · Val ({datasetInfo?.val_n?.toLocaleString() || '7,447'}) · Test ({datasetInfo?.test_n?.toLocaleString() || '7,448'})</div>
              </div>
            </div>
          </div>
        )}

        {/* PESTAÑA 6: GLOSARIO INTERACTIVO */}
        {activeTab === 'glossary' && (
          <div className="animate-in fade-in duration-200">
            <ContextualGlossaryView />
          </div>
        )}
      </div>

      {/* Modal Interactivo de Explicación Conceptual Pedagógica (3 Niveles) */}
      <ConceptExplainerModal
        conceptKey={selectedConcept}
        onClose={() => setSelectedConcept(null)}
      />

      {/* Modal Interactivo de Inspección de Figuras y Gráficas de Investigación */}
      <FigureModal
        figure={selectedFigure}
        onClose={() => setSelectedFigure(null)}
      />
    </div>
  );
};

export default ModelLabView;
