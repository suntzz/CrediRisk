// Compara la inferencia del navegador (src/services/modelV2.ts) con la de Python.
// 1) python scripts/export_static_api_v2.py --paridad 400
// 2) node --experimental-strip-types scripts/paridad_v2.mjs   (desde frontend/)
import { readFileSync } from 'node:fs';
import { predictV2 } from '../src/services/modelV2.ts';

const bundle = JSON.parse(readFileSync(new URL('../public/api-static/model_bundle_v2.json', import.meta.url)));
const ref = JSON.parse(readFileSync(new URL('./paridad_v2_ref.json', import.meta.url)));

const err = { hgb: 0, hgb_sin_score: 0, redes: 0, redes_sin_score: 0, p: 0, p_cal: 0 };
ref.filas.forEach((fila, i) => {
  const r = predictV2(fila, bundle);
  for (const k of ['hgb', 'hgb_sin_score', 'redes', 'redes_sin_score']) {
    err[k] = Math.max(err[k], Math.abs(r.componentes[k] - ref[k][i]));
  }
  err.p = Math.max(err.p, Math.abs(r.puntaje - ref.p[i]));
  err.p_cal = Math.max(err.p_cal, Math.abs(r.puntajeCalibrado - ref.p_cal[i]));
});
console.log(`filas: ${ref.filas.length}`);
for (const [k, v] of Object.entries(err)) console.log(`${k.padEnd(16)} error máximo ${v.toExponential(2)}`);
const ok = err.p < 1e-4;
console.log(ok ? 'PARIDAD OK' : 'PARIDAD FALLA');
process.exit(ok ? 0 : 1);
