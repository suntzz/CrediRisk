// Inferencia del modelo CrediRisk v2 dentro del navegador.
//
// final = 0,85 · (0,90 árbol + 0,10 redes, con score) + 0,15 · (0,90 árbol + 0,10 redes, sin score)
// Después: calibración isotónica, corrección a la mora real y umbral por costo.
// Replica src/model_v2.py, src/cv_candidates.py (add_ratios, RawFrame, PreprocessorV2)
// y src/predict_v2.py. La paridad con Python se comprueba con frontend/scripts/paridad_v2.mjs.

type Activation = 'relu' | 'linear' | 'sigmoid';
type Layer =
  | { type: 'Dense'; activation: Activation; W: number[][]; b: number[] }
  | { type: 'LeakyReLU'; negative_slope: number };

// [isLeaf, featureIdx, threshold, left, right, missingGoLeft, value, isCategorical, bitset(8 × uint32) | 0]
type Node = [number, number, number | null, number, number, number, number | null, number, number[] | 0];

interface HgbSpec {
  features: string[];
  categories: Record<string, string[]>;
  baseline: number;
  trees: Node[][];
}

interface PreSpec {
  num: string[];
  flag: string[];
  log: string[];
  lo: Record<string, number | null>;
  hi: Record<string, number | null>;
  median: Record<string, number | null>;
  dummy_cols: string[];
  mean: number[];
  scale: number[];
}

export interface ModelBundleV2 {
  version: 'v2';
  input_cols: string[];
  cat_cols: string[];
  rare_to_otro: Record<string, string[]>;
  weights: { hgb_con_score: number; hgb_sin_score: number; con_score: number };
  hgb: HgbSpec[];
  hgb_sin_score: HgbSpec[];
  pre_redes: PreSpec;
  pre_redes_sin_score: PreSpec;
  redes: Layer[][];
  redes_sin_score: Layer[][];
  calibrador: { x: number[]; y: number[] };
  politica: {
    productos_permitidos: string[];
    productos_bloqueados: string[];
    mora_real: number;
    proporcion_aptos: number;
    costo_por_defecto: number;
    umbrales: Record<string, Record<string, number>>;
  };
}

type Value = number | string | null;
type Row = Record<string, Value>;

const toNum = (v: unknown): number => {
  if (v === null || v === undefined || v === '') return NaN;
  const n = Number(v);
  return Number.isFinite(n) ? n : NaN;
};
const finite = (v: number): number => (Number.isFinite(v) ? v : NaN);
const positive = (v: number): number => (v > 0 ? v : NaN);

/** Razones de add_ratios(): solo columnas del dataset, ninguna usa el score. */
export function addRatios(input: Record<string, unknown>, inputCols: string[], catCols: string[]): Row {
  const row: Row = {};
  const cats = new Set(catCols);
  let vacios = 0;
  for (const c of inputCols) {
    if (cats.has(c)) {
      const v = input[c];
      const s = v === null || v === undefined || v === '' ? null : String(v);
      row[c] = s;
      if (s === null) vacios++;
    } else {
      const n = toNum(input[c]);
      row[c] = n;
      if (Number.isNaN(n)) vacios++;
    }
  }
  const g = (c: string) => row[c] as number;
  const ing = positive(g('ingreso_mensual'));
  const cuota = positive(g('cuota_estimada'));
  const monto = positive(g('monto_solicitado'));
  const personas = Number.isNaN(g('personas_a_cargo')) ? 0 : g('personas_a_cargo');
  row.r_monto_ingreso = finite(g('monto_solicitado') / ing);
  row.r_cuota_ingreso = finite(g('cuota_estimada') / ing);
  row.r_saldo_ingreso = finite(g('saldo_total_creditos') / ing);
  row.r_obligaciones_ingreso = finite(g('obligaciones_mensuales') / ing);
  row.r_monto_cuota = finite(g('monto_solicitado') / cuota);
  row.r_costo_total = finite((g('cuota_estimada') * g('plazo_meses')) / monto);
  row.r_saldo_monto = finite(g('saldo_total_creditos') / monto);
  row.r_mora_por_credito = finite(g('numero_cuotas_mora') / (g('numero_creditos_activos') + 1));
  row.r_creditos_por_anio = finite(g('numero_creditos_activos') / (g('antiguedad_cliente_anios') + 1));
  row.r_ingreso_por_persona = finite(g('ingreso_mensual') / (personas + 1));
  row.edad_inicio_laboral = finite(g('edad') - g('antiguedad_laboral_anios'));
  row.r_antiguedad_edad = finite(g('antiguedad_laboral_anios') / g('edad'));
  row.n_vacios = vacios;
  return row;
}

function inBitset(bits: number[], code: number): boolean {
  return ((bits[code >>> 5] >>> (code & 31)) & 1) === 1;
}

/** HistGradientBoosting con categorías nativas: devuelve P(apto). */
function hgbProba(row: Row, m: HgbSpec): number {
  const x = m.features.map((f) => {
    const cats = m.categories[f];
    if (cats) {
      const v = row[f];
      const i = v === null ? -1 : cats.indexOf(String(v)); // categoría no vista -> vacío
      return i < 0 ? NaN : i;
    }
    return row[f] as number;
  });
  let raw = m.baseline;
  for (const tree of m.trees) {
    let i = 0;
    for (;;) {
      const [leaf, f, thr, left, right, missLeft, value, isCat, bits] = tree[i];
      if (leaf === 1) {
        raw += value ?? 0;
        break;
      }
      const v = x[f];
      let goLeft: boolean;
      if (Number.isNaN(v)) goLeft = missLeft === 1;
      else if (isCat === 1) goLeft = inBitset(bits as number[], v);
      else goLeft = v <= (thr as number);
      i = goLeft ? left : right;
    }
  }
  return 1 / (1 + Math.exp(-raw));
}

/** PreprocessorV2: recorte, logaritmo, mediana en la misma escala, banderas de vacío, one-hot y escalado. */
function preprocess(row: Row, p: PreSpec, catCols: string[], rare: Record<string, string[]>): number[] {
  const logSet = new Set(p.log);
  const nums = p.num.map((c) => {
    let v = row[c] as number;
    if (Number.isNaN(v)) return p.median[c] ?? 0;
    const lo = p.lo[c];
    const hi = p.hi[c];
    if (lo !== null && lo !== undefined && v < lo) v = lo;
    if (hi !== null && hi !== undefined && v > hi) v = hi;
    if (logSet.has(c)) v = Math.sign(v) * Math.log1p(Math.abs(v));
    return v;
  });
  const flags = p.flag.map((c) => (Number.isNaN(row[c] as number) ? 1 : 0));
  const catVals: Record<string, string | null> = {};
  for (const c of catCols) {
    const v = row[c] as string | null;
    catVals[c] = v !== null && rare[c]?.includes(v) ? 'Otro' : v;
  }
  const dummies = p.dummy_cols.map((d) => {
    const col = catCols.find((c) => d.startsWith(`${c}_`));
    return col && catVals[col] === d.slice(col.length + 1) ? 1 : 0;
  });
  return [...nums, ...flags, ...dummies].map((v, i) => (v - p.mean[i]) / p.scale[i]);
}

function forward(x: number[], layers: Layer[]): number {
  let a = x;
  for (const layer of layers) {
    if (layer.type === 'Dense') {
      const out = new Array<number>(layer.b.length);
      for (let j = 0; j < layer.b.length; j++) {
        let s = layer.b[j];
        for (let i = 0; i < a.length; i++) s += a[i] * layer.W[i][j];
        out[j] = layer.activation === 'relu' ? Math.max(0, s) : layer.activation === 'sigmoid' ? 1 / (1 + Math.exp(-s)) : s;
      }
      a = out;
    } else {
      const k = layer.negative_slope;
      a = a.map((v) => (v > 0 ? v : k * v));
    }
  }
  return a[0];
}

const mean = (xs: number[]) => xs.reduce((s, v) => s + v, 0) / xs.length;

/** Interpolación lineal con recorte en los extremos, como IsotonicRegression.predict. */
function isotonic(p: number, cal: { x: number[]; y: number[] }): number {
  const { x, y } = cal;
  if (p <= x[0]) return y[0];
  if (p >= x[x.length - 1]) return y[y.length - 1];
  let lo = 0;
  let hi = x.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (x[mid] <= p) lo = mid;
    else hi = mid;
  }
  const t = x[hi] === x[lo] ? 0 : (p - x[lo]) / (x[hi] - x[lo]);
  return y[lo] + t * (y[hi] - y[lo]);
}

export interface ComponentesV2 {
  hgb: number;
  hgb_sin_score: number;
  redes: number;
  redes_sin_score: number;
}

export interface PrediccionV2 {
  componentes: ComponentesV2;
  puntaje: number; // salida del modelo (escala del entrenamiento 50/50)
  puntajeCalibrado: number;
  probAptoReal: number; // corregida a la mora real
  umbral: number | null;
  costo: number;
  decision: 'APTO' | 'NO APTO' | 'BLOQUEADO';
}

export function predictV2(input: Record<string, unknown>, b: ModelBundleV2, costo?: number): PrediccionV2 {
  const row = addRatios(input, b.input_cols, b.cat_cols);
  const comp: ComponentesV2 = {
    hgb: mean(b.hgb.map((m) => hgbProba(row, m))),
    hgb_sin_score: mean(b.hgb_sin_score.map((m) => hgbProba(row, m))),
    redes: mean(b.redes.map((n) => forward(preprocess(row, b.pre_redes, b.cat_cols, b.rare_to_otro), n))),
    redes_sin_score: mean(
      b.redes_sin_score.map((n) => forward(preprocess(row, b.pre_redes_sin_score, b.cat_cols, b.rare_to_otro), n)),
    ),
  };
  const w = b.weights;
  const con = w.hgb_con_score * comp.hgb + (1 - w.hgb_con_score) * comp.redes;
  const sin = w.hgb_sin_score * comp.hgb_sin_score + (1 - w.hgb_sin_score) * comp.redes_sin_score;
  const puntaje = w.con_score * con + (1 - w.con_score) * sin;

  const pol = b.politica;
  const pc = isotonic(puntaje, b.calibrador);
  const pi = pol.proporcion_aptos;
  const factor = ((1 - pol.mora_real) / pol.mora_real) / (pi / (1 - pi));
  const probAptoReal = pc >= 1 ? 1 : pc <= 0 ? 0 : (pc / (1 - pc)) * factor / (1 + (pc / (1 - pc)) * factor);

  const c = costo ?? pol.costo_por_defecto;
  const producto = String(input.linea_negocio ?? '');
  if (!pol.productos_permitidos.includes(producto)) {
    return { componentes: comp, puntaje, puntajeCalibrado: pc, probAptoReal, umbral: null, costo: c, decision: 'BLOQUEADO' };
  }
  const umbral = pol.umbrales[producto][String(c)];
  return {
    componentes: comp, puntaje, puntajeCalibrado: pc, probAptoReal, umbral, costo: c,
    decision: probAptoReal >= umbral ? 'APTO' : 'NO APTO',
  };
}
