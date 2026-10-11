import React from 'react';
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
import { QuantitativeMesh } from './QuantitativeMesh';
import { TechText } from './TechText';
import { MagicBento, ParticleCard } from './MagicBento';
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

  return (
    <div className="min-h-[100dvh] flex flex-col justify-between bg-slate-50 dark:bg-[#0B1220] text-slate-900 dark:text-slate-100 transition-colors relative overflow-hidden">
      {/* Retícula técnica sutil de fondo */}
      <div className="absolute inset-0 bg-atelier-grid opacity-75 pointer-events-none" aria-hidden="true" />
      
      {/* Constelación dimensional abstracta de 23 variables */}
      <div className="absolute right-[-10%] top-[-5%] w-[650px] h-[650px] opacity-40 dark:opacity-30 pointer-events-none hidden lg:block">
        <QuantitativeMesh className="w-full h-full" />
      </div>

      {/* Navegación Superior */}
      <header className="relative z-10 w-full max-w-6xl mx-auto px-6 py-5 flex items-center justify-between border-b border-slate-200/70 dark:border-slate-800/60 backdrop-blur-sm">
        {/* Identidad de Marca Oficial */}
        <div className="flex items-center space-x-2.5">
          <BrandLogo size="sm" />
          <span className="font-display font-extrabold text-base tracking-tight text-slate-950 dark:text-white leading-none">
            CrediRisk
          </span>
        </div>

        {/* Acciones y selector de tema */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          <div 
            className="hidden xl:inline-flex items-center space-x-2 px-2.5 py-1 rounded-full text-[11px] font-mono bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 shadow-2xs h-9"
            title={isHealthy ? 'Servicio de inferencia activo' : 'Verificando servicio...'}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-amber-500'}`} />
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

      {/* Área Principal: Composición Asimétrica Editorial */}
      <main className="relative z-10 w-full max-w-6xl mx-auto px-6 py-8 md:py-12 flex-1 flex flex-col justify-center">
        {/* Titular y subtítulo exactos */}
        <div className="max-w-3xl mb-10 md:mb-12">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-md text-[11px] font-mono uppercase tracking-[0.14em] font-semibold bg-blue-50 dark:bg-blue-950/70 text-blue-700 dark:text-blue-300 border border-blue-200/80 dark:border-blue-900/60 mb-3">
            <Binary className="w-3.5 h-3.5" />
            <span>Deep Learning</span>
          </div>
          
          <h1 
            className="w-[280px] sm:w-[330px] lg:w-[370px] h-[60px] sm:h-[72px] lg:h-[82px] flex items-center select-none -ml-1 sm:-ml-2 overflow-visible"
            aria-label="CrediRisk"
          >
            <TechText
              text="CrediRisk"
              fontFamily="'Manrope', sans-serif"
              fontWeight={900}
              fontSize={56}
              color={isDark ? '#FFFFFF' : '#0B1220'}
              accentColor={isDark ? '#38BDF8' : '#2563EB'}
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
          </h1>
          
          <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400 leading-relaxed max-w-2xl font-sans">
            Plataforma de evaluación cuantitativa del riesgo crediticio mediante ensamble de redes neuronales profundas y análisis probabilístico multivariado.
          </p>
        </div>

        {/* Las dos experiencias principales integradas con MagicBento */}
        <MagicBento
          enableStars={true}
          enableSpotlight={true}
          enableBorderGlow={true}
          enableTilt={true}
          enableMagnetism={false}
          clickEffect={true}
          particleCount={8}
          spotlightRadius={340}
          glowColor={isDark ? '56, 189, 248' : '37, 99, 235'}
          blendMode={isDark ? 'screen' : 'normal'}
          className="w-full mb-2"
          gridClassName="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch"
        >
          {/* Tarjeta 1: Abrir evaluador de crédito (7 columnas) */}
          <ParticleCard
            className="lg:col-span-7 magic-bento-card magic-bento-card--border-glow group p-7 md:p-8 flex flex-col justify-between"
            style={{
              '--glow-color': isDark ? '56, 189, 248' : '37, 99, 235'
            } as React.CSSProperties}
            glowColor={isDark ? '56, 189, 248' : '37, 99, 235'}
            particleCount={8}
            enableTilt={true}
            clickEffect={true}
            onClick={() => onSelectView('evaluator')}
            aria-label="Abrir evaluador de crédito: Inferencia activa con 23 variables validadas"
          >
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className="w-11 h-11 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-xs group-hover:scale-105 transition-transform duration-200">
                  <FileCheck2 className="w-5 h-5" />
                </div>
                <span className="font-mono text-[11px] text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 border border-blue-200/60 dark:border-blue-900/50 px-2.5 py-1 rounded-md font-medium">
                  Inferencia Activa
                </span>
              </div>

              <h2 className="font-display text-xl sm:text-2xl font-bold text-slate-950 dark:text-white mb-2.5 tracking-tight group-hover:text-blue-600 dark:group-hover:text-sky-400 transition-colors duration-200">
                Evaluador de crédito
              </h2>
              
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed mb-6 font-sans">
                Introduce los 23 parámetros financieros y personales del solicitante para calcular la probabilidad objetiva de cumplimiento bajo el umbral calibrado del modelo.
              </p>

              {/* Ficha técnica resumida */}
              <div className="grid grid-cols-2 gap-3 mb-6 pt-4 border-t border-slate-100 dark:border-slate-800/80">
                <div className="flex items-center space-x-2 text-xs text-slate-600 dark:text-slate-400">
                  <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" />
                  <span>23 Variables Validadas</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-slate-600 dark:text-slate-400">
                  <Activity className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  <span>Diagnóstico Multivariado</span>
                </div>
              </div>
            </div>

            {/* Acción de la tarjeta */}
            <div className="pt-2">
              <div className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-blue-600 group-hover:bg-blue-700 text-white text-xs sm:text-sm font-semibold shadow-xs transition-colors duration-200">
                <span className="font-sans font-medium">Abrir evaluador de crédito</span>
                <div className="flex items-center space-x-1.5">
                  <span className="text-[11px] opacity-80 font-normal hidden sm:inline">Comenzar</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-200" />
                </div>
              </div>
            </div>
          </ParticleCard>

          {/* Tarjeta 2: Explorar el laboratorio del modelo (5 columnas) */}
          <ParticleCard
            className="lg:col-span-5 magic-bento-card magic-bento-card--border-glow group p-7 md:p-8 flex flex-col justify-between"
            style={{
              '--glow-color': isDark ? '148, 163, 184' : '59, 130, 246'
            } as React.CSSProperties}
            glowColor={isDark ? '148, 163, 184' : '59, 130, 246'}
            particleCount={8}
            enableTilt={true}
            clickEffect={true}
            onClick={() => onSelectView('lab')}
            aria-label="Explorar el laboratorio del modelo: Evidencia empírica y métricas del ensemble"
          >
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className="w-11 h-11 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 flex items-center justify-center border border-slate-200 dark:border-slate-700 group-hover:scale-105 transition-transform duration-200">
                  <FlaskConical className="w-5 h-5" />
                </div>
                <span className="font-mono text-[11px] text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-2.5 py-1 rounded-md font-medium">
                  Evidencia Empírica
                </span>
              </div>

              <h2 className="font-display text-xl sm:text-2xl font-bold text-slate-950 dark:text-white mb-2.5 tracking-tight group-hover:text-blue-600 dark:group-hover:text-sky-400 transition-colors duration-200">
                Laboratorio del modelo
              </h2>
              
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed mb-6 font-sans">
                Inspecciona la arquitectura de las 3 redes neuronales, la matriz de confusión sobre el conjunto Test congelado y los experimentos de optimización.
              </p>

              {/* Métricas clave en formato tabular */}
              <div className="bg-slate-50 dark:bg-slate-950/60 rounded-xl p-3.5 border border-slate-200/80 dark:border-slate-800/80 mb-6 font-mono text-xs">
                <div className="flex justify-between items-center py-1 border-b border-slate-200/60 dark:border-slate-800/60">
                  <span className="text-slate-500 font-sans">Modelo Final</span>
                  <span className="font-semibold text-slate-900 dark:text-white">Ensemble Top-3</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-slate-200/60 dark:border-slate-800/60">
                  <span className="text-slate-500 font-sans">Test ROC-AUC</span>
                  <span className="font-semibold text-blue-600 dark:text-blue-400 tabular-nums">0.7448</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-500 font-sans">Observaciones</span>
                  <span className="font-semibold text-slate-900 dark:text-white tabular-nums">49,650</span>
                </div>
              </div>
            </div>

            {/* Acción de la tarjeta */}
            <div className="pt-2">
              <div className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-slate-900 dark:bg-slate-800 group-hover:bg-slate-800 dark:group-hover:bg-slate-700 text-white text-xs sm:text-sm font-semibold border border-slate-800 dark:border-slate-700 shadow-xs transition-colors duration-200">
                <span className="font-sans font-medium">Explorar el laboratorio del modelo</span>
                <div className="flex items-center space-x-1.5">
                  <span className="text-[11px] opacity-70 font-normal hidden sm:inline">Métricas</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-200" />
                </div>
              </div>
            </div>
          </ParticleCard>
        </MagicBento>
      </main>

      {/* Pie de página unificado */}
      <footer className="relative z-10 w-full max-w-6xl mx-auto px-6 py-6 border-t border-slate-200/70 dark:border-slate-800/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">
        <p className="font-sans">
          Redes Neuronales Profundas para Evaluación Crediticia
        </p>
        <button
          type="button"
          onClick={() => onSelectView('about')}
          className="text-slate-500 dark:text-slate-400 hover:text-slate-950 dark:hover:text-white transition-colors"
        >
          Sobre nosotros
        </button>
      </footer>
    </div>
  );
};

export default HomeView;
