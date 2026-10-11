import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  const [isTransitioning, setIsTransitioning] = useState<boolean>(false);
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
    currentViewRef.current = currentView;
  }, [currentView]);

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

  // Transición rápida, suave y natural entre páginas (100ms salida + 150ms entrada = 250ms total)
  const navigateTo = useCallback((targetView: ViewMode, updateHistory = true) => {
    if (targetView === currentViewRef.current || isTransitioning) return;

    const container = viewContainerRef.current;
    const prefersReduced = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

    setIsTransitioning(true);

    if (updateHistory) {
      const newHash = targetView === 'home' ? '#/' : `#/${targetView}`;
      if (window.location.hash !== newHash) {
        window.history.pushState({ view: targetView }, '', newHash);
      }
    }

    if (!container || prefersReduced) {
      if (container) {
        gsap.killTweensOf(container);
        gsap.to(container, {
          opacity: 0,
          duration: 0.08,
          ease: 'power2.inOut',
          onComplete: () => {
            setCurrentView(targetView);
            window.scrollTo({ top: 0, behavior: 'instant' });
            gsap.fromTo(
              container,
              { opacity: 0 },
              {
                opacity: 1,
                duration: 0.1,
                ease: 'power2.out',
                onComplete: () => {
                  gsap.set(container, { clearProps: 'all' });
                  setIsTransitioning(false);
                }
              }
            );
          }
        });
      } else {
        setCurrentView(targetView);
        setIsTransitioning(false);
      }
      return;
    }

    gsap.killTweensOf(container);
    gsap.to(container, {
      opacity: 0,
      y: -6,
      duration: 0.1,
      ease: 'power2.inOut',
      onComplete: () => {
        setCurrentView(targetView);
        window.scrollTo({ top: 0, behavior: 'instant' });

        gsap.fromTo(
          container,
          {
            opacity: 0,
            y: 8,
          },
          {
            opacity: 1,
            y: 0,
            duration: 0.15,
            ease: 'power2.out',
            onComplete: () => {
              gsap.set(container, { clearProps: 'all' });
              setIsTransitioning(false);
            }
          }
        );
      }
    });
  }, [isTransitioning]);

  // Sincronización con botones Atrás y Adelante del navegador
  useEffect(() => {
    const handlePopState = () => {
      const target = getViewFromHash();
      if (target !== currentViewRef.current) {
        navigateTo(target, false);
      }
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
      <GlobalDock currentView={currentView} onNavigate={navigateTo} />

      {/* Contenedor Principal con Transición Fluida */}
      <main
        ref={viewContainerRef}
        className={`flex-1 w-full relative z-10 transition-opacity print:m-0 print:p-0 ${
          isTransitioning ? 'pointer-events-none' : ''
        }`}
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
