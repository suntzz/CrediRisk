"""Genera el documento técnico de la mejora de AUC de CrediRisk desde los CSV reales."""
import csv, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "reports"
A = ROOT / "artifacts/v2"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/mejora-auc-v2.html"


def rows(name):
    with open(R / f"{name}.csv", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def f(x):
    return float(x) if x not in ("", None) else None


def n(x, d=4):
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, d=0):
    return n(x, d) + " %"


def mil(x, d=1):  # milésimas de AUC
    return ("+" if x >= 0 else "−") + n(abs(x) * 1000, d)


res = {r["metrica"]: (f(r["antes"]), f(r["despues"])) for r in rows("v2_resumen")}
casc = rows("v2_cascada")
comp = {r["comparacion"]: r for r in rows("v2_comparaciones")}
imp = rows("v2_imputacion")
lc = rows("v2_curva_aprendizaje")
cp = rows("v2_curva_peso")
bp = [r for r in rows("v2_busqueda_pesos") if r["modelo"] == "con_score"]
test = {r["segmento"]: r for r in rows("final_v2_test")}
st = rows("stress_resumen")
folds = rows("stress_pliegues")
cal = {r["modelo"]: f(r["ece"]) for r in rows("stress_calibracion")}
umb = rows("umbrales_por_costo")
sub = rows("stress_subgrupos")
man = json.loads((A / "manifest.json").read_text())

auc0, auc1 = res["auc_cv"]
dep0, dep1 = res["dependencia_pct"]
pr0, pr1 = res["auc_prueba"]
ci_lo, ci_hi = res["auc_cv_ci_low"][1], res["auc_cv_ci_high"][1]
vac0, vac1 = res["auc_score_vacio"]

# ---------- utilidades SVG ----------
def sc(v, a, b, p, q):
    return p + (v - a) / (b - a) * (q - p)


def T(x, y, s, cls="lb", anchor="start", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}" {extra}>{s}</text>'


def svg(w, h, body, label):
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{label}" '
            f'preserveAspectRatio="xMinYMin meet">{body}</svg>')


ETQ = {"Peso árbol/redes 0.90/0.10": "Peso árbol / redes: 0,90 / 0,10", "Mezcla con modelo sin score (peso 0.85)": "Mezcla con modelo sin score (85 / 15)"}

# 1) Cascada de aportes -------------------------------------------------------
def chart_cascada():
    steps = [r for r in casc if r["aporte"]]
    W, rowh, top, left, right = 760, 46, 34, 300, 80
    H = top + rowh * len(steps) + 34
    x0, x1 = -0.0004, 0.0018
    X = lambda v: sc(v, x0, x1, left, W - right)
    b = []
    for t in [-0.0002, 0, 0.0005, 0.001, 0.0015]:
        b.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{top-10}" y2="{H-26}" class="{"ax0" if t == 0 else "grid"}"/>')
        b.append(T(X(t), H - 8, mil(t, 1) if t else "0", "tick", "middle"))
    b.append(T(left, 14, "Aporte en milésimas de AUC e intervalo del 95 %", "cap"))
    b.append(T(W - 4, 14, "AUC", "cap", "end"))
    for i, r in enumerate(steps):
        y = top + i * rowh + rowh / 2
        a, lo, hi = f(r["aporte"]), f(r["ci_low"]), f(r["ci_high"])
        sig = r["significativo"] == "True"
        c = "acc" if sig else "mute"
        x_a, x_b = sorted([X(0), X(a)])
        b.append(T(left - 14, y + 5, ETQ.get(r["etiqueta"], r["etiqueta"]), "rowl" + ("" if sig else " dim"), "end"))
        b.append(f'<rect x="{x_a:.1f}" y="{y-11:.1f}" width="{max(x_b-x_a,1.5):.1f}" height="22" rx="3" class="{c}"/>')
        b.append(f'<line x1="{X(lo):.1f}" x2="{X(hi):.1f}" y1="{y:.1f}" y2="{y:.1f}" class="ci"/>')
        for xx in (X(lo), X(hi)):
            b.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{y-6:.1f}" y2="{y+6:.1f}" class="ci"/>')
        b.append(T(W - 4, y + 5, n(f(r["auc"]), 4), "num" + ("" if sig else " dim"), "end"))
    return svg(W, H, "".join(b), "Cascada de aportes al AUC")


# 2) Error de imputación ------------------------------------------------------
def chart_imputacion():
    vs = imp[:4]
    W, rowh, top, left, right = 760, 64, 40, 230, 40
    H = top + rowh * len(vs) + 30
    x0, x1 = -1, 17
    X = lambda v: sc(v, x0, x1, left, W - right)
    b = [T(left, 14, "Escala logarítmica, log(1 + x), que es la que ve la red", "cap")]
    for t in range(0, 17, 4):
        b.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{top-12}" y2="{H-24}" class="grid"/>')
        b.append(T(X(t), H - 6, str(t), "tick", "middle"))
    for i, r in enumerate(vs):
        y = top + i * rowh + rowh / 2 - 4
        p1, p99, med, wrong = f(r["p1_log"]), f(r["p99_log"]), f(r["mediana_correcta_log"]), f(r["valor_que_recibia"])
        name = r["variable"].replace("_", " ")
        b.append(T(left - 14, y + 1, name, "rowl", "end"))
        b.append(T(left - 14, y + 18, f'{n(f(r["pct_vacios"]),1)} % vacíos', "tick", "end"))
        b.append(f'<rect x="{X(p1):.1f}" y="{y-7:.1f}" width="{X(p99)-X(p1):.1f}" height="14" rx="7" class="band"/>')
        b.append(f'<circle cx="{X(med):.1f}" cy="{y:.1f}" r="6" class="acc"/>')
        if wrong > x1:
            xe = W - right
            b.append(f'<line x1="{X(med)+8:.1f}" x2="{xe:.1f}" y1="{y:.1f}" y2="{y:.1f}" class="bad" marker-end="url(#ar)"/>')
            b.append(T(xe, y - 12, f"recibía {n(wrong, 0 if wrong > 100 else 1)}", "badt", "end"))
        else:
            b.append(f'<circle cx="{X(wrong):.1f}" cy="{y:.1f}" r="6" class="badc"/>')
            b.append(T(X(wrong) + 10, y - 10, f"recibía {n(wrong, 0 if wrong > 100 else 1)}", "badt"))
    defs = '<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="badf"/></marker></defs>'
    return svg(W, H, defs + "".join(b), "Valor que recibía la red frente al rango normal")


# 3) Peso árbol / redes ----------------------------------------------------------
def chart_peso():
    W, H, l, r_, t, bt = 760, 300, 64, 24, 30, 44
    xs = [f(r["peso_hgb"]) for r in bp]; ys = [f(r["auc"]) for r in bp]
    y0, y1 = 0.750, 0.7625
    X = lambda v: sc(v, 0, 1, l, W - r_); Y = lambda v: sc(v, y0, y1, H - bt, t)
    b = [T(l, 14, "AUC del modelo con score según cuánto pesa el árbol frente a las redes", "cap")]
    for v in [0.750, 0.754, 0.758, 0.762]:
        b.append(f'<line x1="{l}" x2="{W-r_}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="grid"/>')
        b.append(T(l - 8, Y(v) + 4, n(v, 3), "tick", "end"))
    for v in [0, 0.25, 0.5, 0.75, 1]:
        b.append(T(X(v), H - bt + 20, f"{int(v*100)} %", "tick", "middle"))
    b.append(T((l + W - r_) / 2, H - 6, "peso del árbol en la mezcla", "tick", "middle"))
    pts = " ".join(f"{X(a):.1f},{Y(c):.1f}" for a, c in zip(xs, ys))
    b.append(f'<polyline points="{pts}" class="line"/>')
    d = {round(a, 2): c for a, c in zip(xs, ys)}
    for w, cls, lab, dy in [(0.0, "mutec", f"solo redes {n(d[0.0],4)}", 18), (0.65, "mutec", f"peso de producción 65 % · {n(d[0.65],4)}", 22), (0.9, "accc", f"elegido 90 % · {n(d[0.9],4)}", -16)]:
        b.append(f'<circle cx="{X(w):.1f}" cy="{Y(d[w]):.1f}" r="6" class="{cls}"/>')
        anc = "start" if w < 0.5 else "end"
        b.append(T(X(w) + (10 if anc == "start" else 0), Y(d[w]) + dy, lab, "ann" + (" acct" if cls == "accc" else ""), anc))
    b.append(T(X(1.0), Y(d[1.0]) + 22, f"solo árbol {n(d[1.0],4)}", "ann", "end"))
    return svg(W, H, "".join(b), "Curva del peso entre árbol y redes")


# 4) AUC vs dependencia ------------------------------------------------------
def chart_tradeoff():
    W, H, l, r_, t, bt = 760, 340, 64, 30, 30, 46
    x0, x1, y0, y1 = 15, 63, 0.738, 0.764
    X = lambda v: sc(v, x0, x1, l, W - r_); Y = lambda v: sc(v, y0, y1, H - bt, t)
    b = [T(l, 14, "Cada punto es una mezcla distinta entre el modelo con score y el modelo sin score", "cap")]
    for v in [0.740, 0.745, 0.750, 0.755, 0.760]:
        b.append(f'<line x1="{l}" x2="{W-r_}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="grid"/>')
        b.append(T(l - 8, Y(v) + 4, n(v, 3), "tick", "end"))
    for v in [20, 30, 40, 50, 60]:
        b.append(T(X(v), H - bt + 20, f"{v} %", "tick", "middle"))
    b.append(T((l + W - r_) / 2, H - 6, "dependencia del score (menos es mejor)", "tick", "middle"))
    # zona de producción
    b.append(f'<line x1="{l}" x2="{W-r_}" y1="{Y(auc0):.1f}" y2="{Y(auc0):.1f}" class="ref"/>')
    b.append(T(l + 6, Y(auc0) + 16, f"AUC de producción {n(auc0,4)}", "ann"))
    pts = [(f(r["dependencia_pct"]), f(r["auc"]), r) for r in cp]
    b.append('<polyline points="' + " ".join(f"{X(a):.1f},{Y(c):.1f}" for a, c, _ in pts) + '" class="line"/>')
    for a, c, r in pts:
        tied = f(r["ci_high"]) >= 0
        cls = "accc" if r["elegido"] == "True" else ("tie" if tied else "dot")
        b.append(f'<circle cx="{X(a):.1f}" cy="{Y(c):.1f}" r="{7 if r["elegido"]=="True" else 4.5}" class="{cls}"/>')
        w = f(r["peso_con_score"])
        pos = {1.0: (0, -14, "middle"), 0.6: (-10, 4, "end"), 0.3: (10, 4, "start")}
        if w in pos:
            dx, dy, an = pos[w]
            b.append(T(X(a) + dx, Y(c) + dy, f'{int(w*100)} % con score', "tick", an))
    ch = [p for p in pts if p[2]["elegido"] == "True"][0]
    b.append(f'<circle cx="{X(dep0):.1f}" cy="{Y(auc0):.1f}" r="7" class="mutec"/>')
    b.append(T(X(dep0), Y(auc0) + 24, f"producción {pct(dep0)}", "ann", "end"))
    b.append(T(X(ch[0]) - 12, Y(ch[1]) - 14, f"elegido: 85 % con score · {pct(ch[0])} · {n(ch[1],4)}", "ann acct", "end"))
    return svg(W, H, "".join(b), "Curva AUC frente a dependencia del score")


# 5) Mancuernas: dónde aguanta ---------------------------------------------------
def chart_dumbbell():
    groups = []
    groups.append(("Producto", [(s["segmento"], f(s["auc_produccion"]), f(s["auc_final"])) for s in sub if s["grupo"] == "Producto"]))
    groups.append(("Edad", [(s["segmento"], f(s["auc_produccion"]), f(s["auc_final"])) for s in sub if s["grupo"] == "Edad"]))
    groups.append(("Contrato", [(s["segmento"], f(s["auc_produccion"]), f(s["auc_final"])) for s in sub if s["grupo"] == "Tipo de contrato"]))
    groups.append(("Pliegue", [(f"Pliegue {r['pliegue']}", f(r["auc_produccion"]), f(r["auc_final"])) for r in folds]))
    tr = {"Joven": "Joven (tercil bajo)", "Media": "Media", "Mayor": "Mayor (tercil alto)", "Working": "Asalariado",
          "Pensioner": "Pensionado", "State servant": "Empleado público", "Commercial associate": "Socio comercial"}
    W, rowh, gap, top, left, right = 760, 26, 22, 30, 200, 70
    nrows = sum(len(g[1]) for g in groups)
    H = top + nrows * rowh + gap * len(groups) + 30
    x0, x1 = 0.72, 0.775
    X = lambda v: sc(v, x0, x1, left, W - right)
    b = [T(left, 14, "AUC por segmento: gris = producción, color = modelo nuevo", "cap"), T(W - 4, 14, "ganancia", "cap", "end")]
    for t in [0.73, 0.74, 0.75, 0.76, 0.77]:
        b.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{top-6}" y2="{H-26}" class="grid"/>')
        b.append(T(X(t), H - 8, n(t, 2), "tick", "middle"))
    y = top
    for gname, items in groups:
        y += gap
        b.append(T(12, y - 6, gname.upper(), "grp"))
        for name, a, c in items:
            yy = y + rowh / 2
            b.append(T(left - 14, yy + 4, tr.get(name, name), "rowl sm", "end"))
            b.append(f'<line x1="{X(a):.1f}" x2="{X(c):.1f}" y1="{yy:.1f}" y2="{yy:.1f}" class="dl"/>')
            b.append(f'<circle cx="{X(a):.1f}" cy="{yy:.1f}" r="5" class="mutec"/>')
            b.append(f'<circle cx="{X(c):.1f}" cy="{yy:.1f}" r="5" class="accc"/>')
            b.append(T(W - 4, yy + 4, mil(c - a, 1), "num sm", "end"))
            y += rowh
    return svg(W, H, "".join(b), "AUC por segmento, producción frente a modelo nuevo")


# 6) Curva de aprendizaje -----------------------------------------------------
def chart_lc():
    W, H, l, r_, t, bt = 760, 280, 64, 140, 30, 46
    xs = [f(r["filas_entrenamiento"]) for r in lc]; ys = [f(r["auc"]) for r in lc]
    x0, x1 = math.log2(6000), math.log2(48000)
    y0, y1 = 0.746, 0.758
    X = lambda v: sc(math.log2(v), x0, x1, l, W - r_); Y = lambda v: sc(v, y0, y1, H - bt, t)
    b = [T(l, 14, "AUC del árbol nuevo entrenado con más o menos filas (misma partición 80/20)", "cap")]
    for v in [0.748, 0.752, 0.756]:
        b.append(f'<line x1="{l}" x2="{W-r_}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="grid"/>')
        b.append(T(l - 8, Y(v) + 4, n(v, 3), "tick", "end"))
    b.append(T((l + W - r_) / 2, H - 6, "filas de entrenamiento (cada paso duplica)", "tick", "middle"))
    b.append('<polyline points="' + " ".join(f"{X(a):.1f},{Y(c):.1f}" for a, c in zip(xs, ys)) + '" class="line"/>')
    for i, (a, c) in enumerate(zip(xs, ys)):
        b.append(f'<circle cx="{X(a):.1f}" cy="{Y(c):.1f}" r="6" class="{"accc" if i == 2 else "dot"}"/>')
        b.append(T(X(a), H - bt + 20, n(a, 0), "tick", "middle"))
        b.append(T(X(a) + 10, Y(c) + 4, n(c, 4), "num sm"))
        if i:
            g = f(lc[i]["ganancia_al_duplicar"])
            mx, my = (X(xs[i - 1]) + X(a)) / 2, (Y(ys[i - 1]) + Y(c)) / 2
            b.append(T(mx + 8, my + 18, f"{mil(g,1)} al duplicar", "ann"))
    b.append(T(X(xs[-1]) + 10, Y(ys[-1]) - 24, "todo lo que hay", "ann acct"))
    return svg(W, H, "".join(b), "Curva de aprendizaje")


# 7) Estrés rápido ----------------------------------------------------------------
def chart_estres():
    W, rowh, top, left, right = 760, 52, 30, 200, 70
    H = top + rowh * len(st) + 30
    X = lambda v: sc(v, 0.5, 0.78, left, W - right)
    lab = {"Normal": "Con todos los datos", "Score ausente": "Sin el score", "Score barajado": "Score barajado entre clientes"}
    b = [T(left, 14, "AUC cuando se daña el score a propósito", "cap")]
    for t in [0.5, 0.6, 0.7]:
        b.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{top-6}" y2="{H-26}" class="grid"/>')
        b.append(T(X(t), H - 8, n(t, 1), "tick", "middle"))
    for i, r in enumerate(st):
        y = top + i * rowh + 8
        a, c = f(r["auc_produccion"]), f(r["auc_final"])
        b.append(T(left - 14, y + 18, lab[r["prueba"]], "rowl", "end"))
        b.append(f'<rect x="{X(0.5):.1f}" y="{y:.1f}" width="{X(a)-X(0.5):.1f}" height="14" rx="2" class="mute"/>')
        b.append(f'<rect x="{X(0.5):.1f}" y="{y+17:.1f}" width="{X(c)-X(0.5):.1f}" height="14" rx="2" class="acc"/>')
        b.append(T(X(a) + 6, y + 12, n(a, 4), "num sm dim"))
        b.append(T(X(c) + 6, y + 29, n(c, 4), "num sm"))
    return svg(W, H, "".join(b), "Pruebas de estrés del score")


# 0) Regla de la meta ------------------------------------------------------------
def chart_meta(W=1000):
    narrow = W < 600
    H, l, r_ = (180 if narrow else 150), 20, 20
    x0, x1 = 0.745, 0.785
    X = lambda v: sc(v, x0, x1, l, W - r_)
    y = 78
    b = []
    for t in [0.75, 0.76, 0.77, 0.78]:
        b.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{y-6}" y2="{y+6}" class="ax0"/>')
        b.append(T(X(t), y + 28, n(t, 2), "tick", "middle"))
    b.append(f'<line x1="{X(x0):.1f}" x2="{X(x1):.1f}" y1="{y}" y2="{y}" class="ax0"/>')
    # techo con estas columnas
    b.append(f'<rect x="{X(0.760):.1f}" y="{y-20}" width="{X(0.770)-X(0.760):.1f}" height="40" rx="4" class="band"/>')
    b.append(T((X(0.760) + X(0.770)) / 2, y + (72 if narrow else 48), "techo con estas 23 columnas", "ann", "middle"))
    b.append(f'<line x1="{X(0.78):.1f}" x2="{X(0.78):.1f}" y1="{y-30}" y2="{y+14}" class="bad"/>')
    b.append(T(X(0.78), y - 38, "meta 0,78", "badt", "middle"))
    b.append(T(X(0.78), y + 48, "pide datos de fuera", "ann", "middle"))
    for v, cls, lab, dy, anc in [(pr0, "mutec", f"prueba antes {n(pr0,4)}", 50, "start" if narrow else "end"), (auc0, "mutec", f"antes {n(auc0,4)}", -28, "middle" if narrow else "end"),
                                 (auc1, "accc", f"ahora {n(auc1,4)}", -28, "start")]:
        b.append(f'<circle cx="{X(v):.1f}" cy="{y}" r="8" class="{cls}"/>')
        b.append(T(X(v) + (-12 if anc == "end" else (0 if anc == "middle" else (-8 if v == pr0 else 12))), y + dy, lab, "ann" + (" acct" if cls == "accc" else ""), anc))
    return svg(W, H, "".join(b), "Dónde quedó el AUC frente a la meta de 0,78")


# ---------- tabla de umbrales ----------
def tabla_umbrales():
    h = ['<table class="tb"><thead><tr><th>Producto</th><th>Costo de un mal crédito</th><th>Aprobar si P(paga) ≥</th><th>Se aprueba</th><th>Mora entre aprobados</th></tr></thead><tbody>']
    for r in umb:
        h.append(f'<tr><td>{r["producto"].replace("Cash loans","Efectivo").replace("Revolving loans","Rotativo")}</td>'
                 f'<td>{r["costo_malo_vs_bueno"]} ×</td>'
                 f'<td>{n(f(r["umbral"]),3)}</td>'
                 f'<td>{pct(f(r["tasa_aprobacion"])*100)} <span class="ci">({n(f(r["tasa_aprobacion_ci_low"])*100,0)}–{n(f(r["tasa_aprobacion_ci_high"])*100,0)})</span></td>'
                 f'<td>{pct(f(r["mora_aprobados"])*100,1)} <span class="ci">({n(f(r["mora_aprobados_ci_low"])*100,1)}–{n(f(r["mora_aprobados_ci_high"])*100,1)})</span></td></tr>')
    h.append("</tbody></table>")
    return "".join(h)


def tabla_config():
    a = {"max_iter": 450, "learning_rate": 0.04, "max_leaf_nodes": 31, "min_samples_leaf": 40, "l2_regularization": 3.0, "max_features": 1.0, "n_iter_no_change": 25}
    bcfg = man["hgb_config"]
    filas = [("Hojas por árbol", "max_leaf_nodes", "árboles más simples, menos sobreajuste"),
             ("Tasa de aprendizaje", "learning_rate", "pasos más cortos, más árboles"),
             ("Mínimo de clientes por hoja", "min_samples_leaf", "no aprende reglas de pocos casos"),
             ("Regularización L2", "l2_regularization", "encoge los valores de las hojas"),
             ("Fracción de variables por división", "max_features", "cada división ve el 60 %: árboles menos parecidos"),
             ("Máximo de árboles", "max_iter", "techo; la parada temprana decide"),
             ("Paciencia de la parada temprana", "n_iter_no_change", "espera más antes de cortar")]
    h = ['<table class="tb cfg"><thead><tr><th>Parámetro</th><th>Antes</th><th>Ahora</th><th>Para qué</th></tr></thead><tbody>']
    for lab, k, why in filas:
        va, vb = a[k], bcfg[k]
        fmt = lambda v: n(v, 2) if isinstance(v, float) and v < 1 else (n(v, 1) if isinstance(v, float) else n(v, 0))
        h.append(f"<tr><td>{lab}</td><td class='old'>{fmt(va)}</td><td class='new'>{fmt(vb)}</td><td>{why}</td></tr>")
    h.append("</tbody></table>")
    return "".join(h)


def tabla_vs():
    sg = {s["segmento"]: s for s in sub if s["grupo"] == "Producto"}
    def par(a, b, d=4, fmt=None):
        fmt = fmt or (lambda v: n(v, d))
        return f"<td class='old'>{fmt(a)}</td><td class='new'>{fmt(b)}</td>"
    def txt(a, b):
        return f"<td class='old'>{a}</td><td class='new'>{b}</td>"
    g = []
    g.append(("Resultados", [
        ("AUC en validación cruzada", par(auc0, auc1)),
        ("AUC en la prueba apartada", par(pr0, pr1)),
        ("AUC en efectivo", par(f(sg["Cash loans"]["auc_produccion"]), f(sg["Cash loans"]["auc_final"]))),
        ("AUC en rotativo", par(f(sg["Revolving loans"]["auc_produccion"]), f(sg["Revolving loans"]["auc_final"]))),
        ("Dependencia del score", par(dep0, dep1, fmt=lambda v: pct(v))),
        ("AUC si falta el score", par(vac0, vac1)),
        ("Error de calibración (ECE)", par(cal["Producción"], cal["Final calibrado"])),
    ]))
    g.append(("Cómo está hecho", [
        ("Arquitectura", txt("árbol + 3 redes", "árbol + 3 redes, con y sin score")),
        ("Peso árbol / redes", txt("0,65 / 0,35, fijado a mano", "0,90 / 0,10, buscado")),
        ("Datos que ve el árbol", txt("imputados, escalados, one-hot", "crudos + 12 razones")),
        ("Árbol", txt("31 hojas, tasa 0,04, 1 semilla", "15 hojas, tasa 0,02, 5 semillas")),
        ("Vacíos en las redes", txt("mediana fuera de escala", "mediana en escala logarítmica")),
        ("Modelo sin score", txt("no", "15 % de la mezcla")),
    ]))
    g.append(("Cómo decide", [
        ("Elección del modelo", txt("con la prueba, más de 15 intentos", "validación cruzada 5 × 3")),
        ("Umbral", txt("exactitud en datos 50/50", "costo, calibrado, mora real 8,07 %")),
        ("Productos", txt("efectivo y rotativo", "efectivo y rotativo; hipotecario bloqueado")),
    ]))
    h = ['<table class="tb vs"><thead><tr><th></th><th>Modelo viejo</th><th>Modelo nuevo</th></tr></thead>']
    for name, items in g:
        h.append(f'<tbody><tr class="gh"><th colspan="3">{name}</th></tr>')
        for lab, cells in items:
            h.append(f"<tr><td>{lab}</td>{cells}</tr>")
        h.append("</tbody>")
    h.append("</table>")
    return "".join(h)


cfin = comp["Final vs producción"]
c_red_fix = comp["Redes: arreglo vs producción"]
c_hyb_fix = [r for r in casc if r["paso"] == "1"][0]
cash, rev = comp["Final vs producción · Cash loans"], comp["Final vs producción · Revolving loans"]
tg = test["GLOBAL"]
tdep = test["Dependencia del score (%)"]
tvac = test["AUC con score ausente"]
wrong_saldo = f(imp[0]["valor_que_recibia"])
ratio_saldo = wrong_saldo / f(imp[0]["p99_log"])

ctx = dict(
    auc0=n(auc0), auc1=n(auc1), dep0=pct(dep0), dep1=pct(dep1), pr0=n(pr0), pr1=n(pr1),
    dmil=mil(auc1 - auc0, 1), ci=f"{mil(ci_lo,1)} a {mil(ci_hi,1)}",
    vac0=n(vac0), vac1=n(vac1),
    vs=tabla_vs(), meta=chart_meta(), meta_cel=chart_meta(460), cascada=chart_cascada(), imputacion=chart_imputacion(), peso=chart_peso(), trade=chart_tradeoff(),
    dumb=chart_dumbbell(), lc=chart_lc(), estres=chart_estres(), umbrales=tabla_umbrales(), cfg=tabla_config(),
    red_fix=mil(f(c_red_fix["diff"])), red_fix_ci=f'{mil(f(c_red_fix["ci_low"]))} a {mil(f(c_red_fix["ci_high"]))}',
    hyb_fix=mil(f(c_hyb_fix["aporte"])), saldo_wrong=n(wrong_saldo, 0), saldo_p99=n(f(imp[0]["p99_log"]), 1),
    saldo_med=n(f(imp[0]["mediana_correcta_log"]), 1), saldo_ratio=n(ratio_saldo, 0), saldo_vac=n(f(imp[0]["pct_vacios"]), 0),
    cash=mil(f(cash["diff"])), cash_ci=f'{mil(f(cash["ci_low"]))} a {mil(f(cash["ci_high"]))}',
    rev=mil(f(rev["diff"])), rev_ci=f'{mil(f(rev["ci_low"]))} a {mil(f(rev["ci_high"]))}',
    t_diff=mil(f(tg["diff"])), t_ci=f'{mil(f(tg["ci_low"]))} a {mil(f(tg["ci_high"]))}', t_n=n(f(tg["n"]), 0),
    tdep0=pct(f(tdep["auc_produccion"])), tdep1=pct(f(tdep["auc_final"])),
    tvac0=n(f(tvac["auc_produccion"])), tvac1=n(f(tvac["auc_final"])),
    ece0=n(cal["Producción"], 4), ece_raw=n(cal["Final sin calibrar"], 4), ece1=n(cal["Final calibrado"], 4),
    hybrid_vs_hgb=mil(f(comp["Híbrido de producción vs su árbol solo (3 rep.)"]["diff"])),
    redes_vs_arbol=mil(f(comp["Modelo con score: con redes vs árbol solo"]["diff"])),
    sem=mil(f(comp["Árbol 3 semillas vs 1 semilla (3 rep.)"]["diff"])),
    lc_last=n(f(lc[-1]["ganancia_al_duplicar"]) * 1000, 1),
)

tpl = (Path(__file__).parent / "plantilla_informe_v2.html").read_text()
for k, v in ctx.items():
    tpl = tpl.replace("{{" + k + "}}", v)
assert "{{" not in tpl, [l for l in tpl.splitlines() if "{{" in l][:3]
OUT.write_text(tpl)
print("ok", OUT)
