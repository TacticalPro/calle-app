#!/usr/bin/env python3
"""Banner de la tienda (Hero Image) de las apps Calles, uno por idioma.

    tools/banner.py --region galicia --idioma es   → docs/tienda/galicia/banner_es.png
    tools/banner.py --region madrid --idioma en    → docs/tienda/banner_en.png (Madrid, como la portada)
    tools/banner.py --todos                        los diez (galicia, madrid, coruna, pontevedra, valencia × es, en)

La propuesta A (elegida por el autor el 2026-10-30): el rótulo de la carátula B («CALLES /
GALICIA|MADRID» y el lema) a la izquierda y la pantalla del reloj (tools/mockup.py, 7X Pro) a la derecha, sobre
el callejero real tenue de la carátula B a su escala (k = alto/500), con el centro de la región (casco de Santiago
/ Puerta del Sol) bajo el reloj. El banner es de cada app coincide píxel a píxel con
el de la propuesta.

A Coruña, Pontevedra y la Comunitat Valenciana (2026-10-30): la misma composición, con el rótulo de su portada
(caratula.titulo(), apretado como allí si es largo), el centro de caratula.CENTROS y una escena de su ficha
publicada en la tienda. Si el rótulo no cabe ni apretado, el programa para: no recorta.

El rótulo no se traduce; solo el lema. El cuerpo del rótulo lo fija el lema es, así que los dos idiomas llevan
la misma letra y el lema en no puede ser más ancho.

Medida y peso, de la ayuda del campo «Hero Image (Optional)» del portal de Connect IQ (leída el 2026-10-30):
"The image (JPG, GIF or PNG) has to be 1440x720 pixels large and can have a maximum size of 2048 KB."
Sin zona segura en el formulario. El tope se lee por lo bajo: 2048 KB = 2.048.000 B. Se genera siempre PNG.

Las comprobaciones fallan cerradas: si el PNG no tiene la proporción, la medida, el formato o el peso, no se
escribe y el programa sale con error.
"""
import os
import sys

from PIL import Image, ImageDraw

import caratula as C
import mockup

MEDIDA = (1440, 720)          # obligatoria (portal de Connect IQ)
TOPE = 2_048_000              # bytes: «maximum size of 2048 KB», leído por lo bajo
PROPORCION = (2, 1)
MARGEN = 0.08                 # margen libre por lado para lo esencial; el callejero sí llega al borde
SALIDAS = {"galicia": C.ROOT / "docs" / "tienda" / "galicia",
           "madrid": C.ROOT / "docs" / "tienda",
           "coruna": C.ROOT / "docs" / "tienda" / "coruna",
           "pontevedra": C.ROOT / "docs" / "tienda" / "pontevedra",
           "valencia": C.ROOT / "docs" / "tienda" / "valencia"}
# Pontevedra, Rúa dos Campos 19: lo que enseña docs/tienda/pontevedra/ficha_2.png (tools/medida_c5.py pontevedra
# --ficha, 42.44106 -8.626043), sin barrio. Va aquí y no en mockup.py para no tocar las fichas.
CAMPOS = [("Pontevedra: Rúa dos Campos 19", dict(calle1="Rúa dos Campos", num1="nº 19", tramo=("Rúa da Reguiña",)))]
# Pantallas del reloj solo con sitios públicos, y en las apps nuevas, de su ficha de la tienda.
ESCENA = {"galicia": (mockup.ESCENAS_GALICIA, "Santiago: Rúa do Franco"),
          "madrid": (mockup.ESCENARIOS, "Madrid: Gran Vía"),
          "coruna": (mockup.ESCENAS_GALICIA, "A Coruña: Rúa Real"),          # coruna/ficha_2.png
          "pontevedra": (CAMPOS, "Pontevedra: Rúa dos Campos 19"),          # pontevedra/ficha_2.png
          "valencia": (mockup.ESCENAS_VALENCIA, "València: Sant Vicent Màrtir")}   # valencia/ficha_1.png
# El en, con las palabras de la descripción en de la ficha: «Street name, door number and the streets on each
# side, with no phone and no signal» (docs/tienda/descripcion.md, calle-galicia.md, calle-madrid.md). «STREET
# NAME AND DOOR NUMBER, NO SIGNAL» no cabe al cuerpo del es (625 px de 547); este sí (538).
LEMAS = {"es": "LA CALLE Y EL PORTAL, SIN COBERTURA", "en": "STREET AND DOOR NUMBER, NO SIGNAL"}


def fondo(w, h, region, foco, k):
    """El callejero tenue de la carátula B en w×h, con el centro de la región (Santiago / Sol) en el píxel foco."""
    m_px = C.LADO_M / 500 / k                      # metros por píxel: a k = 1, los de la carátula
    meta, _ = C.meta(region)
    lat, lon = C.CENTROS[region]
    dx, dy = (w / 2 - foco[0]) * m_px, (foco[1] - h / 2) * m_px   # el centro del lienzo, en metros desde el foco
    centro = (lat + dy / meta["ky"], lon + dx / meta["kx"])
    lado = max(w, h)
    esc = 4 if lado <= 1200 else 3
    m = C.mapa(lado, (0x4A, 0x4A, 0x4A), 2.6 * k, centro=centro, lado_m=lado * m_px, esc=esc, region=region)
    img = Image.new("RGBA", (w, h), C.FONDO + (255,))
    img.alpha_composite(m.crop(((lado - w) // 2, (lado - h) // 2, (lado - w) // 2 + w, (lado - h) // 2 + h)))
    return img


def velo(img, x_claro, x_oscuro):
    """El velo oscuro de la carátula B (10,10,10,235), en degradado horizontal: transparente en x_claro, pleno en
    x_oscuro y más allá, para que el rótulo se lea sin cortar el mapa con una franja."""
    w, h = img.size
    capa = Image.new("RGBA", (w, h), (10, 10, 10, 0))
    a = Image.new("L", (w, 1), 0)
    for x in range(w):
        t = (x - x_claro) / (x_oscuro - x_claro)
        a.putpixel((x, 0), round(235 * min(1, max(0, t))))
    capa.putalpha(a.resize((w, h)))
    img.alpha_composite(capa)


def ancho_lema(d, lema, s):
    return sum(d.textlength(ch, font=C.fuente(round(21 * s), 500)) for ch in lema) + s * (len(lema) - 1)


def rotulo(img, cx, cy, region, k, ancho_max, lema):
    """El bloque de texto de la carátula B (CALLES / región / lema), centrado en (cx, cy): a escala k·1,25 o menor, la
    que haga caber el lema es (la línea más ancha) en ancho_max. El lema de otro idioma va al mismo cuerpo."""
    d = ImageDraw.Draw(img)
    s = 1.25 * k
    s = min(s, s * ancho_max / ancho_lema(d, LEMAS["es"], s))
    if ancho_lema(d, lema, s) > ancho_max:
        sys.exit(f"el lema «{lema}» no cabe en {ancho_max:.0f} px al cuerpo del lema es")
    rot, f = C.titulo(region), C.fuente(round(28 * s), 500)
    esp = C.espacio_titulo(d, rot, f, ancho_max, maximo=round(12 * s), minimo=round(2 * s))
    if sum(d.textlength(ch, font=f) for ch in rot) + esp * (len(rot) - 1) > ancho_max:
        sys.exit(f"el rótulo «{rot}» no cabe en {ancho_max:.0f} px ni apretado")
    C.texto(d, (cx, cy - 50 * s), "CALLES", C.fuente(round(78 * s)), C.BLANCO, espacio=round(8 * s))
    C.texto(d, (cx, cy + 0 * s), rot, f, C.AMBAR, espacio=esp)
    C.texto(d, (cx, cy + 38 * s), lema, C.fuente(round(21 * s), 500), C.GRIS, espacio=max(1, round(s)))


def reloj(img, cx, cy, diam, region, k):
    """La pantalla real del reloj (tools/mockup.py, 7X Pro) en su bisel, con sombra y el aro ámbar fino."""
    mockup.usar("fenix7xpro")
    escenas, nombre = ESCENA[region]
    bisel = round(diam * 0.05)
    px = diam - 2 * bisel
    pant = C.circulo(mockup.render(dict(escenas)[nombre]).resize((px, px), Image.LANCZOS), px)
    caja = Image.new("RGBA", (diam, diam), (0, 0, 0, 0))
    dc = ImageDraw.Draw(caja)
    dc.ellipse((0, 0, diam - 1, diam - 1), fill=(0x3A, 0x3A, 0x3A))
    dc.ellipse((3, 3, diam - 4, diam - 4), fill=(0x22, 0x22, 0x22))
    caja.alpha_composite(pant, (bisel, bisel))
    x0, y0 = round(cx - diam / 2), round(cy - diam / 2)
    sombra = Image.new("RGBA", img.size, (0, 0, 0, 0))
    m = round(diam * 0.06)
    ImageDraw.Draw(sombra).ellipse((x0 - m, y0 - m, x0 + diam + m, y0 + diam + m), fill=(0, 0, 0, 200))
    img.alpha_composite(sombra)
    a = round(diam * 0.03) + m
    ImageDraw.Draw(img).ellipse((x0 - a, y0 - a, x0 + diam + a, y0 + diam + a), outline=C.AMBAR + (255,),
                                width=max(2, round(3 * k)))
    img.alpha_composite(caja, (x0, y0))


def banner(region, idioma="es"):
    """Rótulo a la izquierda y reloj a la derecha, sobre el centro de la región. Lo esencial queda dentro del margen
    libre de cada lado; el callejero sí llega al borde."""
    w, h = MEDIDA
    k = h / 500
    mx, my = w * MARGEN, h * MARGEN
    diam = round(min(h * 0.70, (h - 2 * my) / 1.2))   # 1,2: el reloj con su aro ámbar
    foco = (w - mx - diam * 0.6, h / 2)
    borde = foco[0] - diam * 0.62                    # el aro ámbar, con aire
    img = fondo(w, h, region, foco, k)
    velo(img, borde, mx + (borde - mx) * 0.45)     # oscuro bajo el rótulo, se abre hacia el reloj
    rotulo(img, (mx + borde) / 2, h / 2, region, k, (borde - mx) * 0.92, LEMAS[idioma])
    reloj(img, *foco, diam, region, k)
    return img.convert("RGB")


def comprobar(ruta, tope=None):
    """Lista de fallos del PNG en ruta; vacía si cumple proporción, medida, formato y peso."""
    tope = TOPE if tope is None else tope
    fallos = []
    with Image.open(ruta) as im:
        w, h = im.size
        if w * PROPORCION[1] != h * PROPORCION[0]:
            fallos.append(f"proporción {w}×{h}, no {PROPORCION[0]}:{PROPORCION[1]}")
        if im.size != MEDIDA:
            fallos.append(f"medida {w}×{h}, no {MEDIDA[0]}×{MEDIDA[1]}")
        if im.format != "PNG":
            fallos.append(f"formato {im.format}, no PNG")
    peso = os.path.getsize(ruta)
    if peso > tope:
        fallos.append(f"peso {peso} B, por encima del tope de {tope} B")
    return fallos


def escribir(img, out, tope=None):
    """Guarda img en out solo si pasa comprobar(); si no, no deja nada y sale con error."""
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.stem + ".tmp.png")
    img.save(tmp, "PNG", optimize=True)
    fallos = comprobar(tmp, tope)
    if fallos:
        tmp.unlink()
        sys.exit(f"banner NO escrito ({out}): " + "; ".join(fallos))
    os.replace(tmp, out)
    nombre = out.relative_to(C.ROOT) if out.is_relative_to(C.ROOT) else out
    print(f"escrito {nombre} ({MEDIDA[0]}×{MEDIDA[1]}, {os.path.getsize(out)} B)")


def salida(region, idioma):
    return SALIDAS[region] / f"banner_{idioma}.png"


def opcion(nombre, defecto=None):
    if nombre not in sys.argv:
        return defecto
    i = sys.argv.index(nombre) + 1
    return sys.argv[i] if i < len(sys.argv) else None


def main():
    if "--todos" in sys.argv:
        for region in SALIDAS:
            for idioma in LEMAS:
                escribir(banner(region, idioma), salida(region, idioma))
        return
    region, idioma = opcion("--region"), opcion("--idioma", "es")
    if region is None or idioma is None:
        sys.exit(__doc__)
    if region not in SALIDAS:
        sys.exit(f"región desconocida: {region} (galicia | madrid)")
    if idioma not in LEMAS:
        sys.exit(f"idioma desconocido: {idioma} (es | en)")
    escribir(banner(region, idioma), salida(region, idioma))


if __name__ == "__main__":
    main()
