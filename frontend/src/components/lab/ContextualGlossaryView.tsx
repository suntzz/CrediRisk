import React, { useState, useMemo } from 'react';
import { Search, BookOpen, ChevronDown, ChevronUp, Cpu, Lightbulb, Tag } from 'lucide-react';
import { GLOSSARY_ENTRIES } from './labData';

export const ContextualGlossaryView: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('Todas');
  const [expandedTerms, setExpandedTerms] = useState<Record<string, boolean>>({});

  const categories = ['Todas', 'Métricas', 'Arquitectura', 'Preprocesamiento', 'Riesgo Financiero', 'Metodología'];

  const filteredEntries = useMemo(() => {
    return GLOSSARY_ENTRIES.filter((entry) => {
      const matchesCat = selectedCategory === 'Todas' || entry.category === selectedCategory;
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch = !q || (
        entry.term.toLowerCase().includes(q) ||
        entry.simpleExplanation.toLowerCase().includes(q) ||
        entry.technicalExplanation.toLowerCase().includes(q) ||
        entry.crediriskExample.toLowerCase().includes(q)
      );
      return matchesCat && matchesSearch;
    });
  }, [searchQuery, selectedCategory]);

  const toggleExpand = (term: string) => {
    setExpandedTerms((prev) => ({
      ...prev,
      [term]: !prev[term],
    }));
  };

  return (
    <div className="space-y-6">
      {/* Encabezado del Glosario */}
      <div className="bg-[#0B1220] p-6 sm:p-7 rounded-2xl border border-white/10 shadow-lg space-y-4">
        <div>
          <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-blue-400 block mb-1">
            Diccionario Pedagógico Interactivo
          </span>
          <h2 className="text-xl sm:text-2xl font-display font-bold text-white tracking-tight">
            Glosario Técnico y Conceptual de CrediRisk
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-slate-400 leading-relaxed max-w-3xl">
            Explicaciones pedagógicas, rigurosas y conectadas directamente con el modelo de riesgo crediticio.
            Diseñado para que cualquier persona pueda comprender los conceptos y cualquier analista pueda profundizar.
          </p>
        </div>

        {/* Barra de Búsqueda y Filtros */}
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          {/* Input de Búsqueda */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar término, fórmula o concepto (ej. ROC-AUC, Brier, Dropout, L2)..."
              className="w-full bg-slate-950/80 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500 hover:text-white"
              >
                ✕
              </button>
            )}
          </div>

          {/* Chips de Categorías */}
          <div className="flex items-center space-x-1 overflow-x-auto no-scrollbar py-0.5">
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  selectedCategory === cat
                    ? 'bg-blue-600 text-white shadow'
                    : 'bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white border border-white/5'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Conteo de Resultados */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1 font-mono">
        <span>Mostrando {filteredEntries.length} de {GLOSSARY_ENTRIES.length} términos</span>
        <span>Haz clic en cualquier tarjeta para ver la explicación completa</span>
      </div>

      {/* Grid de Términos */}
      {filteredEntries.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredEntries.map((item) => {
            const isExpanded = !!expandedTerms[item.term];

            return (
              <div
                key={item.term}
                className={`p-5 rounded-2xl border transition-all duration-200 bg-[#0B1220] ${
                  isExpanded
                    ? 'border-blue-500/50 shadow-[0_10px_30px_rgba(37,99,235,0.15)] ring-1 ring-blue-500/20'
                    : 'border-white/10 hover:border-white/20'
                }`}
              >
                {/* Cabecera del Término */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 inline-block mb-1.5">
                      {item.category}
                    </span>
                    <h3 className="text-base font-display font-bold text-white tracking-tight">
                      {item.term}
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => toggleExpand(item.term)}
                    className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                    aria-label={`Alternar detalles de ${item.term}`}
                  >
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-blue-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                </div>

                {/* Explicación Sencilla (Siempre Visible) */}
                <div className="text-xs text-slate-300 leading-relaxed mb-3">
                  <p>{item.simpleExplanation}</p>
                </div>

                {/* Detalles Expandibles */}
                {isExpanded && (
                  <div className="space-y-3 pt-3 border-t border-white/10 text-xs animate-in fade-in duration-150">
                    {/* Detalle Técnico */}
                    <div className="p-3 rounded-xl bg-white/5 space-y-1">
                      <strong className="text-slate-200 font-sans flex items-center space-x-1.5 text-[11px]">
                        <Cpu className="w-3.5 h-3.5 text-blue-400" />
                        <span>Detalle Técnico y Matemático:</span>
                      </strong>
                      <p className="text-slate-300 font-mono text-[11px] leading-relaxed">
                        {item.technicalExplanation}
                      </p>
                    </div>

                    {/* Ejemplo en CrediRisk */}
                    <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 space-y-1">
                      <strong className="text-blue-300 font-sans flex items-center space-x-1.5 text-[11px]">
                        <Lightbulb className="w-3.5 h-3.5 text-blue-400" />
                        <span>En CrediRisk:</span>
                      </strong>
                      <p className="text-slate-200 text-[11px] leading-relaxed">
                        {item.crediriskExample}
                      </p>
                    </div>

                    {/* Conceptos Relacionados */}
                    {item.relatedConcepts.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px] font-mono text-slate-400">
                        <Tag className="w-3 h-3 text-slate-500" />
                        <span>Relacionado:</span>
                        {item.relatedConcepts.map((c) => (
                          <span
                            key={c}
                            className="px-2 py-0.5 rounded bg-white/5 border border-white/5 text-slate-300"
                          >
                            {c}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Botón rápido para expandir */}
                <button
                  type="button"
                  onClick={() => toggleExpand(item.term)}
                  className="mt-2 text-[11px] font-mono text-blue-400 hover:text-blue-300 flex items-center space-x-1"
                >
                  <span>{isExpanded ? 'Mostrar menos' : 'Ver explicación técnica y ejemplo'}</span>
                  {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-12 text-center bg-[#0B1220] rounded-2xl border border-white/10 space-y-3">
          <BookOpen className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-sm text-slate-400">
            No se encontraron términos que coincidan con «<strong>{searchQuery}</strong>».
          </p>
          <button
            type="button"
            onClick={() => {
              setSearchQuery('');
              setSelectedCategory('Todas');
            }}
            className="text-xs text-blue-400 hover:underline font-mono"
          >
            Limpiar filtros de búsqueda
          </button>
        </div>
      )}
    </div>
  );
};
