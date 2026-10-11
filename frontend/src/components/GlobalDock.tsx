import React, { useMemo } from 'react';
import { BrandLogo } from './BrandLogo';
import { GooeyNav, type GooeyNavItem } from './GooeyNav';
import type { ViewMode } from '../types';

export interface GlobalDockProps {
  currentView: ViewMode;
  onNavigate: (view: ViewMode) => void;
}

interface NavDestination extends GooeyNavItem {
  view: ViewMode;
}

export const GlobalDock: React.FC<GlobalDockProps> = ({ currentView, onNavigate }) => {
  const destinations: NavDestination[] = useMemo(
    () => [
      { label: 'Inicio', href: '#/', view: 'home' },
      { label: 'Evaluador', href: '#/evaluator', view: 'evaluator' },
      { label: 'Laboratorio', href: '#/lab', view: 'lab' },
      { label: 'Sobre nosotros', href: '#/about', view: 'about' },
    ],
    []
  );

  const activeIndex = useMemo(() => {
    const idx = destinations.findIndex(d => d.view === currentView);
    return idx >= 0 ? idx : 0;
  }, [destinations, currentView]);

  return (
    <header className="sticky top-0 z-40 w-full px-4 sm:px-6 pt-3 sm:pt-4 pb-2 pointer-events-none select-none print:hidden">
      <div className="max-w-5xl mx-auto flex items-center justify-between gap-3 sm:gap-6 px-4 sm:px-6 py-2 rounded-full pointer-events-auto border border-white/10 bg-slate-950/70 backdrop-blur-2xl shadow-[0_20px_50px_rgba(0,0,0,0.65),inset_0_1px_1px_rgba(255,255,255,0.18),inset_0_-1px_1px_rgba(0,0,0,0.4)] transition-all">
        {/* Lado izquierdo: Identidad de Marca CrediRisk */}
        <button
          type="button"
          onClick={() => onNavigate('home')}
          className="flex items-center shrink-0 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded-full py-0.5 transition-transform active:scale-95 text-left"
          title="CrediRisk - Inicio"
        >
          <BrandLogo size="sm" className="shrink-0" />
          <span className="font-display font-extrabold text-base tracking-tight text-white leading-none -ml-1.5">
            rediRisk
          </span>
        </button>

        {/* Lado derecho: GooeyNav integrado en Liquid Glass */}
        <div className="flex items-center justify-end shrink-0">
          <GooeyNav
            items={destinations}
            activeIndex={activeIndex}
            theme="dark"
            size="md"
            frame
            particleCount={15}
            spread={56}
            animationTime={600}
            timeVariance={300}
            gooeyness={0.5}
            wobble={0.5}
            hoverEffect
            onChange={(index) => {
              const target = destinations[index];
              if (target && target.view !== currentView) {
                onNavigate(target.view);
              }
            }}
            style={{
              '--gn-frame': 'rgba(255, 255, 255, 0.04)',
              '--gn-frame-edge': 'rgba(255, 255, 255, 0.08)',
              '--gn-frame-highlight': 'rgba(255, 255, 255, 0.12)',
              '--gn-frame-shadow': 'none',
              '--gn-ink': '#ffffff',
              '--gn-muted': 'rgba(226, 232, 240, 0.72)',
            } as React.CSSProperties}
          />
        </div>
      </div>
    </header>
  );
};

export default GlobalDock;
