import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=110, bottom=110, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1", sz="4"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideV w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def add_callout_box(doc, title, text_lines, bg_hex="EFF6FF", border_hex="2563EB", title_rgb=(30, 64, 175)):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="{border_hex}"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{border_hex}"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_hex}"/>
            <w:right w:val="single" w:sz="6" w:space="0" w:color="{border_hex}"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    r_title = p.add_run(title + "\n")
    r_title.bold = True
    r_title.font.size = Pt(11)
    r_title.font.color.rgb = RGBColor(*title_rgb)
    for idx, line in enumerate(text_lines):
        r = p.add_run(line + ("\n" if idx < len(text_lines) - 1 else ""))
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_styled_table(doc, headers, rows, header_bg="0F172A"):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color="CBD5E1", sz="4")

    hdr_cells = table.rows[0].cells
    for i, h_text in enumerate(headers):
        hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_background(hdr_cells[i], header_bg)
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=120, right=120)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(h_text)
        run.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, row_data in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_background(row_cells[c_idx], bg)
            set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=120, right=120)
            p = row_cells[c_idx].paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(val)
            run.font.size = Pt(9.2)
            run.font.color.rgb = RGBColor(15, 23, 42)
            if c_idx == 0:
                run.bold = True
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_image_with_caption(doc, img_path, caption_text, width_inches=6.4):
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(2)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(width_inches))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(10)
        r_cap = p_cap.add_run(caption_text)
        r_cap.italic = True
        r_cap.font.size = Pt(9)
        r_cap.font.color.rgb = RGBColor(71, 85, 105)

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(15.5)
    r.font.color.rgb = RGBColor(15, 23, 42)
    # Add bottom border to H1
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="4" w:color="2563EB"/></w:pBdr>')
    pPr.append(pBdr)

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(12.5)
    r.font.color.rgb = RGBColor(29, 78, 216)

def add_bullet(doc, bold_prefix, rest_text):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(bold_prefix)
    r1.bold = True
    r1.font.size = Pt(10.2)
    r1.font.color.rgb = RGBColor(15, 23, 42)
    r2 = p.add_run(rest_text)
    r2.font.size = Pt(10.2)
    r2.font.color.rgb = RGBColor(30, 41, 59)

def add_para(doc, text, bold_prefix=""):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(5)
    if bold_prefix:
        r1 = p.add_run(bold_prefix)
        r1.bold = True
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = RGBColor(15, 23, 42)
    r2 = p.add_run(text)
    r2.font.size = Pt(10.5)
    r2.font.color.rgb = RGBColor(30, 41, 59)

def build_docx():
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(10.5)

    # HEADER BANNER
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(4)
    r_sub = p_title.add_run("PROYECTO DE DEEP LEARNING — EVALUACIÓN DE RIESGO CREDITICIO (CREDIRISK)\n")
    r_sub.bold = True
    r_sub.font.size = Pt(9.5)
    r_sub.font.color.rgb = RGBColor(37, 99, 235)

    r_main = p_title.add_run("Guía Maestra de Sustentación: Métodos, Explicación del Error, Pruebas, Épocas, Etapas y Curvas de Aprendizaje")
    r_main.bold = True
    r_main.font.size = Pt(18)
    r_main.font.color.rgb = RGBColor(15, 23, 42)

    p_team = doc.add_paragraph()
    p_team.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_team.paragraph_format.space_after = Pt(12)
    r_team = p_team.add_run("Equipo CrediRisk: Leidy • Sharick • Laura Sofía • Iván Camilo • Cristian Camilo")
    r_team.italic = True
    r_team.font.size = Pt(10)
    r_team.font.color.rgb = RGBColor(100, 116, 139)

    add_callout_box(
        doc,
        "OBJETIVO DE ESTE DOCUMENTO",
        [
            "Responder de manera minuciosa, con gráficas reales del proyecto y en un lenguaje 100% comprensible para todo el mundo (tanto para personas no técnicas como para un jurado académico) las 5 preguntas clave del equipo:",
            "1. Explicación de los métodos utilizados (Preprocesamiento de 23 a 44 variables, Redes MLP, Regularización y Ensamble).",
            "2. Explicación detallada del error (Matriz de Confusión en Test, Falsos Positivos vs Falsos Negativos, Log Loss, Brier y ROC-AUC).",
            "3. Cuántas pruebas se hicieron (166 ejecuciones), qué procesos se corrieron, cuántas épocas entrenó cada modelo y por qué.",
            "4. Justificación científica de cada etapa (Baseline → Fase 1 + Ablación → Fase 2 → Fase 3 → Comité Top-3 Diverso).",
            "5. Gráfica de aprendizaje: ¿El modelo memorizó o realmente aprendió?"
        ],
        bg_hex="EFF6FF", border_hex="2563EB", title_rgb=(29, 78, 216)
    )

    # =========================================================================
    # SECCIÓN 1: EXPLICACIÓN DE LOS MÉTODOS
    # =========================================================================
    add_heading_1(doc, "1. Explicación de los Métodos: ¿Cómo funciona CrediRisk paso a paso?")
    add_para(
        doc,
        "Para que una red neuronal pueda evaluar si un solicitante de crédito es Apto (1) o No Apto (0), no basta con entregarle una hoja de cálculo cruda. Nuestro sistema aplica 5 métodos científicos encadenados desde la lectura del archivo hasta la decisión final:"
    )

    add_image_with_caption(
        doc,
        "docs/images/07_pipeline_datos.png",
        "Figura 1. Pipeline completo de transformación de datos: de las 23 columnas originales a las 44 variables normalizadas sin fuga de información (Zero Data Leakage)."
    )

    add_heading_2(doc, "Método 1.1 — Partición Estratificada 70% / 15% / 15% sin Fuga de Datos (Zero Data Leakage)")
    add_bullet(doc, "Base de datos oficial inmutable: ", "Contamos con DatasetCreditoFinancieroFinalV2.csv compuesto por 49,650 solicitudes de crédito perfectamente balanceadas: 24,825 clientes Aptos (50.0%) y 24,825 clientes No Aptos (50.0%).")
    add_bullet(doc, "División antes de cualquier cálculo (Semilla fija = 42): ", "Dividimos el dataset manteniendo exactamente la proporción 50% / 50% en tres bloques independientes:")
    add_bullet(doc, "  • Entrenamiento (Train — 70% = 34,755 clientes): ", "Es el 'libro de estudio' con el que la red neuronal ajusta sus pesos internos.")
    add_bullet(doc, "  • Validación (Validation — 15% = 7,447 clientes): ", "Es el 'simulacro de examen' que se evalúa al final de cada época para vigilar que el modelo aprenda de verdad y elegir las mejores arquitecturas.")
    add_bullet(doc, "  • Prueba Final (Test — 15% = 7,448 clientes): ", "Es el 'examen de grado guardado bajo llave'. Nunca se usó para decidir épocas ni arquitecturas; solo se abrió al final para medir el rendimiento real.")
    add_bullet(doc, "¿Por qué previene la trampa (Data Leakage)? ", "Porque todas las fórmulas estadísticas (medianas, recortes de extremos, medias y desviaciones estándar) se calcularon exclusivamente sobre los 34,755 clientes de Train y luego se aplicaron a Validación y Test.")

    add_heading_2(doc, "Método 1.2 — Ingeniería y Preprocesamiento: ¿Cómo pasamos de 23 columnas a 44 variables?")
    add_para(
        doc,
        "El archivo original tiene 23 columnas. Primero retiramos id_solicitud (porque un número de radicado no tiene relación con pagar un crédito) y separamos la respuesta apto_credito, quedando 21 variables predictoras base (17 numéricas y 4 categóricas/texto). Esas 21 variables se convierten en 44 características numéricas limpias mediante 6 pasos:"
    )

    add_styled_table(
        doc,
        ["Paso del Método", "¿Qué hace en palabras sencillas?", "¿Por qué es indispensable para la Red Neuronal?", "Impacto en Columnas"],
        [
            ["1. Banderas de Nulos (_nan)", "Antes de rellenar celdas vacías en 7 columnas clave (ingreso, score, mora, etc.), crea una columna extra que vale 1 si el dato faltaba y 0 si estaba.", "En banca, que un cliente no reporte un dato no es casualidad: suele indicar informalidad o falta de historial. Con la bandera la red conserva esa pista.", "+7 columnas binarias"],
            ["2. Recorte de Extremos (Clipping p1–p99)", "Acota los valores extremos por debajo del percentil 1% y por encima del percentil 99% calculados en Train.", "Evita que un error de digitación o un cliente multimillonario distorsione los pesos de toda la red neuronal.", "Mantiene columnas"],
            ["3. Transformación Logarítmica (log1p y signed_log)", "Aplica logaritmo ln(1+x) a variables monetarias muy sesgadas (ingresos, montos, saldos, mora) y logaritmo con signo a ingreso_disponible.", "Comprime cifras de millones a una escala suave en forma de campana para que la red distinga igual de bien sueldos bajos y altos.", "Mantiene columnas"],
            ["4. Imputación por Mediana", "Rellena las celdas numéricas vacías con la mediana de Train (el valor central, no el promedio).", "Las redes neuronales no pueden multiplicar valores vacíos (NaN). La mediana es inmune a valores extremos.", "17 columnas numéricas limpias"],
            ["5. Agrupación y One-Hot Encoding", "Agrupa categorías raras (<1%) en 'Otro' y convierte las 4 columnas de texto (estado civil, contrato, línea, vivienda) en columnas de 0 y 1.", "Si pusiéramos Soltero=1, Casado=2, Viudo=3, la red creería que Viudo vale el triple que Soltero. Con One-Hot cada categoría tiene su propio peso.", "4 de texto pasan a 20 binarias"],
            ["6. Estandarización (StandardScaler)", "Resta el promedio y divide por la desviación estándar (z = (x - media)/desv) dejando todas las variables en escala comparable.", "Sin esto, un monto en millones aplastaría a variables pequeñas como número de cuotas en mora (0 a 5).", "Total: 17 + 7 + 20 = 44 variables"]
        ]
    )

    add_heading_2(doc, "Método 1.3 — Arquitectura de Red Neuronal: Perceptrón Multicapa (MLP en Embudo)")
    add_bullet(doc, "Estructura piramidal decreciente (ej. 44 → 64 → 32 → 16 → 1): ", "La primera capa oculta (64 neuronas) cruza las 44 variables para detectar combinaciones amplias (ej. cuota frente a ingreso y antigüedad). La segunda capa (32) sintetiza esos cruces en indicadores de solvencia. La tercera capa (16) destila el perfil de riesgo antes de la neurona final.")
    add_bullet(doc, "Funciones de Activación No Lineales (ReLU y LeakyReLU): ", "ReLU deja pasar valores positivos y apaga en cero los negativos, permitiendo aprender fronteras de decisión curvas. LeakyReLU(0.1) deja pasar un 10% de los valores negativos para que ninguna neurona quede 'muerta' y para capturar matices cuando un flujo de caja es negativo.")
    add_bullet(doc, "Neurona de Salida Sigmoide: ", "Transforma el puntaje final en una probabilidad continua entre 0.00 (0%) y 1.00 (100%) de que el cliente sea Apto para el crédito.")

    add_heading_2(doc, "Método 1.4 — Métodos de Regularización y Control (Para aprender sin memorizar)")
    add_bullet(doc, "Dropout (15% a 20%): ", "En cada paso de entrenamiento apaga al azar entre el 15% y el 20% de las neuronas. Es como entrenar a un equipo haciendo que distintos miembros descansen en cada práctica: así ninguna neurona memoriza clientes sueltos y toda la red aprende reglas generales.")
    add_bullet(doc, "Optimizador Adam (lr = 0.0005 y 0.001) con Batch Size = 256: ", "Ajusta los pesos de la red cada 256 clientes adaptando automáticamente la velocidad de cada conexión.")
    add_bullet(doc, "ReduceLROnPlateau: ", "Cuando el error de validación lleva 4 o 5 épocas sin mejorar, reduce la velocidad de aprendizaje a la mitad (x0.5) para dar pasos milimétricos y encontrar el fondo exacto del valle de error.")
    add_bullet(doc, "Early Stopping con restore_best_weights = True: ", "Vigila el rendimiento en los 7,447 clientes de Validación en cada época. Si pasan 10–12 épocas seguidas sin superar su mejor marca, detiene el entrenamiento y rebobina los pesos exactamente a la mejor época histórica.")

    add_heading_2(doc, "Método 1.5 — Comité de Decisión Final: Ensamble Heterogéneo Top-3 Diverso")
    add_para(
        doc,
        "En lugar de depender de una sola red neuronal, nuestro modelo final (Ensemble_Top3_Diverso) funciona como un Comité Bancario de 3 especialistas con arquitecturas distintas que promedian sus probabilidades (1/3 cada uno):"
    )
    add_bullet(doc, "1. Especialista 1 (cfg_c_s42): ", "Red profunda [64, 32, 16] con activación ReLU, Dropout 0.15, paso fino lr=0.0005 (5,505 parámetros).")
    add_bullet(doc, "2. Especialista 2 (cfg_b_leaky_s42): ", "Red compacta [32, 16] con activación LeakyReLU(0.1), Dropout 0.15, lr=0.0005 (1,985 parámetros).")
    add_bullet(doc, "3. Especialista 3 (cfg_base_s2026): ", "Red profunda [64, 32, 16] con ReLU, regularización más estricta (Dropout 0.20), lr=0.001 y semilla independiente 2026 (5,505 parámetros).")

    add_image_with_caption(
        doc,
        "docs/images/06_arquitectura_ensamble_final.png",
        "Figura 2. Arquitectura del Ensamble Final Top-3 Diverso (12,995 parámetros totales combinando 3 redes neuronales especialistas)."
    )

    # =========================================================================
    # SECCIÓN 2: EXPLICACIÓN DEL ERROR
    # =========================================================================
    add_heading_1(doc, "2. Explicación Minuciosa del Error: ¿Cuánto se equivoca y qué significa?")
    add_para(
        doc,
        "En Inteligencia Artificial aplicada a banca, el error se analiza de dos formas complementarias: (A) contando cuántos clientes acierta o falla al clasificar en Apto / No Apto (Matriz de Confusión), y (B) midiendo qué tan calibradas y honestas son sus probabilidades (Log Loss, Brier Score y ROC-AUC)."
    )

    add_image_with_caption(
        doc,
        "docs/images/04_matriz_confusion_test.png",
        "Figura 3. Matriz de Confusión oficial evaluada sobre los 7,448 clientes del conjunto de Prueba Final (Test) con umbral estándar de 0.50."
    )

    add_heading_2(doc, "2.1 El Error de Clasificación en los 7,448 Clientes del Examen Final (Test)")
    add_bullet(doc, "Aciertos Totales (Accuracy = 67.48%): ", "El modelo clasifica correctamente a 5,026 de los 7,448 clientes (2,550 Verdaderos Negativos + 2,476 Verdaderos Positivos).")
    add_bullet(doc, "Tasa de Error Global (32.52%): ", "El modelo se equivoca en 2,422 clientes de los 7,448 (1,174 Falsos Positivos + 1,248 Falsos Negativos).")

    add_styled_table(
        doc,
        ["Cuadrante en Test", "Clientes (de 7,448)", "% del Total", "¿Qué ocurrió en la realidad vs. predicción?", "Impacto Financiero y Operativo en el Banco"],
        [
            ["Verdaderos Negativos (TN) — Acierto", "2,550", "34.24%", "El cliente NO era apto (0) y el modelo lo rechazó correctamente (0).", "Pérdida evitada: El banco se protegió de prestarle dinero a 2,550 clientes riesgosos (detectó al 68.47% de los malos pagadores)."],
            ["Verdaderos Positivos (TP) — Acierto", "2,476", "33.24%", "El cliente SÍ era apto (1) y el modelo aprobó el crédito (1).", "Negocio sano: El banco otorgó 2,476 créditos buenos que generan intereses sin caer en mora (captó al 66.49% de los buenos clientes)."],
            ["Falsos Positivos (FP) — Error Tipo I", "1,174", "15.76%", "El cliente NO era apto (0), pero parecía solvente y el modelo lo aprobó (1).", "Riesgo de Cartera (Morosidad): Es el error más sensible para el banco, porque aprueba a un solicitante que puede incumplir."],
            ["Falsos Negativos (FN) — Error Tipo II", "1,248", "16.76%", "El cliente SÍ era apto (1), pero tenía alertas en su perfil y el modelo lo rechazó (0).", "Costo de Oportunidad Comercial: El banco no pierde capital prestado, pero deja de ganar los intereses de un cliente que sí habría pagado."]
        ]
    )

    add_callout_box(
        doc,
        "¿POR QUÉ ES UNA GRAN NOTICIA QUE LOS DOS ERRORES ESTÉN EQUILIBRADOS (15.76% FP vs 16.76% FN)?",
        [
            "Porque demuestra que el modelo NO está sesgado: no es un modelo 'temerario' que aprueba a cualquiera (lo que quebraría al banco con Falsos Positivos), ni un modelo 'paranoico' que rechaza a todo el mundo (lo que dejaría al banco sin clientes). Además, es ligeramente más cauteloso cuidando el capital del banco (acierta el 68.47% de los No Aptos frente al 66.49% de los Aptos)."
        ],
        bg_hex="ECFDF5", border_hex="059669", title_rgb=(6, 95, 70)
    )

    add_heading_2(doc, "2.2 El Error Probabilístico: Log Loss (0.5963), Brier Score (0.2050) y ROC-AUC (0.7448)")
    add_image_with_caption(
        doc,
        "docs/images/02_calidad_probabilistica.png",
        "Figura 4. Reducción del error probabilístico (Log Loss y Brier Score) desde el modelo inicial hasta el Ensamble Final."
    )

    add_bullet(doc, "Log Loss / Binary Cross-Entropy = 0.5963 en Test (0.5888 en Validación): ", "Es el error que la red neuronal minimiza en cada época. Funciona como un 'castigador de arrogancia': si el modelo se equivoca estando 99% seguro, recibe un castigo matemático enorme. Adivinar al azar con una moneda tiene un Log Loss de 0.6931; haberlo bajado a 0.5963 demuestra que las probabilidades del modelo son prudentes y confiables.")
    add_bullet(doc, "Brier Score = 0.2050 en Test (0.2018 en Validación): ", "Es el promedio del error al cuadrado entre la probabilidad predicha y la realidad (0 o 1). Al azar el Brier Score es 0.2500; nuestro modelo lo reduce a 0.2050.")
    add_bullet(doc, "ROC-AUC = 0.74482 en Test (0.75382 en Validación): ", "Significado intuitivo para decir en la exposición: si elegimos al azar a un cliente Apto y a uno No Apto, el 74.5% de las veces nuestro modelo le asigna una probabilidad más alta al cliente Apto.")
    add_bullet(doc, "¿Por qué existe un 32.5% de casos donde el modelo se equivoca? ", "Porque en el comportamiento financiero humano real existen eventos impredecibles que no están en la solicitud (despidos, calamidades familiares o clientes con puntajes medios de 580–620 que tienen perfiles idénticos pero toman decisiones distintas). En datos financieros reales, un modelo que reporte 98% de acierto casi siempre tiene fuga de datos o memorización; un AUC de 0.745–0.754 refleja el techo real de señal limpia.")

    # =========================================================================
    # SECCIÓN 3: CUÁNTAS PRUEBAS SE HICIERON, PROCESOS, ÉPOCAS Y POR QUÉ
    # =========================================================================
    add_heading_1(doc, "3. ¿Cuántas Pruebas se Hicieron, Qué Procesos, Cuántas Épocas y Por Qué?")
    add_para(
        doc,
        "No elegimos una arquitectura al azar. Ejecutamos un protocolo experimental sistemático de 166 entrenamientos y evaluaciones documentadas en archivos CSV dentro de la carpeta reports/:"
    )

    add_image_with_caption(
        doc,
        "docs/images/11_resumen_pruebas_y_epocas.png",
        "Figura 5. Panel A: Desglose de las 166 pruebas experimentales por etapa. Panel B: Épocas entrenadas por cada submodelo vs. su Mejor Época (Early Stopping)."
    )

    add_heading_2(doc, "3.1 Conteo Exacto de las 166 Pruebas y Procesos Ejecutados")
    add_styled_table(
        doc,
        ["Etapa del Proyecto", "Experimentos de Arquitectura", "Corridas Multi-Semilla (5 Seeds)", "Pruebas de Ablación / Ensambles", "Total en la Etapa", "Archivos de Registro (Evidencia)"],
        [
            ["Etapa 0: Baseline Inicial", "1 corrida base", "5 corridas (seeds 1 a 5)", "—", "6 pruebas", "history_final.csv, history_seed1..5.csv"],
            ["Etapa 1: Fase 1 + Ablación", "37 arquitecturas (capas, LR, batch, dropout)", "20 corridas (Top-4 x 5 semillas)", "5 pruebas de ablación + 3 ensambles", "65 pruebas", "experiments.csv, ablation_study.csv, multiseed_evaluation.csv"],
            ["Etapa 2: Regularización Fase 2", "29 experimentos (L2, paciencias 8 a 15)", "20 corridas (Top-4 x 5 semillas)", "5 ensambles candidatos", "54 pruebas", "experiments_phase2.csv, multiseed_evaluation_phase2.csv"],
            ["Etapa 3: Activaciones Fase 3", "18 experimentos (ELU, GELU, Swish, Huber)", "20 corridas (Top-4 x 5 semillas)", "8 ensambles en validación", "46 pruebas", "experiments_phase3.csv, ensemble_validation_phase3.csv"],
            ["TOTAL DOCUMENTADO", "85 experimentos de diseño", "65 pruebas de estabilidad", "16 pruebas de ensambles", "166 pruebas", "Carpeta reports/ completa"]
        ]
    )

    add_heading_2(doc, "3.2 ¿Qué es una Época, cuántas épocas se entrenaron y por qué paró ahí?")
    add_bullet(doc, "¿Qué es 1 Época (Epoch)? ", "Es un ciclo completo en el que la red neuronal estudia los 34,755 clientes de entrenamiento. Como los procesa en bloques (batches) de 256 clientes, en cada época realiza exactamente 136 actualizaciones matemáticas de sus pesos (34,755 / 256 = 136).")
    add_bullet(doc, "¿Por qué no entrenamos un número fijo como 300 o 500 épocas? ", "Porque si obligas a una red neuronal a repasar demasiadas veces los mismos 34,755 clientes, después de cierto punto deja de aprender reglas generales y empieza a memorizar casos particulares (Overfitting).")
    add_bullet(doc, "¿Cómo decidimos el número exacto de épocas de cada modelo? ", "Pusimos un techo amplio (100 a 120 épocas) pero activamos el vigilante automático Early Stopping (paciencia de 10 a 12 épocas con restore_best_weights=True). Cuando el modelo lleva 10 o 12 épocas sin mejorar su calificación en el examen de Validación, se detiene solo y rebobina sus pesos a la mejor época:")

    add_styled_table(
        doc,
        ["Modelo Analizado", "Tope Máximo", "Mejor Época (Best Epoch guardada)", "Época donde paró (Total Epochs)", "Ventana de Paciencia", "¿Por qué entrenó exactamente esas épocas?"],
        [
            ["Baseline Inicial", "100 épocas", "Época 19 (Val Loss = 0.5934)", "Época 24", "5 épocas", "Con tasa de aprendizaje rápida (lr=0.001) convergió en 19 épocas y tras 5 de vigilancia se detuvo en la 24."],
            ["Submodelo 1: cfg_c_s42 ([64,32,16] ReLU)", "120 épocas", "Época 32 (Val AUC = 0.7536)", "Época 44", "12 épocas", "Al usar un aprendizaje el doble de fino (lr=0.0005), necesitó 32 épocas para llegar a la cumbre y paró en la 44."],
            ["Submodelo 2: cfg_b_leaky_s42 ([32,16] LeakyReLU)", "120 épocas", "Época 71 (Val AUC = 0.7537)", "Época 83", "12 épocas", "Por ser una red compacta (1,985 parámetros) con LeakyReLU, aprendió de forma gradual hasta la época 71 y paró en la 83."],
            ["Submodelo 3: cfg_base_s2026 ([64,32,16] Drop 0.20)", "100 épocas", "Época 45 (Val AUC = 0.7525)", "Época 55", "10 épocas", "Al apagar el 20% de las neuronas al azar (Dropout 0.20), requirió 45 épocas para consolidar sus pesos y paró en la 55."]
        ]
    )

    # =========================================================================
    # SECCIÓN 4: JUSTIFICACIÓN DE CADA ETAPA
    # =========================================================================
    add_heading_1(doc, "4. Justificación Científica de Cada Etapa del Proyecto")
    add_para(
        doc,
        "Cada fase del proyecto se diseñó para responder una pregunta científica concreta antes de dar el siguiente paso:"
    )

    add_image_with_caption(
        doc,
        "docs/images/08_flujo_fases_experimentales.png",
        "Figura 6. Flujo metodológico de las etapas experimentales de CrediRisk."
    )

    add_bullet(doc, "Etapa 0 — Baseline Inicial (Punto de Referencia): ", "Toda investigación científica necesita una línea base para comprobar si los cambios futuros realmente aportan valor. El modelo base logró un ROC-AUC de 0.7501 en Validación y 0.7418 en Test (Log Loss = 0.6001).")
    add_bullet(doc, "Etapa 1 — Fase 1 (37 arquitecturas) + Estudio de Ablación (5 pruebas): ", "Justificación doble: (1) Con el estudio de ablación probamos entrenar con 9, 21, 35, 44 y 50 variables. Con solo 9 variables financieras el AUC cayó a 0.6279; con nuestras 44 variables subió a 0.7523; y añadir 6 ratios manuales extra (50 variables) dio 0.7518, demostrando que 44 era el conjunto óptimo. (2) En arquitecturas demostramos que redes gigantes ([256, 128, 64]) sobreajustaban, mientras que embudos compactos ([64, 32, 16] y [32, 16]) con Dropout 0.15 y lr=0.0005 subieron el AUC a 0.7537.")
    add_bullet(doc, "Etapa 2 — Fase 2 (29 experimentos de Regularización L2 y Paciencia): ", "Justificación: Una vez halladas las mejores estructuras de capas, necesitábamos verificar si agregar penalización matemática L2 a los pesos y ampliar la paciencia del Early Stopping (a 12 épocas) mejoraba la calibración. Descubrimos que un L2 fuerte frenaba demasiado a la red, pero que la paciencia de 12 épocas permitía a los modelos con lr=0.0005 alcanzar un mejor óptimo.")
    add_bullet(doc, "Etapa 3 — Fase 3 (18 experimentos de Activaciones y Comité de Ensamble): ", "Justificación: Buscábamos 'diversidad de criterio' probando activaciones suaves (LeakyReLU, ELU, GELU, Swish). Comprobamos que combinar tres redes con distinta profundidad, distinta función de activación y distinta semilla (Ensemble_Top3_Diverso) reducía la varianza y superaba a cualquier modelo individual tanto en Validación (AUC 0.75382) como en Test (AUC 0.74482).")

    add_image_with_caption(
        doc,
        "docs/images/01_evolucion_roc_auc.png",
        "Figura 7. Evolución progresiva del ROC-AUC en Validación y Test a través de las etapas del proyecto."
    )

    # =========================================================================
    # SECCIÓN 5: GRÁFICA DE APRENDIZAJE: ¿MEMORIZÓ O APRENDIÓ?
    # =========================================================================
    add_heading_1(doc, "5. Gráfica de Aprendizaje: ¿El Modelo Memorizó o Aprendió?")

    add_callout_box(
        doc,
        "RESPUESTA DIRECTA PARA LA SUSTENTACIÓN",
        [
            "El modelo APRENDIÓ patrones estadísticos generalizables y NO memorizó (No tuvo Overfitting). Lo demostramos con la curva de aprendizaje época por época, la estabilidad en 5 semillas aleatorias y la evaluación a ciegas en el conjunto Test."
        ],
        bg_hex="ECFDF5", border_hex="059669", title_rgb=(6, 95, 70)
    )

    add_image_with_caption(
        doc,
        "docs/images/10_curva_aprendizaje_memorizo_vs_aprendio.png",
        "Figura 8. Panel A: Curva real de aprendizaje de CrediRisk (Train vs Validación). Panel B: Comparación didáctica entre un modelo que aprende (CrediRisk) y un modelo que memoriza (Overfitting)."
    )

    add_heading_2(doc, "5.1 ¿Cómo explicarle esta gráfica a cualquier persona?")
    add_para(
        doc,
        "Imagina a un estudiante preparándose para un examen con una guía de ejercicios resueltos (Línea Azul = Entrenamiento / Train) y presentando simulacros con preguntas nuevas que nunca ha visto (Línea Naranja = Validación):"
    )
    add_bullet(doc, "¿Qué pasa cuando un modelo MEMORIZA (Overfitting — línea roja del Panel B)? ", "El error en el libro de estudio baja casi a cero porque se aprendió las respuestas de memoria, pero cuando le hacen preguntas nuevas en el simulacro, no sabe resolverlas y la línea de validación se dispara hacia arriba formando una 'U' abierta.")
    add_bullet(doc, "¿Qué pasa en nuestro modelo CrediRisk (Panel A)? ", "Tanto el error de estudio (azul) como el error con clientes nuevos (naranja) bajan juntos desde la época 0 hasta estabilizarse pegados alrededor de 0.593. ¡La línea naranja jamás sube ni se dispara!")

    add_heading_2(doc, "5.2 Las 4 Pruebas Numéricas de que Aprendió y NO Memorizó")
    add_bullet(doc, "Prueba 1 — Brecha mínima entre Train y Validación (0.0004): ", "En la época 13 (punto de cruce óptimo en history_final.csv), el error de entrenamiento es 0.5929 y el de validación en clientes nuevos es 0.5933 (una diferencia diminuta de 0.0004). Incluso en la época 19 la diferencia es de apenas 0.0037 (0.5897 vs 0.5934).")
    add_bullet(doc, "Prueba 2 — ¿Por qué en las primeras épocas la línea Naranja (Validación) está más abajo que la Azul (Train)? ", "Porque durante el entrenamiento (azul) el modelo tiene activado el Dropout (apaga el 15%–20% de sus neuronas al azar para obligarse a esforzarse más), mientras que al presentar el simulacro de Validación (naranja) usa el 100% de sus neuronas.")
    add_bullet(doc, "Prueba 3 — Consistencia en 65 pruebas con 5 Semillas Aleatorias: ", "Al repetir el entrenamiento con 5 semillas distintas (42, 1, 7, 21, 2026), la variación del ROC-AUC fue de apenas ±0.00029 (0.029%). Un modelo que memoriza cambia drásticamente según la semilla; uno que aprende llega siempre a la misma conclusión.")
    add_bullet(doc, "Prueba 4 — Examen Final en los 7,448 clientes ocultos de Test: ", "Al abrir por primera vez los 7,448 clientes de Test, el ROC-AUC pasó de 0.75382 (Validación) a 0.74482 (Test): una variación de apenas -0.00900 (menos de 1%). Esto confirma científicamente que el conocimiento adquirido generaliza a clientes nuevos.")

    # =========================================================================
    # SECCIÓN 6: CHULETA RÁPIDA DE SUSTENTACIÓN
    # =========================================================================
    add_heading_1(doc, "6. Resumen Ejecutivo: Respuestas de 30 Segundos para la Exposición")
    add_styled_table(
        doc,
        ["Pregunta", "Respuesta Clara y Contundente para Decir en la Presentación"],
        [
            ["1. ¿Qué métodos usaron?", "Aplicamos partición estratificada 70/15/15 sin fuga de datos, transformamos las 21 variables base en 44 características normalizadas (banderas de nulos, clipping p1–p99, logaritmos, mediana y One-Hot Encoding) y entrenamos un Comité Ensamble de 3 Redes Neuronales MLP diversas ([64,32,16] ReLU, [32,16] LeakyReLU y [64,32,16] Dropout 0.20)."],
            ["2. ¿Cuál es el error y cómo se explica?", "En probabilidades, logramos un Log Loss de 0.5963 y Brier de 0.2050 (muy por debajo del azar de 0.6931 y 0.2500), con un ROC-AUC de 0.7448. En los 7,448 clientes de Test acertamos el 67.48% (5,026 clientes) y el error del 32.52% está balanceado entre 15.76% de Falsos Positivos (riesgo de morosidad) y 16.76% de Falsos Negativos (costo comercial)."],
            ["3. ¿Cuántas pruebas y épocas hicieron y por qué?", "Ejecutamos 166 pruebas documentadas (84 arquitecturas, 5 ablaciones, 65 corridas multi-semilla y 16 ensambles). Con un tope de 120 épocas y Early Stopping (paciencia de 10–12 épocas), cada modelo paró automáticamente en su punto exacto de convergencia entre 24 y 83 épocas (guardando sus mejores pesos en las épocas 32, 71 y 45)."],
            ["4. ¿Cómo justifican cada etapa?", "Cada etapa respondió una pregunta científica: el Baseline fijó la referencia (AUC 0.7418); la Fase 1 y la Ablación probaron que 44 variables y redes piramidales compactas eran óptimas; la Fase 2 calibró la regularización L2 y la paciencia; y la Fase 3 unió modelos con distinta activación en el Ensamble Top-3 (AUC 0.7448)."],
            ["5. ¿El modelo memorizó o aprendió?", "Aprendió y NO memorizó: en la gráfica de aprendizaje, las curvas de entrenamiento (0.5929) y validación (0.5933) bajan juntas y se estabilizan pegadas con una brecha de apenas 0.0004 sin que la validación suba jamás, y en los 7,448 clientes nuevos de Test el AUC varió menos del 1% (-0.0090)."]
        ]
    )

    out_paths = [
        "docs/GUIA_EXPLICATIVA_MODELO_CREDIRISK.docx",
        "GUIA_EXPLICATIVA_MODELO_CREDIRISK.docx"
    ]
    for p in out_paths:
        doc.save(p)
        print(f"Saved: {os.path.abspath(p)} ({os.path.getsize(p):,} bytes)")

if __name__ == "__main__":
    build_docx()
