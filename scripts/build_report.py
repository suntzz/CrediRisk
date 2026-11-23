"""Genera docs/mejora-auc.html a partir de los CSV de reports/.

Un solo archivo autocontenido: CSS y SVG en línea, sin JS. Si falta un CSV,
su bloque muestra «pendiente» en vez de fallar. Todo número sale del CSV.

    python scripts/build_report.py [--reports DIR] [--out FILE]
"""
import argparse
import csv
import html
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- datos
def leer(dirp: Path, nombre: str):
    p = dirp / nombre
    if not p.exists():
        return None
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            filas = [{k.strip(): (v or "").strip() for k, v in r.items() if k}
                     for r in csv.DictReader(f)]
        return filas or None
    except Exception:
        return None


def num(v):
    try:
        x = float(str(v).replace(",", "."))
        return None if math.isnan(x) else x
    except (TypeError, ValueError):
        return None


def es_true(v):
    return str(v).strip().lower() in ("true", "1", "sí", "si", "yes")


def _coma(s):
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def f_auc(x, signo=False):
    if x is None:
        return "—"
    s = f"{x:+.4f}" if signo else f"{x:.4f}"
    return _coma(s).replace("-", "−")


def f_pct(x, frac=False):
    if x is None:
        return "—"
    if frac:
        x *= 100
    return f"{x:.0f}".replace("-", "−") + " %"


def f_miles(x):
    if x is None:
        return "—"
    return _coma(f"{x:,.0f}")


def f_dec(x, d=1):
    if x is None:
        return "—"
    return _coma(f"{x:.{d}f}").replace("-", "−")


def f_peso(x):
    if x is None:
        return "—"
    return _coma(f"{x:.2f}".rstrip("0").rstrip(".") if x % 1 else f"{x:.1f}")


def e(s):
    return html.escape(str(s))


def pendiente(que):
    return (f'<div class="pend"><span>pendiente</span>'
            f'<p>{e(que)} todavía no está en <code>reports/</code>.</p></div>')


def escala(d0, d1, r0, r1):
    span = (d1 - d0) or 1.0
    return lambda v: r0 + (v - d0) / span * (r1 - r0)


def limites(vals, pad=0.15, paso=0.005):
    lo, hi = min(vals), max(vals)
    m = (hi - lo) * pad or paso
    lo, hi = lo - m, hi + m
    return math.floor(lo / paso) * paso, math.ceil(hi / paso) * paso


def ticks(lo, hi, n=4):
    crudo = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(crudo))
    paso = min((k * mag for k in (1, 2, 2.5, 5, 10) if k * mag >= crudo), default=mag)
    t = math.ceil(lo / paso - 1e-9) * paso
    out = []
    while t <= hi + 1e-9:
        out.append(round(t, 10))
        t += paso
    return out


def svg(w, h, cuerpo, titulo):
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{e(titulo)}" '
            f'preserveAspectRatio="xMinYMin meet">{cuerpo}</svg>')


def dual(fn):
    """Misma gráfica en dos anchos: escritorio (rótulos a la izquierda) y celular (rótulos encima)."""
    return (f'<div class="v-esc">{fn(560, False)}</div>'
            f'<div class="v-mov">{fn(380, True)}</div>')


# ---------------------------------------------------------------- bloques
def resumen_dict(filas):
    if not filas:
        return {}
    return {r.get("metrica", ""): r for r in filas}


def bloque_portada(R):
    auc = R.get("auc_cv")
    dep = R.get("dependencia_pct")
    if not auc and not dep:
        cifras = pendiente("v2_resumen.csv")
    else:
        def par(r, fmt, nombre, sub):
            if not r:
                return f'<div class="kpi">{pendiente(nombre)}</div>'
            a, d = num(r.get("antes")), num(r.get("despues"))
            return (f'<div class="kpi"><p class="kpi-n">{e(nombre)}</p>'
                    f'<p class="kpi-v"><span class="antes">{fmt(a)}</span>'
                    f'<span class="flecha" aria-hidden="true">→</span>'
                    f'<span class="nuevo">{fmt(d)}</span></p>'
                    f'<p class="kpi-s">{sub}</p></div>')
        lo = num((R.get("auc_cv_ci_low") or {}).get("despues"))
        hi = num((R.get("auc_cv_ci_high") or {}).get("despues"))
        sub_auc = "clientes que el modelo no vio"
        if lo is not None and hi is not None:
            sub_auc += f" · mejora entre {f_auc(lo, True)} y {f_auc(hi, True)}"
        cifras = (par(auc, f_auc, "AUC", sub_auc)
                  + par(dep, f_pct, "Dependencia del score",
                        "cuánto del acierto viene solo del score"))
    titular = "Qué cambió en el modelo y cuánto subió el AUC."
    try:
        sube = num(auc["despues"]) > num(auc["antes"])
        baja = num(dep["despues"]) < num(dep["antes"])
        if sube and baja:
            titular = "El modelo nuevo acierta más y depende menos del score."
        elif sube:
            titular = "El modelo nuevo acierta más."
    except (TypeError, KeyError):
        pass
    frase = ("Mismo dato, más acierto y menos apoyo en el score: "
             "arreglamos cómo se rellenaban los vacíos, mezclamos con modelos sin score "
             "y bajamos el peso del score.")
    nota = (R.get("nota_final") or {}).get("despues")
    nota_html = f'<p class="nota">{e(nota)}</p>' if nota else ""
    return f'''
<header class="portada fila">
  <p class="eyebrow col-full">CrediRisk · mejora del AUC</p>
  <h1 class="col-titulo">{e(titular)}</h1>
  <div class="kpis col-full">{cifras}</div>
  <p class="lead col-texto">{e(frase)}</p>{nota_html}
</header>'''


def bloque_cascada(C):
    tit = "Cada arreglo suma; dos no movieron la aguja."
    if not C:
        return seccion("cascada", tit, pendiente("v2_cascada.csv"), "")
    C = sorted(C, key=lambda r: num(r.get("paso")) or 0)
    medios = C[1:-1]
    nosig = sum(1 for r in medios if not es_true(r.get("significativo")))
    if medios and nosig == 0:
        tit = "Cada cambio sumó AUC."
    elif medios:
        sig = len(medios) - nosig
        tit = (f"{sig} de {len(medios)} cambios sumaron; "
               f"{nosig} no {'movió' if nosig == 1 else 'movieron'} la aguja.")
    aucs = [num(r["auc"]) for r in C if num(r.get("auc")) is not None]
    extra = []
    prev = None
    for r in C:
        a, lo, hi = num(r.get("auc")), num(r.get("ci_low")), num(r.get("ci_high"))
        if prev is not None and lo is not None:
            extra += [prev + lo, prev + hi]
        prev = a if a is not None else prev
    d0, d1 = limites(aucs + extra, pad=0.05)
    for r in C:  # coma decimal también en los rótulos que trae el CSV
        r["etiqueta"] = re.sub(r"(\d)\.(\d)", r"\1,\2", r.get("etiqueta", ""))
    largo = max(len(r["etiqueta"]) for r in C) > 22
    graf = dual(lambda W, ap: _cascada_svg(C, d0, d1, W, ap or largo))
    texto = ("Barra = cuánto subió el AUC con ese cambio; bigote = intervalo del 95 %. "
             "En gris, cambios cuyo intervalo cruza el cero: no se puede decir que aporten.")
    return seccion("cascada", tit, graf, texto)


def _cascada_svg(C, d0, d1, W, apilado):
    izq, der = (26, W - 8) if apilado else (190, W - 12)
    fila_h, top = (60, 30) if apilado else (44, 30)
    dl = 20 if apilado else 0  # desplazamiento de la barra bajo el rótulo
    H = top + fila_h * len(C) + 10
    x = escala(d0, d1, izq, der)
    g = []
    for t in ticks(d0, d1, 4):
        g.append(f'<line class="grid" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top-6}" y2="{H-8}"/>'
                 f'<text class="eje" x="{x(t):.1f}" y="{top-12}" text-anchor="middle">{f_auc(t)}</text>')
    prev = None
    n = len(C)
    for i, r in enumerate(C):
        y = top + i * fila_h + 8 + dl
        yl = y - 6 if apilado else y + 17
        a = num(r.get("auc"))
        ap = num(r.get("aporte"))
        lo, hi = num(r.get("ci_low")), num(r.get("ci_high"))
        etiqueta = r.get("etiqueta", "")
        primero, ultimo = i == 0, i == n - 1
        if a is None:
            g.append(f'<text class="lab" x="0" y="{y+18}">{e(etiqueta)}</text>'
                     f'<text class="eje" x="{izq}" y="{y+18}">pendiente</text>')
            continue
        if primero or ultimo:
            cls = "b-antes" if primero else "b-nuevo"
            g.append(f'<rect class="{cls}" x="{izq}" y="{y}" width="{max(x(a)-izq,1):.1f}" height="24" rx="2"/>')
            g.append(f'<text class="lab fuerte" x="0" y="{yl}">{e(etiqueta)}</text>')
            if x(a) - izq > 70:
                g.append(f'<text class="val sobre" x="{x(a)-6:.1f}" y="{y+17}" text-anchor="end">{f_auc(a)}</text>')
            else:
                g.append(f'<text class="val" x="{x(a)+6:.1f}" y="{y+17}">{f_auc(a)}</text>')
        else:
            sig = es_true(r.get("significativo"))
            base = prev if prev is not None else a
            x0, x1 = sorted((x(base), x(a)))
            cls = "b-nuevo" if sig else "b-gris"
            g.append(f'<line class="conector" x1="{x(base):.1f}" x2="{x(base):.1f}" y1="{y-20-dl}" y2="{y+24}"/>')
            g.append(f'<rect class="{cls}" x="{x0:.1f}" y="{y}" width="{max(x1-x0,2):.1f}" height="24" rx="2"/>')
            if lo is not None and hi is not None:
                cl, ch = x(base + lo), x(base + hi)
                yc = y + 12
                g.append(f'<path class="ci" d="M{cl:.1f},{yc-6}v12M{cl:.1f},{yc}H{ch:.1f}M{ch:.1f},{yc-6}v12"/>')
            g.append(f'<text class="lab{"" if sig else " tenue"}" x="0" y="{yl}">{e(etiqueta)}</text>')
            txt = f_auc(ap, True) if ap is not None else ""
            if not sig:
                txt += " · no significativo"
            xt = max(x1, x(base + hi) if hi is not None else x1) + 6
            anchor = "start"
            if xt > der - (150 if not sig else 60):
                xt, anchor = min(x0, x(base + lo) if lo is not None else x0) - 6, "end"
            g.append(f'<text class="val{"" if sig else " tenue"}" x="{xt:.1f}" y="{y+17}" text-anchor="{anchor}">{e(txt)}</text>')
        prev = a
    return svg(W, H, "".join(g), "Cascada del AUC")


def bloque_imputacion(I, C):
    tit = "El error: los vacíos recibían un número fuera de escala."
    if not I:
        return seccion("error", tit, pendiente("v2_imputacion.csv"), "")
    I = sorted(I, key=lambda r: -(num(r.get("pct_vacios")) or 0))
    I = [r for r in I if (num(r.get("pct_vacios")) or 0) >= 0.5][:4] or I[:4]
    graf = dual(lambda W, ap: _imput_svg(I, W))
    efecto = ""
    if C:
        for r in C:
            if "imput" in r.get("etiqueta", "").lower():
                sig = str(r.get("significativo", "")).lower() == "true"
                efecto = (f" Arreglarlo sumó {f_auc(num(r.get('aporte')), True)} de AUC al híbrido"
                          + ("." if sig else " (no significativo). En las redes solas sí sube de forma significativa."))
    r0 = I[0]
    mal0 = num(r0.get("valor_que_recibia"))
    mal0 = f_miles(mal0) if mal0 is not None and abs(mal0) >= 1000 else f_dec(mal0, 0)
    texto = ("La mediana se calculaba antes del logaritmo y se aplicaba después: "
             f"un vacío en {e(r0.get('variable', '').replace('_', ' '))} valía {mal0} "
             f"donde el resto vive entre {f_dec(num(r0.get('p1_log')), 0)} y "
             f"{f_dec(num(r0.get('p99_log')), 0)} (barra gris = rango del 1 % al 99 %)." + efecto)
    return seccion("error", tit, graf, texto)


def _imput_svg(I, W):
    izq, der = 0, W - 110
    fila_h, top = 62, 10
    H = top + fila_h * len(I) + 8
    g = []
    for i, r in enumerate(I):
        y = top + i * fila_h
        p1, p99 = num(r.get("p1_log")), num(r.get("p99_log"))
        med, mal = num(r.get("mediana_correcta_log")), num(r.get("valor_que_recibia"))
        pv = num(r.get("pct_vacios"))
        if None in (p1, p99, med):
            continue
        lo, hi = min(p1, med), max(p99, med)
        span = (hi - lo) or 1
        x = escala(lo - span * 0.05, hi + span * 0.05, izq + 8, der - 30)
        yb = y + 34
        g.append(f'<text class="lab fuerte" x="{izq}" y="{y+14}">{e(r["variable"].replace("_", " "))}'
                 f'<tspan class="tenue"> · {f_pct(pv)} vacíos</tspan></text>')
        g.append(f'<rect class="rango" x="{x(p1):.1f}" y="{yb-5}" width="{x(p99)-x(p1):.1f}" height="10" rx="5"/>')
        g.append(f'<circle class="p-nuevo" cx="{x(med):.1f}" cy="{yb}" r="6"/>')
        g.append(f'<text class="mini nuevo-t" x="{x(med):.1f}" y="{yb+22}" text-anchor="middle">debía: {f_dec(med)}</text>')
        if mal is not None:
            xe = der - 18
            g.append(f'<path class="fuga" d="M{x(p99)+6:.1f},{yb}H{xe:.1f}"/>'
                     f'<path class="fuga-p" d="M{xe:.1f},{yb-5}l8,5l-8,5z"/>')
            g.append(f'<text class="val alerta" x="{xe+14:.1f}" y="{yb+5}">recibía {f_miles(mal) if abs(mal) >= 1000 else f_dec(mal, 0)}</text>')
    return svg(W, H, "".join(g), "Valor que recibía un vacío frente al rango real")


def bloque_score(V, R):
    tit = "Menos score, casi el mismo acierto."
    partes = []
    if not V:
        partes.append(pendiente("v2_curva_peso.csv"))
    else:
        pts = [(num(r.get("dependencia_pct")), num(r.get("auc")), r) for r in V]
        pts = [p for p in pts if p[0] is not None and p[1] is not None]
        prod = R.get("dependencia_pct"), R.get("auc_cv")
        pd_, pa = (num(prod[0].get("antes")) if prod[0] else None,
                   num(prod[1].get("antes")) if prod[1] else None)
        partes.append(dual(lambda W, ap: _curva_svg(pts, pd_, pa, W)))
    sv = R.get("auc_score_vacio")
    if not sv:
        partes.append(pendiente("AUC con score vacío (v2_resumen.csv)"))
    else:
        partes.append(dual(lambda W, ap: _vacio_svg(sv, W)))
    texto = ("Cada punto es un peso distinto del modelo con score frente al modelo sin score. "
             "El elegido es el de menos dependencia sin perder AUC de forma significativa frente al mejor.")
    return seccion("score", tit, "".join(f'<div class="graf">{p}</div>' for p in partes), texto)


def _curva_svg(pts, pd_, pa, W):
        xs = [p[0] for p in pts] + ([pd_] if pd_ is not None else [])
        ys = [p[1] for p in pts] + ([pa] if pa is not None else [])
        if not ys:
            return pendiente("v2_curva_peso.csv")
        H, l, rr, t, b = 320, 58, W - 20, 50, 270
        x0 = 0
        x1 = math.ceil(max(xs + [10]) / 10) * 10
        y0, y1 = limites(ys, pad=0.12)
        X, Y = escala(x0, x1, l, rr), escala(y0, y1, b, t)
        g = []
        for tv in ticks(y0, y1, 4):
            g.append(f'<line class="grid" x1="{l}" x2="{rr}" y1="{Y(tv):.1f}" y2="{Y(tv):.1f}"/>'
                     f'<text class="eje" x="{l-6}" y="{Y(tv)+4:.1f}" text-anchor="end">{f_auc(tv)}</text>')
        for tv in ticks(x0, x1, 5):
            g.append(f'<text class="eje" x="{X(tv):.1f}" y="{b+18}" text-anchor="middle">{f_pct(tv)}</text>')
        g.append(f'<text class="eje" x="{rr}" y="{b+38}" text-anchor="end">dependencia del score →</text>')
        g.append(f'<text class="eje" x="{l-6}" y="{t-6}" text-anchor="end">AUC</text>')
        pts.sort(key=lambda p: p[0])
        g.append('<polyline class="linea" points="' +
                 " ".join(f"{X(a):.1f},{Y(c):.1f}" for a, c, _ in pts) + '"/>')
        xel = next((X(a) for a, c, r in pts if es_true(r.get("elegido"))), None)
        for a, c, r in pts:
            el = es_true(r.get("elegido"))
            cerca = xel is not None and not el and xel - 175 < X(a) < xel + 40
            peso = num(r.get("peso_con_score"))
            g.append(f'<circle class="{"p-nuevo grande" if el else "p-gris"}" cx="{X(a):.1f}" cy="{Y(c):.1f}" r="{7 if el else 4}"/>')
            if not el and not cerca and peso is not None and (len(pts) <= 7 or r is pts[0][2] or r is pts[-1][2]
                                                 or round(peso * 100) % 20 == 0):
                g.append(f'<text class="mini tenue" x="{X(a):.1f}" y="{Y(c)-10:.1f}" text-anchor="middle">peso {f_peso(peso)}</text>')
            if el:
                xa, an = (X(a) - 4, "end") if X(a) > l + 170 else (X(a) + 12, "start")
                g.append(f'<text class="val nuevo-t" x="{xa:.1f}" y="{Y(c)-28:.1f}" text-anchor="{an}">elegido · peso {f_peso(peso)}</text>'
                         f'<text class="mini nuevo-t" x="{xa:.1f}" y="{Y(c)-12:.1f}" text-anchor="{an}">{f_auc(c)} · {f_pct(a)}</text>')
        if pd_ is not None and pa is not None:
            g.append(f'<rect class="p-antes" x="{X(pd_)-6:.1f}" y="{Y(pa)-6:.1f}" width="12" height="12"/>'
                     f'<text class="val" x="{X(pd_)-12:.1f}" y="{Y(pa)+22:.1f}" text-anchor="end">hoy (producción)</text>'
                     f'<text class="mini tenue" x="{X(pd_)-12:.1f}" y="{Y(pa)+38:.1f}" text-anchor="end">{f_auc(pa)} · {f_pct(pd_)}</text>')
        return svg(W, H + 20, "".join(g), "AUC frente a dependencia del score")


def _vacio_svg(sv, W):
        a, d = num(sv.get("antes")), num(sv.get("despues"))
        l, rr = 110, W - 90
        X = escala(0.5, 1.0, l, rr)
        g = [f'<text class="lab fuerte" x="0" y="14">Si el score falta</text>']
        for i, (nom, v, cls) in enumerate((("producción", a, "b-antes"), ("nuevo", d, "b-nuevo"))):
            y = 28 + i * 34
            g.append(f'<text class="lab" x="0" y="{y+17}">{nom}</text>')
            if v is not None:
                g.append(f'<rect class="{cls}" x="{l}" y="{y}" width="{max(X(v)-l,1):.1f}" height="24" rx="2"/>'
                         f'<text class="val" x="{X(v)+6:.1f}" y="{y+17}">{f_auc(v)}</text>')
        g.append(f'<text class="mini tenue" x="{l}" y="112">eje desde 0,5 = azar</text>')
        return svg(W, 120, "".join(g), "AUC cuando el score está vacío")


def dumbbell(filas, k_nom, titulo):
    if not any(num(r.get(k)) is not None for r in filas for k in ("auc_produccion", "auc_final")):
        return pendiente(titulo)
    return dual(lambda W, ap: _dumbbell_svg(filas, k_nom, titulo, W, ap))


def _dumbbell_svg(filas, k_nom, titulo, W, apilado):
    vals = [num(r.get(k)) for r in filas for k in ("auc_produccion", "auc_final")]
    vals = [v for v in vals if v is not None]
    if not vals:
        return pendiente(titulo)
    d0, d1 = limites(vals, pad=0.08, paso=0.01)
    l, rr = (6, W - 60) if apilado else (150, W - 60)
    fila_h, top = (50, 26) if apilado else (34, 26)
    dl = 18 if apilado else 0
    H = top + fila_h * len(filas) + 6
    X = escala(d0, d1, l, rr)
    g = []
    for tv in ticks(d0, d1, 4):
        g.append(f'<line class="grid" x1="{X(tv):.1f}" x2="{X(tv):.1f}" y1="{top-6}" y2="{H-4}"/>'
                 f'<text class="eje" x="{X(tv):.1f}" y="{top-12}" text-anchor="middle">{f_auc(tv)}</text>')
    for i, r in enumerate(filas):
        y = top + i * fila_h + 14 + dl
        yl = y - 12 if apilado else y + 5
        a, f = num(r.get("auc_produccion")), num(r.get("auc_final"))
        nom = r.get(k_nom, "")
        n = num(r.get("n"))
        g.append(f'<text class="lab" x="0" y="{yl}">{e(nom)}'
                 + (f'<tspan class="tenue"> · {f_miles(n)}</tspan>' if n else "") + '</text>')
        if a is not None and f is not None:
            g.append(f'<line class="union" x1="{X(a):.1f}" x2="{X(f):.1f}" y1="{y}" y2="{y}"/>')
        if a is not None:
            g.append(f'<circle class="p-gris" cx="{X(a):.1f}" cy="{y}" r="5"/>')
        if f is not None:
            g.append(f'<circle class="p-nuevo" cx="{X(f):.1f}" cy="{y}" r="6"/>')
            dx = f - a if a is not None else None
            xt = max(X(f), X(a) if a is not None else 0) + 10
            g.append(f'<text class="mini nuevo-t" x="{xt:.1f}" y="{y+4}">{f_auc(f)}</text>')
        if i == 0 and a is not None and f is not None and not apilado:
            # rótulos directos en la primera fila
            ia, fa = ("end", "start") if f >= a else ("start", "end")
            g.append(f'<text class="mini tenue" x="{X(a):.1f}" y="{y-9}" text-anchor="{ia}">antes</text>'
                     f'<text class="mini nuevo-t" x="{X(f):.1f}" y="{y-9}" text-anchor="{fa}">nuevo</text>')
    return svg(W, H, "".join(g), titulo)


def bloque_estres(S, G):
    tit = "Bajo estrés: producción frente al nuevo."
    if S:
        dif = [(num(r.get("auc_final")), num(r.get("auc_produccion"))) for r in S]
        dif = [f - a for f, a in dif if f is not None and a is not None]
        if dif and min(dif) > 0:
            tit = "El nuevo gana en todas las pruebas; sin score, los dos caen."
        elif dif:
            tit = f"El nuevo gana en {sum(d > 0 for d in dif)} de {len(dif)} pruebas de estrés."
    partes = []
    if not S:
        partes.append(pendiente("stress_resumen.csv"))
    else:
        partes.append(dumbbell(S, "prueba", "AUC bajo estrés"))
    prods = [r for r in (G or []) if r.get("grupo", "").lower() == "producto"]
    if not prods:
        partes.append(pendiente("AUC por producto (stress_subgrupos.csv)"))
    else:
        prods.sort(key=lambda r: -(num(r.get("n")) or 0))
        partes.append('<p class="subt">AUC por producto · clientes</p>' + dumbbell(prods, "segmento", "AUC por producto"))
    peor = None
    if prods:
        cand = [(num(r.get("auc_final")), r.get("segmento")) for r in prods if num(r.get("auc_final")) is not None]
        if cand:
            peor = min(cand)
    texto = "Gris = producción, color = nuevo, cada fila es una prueba a propósito difícil."
    if peor:
        texto += f" El punto flojo sigue siendo {e(peor[1])} ({f_auc(peor[0])})."
    return seccion("estres", tit, "".join(f'<div class="graf">{p}</div>' for p in partes), texto)


DIRP = None


def bloque_umbrales(U):
    tit = "Qué umbral usar depende de cuánto cuesta un mal cliente."
    lc = leer(DIRP, "v2_curva_aprendizaje.csv") if DIRP else None
    curva = ""
    if lc and len(lc) >= 2:
        a, b = lc[-2], lc[-1]
        curva = (f' Duplicar los datos de entrenamiento ({f_miles(num(a.get("filas_entrenamiento")))} → '
                 f'{f_miles(num(b.get("filas_entrenamiento")))} filas) subió el AUC solo '
                 f'{f_auc(num(b.get("auc")) - num(a.get("auc")), True)}: harían falta varias veces más filas para 0,77.')
    techo = ('<aside class="techo"><h3>¿Y por qué no 0,78?</h3>'
             '<p>El CSV es la base pública <em>Home Credit Default Risk</em> recortada '
             '(el id 100002 coincide fila a fila: ingreso 202.500, monto 406.597,5, '
             'cuota 24.700,5, incumplió). Con estas 23 columnas lo mejor medido es 0,7617.' + curva +
             ' Llegar a 0,78 exige traer columnas de fuera, y la regla de la '
             'competencia no lo permite.</p></aside>')
    if not U:
        return seccion("umbrales", tit, pendiente("umbrales_por_costo.csv") + techo, "")
    hay_ci = any(r.get("mora_aprobados_ci_low") for r in U)
    filas = []
    prev = None
    for r in U:
        p = r.get("producto", "")
        mora = f_dec((num(r.get("mora_aprobados")) or 0) * 100, 1) + " %" if num(r.get("mora_aprobados")) is not None else "—"
        ci = ""
        if hay_ci:
            lo, hi = num(r.get("mora_aprobados_ci_low")), num(r.get("mora_aprobados_ci_high"))
            ci = (f'<td class="tenue col-ci">{f_dec(lo*100,1)}–{f_dec(hi*100,1)}</td>'
                  if lo is not None and hi is not None else '<td class="tenue col-ci">—</td>')
        cab = f'<th scope="row">{e(p)}</th>' if p != prev else '<th scope="row" class="rep"></th>'
        filas.append(f'<tr class="{"nuevo-grupo" if p != prev else ""}">{cab}'
                     f'<td>{f_dec(num(r.get("costo_malo_vs_bueno")),0)}×</td>'
                     f'<td>{f_dec(num(r.get("umbral")),2)}</td>'
                     f'<td>{f_pct(num(r.get("tasa_aprobacion")), True)}</td>'
                     f'<td class="fuerte">{mora}</td>{ci}</tr>')
        prev = p
    th_ci = '<th scope="col" class="col-ci">intervalo</th>' if hay_ci else ""
    tabla = (f'<div class="tabla-env"><table><thead><tr><th scope="col">producto</th>'
             f'<th scope="col">un malo cuesta</th><th scope="col">umbral</th>'
             f'<th scope="col">se aprueba</th><th scope="col">mora en aprobados</th>{th_ci}</tr></thead>'
             f'<tbody>{"".join(filas)}</tbody></table></div>')
    texto = ("«Un malo cuesta 10×» = aprobar a quien no paga duele diez veces más que "
             "rechazar a quien sí pagaría. A más costo, umbral más alto y menos mora.")
    return seccion("umbrales", tit, tabla + techo, texto)


def seccion(id_, titulo, cuerpo, texto):
    t = f'<p class="col-texto txt">{texto}</p>' if texto else ""
    return f'''
<section class="bloque fila" id="{id_}">
  <div class="col-titulo"><h2>{e(titulo)}</h2>{t}</div>
  <div class="col-graf">{cuerpo}</div>
</section>'''


METODO = '''
<details class="metodo">
  <summary>Cómo se midió</summary>
  <ul>
    <li>Validación cruzada de 5 pliegues × 3 repeticiones sobre entrenamiento + validación (42.202 filas). El AUC «de clientes que el modelo no vio» sale de ahí.</li>
    <li>El preprocesador se ajusta dentro de cada pliegue, así nada del pliegue de prueba se filtra.</li>
    <li>Intervalos por bootstrap pareado: mismos clientes para el modelo de antes y el nuevo.</li>
    <li>Las redes nuevas se midieron con una sola repetición (5 pliegues) por tiempo; por eso las mezclas con redes usan la repetición 0 de todos los modelos.</li>
    <li>Modelo final = 0,85 × (0,90 árbol + 0,10 redes, con score) + 0,15 × (0,90 árbol + 0,10 redes, sin score). Árbol: HistGradientBoosting sobre variables crudas + razones, 5 semillas. Redes: las 3 de siempre, con el preprocesador corregido.</li>
    <li>Las redes quedan con peso 0,10: con los pesos buscados de 0,05 en 0,05 no suman ni restan de forma significativa frente al árbol solo; se conservan porque la arquitectura es híbrida.</li>
    <li>Peso del modelo con score: entre los pesos cuyo AUC no es significativamente menor que el mejor, el de menor dependencia del score. Revolving loans no mejora con un peso propio.</li>
    <li>En la prueba vieja, producción se entrenó solo con entrenamiento; el nuevo con entrenamiento + validación.</li>
    <li>La prueba vieja (7.448 filas) ya la había usado el equipo antes; se miró una sola vez, al final. El número confiable es el de validación cruzada.</li>
    <li>Código: <code>src/cv_protocol.py</code>, <code>src/cv_candidates.py</code>, <code>src/final_blend.py</code>, <code>src/stress_tests.py</code>, <code>src/cost_thresholds.py</code>, <code>src/train_final_v2.py</code>, <code>src/predict_v2.py</code>, <code>artifacts/v2/</code>. Este informe: <code>scripts/build_report.py</code>.</li>
  </ul>
</details>'''


def prueba_linea(R, T):
    """Línea pequeña con el AUC de la prueba vieja (mirada una vez)."""
    r = R.get("auc_prueba")
    if not r:
        return ""
    s = (f'Prueba vieja, mirada una vez: {f_auc(num(r.get("antes")))} → '
         f'<b>{f_auc(num(r.get("despues")))}</b>')
    if T:
        g = next((x for x in T if x.get("segmento", "").lower() in ("global", "todos", "total")), None)
        if g and num(g.get("ci_low")) is not None:
            s += f' (diferencia {f_auc(num(g.get("ci_low")), True)} a {f_auc(num(g.get("ci_high")), True)})'
    return f'<p class="prueba">{s}.</p>'


CSS = r'''
:root{
  --fondo:#f6f7f8; --papel:#ffffff; --tinta:#14171a; --suave:#5b636b; --linea:#dfe3e7;
  --gris:#a3abb3; --gris-osc:#7d868f; --acento:#0b6e4f; --acento-suave:#d6efe5; --alerta:#b42318;
  --titular:"Bricolage Grotesque","Archivo","Helvetica Neue",Arial,sans-serif;
  --texto:"IBM Plex Sans","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){
  :root{ --fondo:#0f1214; --papel:#171b1e; --tinta:#e9ecee; --suave:#9aa3ab; --linea:#2a3035;
    --gris:#5f6870; --gris-osc:#8a939b; --acento:#3ddc97; --acento-suave:#123528; --alerta:#ff7a6b; }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--fondo);color:var(--tinta);font:400 1rem/1.55 var(--texto);
  font-variant-numeric:tabular-nums;}
.envoltura{max-width:1180px;margin:0 auto;padding:0 20px 64px}
.fila{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));column-gap:24px}
.fila>*{grid-column:1/-1;min-width:0}
h1,h2,h3{font-family:var(--titular);font-weight:700;letter-spacing:-.02em;margin:0}
h1{font-size:clamp(2rem,6vw,3.6rem);line-height:1.02;max-width:16ch}
h2{font-size:clamp(1.35rem,2.6vw,1.9rem);line-height:1.12}
h3{font-size:1.1rem}
.eyebrow{font:600 .78rem/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--suave);margin:0 0 18px}
.portada{padding:56px 0 40px;border-bottom:1px solid var(--linea)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin:32px 0 24px}
.kpi{background:var(--papel);border:1px solid var(--linea);border-radius:10px;padding:20px 22px}
.kpi-n{margin:0;font-weight:600;color:var(--suave);font-size:.9rem}
.kpi-v{margin:6px 0 4px;font-family:var(--titular);font-weight:700;font-size:clamp(2rem,5.2vw,3.2rem);line-height:1.05;
  display:flex;flex-wrap:wrap;align-items:baseline;gap:.25em .4em;font-variant-numeric:tabular-nums}
.kpi-v .antes{color:var(--gris-osc);font-size:.62em;font-weight:600}
.kpi-v .flecha{color:var(--gris);font-size:.55em}
.kpi-v .nuevo{color:var(--acento)}
.kpi-s{margin:0;color:var(--suave);font-size:.85rem}
.lead{font-size:1.12rem;margin:0;max-width:60ch}
.nota,.prueba{color:var(--suave);font-size:.88rem;margin:12px 0 0}
.bloque{padding:48px 0;border-bottom:1px solid var(--linea);row-gap:20px;align-items:start}
.txt{color:var(--suave);margin:12px 0 0;max-width:46ch}
.col-graf{background:var(--papel);border:1px solid var(--linea);border-radius:10px;padding:18px 16px}
.graf+.graf{margin-top:22px;padding-top:18px;border-top:1px solid var(--linea)}
.subt{margin:0 0 6px;font-weight:600;font-size:.9rem;color:var(--suave)}
svg{display:block;width:100%;height:auto;overflow:visible;font-family:var(--texto);font-variant-numeric:tabular-nums}
svg text{fill:var(--tinta);font-size:15px}
svg .eje{fill:var(--suave);font-size:13px}
svg .lab{font-size:15px}
svg .fuerte{font-weight:600}
svg .tenue,svg tspan.tenue{fill:var(--gris-osc)}
svg .val{font-size:15px;font-weight:600}
svg .mini{font-size:13px}
svg .nuevo-t{fill:var(--acento);font-weight:600}
svg .sobre{fill:var(--papel)}
svg .alerta{fill:var(--alerta)}
svg .grid{stroke:var(--linea);stroke-width:1}
svg .b-antes{fill:var(--gris)} svg .b-nuevo{fill:var(--acento)}
svg .b-gris{fill:none;stroke:var(--gris);stroke-width:1.5;stroke-dasharray:3 2}
svg .conector{stroke:var(--gris);stroke-width:1;stroke-dasharray:2 3}
svg .ci{stroke:var(--tinta);stroke-width:1.4;fill:none;opacity:.7}
svg .rango{fill:var(--linea)}
svg .fuga{stroke:var(--alerta);stroke-width:1.6;stroke-dasharray:4 3;fill:none}
svg .fuga-p{fill:var(--alerta)}
svg .p-nuevo{fill:var(--acento);stroke:var(--papel);stroke-width:2}
svg .p-gris{fill:var(--gris)}
svg .p-antes{fill:var(--gris-osc)}
svg .linea{fill:none;stroke:var(--gris);stroke-width:1.5}
svg .union{stroke:var(--gris);stroke-width:2}
.pend{border:1px dashed var(--gris);border-radius:8px;padding:14px 16px;color:var(--suave);font-size:.9rem}
.pend span{font:600 .72rem/1 var(--mono);text-transform:uppercase;letter-spacing:.08em}
.pend p{margin:6px 0 0}
.pend+.pend,.graf .pend{margin-top:0}
code{font-family:var(--mono);font-size:.86em}
.tabla-env{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.92rem}
th,td{text-align:right;padding:7px 8px;border-bottom:1px solid var(--linea);white-space:nowrap}
thead th{font-weight:600;color:var(--suave);font-size:.78rem;vertical-align:bottom;white-space:normal}
th:first-child,td:first-child{text-align:left;padding-left:0}
tbody th{font-weight:600}
tr.nuevo-grupo>*{border-top:1px solid var(--tinta)}
tbody tr:first-child>*{border-top:0}
td.fuerte{color:var(--acento);font-weight:600}
td.tenue{color:var(--gris-osc)}
.techo{margin-top:22px;padding:16px 18px;border-left:3px solid var(--gris);background:var(--fondo);border-radius:0 8px 8px 0}
.techo p{margin:6px 0 0;color:var(--suave);font-size:.92rem}
.metodo{margin-top:40px;border:1px solid var(--linea);border-radius:10px;background:var(--papel);padding:0 20px}
.metodo summary{cursor:pointer;padding:16px 0;font-family:var(--titular);font-weight:700;font-size:1.1rem}
.metodo ul{margin:0 0 18px;padding-left:1.1em;color:var(--suave);font-size:.92rem}
.metodo li{margin:6px 0}
.metodo code{overflow-wrap:anywhere}
footer{color:var(--suave);font-size:.8rem;margin-top:24px}
@media (min-width:900px){
  .col-titulo{grid-column:1/6} .col-texto{grid-column:1/8} .col-graf{grid-column:6/13}
  .portada .col-titulo{grid-column:1/10} .col-full{grid-column:1/-1}
  .bloque .col-titulo{position:sticky;top:24px}
}
.v-mov{display:none}
@media (max-width:620px){ .v-esc{display:none} .v-mov{display:block} .col-ci{display:none} }
@media (max-width:520px){
  .envoltura{padding:0 14px 48px}
  .col-graf{padding:14px 10px}
  .kpi{padding:16px}
  th,td{padding:6px 5px}
}
'''


def construir(dirp: Path) -> str:
    global DIRP
    DIRP = dirp
    R = resumen_dict(leer(dirp, "v2_resumen.csv"))
    C = leer(dirp, "v2_cascada.csv")
    I = leer(dirp, "v2_imputacion.csv")
    V = leer(dirp, "v2_curva_peso.csv")
    S = leer(dirp, "stress_resumen.csv")
    G = leer(dirp, "stress_subgrupos.csv")
    U = leer(dirp, "umbrales_por_costo.csv")
    T = leer(dirp, "final_v2_test.csv")
    portada = bloque_portada(R).replace("</header>", prueba_linea(R, T) + "</header>")
    cuerpo = (portada + bloque_cascada(C) + bloque_imputacion(I, C) + bloque_score(V, R)
              + bloque_estres(S, G) + bloque_umbrales(U) + METODO)
    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>CrediRisk · qué cambió y por qué subió el AUC</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<main class="envoltura">
{cuerpo}
<footer>Generado por <code>scripts/build_report.py</code> desde <code>reports/</code>.</footer>
</main>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reports", type=Path, default=ROOT / "reports")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "mejora-auc.html")
    a = ap.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(construir(a.reports), encoding="utf-8")
    print(f"escrito {a.out}")


if __name__ == "__main__":
    main()
