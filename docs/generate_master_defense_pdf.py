import json
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
)

def make_callout(title, body_lines, bg_hex="#EFF6FF", border_hex="#2563EB", title_hex="#1D4ED8"):
    styles = getSampleStyleSheet()
    t_style = ParagraphStyle(
        "CallTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=9.5, leading=13, textColor=colors.HexColor(title_hex), spaceAfter=3
    )
    b_style = ParagraphStyle(
        "CallBody", parent=styles["Normal"], fontName="Helvetica",
        fontSize=8.8, leading=12.2, textColor=colors.HexColor("#1E293B"), spaceAfter=2
    )
    content = [Paragraph(title, t_style)]
    for line in body_lines:
        content.append(Paragraph(line, b_style))
    tbl = Table([[content]], colWidths=[7.2 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)),
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor(border_hex)),
        ("LINEBEFORE", (0, 0), (0, -1), 4.0, colors.HexColor(border_hex)),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return tbl

def make_table(headers, rows, col_widths, header_bg="#0F172A", highlight_rows=None):
    styles = getSampleStyleSheet()
    hdr_style = ParagraphStyle(
        "THdr", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=8.0, leading=10.2, textColor=colors.white
    )
    cell_style = ParagraphStyle(
        "TCell", parent=styles["Normal"], fontName="Helvetica",
        fontSize=7.8, leading=10.2, textColor=colors.HexColor("#0F172A")
    )
    cell_bold = ParagraphStyle(
        "TCellB", parent=cell_style, fontName="Helvetica-Bold"
    )

    data = [[Paragraph(h, hdr_style) for h in headers]]
    for r in rows:
        row_cells = []
        for idx, val in enumerate(r):
            st = cell_bold if idx == 0 else cell_style
            row_cells.append(Paragraph(str(val), st))
        data.append(row_cells)

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#475569")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for r_i in range(1, len(data)):
        if highlight_rows and r_i in highlight_rows:
            t_style.append(("BACKGROUND", (0, r_i), (-1, r_i), colors.HexColor("#DCFCE7")))
        elif r_i % 2 == 0:
            t_style.append(("BACKGROUND", (0, r_i), (-1, r_i), colors.HexColor("#F8FAFC")))
    tbl.setStyle(TableStyle(t_style))
    return tbl

def add_img(story, path, caption, width_in=6.8):
    styles = getSampleStyleSheet()
    cap_style = ParagraphStyle(
        "ImgCap", parent=styles["Normal"], fontName="Helvetica-Oblique",
        fontSize=8.0, leading=10.5, textColor=colors.HexColor("#475569"), alignment=1, spaceAfter=8
    )
    if os.path.exists(path):
        im = Image(path)
        aspect = im.imageHeight / float(im.imageWidth)
        im.drawWidth = width_in * inch
        im.drawHeight = (width_in * aspect) * inch
        im.hAlign = "CENTER"
        story.append(Spacer(1, 4))
        story.append(im)
        story.append(Paragraph(caption, cap_style))

def build_master_pdf():
    with open("frontend/public/api-static/model_bundle.json") as f:
        bundle = json.load(f)
    prep = bundle["preprocessor"]
    imp_df = pd.read_csv("reports/importancia_variables.csv")
    imp_map = dict(zip(imp_df["variable"], imp_df["peso_relativo_pct"]))
    auc_drop_map = dict(zip(imp_df["variable"], imp_df["caida_auc"]))

    out_paths = [
        "GUIA_MAESTRA_SUSTENTACION_CREDIRISK.pdf",
        "docs/GUIA_MAESTRA_SUSTENTACION_CREDIRISK.pdf"
    ]

    for out_path in out_paths:
        doc = SimpleDocTemplate(
            out_path,
            pagesize=letter,
            leftMargin=0.6 * inch,
            rightMargin=0.6 * inch,
            topMargin=0.55 * inch,
            bottomMargin=0.55 * inch,
            title="Guía Maestra de Sustentación — Todo lo que la Profesora Puede Preguntar (CrediRisk)",
            author="Equipo CrediRisk"
        )

        styles = getSampleStyleSheet()
        h_cover_sub = ParagraphStyle(
            "CoverSub", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=9.5, leading=12, textColor=colors.HexColor("#2563EB"), spaceAfter=4
        )
        h_cover_title = ParagraphStyle(
            "CoverTitle", parent=styles["Heading1"], fontName="Helvetica-Bold",
            fontSize=17.5, leading=21.5, textColor=colors.HexColor("#0F172A"), spaceAfter=6
        )
        h_cover_desc = ParagraphStyle(
            "CoverDesc", parent=styles["Normal"], fontName="Helvetica",
            fontSize=9.5, leading=13, textColor=colors.HexColor("#475569"), spaceAfter=10
        )
        h1_style = ParagraphStyle(
            "H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
            fontSize=13.5, leading=17, textColor=colors.HexColor("#0F172A"),
            spaceBefore=12, spaceAfter=6
        )
        h2_style = ParagraphStyle(
            "H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=10.8, leading=14, textColor=colors.HexColor("#1D4ED8"),
            spaceBefore=8, spaceAfter=4
        )
        p_style = ParagraphStyle(
            "BodyP", parent=styles["Normal"], fontName="Helvetica",
            fontSize=9.0, leading=12.8, textColor=colors.HexColor("#1E293B"), spaceAfter=5
        )
        b_style = ParagraphStyle(
            "BulletP", parent=p_style, leftIndent=12, firstLineIndent=-8, spaceAfter=3.5
        )

        story = []

        # =====================================================================
        # PORTADA / ENCABEZADO MAESTRO
        # =====================================================================
        story.append(Paragraph("DOCUMENTO MAESTRO DE SUSTENTACIÓN ACADÉMICA — PROYECTO CREDIRISK (DEEP LEARNING)", h_cover_sub))
        story.append(Paragraph("Guía Completa de Defensa: Términos Técnicos, Variables y One-Hot, Arquitectura de Capas y Neuronas, Comité de 3 Redes, Errores de Pruebas, Épocas y Curva de Aprendizaje", h_cover_title))
        story.append(Paragraph(
            "Equipo CrediRisk: <b>Leidy • Sharick • Laura Sofía • Iván Camilo • Cristian Camilo</b> | "
            "Dataset Oficial: <b>DatasetCreditoFinancieroFinalV2.csv (49,650 registros)</b> | "
            "Modelo Final: <b>Ensemble_Top3_Diverso (ROC-AUC Test = 0.74482 | Val = 0.75382)</b>",
            h_cover_desc
        ))

        story.append(make_callout(
            "¿QUÉ CONTIENE ESTE PDF? (ÍNDICE DE PREGUNTAS DE LA PROFESORA)",
            [
                "<b>Sección 1 — Diccionario Completo de Términos Técnicos:</b> Qué significa cada término (MLP, Neurona, Peso, Sesgo, ReLU, LeakyReLU, Sigmoide, Dropout, L2, Adam, Batch Size, Época, Early Stopping, ReduceLROnPlateau, Data Leakage, Semilla) explicado fácil y con su valor en nuestro proyecto.",
                "<b>Sección 2 — Las Variables Totales y One-Hot Encoding:</b> Cuántas columnas tenía el CSV (26), cuáles quitamos (2), cuáles son las 23 predictoras base, cuáles son exactamente las 18 variables One-Hot, por qué llegamos a 44 variables finales y las tablas completas de las 26 y 44 variables.",
                "<b>Sección 3 — Partición 70% / 15% / 15%:</b> Por qué dividimos en 34,755 (Train), 7,447 (Validación) y 7,448 (Test) y cómo garantizamos Cero Fuga de Datos.",
                "<b>Sección 4 — Cantidad de Capas y Neuronas (44 → 64 → 32 → 16 → 1):</b> Por qué esa cantidad de capas y neuronas, qué pregunta responde cada capa por dentro, y por qué NO escogimos más capas (4 o 5) ni más neuronas (128 o 256) demostrado con los errores reales de nuestras pruebas.",
                "<b>Sección 5 — Por qué usamos 3 Redes Neuronales y luego hacemos el Promedio:</b> Por qué cada una de las 3 redes tiene esa estructura, qué aporta cada una y por qué promediar sus probabilidades supera a cualquier red individual.",
                "<b>Sección 6 — Por qué escogimos esa Clase de Error y NO otros + Tabla de Errores de las Pruebas:</b> Por qué usamos Binary Cross-Entropy (Log Loss = 0.5963), Brier (0.2050), ROC-AUC (0.7448) y Matriz de Confusión (Accuracy = 67.48%, Error = 32.52%, FP = 15.76%, FN = 16.76%).",
                "<b>Sección 7 — Las 166 Pruebas, Épocas Entrenadas y Curva de Aprendizaje:</b> Por qué cada modelo paró en su época exacta (24, 44, 83, 55) y las 4 pruebas irrefutables de que el modelo APRENDIÓ y NO MEMORIZÓ.",
                "<b>Sección 8 — Banco de 15 Preguntas Directas de la Profesora con Respuestas Listas para Decir en Voz Alta.</b>"
            ]
        ))
        story.append(Spacer(1, 6))

        # =====================================================================
        # SECCIÓN 1: DICCIONARIO DE TÉRMINOS QUE LA PROFESORA PUEDE PREGUNTAR
        # =====================================================================
        story.append(Paragraph("1. Diccionario Completo de Términos que la Profesora Puede Preguntar", h1_style))
        story.append(Paragraph(
            "Si la profesora pregunta <i>«¿Qué significa X término y cómo lo usaron ustedes?»</i>, esta tabla tiene la definición sencilla para todo el mundo y la aplicación exacta en nuestro código:",
            p_style
        ))

        glossary_rows = [
            ["Perceptrón Multicapa (MLP / Red Densa)", "Es una red neuronal formada por varias capas de neuronas organizadas en fila (entrada, capas ocultas y salida), donde cada neurona se conecta con todas las de la capa anterior.", "Es el tipo de arquitectura de nuestras 3 redes: reciben las 44 variables tabulares del cliente y las procesan en forma de embudo hasta dar la probabilidad de crédito."],
            ["Neurona, Peso (w) y Sesgo (Bias b)", "Cada neurona hace una suma multiplicando cada dato de entrada por su importancia (Peso w), le suma un ajuste base (Sesgo b) y pasa el resultado por una función de activación: y = f(w·x + b).", "Nuestra red principal [64, 32, 16] tiene exactamente 113 neuronas (64+32+16+1) y 5,505 parámetros (5,392 pesos w + 113 sesgos b)."],
            ["Función de Activación: ReLU", "Fórmula: max(0, x). Si el resultado de la neurona es positivo lo deja pasar tal cual; si es negativo lo apaga en cero (0). Permite aprender relaciones curvas (no lineales).", "Es la activación de las capas ocultas en los Submodelos 1 y 3 ([64, 32, 16]). Sin ReLU, toda la red colapsaría en una simple regresión lineal."],
            ["Función de Activación: LeakyReLU (α = 0.1)", "Fórmula: max(0.1x, x). Igual que ReLU en los positivos, pero cuando el valor es negativo deja pasar un 10% (0.1x) en vez de clavar un cero absoluto.", "La usamos en el Submodelo 2 ([32, 16]). Evita que queden 'neuronas muertas' y conserva información cuando un cliente tiene flujo de caja negativo."],
            ["Función de Activación: Sigmoide (Salida)", "Fórmula: 1 / (1 + e^-z). Comprime cualquier número real (de -∞ a +∞) en un valor entre 0.00 (0%) y 1.00 (100%).", "Va únicamente en la última neurona (Capa de Salida) para entregar la probabilidad exacta de que el solicitante sea Apto (1)."],
            ["Época (Epoch), Batch Size e Iteración", "• Batch Size (Lote): Cuántos clientes estudia la red antes de corregir sus pesos.\n• Iteración: 1 corrección de pesos (1 lote).\n• Época: 1 vuelta completa a los 34,755 clientes de entrenamiento.", "Usamos Batch Size = 128 y 256. Con 256 clientes por lote, 1 época equivale a 34,755 / 256 = 136 actualizaciones de pesos por época."],
            ["Optimizador Adam y Learning Rate (lr)", "Adam es el motor matemático que ajusta los pesos en cada paso para bajar el error. El Learning Rate (lr) es el 'tamaño del paso' con el que corrige.", "Probamos SGD, RMSprop, AdamW y Adam. Ganó Adam con paso fino lr = 0.0005 (Submodelos 1 y 2) y lr = 0.001 (Submodelo 3)."],
            ["Overfitting (Memorización) vs. Generalización", "• Overfitting: El modelo se aprende de memoria los clientes de entrenamiento (error Train baja mucho, pero en datos nuevos Val sube).\n• Generalización: El modelo aprende reglas reales que funcionan en clientes nuevos.", "Nuestro modelo generalizó: en la mejor época el error Train (0.5929) y Val (0.5933) están separados por solo 0.0004, y en Test el AUC varió menos de 1% (-0.0090)."],
            ["Dropout (Apagado Aleatorio 0.15 y 0.20)", "Durante el entrenamiento apaga al azar el 15% o 20% de las neuronas en cada lote. En validación y producción se usan el 100% de las neuronas.", "Evita que una sola neurona memorice clientes específicos. En EXP_17 probamos quitar el Dropout (0.0) y el modelo memorizó de inmediato (AUC cayó a 0.7447)."],
            ["Regularización L2 (Weight Decay)", "Es un castigo matemático que se suma al error si los pesos (w) de las neuronas se vuelven demasiado grandes.", "La probamos en Fase 1 y Fase 2 (1e-5, 1e-4, 1e-3). Descubrimos que Dropout 0.15 por sí solo (o con L2 muy suave) daba mejor AUC que un L2 agresivo."],
            ["Early Stopping + restore_best_weights", "Vigilante que evalúa el conjunto de Validación al final de cada época. Si pasan N épocas (paciencia) sin mejorar el récord, detiene el entrenamiento y devuelve los pesos a la mejor época.", "Con paciencia de 10 a 12 épocas evitamos entrenar de más: por ejemplo, el Submodelo 1 entrenó hasta la época 44 pero restauró los pesos óptimos de la época 32."],
            ["ReduceLROnPlateau", "Cuando el modelo lleva 4–5 épocas estancado en una meseta sin mejorar, reduce el Learning Rate a la mitad (x0.5).", "Es como bajar la velocidad al estacionar un auto: permite dar pasos milimétricos al final del entrenamiento para asentarse en el mínimo error."],
            ["Normalización StandardScaler (Z-Score)", "A cada variable le resta su promedio (μ) y la divide por su desviación estándar (σ), dejando todas las 44 columnas con media 0 y desviación 1.", "Evita que variables en millones (monto_solicitado) aplasten a variables pequeñas (cuotas en mora de 0 a 5). Se ajustó SOLO en Train."],
            ["Data Leakage (Fuga de Datos)", "Error metodológico grave que ocurre cuando información del examen final (Test) o del futuro se filtra en el entrenamiento.", "Lo evitamos al 100%: eliminamos INCUMPLIO_PAGO (variable post-crédito) y ajustamos medianas, recortes y StandardScaler exclusivamente con el 70% de Train."],
            ["Semilla Aleatoria (Random Seed)", "Número fijo que controla el generador aleatorio para que la partición de datos y los pesos iniciales sean 100% reproducibles.", "Usamos seed = 42 para la partición y evaluamos la estabilidad de cada modelo entrenándolo en 5 semillas distintas: 42, 1, 7, 21 y 2026."]
        ]
        story.append(make_table(
            ["Término Técnico", "¿Qué significa en palabras sencillas?", "¿Cómo y por qué se usó en CrediRisk?"],
            glossary_rows,
            col_widths=[1.45 * inch, 2.75 * inch, 3.00 * inch]
        ))

        story.append(PageBreak())

        # =====================================================================
        # SECCIÓN 2: LAS VARIABLES TOTALES Y ONE-HOT ENCODING
        # =====================================================================
        story.append(Paragraph("2. Las Variables Totales: ¿Cuántas tomamos, cuáles son One-Hot y por qué son 44?", h1_style))
        story.append(Paragraph(
            "Una de las preguntas fijas de la profesora es: <b>«¿Cuántas variables tenía la base de datos, cuántas tomaron ustedes, cuáles son One-Hot y por qué a la red neuronal le entran 44?»</b> Aquí está la cuenta matemática exacta:",
            p_style
        ))

        story.append(make_callout(
            "LA ECUACIÓN EXACTA DE NUESTRAS VARIABLES (DE 26 A 23 Y DE 23 A 44)",
            [
                "• <b>1. El archivo CSV original (DatasetCreditoFinancieroFinalV2.csv) tiene 26 columnas en total.</b>",
                "• <b>2. Quitamos 2 columnas prohibidas/inútiles:</b> <b>id_solicitud</b> (porque el número de radicado no dice si alguien paga) e <b>INCUMPLIO_PAGO</b> (porque ocurre después de dar el crédito y usarla sería hacer trampa / Data Leakage).",
                "• <b>3. Separamos 1 columna como Variable Objetivo (Target Y):</b> <b>APTO_PARA_CREDITO</b> (vale 1 si es Apto [50%] y 0 si es No Apto [50%]).",
                "• <b>4. Nos quedan exactamente 23 Variables Predictoras Base que tomamos como entrada:</b> <b>19 variables numéricas</b> + <b>4 variables categóricas (de texto)</b>.",
                "• <b>5. ¿Cómo se convierten esas 23 variables en las 44 variables que entran a la primera capa de la red?</b>",
                "   <b>19 Numéricas limpias</b> + <b>7 Banderas de datos faltantes (_nan)</b> + <b>18 Columnas One-Hot Encoding</b> (que salen de las 4 de texto) = <b>44 VARIABLES FINALES</b>."
            ],
            bg_hex="#ECFDF5", border_hex="#059669", title_hex="#065F46"
        ))
        story.append(Spacer(1, 6))

        add_img(
            story,
            "docs/images/07_pipeline_datos.png",
            "Figura 1. Flujo de transformación desde el CSV original hasta las 44 características normalizadas que alimentan la red neuronal.",
            width_in=6.6
        )

        story.append(Paragraph("2.1 ¿Qué es One-Hot Encoding, por qué lo hicimos y cuáles son las 18 variables One-Hot?", h2_style))
        story.append(Paragraph(
            "Las redes neuronales solo pueden multiplicar números; no pueden multiplicar palabras como <i>'Casado'</i>, <i>'Soltero'</i> o <i>'Pensionado'</i>. "
            "<b>¿Por qué NO les pusimos números seguidos como Soltero = 1, Casado = 2, Divorciado = 3, Viudo = 4?</b> "
            "Porque si hiciéramos eso, la red neuronal creería matemáticamente que <i>Viudo (4) vale cuatro veces más que Soltero (1)</i> o que el promedio entre Soltero (1) y Divorciado (3) es Casado (2), lo cual no tiene ningún sentido.",
            p_style
        ))
        story.append(Paragraph(
            "<b>Solución — One-Hot Encoding (Codificación Binaria 0 / 1):</b> Creamos una columna independiente para cada categoría posible, donde solo se enciende con <b>1</b> la categoría que tiene el cliente y las demás quedan en <b>0</b>. Antes de hacerlo, en <b>tipo_contrato</b> agrupamos las categorías ultra-raras (que aparecían en menos del 1% de los clientes: <i>Student, Unemployed, Maternity leave, Businessman</i>) bajo la etiqueta <b>'Otro'</b> para evitar columnas vacías que causen ruido. Así, nuestras <b>4 variables de texto se convirtieron en estas 18 variables One-Hot exactas</b>:",
            p_style
        ))

        onehot_rows = [
            ["1. estado_civil\n(Variable de texto #1)", "5 columnas One-Hot\n(F27 a F31)", "1. estado_civil_Civil marriage (Unión libre — 10.69%)\n2. estado_civil_Married (Casado — 62.09%)\n3. estado_civil_Separated (Separado — 6.57%)\n4. estado_civil_Single / not married (Soltero — 16.19%)\n5. estado_civil_Widow (Viudo — 4.45%)", "Permite que cada estado civil tenga su propio peso independiente en la red según su estabilidad familiar/financiera."],
            ["2. linea_negocio\n(Variable de texto #2)", "2 columnas One-Hot\n(F32 a F33)", "6. linea_negocio_Cash loans (Crédito de libre inversión/efectivo — 91.72%)\n7. linea_negocio_Revolving loans (Crédito rotativo/cupo — 8.28%)", "Distingue entre préstamos de desembolso fijo y líneas rotativas, que tienen comportamientos de pago muy diferentes."],
            ["3. tipo_contrato\n(Variable de texto #3)", "5 columnas One-Hot\n(F34 a F38)", "8. tipo_contrato_Commercial associate (Socio/Independiente — 22.65%)\n9. tipo_contrato_Otro (Agrupación <1%: Estudiante/Desempleado — 0.04%)\n10. tipo_contrato_Pensioner (Pensionado — 15.27%)\n11. tipo_contrato_State servant (Funcionario público — 6.19%)\n12. tipo_contrato_Working (Empleado asalariado — 55.86%)", "Es la 5.ª variable más importante del modelo (2.69% del peso total): un pensionado o empleado estatal tiene flujo mucho más predecible."],
            ["4. tipo_vivienda\n(Variable de texto #4)", "6 columnas One-Hot\n(F39 a F44)", "13. tipo_vivienda_Co-op apartment (Cooperativa — 0.40%)\n14. tipo_vivienda_House / apartment (Casa o apto propio/familiar — 87.02%)\n15. tipo_vivienda_Municipal apartment (Vivienda municipal — 3.83%)\n16. tipo_vivienda_Office apartment (Apto estudio/oficina — 0.85%)\n17. tipo_vivienda_Rented apartment (Arriendo — 1.94%)\n18. tipo_vivienda_With parents (Vive con los padres — 5.96%)", "Captura el respaldo habitacional y si el cliente tiene presión adicional por pago de arriendo."]
        ]
        story.append(make_table(
            ["Variable Categórica Original", "Cuántas Columnas Genera", "Nombre Exacto de las 18 Variables One-Hot (% en Train)", "¿Qué le aporta a la Red Neuronal?"],
            onehot_rows,
            col_widths=[1.35 * inch, 1.15 * inch, 2.85 * inch, 1.85 * inch]
        ))
        story.append(Spacer(1, 6))

        story.append(Paragraph("2.2 ¿Por qué creamos las 7 Banderas Binarias de Nulos (_nan)?", h2_style))
        story.append(Paragraph(
            "En 7 variables crediticias e históricas había clientes con celdas vacías (NaN). En lugar de simplemente rellenarlas con la mediana y borrar la huella, creamos <b>7 columnas binarias (_nan) que valen 1 si el dato venía vacío y 0 si venía lleno</b>: "
            "<i>saldo_total_creditos_nan, numero_creditos_activos_nan, antiguedad_laboral_anios_nan, antiguedad_cliente_anios_nan, porcentaje_pagos_oportunos_nan, obligaciones_mensuales_nan y numero_cuotas_mora_nan</i>. "
            "<b>¿Por qué?</b> Porque en finanzas la ausencia de un dato es una señal en sí misma (por ejemplo, un cliente sin saldo de créditos previos o sin antigüedad reportada tiene un perfil distinto al de un cliente promedio).",
            p_style
        ))

        story.append(Paragraph("2.3 Prueba Científica (Estudio de Ablación): ¿Cómo demostramos que 44 variables era el número perfecto?", h2_style))
        story.append(Paragraph(
            "Si la profesora pregunta: <i>«¿Por qué 44 variables y no menos o más?»</i>, le mostramos nuestro <b>Estudio de Ablación</b> (registrado en <b>reports/ablation_study.csv</b>), donde entrenamos la misma red quitando y agregando grupos de variables:",
            p_style
        ))

        ablation_rows = [
            ["Set C: Solo Financieras Básicas", "9 variables", "0.62789", "0.6691", "59.02%", "40.98%", "Sin historial crediticio (score, mora) el modelo pierde casi toda su capacidad."],
            ["Set D: Financieras + Comportamiento", "21 variables", "0.74409", "0.5975", "68.35%", "31.65%", "Al incluir score y mora da un gran salto, pero aún le faltan las One-Hot y banderas _nan."],
            ["Set B: Sin 4 Variables Menores", "35 variables", "0.75202", "0.5910", "68.75%", "31.25%", "Buen rendimiento, pero ligeramente inferior en AUC al conjunto completo de 44."],
            ["Set A: Nuestras 44 Variables Canónicas", "44 variables", "0.75225", "0.5909", "68.71%", "31.29%", "¡PUNTO ÓPTIMO! Alcanza el mejor ROC-AUC combinando las 19 numéricas + 7 _nan + 18 One-Hot."],
            ["Set E: 44 Variables + 6 Ratios Manuales", "50 variables", "0.75180", "0.5904", "68.81%", "31.19%", "Meter 6 divisiones financieras a mano NO sube el AUC, porque las 64 neuronas de la Capa 1 ya aprenden esos cruces solas."]
        ]
        story.append(make_table(
            ["Experimento de Ablación", "N.° Variables", "Val ROC-AUC", "Error Log Loss", "Accuracy", "Error %", "Conclusión Científica para la Profesora"],
            ablation_rows,
            col_widths=[1.45 * inch, 0.72 * inch, 0.75 * inch, 0.75 * inch, 0.65 * inch, 0.63 * inch, 2.25 * inch],
            highlight_rows=[4]
        ))

        story.append(PageBreak())

        # TABLA COMPLETA DE LAS 26 COLUMNAS ORIGINALES Y LAS 44 FINALES
        story.append(Paragraph("2.4 Tabla Completa de las 26 Columnas del CSV Original y Peso de Importancia de las 23 Predictoras", h2_style))
        raw_descriptions = {
            "score_crediticio": ("Numérica", "Puntaje de buró crediticio (300–850). Es la variable reina del modelo.", "Recorte [p1, p99] + Mediana + Z-Score"),
            "tasa_interes_ea": ("Numérica", "Tasa de interés efectiva anual (%) asignada al crédito.", "Recorte [p1, p99] + Mediana + Z-Score"),
            "numero_creditos_activos": ("Numérica", "Cantidad de créditos vigentes en el sistema financiero.", "Bandera _nan + Recorte + log1p + Mediana + Z-Score"),
            "porcentaje_pagos_oportunos": ("Numérica", "Porcentaje histórico de pagos realizados a tiempo (0–100%).", "Bandera _nan + Recorte + Mediana + Z-Score"),
            "tipo_contrato": ("Categórica", "Situación laboral (Working, Commercial associate, Pensioner, State servant, Otro).", "Agrupación <1% en 'Otro' + One-Hot (5 cols) + Z-Score"),
            "antiguedad_cliente_anios": ("Numérica", "Años de vinculación histórica con la entidad financiera.", "Bandera _nan + Recorte + Mediana + Z-Score"),
            "linea_negocio": ("Categórica", "Modalidad del crédito (Cash loans vs Revolving loans).", "One-Hot Encoding (2 cols) + Z-Score"),
            "plazo_meses": ("Numérica", "Plazo solicitado en meses (12 a 60 meses).", "Recorte [p1, p99] + Mediana + Z-Score"),
            "patrimonio_indice": ("Numérica", "Índice de respaldo patrimonial y activos del solicitante.", "Recorte [p1, p99] + Mediana + Z-Score"),
            "monto_solicitado": ("Numérica", "Valor monetario del préstamo solicitado.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
            "saldo_total_creditos": ("Numérica", "Deuda total acumulada en créditos actuales.", "Bandera _nan + Recorte + log1p + Mediana + Z-Score"),
            "antiguedad_laboral_anios": ("Numérica", "Años de estabilidad en el empleo actual.", "Bandera _nan + Recorte + Mediana + Z-Score"),
            "edad": ("Numérica", "Edad del solicitante en años cumplidos.", "Recorte [p1, p99] + Mediana + Z-Score"),
            "estado_civil": ("Categórica", "Estado civil (Married, Single, Civil marriage, Separated, Widow).", "One-Hot Encoding (5 cols) + Z-Score"),
            "dias_maximo_mora": ("Numérica", "Máximo histórico de días de atraso registrados.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
            "nivel_endeudamiento_pct": ("Numérica", "Relación deuda/ingreso en porcentaje.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
            "obligaciones_mensuales": ("Numérica", "Gasto mensual destinado al pago de deudas vigentes.", "Bandera _nan + Recorte + log1p + Mediana + Z-Score"),
            "numero_cuotas_mora": ("Numérica", "Cantidad de cuotas vencidas o en mora registradas.", "Bandera _nan + Recorte + log1p + Mediana + Z-Score"),
            "ingreso_mensual": ("Numérica", "Ingreso mensual bruto del solicitante.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
            "ingreso_disponible": ("Numérica", "Flujo libre mensual (ingreso menos obligaciones; puede ser negativo).", "Recorte [p1, p99] + signed_log + Mediana + Z-Score"),
            "cuota_estimada": ("Numérica", "Valor estimado de la cuota mensual del nuevo préstamo.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
            "tipo_vivienda": ("Categórica", "Tenencia de vivienda (House/apt, With parents, Municipal, Rented, Office, Co-op).", "One-Hot Encoding (6 cols) + Z-Score"),
            "personas_a_cargo": ("Numérica", "Número de dependientes económicos a cargo.", "Recorte [p1, p99] + log1p + Mediana + Z-Score"),
        }

        t26_rows = []
        for i, vname in enumerate(imp_df["variable"], 1):
            vtype, desc, proc = raw_descriptions[vname]
            pct = imp_map[vname]
            t26_rows.append([f"{i:02d}. {vname}", "Predictora Base", vtype, desc, proc, f"{pct:.2f}%"])
        t26_rows.append(["24. APTO_PARA_CREDITO", "Variable Objetivo (Y)", "Binaria 0/1", "Respuesta real que aprende la red: 1 = Apto (50%), 0 = No Apto (50%).", "Separada en y_train, y_val, y_test", "Target (Y)"])
        t26_rows.append(["25. id_solicitud", "Excluida (ID)", "Entero", "Número consecutivo del trámite.", "Eliminada (sin valor predictivo)", "Excluida"])
        t26_rows.append(["26. INCUMPLIO_PAGO", "Excluida (Anti-Fuga)", "Binaria 0/1", "Evento posterior al otorgamiento del crédito.", "Eliminada para evitar Data Leakage", "Excluida"])

        story.append(make_table(
            ["Columna del CSV", "Rol", "Tipo", "Significado Financiero", "Transformación Aplicada", "Importancia"],
            t26_rows,
            col_widths=[1.45 * inch, 0.92 * inch, 0.65 * inch, 2.08 * inch, 1.45 * inch, 0.65 * inch],
            highlight_rows=[1, 2, 3]
        ))

        story.append(PageBreak())

        story.append(Paragraph("2.5 Listado Completo de las 44 Variables Finales que Entran a la Red Neuronal (F01 a F44)", h2_style))
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

        t44_rows = []
        for idx, feat in enumerate(all_44):
            f_code = f"F{idx+1:02d}"
            mu, sd = means[idx], scales[idx]
            if feat.endswith("_nan"):
                grp = "2. Bandera _nan"
                orig = feat.replace("_nan", "")
                tr_txt = "Binaria 1 si faltaba dato, 0 si estaba"
                stat_txt = f"Proporción vacío en Train = {mu*100:.2f}%"
            elif feat in dummy_cols:
                grp = "3. One-Hot (0/1)"
                orig = "estado_civil" if feat.startswith("estado_civil_") else ("linea_negocio" if feat.startswith("linea_negocio_") else ("tipo_contrato" if feat.startswith("tipo_contrato_") else "tipo_vivienda"))
                tr_txt = "Binaria 1 si pertenece a categoría, 0 si no"
                stat_txt = f"Frecuencia en Train = {mu*100:.2f}%"
            else:
                grp = "1. Numérica"
                orig = feat
                if feat in skew_set:
                    tr_txt = "Clipping [p1,p99] + log1p + Mediana"
                elif feat in signed_set:
                    tr_txt = "Clipping [p1,p99] + signed_log + Mediana"
                else:
                    tr_txt = "Clipping [p1,p99] + Directa + Mediana"
                stat_txt = f"p1={lo_map[feat]:,.1f} | p99={hi_map[feat]:,.1f} | Med={med_map[feat]:,.1f}"
            t44_rows.append([f"{f_code}: {feat}", grp, orig, tr_txt, stat_txt, f"μ={mu:.3f}, σ={sd:.3f}"])

        story.append(make_table(
            ["Variable Final (F01–F44)", "Familia", "Columna Madre", "Fórmula Pre-Escalado", "Estadísticos en Train", "StandardScaler (Z)"],
            t44_rows,
            col_widths=[1.68 * inch, 0.85 * inch, 1.05 * inch, 1.42 * inch, 1.32 * inch, 0.88 * inch]
        ))

        story.append(PageBreak())

        # =====================================================================
        # SECCIÓN 3: PARTICIÓN 70 / 15 / 15
        # =====================================================================
        story.append(Paragraph("3. ¿Por qué hicimos la Proporción 70% Entrenamiento / 15% Validación / 15% Prueba?", h1_style))
        story.append(Paragraph(
            "Dividimos las <b>49,650 solicitudes</b> con partición estratificada (manteniendo exactamente 50.0% Aptos y 50.0% No Aptos en cada grupo con semilla fija 42) en tres bloques independientes por 4 razones científicas:",
            p_style
        ))
        story.append(Paragraph("• <b>1. ¿Por qué 3 bloques y NO solo 2 (Train y Test)?</b> Porque hicimos <b>166 pruebas</b> y usamos <i>Early Stopping</i> época tras época. Si hubiéramos usado el conjunto de Test para decidir en qué época parar y qué arquitectura elegir, habríamos contaminado el examen final. Por eso creamos un juez intermedio (<b>Validación = 15%</b>) y dejamos el conjunto de <b>Test (15%)</b> sellado bajo llave hasta el final.", b_style))
        story.append(Paragraph("• <b>2. ¿Por qué 70% para Entrenamiento (34,755 clientes)?</b> Porque nuestra red neuronal principal tiene <b>5,505 parámetros</b>. Con 34,755 clientes tenemos <b>6.3 clientes reales por cada peso de la red</b> (y 136 lotes de 256 clientes por época), volumen ideal para que la red aprenda relaciones complejas sin quedarse corta de datos.", b_style))
        story.append(Paragraph("• <b>3. ¿Por qué 15% y 15% simétricos (7,447 y 7,448 clientes)?</b> Porque casi 7,500 clientes por bloque garantizan un margen de error estadístico menor a ±1.1%. Además, al tener exactamente el mismo tamaño y el mismo balance 50/50, podemos comparar justamente el resultado de Validación (AUC 0.7538) contra el de Test (AUC 0.7448).", b_style))
        story.append(Paragraph("• <b>4. Cero Fuga de Datos (Zero Data Leakage):</b> El método <i>Preprocessor().fit()</i> (que calcula los percentiles p1 y p99, las medianas de imputación y la media/desviación del StandardScaler) se ejecutó <b>exclusivamente sobre los 34,755 registros del 70% de Entrenamiento</b>.", b_style))

        # =====================================================================
        # SECCIÓN 4: CAPAS Y NEURONAS — POR QUÉ ESA CANTIDAD Y QUÉ REPRESENTA CADA CAPA
        # =====================================================================
        story.append(Paragraph("4. Capas y Neuronas: ¿Por qué esa cantidad, qué representa cada capa y por qué NO pusimos más capas?", h1_style))
        story.append(Paragraph(
            "Esta es una de las preguntas más importantes de la profesora: <b>«¿Por qué su red principal tiene 3 capas ocultas de [64, 32, 16] neuronas, por qué la segunda red tiene 2 capas de [32, 16], qué hace cada capa por dentro y por qué no pusieron 4, 5 o más capas con 128 o 256 neuronas?»</b>",
            p_style
        ))

        story.append(Paragraph("4.1 ¿Qué representa y qué preguntas responde cada capa por dentro? (El Embudo 44 → 64 → 32 → 16 → 1)", h2_style))
        layers_meaning = [
            ["Capa de Entrada\n(44 Variables)", "0 parámetros\n(Tensor X)", "Entrega la radiografía limpia del cliente", "Recibe las 44 características ya estandarizadas en escala Z-Score (media 0, desviación 1): 19 numéricas + 7 banderas _nan + 18 One-Hot."],
            ["Capa Oculta 1\n(64 Neuronas)\nReLU + Dropout", "(44 × 64) + 64 =\n2,880 parámetros\n(52.3% de la red)", "EXPANSIÓN Y CRUCES DIRECTOS\n(Los 64 Analistas Junior)", "¿Por qué sube de 44 a 64? Porque una variable sola no basta. Necesitamos 64 detectores para formar 64 combinaciones directas de 2 o 3 variables:\n• ¿La cuota_estimada y monto_solicitado superan su ingreso_mensual?\n• ¿Tiene buen score_crediticio pero tasa_interes_ea muy alta?\n• ¿Combina dias_maximo_mora altos con bajo porcentaje_pagos_oportunos?\n• ¿Qué tan estable es su tipo_contrato junto con su antiguedad_laboral?\n• ¿Las banderas _nan indican falta de historial crediticio?"],
            ["Capa Oculta 2\n(32 Neuronas)\nReLU + Dropout", "(64 × 32) + 32 =\n2,080 parámetros\n(37.8% de la red)", "SÍNTESIS Y RESOLUCIÓN DE CONTRADICCIONES\n(Los 32 Coordinadores)", "¿Por qué baja a la mitad (de 64 a 32)? Para comprimir los 64 cruces básicos y resolver contradicciones financieras:\n• Ej. 1: 'Gana muy buen sueldo y tiene vivienda propia (señal positiva de Capa 1), PERO tiene muchos créditos activos y mora reciente (señal negativa). ¿Qué pesa más?'\n• Ej. 2: 'Tiene ingreso moderado, PERO lleva 10 años de antigüedad con 100% de pagos oportunos.'"],
            ["Capa Oculta 3\n(16 Neuronas)\nReLU", "(32 × 16) + 16 =\n528 parámetros\n(9.6% de la red)", "DESTILACIÓN EJECUTIVA / CUELLO DE BOTELLA\n(Los 16 Directores)", "¿Por qué baja otra vez a la mitad (de 32 a 16)? Es un cuello de botella intencional: obliga a la red a resumir toda la historia del cliente en solo 16 señales maestras de solvencia y riesgo. Al ser solo 16 neuronas, la red NO tiene espacio para memorizar ruido ni casos particulares."],
            ["Capa de Salida\n(1 Neurona)\nSigmoide", "(16 × 1) + 1 =\n17 parámetros\n(0.3% de la red)", "VEREDICTO PROBABILÍSTICO\n(El Gerente General)", "Toma las 16 señales ejecutivas de la Capa 3, las pondera y aplica la función Sigmoide 1/(1+e^-z) para entregar un único número continuo entre 0.00 (0%) y 1.00 (100%). Si es ≥ 0.50 → Apto (1); si es < 0.50 → No Apto (0)."]
        ]
        story.append(make_table(
            ["Capa de la Red", "Parámetros Exactos", "Rol en la Arquitectura", "¿Qué preguntas responde y por qué tiene ese número de neuronas?"],
            layers_meaning,
            col_widths=[1.15 * inch, 1.05 * inch, 1.45 * inch, 3.55 * inch],
            highlight_rows=[2, 3, 4]
        ))
        story.append(Spacer(1, 6))

        story.append(Paragraph("4.2 ¿Por qué NO escogimos MÁS capas (4 o 5 capas) ni MÁS neuronas (96, 128, 160)? (Demostración con los errores de nuestras pruebas)", h2_style))
        story.append(Paragraph(
            "No adivinamos el tamaño `[64, 32, 16]` ni `[32, 16]`: en la <b>Fase 1 (reports/experiments.csv)</b> construimos y entrenamos redes más anchas y de más capas (4 capas con 128 y 160 neuronas). <b>¿Qué pasó cuando metimos más capas y más neuronas? ¡El modelo empeoró porque empezó a memorizar!</b> Mira la tabla real de pruebas:",
            p_style
        ))

        arch_exp_rows = [
            ["EXP_34 (Ganadora 3 Capas)", "[64, 32, 16]", "3 capas", "5,505", "0.5869", "0.5909", "0.75225", "31.29%", "¡PUNTO DULCE! 6.3 clientes por parámetro: aprende todos los cruces sin sobreajustar."],
            ["EXP_37 (Ganadora 2 Capas)", "[32, 16] LeakyReLU", "2 capas", "1,985", "0.5862", "0.5894", "0.75224", "30.93%", "¡EXCELENTE! Compacta (17.5 clientes por parámetro), logra el menor Val Loss (0.5894)."],
            ["EXP_03 (Intermedia 2 Capas)", "[48, 24]", "2 capas", "3,361", "0.5829", "0.5911", "0.75082", "31.29%", "Buena, pero con ReLU estándar capta un poco menos de señal que [64, 32, 16]."],
            ["EXP_36 (Muy estrecha al final)", "[48, 24, 12]", "3 capas", "3,649", "0.5869", "0.5941", "0.74764", "31.49%", "Bajar hasta 12 neuronas comprime demasiado (cuello de botella excesivo, pierde información)."],
            ["EXP_05 (Ancha 3 Capas)", "[96, 48, 24]", "3 capas", "10,177", "0.5895", "0.5939", "0.74899", "31.57%", "Al duplicar los parámetros a 10,177, el error de validación sube a 0.5939 y el AUC cae."],
            ["EXP_06 (Muy Ancha 3 Capas)", "[128, 64, 32]", "3 capas", "16,129", "0.5872", "0.5945", "0.74927", "31.73%", "Con 16,129 parámetros empieza a memorizar ruido de Train y pierde precisión en Validación."],
            ["EXP_07 (Profunda 4 Capas)", "[128, 64, 32, 16]", "4 capas", "16,641", "0.5904", "0.5933", "0.75052", "31.78%", "Meter una 4.ª capa triplica los parámetros pero el error en Validación es peor que en 3 capas."],
            ["EXP_08 (Profunda Ancha 4 Capas)", "[128, 96, 48, 24]", "4 capas", "24,001", "0.5829", "0.5934", "0.74982", "31.34%", "Train Loss baja a 0.5829 pero Val Loss sube a 0.5934 (abre la brecha de memorización)."],
            ["EXP_09 (Gigante 4 Capas)", "[160, 96, 48, 24]", "4 capas", "28,513", "0.5897", "0.5939", "0.74897", "31.65%", "Con 28,513 parámetros se degrada ya en la época 11: demasiada capacidad para datos tabulares."]
        ]
        story.append(make_table(
            ["Experimento", "Capas y Neuronas", "N.° Capas", "Parámetros", "Train Loss", "Val Loss", "Val AUC", "Error Val %", "¿Por qué ocurrió este resultado?"],
            arch_exp_rows,
            col_widths=[1.12 * inch, 0.98 * inch, 0.52 * inch, 0.58 * inch, 0.55 * inch, 0.55 * inch, 0.55 * inch, 0.58 * inch, 1.77 * inch],
            highlight_rows=[1, 2]
        ))

        story.append(PageBreak())

        # =====================================================================
        # SECCIÓN 5: POR QUÉ 3 REDES Y POR QUÉ SE HACE EL PROMEDIO
        # =====================================================================
        story.append(Paragraph("5. ¿Por qué utilizamos 3 Redes Neuronales, por qué tienen esas capas y por qué luego se hace el Promedio?", h1_style))
        story.append(Paragraph(
            "Si la profesora pregunta: <b>«¿Por qué su modelo final no es una sola red sino 3 redes, por qué esas 3 tienen esas capas y neuronas, y por qué les sacan el promedio?»</b>, aquí tienes la explicación completa:",
            p_style
        ))

        add_img(
            story,
            "docs/images/06_arquitectura_ensamble_final.png",
            "Figura 2. Estructura exacta de las 3 Redes Neuronales que conforman nuestro Comité Ensamble Final (Ensemble_Top3_Diverso).",
            width_in=6.5
        )

        story.append(Paragraph("5.1 ¿Por qué cada una de las 3 redes tiene esa cantidad de capas y neuronas?", h2_style))
        story.append(Paragraph(
            "Para que un comité de expertos funcione en la vida real, <b>los 3 expertos NO pueden ser clones idénticos</b> (si los 3 piensan exactamente igual, se equivocan en los mismos clientes). Por eso elegimos a los <b>3 campeones con distinta personalidad matemática</b> de nuestras fases experimentales:",
            p_style
        ))

        ens3_rows = [
            ["Red 1: cfg_c_s42\n('El Analista Profundo Detallista')", "3 capas ocultas:\n[64, 32, 16]\n(5,505 parámetros)", "ReLU en ocultas\nSigmoide en salida", "Dropout = 0.15\nlr = 0.0005 (fino)\nSemilla = 42\nBest Epoch = 32 (de 44)", "Al tener 3 capas (64→32→16) y paso de aprendizaje lento (0.0005), detecta interacciones profundas de 3 niveles con alta precisión."],
            ["Red 2: cfg_b_leaky_s42\n('El Analista Compacto sin Neuronas Muertas')", "2 capas ocultas:\n[32, 16]\n(1,985 parámetros)", "LeakyReLU (α=0.1)\nSigmoide en salida", "Dropout = 0.15\nlr = 0.0005 (fino)\nSemilla = 42\nBest Epoch = 71 (de 83)", "Tiene casi la tercera parte de parámetros (1,985 vs 5,505) y solo 2 capas, por lo que es inmune al ruido complejo; además, su LeakyReLU no apaga a cero los valores negativos (como flujos de caja negativos)."],
            ["Red 3: cfg_base_s2026\n('El Analista Escéptico de Otra Semilla')", "3 capas ocultas:\n[64, 32, 16]\n(5,505 parámetros)", "ReLU en ocultas\nSigmoide en salida", "Dropout = 0.20 (alto)\nlr = 0.001 (rápido)\nSemilla = 2026\nBest Epoch = 45 (de 55)", "Aunque tiene 3 capas [64, 32, 16], nació con otra semilla aleatoria (2026) y se entrenó apagando más neuronas al azar (Dropout 20%), por lo que recorrió otro camino en el paisaje de error."]
        ]
        story.append(make_table(
            ["Nombre y Rol en el Comité", "Capas y Parámetros", "Activaciones", "Hiperparámetros y Épocas", "¿Por qué aporta un punto de vista distinto al Comité?"],
            ens3_rows,
            col_widths=[1.45 * inch, 1.10 * inch, 1.00 * inch, 1.25 * inch, 2.40 * inch],
            highlight_rows=[1, 2, 3]
        ))
        story.append(Spacer(1, 6))

        story.append(Paragraph("5.2 ¿Por qué luego se hace el Promedio Simple (1/3 + 1/3 + 1/3) de las 3 redes?", h2_style))
        story.append(Paragraph(
            "La probabilidad final que entrega CrediRisk es el promedio aritmético de las 3 redes: <b>p_final = (p_Red1 + p_Red2 + p_Red3) / 3</b>. Se hace así por <b>3 razones matemáticas demostradas en nuestros reportes</b>:",
            p_style
        ))
        story.append(Paragraph("• <b>1. Cancelación de errores individuales en casos fronterizos:</b> En <b>reports/correlacion_errores_phase3.csv</b> medimos qué tanto coincidían los errores de las redes y vimos que la correlación de desacuerdo está alrededor de <b>0.78–0.81</b> (no es 1.00). Es decir: cuando un cliente difícil está cerca del 50% y la Red 1 se equivoca por un poquito dando <i>0.47 (No Apto)</i>, pero la Red 2 (con LeakyReLU) ve su flujo de caja y da <i>0.55 (Apto)</i> y la Red 3 da <i>0.54 (Apto)</i>, el promedio da <b>(0.47 + 0.55 + 0.54) / 3 = 0.52 → ¡Acierto (Apto)!</b>", b_style))
        story.append(Paragraph("• <b>2. Reducción matemática de la varianza y mejor calibración (Log Loss y Brier):</b> En estadística, el promedio de 3 estimadores diversos reduce la varianza del error casi a la tercera parte en la componente no correlacionada. Por eso el Ensamble logra un <b>Log Loss de 0.5888 en Validación y 0.5963 en Test</b>, superando a cada una de las 3 redes por separado.", b_style))
        story.append(Paragraph("• <b>3. ¿Por qué promedio igual (1/3 cada una) y no promedio ponderado ni 5 o 10 redes?</b> En las Fases 1, 2 y 3 probamos <b>16 combinaciones de ensambles</b> (de 3, 4, 5, 6, 10 y 11 modelos, con pesos iguales y con pesos desiguales como 60%/20%/20%). Como muestra la tabla siguiente, el <b>Top-3 Diverso con pesos iguales (1/3 c/u) fue el campeón absoluto</b> porque darle pesos desiguales sobreajustaba la validación:", b_style))

        ens_comp_rows = [
            ["Baseline Individual ([64,32,16] inicial)", "1 red", "0.74969", "0.74243", "0.5992", "0.2062", "67.32%", "32.68%", "Punto de partida con una sola red sin afinar."],
            ["Mejor Red Individual Fase 1 (cfg_c_s42)", "1 red", "0.75225", "0.74373", "0.5979", "0.2056", "67.32%", "32.68%", "Mejoró el AUC (+0.0013 en Test), pero depende de 1 solo criterio."],
            ["Mejor Red Individual Fase 2 (con L2)", "1 red", "0.75250", "0.74336", "0.5980", "0.2057", "67.33%", "32.67%", "Buena en validación, pero una sola red tiene mayor varianza en Test."],
            ["Ensamble Misma Red con 5 Semillas", "5 redes iguales", "0.75249", "—", "0.5898 (Val)", "0.2022 (Val)", "68.66% (Val)", "31.34% (Val)", "Promediar la MISMA arquitectura 5 veces ayuda poco porque piensan muy parecido."],
            ["Ensamble Ponderado (6 redes pesos distintos)", "6 redes", "0.75372", "0.74420", "0.5967", "0.2052", "67.48%", "32.52%", "Poner pesos desiguales pierde un poco de generalización en Test."],
            ["ENSAMBLE FINAL TOP-3 DIVERSO (1/3 c/u)", "3 redes diversas", "0.75382", "0.74482", "0.5963", "0.2050", "67.48%", "32.52%", "¡CAMPEÓN! Mejor AUC en Val y Test, menor Log Loss y menor Brier Score."]
        ]
        story.append(make_table(
            ["Modelo / Ensamble Evaluado", "N.° Redes", "Val AUC", "Test AUC", "Test Log Loss", "Test Brier", "Test Acc %", "Test Error %", "Por qué se tomó la decisión"],
            ens_comp_rows,
            col_widths=[1.55 * inch, 0.65 * inch, 0.58 * inch, 0.58 * inch, 0.68 * inch, 0.58 * inch, 0.60 * inch, 0.62 * inch, 1.36 * inch],
            highlight_rows=[6]
        ))

        story.append(PageBreak())

        # =====================================================================
        # SECCIÓN 6: POR QUÉ ESCOGIMOS ESA CLASE DE ERROR Y NO OTROS
        # =====================================================================
        story.append(Paragraph("6. Explicación del Error: ¿Por qué escogimos esa clase de error, por qué NO otros y cuánto dio?", h1_style))
        story.append(Paragraph(
            "Si la profesora pregunta: <b>«¿Por qué escogieron Binary Cross-Entropy (Log Loss) para entrenar la red y por qué no usaron el Error Cuadrático Medio (MSE), el Error Absoluto (MAE) o simplemente el porcentaje de aciertos (Accuracy)?»</b>, aquí está la respuesta técnica y sencilla:",
            p_style
        ))

        err_choice_rows = [
            ["Binary Cross-Entropy\n(Log Loss = 0.5963)\n[SÍ LO ESCOGIMOS — Error de Entrenamiento]", "Fórmula: -[y·ln(p) + (1-y)·ln(1-p)].\n1. Es el único error que al combinarse con la neurona Sigmoide produce una derivada limpia (p - y) que no se estanca.\n2. Es un 'detector de arrogancia': si el modelo se equivoca diciendo que está 99% seguro, el logaritmo le aplica un castigo enorme, obligándolo a dar probabilidades honestas.", "Bajó de 0.6710 (inicio) y 0.6001 (Baseline) a 0.5888 en Validación y 0.5963 en Test (muy inferior al azar de 0.6931)."],
            ["Error Cuadrático Medio (MSE) o MAE\n[NO LO ESCOGIMOS para entrenar]", "¿Por qué NO usamos MSE o MAE como función de pérdida principal? Porque MSE y MAE son para Regresión (predecir el precio de una casa). Si usas MSE con una neurona Sigmoide en clasificación binaria, cuando la neurona está muy equivocada la curva Sigmoide es plana (derivada casi 0) y la red neuronal se queda 'congelada' sin aprender (Vanishing Gradient).", "No se usa como función de pérdida de entrenamiento en clasificación binaria con Sigmoide."],
            ["Exactitud sola (Accuracy)\n[NO sirve para entrenar pesos, SÍ para reportar]", "¿Por qué NO se puede entrenar la red directamente con Accuracy? Porque el Accuracy da saltos bruscos (acertó = 1, falló = 0) y su derivada es cero en casi todas partes, así que el optimizador Adam no sabría hacia dónde mover los pesos. Sí lo usamos al final para reportar cuántos clientes acertamos con umbral 0.50.", "Accuracy en Test = 67.48% (5,026 aciertos de 7,448) → Tasa de Error Global = 32.52% (2,422 errores)."],
            ["Brier Score (0.2050)\n[SÍ LO ESCOGIMOS — Calibración]", "Mide la distancia cuadrática media entre la probabilidad predicha y la realidad: (p - y)^2. Lo escogimos para verificar en una escala fácil (de 0.00 a 0.25) que las probabilidades están bien calibradas.", "En Validación = 0.2018 | En Test = 0.2050 (superando ampliamente el 0.2500 del azar)."],
            ["ROC-AUC (0.7448) y PR-AUC (0.7351)\n[SÍ LOS ESCOGIMOS — Ranking sin Umbral]", "¿Por qué escogimos ROC-AUC para vigilar el Early Stopping y elegir el ganador? Porque evalúa qué tan bien ordena el modelo a los clientes de menor a mayor riesgo en TODOS los umbrales posibles (de 0% a 100%), sin depender solo del corte en 50%.", "ROC-AUC Val = 0.75382 | Test = 0.74482 (el 74.5% de las veces puntúa más alto a un Apto que a un No Apto)."],
            ["Matriz de Confusión:\nFalsos Positivos (FP) vs Falsos Negativos (FN)\n[SÍ LOS ESCOGIMOS — Impacto Bancario]", "En banca no basta con saber el error total (32.52%): es obligatorio separar cuántos errores son Falsos Positivos (aprobar a un mal pagador → pérdida de capital por mora) y cuántos son Falsos Negativos (rechazar a un buen pagador → dejar de ganar intereses).", "En Test (7,448 clientes):\n• TN (Acierto No Apto) = 2,550 (34.24%)\n• TP (Acierto Apto) = 2,476 (33.24%)\n• FP (Error Riesgo Mora) = 1,174 (15.76%)\n• FN (Error Oportunidad) = 1,248 (16.76%)"]
        ]
        story.append(make_table(
            ["Clase de Error / Métrica", "¿Por qué SÍ la escogimos (o por qué NO escogimos otras)?", "Resultado Oficial en CrediRisk"],
            err_choice_rows,
            col_widths=[1.55 * inch, 3.65 * inch, 2.00 * inch],
            highlight_rows=[1, 4, 5, 6]
        ))

        add_img(
            story,
            "docs/images/04_matriz_confusion_test.png",
            "Figura 3. Matriz de Confusión en el conjunto de Prueba Final (Test = 7,448 clientes): 5,026 aciertos (67.48%) y 2,422 errores equilibrados (15.76% FP y 16.76% FN).",
            width_in=4.6
        )

        story.append(PageBreak())

        # =====================================================================
        # SECCIÓN 7: LAS 166 PRUEBAS, ÉPOCAS, ERRORES DE LAS PRUEBAS Y CURVA DE APRENDIZAJE
        # =====================================================================
        story.append(Paragraph("7. Las 166 Pruebas, Épocas Entrenadas, Errores de las Pruebas y Curva de Aprendizaje", h1_style))
        story.append(Paragraph(
            "En total ejecutamos <b>166 pruebas documentadas</b> en 4 etapas: <b>Etapa 0 Baseline (6 pruebas)</b>, <b>Fase 1 + Ablación (65 pruebas)</b>, <b>Fase 2 Regularización L2 y Paciencia (54 pruebas)</b> y <b>Fase 3 Nuevas Activaciones y Ensambles (46 pruebas)</b>.",
            p_style
        ))

        add_img(
            story,
            "docs/images/11_resumen_pruebas_y_epocas.png",
            "Figura 4. Panel A: Conteo exacto de las 166 pruebas por etapa. Panel B: Épocas entrenadas vs Mejor Época (Best Epoch) gracias a Early Stopping.",
            width_in=6.8
        )

        story.append(Paragraph("7.1 Tabla del Error en las Pruebas Principales (¿Qué probamos y cuánto dio el error en cada prueba?)", h2_style))
        story.append(Paragraph(
            "Si la profesora pide ver cómo cambiaba el error cuando probábamos distintos hiperparámetros (Dropout, Learning Rate, Batch Size, L2, Activaciones), esta tabla resume las pruebas clave de nuestros archivos CSV:",
            p_style
        ))

        all_tests_rows = [
            ["Fase 0 — Baseline", "Baseline inicial [64,32,16] lr=0.001, Drop=0.20", "24 (Best: 19)", "0.5897", "0.5934", "0.75010", "31.20%", "Punto de partida limpio."],
            ["Fase 1 — Sin Dropout", "EXP_17: [64,32,16] con Dropout = 0.0 (Apagado)", "20 (Best: 8)", "0.5812", "0.5968", "0.74471", "31.95%", "¡MEMORIZÓ! Sin Dropout el error de validación subió a 0.5968 y el AUC se desplomó."],
            ["Fase 1 — Dropout Excesivo", "EXP_21: [64,32,16] con Dropout = 0.40 (40% apagado)", "21 (Best: 9)", "0.6057", "0.6020", "0.74844", "31.42%", "Apagar el 40% de las neuronas impidió aprender (Subajuste: error subió a 0.6020)."],
            ["Fase 1 — Dropout Óptimo", "EXP_34 (Submodelo 1): [64,32,16] Drop=0.15, lr=0.0005", "44 (Best: 32)", "0.5869", "0.5909", "0.75225", "31.29%", "¡ÓPTIMO! Con 15% de Dropout y paso fino 0.0005 bajó el error a 0.5909."],
            ["Fase 1 — LR Muy Bajo", "EXP_10: [64,32,16] con lr = 0.0001 (demasiado lento)", "100 (Best: 100)", "0.5940", "0.5936", "0.75043", "31.29%", "Agotó las 100 épocas sin terminar de converger por dar pasos demasiado cortos."],
            ["Fase 1 — Batch Normalization", "EXP_23: [64,32,16] CON Batch Normalization interno", "41 (Best: 29)", "0.5834", "0.5929", "0.74937", "31.68%", "Dio más error que sin BatchNorm porque las 44 entradas ya venían con StandardScaler."],
            ["Fase 1 — LeakyReLU 2 Capas", "EXP_37 (Submodelo 2): [32,16] LeakyReLU(0.1), lr=0.0005", "83 (Best: 71)", "0.5862", "0.5894", "0.75224", "30.93%", "¡EXCELENTE! Logró el error de validación individual más bajo (0.5894) en 71 épocas."],
            ["Fase 2 — Regularización L2", "P2: [64,32,16] con L2=1e-4 y paciencia=12 épocas", "44 (Best: 32)", "0.5890", "0.5912", "0.75250", "31.18%", "Confirmó que paciencia de 12 épocas estabiliza el pico de validación."],
            ["Fase 3 — Activación ELU", "P3_06: [64,32,16] con activación suave ELU", "62 (Best: 50)", "0.5885", "0.6003", "0.75226", "31.29%", "Buena discriminación (AUC 0.7523), pero ReLU y LeakyReLU calibraron mejor el Log Loss."],
            ["Fase 3 — Activación GELU", "P3_05: [64,32,16] con activación GELU", "41 (Best: 29)", "0.5892", "0.6030", "0.75159", "31.25%", "Correcta pero no superó a la dupla ReLU + LeakyReLU."],
            ["MODELO FINAL (Test)", "Ensemble_Top3_Diverso (Promedio de las 3 mejores redes)", "32, 71 y 45", "—", "0.5888 (Val)\n0.5963 (Test)", "0.75382 (Val)\n0.74482 (Test)", "30.83% (Val)\n32.52% (Test)", "¡MEJOR RESULTADO GLOBAL! Menor error probabilístico y menor tasa de error."]
        ]
        story.append(make_table(
            ["Etapa / Prueba", "Configuración Probada", "Épocas (Best)", "Train Loss", "Val Loss", "ROC-AUC", "Error Clasif. %", "Lección Aprendida"],
            all_tests_rows,
            col_widths=[1.05 * inch, 1.55 * inch, 0.68 * inch, 0.55 * inch, 0.68 * inch, 0.68 * inch, 0.65 * inch, 1.36 * inch],
            highlight_rows=[4, 7, 11]
        ))

        story.append(PageBreak())

        story.append(Paragraph("7.2 Gráfica de Aprendizaje: ¿El Modelo Memorizó o Aprendió?", h2_style))
        add_img(
            story,
            "docs/images/10_curva_aprendizaje_memorizo_vs_aprendio.png",
            "Figura 5. Panel A: Curva real de aprendizaje de CrediRisk (Train Loss vs Val Loss). Panel B: Comparación visual entre un modelo que aprende y uno que memoriza (Overfitting).",
            width_in=6.8
        )

        story.append(make_callout(
            "LAS 4 PRUEBAS CIENTÍFICAS DE QUE CREDIRISK APRENDIÓ Y NO MEMORIZÓ",
            [
                "<b>1. Convergencia paralela con brecha casi cero (0.0004):</b> En la gráfica (Panel A), la línea azul (Error en Entrenamiento) y la línea naranja (Error en Validación con clientes nuevos) bajan juntas y se estabilizan pegadas alrededor de 0.593 (en la época 13, Train = 0.5929 vs Val = 0.5933; en la época 19, Train = 0.5897 vs Val = 0.5934). Si hubiera memorizado, la línea naranja habría subido disparada hacia arriba como en la línea roja del Panel B.",
                "<b>2. ¿Por qué al principio (Épocas 0 a 10) el error de Validación (naranja) es más bajo que el de Entrenamiento (azul)?</b> Porque durante el entrenamiento la red tiene activado el <b>Dropout (15%–20% de neuronas apagadas al azar)</b>, lo que hace más difícil el estudio, mientras que en el examen de Validación usa el 100% de sus neuronas.",
                "<b>3. Estabilidad en 65 pruebas con 5 Semillas Aleatorias (42, 1, 7, 21, 2026):</b> Al entrenar desde 5 puntos de partida distintos, la desviación estándar del ROC-AUC fue de apenas <b>±0.00029 (0.029%)</b>. Un modelo que memoriza da resultados erráticos al cambiar la semilla; el nuestro siempre encuentra las mismas reglas financieras.",
                "<b>4. Prueba de fuego en los 7,448 clientes nunca vistos de Test:</b> Al evaluar el modelo en el conjunto Test guardado bajo llave, el ROC-AUC pasó de 0.75382 (Validación) a 0.74482 (Test), una diferencia de apenas <b>-0.00900 (menos de 1%)</b>."
            ],
            bg_hex="#ECFDF5", border_hex="#059669", title_hex="#065F46"
        ))
        story.append(Spacer(1, 8))

        # =====================================================================
        # SECCIÓN 8: BANCO DE 15 PREGUNTAS DE LA PROFESORA CON RESPUESTA EXACTA
        # =====================================================================
        story.append(Paragraph("8. Banco Rápido: 12 Preguntas Directas de la Profesora y Qué Responder", h1_style))
        qa_rows = [
            ["1. ¿Cuántas variables tenía el dataset y cuántas entraron a la red?", "El CSV original tenía 26 columnas: quitamos 2 (id_solicitud e INCUMPLIO_PAGO para evitar fuga de datos) y separamos 1 como objetivo (APTO_PARA_CREDITO). Tomamos las 23 variables predictoras base (19 numéricas + 4 de texto), las cuales tras agregar 7 banderas de nulos (_nan) y expandir las 4 de texto en 18 columnas One-Hot se convirtieron en 44 variables finales estandarizadas."],
            ["2. ¿Cuáles son las variables One-Hot y por qué las hicieron?", "Son las 18 columnas binarias (0 y 1) creadas a partir de estado_civil (5), linea_negocio (2), tipo_contrato (5) y tipo_vivienda (6). Las hicimos porque la red no lee texto y si pusiéramos 1, 2, 3, 4 inventaríamos una jerarquía matemática falsa entre categorías."],
            ["3. ¿Por qué hicieron la partición 70% / 15% / 15%?", "70% Train (34,755 clientes) para ajustar el preprocesador y los pesos con más de 6 clientes por parámetro; 15% Validación (7,447) como juez intermedio para Early Stopping y comparar las 166 pruebas; y 15% Test (7,448) sellado hasta el final para medir generalización real sin hacer trampa."],
            ["4. ¿Por qué la red tiene 3 capas de [64, 32, 16] neuronas y qué hace cada capa?", "La Capa 1 sube de 44 a 64 neuronas para expandir y armar 64 cruces directos entre pares/tríos de variables (ej. cuota vs ingreso, score vs tasa). La Capa 2 baja a 32 para resolver contradicciones entre esos cruces. La Capa 3 baja a 16 como cuello de botella para resumir el perfil ejecutivo sin memorizar ruido. Y la neurona final Sigmoide entrega la probabilidad de 0 a 1."],
            ["5. ¿Por qué NO pusieron más capas (4 o 5) o más neuronas (128, 256)?", "Sí las probamos en la Fase 1 (EXP_05 a EXP_09 con 4 capas y hasta 28,513 parámetros), y demostramos con datos que al pasar de 10,000 parámetros la red memorizaba el entrenamiento y empeoraba el error de validación (subía a 0.5945). El punto óptimo para 34,755 filas fue 5,505 parámetros ([64,32,16]) y 1,985 parámetros ([32,16])."],
            ["6. ¿Por qué usaron 3 redes neuronales y luego les sacan el promedio?", "Porque un comité de 3 redes diversas (Red 1 profunda [64,32,16] ReLU, Red 2 compacta [32,16] LeakyReLU y Red 3 [64,32,16] con Dropout 0.20 y semilla 2026) cancela los errores individuales en clientes dudosos cercanos al 50%, bajando el Log Loss a 0.5963 y subiendo el AUC a 0.7448."],
            ["7. ¿Por qué escogieron Binary Cross-Entropy (Log Loss) y no otro error?", "Porque con una salida Sigmoide, Binary Cross-Entropy tiene derivada continua que evita que las neuronas se congelen y además castiga exponencialmente cuando el modelo se equivoca con exceso de confianza."],
            ["8. ¿Cuánto es el error del modelo?", "En Test (7,448 clientes): el error probabilístico Log Loss es 0.5963 y el Brier Score es 0.2050. En clasificación con umbral 0.50, acierta el 67.48% (5,026 clientes) y su tasa de error es 32.52% (2,422 clientes), repartida equilibradamente en 15.76% de Falsos Positivos y 16.76% de Falsos Negativos, con un ROC-AUC de 0.7448."],
            ["9. ¿Por qué el error de clasificación es 32.52% y no 5%?", "Porque en crédito real dos clientes con el mismo sueldo y puntaje intermedio (580–620) pueden tomar caminos distintos por imprevistos externos que no existen al pedir el préstamo. Un AUC de ~0.75 es el techo real sin fuga de datos."],
            ["10. ¿Cuántas pruebas y cuántas épocas hicieron y por qué pararon ahí?", "Hicimos 166 pruebas documentadas. Pusimos un tope de 120 épocas con Early Stopping (paciencia 10–12 épocas y restore_best_weights=True): los 3 modelos finales entrenaron 44, 83 y 55 épocas, rebobinando y guardando sus mejores pesos en las épocas 32, 71 y 45."],
            ["11. ¿Aplicaron alguna normalización?", "Sí, tres: (1) Recorte [p1, p99] + logaritmos (log1p y signed_log) para normalizar la asimetría de los montos en dinero; (2) StandardScaler (Z-Score) ajustado solo en Train para dejar las 44 variables con media 0 y desviación 1; y (3) inicialización he_normal en los pesos."],
            ["12. ¿El modelo memorizó o aprendió?", "Aprendió y NO memorizó: las curvas de error de entrenamiento (0.5929) y validación (0.5933) bajan juntas y se estabilizan pegadas (brecha de 0.0004) sin que la validación suba jamás, y en Test el AUC varió menos de 1% (-0.0090)."]
        ]
        story.append(make_table(
            ["Pregunta de la Profesora", "Respuesta Exacta y Contundente"],
            qa_rows,
            col_widths=[2.15 * inch, 5.05 * inch]
        ))

        doc.build(story)
        print(f"Generated Master PDF: {os.path.abspath(out_path)} ({os.path.getsize(out_path):,} bytes)")

if __name__ == "__main__":
    build_master_pdf()
