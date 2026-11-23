import { useEffect, useState } from 'react';
import { fetchComparacionV2, type ComparacionV2 } from '../../services/api';

// Comparación del modelo viejo (producción hasta nov-2026) con el modelo v2 que hoy predice en la web.
// Las cifras salen de reports/ vía scripts/export_static_api_v2.py -> api-static/comparacion_v2.json.

const fmt = (v: number, f: string) => (f === 'pct_menor' ? `${v.toFixed(0)} %` : v.toFixed(4)).replace('.', ',');

export default function ModelV2ComparisonView() {
  const [data, setData] = useState<ComparacionV2 | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchComparacionV2().then(setData).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="text-xs text-rose-300">{error}</p>;
  if (!data) return <div className="h-40 rounded-2xl border border-white/10 bg-[#0B1220] animate-pulse" />;

  const auc = data.resultados[0];
  const m = data.mejora_cv;
  const mil = (v: number) => `${v >= 0 ? '+' : '−'}${Math.abs(v * 1000).toFixed(1).replace('.', ',')}`;

  return (
    <section className="bg-[#0B1220] p-6 sm:p-8 rounded-2xl border border-white/10 shadow-lg space-y-6">
      <div className="space-y-2 max-w-3xl">
        <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-blue-400 block">
          Modelo en uso: CrediRisk v2
        </span>
        <h2 className="text-xl sm:text-2xl font-display font-extrabold text-white tracking-tight">
          Modelo viejo frente a modelo nuevo
        </h2>
        <p className="text-base sm:text-lg text-slate-200 leading-relaxed">
          El AUC pasó de <span className="text-slate-400">{fmt(auc.viejo, 'auc')}</span> a{' '}
          <strong className="text-blue-300">{fmt(auc.nuevo, 'auc')}</strong>: {mil(m.diff)} milésimas, intervalo del 95 %{' '}
          {mil(m.ci_low)} a {mil(m.ci_high)}. La meta era 0,78; con estas 23 columnas el techo está entre 0,76 y 0,77.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="overflow-x-auto rounded-xl border border-white/10">
          <table className="w-full min-w-[420px] text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <th className="py-2.5 px-3 font-medium">Resultado</th>
                <th className="py-2.5 px-3 font-medium">Viejo</th>
                <th className="py-2.5 px-3 font-medium">Nuevo</th>
              </tr>
            </thead>
            <tbody>
              {data.resultados.map((r) => (
                <tr key={r.nombre} className="border-b border-white/5 last:border-0">
                  <td className="py-2.5 px-3 text-slate-200">{r.nombre}</td>
                  <td className="py-2.5 px-3 font-mono text-slate-400">{fmt(r.viejo, r.formato)}</td>
                  <td className="py-2.5 px-3 font-mono font-bold text-blue-300">{fmt(r.nuevo, r.formato)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/10">
          <table className="w-full min-w-[420px] text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <th className="py-2.5 px-3 font-medium">Qué cambió</th>
                <th className="py-2.5 px-3 font-medium">Viejo</th>
                <th className="py-2.5 px-3 font-medium">Nuevo</th>
              </tr>
            </thead>
            <tbody>
              {data.cambios.map(([k, a, b]) => (
                <tr key={k} className="border-b border-white/5 last:border-0 align-top">
                  <td className="py-2.5 px-3 text-slate-200">{k}</td>
                  <td className="py-2.5 px-3 text-slate-400">{a}</td>
                  <td className="py-2.5 px-3 text-slate-100">{b}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed max-w-3xl">
        Resultados en validación cruzada sobre 42.202 clientes, salvo la prueba apartada (7.448, mirada una sola vez). Las
        pestañas siguientes documentan el historial de experimentos del modelo anterior.
      </p>
    </section>
  );
}
