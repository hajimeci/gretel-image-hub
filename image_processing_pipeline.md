# image_processing_pipeline.md — E-commerce Image Standardization Pipeline
> Gretel International SAC · E-commerce · Operaciones

---

## Propósito y Visión

Este flujo de trabajo define el estándar operativo para la preparación, estandarización y procesamiento de imágenes de producto destinadas a los canales de e-commerce de Gretel.

Actualmente opera como un script unificado de Python (`tools/procesador_imagenes_ml.py`), con el objetivo a mediano plazo de migrar a una aplicación interactiva con interfaz de usuario (UI), reduciendo la complejidad técnica para el equipo comercial y de marketing.

---

## Reglas de Formato por Marca (ASICS & Otras)

### 1. Formato de Descarga Recomendado: **JPG**
- **Regla:** Para todas las marcas, incluyendo ASICS (que suele proveer imágenes en PNG con fondo blanco), se debe preferir la descarga de archivos en formato **JPG**.
- **Justificación Técnica:**
  - El script utiliza una inteligencia artificial local (`rembg`) que no consume tokens de APIs externas, pero sí consume CPU/GPU locales. El esfuerzo de procesamiento de la IA es idéntico para un PNG con fondo blanco o un JPG con fondo blanco.
  - Los PNG con fondo blanco sólido no contienen transparencia real y pesan entre 3x y 4x más que un JPG equivalente. Descargar en JPG optimiza dramáticamente el espacio en disco, la velocidad de descarga y mantiene idéntico el rendimiento del recorte.
  - El script cuenta con la función `tiene_transparencia_real()` que identifica automáticamente si un archivo PNG tiene transparencia real (canal Alpha). Si detecta un falso PNG (fondo blanco sólido), lo trata como JPG y le remueve el fondo por IA para conservar sombras.

---

## Especificaciones Técnicas del Lienzo

| Parámetro | Valor por Defecto | Notas |
|---|---|---|
| **Dimensiones del Lienzo** | 1200 x 1500 px | Proporción de aspecto vertical optimizada para e-commerce (4:5). |
| **Color de Fondo** | `#F5F5F5` | Gris claro neutro institucional. |
| **Margen Inferior (Offset)**| -- | (Obsoleto, todas las fotos se procesan mediante Centrado Absoluto). |
| **Ancho Máximo del Producto (Vertical)** | 820 px | Para fotos verticales/cuadradas (vistas top, suela, atrás, adelante). |
| **Ancho Máximo del Producto (Costado)** | 1000 px | Para fotos de perfil/costado (aspect_ratio > 1.2) para reducir márgenes y agrandar el calzado. |
| **Alto Máximo del Producto** | 1100 px | Garantiza márgenes superior e inferior proporcionales. |

---

## Flujo de Clasificación y Tratamiento

El script clasifica cada imagen en uno de tres tipos mediante detección semántica (nombre del archivo) y geométrica:

### 1. MAIN (Portada)
- **Detección:** Archivos que terminan en `-1.jpg`, `_MAIN`, `FRONT`, `ALT100`, `_A_107X1` (Converse), o `SR_RT_GLB`/`RT_GLB` (ASICS).
- **Procesamiento:**
  - Se remueve el fondo mediante IA (`rembg`) para aislar el calzado u objeto conservando las sombras de estudio mediante multiplicación.
  - Procesada mediante **Centrado Absoluto** horizontal y vertical. Si la vista es de perfil (costado), se escala al ancho máximo de **1000 px** para el carrusel de productos.

### 2. SECONDARY (Center) — Fotos Secundarias de Producto
- **Detección:** Vistas angulares, traseras o superiores que no clasifican como MAIN ni tocan los bordes de la imagen original.
- **Procesamiento:**
  - Remoción de fondo y preservación de sombras naturales idéntico a MAIN.
  - Centrado absoluto horizontal y vertical dentro del lienzo de 1200x1500 px.

### 3. FULL_BLEED (Center Crop) — Textil, Modelos y Lifestyle
- **Detección:** Nombres que contienen `_MODEL`, `_DETAIL`, `_LIFESTYLE`, `_MOOD`, o ropa Diesel (comienzan con `A` o `00`). También mediante "Regla de los Bordes" si el producto toca 2 o más bordes de la imagen original.
- **Procesamiento:**
  - Se escala y recorta por el centro para cubrir el 100% del lienzo, preservando el fondo complejo original (pasarela, exteriores).
  - En caso de ropa Diesel, se remueve el fondo para colocar la prenda flotando sobre el gris `#F5F5F5` corporativo.

---

## Arquitectura Objetivo: La Aplicación de E-commerce (UI)

Para eliminar la dependencia de comandos en terminal, el procesador se convertirá en una aplicación web interactiva (sugerido **Streamlit**).

### Especificaciones de la Interfaz (UI)

1. **Carga de Archivos / Carpetas:** Arrastrar y soltar (Drag and Drop) imágenes o carpetas completas.
2. **Selector Obligatorio de Marca:** Un desplegable donde el usuario selecciona la marca antes de procesar:
   - `Diesel`
   - `Fjällräven`
   - `ASICS`
   - `Converse`
   - `Hey Dude`
   - `Crocs`
3. **Anulación de Inferencia Automática:** Al seleccionar la marca manualmente en la UI, el backend anulará la heurística de nombres de archivo y aplicará de forma determinista la lógica de la marca seleccionada:
   - **Diesel:** Forzará "Full Bleed" y remoción de fondo para calzados y prendas (códigos que inician con A o 00).
   - **ASICS / Converse:** Forzará "Centrado Absoluto" utilizando multiplicación de sombras de alta fidelidad.
   - **Fjällräven:** Aplicará centrado absoluto con márgenes generosos de protección para evitar recortes en mochilas y accesorios de volumen.
4. **Previsualización en Tiempo Real:** Mostrar una comparativa de "Antes" y "Después" de una imagen de muestra antes de procesar el lote completo.
5. **Descarga Consolidada:** Botón para exportar todas las imágenes procesadas en un archivo comprimido `.zip` o descargarlas en el directorio local de descargas del usuario.

---

## Lógica de Renombrado de Archivos (`tools/image_renamer_gui.py`)

Esta sección documenta el comportamiento de la aplicación de escritorio (`image_renamer_gui.py`) utilizada para estandarizar los nombres de los archivos antes de subirlos. **Cualquier agente que necesite replicar o actualizar el renombrado de imágenes debe seguir estrictamente estas reglas.**

### 1. ASICS
Utiliza búsqueda de coincidencias (substrings) y reemplaza toda la terminación.
- **Formato Final:** `AS[CodigoOriginal].[Color]-000X.jpg` (Cambia los `_` restantes por `.`)
- **Reglas (Zapatillas SR/SB):** `_SR_RT_GLB` (-0001), `_SR_LT_GLB` (-0002), `_SB_FR_GLB` (-0003), `_SB_TP_GLB` (-0004), `_SB_FL_GLB` (-0005), `_SB_BT_GLB` (-0006), `_SB_BK_GLB` (-0007).
- **Reglas (Textil GM/NM/GF):** `_GM_FT_GLB` / `_GF_FT_GLB` (-0001), `_NM_FT_GLB` (-0002), `_GM_BK_GLB` / `_GF_BK_GLB` (-0003), `_GM_SD_GLB` / `_GF_SD_GLB` (-0004), y secuencias `_Z1_GLB` a `_Z7_GLB` (-0005 a -0011).
- **Reglas (Accesorios AC):** `_AC_FT_GLB` (-0001), `_AC_BK_GLB` (-0002), `_AC_SD_GLB` (-0003), secuencias `_Z1_GLB` a `_Z4_GLB` (-0004 a -0007).

### 2. DIESEL
Búsqueda simple de dígito final y eliminación de guiones bajos.
- **Formato Final:** `[CodigoOriginal]-000X.jpg` (Elimina los `_` del nombre original).
- **Reglas:** `-1` (-0001), `-2` (-0002), `-3` (-0003)... hasta `-9` (-0009).

### 3. ADIDAS
Divide el nombre original por el guion bajo (`_`). La Parte 0 es el código de producto y la Parte 1 es el identificador de la vista. *(Nota: Actualmente el código asume que el identificador no tiene extensión al hacer la separación, comportamiento a corregir en futuras versiones).*
- **Formato Final:** `AD[CodigoProducto]-000X.jpg`
- **Reglas:** `1` (-0001), `5` (-0002), `6` (-0003), `3` (-0004), `7` (-0005), `4` (-0006), `8` a `19` (-0007 a -0018).

### 4. NEW BALANCE
Búsqueda de sufijos cortos y forzado de mayúsculas.
- **Formato Final:** `NB[CODIGOORIGINAL]-0-000X.ext` (Todo el nombre a mayúsculas, conservando la extensión original en minúsculas).
- **Reglas:** `_2` (-0-0001), `_3` (-0-0002), `_5` (-0-0003), `_4` (-0-0004), `_7` (-0-0005), `_6` (-0-0006).

---

## Lógica Específica por Marca: ADIDAS

### Reglas de Dimensionamiento y Márgenes
Adidas cuenta con reglas de dimensionamiento (ancho/alto máximo) más estrictas que el resto de marcas para estandarizar sus márgenes visuales:
- **Constante Global / Marcas Genéricas:** El ancho máximo base del producto es de **950px**.
- **Adidas (Vistas 0003 y 0005):** Ancho máximo restringido a **820px**. (Aumenta el espacio en blanco horizontal, excluyendo sombras gracias al filtro de opacidad severo).
- **Adidas (Vistas 0004 y 0006):** Ancho máximo restringido a **900px** y alto a **1050px**.

El script lee las transparencias de las fotos con IA. Para evitar que la sombra semi-transparente expanda el tamaño de la caja delimitadora, se aplica un filtro severo de canal alfa (ignora píxeles `< 254` de opacidad al calcular el `bounding box`).

El script aplica un mapeo numérico específico a las imágenes de Adidas basado en el patrón de nombre `CODIGO_NUMERO.jpg`. El mapeo estandariza las vistas y determina el tratamiento:

### Mapeo de Vistas
| Original | Final Mapeado | Tratamiento | Acción |
|---|---|---|---|
| `_1` | `0001` | **MAIN** | Se remueve fondo. Se procesa mediante Centrado Absoluto. |
| `_5`, `_6`, `_3`, `_7`, `_4` | `0002` a `0006` | **SECONDARY** | Vistas de producto. Se remueve el fondo y se aplica centrado absoluto. |
| `_8`, `_9` | `0007` a `0008` | **FULL_BLEED (Detalles)** | Se remueve el fondo con IA y se recorta al 100% (flota sobre gris). |
| `_10` al `_19` | `0009` a `0018` | **FULL_BLEED (Lifestyle)** | Recorte al 100%. **NO se remueve el fondo** (se conserva la pasarela/exterior original). |

**Nota sobre renombrado:** El script intercepta el archivo al exportar, leyendo el número original (ej. `ADIG5119_5.jpg`) y lo guarda directamente en la carpeta de salida con el nuevo nombre estandarizado (ej. `ADIG5119-0002.jpg`).

---

## Lógica Específica por Marca: NEW BALANCE

### Reglas de Dimensionamiento y Márgenes
New Balance utiliza reglas de dimensionamiento reducidas para igualar las proporciones visuales de Adidas en ciertas vistas, compensando la diferencia de volumen natural del calzado:
- **New Balance (Vistas 0004 y 0005):** Ancho máximo restringido a **900px** y alto a **1050px** (Mismas proporciones que la vista 0004 de Adidas).

El resto de vistas de New Balance (MAIN, perfil) utiliza la constante global estándar de 950px.

---

## Lógica Específica por Marca: ASICS

### Reglas de Dimensionamiento y Márgenes
ASICS utiliza reglas de centrado absoluto para todas sus vistas (Opción C) para alinearse con la grilla uniforme de la tienda multimarca Inbox. Además, aplica reglas de dimensionamiento reducidas para controlar el peso visual de sus vistas angulares, de suela o traseras:
- **ASICS (Vistas 0004, 0006 y 0007):** Ancho máximo restringido a **900px** y alto a **1050px** (Mismas proporciones reducidas de Adidas y New Balance).
  * 0004: Vista de planta/suela (`_SB_TP_GLB`).
  * 0006: Vista de talón (`_SB_BT_GLB`).
  * 0007: Vista de par completo/atrás (`_SB_BK_GLB`).

El resto de vistas de ASICS (MAIN, perfil lateral 0001 y 0002) utiliza la constante global estándar de 950px.


