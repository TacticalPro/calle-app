#!/usr/bin/env python3
"""Icono de lanzador 40×40 (fenix7xpro): marcador de posición blanco sobre negro."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
LADO = 40
ESC = 8  # se dibuja a 8× y se reduce, para suavizar el contorno

g = LADO * ESC
img = Image.new("RGB", (g, g), (0, 0, 0))
d = ImageDraw.Draw(img)
d.ellipse((0, 0, g - 1, g - 1), outline=(0x55, 0x55, 0x55), width=2 * ESC)
# Marcador: círculo con punta hacia abajo y un hueco negro en el centro.
cx, cy, r = g / 2, g * 0.40, g * 0.20
d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255))
d.polygon([(cx - r * 0.86, cy + r * 0.5), (cx + r * 0.86, cy + r * 0.5), (cx, g * 0.82)], fill=(255, 255, 255))
h = r * 0.42
d.ellipse((cx - h, cy - h, cx + h, cy + h), fill=(0, 0, 0))
img = img.resize((LADO, LADO), Image.LANCZOS)
out = ROOT / "resources" / "drawables" / "launcher_icon.png"
img.save(out)
print(f"escrito {out}")
