import React, { useState, useEffect, useRef, useCallback } from 'react';
import { flushSync } from 'react-dom';
import { gsap } from 'gsap';
import { ThemeProvider } from './context/ThemeContext';
import { GlobalDock } from './components/GlobalDock';
import { FaultyTerminal } from './components/FaultyTerminal';
import { HomeView } from './components/HomeView';
import { EvaluatorView } from './components/EvaluatorView';
import { ModelLabView } from './components/ModelLabView';
import { AboutUsView } from './components/AboutUsView';
import { fetchHealth, fetchMetrics } from './services/api';
import type { HealthStatus, SystemMetrics, ViewMode } from './types';

const getViewFromHash = (): ViewMode => {
  const hash = window.location.hash.replace(/^#\/?/, '').trim();
  if (hash === 'evaluator') return 'evaluator';
  if (hash === 'lab') return 'lab';
  if (hash === 'about' || hash === 'sobre-nosotros') return 'about';
  return 'home';
};

const MainContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewMode>(getViewFromHash);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const viewContainerRef = useRef<HTMLElement>(null);
  const currentViewRef = useRef<ViewMode>(currentView);

  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return false;
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      const listener = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
      mediaQuery.addEventListener('change', listener);
      return () => mediaQuery.removeEventListener('change', listener);
    }
  }, []);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(err => console.warn('Backend aun no disponible:', err.message));

    fetchMetrics()
      .then(setMetrics)
      .catch(err => console.warn('Error cargando metricas:', err.message));
  }, []);

  // Fundido cruzado discreto entre pestañas (120ms salida + 180ms entrada), solo opacidad.
  // La última navegación solicitada siempre gana: un clic o un "Atrás" a mitad de transición
  // redirige al nuevo destino en lugar de descartarse, manteniendo URL, vista y dock sincronizados.
  const transitionPhaseRef = useRef<'idle' | 'out' | 'in'>('idle');
  const targetViewRef = useRef<ViewMode>(currentView);
  // El dock refleja el destino solicitado de inmediato, sin esperar a que salga la vista actual
  const [requestedView, setRequestedView] = useState<ViewMode>(currentView);

  const navigateTo = useCallback((targetView: ViewMode, updateHistory = true) => {
    if (updateHistory) {
      const newHash = targetView === 'home' ? '#/' : `#/${targetView}`;
      if (window.location.hash !== newHash) {
        window.history.pushState({ view: targetView }, '', newHash);
      }
    }

    targetViewRef.current = targetView;
    setRequestedView(targetView);
    const phase = transitionPhaseRef.current;

    // La salida en curso leerá el destino más reciente al terminar
    if (phase === 'out') return;
    if (phase === 'idle' && targetView === currentViewRef.current) return;

    const container = viewContainerRef.current;
    const prefersReduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

    const commitView = (view: ViewMode) => {
      // flushSync garantiza que la vista nueva esté en el DOM antes de iniciar la entrada
      flushSync(() => setCurrentView(view));
      currentViewRef.current = view;
      window.scrollTo({ top: 0, behavior: 'instant' });
    };

    if (!container || prefersReduced) {
      commitView(targetView);
      return;
    }

    const fadeIn = () => {
      transitionPhaseRef.current = 'in';
      gsap.to(container, {
        opacity: 1,
        duration: 0.18,
        ease: 'power2.out',
        onComplete: () => {
          gsap.set(container, { clearProps: 'opacity,pointerEvents' });
          transitionPhaseRef.current = 'idle';
        }
      });
    };

    gsap.killTweensOf(container);

    // Se pidió volver a la vista que ya está entrando: basta con completar la entrada
    if (phase === 'in' && targetView === currentViewRef.current) {
      fadeIn();
      return;
    }

    transitionPhaseRef.current = 'out';
    gsap.set(container, { pointerEvents: 'none' });
    gsap.to(container, {
      opacity: 0,
      duration: 0.12,
      ease: 'power2.in',
      onComplete: () => {
        const next = targetViewRef.current;
        if (next !== currentViewRef.current) commitView(next);
        fadeIn();
      }
    });
  }, []);

  // El scroll lo gestiona la navegación; evita que el navegador lo restaure sobre la vista saliente
  useEffect(() => {
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }
  }, []);

  // Sincronización con botones Atrás y Adelante del navegador
  useEffect(() => {
    const handlePopState = () => {
      navigateTo(getViewFromHash(), false);
    };

    window.addEventListener('popstate', handlePopState);
    window.addEventListener('hashchange', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
      window.removeEventListener('hashchange', handlePopState);
    };
  }, [navigateTo]);

  const renderCurrentView = () => {
    switch (currentView) {
      case 'evaluator':
        return (
          <EvaluatorView
            onBackToHome={() => navigateTo('home')}
            onOpenLab={() => navigateTo('lab')}
            onOpenAbout={() => navigateTo('about')}
          />
        );
      case 'lab':
        return (
          <ModelLabView
            onBackToHome={() => navigateTo('home')}
            onOpenEvaluator={() => navigateTo('evaluator')}
            onOpenAbout={() => navigateTo('about')}
            metrics={metrics}
          />
        );
      case 'about':
        return (
          <AboutUsView
            onBackToHome={() => navigateTo('home')}
            onOpenEvaluator={() => navigateTo('evaluator')}
            onOpenLab={() => navigateTo('lab')}
          />
        );
      case 'home':
      default:
        return (
          <HomeView
            onSelectView={navigateTo}
            health={health}
          />
        );
    }
  };

  return (
    <div className="min-h-screen w-full bg-black text-slate-100 relative flex flex-col selection:bg-blue-600/30 selection:text-white print:bg-white print:text-slate-900 print:min-h-0">
      {/* Fondo Tecnológico Interactivo FaultyTerminal Persistente */}
      <div 
        className="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none print:hidden"
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

      {/* Dock Global Compartido con GooeyNav y Liquid Glass */}
      <GlobalDock currentView={requestedView} onNavigate={navigateTo} />

      {/* Contenedor Principal con Transición Fluida */}
      <main
        ref={viewContainerRef}
        className="flex-1 w-full relative z-10 print:m-0 print:p-0"
      >
        {renderCurrentView()}
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <MainContent />
    </ThemeProvider>
  );
};

export default App;
