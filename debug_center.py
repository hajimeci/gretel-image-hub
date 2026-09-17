from PIL import Image
import os

img_path = r'C:\Users\hchumpitaz\Downloads\prueba_imagenes_0709\ADKJ7422-0001.jpg'
img = Image.open(img_path).convert("RGB")
width, height = img.size

# Let's find the bounding box of pixels that are significantly darker than the background F5F5F5
# and not just a light shadow.
# A shadow is usually greyish, so R, G, B are similar and close to 245.
# Let's check the pixel intensity.
left, top, right, bottom = width, height, 0, 0

for y in range(height):
    for x in range(width):
        r, g, b = img.getpixel((x, y))
        # Distance from white/light grey
        dist = ((r - 245)**2 + (g - 245)**2 + (b - 245)**2)**0.5
        # Also check if it's a shadow (shadows are neutral, so std dev of rgb is low)
        mean_val = (r + g + b) / 3
        is_neutral = abs(r - mean_val) < 10 and abs(g - mean_val) < 10 and abs(b - mean_val) < 10
        
        # If it's far from background, and NOT a light neutral shadow
        # Let's say if it's darker than 220, it's either dark shadow or object.
        # But wait, Adidas shadows can be very dark right next to the shoe.
        if r < 235 and g < 235 and b < 235:
            # Let's consider this part of the object/shadow
            if x < left: left = x
            if x > right: right = x
            if y < top: top = y
            if y > bottom: bottom = y

print(f"Simple Dark Threshold Bbox: left={left}, right={right}, top={top}, bottom={bottom}")
print(f"Width: {right - left}, Height: {bottom - top}")

# What if we trim the left by a percentage to ignore the shadow?
# The user mentioned the shadow is on the left.
print(f"Let's check the pixels on the far left of this bbox (x={left} to {left+50}, y={top} to {bottom})")
sample_y = (top + bottom) // 2
print(f"Pixel at ({left}, {sample_y}): {img.getpixel((left, sample_y))}")
print(f"Pixel at ({left+20}, {sample_y}): {img.getpixel((left+20, sample_y))}")
print(f"Pixel at ({left+50}, {sample_y}): {img.getpixel((left+50, sample_y))}")
