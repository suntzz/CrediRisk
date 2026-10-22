import React, { useState } from 'react';
import { 
  FileCheck2, 
  FlaskConical, 
  ArrowRight, 
  Binary, 
  ShieldCheck, 
  Activity
} from 'lucide-react';
import { TechText } from './TechText';
import type { HealthStatus, ViewMode } from '../types';

interface HomeViewProps {
  onSelectView: (view: ViewMode) => void;
  health: HealthStatus | null;
}

export const HomeView: React.FC<HomeViewProps> = ({ onSelectView }) => {
  const [hoveredOption, setHoveredOption] = useState<'evaluator' | 'lab' | null>(null);
  // Contenido mostrado en el panel: se conserva mientras se cierra para que el colapso sea visible y no un corte
  const [panelOption, setPanelOption] = useState<'evaluator' | 'lab' | null>(null);

  const showOption = (option: 'evaluator' | 'lab') => {
    setHoveredOption(option);
    setPanelOption(option);
  };

  return (
    <div className="w-full flex flex-col justify-between bg-transparent text-slate-100 relative">
      {/* Area Principal: Composicion Centrada, Limpia y Minimalista */}
      <div className="relative z-10 w-full max-w-4xl mx-auto px-6 py-8 md:py-14 flex-1 flex flex-col items-center justify-center text-center">
        {/* Velo radial tenue: mejora la lectura del subtítulo sobre el fondo animado sin ocultarlo */}
        <div
          className="pointer-events-none absolute inset-x-0 top-0 h-[460px] -z-10 bg-[radial-gradient(ellipse_at_center,rgba(2,6,23,0.7)_0%,rgba(2,6,23,0.35)_45%,transparent_72%)]"
          aria-hidden="true"
        />
        {/* Titulo Central con TechText */}
        <div className="flex justify-center items-center w-full my-2">
          <div className="w-[320px] sm:w-[440px] md:w-[500px] h-[75px] sm:h-[95px] md:h-[110px] flex items-center justify-center select-none overflow-visible">
            <TechText
              text="CrediRisk"
              fontFamily="'Manrope', sans-serif"
              fontWeight={900}
              fontSize={68}
              color="#FFFFFF"
              accentColor="#38BDF8"
              dashLength={4}
              dashGap={2}
              strokeWidth={1.5}
              lineStyle="dashed"
              reveal="letter"
              draggable={false}
              sweep={true}
              speed={0.8}
              labels={true}
              selection={true}
              className="w-full h-full"
            />
          </div>
        </div>

        {/* Subtitulo Claro y Elegante */}
        <p className="mt-4 text-sm sm:text-base md:text-lg text-slate-300 font-sans max-w-xl mx-auto leading-relaxed text-center">
          Evaluación cuantitativa del riesgo crediticio mediante ensamble de redes neuronales profundas y análisis probabilístico multivariado.
        </p>

        {/* Botones de Accion Centrados (estilo minimalista de la foto) */}
        <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 w-full">
          {/* Boton 1: Abrir evaluador de credito */}
          <button
            type="button"
            onClick={() => onSelectView('evaluator')}
            onMouseEnter={() => showOption('evaluator')}
            onMouseLeave={() => setHoveredOption(null)}
            className={`relative group px-7 py-3.5 rounded-full text-sm font-semibold transition-all duration-300 flex items-center space-x-2.5 cursor-pointer active:scale-100 ${
              hoveredOption === 'evaluator'
                ? 'bg-white text-slate-950 shadow-[0_0_35px_rgba(56,189,248,0.55)] scale-105'
                : 'bg-white text-slate-950 hover:bg-slate-100 shadow-xl'
            }`}
          >
            <FileCheck2 className="w-4 h-4 text-blue-600" />
            <span>Abrir evaluador de crédito</span>
            <ArrowRight className="w-4 h-4 text-slate-800 group-hover:translate-x-1 transition-transform" />
          </button>

          {/* Boton 2: Explorar laboratorio del modelo */}
          <button
            type="button"
            onClick={() => onSelectView('lab')}
            onMouseEnter={() => showOption('lab')}
            onMouseLeave={() => setHoveredOption(null)}
            className={`relative group px-7 py-3.5 rounded-full text-sm font-semibold transition-all duration-300 flex items-center space-x-2.5 backdrop-blur-xl border cursor-pointer active:scale-100 ${
              hoveredOption === 'lab'
                ? 'bg-blue-950/80 text-white border-blue-400/80 shadow-[0_0_35px_rgba(59,130,246,0.45)] scale-105'
                : 'bg-slate-900/70 text-slate-200 border-white/15 hover:bg-slate-800/80 hover:text-white shadow-xl'
            }`}
          >
            <FlaskConical className="w-4 h-4 text-sky-400" />
            <span>Explorar laboratorio del modelo</span>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>

        {/* Panel Desplegable Interactivo al pasar el raton (hover) */}
        <div 
          className={`w-full max-w-xl mx-auto mt-6 transition-all duration-300 ease-out overflow-hidden ${
            hoveredOption 
              ? 'opacity-100 max-h-[340px] translate-y-0 pointer-events-auto' 
              : 'opacity-0 max-h-0 -translate-y-2 pointer-events-none'
          }`}
          onMouseEnter={() => {
            // Mantiene el panel abierto al interactuar directamente dentro de el
          }}
          onMouseLeave={() => setHoveredOption(null)}
        >
          {panelOption === 'evaluator' && (
            <div 
              className="bg-slate-950/85 backdrop-blur-2xl border border-blue-500/40 rounded-2xl p-6 shadow-2xl text-left relative ring-1 ring-blue-500/20"
              onMouseEnter={() => showOption('evaluator')}
            >
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-400 to-transparent" />
              
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="text-xs font-mono font-semibold text-blue-400 uppercase tracking-wider">
                    Inferencia en Tiempo Real
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  23 Variables Validadas
                </span>
              </div>

              <h3 className="text-base font-bold text-white mb-1.5">
                Evaluador de Crédito Financiero
              </h3>

              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
                Introduce los 23 parámetros financieros y de endeudamiento del solicitante para calcular la probabilidad de cumplimiento frente al umbral de decisión del modelo (0.50).
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-3 border-t border-slate-800/80 text-xs text-slate-300">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>Formulario 23 vars</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Activity className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Diagnóstico en vivo</span>
                </div>
                <div className="flex items-center space-x-2">
                  <FileCheck2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  <span>Dictamen y Radar</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-end">
                <button
                  type="button"
                  onClick={() => onSelectView('evaluator')}
                  className="inline-flex items-center space-x-1.5 text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors cursor-pointer"
                >
                  <span>Abrir Evaluador ahora</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}

          {panelOption === 'lab' && (
            <div 
              className="bg-slate-950/85 backdrop-blur-2xl border border-sky-500/40 rounded-2xl p-6 shadow-2xl text-left relative ring-1 ring-sky-500/20"
              onMouseEnter={() => showOption('lab')}
            >
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-sky-400 to-transparent" />

              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-sky-400" />
                  <span className="text-xs font-mono font-semibold text-sky-400 uppercase tracking-wider">
                    Evidencia Empírica de Modelos
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  Test ROC-AUC: 0.7448
                </span>
              </div>

              <h3 className="text-base font-bold text-white mb-1.5">
                Laboratorio del Modelo y Métricas
              </h3>

              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
                Inspecciona la arquitectura de las 3 redes neuronales profundas (MLP), la matriz de confusión sobre el conjunto Test congelado (49,650 registros) y las curvas ROC-AUC.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-3 border-t border-slate-800/80 text-xs text-slate-300">
                <div className="flex items-center space-x-2">
                  <Binary className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  <span>Ensemble Top-3 MLP</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Activity className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>Matriz de Confusión</span>
                </div>
                <div className="flex items-center space-x-2">
                  <FlaskConical className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span>49,650 Casos Test</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-end">
                <button
                  type="button"
                  onClick={() => onSelectView('lab')}
                  className="inline-flex items-center space-x-1.5 text-xs font-semibold text-sky-400 hover:text-sky-300 transition-colors cursor-pointer"
                >
                  <span>Abrir Laboratorio ahora</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomeView;
