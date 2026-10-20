#!/usr/bin/env python3
"""
Script para procesar y mejorar las fotos del equipo de CrediRisk:
- Remoción de fondo automática mediante rembg (U^2-Net)
- Encuadre óptimo de retrato (cabeza y torso superior centrado)
- Realce de contraste, luminosidad, nitidez y tono
- Integración cromática con la paleta CrediRisk (fondos oscuros #0b1120/#0f172a con halo azul eléctrico #2563eb y cian #38bdf8)
- Generación de versiones recortadas (PNG transparente) y avatares listos para credenciales
"""

import os
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import rembg
import numpy as np

OUTPUT_DIR = "frontend/public/team"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PHOTOS = [
    {
        "id": 2,
        "key": "sharick",
        "name": "Sharick Natalia Hernández Gómez",
        "src": "/Users/suntz/.gemini/antigravity/brain/e36f2d6e-1258-4fb2-a446-7a568418f166/.user_uploaded/media_1792463670021_781ebaab.jpg",
        "crop_box": (30, 40, 738, 980), # (left, top, right, bottom)
        "contrast": 1.08,
        "brightness": 1.03,
        "color": 1.05,
        "sharpness": 1.25,
    },
    {
        "id": 4,
        "key": "ivan",
        "name": "Iván Camilo Solano Sánchez",
        "src": "/Users/suntz/.gemini/antigravity/brain/e36f2d6e-1258-4fb2-a446-7a568418f166/.user_uploaded/media_1792463670024_b054e46d.jpg",
        "crop_box": (40, 60, 728, 980),
        "contrast": 1.10,
        "brightness": 1.04,
        "color": 1.06,
        "sharpness": 1.30,
    },
    {
        "id": 5,
        "key": "cristian",
        "name": "Cristian Camilo Martínez Delgado",
        "src": "/Users/suntz/.gemini/antigravity/brain/e36f2d6e-1258-4fb2-a446-7a568418f166/.user_uploaded/media_1792463670027_733be766.jpg",
        "crop_box": (160, 20, 864, 760),
        "contrast": 1.12,
        "brightness": 1.05,
        "color": 1.08,
        "sharpness": 1.28,
    },
]

def enhance_portrait(img_rgba, cfg):
    """Mejora contraste, nitidez, balance de color y luminosidad de la persona recortada."""
    r, g, b, a = img_rgba.split()
    rgb = Image.merge("RGB", (r, g, b))
    
    # 1. Luminosidad
    if cfg.get("brightness", 1.0) != 1.0:
        enhancer = ImageEnhance.Brightness(rgb)
        rgb = enhancer.enhance(cfg["brightness"])
    
    # 2. Contraste sutil
    if cfg.get("contrast", 1.0) != 1.0:
        enhancer = ImageEnhance.Contrast(rgb)
        rgb = enhancer.enhance(cfg["contrast"])
        
    # 3. Saturación / viveza de color
    if cfg.get("color", 1.0) != 1.0:
        enhancer = ImageEnhance.Color(rgb)
        rgb = enhancer.enhance(cfg["color"])
        
    # 4. Nitidez para detalles en cabello y ojos
    if cfg.get("sharpness", 1.0) != 1.0:
        enhancer = ImageEnhance.Sharpness(rgb)
        rgb = enhancer.enhance(cfg["sharpness"])
        
    # Suavizado sutil de máscara alfa en los bordes para eliminar cualquier halo
    a_smooth = a.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    r_n, g_n, b_n = rgb.split()
    return Image.merge("RGBA", (r_n, g_n, b_n, a_smooth))

def create_credirisk_avatar(cutout_img, size=600):
    """
    Crea un avatar circular/cuadrado con el fondo exacto de CrediRisk:
    - Gradiente profundo azul/slate (#0b1120 a #0f172a a #020617)
    - Halo radial cyan/azul eléctrico (#2563eb / #38bdf8) detrás del sujeto
    - Borde sutil de anillo tecnológico
    """
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    
    # Crear fondo gradiente
    bg = Image.new("RGBA", (size, size))
    bg_data = np.zeros((size, size, 4), dtype=np.uint8)
    
    # Centro para el gradiente radial
    cx, cy = size // 2, int(size * 0.45)
    max_radius = size * 0.65
    
    # Paleta CrediRisk
    # Color central del halo: azul eléctrico / cian (37, 99, 235) / (56, 189, 248)
    # Color medio: azul pizarra profundo (15, 23, 42)
    # Color exterior: azul noche casi negro (11, 17, 32)
    for y in range(size):
        for x in range(size):
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            ratio = min(1.0, dist / max_radius)
            
            # Halo luminoso suave detrás de la cabeza
            halo_dist = np.sqrt((x - cx)**2 + (y - cy * 0.9)**2)
            halo_ratio = max(0.0, 1.0 - (halo_dist / (size * 0.42)))
            
            # Interpolación base
            r = int(11 * (1 - ratio) + 2 * ratio + 30 * halo_ratio)
            g = int(23 * (1 - ratio) + 6 * ratio + 70 * halo_ratio)
            b = int(45 * (1 - ratio) + 18 * ratio + 140 * halo_ratio)
            
            bg_data[y, x] = [min(255, r), min(255, g), min(255, b), 255]
            
    bg = Image.fromarray(bg_data, mode="RGBA")
    canvas.paste(bg, (0, 0))
    
    # Redimensionar y posicionar la persona recortada
    # Ajustamos para que la cabeza y hombros queden centrados y llenen armoniosamente
    cw, ch = cutout_img.size
    aspect = cw / ch
    
    target_height = int(size * 0.92)
    target_width = int(target_height * aspect)
    
    resized_person = cutout_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # Pegar persona centrada en la base
    pos_x = (size - target_width) // 2
    pos_y = size - target_height + int(size * 0.05)
    
    canvas.alpha_composite(resized_person, (pos_x, pos_y))
    
    return canvas

def main():
    print("Iniciando procesamiento de fotos de equipo CrediRisk...")
    
    for item in PHOTOS:
        print(f"\n-> Procesando {item['name']} ({item['key']})...")
        src_path = item["src"]
        
        if not os.path.exists(src_path):
            print(f"ERROR: Archivo no encontrado: {src_path}")
            continue
            
        raw_img = Image.open(src_path)
        
        # 1. Recortar área de interés antes del removedor de fondo
        crop_box = item.get("crop_box")
        if crop_box:
            cropped = raw_img.crop(crop_box)
        else:
            cropped = raw_img
            
        # 2. Remover fondo con rembg
        print("   Extrayendo fondo con U^2-Net...")
        cutout = rembg.remove(cropped)
        
        # 3. Mejoras de imagen (luz, contraste, nitidez)
        print("   Aplicando mejoras de retrato y colorimetría...")
        enhanced_cutout = enhance_portrait(cutout, item)
        
        # Guardar recorte transparente de alta resolución
        cutout_path = os.path.join(OUTPUT_DIR, f"{item['key']}-cutout.png")
        enhanced_cutout.save(cutout_path, "PNG", optimize=True)
        print(f"   ✓ Guardado recorte PNG transparente: {cutout_path}")
        
        # 4. Crear versión integrada con el fondo CrediRisk
        print("   Componiendo con paleta de color CrediRisk (#0b1120 / #2563eb / #38bdf8)...")
        avatar_img = create_credirisk_avatar(enhanced_cutout, size=600)
        avatar_path = os.path.join(OUTPUT_DIR, f"{item['key']}.png")
        avatar_img.save(avatar_path, "PNG", optimize=True)
        print(f"   ✓ Guardado avatar integrado: {avatar_path}")

    print("\nProcesamiento finalizado con éxito.")

if __name__ == "__main__":
    main()
