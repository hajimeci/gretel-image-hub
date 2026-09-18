# Technical & Operational Manual: Gretel Image E-commerce Hub
> **Prepared for:** Product Presentation - Gretel International SAC
> 
> *Read in English 🇬🇧 | [Leer en Español 🇪🇸](README_es.md)*

---

## 1. Product Overview

**Gretel Image Hub** is a smart image processing engine custom-built to standardize multi-brand catalogs (ASICS, New Balance, Timberland).

The core problem in multi-brand e-commerce is visual inconsistency: every supplier provides photographs with different backgrounds, resolutions, and proportions. If published directly, the store's grid (e.g., Inbox) looks cluttered, negatively affecting the perceived quality and user conversion rates.

**Solution:** This application analyzes images using Artificial Intelligence, identifies whether the product is footwear, apparel, or accessories, crops the object while preserving its natural shadows, and rescales it based on precise geometric rules. The result is a premium, unified, and automated catalog with just one click.

---

## 2. Business Case (ROI & Efficiency)

The true value of this tool lies in eliminating operational bottlenecks and outsourcing costs.

**Standard Season Scenario (800 products x 10 views = 8,000 photographs):**
*   **Direct Financial Savings:** Completely eliminates the outsourcing costs associated with external photo processing agencies per collection.
*   **Operational Impact (Speed):** The manual work of 12 minutes per product (160 man-hours / 20 business days) is reduced to **under 5 hours** of automated background processing by the local AI.
*   **Time-to-Market:** Products can be launched for sale on the same day the assortment is defined, maximizing *Full Price* selling days.

---

## 3. Key AI Engine Capabilities

The core of the program does not simply resize images; it applies an advanced computer vision pipeline. One of its greatest added values is its background removal engine (**Rembg**):

*   **Zero Token Cost:** Unlike commercial cloud services, our implementation is local (Open Source). Infinite batches of images can be processed, and the operational cost will always be zero.
*   **100% Offline (No Internet Required):** It does not send photos to the cloud. It uses a pre-trained neural model (U2-Net) that runs physically within the computer's processor, ensuring speed and total privacy for upcoming catalogs.
*   **Saliency Detection:** It doesn't use a color-based "magic wand". The neural network understands what the "main subject" is and what the background is (whether a photo studio or outdoors), drawing a perfect cutout map.

Beyond AI cropping, the pipeline includes:
1. **Shadow Preservation (Layer Multiplication):** Separates the original shoe shadow and multiplies it over the new corporate gray background (`#F5F5F5`). This maintains the volume and realism of a photographic studio.
2. **Smart Hole Filling (Fill Holes):** When processing very light-colored clothing, AIs often confuse the garment with the background. The program detects the closed silhouette of the garment and algorithmically reconstructs any internal holes before pasting it.
3. **Auto-Trim and Bounding Box:** Scans the image at the pixel level to find the exact boundaries of the product and crops out excess white space before centering it.

---

## 4. Smart Categorization (Semantic & Geometric)

The program doesn't treat all photos equally. It dynamically classifies the image into one of four categories:

*   **MAIN (Cover) / SECONDARY:** Floating products. The background is removed, the shadow is extracted, and they are placed with **Absolute Centering** on a 1200x1500 px canvas.
*   **ANCHORED APPAREL:** If the AI detects that a garment or model touches the edges of the original photo (e.g., a shirt cut off at the waist or a mannequin), it applies **Dynamic Anchoring**. It centers the garment horizontally but aligns the cut flush with the floor (bottom edge) or the ceiling (top edge) so it doesn't look like it's "floating amputated" in mid-air.
*   **FULL BLEED (Zoom / Lifestyle):** If the photo touches multiple edges at once, is very elongated, or covers more than 85% of the area, it classifies it as a detail or *lifestyle* photo. Instead of shrinking it, it makes a central crop (Center Crop) covering 100% of the final frame.
*   **Timberland Contextual Detection:** An exclusive feature that inspects the physical format of the photo and the file path to discern with 100% accuracy whether the SKU belongs to **Footwear**, **Apparel**, or **Accessories** (backpacks), applying different logic to each.

---

## 5. Strict Brand Rules (Specific Sizing)

Every brand has different silhouettes and volumes. The program standardizes their "visual weights" on the screen based on these geometric rules for Max Width / Max Height:

### Global Constant
*   **Final Canvas:** 1200 x 1500 pixels.
*   **Background Color:** `#F5F5F5` (Inbox neutral gray).

### 👟 ASICS
*   All photos adopt Inbox's "Absolute Centering".
*   **Standard Views (MAIN, Profiles, etc.):** Max width **950 px** and Max height **1100 px**.
*   **Reduced Views (Sole, Heel, and Full Pair - 0004, 0006, 0007):** These are restricted and shrunk to **900 px** wide and **1050 px** high to prevent them from visually dominating the profile sneakers, balancing the catalog.

### 👟 NEW BALANCE
*   Follows a strict volume control pattern to match proportions in the multi-brand store.
*   **Standard Views (MAIN, Profiles):** Max width **950 px** and Max height **1100 px**.
*   **Reduced Views (0004, 0005):** Max width restricted to **900 px** and height to **1050 px**. These views (like top shots or whole pairs) tend to look giant because they are rectangular blocks; the restriction neutralizes their massive volume on the grid.

### 🥾 TIMBERLAND (Triple Logic)
*   **Footwear:** Uses the standard Inbox constant (**950 px wide / 1100 px high**) but automatically deletes "View 8" (per brand requirements) and follows multi-brand centering.
*   **Apparel:** If it detects full-body model photos (Views 1 and 2), it expands the height limit to **1400 px**, giving prominence to the full look on the 1500 px canvas. It mandatorily activates "Fill Holes" and the anti-white-halo filter to protect the clothing's color.
*   **Accessories:** Recognizes backpacks by their folder path and assigns them wider custom rules (**820 px wide / 950 px high**) so that bags and backpacks don't look disproportionate or too close to the edges compared to footwear.

---

## 6. Automated Renaming (View Mapping)

To prevent the commercial team from having to rename thousands of photos by hand for the VTEX/Shopify web loader, the Hub translates factory codes to the unified standard `SKU-000X.jpg`.

*   **ASICS:** Translates complex sequences like `_SR_RT_GLB` to `-0001` (Right Lateral), `_SB_BK_GLB` to `-0007` (Full Pair), and normalizes the text.
*   **New Balance:** Converts names to lowercase and sequences like `_2`, `_3` into `SKU-0-0001`, `SKU-0-0002` with a `.jpg` extension.
*   **Timberland:** Maps the messy original footwear (`_1`->`0001`, `_6`->`0002`, `_4`->`0003`) omitting view `_8`, and automatically structures views for apparel and accessories using logical rules.

## Conclusion

The **Gretel Image Hub** is more than just a photo cropper; it is the guardian of brand aesthetics. It turns chaotic batches from international suppliers into a visually harmonious storefront operated by zero-cost local artificial intelligence, freeing up hundreds of operational hours and ensuring that the perceived quality of the e-commerce is always at the highest level.