# Manual Técnico y Operativo: Gretel Image E-commerce Hub
> **Preparado para:** Presentación de Producto - Gretel International SAC

---

## 1. Visión General del Producto

**Gretel Image Hub** es un motor inteligente de procesamiento de imágenes desarrollado a medida para estandarizar catálogos multimarca (ASICS, New Balance, Timberland). 

El problema central del e-commerce multimarca es la inconsistencia visual: cada proveedor entrega fotografías con diferentes fondos, distintas resoluciones y diversas proporciones. Si se publican directamente, la parrilla de la tienda (ej. Inbox) luce desordenada, afectando la percepción de calidad y la conversión del usuario.

**Solución:** Este aplicativo analiza la imagen mediante Inteligencia Artificial, identifica si es calzado, ropa o accesorios, recorta el objeto conservando sus sombras naturales, y lo reescala bajo reglas geométricas milimétricas. El resultado es un catálogo de aspecto premium, unificado y automatizado con un solo clic.

---

## 2. El Caso de Negocio (ROI y Eficiencia)

El verdadero valor de la herramienta reside en la eliminación de cuellos de botella operativos y sobrecostos por tercerización.

**Escenario de una Temporada Estándar (800 productos x 10 vistas = 8,000 fotografías):**
*   **Ahorro Financiero Directo:** Evita el costo de S/ 1.50 por foto procesada en agencia. Representa un **ahorro de S/ 12,000** por colección.
*   **Impacto Operativo (Velocidad):** El trabajo manual de 12 minutos por producto (160 horas hombre / 20 días laborables) se reduce a **menos de 5 horas** de procesamiento automatizado en segundo plano por la IA local.
*   **Time-to-Market:** El producto se puede lanzar a la venta el mismo día que se define el surtido, maximizando los días de venta a *Full Price*.

---

## 3. Capacidades Clave del Motor de IA

El núcleo del programa no realiza simples redimensiones; aplica un flujo de visión computacional avanzado. Uno de sus mayores valores agregados es su motor de remoción de fondo (**Rembg**):

*   **Sin costo por Tokens:** A diferencia de servicios comerciales de la nube, nuestra implementación es local (Open Source). Se pueden procesar lotes infinitos de imágenes y el costo operativo siempre será cero.
*   **100% Offline (Sin Internet):** No envía las fotos a la nube. Utiliza un modelo neuronal pre-entrenado (U2-Net) que se ejecuta físicamente dentro del procesador de la computadora, garantizando velocidad y la total privacidad del catálogo.
*   **Detección de Saliencia:** No usa "varita mágica" por color. La red neuronal entiende qué es el "sujeto principal" y qué es el fondo (sea un estudio fotográfico o exteriores), dibujando un mapa de recorte perfecto.

Además del recorte por IA, el flujo incluye:
1. **Preservación de Sombras (Multiplicación de Capas):** Separa la sombra original del calzado y la multiplica sobre el nuevo fondo gris corporativo (`#F5F5F5`). Esto mantiene el volumen y realismo de estudio fotográfico.
2. **Relleno de Huecos Inteligente (Fill Holes):** Cuando se procesa ropa de colores muy claros, las IAs suelen confundir la prenda con el fondo. El programa detecta la silueta cerrada de la prenda y reconstruye algorítmicamente cualquier hueco interno antes de pegarla.
3. **Auto-Trim y Bounding Box:** Escanea la imagen a nivel de píxel para encontrar los límites exactos del producto y recortar los espacios en blanco sobrantes antes de centrarlo.

---

## 4. Inteligencia de Categorización (Semántica y Geométrica)

El programa no trata todas las fotos igual. Clasifica dinámicamente la imagen en una de cuatro categorías:

*   **MAIN (Portada) / SECONDARY:** Productos flotantes. Se les remueve el fondo, se extrae la sombra y se ubican en **Centrado Absoluto** en un lienzo de 1200x1500 px.
*   **VESTUARIO ANCLADO:** Si la IA detecta que una prenda o modelo toca los bordes de la foto original (ej. un polo cortado por la cintura o un maniquí), aplica **Anclaje Dinámico**. Centra la prenda horizontalmente, pero alinea el corte al ras del piso (borde inferior) o del techo (borde superior) para que no parezca estar "flotando amputada" en el aire.
*   **FULL BLEED (Zoom / Lifestyle):** Si la foto toca varios bordes a la vez, es muy alargada o cubre más del 85% del área, la clasifica como foto de detalle o *lifestyle*. En lugar de achicarla, hace un recorte central (Center Crop) cubriendo el 100% del marco final.
*   **Detección Contextual Timberland:** Capacidad exclusiva que inspecciona el formato físico de la foto y la ruta del archivo para discernir con 100% de precisión si el SKU pertenece a **Calzado**, **Vestuario** o **Accesorios** (mochilas), aplicando una lógica distinta a cada uno.

---

## 5. Reglas Estrictas por Marca (Dimensionamiento Específico)

Cada marca tiene siluetas y volúmenes distintos. El programa estandariza sus "pesos visuales" en la pantalla basándose en estas reglas geométricas de ancho/alto máximo (Max Width / Max Height):

### Constante Global
*   **Lienzo Final:** 1200 x 1500 píxeles.
*   **Color de Fondo:** `#F5F5F5` (Gris neutro de Inbox).

### 👟 ASICS
*   Todas sus fotos adoptan el "Centrado Absoluto" de Inbox.
*   **Vistas Estándar (MAIN, Perfiles, etc.):** Ancho máximo **950 px** y Alto máximo **1100 px**.
*   **Vistas Reducidas (Planta, Talón y Par Completo - 0004, 0006, 0007):** Se restringen y achican a **900 px** de ancho y **1050 px** de alto para evitar que dominen visualmente a las zapatillas de perfil, equilibrando el catálogo.

### 👟 NEW BALANCE
*   Sigue un patrón estricto de control de volumen para igualar proporciones en la tienda multimarca.
*   **Vistas Estándar (MAIN, Perfiles):** Ancho máximo **950 px** y Alto máximo **1100 px**.
*   **Vistas Reducidas (0004, 0005):** Ancho máximo restringido a **900 px** y alto a **1050 px**. Estas vistas (como planos superiores o pares enteros) tienden a verse gigantes porque son bloques rectangulares; la restricción neutraliza su volumen masivo en la grilla.

### 🥾 TIMBERLAND (Lógica Triple)
*   **Calzado:** Utiliza la constante estándar de Inbox (**950 px de ancho / 1100 px de alto**) pero elimina automáticamente la "Vista 8" (por requerimiento de marca) y sigue el centrado multimarca.
*   **Vestuario:** Si detecta fotos de modelo de cuerpo completo (Vistas 1 y 2), expande el límite de altura a **1400 px**, dándole protagonismo al look completo en el lienzo de 1500 px. Activa obligatoriamente el "Relleno de Huecos" (Fill Holes) y el filtro anti-halos blancos para cuidar el color de la ropa.
*   **Accesorios:** Reconoce las mochilas por su ruta de carpeta y les asigna reglas personalizadas más anchas (**820 px de ancho / 950 px de alto**) para que los bolsos y mochilas no se vean desproporcionados o muy pegados a los bordes frente al calzado.

---

## 6. Renombrado Automático (Mapeo de Vistas)

Para evitar que el equipo comercial tenga que renombrar miles de fotos a mano para el cargador web de VTEX/Shopify, el Hub traduce los códigos de fábrica al estándar unificado `SKU-000X.jpg`.

*   **ASICS:** Traduce secuencias complejas como `_SR_RT_GLB` a `-0001` (Lateral Derecho), `_SB_BK_GLB` a `-0007` (Par Completo), y normaliza el texto.
*   **New Balance:** Convierte nombres en minúsculas y secuencias como `_2`, `_3` en `SKU-0-0001`, `SKU-0-0002` con extensión `.jpg`.
*   **Timberland:** Mapea el desordenado calzado original (`_1`->`0001`, `_6`->`0002`, `_4`->`0003`) omitiendo la vista `_8`, y estructura automáticamente las vistas para ropa y accesorios mediante reglas lógicas.

## Conclusión

El **Gretel Image Hub** es más que un simple recortador de fotos; es el guardián de la estética de marca. Convierte lotes caóticos de proveedores internacionales en un escaparate visualmente armonioso operado por inteligencia artificial local de costo cero, liberando cientos de horas operativas y asegurando que la calidad percibida del e-commerce sea siempre del más alto nivel.