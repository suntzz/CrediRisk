import React from 'react';
import { ZoomIn, ArrowRight } from 'lucide-react';
import { DOC_FIGURES, type DocFigure } from './labData';

interface FigureGalleryViewProps {
  onSelectFigure: (fig: DocFigure) => void;
}

export const FigureGalleryView: React.FC<FigureGalleryViewProps> = ({ onSelectFigure }) => {
  return (
    <div className="bg-[#0B1220] p-6 sm:p-7 rounded-2xl border border-white/10 shadow-lg space-y-6">
      {/* Encabezado */}
      <div className="border-b border-white/10 pb-4">
        <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-blue-400 block mb-1">
          Evidencia Gráfica Documentada
        </span>
        <h2 className="text-base sm:text-lg font-display font-bold text-white tracking-tight">
          Galería de Visualizaciones y Gráficas de Investigación
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Gráficas generadas por el script de documentación oficial (docs/generate_doc_charts.py) y verificadas con los resultados de los experimentos.
          Haz clic en cualquier gráfica para inspeccionar sus ejes, series, hallazgos y advertencias metodológicas.
        </p>
      </div>

      {/* Grid de Gráficas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {DOC_FIGURES.map((fig) => (
          <button
            key={fig.id}
            type="button"
            onClick={() => onSelectFigure(fig)}
            className="group text-left p-3.5 rounded-xl border border-white/10 bg-slate-950/60 hover:bg-slate-900/80 hover:border-blue-500/50 transition-all flex flex-col justify-between space-y-3 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {/* Imagen Miniatura */}
            <div className="w-full h-32 rounded-lg bg-black/60 border border-white/5 overflow-hidden relative flex items-center justify-center p-2">
              <img 
                src={fig.filename} 
                alt={fig.title} 
                className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-blue-600/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <span className="p-2 rounded-full bg-slate-950/80 text-white shadow">
                  <ZoomIn className="w-4 h-4 text-blue-400" />
                </span>
              </div>
            </div>

            {/* Metadatos */}
            <div>
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1">
                <span className="shrink-0 whitespace-nowrap px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-bold">
                  FIG. {fig.number}
                </span>
                <span className="min-w-0 truncate ml-2">{fig.category}</span>
              </div>
              <h3 className="text-xs font-sans font-bold text-white group-hover:text-blue-300 transition-colors line-clamp-2">
                {fig.title}
              </h3>
              <p className="text-[11px] text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                {fig.description}
              </p>
            </div>

            <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-blue-400 font-mono">
              <span>Inspeccionar</span>
              <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
