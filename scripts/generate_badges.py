#!/usr/bin/env python3
"""
Generador de tarjetas 3D minimalistas estilo ReactBits / CrediRisk:
- Sin banners, sin cajas, sin códigos de barras ni círculos.
- Fondo en la paleta oscura de la página (#0b1120 -> #0f172a -> #070b16) con halo azul/cian sutil.
- Descontaminación de color en bordes (elimina cualquier halo blanco de la pared original en el cabello).
- Retrato recortado limpio en la parte inferior con una línea die-cut sutil (15% opacidad).
"""

import os
import shutil
import numpy as np
import rembg
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

WIDTH = 800
HEIGHT = 1125
OUTPUT_DIR = "frontend/public/team"
DIST_DIR = "frontend/dist/team"
BRAND_DIR = "frontend/public/brand"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DIST_DIR, exist_ok=True)

RAW_PHOTOS = {
    "sharick": {
        "src": "/Users/suntz/.gemini/antigravity/brain/e36f2d6e-1258-4fb2-a446-7a568418f166/.user_uploaded/media_1792463670021_781ebaab.jpg",
        "crop": (0, 80, 768, 700),
        "brightness": 1.04,
        "contrast": 1.12,
        "sharpness": 1.30,
        "target_h": 790,
    },
    "laura": {
        "src": "/Users/suntz/.gemini/antigravity/brain/e36f2d6e-1258-4fb2-a446-7a568418f166/.user_uploaded/media_1792515182635_d1e76ba0.jpg",
        "crop": (0, 315, 472, 625),
        "brightness": 1.04,
        "contrast": 1.12,
        "sharpness": 1.38,
        "target_h": 790,
    },
    "ivan": {
        "src": "/Users/suntz/.gemini/antigravity/brain/e36f2d6e-1258-4fb2-a446-7a568418f166/.user_uploaded/media_1792463670024_b054e46d.jpg",
        "crop": (0, 100, 768, 750),
        "brightness": 1.05,
        "contrast": 1.14,
        "sharpness": 1.30,
        "target_h": 790,
    },
    "cristian": {
        "src": "/Users/suntz/.gemini/antigravity/brain/e36f2d6e-1258-4fb2-a446-7a568418f166/.user_uploaded/media_1792463670027_733be766.jpg",
        "crop": (80, 10, 960, 769),
        "brightness": 1.07,
        "contrast": 1.14,
        "sharpness": 1.30,
        "target_h": 790,
    },
}

TEAM_MEMBERS = [
    {
        "id": 1,
        "nombre": "Leidy Vanessa Guecha Alape",
        "codigo": "67001077",
        "handle": "@lvguecha77",
        "iniciales": "LG",
        "key": None,
    },
    {
        "id": 2,
        "nombre": "Sharick Natalia Hernández Gómez",
        "codigo": "67000979",
        "handle": "@snhernandez79",
        "iniciales": "SH",
        "key": "sharick",
    },
    {
        "id": 3,
        "nombre": "Laura Sofia Diaz Suarez",
        "codigo": "67000991",
        "handle": "@lsdiaz91",
        "iniciales": "LD",
        "key": "laura",
    },
    {
        "id": 4,
        "nombre": "Iván Camilo Solano Sánchez",
        "codigo": "67001118",
        "handle": "@icsolano18",
        "iniciales": "IS",
        "key": "ivan",
    },
    {
        "id": 5,
        "nombre": "Cristian Camilo Martínez Delgado",
        "codigo": "67001140",
        "handle": "@ccmartinez40",
        "iniciales": "CM",
        "key": "cristian",
    },
]


def clean_and_grade_portrait(img_rgba, cfg):
    """
    1. Descontamina los bordes semitransparentes para eliminar el fondo blanco del cabello.
    2. Aplica colorimetría fría armónica con CrediRisk (#0b1120 / #2563eb / #38bdf8).
    """
    r, g, b, a = img_rgba.split()
    rgb = Image.merge("RGB", (r, g, b))

    rgb = ImageEnhance.Brightness(rgb).enhance(cfg.get("brightness", 1.04))
    rgb = ImageEnhance.Contrast(rgb).enhance(cfg.get("contrast", 1.12))
    rgb = ImageEnhance.Color(rgb).enhance(0.86)
    rgb = ImageEnhance.Sharpness(rgb).enhance(cfg.get("sharpness", 1.3))

    arr = np.array(rgb, dtype=np.float32)
    alpha_raw = np.array(a, dtype=np.float32) / 255.0

    # Contraer ligeramente la máscara alfa y hacer rampa suave para cortar cualquier borde blanco de pared
    a_eroded = a.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    alpha_norm = np.array(a_eroded, dtype=np.float32) / 255.0
    # Ramp: lo menor a 0.35 se vuelve 0, lo mayor a 0.85 se vuelve 1
    alpha_clean = np.clip((alpha_norm - 0.32) / 0.52, 0.0, 1.0)

    # Descontaminación de color en el borde: oscurecer píxeles de borde hacia azul noche (#0b1120)
    edge_factor = alpha_clean ** 0.75
    arr[:, :, 0] = arr[:, :, 0] * edge_factor + 11.0 * (1.0 - edge_factor)
    arr[:, :, 1] = arr[:, :, 1] * edge_factor + 17.0 * (1.0 - edge_factor)
    arr[:, :, 2] = arr[:, :, 2] * edge_factor + 32.0 * (1.0 - edge_factor)

    # Armonización tonal con la paleta azul/cian de la página
    lum = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]) / 255.0
    shadow_weight = (1.0 - lum) ** 1.5
    mid_weight = 4.0 * lum * (1.0 - lum)

    arr[:, :, 0] = arr[:, :, 0] * 0.95 - shadow_weight * 5.0
    arr[:, :, 1] = arr[:, :, 1] * 0.99 + mid_weight * 3.0
    arr[:, :, 2] = arr[:, :, 2] * 1.07 + shadow_weight * 16.0 + mid_weight * 8.0

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    final_a = (alpha_clean * 255.0).astype(np.uint8)

    rgba_arr = np.dstack([arr, final_a])
    return Image.fromarray(rgba_arr)


def extract_and_prepare_cutouts():
    cutouts = {}
    for key, cfg in RAW_PHOTOS.items():
        print(f"Procesando retrato limpio de {key}...")
        raw = Image.open(cfg["src"]).convert("RGB")
        cropped = raw.crop(cfg["crop"])
        cutout = rembg.remove(cropped)
        graded = clean_and_grade_portrait(cutout, cfg)

        bbox = graded.split()[3].point(lambda p: 255 if p > 20 else 0).getbbox()
        if bbox:
            graded = graded.crop((bbox[0], bbox[1], bbox[2], cropped.height))

        out_path = os.path.join(OUTPUT_DIR, f"{key}-cutout.png")
        graded.save(out_path, "PNG")
        cutouts[key] = (graded, cfg.get("target_h", 790))
    return cutouts


def create_base_card():
    """
    Superficie oscura CrediRisk (#0b1120 -> #0f172a -> #060b16) con halo azul/cian suave.
    """
    y_idx, x_idx = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float32)
    ratio_y = y_idx / HEIGHT

    r = 12 * (1 - ratio_y) + 6 * ratio_y
    g = 19 * (1 - ratio_y) + 10 * ratio_y
    b = 35 * (1 - ratio_y) + 22 * ratio_y

    # Halo radial azul/cian detrás del retrato
    cx, cy = WIDTH * 0.5, HEIGHT * 0.58
    dist = np.sqrt(((x_idx - cx) / (WIDTH * 0.48)) ** 2 + ((y_idx - cy) / (HEIGHT * 0.38)) ** 2)
    glow = np.clip(1.0 - dist, 0.0, 1.0) ** 1.8

    r += glow * 20
    g += glow * 52
    b += glow * 115

    arr = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    arr[:, :, 0] = np.clip(r, 0, 255).astype(np.uint8)
    arr[:, :, 1] = np.clip(g, 0, 255).astype(np.uint8)
    arr[:, :, 2] = np.clip(b, 0, 255).astype(np.uint8)
    arr[:, :, 3] = 255

    card = Image.fromarray(arr)

    # Marca de agua del logo CrediRisk arriba a la izquierda (más luminosa y visible)
    logo_path = os.path.join(BRAND_DIR, "credirisk-icon-192.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA").resize((138, 138), Image.Resampling.LANCZOS)
        lr, lg, lb, la = logo.split()
        l_rgb = Image.merge("RGB", (lr, lg, lb))
        l_rgb = ImageEnhance.Brightness(l_rgb).enhance(1.55)
        l_rgb = ImageEnhance.Color(l_rgb).enhance(1.25)
        lr2, lg2, lb2 = l_rgb.split()
        la = la.point(lambda p: int(p * 0.52))
        watermark = Image.merge("RGBA", (lr2, lg2, lb2, la))
        card.alpha_composite(watermark, (64, 82))

    return card


def add_portrait_to_card(card, cutout_img, target_h=790):
    cw, ch = cutout_img.size
    scale = target_h / ch
    target_w = int(cw * scale)

    person = cutout_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    px = (WIDTH - target_w) // 2
    py = HEIGHT - target_h

    person_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    person_layer.paste(person, (px, py))

    # Contorno die-cut ultra sutil (solo una línea fina translúcida a 14px de la silueta, sin relleno blanco)
    alpha = person_layer.split()[3]
    binary_mask = alpha.point(lambda p: 255 if p > 80 else 0)

    outer = binary_mask.filter(ImageFilter.MaxFilter(29))
    inner = binary_mask.filter(ImageFilter.MaxFilter(25))
    ring_arr = np.clip(np.array(outer, dtype=np.int16) - np.array(inner, dtype=np.int16), 0, 255).astype(np.float32)
    ring_img = Image.fromarray(ring_arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))

    # Crear capa RGBA para la línea die-cut con opacidad baja (18%) en azul cian pizarra
    ring_alpha = (np.array(ring_img, dtype=np.float32) * 0.18).astype(np.uint8)
    diecut_rgba = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    diecut_rgba[:, :, 0] = 96
    diecut_rgba[:, :, 1] = 165
    diecut_rgba[:, :, 2] = 250
    diecut_rgba[:, :, 3] = ring_alpha
    card.alpha_composite(Image.fromarray(diecut_rgba))

    # Componer retrato limpio
    card.alpha_composite(person_layer)

    # Viñeta inferior suave para fundir la base con el borde inferior de la tarjeta
    v_arr = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    fade_start = int(HEIGHT * 0.82)
    for y in range(fade_start, HEIGHT):
        t = ((y - fade_start) / (HEIGHT - fade_start)) ** 1.6
        v_arr[y, :, 0] = 6
        v_arr[y, :, 1] = 10
        v_arr[y, :, 2] = 22
        v_arr[y, :, 3] = int(t * 170)
    card.alpha_composite(Image.fromarray(v_arr))


def add_minimal_silhouette(card, member):
    sil_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(sil_layer)

    cx = WIDTH // 2
    head_cy = 530
    head_r = 120
    s_draw.ellipse([(cx - head_r, head_cy - head_r), (cx + head_r, head_cy + head_r)], fill=(15, 23, 42, 235), outline=(56, 189, 248, 70), width=2)
    s_draw.ellipse([(cx - 310, 700), (cx + 310, 1340)], fill=(15, 23, 42, 235), outline=(56, 189, 248, 70), width=2)

    font_init = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", 68)
    s_draw.text((cx, head_cy), member["iniciales"], font=font_init, fill=(125, 211, 252, 200), anchor="mm")

    card.alpha_composite(sil_layer)


def render_member_card(member, cutouts):
    card = create_base_card()

    key = member.get("key")
    if key and key in cutouts:
        cutout_img, target_h = cutouts[key]
        add_portrait_to_card(card, cutout_img, target_h=target_h)
        avatar_out = os.path.join(OUTPUT_DIR, f"{key}.png")
        card.save(avatar_out, "PNG")
        shutil.copy2(avatar_out, os.path.join(DIST_DIR, f"{key}.png"))
    else:
        add_minimal_silhouette(card, member)

    draw = ImageDraw.Draw(card)
    font_handle = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", 23)
    draw.text((WIDTH - 56, 70), member["handle"], font=font_handle, fill=(148, 163, 184, 180), anchor="rm")

    return card


def update_card_back():
    y_idx, x_idx = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float32)
    ratio_y = y_idx / HEIGHT

    r = 13 * (1 - ratio_y) + 7 * ratio_y
    g = 21 * (1 - ratio_y) + 12 * ratio_y
    b = 38 * (1 - ratio_y) + 26 * ratio_y

    cx, cy = WIDTH * 0.5, HEIGHT * 0.48
    dist = np.sqrt(((x_idx - cx) / (WIDTH * 0.46)) ** 2 + ((y_idx - cy) / (HEIGHT * 0.36)) ** 2)
    glow = np.clip(1.0 - dist, 0.0, 1.0) ** 1.7

    r += glow * 28
    g += glow * 72
    b += glow * 155

    arr = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    arr[:, :, 0] = np.clip(r, 0, 255).astype(np.uint8)
    arr[:, :, 1] = np.clip(g, 0, 255).astype(np.uint8)
    arr[:, :, 2] = np.clip(b, 0, 255).astype(np.uint8)
    arr[:, :, 3] = 255
    back = Image.fromarray(arr)

    logo_path = os.path.join(BRAND_DIR, "credirisk-icon-512.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA").resize((380, 380), Image.Resampling.LANCZOS)
        lr, lg, lb, la = logo.split()
        l_rgb = Image.merge("RGB", (lr, lg, lb))
        l_rgb = ImageEnhance.Brightness(l_rgb).enhance(1.45)
        l_rgb = ImageEnhance.Contrast(l_rgb).enhance(1.15)
        l_rgb = ImageEnhance.Color(l_rgb).enhance(1.20)
        lr2, lg2, lb2 = l_rgb.split()

        glow_logo = Image.merge("RGBA", (lr2, lg2, lb2, la.point(lambda p: int(p * 0.55)))).filter(ImageFilter.GaussianBlur(14))
        pos = ((WIDTH - 380) // 2, (HEIGHT - 380) // 2 - 25)
        back.alpha_composite(glow_logo, pos)

        bright_logo = Image.merge("RGBA", (lr2, lg2, lb2, la.point(lambda p: int(p * 0.95))))
        back.alpha_composite(bright_logo, pos)

    draw = ImageDraw.Draw(back)
    font_bottom = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", 23)
    draw.text((WIDTH // 2, HEIGHT - 85), "credirisk · ucatolica.edu.co", font=font_bottom, fill=(186, 230, 253, 210), anchor="mm")

    out_path = os.path.join(BRAND_DIR, "credirisk-card-back.png")
    back.save(out_path, "PNG", optimize=True)
    dist_brand = "frontend/dist/brand"
    os.makedirs(dist_brand, exist_ok=True)
    shutil.copy2(out_path, os.path.join(dist_brand, "credirisk-card-back.png"))


def main():
    cutouts = extract_and_prepare_cutouts()
    for m in TEAM_MEMBERS:
        badge = render_member_card(m, cutouts)
        out_path = os.path.join(OUTPUT_DIR, f"badge-{m['id']}.png")
        badge.save(out_path, "PNG", optimize=True)
        shutil.copy2(out_path, os.path.join(DIST_DIR, f"badge-{m['id']}.png"))
        print(f"✓ Generada tarjeta limpia: {out_path}")
    update_card_back()
    print("✓ Reverso luminoso actualizado.")


if __name__ == "__main__":
    main()
