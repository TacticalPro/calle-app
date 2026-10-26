#!/usr/bin/env python3
"""Carátula de la tienda (500×500) e icono del lanzador (40×40) de CALLE: propuestas.

    tools/caratula.py            las tres propuestas → tools/out/caratulas.png (hoja para elegir)
                                 y tools/out/caratula_<X>.png / icono_<X>.png
    tools/caratula.py --instalar la elegida (B, 2026-10-25): docs/tienda/galicia/portada_500.png,
                                 docs/tienda/portada_500.png (Madrid) y el icono del lanzador,
                                 resources/drawables/launcher_icon.png (de todas las apps Calles)
    tools/caratula.py --region valencia   solo la carátula B de esa app: docs/tienda/<región>/portada_500.png

El fondo es el callejero real de cada app (tools/out/geom-<región>.json, ODbL), dibujado tenue: el casco de
Santiago en Galicia y la Puerta del Sol en Madrid.
La pantalla del reloj sale de tools/mockup.py (la escena «Santiago: Rúa do Franco», datos reales).
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import mockup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "out"
FUENTE = ROOT / "tools" / "fonts" / "RobotoCondensed.ttf"
NEGRO, FONDO = (0, 0, 0), (17, 17, 17)
BLANCO, GRIS, GRIS_OSC = (255, 255, 255), (0xAA, 0xAA, 0xAA), (0x55, 0x55, 0x55)
AMBAR, AZUL_PLACA = (0xFF, 0xAA, 0x00), (0x1F, 0x3B, 0x73)
CENTRO = (42.8792, -8.5446)   # casco de Santiago, entre el Obradoiro y la Quintana
CENTROS = {"galicia": CENTRO, "madrid": (40.4169, -3.7035),   # Madrid: la Puerta del Sol
           "valencia": (39.4697, -0.3765)}                      # València: la Plaça de l'Ajuntament
TITULOS = {"valencia": "COMUNITAT VALENCIANA"}                  # el rótulo ámbar; si no, la región en mayúsculas
LADO_M = 900                  # metros de mapa que caben en la carátula


def fuente(px, peso=700):
    f = ImageFont.truetype(str(FUENTE), px)
    f.set_variation_by_axes([peso])
    return f


def mapa(lado, color, ancho, centro=CENTRO, lado_m=LADO_M, esc=4, region="galicia"):
    """El callejero real alrededor de centro, lado_m metros en lado px (dibujado a esc× y reducido)."""
    meta = json.loads((OUT / f"meta-{region}.json").read_text("utf-8"))
    geom = json.loads((OUT / f"geom-{region}.json").read_text("utf-8"))
    cx = (centro[1] - meta["lon_min"]) * meta["kx"]
    cy = (centro[0] - meta["lat_min"]) * meta["ky"]
    g = lado * esc
    k = g / lado_m
    img = Image.new("RGBA", (g, g), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for c in geom["calles"]:
        pts = [((x - cx) * k + g / 2, g / 2 - (y - cy) * k) for x, y in c["p"]]
        if all(abs(px - g / 2) > g * 0.7 or abs(py - g / 2) > g * 0.7 for px, py in pts):
            continue
        w = ancho * esc * (1.0 if c["c"] == 0 else 0.6 if c["c"] == 1 else 0.35)
        if c["a"]:
            d.polygon(pts, fill=color + (90,))
        else:
            d.line(pts, fill=color + (255,), width=max(1, round(w)), joint="curve")
    return img.resize((lado, lado), Image.LANCZOS)


def pantalla(px):
    """La pantalla real del reloj (mockup, Rúa do Franco) a px de diámetro."""
    mockup.usar("fenix7xpro")
    esc = dict(mockup.ESCENAS_GALICIA)
    return mockup.render(esc["Santiago: Rúa do Franco"]).resize((px, px), Image.LANCZOS)


def circulo(img, px):
    m = Image.new("L", (px, px), 0)
    ImageDraw.Draw(m).ellipse((0, 0, px - 1, px - 1), fill=255)
    out = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    out.paste(img, (0, 0), m)
    return out


def esfera(px, bisel=14):
    """Pantalla dentro de un bisel gris, como el reloj visto de frente."""
    total = px + 2 * bisel
    img = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, total - 1, total - 1), fill=(0x3A, 0x3A, 0x3A))
    d.ellipse((3, 3, total - 4, total - 4), fill=(0x22, 0x22, 0x22))
    img.alpha_composite(circulo(pantalla(px), px), (bisel, bisel))
    return img


def marcador(d, cx, cy, r, color, hueco=NEGRO):
    """El marcador de posición: círculo con punta abajo y hueco."""
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    d.polygon([(cx - r * 0.86, cy + r * 0.5), (cx + r * 0.86, cy + r * 0.5), (cx, cy + r * 2.05)], fill=color)
    h = r * 0.42
    d.ellipse((cx - h, cy - h, cx + h, cy + h), fill=hueco)


def texto(d, xy, s, f, color, anchor="mm", espacio=0):
    if not espacio:
        d.text(xy, s, font=f, fill=color, anchor=anchor)
        return
    ancho = sum(d.textlength(ch, font=f) for ch in s) + espacio * (len(s) - 1)
    x = xy[0] - ancho / 2
    for ch in s:
        d.text((x, xy[1]), ch, font=f, fill=color, anchor="lm")
        x += d.textlength(ch, font=f) + espacio


# ---------------------------------------------------------------- A: el reloj sobre el mapa

def caratula_a():
    img = Image.new("RGBA", (500, 500), FONDO + (255,))
    img.alpha_composite(mapa(500, (0x33, 0x33, 0x33), 2.2))
    sombra = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).ellipse((95, 25, 405, 335), fill=(0, 0, 0, 200))
    img.alpha_composite(sombra)
    img.alpha_composite(esfera(280, 15), (95, 25))
    d = ImageDraw.Draw(img)
    texto(d, (250, 382), "CALLE", fuente(64), BLANCO, espacio=6)
    texto(d, (250, 428), "GALICIA", fuente(28, 500), AMBAR, espacio=10)
    texto(d, (250, 466), "calle y portal, sin cobertura", fuente(22, 400), GRIS)
    return img.convert("RGB")


def icono_a(lado=40, esc=8):
    g = lado * esc
    img = Image.new("RGB", (g, g), NEGRO)
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, g - 1, g - 1), outline=GRIS_OSC, width=2 * esc)
    marcador(d, g / 2, g * 0.38, g * 0.19, BLANCO)
    d.line((g * 0.26, g * 0.86, g * 0.74, g * 0.86), fill=AMBAR, width=3 * esc)
    return img.resize((lado, lado), Image.LANCZOS)


# ---------------------------------------------------------------- B: el marcador en el cruce

def caratula_b(region="galicia"):
    img = Image.new("RGBA", (500, 500), FONDO + (255,))
    img.alpha_composite(mapa(500, (0x4A, 0x4A, 0x4A), 2.6, centro=CENTROS[region], region=region))
    velo = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
    ImageDraw.Draw(velo).rectangle((0, 330, 500, 500), fill=(10, 10, 10, 235))
    img.alpha_composite(velo)
    d = ImageDraw.Draw(img)
    d.ellipse((250 - 60, 175 - 60, 250 + 60, 175 + 60), outline=AMBAR + (255,), width=3)
    marcador(d, 250, 140, 38, AMBAR + (255,), hueco=FONDO + (255,))
    texto(d, (250, 382), "CALLES", fuente(78), BLANCO, espacio=8)
    titulo = TITULOS.get(region, region.upper())
    # Con el espaciado de siempre (12) si cabe en 440 px; un rótulo largo se aprieta.
    f28 = fuente(28, 500)
    espacio = min(12, max(2, (440 - sum(d.textlength(ch, font=f28) for ch in titulo)) // max(1, len(titulo) - 1)))
    texto(d, (250, 432), titulo, f28, AMBAR, espacio=espacio)
    texto(d, (250, 470), "LA CALLE Y EL PORTAL, SIN COBERTURA", fuente(21, 500), GRIS, espacio=1)
    return img.convert("RGB")


def icono_b(lado=40, esc=8):
    g = lado * esc
    img = Image.new("RGB", (g, g), NEGRO)
    d = ImageDraw.Draw(img)
    # Dos calles que se cruzan y el marcador ámbar en el cruce.
    d.line((g * 0.06, g * 0.66, g * 0.94, g * 0.66), fill=GRIS_OSC, width=3 * esc)
    d.line((g * 0.30, g * 0.06, g * 0.62, g * 0.94), fill=GRIS_OSC, width=3 * esc)
    marcador(d, g * 0.53, g * 0.34, g * 0.20, AMBAR)
    return img.resize((lado, lado), Image.LANCZOS)


# ---------------------------------------------------------------- C: la placa de la calle

def placa(d, x0, y0, x1, y1, r):
    d.rounded_rectangle((x0, y0, x1, y1), r, fill=AZUL_PLACA)
    m = int(max(3, (y1 - y0) // 18))
    r = int(r)
    d.rounded_rectangle((x0 + m, y0 + m, x1 - m, y1 - m), max(1, r - m), outline=BLANCO, width=m)


def caratula_c():
    img = Image.new("RGBA", (500, 500), FONDO + (255,))
    img.alpha_composite(mapa(500, (0x30, 0x30, 0x30), 2.2))
    d = ImageDraw.Draw(img)
    placa(d, 70, 120, 430, 300, 22)
    texto(d, (250, 196), "CALLE", fuente(96), BLANCO, espacio=8)
    texto(d, (250, 262), "GALICIA", fuente(32, 500), BLANCO, espacio=12)
    marcador(d, 250, 360, 26, AMBAR + (255,), hueco=FONDO + (255,))
    texto(d, (250, 455), "la calle y el portal, sin cobertura", fuente(24, 400), GRIS)
    return img.convert("RGB")


def icono_c(lado=40, esc=8):
    g = lado * esc
    img = Image.new("RGB", (g, g), NEGRO)
    d = ImageDraw.Draw(img)
    placa(d, g * 0.06, g * 0.22, g * 0.94, g * 0.78, 4 * esc)
    marcador(d, g / 2, g * 0.40, g * 0.13, BLANCO, hueco=AZUL_PLACA)
    return img.resize((lado, lado), Image.LANCZOS)


def hoja(propuestas):
    """Las propuestas en una hoja: la carátula y el icono a tamaño real (40) y ampliado (×4, sin suavizar)."""
    f, fs = fuente(30), fuente(20, 500)
    img = Image.new("RGB", (len(propuestas) * 540 + 20, 760), (40, 40, 40))
    d = ImageDraw.Draw(img)
    for i, (letra, nombre, car, ico) in enumerate(propuestas):
        x = 20 + i * 540
        d.text((x, 20), f"{letra} · {nombre}", font=f, fill=BLANCO)
        img.paste(car, (x, 70))
        img.paste(ico, (x, 600))
        d.text((x + 50, 620), "40 px (real)", font=fs, fill=GRIS, anchor="lm")
        img.paste(ico.resize((160, 160), Image.NEAREST), (x + 340, 590))
    return img


def main():
    import sys
    if "--region" in sys.argv:
        region = sys.argv[sys.argv.index("--region") + 1]
        out = ROOT / "docs" / "tienda" / region
        out.mkdir(parents=True, exist_ok=True)
        caratula_b(region).save(out / "portada_500.png", optimize=True)
        print(f"escrito {out / 'portada_500.png'}")
        return
    if "--instalar" in sys.argv:
        caratula_b().save(ROOT / "docs" / "tienda" / "galicia" / "portada_500.png", optimize=True)
        caratula_b("madrid").save(ROOT / "docs" / "tienda" / "portada_500.png", optimize=True)
        icono_b().save(ROOT / "resources" / "drawables" / "launcher_icon.png")
        print("escrito docs/tienda/galicia/portada_500.png, docs/tienda/portada_500.png "
              "y resources/drawables/launcher_icon.png")
        return
    OUT.mkdir(exist_ok=True)
    props = [("A", "El reloj sobre el mapa", caratula_a(), icono_a()),
             ("B", "El marcador en el cruce", caratula_b(), icono_b()),
             ("C", "La placa de la calle", caratula_c(), icono_c())]
    for letra, _, car, ico in props:
        car.save(OUT / f"caratula_{letra}.png", optimize=True)
        ico.save(OUT / f"icono_{letra}.png")
    hoja(props).save(OUT / "caratulas.png")
    print(f"escrito {OUT / 'caratulas.png'}")


if __name__ == "__main__":
    main()
