import React, { useEffect, useRef } from 'react';
import { X, Info, AlertTriangle, BarChart2 } from 'lucide-react';
import type { DocFigure } from './labData';

interface FigureModalProps {
  figure: DocFigure | null;
  onClose: () => void;
}

export const FigureModal: React.FC<FigureModalProps> = ({ figure, onClose }) => {
  const closeBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (figure) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
      setTimeout(() => closeBtnRef.current?.focus(), 50);
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [figure, onClose]);

  if (!figure) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="figure-modal-title"
      onClick={onClose}
    >
      <div 
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-4xl bg-[#0B1220] border border-white/10 rounded-2xl shadow-[0_30px_70px_rgba(0,0,0,0.85)] overflow-hidden flex flex-col max-h-[92vh] text-slate-100 animate-in zoom-in-95 duration-200"
      >
        {/* Cabecera */}
        <div className="p-4 sm:p-5 border-b border-white/10 bg-slate-950/70 flex items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-mono font-bold px-2 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
              FIGURA {figure.number}
            </span>
            <div>
              <h2 id="figure-modal-title" className="text-base sm:text-lg font-display font-bold text-white tracking-tight">
                {figure.title}
              </h2>
              <span className="text-[11px] font-mono text-slate-400">
                {figure.category} · Documentación Oficial CrediRisk
              </span>
            </div>
          </div>
          <button
            ref={closeBtnRef}
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Cerrar visor de gráfica"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido scrolleable */}
        <div className="overflow-y-auto p-4 sm:p-6 space-y-5">
          {/* Imagen de la gráfica */}
          <div className="rounded-xl border border-white/10 bg-black/60 p-2 sm:p-4 flex items-center justify-center overflow-hidden">
            <img 
              src={figure.filename} 
              alt={figure.title}
              className="max-h-[50vh] sm:max-h-[55vh] w-auto object-contain rounded-lg shadow-lg"
              loading="eager"
            />
          </div>

          {/* Ficha de lectura científica de la gráfica */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
              <span className="font-bold text-slate-200 flex items-center space-x-1.5">
                <BarChart2 className="w-3.5 h-3.5 text-blue-400" />
                <span>¿Qué mide esta visualización?</span>
              </span>
              <p className="text-slate-300 leading-relaxed">{figure.description}</p>
              <div className="pt-2 border-t border-white/5 space-y-1 font-mono text-[11px]">
                <div><strong className="text-slate-400">Eje X:</strong> <span className="text-slate-300">{figure.xAxis}</span></div>
                <div><strong className="text-slate-400">Eje Y:</strong> <span className="text-slate-300">{figure.yAxis}</span></div>
                <div><strong className="text-slate-400">Series:</strong> <span className="text-slate-300">{figure.series}</span></div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/25 space-y-1.5">
                <span className="font-bold text-blue-300 flex items-center space-x-1.5">
                  <Info className="w-3.5 h-3.5 text-blue-400" />
                  <span>Hallazgo Empírico Clave</span>
                </span>
                <p className="text-slate-200 leading-relaxed text-xs">{figure.keyFinding}</p>
              </div>

              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/25 space-y-1.5">
                <span className="font-bold text-amber-300 flex items-center space-x-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span>Advertencia Metodológica</span>
                </span>
                <p className="text-amber-200/90 leading-relaxed text-xs">{figure.methodologicalCaveat}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Pie */}
        <div className="p-3.5 px-6 border-t border-white/10 bg-slate-950/70 flex items-center justify-between text-xs text-slate-400">
          <span className="font-mono text-[11px]">Archivo: {figure.filename}</span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-medium transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};
