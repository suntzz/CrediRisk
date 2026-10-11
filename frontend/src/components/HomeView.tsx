import React, { useState } from 'react';
import { 
  FileCheck2, 
  FlaskConical, 
  ArrowRight, 
  Binary, 
  ShieldCheck, 
  Activity
} from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { BrandLogo } from './BrandLogo';
import { TechText } from './TechText';
import { FaultyTerminal } from './FaultyTerminal';
import { PillNav } from './PillNav';
import { useTheme } from '../context/ThemeContext';
import type { HealthStatus, ViewMode } from '../types';

interface HomeViewProps {
  onSelectView: (view: ViewMode) => void;
  health: HealthStatus | null;
}

export const HomeView: React.FC<HomeViewProps> = ({ onSelectView, health }) => {
  const isHealthy = health?.status === 'healthy';
  const { isDark } = useTheme();
  const [hoveredOption, setHoveredOption] = useState<'evaluator' | 'lab' | null>(null);

  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return false;
  });

  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      const listener = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
      mediaQuery.addEventListener('change', listener);
      return () => mediaQuery.removeEventListener('change', listener);
    }
  }, []);

  const terminalBackground = React.useMemo(() => (
    <div 
      className="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none"
      aria-hidden="true"
    >
      <FaultyTerminal
        tint="#2563eb"
        scale={1.5}
        digitSize={1.2}
        timeScale={prefersReducedMotion ? 0 : 0.5}
        pause={prefersReducedMotion}
        scanlineIntensity={0.5}
        curvature={0.1}
        noiseAmp={1}
        brightness={0.7}
        mouseStrength={0.5}
        mouseReact={true}
        pageLoadAnimation={true}
        dpr={typeof window !== 'undefined' ? Math.min(window.devicePixelRatio || 1, 2) : 1}
        className="w-full h-full"
      />
    </div>
  ), [prefersReducedMotion]);

  return (
    <div className="min-h-[100dvh] flex flex-col justify-between bg-black text-slate-100 transition-colors relative overflow-hidden">
      {/* Fondo Tecnologico Interactivo FaultyTerminal (Azul Cobalto como la imagen de referencia) */}
      {terminalBackground}

      {/* Navegacion Superior Flotante tipo Pill inspirada en la referencia */}
      <div className="relative z-20 w-full px-6 pt-5">
        <header className="max-w-4xl mx-auto px-5 sm:px-6 py-2.5 flex items-center justify-between border border-white/10 rounded-full bg-slate-950/70 backdrop-blur-xl shadow-2xl">
          {/* Identidad de Marca */}
          <div className="flex items-center space-x-2.5">
            <BrandLogo size="sm" />
            <span className="font-display font-extrabold text-base tracking-tight text-white leading-none">
              CrediRisk
            </span>
          </div>

          {/* Acciones y selector de tema */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            <div 
              className="hidden md:inline-flex items-center space-x-2 px-2.5 py-1 rounded-full text-[11px] font-mono bg-slate-900/80 border border-white/10 text-slate-300 shadow-2xs h-8"
              title={isHealthy ? 'Servicio de inferencia activo' : 'Verificando servicio...'}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${isHealthy ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <span>{isHealthy ? 'API Conectada' : 'API Desconectada'}</span>
            </div>

            <PillNav
              items={[
                { label: 'Inicio', href: '#/', onClick: (e) => { e?.preventDefault(); onSelectView('home'); } },
                { label: 'Evaluador', href: '#/evaluator', onClick: (e) => { e?.preventDefault(); onSelectView('evaluator'); } },
                { label: 'Laboratorio', href: '#/lab', onClick: (e) => { e?.preventDefault(); onSelectView('lab'); } },
                { label: 'Sobre nosotros', href: '#/about', onClick: (e) => { e?.preventDefault(); onSelectView('about'); } },
              ]}
              activeHref="#/"
              baseColor={isDark ? '#0B1220' : '#FFFFFF'}
              pillColor={isDark ? '#1E293B' : '#F1F5F9'}
              pillTextColor={isDark ? '#E2E8F0' : '#475569'}
              hoveredPillTextColor={isDark ? '#FFFFFF' : '#0B1220'}
              initialLoadAnimation={false}
            />

            <ThemeToggle />
          </div>
        </header>
      </div>

      {/* Area Principal: Composicion Centrada, Limpia y Minimalista */}
      <main className="relative z-10 w-full max-w-4xl mx-auto px-6 py-12 md:py-20 flex-1 flex flex-col items-center justify-center text-center">
        {/* Badge Pill Tecnologico */}
        <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full text-xs font-mono bg-blue-950/70 border border-blue-500/30 text-blue-300 backdrop-blur-md mb-6 shadow-xs">
          <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-white text-slate-950">AI</span>
          <span>Redes Neuronales Profundas · 23 Variables</span>
        </div>

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
          Evaluacion cuantitativa del riesgo crediticio mediante ensamble de redes neuronales profundas y analisis probabilistico multivariado.
        </p>

        {/* Botones de Accion Centrados (estilo minimalista de la foto) */}
        <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 w-full">
          {/* Boton 1: Abrir evaluador de credito */}
          <button
            type="button"
            onClick={() => onSelectView('evaluator')}
            onMouseEnter={() => setHoveredOption('evaluator')}
            onMouseLeave={() => setHoveredOption(null)}
            className={`relative group px-7 py-3.5 rounded-full text-sm font-semibold transition-all duration-300 flex items-center space-x-2.5 cursor-pointer ${
              hoveredOption === 'evaluator'
                ? 'bg-white text-slate-950 shadow-[0_0_35px_rgba(56,189,248,0.55)] scale-105'
                : 'bg-white text-slate-950 hover:bg-slate-100 shadow-xl'
            }`}
          >
            <FileCheck2 className="w-4 h-4 text-blue-600" />
            <span>Abrir evaluador de credito</span>
            <ArrowRight className="w-4 h-4 text-slate-800 group-hover:translate-x-1 transition-transform" />
          </button>

          {/* Boton 2: Explorar laboratorio del modelo */}
          <button
            type="button"
            onClick={() => onSelectView('lab')}
            onMouseEnter={() => setHoveredOption('lab')}
            onMouseLeave={() => setHoveredOption(null)}
            className={`relative group px-7 py-3.5 rounded-full text-sm font-semibold transition-all duration-300 flex items-center space-x-2.5 backdrop-blur-xl border cursor-pointer ${
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
          {hoveredOption === 'evaluator' && (
            <div 
              className="bg-slate-950/85 backdrop-blur-2xl border border-blue-500/40 rounded-2xl p-6 shadow-2xl text-left relative ring-1 ring-blue-500/20"
              onMouseEnter={() => setHoveredOption('evaluator')}
            >
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-400 to-transparent" />
              
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs font-mono font-semibold text-blue-400 uppercase tracking-wider">
                    Inferencia en Tiempo Real
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  23 Variables Validadas
                </span>
              </div>

              <h3 className="text-base font-bold text-white mb-1.5">
                Evaluador de Credito Financiero
              </h3>

              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
                Introduce los 23 parametros financieros y de endeudamiento del solicitante para calcular la probabilidad objetiva de cumplimiento bajo el umbral calibrado del modelo (0.0700).
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-3 border-t border-slate-800/80 text-xs text-slate-300">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>Formulario 23 vars</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Activity className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Diagnostico en vivo</span>
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

          {hoveredOption === 'lab' && (
            <div 
              className="bg-slate-950/85 backdrop-blur-2xl border border-sky-500/40 rounded-2xl p-6 shadow-2xl text-left relative ring-1 ring-sky-500/20"
              onMouseEnter={() => setHoveredOption('lab')}
            >
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-sky-400 to-transparent" />

              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
                  <span className="text-xs font-mono font-semibold text-sky-400 uppercase tracking-wider">
                    Evidencia Empirica de Modelos
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  Test ROC-AUC: 0.7448
                </span>
              </div>

              <h3 className="text-base font-bold text-white mb-1.5">
                Laboratorio del Modelo y Metricas
              </h3>

              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
                Inspecciona la arquitectura de las 3 redes neuronales profundas (MLP), la matriz de confusion sobre el conjunto Test congelado (49,650 registros) y las curvas ROC-AUC.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-3 border-t border-slate-800/80 text-xs text-slate-300">
                <div className="flex items-center space-x-2">
                  <Binary className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  <span>Ensemble Top-3 MLP</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Activity className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>Matriz de Confusion</span>
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
      </main>

      {/* Pie de pagina unificado */}
      <footer className="relative z-10 w-full max-w-5xl mx-auto px-6 py-6 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
        <p className="font-sans">
          Redes Neuronales Profundas para Evaluacion Crediticia
        </p>
        <button
          type="button"
          onClick={() => onSelectView('about')}
          className="text-slate-400 hover:text-white transition-colors cursor-pointer"
        >
          Sobre nosotros
        </button>
      </footer>
    </div>
  );
};

export default HomeView;
