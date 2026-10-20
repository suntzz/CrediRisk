#!/usr/bin/env python3
"""
Script para generar las texturas frontales de alta resolución (800x1125)
de las credenciales 3D de CrediRisk para los 5 integrantes del equipo.
Integra las fotos procesadas y mejoradas con la estética y paleta de la web.
"""

import os
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH = 800
HEIGHT = 1125
OUTPUT_DIR = "frontend/public/team"
DIST_DIR = "frontend/dist/team"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DIST_DIR, exist_ok=True)

TEAM_MEMBERS = [
    {
        "id": 1,
        "nombre": "Leidy Vanessa Guecha Alape",
        "codigo": "67001077",
        "correo": "lvguecha77@ucatolica.edu.co",
        "iniciales": "LG",
        "photo": None,
    },
    {
        "id": 2,
        "nombre": "Sharick Natalia Hernández Gómez",
        "codigo": "67000979",
        "correo": "snhernandez79@ucatolica.edu.co",
        "iniciales": "SH",
        "photo": "sharick-avatar-v2.png",
    },
    {
        "id": 3,
        "nombre": "Laura Sofia Diaz Suarez",
        "codigo": "67000991",
        "correo": "lsdiaz91@ucatolica.edu.co",
        "iniciales": "LD",
        "photo": None,
    },
    {
        "id": 4,
        "nombre": "Iván Camilo Solano Sánchez",
        "codigo": "67001118",
        "correo": "icsolano18@ucatolica.edu.co",
        "iniciales": "IS",
        "photo": "ivan-avatar-v2.png",
    },
    {
        "id": 5,
        "nombre": "Cristian Camilo Martínez Delgado",
        "codigo": "67001140",
        "correo": "ccmartinez40@ucatolica.edu.co",
        "iniciales": "CM",
        "photo": "cristian-avatar-v2.png",
    },
]

def render_badge(member):
    # 1. Fondo gradiente profundo CrediRisk: #0b1120 -> #0f172a -> #020617
    bg_arr = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        if ratio < 0.5:
            r = 11 * (1 - ratio*2) + 15 * (ratio*2)
            g = 17 * (1 - ratio*2) + 23 * (ratio*2)
            b = 32 * (1 - ratio*2) + 42 * (ratio*2)
        else:
            r2 = (ratio - 0.5) * 2
            r = 15 * (1 - r2) + 2 * r2
            g = 23 * (1 - r2) + 6 * r2
            b = 42 * (1 - r2) + 23 * r2
        bg_arr[y, :, 0] = int(r)
        bg_arr[y, :, 1] = int(g)
        bg_arr[y, :, 2] = int(b)
        bg_arr[y, :, 3] = 255
    img = Image.fromarray(bg_arr)
    draw = ImageDraw.Draw(img)

    # 2. Header banner gradiente azul tecnológico: #1d4ed8 -> #2563eb -> #3b82f6
    for x in range(WIDTH):
        ratio = x / WIDTH
        if ratio < 0.5:
            r = int(29 * (1 - ratio*2) + 37 * (ratio*2))
            g = int(78 * (1 - ratio*2) + 99 * (ratio*2))
            b = int(216 * (1 - ratio*2) + 235 * (ratio*2))
        else:
            r2 = (ratio - 0.5) * 2
            r = int(37 * (1 - r2) + 59 * r2)
            g = int(99 * (1 - r2) + 130 * r2)
            b = int(235 * (1 - r2) + 246 * r2)
        draw.line([(x, 0), (x, 140)], fill=(r, g, b, 255))

    # Línea decorativa dorada
    draw.rectangle([(0, 140), (WIDTH, 144)], fill=(245, 158, 11, 255))

    # Fuentes
    font_bold = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 26)
    font_sub = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 17)
    font_lab = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 14)
    font_name = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 31)
    font_pill = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 15)
    font_box_label = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 15)
    font_code = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 28)
    font_email = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 20)
    font_footer_id = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 14)
    font_footer_text = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 13)

    # Textos del encabezado
    draw.text((WIDTH / 2, 45), 'UNIVERSIDAD CATÓLICA DE COLOMBIA', font=font_bold, fill=(255, 255, 255, 255), anchor='mm')
    draw.text((WIDTH / 2, 85), 'FACULTAD DE INGENIERÍA · SISTEMAS', font=font_sub, fill=(255, 255, 255, 230), anchor='mm')
    draw.text((WIDTH / 2, 115), 'CREDIRISK NEURAL LAB', font=font_lab, fill=(255, 255, 255, 190), anchor='mm')

    # Ranura del Lanyard (Slot indicator)
    draw.rounded_rectangle([(WIDTH / 2 - 80, 156), (WIDTH / 2 + 80, 180)], radius=8, outline=(255, 255, 255, 50), width=2)

    # Contenedor del Avatar en (400, 350) con radio 120 (diámetro 240)
    cx, cy = WIDTH // 2, 350
    radius = 120

    # Halo radial de luz azul eléctrica detrás del avatar
    glow_size = 350
    glow_img = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_draw.ellipse([(20, 20), (glow_size - 20, glow_size - 20)], fill=(37, 99, 235, 110))
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(40))
    img.alpha_composite(glow_img, (cx - glow_size // 2, cy - glow_size // 2))

    # Avatar: Foto o Monograma
    photo_file = member.get("photo")
    if photo_file:
        photo_path = os.path.join(OUTPUT_DIR, photo_file)
        if os.path.exists(photo_path):
            circ_photo = Image.open(photo_path).convert('RGBA').resize((radius * 2, radius * 2), Image.Resampling.LANCZOS)
            img.alpha_composite(circ_photo, (cx - radius, cy - radius))
    else:
        # Monograma elegante
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=(30, 41, 59, 255))
        font_mono_large = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 82)
        draw.text((cx, cy), member['iniciales'], font=font_mono_large, fill=(96, 165, 250, 255), anchor='mm')

    # Anillo exterior doble con estética de cian / azul brillante
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], outline=(37, 99, 235, 255), width=6)
    draw.ellipse([(cx - radius - 3, cy - radius - 3), (cx + radius + 3, cy + radius + 3)], outline=(56, 189, 248, 140), width=2)

    # Nombre del estudiante centrado
    draw.text((WIDTH / 2, 535), member['nombre'].upper(), font=font_name, fill=(255, 255, 255, 255), anchor='mm')

    # Pill: Credencial de Investigador
    pill_w, pill_h = 340, 36
    px1, py1 = WIDTH / 2 - pill_w / 2, 575
    px2, py2 = WIDTH / 2 + pill_w / 2, py1 + pill_h
    draw.rounded_rectangle([(px1, py1), (px2, py2)], radius=18, fill=(30, 58, 138, 200), outline=(96, 165, 250, 180), width=2)
    draw.text((WIDTH / 2, py1 + pill_h / 2), 'CREDENCIAL DE INVESTIGADOR', font=font_pill, fill=(186, 230, 253, 255), anchor='mm')

    # Caja de datos institucionales
    bx1, by1 = WIDTH / 2 - 330, 655
    bx2, by2 = WIDTH / 2 + 330, by1 + 195
    draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=16, fill=(15, 23, 42, 230), outline=(51, 65, 85, 200), width=2)

    draw.text((bx1 + 36, by1 + 32), 'CÓDIGO INSTITUCIONAL', font=font_box_label, fill=(148, 163, 184, 255))
    draw.text((bx1 + 36, by1 + 60), member['codigo'], font=font_code, fill=(56, 189, 248, 255))

    draw.line([(bx1 + 36, by1 + 104), (bx2 - 36, by1 + 104)], fill=(51, 65, 85, 180), width=1)

    draw.text((bx1 + 36, by1 + 124), 'CORREO INSTITUCIONAL', font=font_box_label, fill=(148, 163, 184, 255))
    draw.text((bx1 + 36, by1 + 152), member['correo'], font=font_email, fill=(226, 232, 240, 255))

    # Código de barras
    bar_y = 905
    draw.rectangle([(WIDTH / 2 - 250, bar_y), (WIDTH / 2 + 250, bar_y + 65)], fill=(255, 255, 255, 255))
    
    curr_x = WIDTH / 2 - 230
    seed = (member['id'] * 17 + int(member['codigo'][-4:])) % 1000
    for i in range(68):
        bw = 5 if (i * 7 + seed) % 5 == 0 else (3 if i % 3 == 0 else 1.5)
        if (i * 11 + seed) % 7 != 2:
            draw.rectangle([(curr_x, bar_y + 6), (curr_x + bw, bar_y + 59)], fill=(0, 0, 0, 255))
        curr_x += bw + 3
        if curr_x > WIDTH / 2 + 230:
            break

    # Textos de autenticidad en el pie
    cod = member['codigo']
    draw.text((WIDTH / 2, 1025), f'VERIFICACIÓN DE AUTENTICIDAD · ID: {cod}', font=font_footer_id, fill=(100, 116, 139, 255), anchor='mm')
    draw.text((WIDTH / 2, 1055), 'Bogotá D.C., Colombia · Redes Neuronales Profundas', font=font_footer_text, fill=(71, 85, 105, 255), anchor='mm')

    return img

def main():
    print("Generando las 5 credenciales de equipo...")
    for m in TEAM_MEMBERS:
        badge = render_badge(m)
        out_file = os.path.join(OUTPUT_DIR, f"badge-{m['id']}.png")
        badge.save(out_file, "PNG", optimize=True)
        # Copiar también a dist
        dist_file = os.path.join(DIST_DIR, f"badge-{m['id']}.png")
        shutil.copy2(out_file, dist_file)
        print(f"✓ Guardado {out_file} y {dist_file}")

if __name__ == "__main__":
    main()
