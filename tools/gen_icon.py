#!/usr/bin/env python3
"""Icono de lanzador 40×40 de CALLE: el marcador ámbar en un cruce (propuesta B, elegida el 2026-10-25).
El dibujo vive en tools/caratula.py, junto con la carátula de la tienda."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from caratula import ROOT, icono_b  # noqa: E402

out = ROOT / "resources" / "drawables" / "launcher_icon.png"
icono_b().save(out)
print(f"escrito {out}")
