"""
procesador_imagenes_ml.py
Estandariza fotos de producto multimarca para e-commerce.

Características:
  - Lienzo final ajustable (por defecto 1200x1500 px).
  - Fondo de color uniforme (por defecto #F5F5F5).
  - Productos principales: auto-trim, escalado inteligente y anclaje inferior (Bottom-Anchoring) / Centrado Absoluto.
  - Fotos de detalles y modelos (lifestyle): detección geométrica ("Regla de los Bordes")
    y enrutamiento por nombre para aplicar "Full Bleed" (Center Crop).
  - Remoción de fondo automática para JPGs mediante rembg (si está disponible) o croma-key de fallback.
  - Filtro de erosión de 1px para evitar halos blancos en vestuario y accesorios.
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


# ── CONFIGURACIONES POR DEFECTO ──────────────────────────────────────────────
CANVAS_W, CANVAS_H = 1200, 1500
BG_COLOR = (245, 245, 245)  # #F5F5F5
MAX_PRODUCT_W, MAX_PRODUCT_H = 950, 1100
MAX_PRODUCT_W_SIDE = 950  # Ancho máximo para fotos de perfil/costado (horizontales)
MAX_PRODUCT_W_ADIDAS_SIDE = 820  # Ancho máximo exclusivo para vistas 0003 y 0005 de Adidas
MAX_PRODUCT_W_ADIDAS_0004 = 900  # Reducido en 50px
MAX_PRODUCT_H_ADIDAS_0004 = 1050 # Reducido en 50px
MAX_PRODUCT_W_NB_REDUCED = 900   # Igualado a Adidas para vistas 0004 y 0005 de NB
MAX_PRODUCT_H_NB_REDUCED = 1050  # Igualado a Adidas
MAX_PRODUCT_W_ASICS_REDUCED = 900 # Reducido en 50px para vistas 0004, 0006 y 0007 de ASICS
MAX_PRODUCT_H_ASICS_REDUCED = 1050 # Reducido en 50px para vistas 0004, 0006 y 0007 de ASICS

# Nuevas marcas: dimensiones y márgenes específicos
MAX_PRODUCT_W_FJALLRAVEN = 820   # Márgenes súper generosos para mochilas Fjällräven
MAX_PRODUCT_H_FJALLRAVEN = 950
MAX_PRODUCT_W_TIMBERLAND_ACC = 820  # Para mochilas y bolsos voluminosos de Timberland
MAX_PRODUCT_H_TIMBERLAND_ACC = 950
MAX_PRODUCT_W_CROCS = 900        # Reducido para neutralizar volumen masivo de Crocs
MAX_PRODUCT_H_CROCS = 1000
MAX_PRODUCT_W_HEYDUDE = 920      # Reducido para mantener la ligereza y elegancia de Hey Dude
MAX_PRODUCT_H_HEYDUDE = 1050

BORDER_THRESHOLD_PX = 8  # Umbral para detectar contacto con bordes

ADIDAS_VIEW_MAPPING = {
    "1": "0001", "5": "0002", "6": "0003", "3": "0004", "7": "0005", "4": "0006",
    "8": "0007", "9": "0008", "10": "0009", "11": "0010", "12": "0011",
    "13": "0012", "14": "0013", "15": "0014", "16": "0015", "17": "0016",
    "18": "0017", "19": "0018",
}

ASICS_VIEW_MAPPING = {
    # Calzado
    "_SR_RT_GLB": "-0001", "_SR_LT_GLB": "-0002", "_SB_FR_GLB": "-0003",
    "_SB_TP_GLB": "-0004", "_SB_FL_GLB": "-0005", "_SB_BT_GLB": "-0006",
    "_SB_BK_GLB": "-0007",
    # Textil Masculino
    "_GM_FT_GLB": "-0001", "_NM_FT_GLB": "-0002", "_GM_BK_GLB": "-0003",
    "_GM_SD_GLB": "-0004", "_GM_Z1_GLB": "-0005", "_GM_Z2_GLB": "-0006",
    "_GM_Z3_GLB": "-0007", "_GM_Z4_GLB": "-0008", "_GM_Z5_GLB": "-0009",
    "_GM_Z6_GLB": "-0010", "_GM_Z7_GLB": "-0011",
    # Textil Femenino
    "_GF_FT_GLB": "-0001", "_GF_BK_GLB": "-0003", "_GF_SD_GLB": "-0004",
    "_GF_Z1_GLB": "-0005", "_GF_Z2_GLB": "-0006", "_GF_Z3_GLB": "-0007",
    "_GF_Z4_GLB": "-0008", "_GF_Z5_GLB": "-0009", "_GF_Z6_GLB": "-0010",
    "_GF_Z7_GLB": "-0011",
    # Accesorios
    "_AC_FT_GLB": "-0001", "_AC_BK_GLB": "-0002", "_AC_SD_GLB": "-0003",
    "_AC_Z1_GLB": "-0004", "_AC_Z2_GLB": "-0005", "_AC_Z3_GLB": "-0006",
    "_AC_Z4_GLB": "-0007"
}

NB_VIEW_MAPPING = {
    "_2": "-0-0001",
    "_3": "-0-0002",
    "_5": "-0-0003",
    "_4": "-0-0004",
    "_7": "-0-0005",
    "_6": "-0-0006"
}

TIMBERLAND_CALZADO_VIEW_MAPPING = {
    "1": "0001",
    "2": "0004",
    "3": "0006",
    "4": "0003",
    "5": "0005",
    "6": "0002",
    "7": "0008",
    "9": "0007",
}

CONVERSE_VIEW_MAPPING = {
    "_A_107X1": "-0001", "_107X1": "-0001",
    "_A_108X1": "-0002", "_108X1": "-0002",
    "_A_109X1": "-0003", "_109X1": "-0003",
    "_A_110X1": "-0004", "_110X1": "-0004",
    "_A_111X1": "-0005", "_111X1": "-0005",
    "_A_112X1": "-0006", "_112X1": "-0006",
    "_A_113X1": "-0007", "_113X1": "-0007",
}

DIESEL_VIEW_MAPPING = {
    "-1": "-0001",
    "-2": "-0002",
    "-3": "-0003",
    "-4": "-0004",
    "-5": "-0005",
    "-6": "-0006",
    "-7": "-0007",
    "-8": "-0008",
    "-9": "-0009",
}


# ── DETECCIÓN GEOMÉTRICA Y SEMÁNTICA ─────────────────────────────────────────
def tiene_transparencia_real(img_pil: Image.Image) -> bool:
    if img_pil.mode in ('RGBA', 'LA') or (img_pil.mode == 'P' and 'transparency' in img_pil.info):
        alpha = img_pil.convert('RGBA').split()[-1]
        extrema = alpha.getextrema()
        if extrema[0] < 255:  # Tiene al menos un pixel con transparencia
            return True
    return False

def normalize_background_to_white(img_rgb: Image.Image) -> Image.Image:
    """Detecta el color de fondo de las esquinas y lo normaliza a blanco (255, 255, 255)."""
    width, height = img_rgb.size
    corners = [img_rgb.getpixel((0, 0)), img_rgb.getpixel((width - 1, 0)),
               img_rgb.getpixel((0, height - 1)), img_rgb.getpixel((width - 1, height - 1))]
    bg_color = tuple(int(sum(c[i] for c in corners) / 4) for i in range(3))
    
    # Evitar división por cero
    bg_r = max(1, bg_color[0])
    bg_g = max(1, bg_color[1])
    bg_b = max(1, bg_color[2])

    r, g, b = img_rgb.split()
    r = r.point(lambda i: min(255, int(i * 255 / bg_r)))
    g = g.point(lambda i: min(255, int(i * 255 / bg_g)))
    b = b.point(lambda i: min(255, int(i * 255 / bg_b)))
    return Image.merge("RGB", (r, g, b))

def get_shadow_bbox(img_rgb: Image.Image):
    """Obtiene el bounding box que incluye el producto y su sombra comparando contra el color de fondo."""
    width, height = img_rgb.size
    corners = [img_rgb.getpixel((0, 0)), img_rgb.getpixel((width - 1, 0)),
               img_rgb.getpixel((0, height - 1)), img_rgb.getpixel((width - 1, height - 1))]
    bg_color = tuple(int(sum(c[i] for c in corners) / 4) for i in range(3))
    bg_img = Image.new("RGB", (width, height), bg_color)
    diff = ImageChops.difference(img_rgb, bg_img)
    diff_l = diff.convert("L")
    mask = diff_l.point(lambda p: 255 if p > 10 else 0)
    return mask.getbbox()


def obtener_subcategoria_timberland(file_path: Path) -> str:
    """
    Analiza la ruta o geométricamente la imagen para determinar la subcategoría.
    """
    path_lower = str(file_path).lower()
    if "vestuario" in path_lower or "ropa" in path_lower or "apparel" in path_lower:
        return "VESTUARIO"
    if "accesorio" in path_lower or "accs" in path_lower or "acc" in path_lower.split(os.sep):
        return "ACCESORIO"
    if "calzado" in path_lower or "shoes" in path_lower or "footwear" in path_lower:
        return "CALZADO"

    stem = file_path.stem
    import re
    parts = re.split(r'[_\\-]', stem)
    sku = parts[0] if parts else stem
    
    parent_dir = file_path.parent
    portadas = (
        list(parent_dir.glob(f"{sku}_1.*")) + 
        list(parent_dir.glob(f"{sku}_01.*")) + 
        list(parent_dir.glob(f"{sku}-1.*")) +
        list(parent_dir.glob(f"{sku}_1_*.jpg")) +
        list(parent_dir.glob(f"{sku}-0001.*"))
    )
    if not portadas:
        portada_file = file_path
    else:
        portada_file = portadas[0]
        
    try:
        img = Image.open(portada_file)
        img_rgb = img.convert("RGB")
        w, h = img.size
        
        corners = [img_rgb.getpixel((0,0)), img_rgb.getpixel((w-1,0)), img_rgb.getpixel((0,h-1)), img_rgb.getpixel((w-1,h-1))]
        bg_r = sum(c[0] for c in corners) // 4
        bg_g = sum(c[1] for c in corners) // 4
        bg_b = sum(c[2] for c in corners) // 4
        
        bbox_left, bbox_top, bbox_right, bbox_bottom = w, h, 0, 0
        for y in range(0, h, 15):
            for x in range(0, w, 15):
                p = img_rgb.getpixel((x, y))
                dist = ((p[0]-bg_r)**2 + (p[1]-bg_g)**2 + (p[2]-bg_b)**2)**0.5
                if dist > 20:
                    if x < bbox_left: bbox_left = x
                    if x > bbox_right: bbox_right = x
                    if y < bbox_top: bbox_top = y
                    if y > bbox_bottom: bbox_bottom = y
                    
        obj_w = bbox_right - bbox_left
        obj_h = bbox_bottom - bbox_top
        aspect = obj_w / obj_h if obj_h > 0 else 0
        
        # Margen de 20px para detectar contacto físico con bordes
        touch_bottom = bbox_bottom > h - 20
        touch_top = bbox_top < 20
        
        if aspect < 0.55 or touch_bottom or touch_top:
            return "VESTUARIO"
        elif 0.55 <= aspect < 0.75:
            return "ACCESORIO"
        else:
            return "CALZADO"
    except Exception as e:
        print(f"  [Warning] Error al clasificar Timberland {sku} geométricamente: {e}. Fallback a CALZADO.")
        return "CALZADO"


def clasificar_imagen(file_path: Path, img_pil: Image.Image, output_path: Path = None, marca_forzada: str = None):
    """
    Clasifica la imagen y determina si se le debe remover el fondo.
    Retorna: (tipo_procesamiento, remover_fondo)
    Tipos: 'MAIN', 'SECONDARY', 'VESTUARIO_ANCLADO', 'FULL_BLEED'
    """
    stem_upper = file_path.stem.upper()
    
    brand = None
    if marca_forzada:
        brand = marca_forzada.upper()
    else:
        if stem_upper.startswith("AD"):
            brand = "ADIDAS"
        elif stem_upper.startswith("AS"):
            brand = "ASICS"
        elif stem_upper.startswith("NB"):
            brand = "NEW BALANCE"
        elif stem_upper.startswith("TB") or "TIMBERLAND" in stem_upper:
            brand = "TIMBERLAND"
        elif stem_upper.startswith("CO") or "_A_107X1" in stem_upper:
            brand = "CONVERSE"
        elif bool(re.match(r"^[AXY]\d+", stem_upper)):
            brand = "DIESEL"

    is_diesel = (brand == "DIESEL")
    es_ropa_diesel = bool(re.match(r"^(A|00)\d+", stem_upper))

    # 1. Semántica Explícita Full Bleed (Modelos, Detalles, Lifestyle, Mood) - Prioridad Absoluta
    if any(k in stem_upper for k in ["_MODEL", "_DETAIL", "_LIFESTYLE", "_MOOD"]):
        return "FULL_BLEED", is_diesel

    if brand == "DIESEL" and es_ropa_diesel:
        return "FULL_BLEED", True

    # 2. Caso Especial Timberland Vestuario
    if brand == "TIMBERLAND":
        subcat = obtener_subcategoria_timberland(file_path)
        if subcat == "VESTUARIO" or subcat == "ACCESORIO":
            has_real_alpha = tiene_transparencia_real(img_pil)
            w, h = img_pil.size
            img_rgb = img_pil.convert("RGBA") if has_real_alpha else img_pil.convert("RGB")
            
            bbox_left, bbox_top, bbox_right, bbox_bottom = w, h, 0, 0
            if has_real_alpha:
                alpha = img_rgb.split()[-1]
                bbox = alpha.getbbox()
                if bbox: bbox_left, bbox_top, bbox_right, bbox_bottom = bbox
                
                left_active = any(alpha.getpixel((x, y)) > 15 for x in range(min(BORDER_THRESHOLD_PX, w)) for y in range(h))
                right_active = any(alpha.getpixel((x, y)) > 15 for x in range(max(0, w - BORDER_THRESHOLD_PX), w) for y in range(h))
                top_active = any(alpha.getpixel((x, y)) > 15 for x in range(w) for y in range(min(BORDER_THRESHOLD_PX, h)))
                bottom_active = any(alpha.getpixel((x, y)) > 15 for x in range(w) for y in range(max(0, h - BORDER_THRESHOLD_PX), h))
            else:
                corners = [img_rgb.getpixel((0, 0)), img_rgb.getpixel((w - 1, 0)),
                           img_rgb.getpixel((0, h - 1)), img_rgb.getpixel((w - 1, h - 1))]
                bg_r = int(sum(c[0] for c in corners) / 4)
                bg_g = int(sum(c[1] for c in corners) / 4)
                bg_b = int(sum(c[2] for c in corners) / 4)
                bg_color = (bg_r, bg_g, bg_b)
                
                def es_color_producto(pixel):
                    return sum((pixel[i] - bg_color[i]) ** 2 for i in range(3)) ** 0.5 > 30

                left_active = any(es_color_producto(img_rgb.getpixel((x, y))) for x in range(min(BORDER_THRESHOLD_PX, w)) for y in range(h))
                right_active = any(es_color_producto(img_rgb.getpixel((x, y))) for x in range(max(0, w - BORDER_THRESHOLD_PX), w) for y in range(h))
                top_active = any(es_color_producto(img_rgb.getpixel((x, y))) for x in range(w) for y in range(min(BORDER_THRESHOLD_PX, h)))
                bottom_active = any(es_color_producto(img_rgb.getpixel((x, y))) for x in range(w) for y in range(max(0, h - BORDER_THRESHOLD_PX), h))

                for y in range(0, h, 10):
                    for x in range(0, w, 10):
                        if es_color_producto(img_rgb.getpixel((x, y))):
                            if x < bbox_left: bbox_left = x
                            if x > bbox_right: bbox_right = x
                            if y < bbox_top: bbox_top = y
                            if y > bbox_bottom: bbox_bottom = y

            obj_w = bbox_right - bbox_left
            obj_h = bbox_bottom - bbox_top
            
            area_ratio = (obj_w * obj_h) / (w * h) if w > 0 and h > 0 else 0
            
            # Regla de Zoom (Full Bleed): Toca múltiples bordes, no tiene bordes claros, o es muy denso (> 85% del área)
            if (top_active and bottom_active) or (left_active and right_active) or bbox_right <= bbox_left or area_ratio > 0.85:
                print(f"  [Detección] Toca múltiples bordes o llena la foto (Área: {area_ratio:.2f}). Clasificada como Zoom (Full Bleed).")
                return "FULL_BLEED", False
                
            if subcat == "VESTUARIO":
                if top_active or bottom_active:
                    print(f"  [Detección] Ropa toca un borde. Clasificada como Vestuario Anclado.")
                    return "VESTUARIO_ANCLADO", True
                return "SECONDARY", True

    # 3. Caso Especial Adidas (Forzar vistas)
    if brand == "ADIDAS" and output_path:
        out_stem = output_path.stem.upper()
        match_adidas = re.match(r"^AD.+-(\d{4})$", out_stem)
        if match_adidas:
            mapped_num = match_adidas.group(1)
            print(f"  [Detección] Lógica ADIDAS detectada en clasificador. Vista mapeada: {mapped_num}")
            if mapped_num == "0001":
                return "MAIN", True
            elif mapped_num in ["0002", "0003", "0004", "0005", "0006"]:
                return "SECONDARY", True
            elif mapped_num in ["0007", "0008"]:
                return "FULL_BLEED", True # Detalles (Remover fondo)
            else:
                return "FULL_BLEED", False # Lifestyle

    # 4. Detección de Imagen MAIN (Portadas)
    es_main = False
    if re.search(r"[-_]0*1[A-Z]*$", stem_upper) or "_A_MAIN" in stem_upper or "FRONT" in stem_upper or "ALT100" in stem_upper:
        es_main = True
        
    # ASICS MAIN
    if "SR_RT_GLB" in stem_upper or "RT_GLB" in stem_upper:
        es_main = True
        
    # New Balance MAIN
    if "-0-0001" in stem_upper or stem_upper.endswith("_2"):
        es_main = True
        
    # Converse MAIN
    if "_A_107X1" in stem_upper or stem_upper.endswith("_107X1") or "-1.JPG" in stem_upper or "-1.PNG" in stem_upper:
        es_main = True

    # Mapeo en el output path para mayor seguridad
    if output_path:
        out_stem = output_path.stem.upper()
        if out_stem.endswith("-0001"):
            es_main = True
            
    es_producto_explicito = "_MAIN" in stem_upper or es_main

    # 5. Geometría fallback para detectar modelos
    if not es_producto_explicito or is_diesel:
        has_real_alpha = tiene_transparencia_real(img_pil)
        width, height = img_pil.size
        bbox_left, bbox_top, bbox_right, bbox_bottom = width, height, 0, 0

        img_rgb = img_pil.convert("RGBA") if has_real_alpha else img_pil.convert("RGB")

        if has_real_alpha:
            alpha = img_rgb.split()[-1]
            left_active = any(alpha.getpixel((x, y)) > 15 for x in range(min(BORDER_THRESHOLD_PX, width)) for y in range(height))
            right_active = any(alpha.getpixel((x, y)) > 15 for x in range(max(0, width - BORDER_THRESHOLD_PX), width) for y in range(height))
            top_active = any(alpha.getpixel((x, y)) > 15 for x in range(width) for y in range(min(BORDER_THRESHOLD_PX, height)))
            bottom_active = any(alpha.getpixel((x, y)) > 15 for x in range(width) for y in range(max(0, height - BORDER_THRESHOLD_PX), height))
            bbox = img_rgb.getbbox()
            if bbox: bbox_left, bbox_top, bbox_right, bbox_bottom = bbox
        else:
            corners = [
                img_rgb.getpixel((0, 0)), img_rgb.getpixel((width - 1, 0)),
                img_rgb.getpixel((0, height - 1)), img_rgb.getpixel((width - 1, height - 1))
            ]
            bg_r = int(sum(c[0] for c in corners) / 4)
            bg_g = int(sum(c[1] for c in corners) / 4)
            bg_b = int(sum(c[2] for c in corners) / 4)
            bg_color = (bg_r, bg_g, bg_b)
            
            color_diffs = []
            for i in range(4):
                squared_sum = 0
                for j in range(3):
                    squared_sum += (corners[i][j] - bg_color[j]) ** 2
                color_diffs.append(squared_sum ** 0.5)
                
            if max(color_diffs) > 30:
                print(f"  [Detección] Fondo complejo detectado (Runway/Lifestyle). Protegiendo fondo.")
                return "FULL_BLEED", False

            def es_color_producto(pixel):
                return sum((pixel[i] - bg_color[i]) ** 2 for i in range(3)) ** 0.5 > 30

            left_active = any(es_color_producto(img_rgb.getpixel((x, y))) for x in range(min(BORDER_THRESHOLD_PX, width)) for y in range(height))
            right_active = any(es_color_producto(img_rgb.getpixel((x, y))) for x in range(max(0, width - BORDER_THRESHOLD_PX), width) for y in range(height))
            top_active = any(es_color_producto(img_rgb.getpixel((x, y))) for x in range(width) for y in range(min(BORDER_THRESHOLD_PX, height)))
            bottom_active = any(es_color_producto(img_rgb.getpixel((x, y))) for x in range(width) for y in range(max(0, height - BORDER_THRESHOLD_PX), height))

            for y in range(0, height, 5):
                for x in range(0, width, 5):
                    if es_color_producto(img_rgb.getpixel((x, y))):
                        if x < bbox_left: bbox_left = x
                        if x > bbox_right: bbox_right = x
                        if y < bbox_top: bbox_top = y
                        if y > bbox_bottom: bbox_bottom = y

        active_borders = sum([left_active, right_active, top_active, bottom_active])
        if active_borders >= 2:
            print(f"  [Detección] Geométrica (Multiborde): '{file_path.name}' toca {active_borders} bordes. Clasificada como Full Bleed.")
            return "FULL_BLEED", is_diesel
        if bottom_active:
            print(f"  [Detección] Geométrica (Base): '{file_path.name}' choca con el borde inferior. Clasificada como Full Bleed.")
            return "FULL_BLEED", is_diesel
        if bbox_right <= bbox_left or bbox_bottom <= bbox_top:
            print(f"  [Detección] Geométrica (Sin bordes definidos): '{file_path.name}' es una textura o zoom. Clasificada como Full Bleed.")
            return "FULL_BLEED", False
        if bbox_right > bbox_left and bbox_bottom > bbox_top:
            aspect_ratio = (bbox_bottom - bbox_top) / (bbox_right - bbox_left)
            if aspect_ratio > 1.8 and es_ropa_diesel:
                print(f"  [Detección] Geométrica (Aspecto {aspect_ratio:.2f}): '{file_path.name}' es alta/delgada. Clasificada como Full Bleed (Modelo Completo).")
                return "FULL_BLEED", is_diesel

    # 6. Portada o Secundario estándar
    if es_main:
        print(f"  [Detección] Producto Principal -> MAIN (Center).")
        return "MAIN", True
    else:
        print(f"  [Detección] Producto Secundario -> SECONDARY (Center).")
        return "SECONDARY", True


# ── REMOCIÓN DE FONDO (JPG -> PNG) ───────────────────────────────────────────
def remover_fondo_inteligente(img_pil: Image.Image, erodir: bool = False) -> Image.Image:
    """
    Remueve el fondo convirtiendo la imagen a RGBA transparente.
    Aplica relleno de huecos en la máscara alfa (fill holes) para evitar que
    rembg perfore prendas claras.
    Si erodir es True, aplica un filtro de erosión de 1px en el canal Alpha para eliminar halos.
    """
    if REMBG_AVAILABLE:
        try:
            img_rgba = remove(img_pil).convert("RGBA")
            alpha = img_rgba.split()[-1]
            
            # Rellenar huecos internos (fill holes) en la máscara alfa para evitar recortes en ropa clara
            import numpy as np
            from scipy import ndimage
            arr_alpha = np.array(alpha)
            binary_alpha = arr_alpha > 128
            filled_binary = ndimage.binary_fill_holes(binary_alpha)
            arr_alpha_filled = arr_alpha.copy()
            arr_alpha_filled[filled_binary & ~binary_alpha] = 255
            alpha = Image.fromarray(arr_alpha_filled)
            
            if erodir:
                alpha = alpha.filter(ImageFilter.MinFilter(3)) # MinFilter de vecindario 3x3 (erosion 1px)
                
            img_rgba = Image.merge("RGBA", img_rgba.split()[:3] + (alpha,))
            return img_rgba
        except Exception as e:
            print(f"  [Warning] Falló rembg: {e}. Usando fallback chroma-key.")
    
    # Fallback Chroma-key ultra-conservador para evitar comerse prendas de color claro (gris, beige)
    img_rgba = img_pil.convert("RGBA")
    width, height = img_rgba.size
    data = img_rgba.getdata()
    
    corners = [data[0], data[width - 1], data[(height - 1) * width], data[width * height - 1]]
    bg_color = tuple(int(sum(c[i] for c in corners) / 4) for i in range(3))
    
    new_data = []
    for item in data:
        # Calcular distancia euclidiana del color del pixel al color de fondo estimado
        dist = sum((item[i] - bg_color[i]) ** 2 for i in range(3)) ** 0.5
        if dist < 10:
            # Fondo puro -> 100% transparente
            new_data.append((255, 255, 255, 0))
        elif dist < 25:
            # Transición suave
            alpha_val = int((dist - 10) / (25 - 10) * 255)
            alpha_val = max(0, min(255, alpha_val))
            new_data.append((item[0], item[1], item[2], alpha_val))
        else:
            # Cuerpo del producto -> 100% opaco para preservar su color real (evita transparencias fantasma)
            new_data.append((item[0], item[1], item[2], 255))
            
    img_rgba.putdata(new_data)
    if erodir:
        alpha = img_rgba.split()[-1]
        eroded_alpha = alpha.filter(ImageFilter.MinFilter(3))
        img_rgba = Image.merge("RGBA", img_rgba.split()[:3] + (eroded_alpha,))
    return img_rgba


# ── TRATAMIENTOS DE IMAGEN ───────────────────────────────────────────────────
def aplicar_full_bleed(img_pil: Image.Image, target_w: int, target_h: int) -> Image.Image:
    mode = "RGBA" if img_pil.mode in ["RGBA", "LA"] or (img_pil.mode == "P" and "transparency" in img_pil.info) else "RGB"
    img_conv = img_pil.convert(mode)
    w, h = img_conv.size
    
    target_aspect = target_w / target_h
    img_aspect = w / h
    
    if img_aspect > target_aspect:
        new_h = target_h
        new_w = int(w * (target_h / h))
        img_resized = img_conv.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - target_w) // 2
        right = left + target_w
        return img_resized.crop((left, 0, right, target_h))
    else:
        new_w = target_w
        new_h = int(h * (target_w / w))
        img_resized = img_conv.resize((new_w, new_h), Image.LANCZOS)
        top = (new_h - target_h) // 2
        bottom = top + target_h
        return img_resized.crop((0, top, target_w, bottom))


def aplicar_anclaje_dinamico(img_rgba: Image.Image, bg_color: tuple, 
                             canvas_w: int, canvas_h: int, 
                             max_h: int = 1350) -> Image.Image:
    """
    Escala la imagen proporcionalmente respetando una altura máxima,
    y la ancla dinámicamente al borde inferior (si toca abajo) o superior (si toca arriba).
    """
    alpha = img_rgba.split()[-1]
    mask_solid = alpha.point(lambda p: 255 if p >= 254 else 0)
    bbox = mask_solid.getbbox()
    
    if not bbox:
        return Image.new("RGB", (canvas_w, canvas_h), bg_color)
        
    obj_left, obj_top, obj_right, obj_bottom = bbox
    obj_w = obj_right - obj_left
    obj_h = obj_bottom - obj_top
    
    # Escalar proporcionalmente
    scale = max_h / obj_h if obj_h > 0 else 1.0
    new_full_w = int(img_rgba.width * scale)
    new_full_h = int(img_rgba.height * scale)
    
    img_resized = img_rgba.resize((new_full_w, new_full_h), Image.LANCZOS)
    
    new_obj_w = int(obj_w * scale)
    new_obj_h = int(obj_h * scale)
    new_obj_left = int(obj_left * scale)
    new_obj_top = int(obj_top * scale)
    
    # Anclaje horizontal: Centrar la imagen completa (confiar en el encuadre del fotógrafo)
    paste_x = (canvas_w - new_full_w) // 2
    
    # Determinar anclaje vertical
    touch_bottom = obj_bottom > img_rgba.height - 20
    touch_top = obj_top < 20
    
    if touch_top and not touch_bottom:
        # Anclar al ras del techo (borde superior)
        target_y = 0
    else:
        # Anclar al ras del piso (borde inferior) o fallback
        target_y = canvas_h - new_obj_h
        
    paste_y = target_y - new_obj_top
    
    canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    canvas.paste(img_resized, (paste_x, paste_y), mask=img_resized)
    return canvas


def aplicar_centrado_absoluto(img_pil: Image.Image, bg_color: tuple, 
                              canvas_w: int, canvas_h: int, 
                              max_w: int, max_h: int,
                              original_img: Image.Image = None,
                              file_path: Path = None,
                              marca_forzada: str = None) -> Image.Image:
    """
    Recorta al ras, escala respetando proporciones máximas, 
    y centra absolutamente (horizontal y verticalmente) ignorando la sombra.
    """
    img_rgba = img_pil.convert("RGBA")
    
    alpha = img_rgba.split()[-1]
    mask_solid = alpha.point(lambda p: 255 if p >= 254 else 0)
    obj_bbox = mask_solid.getbbox()
        
    if not obj_bbox:
        return Image.new("RGB", (canvas_w, canvas_h), bg_color)
        
    obj_left, obj_top, obj_right, obj_bottom = obj_bbox
    
    mask_shoe = alpha.point(lambda p: 255 if p >= 240 else 0)
    shoe_bbox = mask_shoe.getbbox()
    if shoe_bbox:
        obj_left, obj_top, obj_right, obj_bottom = shoe_bbox

    obj_w = obj_right - obj_left
    obj_h = obj_bottom - obj_top
    
    calc_left, calc_top, calc_right, calc_bottom = obj_left, obj_top, obj_right, obj_bottom
    calc_w, calc_h = obj_w, obj_h
    
    aspect_ratio = calc_w / calc_h if calc_h > 0 else 1.0
    es_atras = False
    stem_upper = ""
    if file_path:
        stem_upper = file_path.stem.upper()
    
    # Determinar marca de forma determinista para las dimensiones
    brand = None
    if marca_forzada:
        brand = marca_forzada.upper()
    elif stem_upper:
        if stem_upper.startswith("AD"):
            brand = "ADIDAS"
        elif stem_upper.startswith("AS"):
            brand = "ASICS"
        elif stem_upper.startswith("NB"):
            brand = "NEW BALANCE"
        elif stem_upper.startswith("CO") or "_A_107X1" in stem_upper:
            brand = "CONVERSE"
        elif stem_upper.startswith("TB") or "TIMBERLAND" in stem_upper:
            brand = "TIMBERLAND"

    es_ropa_diesel = bool(re.match(r"^(A|00)\d+", stem_upper))

    # Forzar dimensiones específicas por marca / subcategoría
    if brand == "FJALLRAVEN" or brand == "FJÄLLRÄVEN":
        max_w = MAX_PRODUCT_W_FJALLRAVEN
        max_h = MAX_PRODUCT_H_FJALLRAVEN
    elif brand == "CROCS":
        max_w = MAX_PRODUCT_W_CROCS
        max_h = MAX_PRODUCT_H_CROCS
    elif brand == "HEY DUDE" or brand == "HEYDUDE":
        max_w = MAX_PRODUCT_W_HEYDUDE
        max_h = MAX_PRODUCT_H_HEYDUDE
    elif brand == "TIMBERLAND":
        subcat = obtener_subcategoria_timberland(file_path if file_path else Path("TB_dummy_1.jpg"))
        if subcat == "ACCESORIO":
            max_w = MAX_PRODUCT_W_TIMBERLAND_ACC
            max_h = MAX_PRODUCT_H_TIMBERLAND_ACC
        elif subcat == "VESTUARIO":
            if stem_upper.endswith("_1") or stem_upper.endswith("_2") or stem_upper.endswith("-0001") or stem_upper.endswith("-0002"):
                max_h = 1400  # Modelo cuerpo completo: margen de 50px por lado (1500 - 100 = 1400)
            # Para 0004, 0005 (producto solo), conserva los max_h y max_w por defecto (1100 y 950)
    elif brand == "DIESEL":
        if es_ropa_diesel:
            max_h = 1350  # Expande Diesel ropa a 1350px para consistencia

    if stem_upper:
        # Reglas comunes (keywords)
        if any(k in stem_upper for k in ["_BK", "BACK", "TALON", "ATRAS", "DETRAS", "TRASERA", "_TR"]):
            es_atras = True
        elif stem_upper.startswith("AD") and (stem_upper.endswith("-0004") or stem_upper.endswith("-0006")):
            es_atras = True
        elif stem_upper.startswith("AS") and (stem_upper.endswith("-0003") or stem_upper.endswith("-0004") or stem_upper.endswith("-0006") or stem_upper.endswith("-0007")):
            es_atras = True
        elif stem_upper.startswith("NB") and ("-0-0004" in stem_upper or "-0-0005" in stem_upper):
            es_atras = True
        elif not (stem_upper.startswith("AD") or stem_upper.startswith("AS") or stem_upper.startswith("NB")):
            if stem_upper.endswith("-0007") or stem_upper.endswith("-0003") or \
               stem_upper.endswith("-0004") or stem_upper.endswith("-0006") or \
               "-0-0004" in stem_upper or "-0-0005" in stem_upper:
                es_atras = True
            
    es_ancho_forzado = False
    es_0004_adidas = False
    es_reducido_nb = False
    es_reducido_asics = False
    
    if stem_upper:
        if brand == "ADIDAS":
            if stem_upper.endswith("-0003") or stem_upper.endswith("-0005"):
                es_ancho_forzado = True
            elif stem_upper.endswith("-0004") or stem_upper.endswith("-0006"):
                es_0004_adidas = True
        elif brand == "NEW BALANCE":
            if "-0-0004" in stem_upper or "-0-0005" in stem_upper:
                es_reducido_nb = True
        elif brand == "ASICS":
            if stem_upper.endswith("-0004") or stem_upper.endswith("-0006") or stem_upper.endswith("-0007"):
                es_reducido_asics = True

    if es_0004_adidas:
        max_w = MAX_PRODUCT_W_ADIDAS_0004
        max_h = MAX_PRODUCT_H_ADIDAS_0004
    elif es_reducido_nb:
        max_w = MAX_PRODUCT_W_NB_REDUCED
        max_h = MAX_PRODUCT_H_NB_REDUCED
    elif es_reducido_asics:
        max_w = MAX_PRODUCT_W_ASICS_REDUCED
        max_h = MAX_PRODUCT_H_ASICS_REDUCED

    if (aspect_ratio > 1.2 or es_ancho_forzado) and not es_atras:
        if max_w == MAX_PRODUCT_W:
            if es_ancho_forzado:
                max_w = MAX_PRODUCT_W_ADIDAS_SIDE
            else:
                max_w = MAX_PRODUCT_W_SIDE
            
    if es_ancho_forzado:
        scale = max_w / calc_w if calc_w > 0 else 1.0
    else:
        scale = min(max_w / calc_w, max_h / calc_h) if calc_w > 0 and calc_h > 0 else 1.0
    
    new_calc_w = int(calc_w * scale)
    new_calc_h = int(calc_h * scale)
    new_calc_left = int(calc_left * scale)
    new_calc_top = int(calc_top * scale)
    
    full_w, full_h = img_rgba.size
    new_full_w = int(full_w * scale)
    new_full_h = int(full_h * scale)
    
    img_rgba_resized = img_rgba.resize((new_full_w, new_full_h), Image.LANCZOS)
    
    if original_img:
        orig_resized = original_img.convert("RGB").resize((new_full_w, new_full_h), Image.LANCZOS)
        orig_resized = normalize_background_to_white(orig_resized)
    else:
        orig_resized = None
        
    # Coordenadas de centrado absoluto basadas en el OBJETO VIRTUAL
    target_obj_x = (canvas_w - new_calc_w) // 2
    target_obj_y = (canvas_h - new_calc_h) // 2
    
    paste_x = target_obj_x - new_calc_left
    paste_y = target_obj_y - new_calc_top
    
    canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    
    if orig_resized:
        temp_canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        temp_canvas.paste(orig_resized, (paste_x, paste_y))
        canvas = ImageChops.multiply(canvas, temp_canvas)
        
    canvas.paste(img_rgba_resized, (paste_x, paste_y), mask=img_rgba_resized)
    return canvas


# ── CONTROLADOR PRINCIPAL ────────────────────────────────────────────────────
def procesar_imagen(file_path: Path, output_path: Path, 
                    canvas_w: int, canvas_h: int, 
                    bg_hex: str, max_w: int, max_h: int, 
                    marca_forzada: str = None):
    """Procesa una sola imagen de acuerdo a sus características."""
    hex_clean = bg_hex.lstrip("#")
    bg_tuple = tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))

    img = Image.open(file_path)
    
    # Clasificación de tipo
    tipo, remover_bg = clasificar_imagen(file_path, img, output_path=output_path, marca_forzada=marca_forzada)
    
    # Determinar si aplicamos filtro de erosión de alpha (para vestuario y accesorios)
    brand = (marca_forzada or "").upper()
    if not brand:
        stem_upper = file_path.stem.upper()
        if stem_upper.startswith("TB") or "TIMBERLAND" in stem_upper:
            brand = "TIMBERLAND"
        elif stem_upper.startswith("AD"):
            brand = "ADIDAS"
        elif stem_upper.startswith("AS"):
            brand = "ASICS"
        elif stem_upper.startswith("NB"):
            brand = "NEW BALANCE"
            
    is_apparel_or_acc = False
    if brand == "TIMBERLAND":
        subcat = obtener_subcategoria_timberland(file_path)
        if subcat in ["VESTUARIO", "ACCESORIO"]:
            is_apparel_or_acc = True
    elif brand in ["DIESEL", "FJALLRAVEN", "FJÄLLRÄVEN", "CROCS", "HEY DUDE", "HEYDUDE"]:
        is_apparel_or_acc = True

    remover_bg_erodir = is_apparel_or_acc # Activo para ropa/accesorios para evitar halos blancos, inactivo para calzado

    if tipo == "FULL_BLEED":
        print(f"  [Proceso] Aplicando Full Bleed (Center Crop) a '{file_path.name}'...")
        resultado_cropped = aplicar_full_bleed(img, canvas_w, canvas_h)
        
        ext = file_path.suffix.lower()
        if remover_bg and (ext in [".jpg", ".jpeg"] or resultado_cropped.mode != "RGBA"):
            print(f"    [Remoción de fondo] Reemplazando fondo por {bg_hex} con IA (Erosión: {remover_bg_erodir})...")
            img_rgba = remover_fondo_inteligente(resultado_cropped, erodir=remover_bg_erodir)
            canvas = Image.new("RGB", (canvas_w, canvas_h), bg_tuple)
            canvas.paste(img_rgba, (0, 0), mask=img_rgba)
            resultado = canvas
        else:
            if resultado_cropped.mode == "RGBA":
                canvas = Image.new("RGB", (canvas_w, canvas_h), bg_tuple)
                canvas.paste(resultado_cropped, (0, 0), mask=resultado_cropped)
                resultado = canvas
            else:
                resultado = resultado_cropped.convert("RGB")
                
    elif tipo == "VESTUARIO_ANCLADO":
        print(f"  [Proceso] Aplicando Anclaje Dinámico a '{file_path.name}'...")
        ext = file_path.suffix.lower()
        has_real_alpha = tiene_transparencia_real(img)
        
        # Siempre remover fondo y aplicar erosión para vestuario anclado (Erosión True para evitar halos blancos)
        print(f"    [Remoción de fondo] Extrayendo máscara con IA (Erosión: True)...")
        img_rgba = remover_fondo_inteligente(img, erodir=True)
        
        # Calcular altura máxima dinámica
        h_max = 1350
        stem_upper = file_path.stem.upper()
        if stem_upper.endswith("_1") or stem_upper.endswith("_2") or stem_upper.endswith("-0001") or stem_upper.endswith("-0002"):
            h_max = 1400
            
        resultado = aplicar_anclaje_dinamico(img_rgba, bg_tuple, canvas_w, canvas_h, max_h=h_max)
        
    elif tipo == "MAIN":
        print(f"  [Proceso] Aplicando Centrado Absoluto a '{file_path.name}'...")
        ext = file_path.suffix.lower()
        has_real_alpha = tiene_transparencia_real(img)
        original_to_pass = None
        if (ext in [".jpg", ".jpeg"] or not has_real_alpha) and remover_bg:
            print(f"    [Remoción de fondo] Extrayendo máscara con IA (Erosión: {remover_bg_erodir})...")
            img_rgba = remover_fondo_inteligente(img, erodir=remover_bg_erodir)
            if not is_apparel_or_acc:
                original_to_pass = img
        else:
            img_rgba = img.convert("RGBA")

        resultado = aplicar_centrado_absoluto(
            img_rgba, bg_tuple, canvas_w, canvas_h, max_w, max_h, original_img=original_to_pass, file_path=file_path, marca_forzada=marca_forzada
        )
    elif tipo == "SECONDARY":
        print(f"  [Proceso] Aplicando Centrado Absoluto a '{file_path.name}'...")
        ext = file_path.suffix.lower()
        has_real_alpha = tiene_transparencia_real(img)
        original_to_pass = None
        if (ext in [".jpg", ".jpeg"] or not has_real_alpha) and remover_bg:
            print(f"    [Remoción de fondo] Extrayendo máscara con IA (Erosión: {remover_bg_erodir})...")
            img_rgba = remover_fondo_inteligente(img, erodir=remover_bg_erodir)
            if not is_apparel_or_acc:
                original_to_pass = img
        else:
            img_rgba = img.convert("RGBA")
            
        resultado = aplicar_centrado_absoluto(
            img_rgba, bg_tuple, canvas_w, canvas_h, max_w, max_h, original_img=original_to_pass, file_path=file_path, marca_forzada=marca_forzada
        )
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resultado.save(output_path, "JPEG", quality=95)
    print(f"  [Listo] Guardado en: '{output_path.name}'")


def get_adidas_mapped_filename(file_path: Path) -> str:
    """Intenta mapear el nombre original de Adidas al nuevo formato AD{CODE}-{MAPPED_VIEW}.jpg"""
    stem = file_path.stem
    if "_" in stem:
        parts = stem.split("_")
        if len(parts) >= 2:
            code = parts[0]
            view_num = parts[1]
            if view_num in ADIDAS_VIEW_MAPPING:
                mapped_view = ADIDAS_VIEW_MAPPING[view_num]
                return f"AD{code}-{mapped_view}"
    return stem

def get_asics_mapped_filename(file_path: Path) -> str:
    """Intenta mapear el nombre original de ASICS al nuevo formato AS{CODE}-{MAPPED_VIEW}.jpg"""
    stem = file_path.stem.upper()
    for key, mapped_view in ASICS_VIEW_MAPPING.items():
        if key in stem:
            new_stem = stem.replace(key, mapped_view)
            new_stem = "AS" + new_stem
            new_stem = new_stem.replace("_", ".")
            return new_stem
    return file_path.stem

def get_nb_mapped_filename(file_path: Path) -> str:
    """Intenta mapear el nombre original de New Balance al nuevo formato NB{CODE}-0-{VIEW}.jpg"""
    stem = file_path.stem.upper()
    for key, mapped_view in NB_VIEW_MAPPING.items():
        if stem.endswith(key):
            new_stem = stem[:-len(key)] + mapped_view
            new_stem = "NB" + new_stem
            return new_stem
    return file_path.stem

def get_converse_mapped_filename(file_path: Path) -> str:
    """Intenta mapear el nombre original de Converse al formato CO{CODE}-{MAPPED_VIEW}.jpg"""
    stem = file_path.stem.upper()
    for key, mapped_view in CONVERSE_VIEW_MAPPING.items():
        if key in stem:
            new_stem = stem.replace(key, mapped_view)
            if not new_stem.startswith("CO"):
                new_stem = "CO" + new_stem
            return new_stem
    return file_path.stem

def get_diesel_mapped_filename(file_path: Path) -> str:
    """Intenta mapear el nombre original de Diesel al formato {CODE}-000X.jpg"""
    stem = file_path.stem.upper()
    for key, mapped_view in DIESEL_VIEW_MAPPING.items():
        if key in stem:
            new_stem = stem.replace(key, mapped_view)
            new_stem = new_stem.replace("_", "")
            return new_stem
    return file_path.stem

def get_timberland_mapped_filename(file_path: Path) -> str:
    """Intenta mapear el nombre original de Timberland según su subcategoría detectada."""
    stem = file_path.stem
    subcat = obtener_subcategoria_timberland(file_path)
    
    parts = stem.split("_")
    if len(parts) >= 2:
        sku = parts[0]
        view_num = parts[1]
        
        if subcat == "CALZADO":
            if view_num in TIMBERLAND_CALZADO_VIEW_MAPPING:
                mapped_view = TIMBERLAND_CALZADO_VIEW_MAPPING[view_num]
                return f"{sku}-{mapped_view}"
            elif view_num == "8":
                # Omitir vista 8 en calzado (retornar el nombre original para que el motor lo salte)
                return stem
            else:
                try:
                    num = int(view_num)
                    if num >= 10:
                        # Vistas 10, 11, 12... pasan a ser 0009, 0010, 0011...
                        return f"{sku}-{(num - 1):04d}"
                except ValueError:
                    pass
        else:
            try:
                num = int(view_num)
                return f"{sku}-{num:04d}"
            except ValueError:
                pass
    return stem


def main():
    parser = argparse.ArgumentParser(description="Procesador Inteligente de Imágenes E-commerce.")
    parser.add_argument("--input", type=str, required=True, help="Ruta de la carpeta de origen o de un archivo.")
    parser.add_argument("--output", type=str, required=True, help="Ruta de la carpeta de salida.")
    parser.add_argument("--width", type=int, default=CANVAS_W, help="Ancho del lienzo final.")
    parser.add_argument("--height", type=int, default=CANVAS_H, help="Alto del lienzo final.")
    parser.add_argument("--bg", type=str, default="#F5F5F5", help="Color de fondo en formato HEX (ej. #F5F5F5).")
    parser.add_argument("--max-w", type=int, default=MAX_PRODUCT_W, help="Ancho máximo del producto principal.")
    parser.add_argument("--max-h", type=int, default=MAX_PRODUCT_H, help="Alto máximo del producto principal.")
    parser.add_argument("--brand", type=str, default=None, help="Forzar marca específica para aplicar sus reglas.")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    
    if not REMBG_AVAILABLE:
        print("\n[Aviso] La librería 'rembg' no está instalada.")
        print("  Los archivos JPG se procesarán con un algoritmo básico de contraste.")
        print("  Para habilitar la remoción de fondo profesional por IA, ejecuta:")
        print("  pip install rembg\n")
        
    def get_mapped_stem(path: Path) -> str:
        brand_forced = (args.brand or "").upper()
        
        if brand_forced == "NEW BALANCE":
            return get_nb_mapped_filename(path)
        elif brand_forced == "ASICS":
            return get_asics_mapped_filename(path)
        elif brand_forced == "ADIDAS":
            return get_adidas_mapped_filename(path)
        elif brand_forced == "CONVERSE":
            return get_converse_mapped_filename(path)
        elif brand_forced == "DIESEL":
            return get_diesel_mapped_filename(path)
        elif brand_forced == "TIMBERLAND":
            return get_timberland_mapped_filename(path)
            
        nb_stem = get_nb_mapped_filename(path)
        if nb_stem != path.stem:
            return nb_stem
        asics_stem = get_asics_mapped_filename(path)
        if asics_stem != path.stem:
            return asics_stem
        adidas_stem = get_adidas_mapped_filename(path)
        if adidas_stem != path.stem:
            return adidas_stem
        converse_stem = get_converse_mapped_filename(path)
        if converse_stem != path.stem:
            return converse_stem
        diesel_stem = get_diesel_mapped_filename(path)
        if diesel_stem != path.stem:
            return diesel_stem
        timberland_stem = get_timberland_mapped_filename(path)
        if timberland_stem != path.stem:
            return timberland_stem
        return path.stem
        
    if input_path.is_file():
        if input_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            new_stem = get_mapped_stem(input_path)
            if new_stem == input_path.stem and not args.brand:
                print(f"  [Omitido] '{input_path.name}' no tiene reglas de mapeo en el diccionario.")
                return
            out_file = output_dir / f"{new_stem}.jpg"
            procesar_imagen(
                input_path, out_file, args.width, args.height, args.bg,
                args.max_w, args.max_h, marca_forzada=args.brand
            )
    elif input_path.is_dir():
        valid_extensions = {".png", ".jpg", ".jpeg"}
        files = []
        for f in input_path.rglob("*"):
            if f.is_file() and f.suffix.lower() in valid_extensions:
                if "procesadas" in f.name.lower() or "exportxls_procesadas" in f.name.lower():
                    continue
                files.append(f)
        
        if not files:
            print(f"No se encontraron imágenes válidas en: {input_path}")
            return
            
        print(f"Iniciando procesamiento recursivo de {len(files)} imágenes...")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, file in enumerate(files):
            print(f"\n[{i+1}/{len(files)}] Procesando '{file.name}'...")
            new_stem = get_mapped_stem(file)
            
            # Omitir específicamente la vista 8 en Timberland
            if new_stem == file.stem and (args.brand or "").upper() == "TIMBERLAND" and file.stem.endswith("_8"):
                print(f"  [Omitido] Vista 8 ('_8') ignorada en calzado Timberland.")
                continue
                
            if new_stem == file.stem and not args.brand:
                print(f"  [Omitido] No hay reglas de mapeo para esta vista.")
                continue
            out_file = output_dir / f"{new_stem}.jpg"
            try:
                procesar_imagen(
                    file, out_file, args.width, args.height, args.bg,
                    args.max_w, args.max_h, marca_forzada=args.brand
                )
            except Exception as e:
                print(f"  [ERROR] No se pudo procesar '{file.name}': {e}")
                
        print("\n¡Proceso de estandarización completado con éxito!")
    else:
        print(f"Ruta de entrada no válida: {input_path}")


if __name__ == "__main__":
    main()
