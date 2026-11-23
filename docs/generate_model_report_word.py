#!/usr/bin/env python3
"""Genera el informe Word de Fase 5 a partir de los reportes reproducibles."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs"
IMAGES = DOCS / "images"
OUT = DOCS / "Informe_Tecnico_Modelo_CrediRisk_Fase5.docx"
CHART = IMAGES / "fase5_comparacion_modelos.png"

NAVY = "102A43"
TEAL = "0F766E"
PALE = "EAF2F8"
LIGHT = "F6F8FA"
GRAY = "5B6770"
GRID = "D9E2EC"


def shade(cell, color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def set_cell_border(cell, color=GRID) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:color"), color)


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def add_table(document, headers, rows, widths=None, font_size=9) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    header = table.rows[0]
    set_repeat_table_header(header)
    for i, text in enumerate(headers):
        cell = header.cells[i]
        cell.text = str(text)
        shade(cell, NAVY)
        set_cell_border(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(font_size)
        if widths:
            cell.width = Inches(widths[i])
    for r_idx, row in enumerate(rows):
        cells = table.add_row().cells
        for i, text in enumerate(row):
            cell = cells[i]
            cell.text = str(text)
            set_cell_border(cell)
            if r_idx % 2 == 1:
                shade(cell, LIGHT)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if widths:
                cell.width = Inches(widths[i])
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.size = Pt(font_size)
    document.add_paragraph().paragraph_format.space_after = Pt(3)


def paragraph(document, text, bold_lead: str | None = None) -> None:
    p = document.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.line_spacing = 1.15
    if bold_lead and text.startswith(bold_lead):
        run = p.add_run(bold_lead)
        run.bold = True
        p.add_run(text[len(bold_lead):])
    else:
        p.add_run(text)


def metric(value) -> str:
    return f"{float(value):.5f}"


def build_chart(validation: pd.DataFrame, score32: pd.DataFrame) -> None:
    score_mask = score32.loc[score32["candidate"] == "score_mask_32"].iloc[0]
    comparison = pd.concat([
        validation[["candidate", "auc"]],
        pd.DataFrame([{"candidate": "score_mask_32", "auc": float(score_mask["auc"])}]),
    ], ignore_index=True)
    order = comparison.sort_values("auc", ascending=True)
    labels = order["candidate"].replace({
        "baseline_production": "Ensamble publicado",
        "elu_input_noise": "ELU con ruido de entrada",
        "elu_regularized": "ELU regularizado",
        "wide_elu_regularized": "ELU amplio regularizado",
        "compact_gelu": "GELU compacto",
        "score_mask_32": "Score enmascarado 32%",
    })
    colors = [
        f"#{TEAL}" if c == "baseline_production" else "#C97A40" if c == "score_mask_32" else "#8DA7B8"
        for c in order["candidate"]
    ]
    fig, ax = plt.subplots(figsize=(8.3, 4.9), dpi=180)
    bars = ax.barh(labels, order["auc"], color=colors, height=0.58)
    ax.set_xlim(0.748, 0.755)
    ax.set_xlabel("ROC AUC en validation")
    ax.grid(axis="x", color="#D9E2EC", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, order["auc"]):
        ax.text(value + 0.00004, bar.get_y() + bar.get_height() / 2, f"{value:.5f}", va="center", fontsize=9, color=f"#{NAVY}")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    IMAGES.mkdir(exist_ok=True)
    fig.savefig(CHART, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def setup_styles(document: Document) -> None:
    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Aptos")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    for name, size in (("Title", 26), ("Heading 1", 16), ("Heading 2", 12)):
        style = styles[name]
        style.font.name = "Aptos Display" if name != "Heading 2" else "Aptos"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), style.font.name)
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
    if "Caption" not in styles:
        styles.add_style("Caption", WD_STYLE_TYPE.PARAGRAPH)
    styles["Caption"].font.name = "Aptos"
    styles["Caption"].font.size = Pt(9)
    styles["Caption"].font.color.rgb = RGBColor.from_string(GRAY)


def add_header_footer(section) -> None:
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = header.add_run("CrediRisk  |  Informe técnico del modelo")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor.from_string(GRAY)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("Universidad Católica de Colombia  |  CrediRisk  |  23 de noviembre de 2026")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor.from_string(GRAY)


def main() -> None:
    validation = pd.read_csv(REPORTS / "phase5_generalization_validation.csv")
    epochs = pd.read_csv(REPORTS / "phase5_generalization_epochs.csv")
    test = pd.read_csv(REPORTS / "phase5_generalization_test.csv")
    score32 = pd.read_csv(REPORTS / "phase4_score32_candidate_comparison.csv")
    build_chart(validation, score32)

    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)
    setup_styles(document)
    add_header_footer(section)

    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Informe técnico del modelo CrediRisk")
    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Entrenamiento reproducible, controles de generalización y resultados publicados")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor.from_string(GRAY)
    document.add_paragraph()
    paragraph(document, "Conclusión. El ensamble neuronal ya publicado se conservó como modelo de producción porque obtuvo el mejor equilibrio entre discriminación y calibración. Se ejecutaron 12 entrenamientos adicionales con controles anti sobreajuste; ninguno lo superó de forma objetiva.")
    paragraph(document, "Este informe reúne los cambios realizados, los datos reproducibles, las épocas efectivamente ejecutadas y las pruebas de publicación. Está pensado para explicar la decisión técnica ante docentes y equipo de proyecto.")
    document.add_paragraph()

    document.add_heading("Resumen de resultados", level=1)
    base = validation.loc[validation["candidate"] == "baseline_production"].iloc[0]
    selected_test = test.loc[test["linea_negocio"] == "GLOBAL"].iloc[0]
    add_table(document, ["Indicador", "Resultado", "Interpretación"], [
        ["Modelo publicado", "Ensamble diverso de 3 redes", "Ganador por AUC y Brier en validation"],
        ["AUC validation", metric(base["auc"]), "Capacidad de separar aptos y no aptos"],
        ["AUC test aislado", metric(selected_test["auc"]), "Resultado en datos no usados durante selección"],
        ["Brier validation", metric(base["brier"]), "Calidad de las probabilidades estimadas"],
        ["Umbral Cash loans", "0.51", "Seleccionado en validation"],
        ["Umbral Revolving loans", "0.63", "Seleccionado en validation"],
    ], widths=[1.65, 1.5, 3.55])

    document.add_heading("Datos y protocolo reproducible", level=1)
    paragraph(document, "El análisis usa DatasetCreditoFinancieroFinalV2.csv con 49,650 solicitudes. La división fue estratificada y fija: 34,755 para entrenamiento, 7,447 para validation y 7,448 para test. El preprocesador se ajustó solo con training y luego se aplicó sin volver a ajustarse a los demás conjuntos.")
    paragraph(document, "Las transformaciones incluyen recorte p1 p99, imputación por mediana, transformaciones logarítmicas, banderas de valores faltantes, variables categóricas one hot y estandarización. Cada red se entrenó con batch de 128 y un máximo de 120 épocas. Early stopping monitoreó val_auc con paciencia de 16 épocas y restauró los mejores pesos.")

    document.add_heading("Prueba del score al 32 por ciento", level=1)
    paragraph(document, "La solicitud de limitar el score se aplicó mediante enmascaramiento en el 32% de los casos de entrenamiento. Esta técnica limita la disponibilidad de score_crediticio sin inventar un porcentaje de peso dentro de una red, donde los pesos individuales no se interpretan como contribuciones globales.")
    score_base = score32.loc[score32["candidate"] == "baseline_historico"].iloc[0]
    score_mask = score32.loc[score32["candidate"] == "score_mask_32"].iloc[0]
    add_table(document, ["Candidato", "AUC validation", "Brier", "Caída AUC al permutar score"], [
        ["Ensamble base", metric(score_base["auc"]), metric(score_base["brier"]), metric(score_base["score_auc_drop"])],
        ["Score enmascarado 32%", metric(score_mask["auc"]), metric(score_mask["brier"]), metric(score_mask["score_auc_drop"])],
    ], widths=[2.25, 1.3, 1.0, 2.15])
    paragraph(document, "El enmascaramiento redujo la dependencia medida del score, pero redujo AUC y empeoró Brier. Por ello no se promovió a producción.")

    document.add_heading("Búsqueda de generalización", level=1)
    document.add_picture(str(CHART), width=Inches(6.55))
    cap = document.add_paragraph("Figura 1. Comparación ROC AUC en validation. Verde: modelo publicado. Naranja: score enmascarado al 32%.", style="Caption")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    display = validation.copy()
    display["candidate"] = display["candidate"].replace({
        "baseline_production": "Ensamble publicado", "elu_input_noise": "ELU con ruido", "elu_regularized": "ELU regularizado",
        "wide_elu_regularized": "ELU amplio", "compact_gelu": "GELU compacto",
    })
    add_table(document, ["Candidato", "AUC", "Brier", "Época óptima media", "Brecha train validation"], [
        [r["candidate"], metric(r["auc"]), metric(r["brier"]), "—" if pd.isna(r["mean_best_epoch"]) else f"{r['mean_best_epoch']:.1f}", "—" if pd.isna(r["mean_loss_gap"]) else f"{r['mean_loss_gap']:.5f}"]
        for _, r in display.iterrows()
    ], widths=[2.25, 1.0, 0.95, 1.3, 1.0])
    paragraph(document, "Las cuatro familias evaluadas fueron ELU regularizado, ELU con ruido gaussiano de entrada, ELU amplio regularizado y GELU compacto. Cada una se repitió con las semillas 42, 2026 y 7. Ninguna superó la regla de promoción: mejorar al menos 0.001 AUC sin empeorar Brier y sin señales de una brecha train validation excesiva.")

    document.add_heading("Épocas y control de sobreajuste", level=1)
    epochs_display = epochs[["candidate", "seed", "epochs_trained", "best_epoch", "best_val_auc", "loss_gap"]].copy()
    epochs_display["candidate"] = epochs_display["candidate"].replace({
        "elu_regularized": "ELU regularizado", "elu_input_noise": "ELU con ruido", "wide_elu_regularized": "ELU amplio", "compact_gelu": "GELU compacto",
    })
    add_table(document, ["Familia", "Semilla", "Épocas", "Mejor época", "Mejor AUC val", "Brecha pérdida"], [
        [r["candidate"], int(r["seed"]), int(r["epochs_trained"]), int(r["best_epoch"]), metric(r["best_val_auc"]), f"{r['loss_gap']:.5f}"]
        for _, r in epochs_display.iterrows()
    ], widths=[1.75, 0.65, 0.7, 0.8, 1.1, 1.15], font_size=8)

    document.add_page_break()
    document.add_heading("Resultado final por producto", level=1)
    product_rows = test.copy()
    add_table(document, ["Segmento", "Registros test", "AUC", "PR AUC", "Brier", "Exactitud balanceada", "Umbral"], [
        [r["linea_negocio"], int(r["n_test"]), metric(r["auc"]), metric(r["pr_auc"]), metric(r["brier"]), metric(r["balanced_accuracy"]), f"{r['threshold']:.2f}"]
        for _, r in product_rows.iterrows()
    ], widths=[1.2, 0.75, 0.8, 0.8, 0.72, 1.25, 0.65], font_size=8.5)
    paragraph(document, "Cash loans y Revolving loans tienen políticas de umbral independientes. Crédito hipotecario no se activa todavía porque el dataset actual no contiene casos hipotecarios etiquetados para entrenar y validar una política propia.")

    document.add_heading("Cambios implementados y verificaciones", level=1)
    for text in [
        "Se añadió ruido gaussiano opcional de entrada para experimentos de regularización. Este ruido actúa únicamente durante entrenamiento.",
        "Se creó una búsqueda reproducible que guarda la configuración, semillas, épocas, pérdidas y métricas de cada corrida.",
        "Se conservaron el ensamble y los umbrales que ganaron con evidencia. No se promovió ninguna variante inferior.",
        "Se verificó la compilación de módulos Python, inferencia directa por producto, git diff check y build de producción del frontend.",
        "La política y el bundle estático fueron publicados en GitHub Pages sin cambios visuales de interfaz.",
    ]:
        p = document.add_paragraph(style="Normal")
        p.style = document.styles["Normal"]
        p.paragraph_format.left_indent = Inches(0.2)
        p.add_run("• " + text)

    document.add_heading("Archivos reproducibles", level=1)
    paragraph(document, "Los resultados de este documento pueden verificarse con reports/phase5_generalization_validation.csv, reports/phase5_generalization_epochs.csv, reports/phase5_generalization_test.csv, reports/phase4_score32_candidate_comparison.csv y src/phase5_generalization_search.py. El informe fuente en Markdown está en docs/INFORME_TECNICO_MODELO_FASE5.md.")

    document.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
