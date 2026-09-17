import os
import sys
from pathlib import Path
from PIL import Image, ImageChops
import time

sys.path.append(r'G:\Mi unidad\Brand Manager\Gretel Gemini\image_resize')
from procesador_imagenes_ml import (
    normalize_background_to_white, 
    remover_fondo_inteligente,
    clasificar_imagen,
    get_adidas_mapped_filename,
    CANVAS_W, CANVAS_H, MAX_PRODUCT_W, MAX_PRODUCT_H
)

def center_of_mass(mask):
    """Calculates the center of mass of a binary/grayscale mask."""
    width, height = mask.size
    data = list(mask.getdata())
    total_mass = 0
    sum_x = 0
    sum_y = 0
    for y in range(height):
        for x in range(width):
            val = data[y*width + x]
            if val > 0:
                total_mass += val
                sum_x += x * val
                sum_y += y * val
    if total_mass == 0:
        return width / 2, height / 2
    return sum_x / total_mass, sum_y / total_mass

def aplicar_opcion_a_umbral(img_rgba, bg_color, canvas_w, canvas_h, max_w, max_h, original_img=None, file_path=None):
    """Opción A: Umbral de luminosidad/alpha para ignorar sombra."""
    alpha = img_rgba.split()[-1]
    
    # Solid bbox for cropping top/bottom/right
    mask_solid = alpha.point(lambda p: 255 if p >= 254 else 0)
    obj_bbox = mask_solid.getbbox()
    if not obj_bbox:
        return Image.new("RGB", (canvas_w, canvas_h), bg_color)
    
    obj_left, obj_top, obj_right, obj_bottom = obj_bbox
    
    # Shoe body bbox (ignores soft shadow using threshold 200)
    mask_shoe = alpha.point(lambda p: 255 if p >= 200 else 0)
    shoe_bbox = mask_shoe.getbbox()
    if shoe_bbox:
        # Use the shoe's left bound instead of the solid mask's left bound
        obj_left = shoe_bbox[0]
        
    calc_left, calc_top, calc_right, calc_bottom = obj_left, obj_top, obj_right, obj_bottom
    calc_w = calc_right - calc_left
    calc_h = calc_bottom - calc_top
    
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

def aplicar_opcion_b_centro_masa(img_rgba, bg_color, canvas_w, canvas_h, max_w, max_h, original_img=None, file_path=None):
    """Opción B: Centrado de Centro de Masa."""
    alpha = img_rgba.split()[-1]
    
    mask_solid = alpha.point(lambda p: 255 if p >= 254 else 0)
    obj_bbox = mask_solid.getbbox()
    if not obj_bbox:
        return Image.new("RGB", (canvas_w, canvas_h), bg_color)
    
    obj_left, obj_top, obj_right, obj_bottom = obj_bbox
    calc_w = obj_right - obj_left
    calc_h = obj_bottom - obj_top
    
    scale = min(max_w / calc_w, max_h / calc_h) if calc_w > 0 and calc_h > 0 else 1.0
    
    # Find center of mass of the shoe (threshold > 100 to ignore soft fringes but capture body)
    mask_com = alpha.point(lambda p: 255 if p >= 100 else 0)
    com_x, com_y = center_of_mass(mask_com)
    
    new_com_x = com_x * scale
    new_com_y = com_y * scale
    
    full_w, full_h = img_rgba.size
    new_full_w = int(full_w * scale)
    new_full_h = int(full_h * scale)
    
    img_rgba_resized = img_rgba.resize((new_full_w, new_full_h), Image.LANCZOS)
    
    if original_img:
        orig_resized = original_img.convert("RGB").resize((new_full_w, new_full_h), Image.LANCZOS)
        orig_resized = normalize_background_to_white(orig_resized)
    else:
        orig_resized = None
        
    # Align the center of mass with the center of the canvas
    paste_x = int((canvas_w / 2) - new_com_x)
    paste_y = int((canvas_h / 2) - new_com_y)
    
    canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    if orig_resized:
        temp_canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        temp_canvas.paste(orig_resized, (paste_x, paste_y))
        canvas = ImageChops.multiply(canvas, temp_canvas)
        
    canvas.paste(img_rgba_resized, (paste_x, paste_y), mask=img_rgba_resized)
    return canvas


def procesar_test(file_path: Path, output_dir_a: Path, output_dir_b: Path):
    bg_tuple = (245, 245, 245)
    img = Image.open(file_path)
    
    stem_upper = get_adidas_mapped_filename(file_path)
    if stem_upper == file_path.stem:
        return
        
    print(f"[{stem_upper}] Extrayendo fondo...")
    img_rgba = remover_fondo_inteligente(img)
    
    # Determinar max_w max_h basado en reglas
    max_w = MAX_PRODUCT_W
    max_h = MAX_PRODUCT_H
    
    if stem_upper.endswith("-0003") or stem_upper.endswith("-0005"):
        max_w = 820
    elif stem_upper.endswith("-0004") or stem_upper.endswith("-0006"):
        max_w = 900
        max_h = 1050
        
    # Solo probar en MAIN y SECONDARY (no full bleed para no demorar)
    if int(stem_upper.split("-")[-1]) > 6:
        return
        
    print(f"[{stem_upper}] Aplicando Opción A (Umbral)...")
    res_a = aplicar_opcion_a_umbral(img_rgba, bg_tuple, CANVAS_W, CANVAS_H, max_w, max_h, original_img=img, file_path=file_path)
    res_a.save(output_dir_a / f"{stem_upper}.jpg", "JPEG", quality=95)
    
    print(f"[{stem_upper}] Aplicando Opción B (Centro de Masa)...")
    res_b = aplicar_opcion_b_centro_masa(img_rgba, bg_tuple, CANVAS_W, CANVAS_H, max_w, max_h, original_img=img, file_path=file_path)
    res_b.save(output_dir_b / f"{stem_upper}.jpg", "JPEG", quality=95)


if __name__ == "__main__":
    input_dir = Path(r"C:\Users\hchumpitaz\Downloads\imagenes_prueba\adidas")
    out_dir_a = Path(r"C:\Users\hchumpitaz\Downloads\prueba_imagenes_0709\TEST_OPCION_A_UMBRAL")
    out_dir_b = Path(r"C:\Users\hchumpitaz\Downloads\prueba_imagenes_0709\TEST_OPCION_B_CENTROMASA")
    
    out_dir_a.mkdir(parents=True, exist_ok=True)
    out_dir_b.mkdir(parents=True, exist_ok=True)
    
    for f in input_dir.glob("*.jpg"):
        procesar_test(f, out_dir_a, out_dir_b)
        
    print("Pruebas A/B finalizadas con éxito.")
