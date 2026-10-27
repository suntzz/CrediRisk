import json
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

def build_variables_pdf():
    with open("frontend/public/api-static/model_bundle.json") as f:
        bundle = json.load(f)
    prep = bundle["preprocessor"]
    imp_df = pd.read_csv("reports/importancia_variables.csv")
    imp_map = dict(zip(imp_df["variable"], imp_df["peso_relativo_pct"]))
    auc_drop_map = dict(zip(imp_df["variable"], imp_df["caida_auc"]))

    out_files = [
        "VARIABLES_TOTALES_CREDIRISK.pdf",
        "docs/VARIABLES_TOTALES_CREDIRISK.pdf"
    ]

    for out_path in out_files:
        doc = SimpleDocTemplate(
            out_path,
            pagesize=landscape(letter),
            leftMargin=0.45 * inch,
            rightMargin=0.45 * inch,
            topMargin=0.45 * inch,
            bottomMargin=0.45 * inch,
            title="Catálogo Completo de Variables — CrediRisk",
            author="Equipo CrediRisk"
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "DocSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#475569"),
            spaceAfter=10
        )
        sec_style = ParagraphStyle(
            "SecHead",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1D4ED8"),
            spaceBefore=8,
            spaceAfter=6
        )
        cell_style = ParagraphStyle(
            "Cell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10,
            textColor=colors.HexColor("#0F172A")
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=cell_style,
            fontName="Helvetica-Bold"
        )
        hdr_style = ParagraphStyle(
            "Hdr",
            parent=cell_style,
            fontName="Helvetica-Bold",
            fontSize=8.0,
            leading=10,
            textColor=colors.white
        )

        story = []

        # HEADER
        story.append(Paragraph("CATÁLOGO MAESTRO DE VARIABLES TOTALES — PROYECTO CREDIRISK", title_style))
        story.append(Paragraph(
            "Desglose completo de las <b>26 columnas del Dataset Original</b> (DatasetCreditoFinancieroFinalV2.csv, N = 49,650), "
            "las <b>23 variables predictoras base</b> con su peso de importancia y el catálogo exacto de las "
            "<b>44 variables finales normalizadas</b> que ingresan al Ensamble de Redes Neuronales MLP.",
            subtitle_style
        ))

        # SUMMARY KPI BOXES TABLE
        summary_data = [
            [
                Paragraph("<b>26 Columnas en el CSV Original</b><br/>1 ID + 1 Auxiliar excluida + 1 Objetivo + 23 Predictoras Base", cell_style),
                Paragraph("<b>23 Variables Predictoras Base</b><br/>19 Numéricas Financieras/Crediticias + 4 Categóricas (Texto)", cell_style),
                Paragraph("<b>+7 Banderas Binarias (_nan)</b><br/>Capturan ausencia informativa antes de imputar la mediana", cell_style),
                Paragraph("<b>+18 Variables One-Hot (Dummies)</b><br/>Expansión sin orden artificial de las 4 variables categóricas", cell_style),
                Paragraph("<b>= 44 Variables Finales (Tensor X)</b><br/>19 Numéricas + 7 Banderas _nan + 18 One-Hot estandarizadas (Z-score)", cell_style),
            ]
        ]
        sum_tbl = Table(summary_data, colWidths=[2.02 * inch] * 5)
        sum_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#2563EB")),
            ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#BFDBFE")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(sum_tbl)
        story.append(Spacer(1, 8))

        # =====================================================================
        # PARTE 1: LAS 26 COLUMNAS ORIGINALES DEL DATASET Y SU IMPORTANCIA
        # =====================================================================
        story.append(Paragraph("1. Las 26 Columnas del Dataset Original (23 Predictoras Base + 1 Objetivo + 2 Excluidas)", sec_style))

        raw_descriptions = {
            "score_crediticio": ("Numérica Continua", "Puntaje de buró crediticio del solicitante (300 a 850).", "Recorte [p1, p99] + Mediana + Z-Score"),
            "tasa_interes_ea": ("Numérica Continua", "Tasa de interés efectiva anual (%) asignada a la operación.", "Recorte [p1, p99] + Mediana + Z-Score"),
            "numero_creditos_activos": ("Numérica Discreta", "Cantidad de créditos vigentes en el sistema financiero.", "Bandera _nan + Recorte + log1p + Mediana + Z-Score"),
            "porcentaje_pagos_oportunos": ("Numérica Continua", "Porcentaje histórico de pagos realizados a tiempo (0% a 100%).", "Bandera _nan + Recorte + Mediana + Z-Score"),
            "tipo_contrato": ("Categórica (Texto)", "Situación laboral (Working, Commercial associate, Pensioner, State servant, Otro).", "Agrupación <1% en 'Otro' + One-Hot (5 cols) + Z-Score"),
            "antiguedad_cliente_anios": ("Numérica Continua", "Años de vinculación histórica con la entidad financiera.", "Bandera _nan + Recorte + Mediana + Z-Score"),
            "linea_negocio": ("Categórica (Texto)", "Modalidad del producto crediticio (Cash loans vs Revolving loans).", "One-Hot Encoding (2 cols) + Z-Score"),
            "plazo_meses": ("Numérica Discreta", "Plazo solicitado para amortizar el crédito (en meses).", "Recorte [p1, p99] + Mediana + Z-Score"),
            "patrimonio_indice": ("Numérica Continua", "Índice compuesto de respaldo patrimonial y activos del cliente.", "Recorte [p1, p99] + Mediana + Z-Score"),
            "monto_solicitado": ("Numérica Continua", "Valor monetario del préstamo solicitado por el cliente.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
            "saldo_total_creditos": ("Numérica Continua", "Deuda total acumulada en créditos actuales.", "Bandera _nan + Recorte + log1p + Mediana + Z-Score"),
            "antiguedad_laboral_anios": ("Numérica Continua", "Años de estabilidad en el empleo o actividad económica actual.", "Bandera _nan + Recorte + Mediana + Z-Score"),
            "edad": ("Numérica Discreta", "Edad del solicitante en años cumplidos al momento de la solicitud.", "Recorte [p1, p99] + Mediana + Z-Score"),
            "estado_civil": ("Categórica (Texto)", "Estado civil (Married, Single / not married, Civil marriage, Separated, Widow).", "One-Hot Encoding (5 cols) + Z-Score"),
            "dias_maximo_mora": ("Numérica Discreta", "Máximo histórico de días de atraso registrados por el solicitante.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
            "nivel_endeudamiento_pct": ("Numérica Continua", "Relación deuda/ingreso expresada en porcentaje.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
            "obligaciones_mensuales": ("Numérica Continua", "Gasto mensual fijo destinado al pago de deudas vigentes.", "Bandera _nan + Recorte + log1p + Mediana + Z-Score"),
            "numero_cuotas_mora": ("Numérica Discreta", "Cantidad de cuotas vencidas o en mora registradas.", "Bandera _nan + Recorte + log1p + Mediana + Z-Score"),
            "ingreso_mensual": ("Numérica Continua", "Ingreso mensual bruto percibido por el solicitante.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
            "ingreso_disponible": ("Numérica Continua", "Flujo libre mensual (ingreso mensual menos obligaciones; puede ser negativo).", "Recorte [p1, p99] + signed_log + Mediana + Z-Score"),
            "cuota_estimada": ("Numérica Continua", "Valor estimado de la cuota mensual del nuevo crédito.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
            "tipo_vivienda": ("Categórica (Texto)", "Tenencia de vivienda (House/apt, With parents, Municipal, Rented, Office, Co-op).", "One-Hot Encoding (6 cols) + Z-Score"),
            "personas_a_cargo": ("Numérica Discreta", "Número de dependientes económicos a cargo del solicitante.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
        }

        t1_rows = [[
            Paragraph("#", hdr_style),
            Paragraph("Nombre de la Columna", hdr_style),
            Paragraph("Rol en el Proyecto", hdr_style),
            Paragraph("Tipo de Variable", hdr_style),
            Paragraph("Descripción Funcional y Financiera", hdr_style),
            Paragraph("Tratamiento en Preprocesamiento", hdr_style),
            Paragraph("Peso Imp. (%)", hdr_style),
        ]]

        # 23 predictors ordered by importance
        ordered_predictors = list(imp_df["variable"])
        for idx, var_name in enumerate(ordered_predictors, 1):
            vtype, desc, proc = raw_descriptions[var_name]
            pct = imp_map.get(var_name, 0.0)
            drop_auc = auc_drop_map.get(var_name, 0.0)
            t1_rows.append([
                Paragraph(f"{idx:02d}", cell_bold),
                Paragraph(var_name, cell_bold),
                Paragraph("Predictora Base (Entrada)", cell_style),
                Paragraph(vtype, cell_style),
                Paragraph(desc, cell_style),
                Paragraph(proc, cell_style),
                Paragraph(f"<b>{pct:.2f}%</b> (ΔAUC {drop_auc:+.4f})", cell_style),
            ])

        # Add Target + 2 Excluded columns to complete all 26 columns of CSV
        extra_cols = [
            ("24", "APTO_PARA_CREDITO", "Variable Objetivo (Target Y)", "Binaria (0 / 1)", "Etiqueta real a predecir: 1 = Apto para crédito (50.0%), 0 = No Apto (50.0%).", "Separada en y_train, y_val, y_test", "Target (Y)"),
            ("25", "id_solicitud", "Excluida (Identificador)", "Entero Único", "Identificador consecutivo único del radicado de solicitud.", "Eliminada (No aporta señal predictiva)", "Excluida"),
            ("26", "INCUMPLIO_PAGO", "Excluida (Anti-Fuga)", "Binaria (0 / 1)", "Indicador post-crédito de incumplimiento.", "Eliminada estrictamente para evitar Data Leakage", "Excluida"),
        ]
        for num_s, cname, role, vtype, desc, proc, w_str in extra_cols:
            t1_rows.append([
                Paragraph(num_s, cell_bold),
                Paragraph(cname, cell_bold),
                Paragraph(role, cell_bold),
                Paragraph(vtype, cell_style),
                Paragraph(desc, cell_style),
                Paragraph(proc, cell_style),
                Paragraph(w_str, cell_bold),
            ])

        t1 = Table(
            t1_rows,
            colWidths=[0.35 * inch, 1.65 * inch, 1.25 * inch, 1.15 * inch, 2.75 * inch, 1.85 * inch, 1.10 * inch],
            repeatRows=1
        )
        t1_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#64748B")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]
        for r in range(1, len(t1_rows)):
            if r >= 24:
                t1_style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#FEF3C7")))
            elif r % 2 == 0:
                t1_style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F8FAFC")))
        t1.setStyle(TableStyle(t1_style))
        story.append(t1)

        story.append(PageBreak())

        # =====================================================================
        # PARTE 2: LAS 44 VARIABLES FINALES DE ENTRADA A LA RED NEURONAL
        # =====================================================================
        story.append(Paragraph("2. Catálogo Exacto de las 44 Variables Finales que Entran a la Red Neuronal (Tensor X de 44 Columnas)", sec_style))
        story.append(Paragraph(
            "Después de aplicar el preprocesador (fit exclusivamente sobre los 34,755 registros de Entrenamiento), "
            "las 23 variables predictoras base se convierten en estas <b>44 características numéricas estandarizadas</b> "
            "(26 en el bloque numérico/banderas + 18 en el bloque One-Hot):",
            subtitle_style
        ))

        t2_rows = [[
            Paragraph("Índice", hdr_style),
            Paragraph("Nombre Exacto de la Variable (44 Features)", hdr_style),
            Paragraph("Grupo / Familia", hdr_style),
            Paragraph("Variable Origen", hdr_style),
            Paragraph("Transformación Pre-Escalado", hdr_style),
            Paragraph("Límites Clipping [p1, p99] y Mediana (Train)", hdr_style),
            Paragraph("StandardScaler (Media μ | Desv σ)", hdr_style),
        ]]

        num_cols = prep["num_cols"]
        dummy_cols = prep["dummy_cols"]
        all_44 = num_cols + dummy_cols
        skew_set = set(prep["skew_cols"])
        signed_set = set(prep["signed_log_cols"])
        lo_map = prep["lo"]
        hi_map = prep["hi"]
        med_map = prep["median"]
        means = prep["scaler_mean"]
        scales = prep["scaler_scale"]

        for i, feat in enumerate(all_44):
            idx_num = i + 1
            mu = means[i]
            sd = scales[i]

            if feat.endswith("_nan"):
                base_v = feat.replace("_nan", "")
                grp = "2. Bandera de Nulo (_nan)"
                trans = "Indicador binario (1 si faltaba el dato, 0 si estaba presente)"
                clip_med_str = f"Mediana post-flag: {med_map.get(feat, 0.0):.0f} (Binaria 0/1)"
            elif feat in dummy_cols:
                if feat.startswith("estado_civil_"):
                    base_v = "estado_civil"
                elif feat.startswith("linea_negocio_"):
                    base_v = "linea_negocio"
                elif feat.startswith("tipo_contrato_"):
                    base_v = "tipo_contrato"
                else:
                    base_v = "tipo_vivienda"
                grp = "3. Categórica One-Hot"
                trans = "Codificación binaria One-Hot (1 si pertenece a la categoría, 0 si no)"
                clip_med_str = "Variable binaria {0, 1} (proporción en Train = μ)"
            else:
                base_v = feat
                grp = "1. Numérica Continua/Discreta"
                if feat in skew_set:
                    trans = "Clipping [p1, p99] → Transformación log1p(x) → Imputación Mediana"
                elif feat in signed_set:
                    trans = "Clipping [p1, p99] → Transformación sign(x)*log1p(|x|) → Mediana"
                else:
                    trans = "Clipping [p1, p99] → Escala original directa → Imputación Mediana"
                lo_v = lo_map.get(feat, 0.0)
                hi_v = hi_map.get(feat, 0.0)
                med_v = med_map.get(feat, 0.0)
                clip_med_str = f"p1={lo_v:,.2f} | p99={hi_v:,.2f} | Mediana={med_v:,.3f}"

            t2_rows.append([
                Paragraph(f"F{idx_num:02d}", cell_bold),
                Paragraph(feat, cell_bold),
                Paragraph(grp, cell_style),
                Paragraph(base_v, cell_style),
                Paragraph(trans, cell_style),
                Paragraph(clip_med_str, cell_style),
                Paragraph(f"μ = {mu:.4f} | σ = {sd:.4f}", cell_style),
            ])

        t2 = Table(
            t2_rows,
            colWidths=[0.45 * inch, 2.15 * inch, 1.35 * inch, 1.30 * inch, 2.05 * inch, 1.55 * inch, 1.25 * inch],
            repeatRows=1
        )
        t2_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#64748B")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
            ("LEFTPADDING", (0, 0), (-1, -1), 4.5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
        ]
        for r in range(1, len(t2_rows)):
            if 20 <= r <= 26:
                t2_style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#EFF6FF")))
            elif r >= 27:
                t2_style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#ECFDF5" if r % 2 == 0 else "#F0FDF4")))
            elif r % 2 == 0:
                t2_style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F8FAFC")))
        t2.setStyle(TableStyle(t2_style))
        story.append(t2)

        doc.build(story)
        print(f"Generated PDF: {os.path.abspath(out_path)} ({os.path.getsize(out_path):,} bytes)")

if __name__ == "__main__":
    build_variables_pdf()
