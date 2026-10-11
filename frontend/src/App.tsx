import React, { useState, useEffect, useRef, useCallback } from 'react';
import { gsap } from 'gsap';
import { ThemeProvider } from './context/ThemeContext';
import { HomeView } from './components/HomeView';
import { EvaluatorView } from './components/EvaluatorView';
import { ModelLabView } from './components/ModelLabView';
import { AboutUsView } from './components/AboutUsView';
import { fetchHealth, fetchMetrics } from './services/api';
import type { ApplicantFormData, HealthStatus, SystemMetrics, ViewMode } from './types';

const DEFAULT_APPLICANT: ApplicantFormData = {
  id_solicitud: 172745,
  edad: 43.9,
  ingreso_mensual: 202500.0,
  obligaciones_mensuales: 153454.09,
  estado_civil: 'Single / not married',
  ingreso_disponible: 13522.91,
  monto_solicitado: 835380.0,
  plazo_meses: 48.0,
  cuota_estimada: 35523.0,
  tasa_interes_ea: 49.31,
  nivel_endeudamiento_pct: 93.32,
  score_crediticio: 585.0,
  numero_creditos_activos: 2.0,
  saldo_total_creditos: 2619045.0,
  numero_cuotas_mora: 0.0,
  dias_maximo_mora: 0.0,
  porcentaje_pagos_oportunos: 100.0,
  antiguedad_laboral_anios: 7.17,
  patrimonio_indice: 4,
  antiguedad_cliente_anios: 7.74,
  linea_negocio: 'Cash loans',
  tipo_contrato: 'Working',
  personas_a_cargo: 1,
  tipo_vivienda: 'House / apartment',
  model_type: 'ensemble',
};

const getViewFromHash = (): ViewMode => {
  const hash = window.location.hash.replace(/^#\/?/, '').trim();
  if (hash === 'evaluator') return 'evaluator';
  if (hash === 'lab') return 'lab';
  if (hash === 'about') return 'about';
  return 'home';
};

const MainContent: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewMode>(getViewFromHash);
  const [isTransitioning, setIsTransitioning] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const viewContainerRef = useRef<HTMLDivElement>(null);
  const currentViewRef = useRef<ViewMode>(currentView);

  useEffect(() => {
    currentViewRef.current = currentView;
  }, [currentView]);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(err => console.warn('Backend aun no disponible:', err.message));

    fetchMetrics()
      .then(setMetrics)
      .catch(err => console.warn('Error cargando metricas:', err.message));
  }, []);

  // Coordinated section navigation transition with GSAP
  const navigateTo = useCallback((targetView: ViewMode, updateHistory = true) => {
    if (targetView === currentViewRef.current || isTransitioning) return;

    const fromView = currentViewRef.current;
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
      // Discrete, accessible cross-fade for reduced motion
      if (container) {
        gsap.to(container, {
          opacity: 0,
          duration: 0.14,
          ease: 'power2.inOut',
          onComplete: () => {
            setCurrentView(targetView);
            window.scrollTo({ top: 0, behavior: 'instant' });
            gsap.fromTo(
              container,
              { opacity: 0 },
              {
                opacity: 1,
                duration: 0.18,
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

    // Directional transition:
    // Option 1 (evaluator, left card): slide/perspective fold left (-1)
    // Option 2 (lab, right card): slide/perspective fold right (+1)
    // Return to home: reverse directional motion
    let direction = 0;
    if (fromView === 'home') {
      direction = targetView === 'evaluator' ? -1 : 1;
    } else if (targetView === 'home') {
      direction = fromView === 'evaluator' ? 1 : -1;
    }

    // 1. Exit animation: current page smoothly slides and tilts subtly
    gsap.to(container, {
      opacity: 0,
      x: direction * 45,
      rotateY: direction * 2.2,
      scale: 0.985,
      duration: 0.26,
      ease: 'power2.in',
      transformPerspective: 1100,
      onComplete: () => {
        // 2. Switch view in React and scroll to top
        setCurrentView(targetView);
        window.scrollTo({ top: 0, behavior: 'instant' });

        // 3. Entrance animation: new section unfolds smoothly into place
        gsap.fromTo(
          container,
          {
            opacity: 0,
            x: -direction * 35,
            rotateY: -direction * 1.8,
            scale: 0.985,
            transformPerspective: 1100
          },
          {
            opacity: 1,
            x: 0,
            rotateY: 0,
            scale: 1,
            duration: 0.34,
            ease: 'power3.out',
            onComplete: () => {
              gsap.set(container, { clearProps: 'all' });
              setIsTransitioning(false);
            }
          }
        );
      }
    });
  }, [isTransitioning]);

  // Synchronize browser history and hash navigation (Back/Forward buttons)
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
            defaultData={DEFAULT_APPLICANT}
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
    <div
      ref={viewContainerRef}
      className={`min-h-screen w-full transition-opacity ${
        isTransitioning ? 'pointer-events-none' : ''
      }`}
    >
      {renderCurrentView()}
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
