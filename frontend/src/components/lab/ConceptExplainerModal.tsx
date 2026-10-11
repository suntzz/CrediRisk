import React, { useState, useEffect, useRef } from 'react';
import { 
  X, 
  HelpCircle, 
  BookOpen, 
  Sparkles, 
  Cpu, 
  AlertTriangle, 
  CheckCircle2, 
  Lightbulb, 
  Sliders
} from 'lucide-react';
import { CONCEPTS_REPOSITORY, type ConceptDefinition } from './labData';

interface ConceptExplainerModalProps {
  conceptKey: string | null;
  onClose: () => void;
}

export const ConceptExplainerModal: React.FC<ConceptExplainerModalProps> = ({
  conceptKey,
  onClose,
}) => {
  const [depthLevel, setDepthLevel] = useState<'short' | 'how' | 'technical'>('short');
  const modalRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const concept: ConceptDefinition | undefined = conceptKey 
    ? CONCEPTS_REPOSITORY[conceptKey] 
    : undefined;

  // Cerrar con Escape y atrapar foco básico
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (conceptKey) {
      document.addEventListener('keydown', handleKeyDown);
      // Autoenfoque en el botón cerrar
      setTimeout(() => closeButtonRef.current?.focus(), 50);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [conceptKey, onClose]);

  // Bloquear scroll de fondo cuando el modal esté abierto
  useEffect(() => {
    if (conceptKey) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [conceptKey]);

  if (!concept) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-concept-title"
      onClick={onClose}
    >
      <div 
        ref={modalRef}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl bg-[#0B1220] border border-white/10 rounded-2xl shadow-[0_25px_60px_rgba(0,0,0,0.8)] overflow-hidden flex flex-col max-h-[90vh] text-slate-100 animate-in zoom-in-95 duration-200"
      >
        {/* Cabecera del Modal */}
        <div className="p-5 sm:p-6 border-b border-white/10 bg-slate-950/60 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
                {concept.badge}
              </span>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                {concept.category}
              </span>
            </div>
            <h2 id="modal-concept-title" className="text-xl sm:text-2xl font-display font-extrabold text-white tracking-tight">
              {concept.title}
            </h2>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Cerrar ventana de explicación"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Selector de Nivel de Profundidad (3 Niveles Pedagógicos) */}
        <div className="px-5 sm:px-6 pt-4 pb-2 border-b border-white/5 bg-slate-900/40">
          <div className="text-[11px] font-mono text-slate-400 mb-2 flex items-center space-x-1.5">
            <Sliders className="w-3.5 h-3.5 text-blue-400" />
            <span>Elige el nivel de detalle que deseas explorar:</span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => setDepthLevel('short')}
              className={`py-2 px-2.5 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all ${
                depthLevel === 'short'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white/5 hover:bg-white/10 text-slate-300'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">En pocas palabras</span>
            </button>

            <button
              type="button"
              onClick={() => setDepthLevel('how')}
              className={`py-2 px-2.5 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all ${
                depthLevel === 'how'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white/5 hover:bg-white/10 text-slate-300'
              }`}
            >
              <Lightbulb className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">Cómo funciona</span>
            </button>

            <button
              type="button"
              onClick={() => setDepthLevel('technical')}
              className={`py-2 px-2.5 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all ${
                depthLevel === 'technical'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white/5 hover:bg-white/10 text-slate-300'
              }`}
            >
              <Cpu className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">Detalle técnico</span>
            </button>
          </div>
        </div>

        {/* Contenido Dinámico según Nivel de Profundidad */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-5 text-xs sm:text-sm">
          {/* Tarjeta de Respuesta según Nivel */}
          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-slate-200 leading-relaxed">
            {depthLevel === 'short' && (
              <div>
                <strong className="block text-blue-300 font-sans mb-1 text-xs uppercase tracking-wider font-bold">
                  Resumen Intuitivo:
                </strong>
                <p>{concept.short}</p>
              </div>
            )}
            {depthLevel === 'how' && (
              <div>
                <strong className="block text-blue-300 font-sans mb-1 text-xs uppercase tracking-wider font-bold">
                  Funcionamiento e Intuición Práctica:
                </strong>
                <p>{concept.howItWorks}</p>
              </div>
            )}
            {depthLevel === 'technical' && (
              <div>
                <strong className="block text-blue-300 font-sans mb-1 text-xs uppercase tracking-wider font-bold">
                  Formulación Matemática y Rigor Estadístico:
                </strong>
                <p className="font-mono text-xs text-slate-300 leading-relaxed">{concept.technical}</p>
              </div>
            )}
          </div>

          {/* Bloques Pedagógicos Estructurados de Alto Valor */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
            {/* ¿Qué es? */}
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
              <span className="font-bold text-slate-200 flex items-center space-x-1.5">
                <BookOpen className="w-3.5 h-3.5 text-blue-400" />
                <span>¿Qué es?</span>
              </span>
              <p className="text-slate-400 leading-relaxed">{concept.whatIs}</p>
            </div>

            {/* ¿Para qué sirve? */}
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
              <span className="font-bold text-slate-200 flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>¿Para qué sirve?</span>
              </span>
              <p className="text-slate-400 leading-relaxed">{concept.whyItMatters}</p>
            </div>

            {/* ¿Cómo se interpreta? */}
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
              <span className="font-bold text-slate-200 flex items-center space-x-1.5">
                <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                <span>¿Cómo se interpreta?</span>
              </span>
              <p className="text-slate-400 leading-relaxed">{concept.howToRead}</p>
            </div>

            {/* ¿Qué significa en CrediRisk? */}
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
              <span className="font-bold text-slate-200 flex items-center space-x-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                <span>En CrediRisk</span>
              </span>
              <p className="text-slate-400 leading-relaxed">{concept.meaningInCrediRisk}</p>
            </div>
          </div>

          {/* Advertencia Metodológica: ¿Qué NO significa? */}
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-200/90 text-xs flex items-start space-x-3">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <strong className="block text-amber-300 font-semibold mb-0.5">
                ¿Qué NO significa? (Advertencia Metodológica)
              </strong>
              <p className="leading-relaxed">{concept.whatItDoesNotMean}</p>
            </div>
          </div>
        </div>

        {/* Pie del Modal */}
        <div className="p-4 border-t border-white/10 bg-slate-950/70 flex items-center justify-between text-xs text-slate-400">
          <span>Fuente: README.md y reportes experimentales verificados.</span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white font-medium transition-colors"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
};

export interface ConceptTriggerProps {
  conceptKey: string;
  label?: string;
  onOpenExplainer: (key: string) => void;
  className?: string;
}

export const ConceptTrigger: React.FC<ConceptTriggerProps> = ({
  conceptKey,
  label,
  onOpenExplainer,
  className = '',
}) => {
  const concept = CONCEPTS_REPOSITORY[conceptKey];
  const displayLabel = label || concept?.title || conceptKey;

  return (
    <button
      type="button"
      onClick={() => onOpenExplainer(conceptKey)}
      className={`inline-flex items-center space-x-1 text-slate-300 hover:text-white group cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded px-1 -mx-1 py-0.5 transition-colors ${className}`}
      title={`Haz clic para ver la explicación detallada de ${displayLabel}`}
      aria-label={`Explicación pedagógica de ${displayLabel}`}
    >
      <span className="underline decoration-blue-500/50 decoration-dotted underline-offset-4 group-hover:decoration-blue-400 group-hover:text-blue-300 transition-colors">
        {displayLabel}
      </span>
      <HelpCircle className="w-3 h-3 text-blue-400/70 group-hover:text-blue-300 shrink-0 transition-colors" />
    </button>
  );
};
