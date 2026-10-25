#!/usr/bin/env python3
"""Maquetas de CALLE sin simulador (no hay permiso de captura de pantalla).

Replica las cotas de source/VistaCalle.mc y el reparto en líneas de source/Texto.mc
con Roboto Condensed Bold, la fuente vectorial del reloj. Las fuentes de sistema
(XTINY, TINY) se aproximan con la misma Roboto: lo fiel es el nombre y su reparto.
Escribe tools/out/mockups.png.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FUENTE = ROOT / "tools" / "fonts" / "RobotoCondensed.ttf"
W = H = 280
BLANCO, GRIS, GRIS_OSC = (255, 255, 255), (0xAA, 0xAA, 0xAA), (0x55, 0x55, 0x55)
AMARILLO, ROJO, VERDE, NARANJA = (0xFF, 0xAA, 0x00), (0xFF, 0, 0), (0, 0xFF, 0), (0xFF, 0x55, 0)


def roboto(size, peso=700):
    f = ImageFont.truetype(str(FUENTE), size)
    f.set_variation_by_axes([peso])
    return f


V = {s: roboto(s) for s in (26, 28, 30, 32, 38, 44)}
# Cotas de source/L.mc (pantalla v3: la hora en grande arriba).
HORA_Y, HORA_PUNTO, SUB_Y, NOMBRE_Y, NOMBRE_Y_SUB = 34, 18, 63, 58, 76
XTINY, TINY, SMALL = roboto(16, 500), roboto(25, 500), roboto(27, 600)
GRANDE = [V[38], V[32], V[28], V[26], SMALL]
MEDIA = [V[30], V[26], SMALL, TINY]

TIPOS = dict(zip(*[iter("Rúa R. Avenida Av. Praza Pr. Praciña Prc. Travesa Tr. Travesía Tr. Camiño Cm. Calle C/ "
                        "Plaza Pl. Paseo P.º Rolda Rd. Ronda Rd. Estrada Estr. Carretera Ctra. Corredoira Corr. "
                        "Costa Cta. Glorieta Gl. Lugar Lg. Urbanización Urb. Polígono Pol. Pasaxe Psx. "
                        "Ruela Rla.".split())] * 2))


def corta(n):
    t, _, resto = n.partition(" ")
    return TIPOS[t] + " " + resto if t in TIPOS and resto else n


def alto(f):
    a, d = f.getmetrics()
    return f.size if f in V.values() else a + d


def ancho_franja(y0, y1, margen):
    r, c = W // 2, H // 2
    d = max(abs(y0 - c), abs(y1 - c))
    return 0 if d >= r else int(2 * math.sqrt(r * r - d * d)) - 2 * margen


def partir(s, f, anchos):
    lineas, actual = [], ""
    for p in s.split():
        prueba = p if not actual else actual + " " + p
        if f.getlength(prueba) <= anchos[len(lineas)]:
            actual = prueba
            continue
        if not actual:
            return None
        lineas.append(actual)
        if len(lineas) >= len(anchos) or f.getlength(p) > anchos[len(lineas)]:
            return None
        actual = p
    if actual:
        lineas.append(actual)
    return lineas


def colocar(nombre, fuentes, max_lineas, y0, y1):
    formas = [nombre] if corta(nombre) == nombre else [nombre, corta(nombre)]
    for f in fuentes:
        a = alto(f)
        lh = int(a * 0.92)
        for forma in formas:
            for n in range(1, max_lineas + 1):
                if n * lh > y1 - y0:
                    break
                top = (y0 + y1 - n * lh) // 2
                lineas = partir(forma, f, [ancho_franja(top + i * lh, top + i * lh + a, 10) for i in range(n)])
                if lineas:
                    return f, lineas, (y0 + y1 - len(lineas) * lh) // 2, lh
    return None


def caja(d, nombre, fuentes, max_lineas, y0, y1, color):
    c = colocar(nombre, fuentes, max_lineas, y0, y1)
    if not c:
        d.text((W // 2, (y0 + y1) // 2), corta(nombre)[:22] + "…", font=TINY, fill=color, anchor="mm")
        return
    f, lineas, top, lh = c
    for i, ln in enumerate(lineas):
        d.text((W // 2, top + i * lh), ln, font=f, fill=color, anchor="ma")


def estado(d, e):
    """La hora en grande (Roboto Condensed Bold 44, como el fēnix 7) con el punto del GPS a la izquierda;
    si el dato es viejo, su edad debajo en amarillo, en lugar del barrio."""
    w = d.textlength("23:41", font=V[44])
    x0 = W / 2 - (w + HORA_PUNTO) / 2
    d.ellipse((x0, HORA_Y - 6, x0 + 12, HORA_Y + 6), fill=e.get("punto", VERDE))
    d.text((x0 + HORA_PUNTO, HORA_Y), "23:41", font=V[44], fill=BLANCO, anchor="lm")
    if e.get("edad") and "detalle" not in e:
        linea(d, SUB_Y, e["edad"], AMARILLO)


def linea(d, y, txt, color, margen=10):
    """Una línea XTINY recortada al ancho de la franja, como VistaCalle.linea()."""
    w = ancho_franja(y - 11, y + 11, margen)
    while txt and XTINY.getlength(txt) > w:
        txt = txt[:-2] + "…" if not txt.endswith("…") else txt[:-2] + "…"
    d.text((W // 2, y), txt, font=XTINY, fill=color, anchor="mm")


def render(e):
    if "anillo" in e:
        return ir_anillo(e)
    if "acciones" in e:
        return acciones(e)
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    if "lista" not in e:
        estado(d, e)
    col = GRIS if e.get("edad") else BLANCO
    if "aviso" in e:
        titulo, color, sub = e["aviso"]
        d.text((W // 2, 112), titulo, font=V[30], fill=color, anchor="mm")
        linea(d, 152, sub, GRIS)
        if e.get("pie"):
            d.text((W // 2, 236), e["pie"], font=XTINY, fill=GRIS, anchor="mm")
    elif "lugar" in e:
        linea(d, SUB_Y, "sin calle a 50 m", AMARILLO)
        caja(d, e["lugar"], MEDIA, 2, 86, 146, col)
        linea(d, 164, e["sub"], GRIS)
        d.text((W // 2, 236), e["pie"], font=XTINY, fill=GRIS, anchor="mm")
    elif "detalle" in e:
        for i, ln in enumerate(e["detalle"]):
            d.text((W // 2, SUB_Y + 2 + i * 26), ln, font=XTINY, fill=BLANCO, anchor="mm")
    elif "ir" in e:
        return ir(e)
    elif "lista" in e:
        d.text((W // 2, 62), "Anotaciones", font=SMALL, fill=BLANCO, anchor="mm")
        for i, (et, sub) in enumerate(e["lista"]):
            y = 96 + i * 58
            if i == 0:
                d.rounded_rectangle((18, y - 6, W - 18, y + 46), 8, outline=GRIS_OSC)
            d.text((W // 2, y + 10), corta(et), font=TINY, fill=BLANCO, anchor="mm")
            d.text((W // 2, y + 34), sub, font=XTINY, fill=GRIS, anchor="mm")
    elif e.get("cruce"):
        y0 = NOMBRE_Y_SUB if e.get("barrio") or e.get("edad") else NOMBRE_Y
        if e.get("barrio") and not e.get("edad"):
            linea(d, SUB_Y, e["barrio"], GRIS)
        caja(d, e["calle1"], GRANDE, 3, y0, 168, col)
        if e.get("num1"):
            d.text((W // 2, 170), e["num1"], font=V[30], fill=col, anchor="ma")
        linea(d, 221, "esq. " + corta(e["cruce"]), col)
        d.text((W // 2, 252), "CRUCE", font=XTINY, fill=AMARILLO, anchor="mm")
    elif "calle2" in e:
        caja(d, e["calle1"], MEDIA, 2, NOMBRE_Y_SUB if e.get("edad") else NOMBRE_Y, 116, col)
        if e.get("num1"):
            d.text((W // 2, 117), e["num1"], font=XTINY, fill=col, anchor="ma")
        d.line((W // 2 - 90, 146, W // 2 + 90, 146), fill=GRIS_OSC)
        caja(d, e["calle2"], MEDIA, 2, 152, 214, col)
        if e.get("num2"):
            d.text((W // 2, 215), e["num2"], font=XTINY, fill=col, anchor="ma")
        d.text((W // 2, 252), "DOS CALLES", font=XTINY, fill=AMARILLO, anchor="mm")
    else:
        y0 = NOMBRE_Y_SUB if e.get("barrio") or e.get("edad") else NOMBRE_Y
        y1 = 146 if e.get("tramo") else 192
        if e.get("barrio") and not e.get("edad"):
            linea(d, SUB_Y, e["barrio"], GRIS)
        caja(d, e["calle1"], GRANDE, 3, y0, y1, col)
        t = e.get("tramo")
        if e.get("num1"):
            d.text((W // 2, y1 + 4 if t else y1 + 8), e["num1"], font=V[30], fill=col, anchor="ma")
        if t and len(t) == 2:
            linea(d, 190, "entre " + corta(t[0]), GRIS)
            linea(d, 212, "y " + corta(t[1]), GRIS)
        elif t:
            linea(d, 190, "cerca de " + corta(t[0]), GRIS)
    if e.get("anotado"):
        txt, color = e["anotado"]
        d.rounded_rectangle((24, 108, W - 24, 172), 12, fill=(0, 0, 0), outline=color, width=3)
        d.text((W // 2, 140), txt, font=SMALL, fill=BLANCO, anchor="mm")
    return redondo(img)


def redondo(img):
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, W - 1, H - 1), fill=255)
    fondo = Image.new("RGB", (W, H), (40, 40, 40))
    fondo.paste(img, (0, 0), mask)
    return fondo


def ir(e):
    """La guía de source/VistaIr.mc: tipo, nombre, flecha (relativa a la brújula), distancia y dirección."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    nombre, dirc, tipo, dist, ang, card, i, n = e["ir"]
    hosp = tipo.startswith("HOSPITAL")
    color = (0xFF, 0, 0) if hosp else (0, 0x55, 0xFF)
    d.text((W // 2, 24), f"23:41   {i}/{n}", font=XTINY, fill=GRIS, anchor="mm")
    d.text((W // 2, 48), tipo, font=XTINY, fill=color, anchor="mm")
    lineas = partir(nombre, V[26], [ancho_franja(60, 108, 10)] * 2) or [nombre[:24] + "…"]
    for k, ln in enumerate(lineas):
        d.text((W // 2, 84 + (k - (len(lineas) - 1) / 2) * 26), ln, font=V[26], fill=BLANCO, anchor="mm")
    if e.get("llegado"):
        d.text((W // 2, 152), "HA LLEGADO", font=V[32], fill=VERDE, anchor="mm")
    else:
        c, s_ = math.cos(ang), math.sin(ang)
        pts = [(W // 2 + x * c - y * s_, 152 + x * s_ + y * c) for x, y in ((0, -40), (27, 22), (0, 9), (-27, 22))]
        d.polygon(pts, fill=color, outline=BLANCO, width=2)
    d.text((W // 2, 208), dist, font=V[38], fill=BLANCO, anchor="mm")
    linea(d, 238, corta(dirc), GRIS)
    d.text((W // 2, 258), f"línea recta · {card}", font=XTINY, fill=GRIS_OSC, anchor="mm")
    return redondo(img)


# Anillo de brújula (v3.1, 2026-10-24; source/Anillo.mc; referencia: Pin Point — Location and Share). Ocupa la franja
# exterior: el texto vive dentro de RI y el anillo gira con el rumbo del reloj.
RI, R_CIRC = 128, 133   # radio libre para el texto; radio del círculo fino del anillo
AZUL = (0, 0x55, 0xFF)
OSCURO = {ROJO: (0xAA, 0, 0), AZUL: (0, 0, 0xAA), VERDE: (0, 0xAA, 0)}   # el círculo, en el tono oscuro del destino


def punto(a, r):
    """Punto a r px del centro en el ángulo a (radianes, 0 = arriba, horario)."""
    return (W / 2 + r * math.sin(a), H / 2 - r * math.cos(a))


def anillo(d, rumbo, destino, color):
    """Círculo fino (tono oscuro del destino), marcas cada 10° (cada 30°, más largas), triángulos en los cardinales (N rojo y mayor)
    y el destino como una bola de su color. rumbo y destino en grados; el anillo gira con el rumbo."""
    c = W / 2
    d.ellipse((c - R_CIRC, c - R_CIRC, c + R_CIRC, c + R_CIRC), outline=OSCURO.get(color, GRIS_OSC), width=1)
    for k in range(36):
        if k % 9 == 0:
            continue
        a = math.radians(k * 10 - rumbo)
        if k % 3 == 0:
            d.line([punto(a, 129), punto(a, 138)], fill=GRIS, width=2)
        else:
            d.line([punto(a, 131), punto(a, 135)], fill=GRIS_OSC, width=1)
    for k in range(4):
        a = math.radians(k * 90 - rumbo)
        punta, base, medio, col = (123, 139, 8, ROJO) if k == 0 else (128, 138, 5, GRIS)
        bx, by = punto(a, base)
        tx, ty = math.cos(a), math.sin(a)          # tangente al anillo
        d.polygon([punto(a, punta), (bx + medio * tx, by + medio * ty), (bx - medio * tx, by - medio * ty)], fill=col)
    if destino is not None:
        x, y = punto(math.radians(destino - rumbo), R_CIRC)
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color, outline=BLANCO, width=2)


def ancho_in(y0, y1, margen=4):
    """Ancho libre dentro del anillo en la franja [y0, y1]."""
    dd = max(abs(y0 - H / 2), abs(y1 - H / 2))
    return 0 if dd >= RI else int(2 * math.sqrt(RI * RI - dd * dd)) - 2 * margen


def linea_in(d, y, txt, color, f=None):
    f = f or XTINY
    w = ancho_in(y - 8, y + 8)
    while txt and f.getlength(txt) > w:
        txt = txt[:-2] + "…"
    d.text((W // 2, y), txt, font=f, fill=color, anchor="mm")


def ir_anillo(e):
    """VistaIr con el anillo: el mismo contenido, recolocado dentro de RI."""
    a = e["anillo"]
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    llegado = a.get("llegado")
    anillo(d, a["rumbo"], None if llegado else a["destino"], a["color"])
    linea_in(d, 30, f"23:41  {a['i']}/{a['n']}", GRIS)
    linea_in(d, 52, a["tipo"], a["color"])
    lh = 26
    for n in (1, 2):
        top = 86 - n * lh // 2
        lineas = partir(a["nombre"], V[26], [ancho_in(top + k * lh, top + (k + 1) * lh) for k in range(n)])
        if lineas:
            break
    else:
        lineas = [a["nombre"][:22] + "…"]
    for k, ln in enumerate(lineas):
        d.text((W // 2, 86 + (k - (len(lineas) - 1) / 2) * lh), ln, font=V[26], fill=BLANCO, anchor="mm")
    if llegado:
        d.text((W // 2, 154), "HA LLEGADO", font=V[32], fill=VERDE, anchor="mm")
    else:
        ang = math.radians(a["destino"] - a["rumbo"])
        c, s_ = math.cos(ang), math.sin(ang)
        pts = [(W // 2 + x * c - y * s_, 154 + x * s_ + y * c) for x, y in ((0, -40), (27, 22), (0, 9), (-27, 22))]
        d.polygon(pts, fill=a["color"], outline=BLANCO, width=2)
    d.text((W // 2, 200), a["dist"], font=V[38], fill=BLANCO, anchor="mm")
    linea_in(d, 226, corta(a["dir"]), GRIS)
    card = "N NE E SE S SO O NO".split()[round((a["destino"] or 0) / 45) % 8]
    linea_in(d, 245, "línea recta · " + card, GRIS_OSC)
    return redondo(img)


def acciones(e):
    """Menú de una anotación: «Ir aquí» y «Borrar» (Menu2: título arriba, la opción con foco enmarcada)."""
    titulo, items = e["acciones"]
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    linea(d, 62, corta(titulo), BLANCO)
    for i, (et, sub) in enumerate(items):
        y = 100 + i * 64
        if i == 0:
            d.rounded_rectangle((18, y - 8, W - 18, y + 48), 8, outline=GRIS_OSC)
        d.text((W // 2, y + 10), et, font=SMALL, fill=BLANCO, anchor="mm")
        d.text((W // 2, y + 34), sub, font=XTINY, fill=GRIS, anchor="mm")
    return redondo(img)


ESCENARIOS_BRUJULA = [
    ("Antes (v3)", dict(ir=("Hospital Clínico San Carlos", "Calle del Profesor Martín Lagos", "HOSPITAL · URGENCIAS",
                            "1,4 km", math.radians(290 - 25), "O", 1, 8))),
    ("Anillo: hospital", dict(anillo=dict(nombre="Hospital Clínico San Carlos", dir="Calle del Profesor Martín Lagos",
                                          tipo="HOSPITAL · URGENCIAS", color=ROJO, dist="1,4 km", rumbo=25,
                                          destino=290, i=1, n=8))),
    ("Anillo: comisaría", dict(anillo=dict(nombre="Comisaría de Distrito Centro", dir="Calle de Leganitos 19",
                                           tipo="COMISARÍA CNP", color=AZUL, dist="650 m", rumbo=180, destino=137,
                                           i=1, n=8))),
    ("Anotación: acciones", dict(acciones=("21:15 · Rúa do Vilar 44 / Rúa Nova ~11",
                                           [("Ir aquí", "flecha y distancia"), ("Borrar", "pide confirmación")]))),
    ("Ir a una anotación", dict(anillo=dict(nombre="Rúa do Vilar 44 / Rúa Nova ~11", dir="29T 537189 4747429",
                                            tipo="ANOTACIÓN · 21:15", color=VERDE, dist="320 m", rumbo=90, destino=20,
                                            i=3, n=3))),
    ("Anillo: llegada", dict(anillo=dict(nombre="Comisaría de Distrito Centro", dir="Calle de Leganitos 19",
                                         tipo="COMISARÍA CNP", color=AZUL, dist="20 m", rumbo=330, destino=0,
                                         i=1, n=3, llegado=True))),
]

FRANCO = dict(calle1="Rúa do Franco", num1="nº 33", barrio="Casco Histórico",
              tramo=("Ruela de Paio o Eremita", "Rúa da Raíña"))
ESCENARIOS = [
    ("Tramo y barrio", FRANCO),
    ("Madrid: barrio · distrito", dict(calle1="Calle de la Princesa", num1="nº 25", barrio="Argüelles · Moncloa-Aravaca",
                                      tramo=("Calle de Alberto Aguilera", "Calle del Marqués de Urquijo"))),
    ("Madrid: Gran Vía", dict(calle1="Gran Vía", num1="nº 31", barrio="Sol · Centro",
                             tramo=("Calle de la Montera", "Calle de Hortaleza"))),
    ("Dato viejo (edad)", dict(FRANCO, edad="hace 3 min", punto=ROJO)),
    ("Un solo lado", dict(calle1="Avenida de Lugo", num1="nº 157", barrio="A Raxeira",
                          tramo=("Rúa da Batalla de Clavijo",))),
    ("Sin barrio, sin nº", dict(calle1="Rúa do Hórreo", tramo=("Rúa da República de El Salvador", "Rúa de Gómez Ulla"),
                                punto=AMARILLO)),
    ("Muy largo", dict(calle1="Rúa de Bernardo Barreiro de Vázquez-Varela", num1="nº 4", barrio="O Ensanche",
                       tramo=("Rúa de San Pedro de Mezonzo", "Rúa do Doutor Teixeiro"))),
    ("Esquina", dict(calle1="Rúa do Franco", num1="nº 54", cruce="Rúa da Raíña", barrio="Casco Histórico")),
    ("Dos calles", dict(calle1="Rúa do Vilar", num1="nº 44", calle2="Rúa Nova", num2="nº 11")),
    ("Sin calle: lugar", dict(lugar="A Amañecida", sub="parroquia de Sorribas", pie="29T 526416 4738906")),
    ("Sin calle, sin lugar", dict(aviso=("SIN CALLE", BLANCO, "parroquia de Calo"), pie="29T 531794 4739311")),
    ("Fuera de zona", dict(aviso=("FUERA DE ZONA", ROJO, "Callejero: Santiago"), pie="29T 540754 4760936")),
    ("START: anotado", dict(FRANCO, anotado=("Anotado 23:41", VERDE))),
    ("Anotaciones (menú)", dict(lista=[("23:41 · Rúa do Franco 33", "23-oct · 29T 537134 4747387"),
                                      ("22:58 · Cornide (parroquia de Calo)", "23-oct · 29T 531794 4739311"),
                                      ("21:15 · Rúa do Vilar 44 / Rúa Nova 11", "23-oct · 29T 537189 4747429")])),
    ("Detalle", dict(detalle=["42.87854  -8.54465", "29T 537188 4747428", "GPS buena · ±8 m", "d1 0.1 m   d2 11.4 m",
                              "tesela t804   12 ms", "memoria 158/768 KB", "Santiago (auto) · 2026-10-23"])),
    # La guía, con el anillo de brújula desde la v3.1 (la de la v3, en ESCENARIOS_BRUJULA, «Antes (v3)»).
    ("Ir: hospital", dict(anillo=dict(nombre="Hospital Clínico San Carlos", dir="Calle del Profesor Martín Lagos",
                                      tipo="HOSPITAL · URGENCIAS", color=ROJO, dist="1,4 km", rumbo=25, destino=290,
                                      i=1, n=8))),
    ("Ir: comisaría", dict(anillo=dict(nombre="Comisaría de Distrito Centro", dir="Calle de Leganitos 19",
                                       tipo="COMISARÍA CNP", color=AZUL, dist="650 m", rumbo=180, destino=137, i=1, n=8))),
    ("Ir: anotación", dict(anillo=dict(nombre="Rúa do Vilar 44 / Rúa Nova ~11", dir="29T 537189 4747429",
                                       tipo="ANOTACIÓN · 21:15", color=VERDE, dist="320 m", rumbo=90, destino=20,
                                       i=3, n=3))),
    ("Ir: llegada", dict(anillo=dict(nombre="Comisaría de Distrito Centro", dir="Calle de Leganitos 19", tipo="COMISARÍA CNP",
                                     color=AZUL, dist="20 m", rumbo=330, destino=0, i=1, n=3, llegado=True))),
]


def ficha():
    """Imágenes de la ficha de la Connect IQ Store en docs/tienda/: portada de 500×500 y cuatro pantallas
    a doble tamaño (560×560) con su rótulo. Solo datos públicos de ejemplo (calles y centros públicos)."""
    out = ROOT / "docs" / "tienda"
    out.mkdir(parents=True, exist_ok=True)
    esc = dict(ESCENARIOS)
    portada = Image.new("RGB", (500, 500), (24, 24, 24))
    portada.paste(render(esc["Madrid: Gran Vía"]).resize((440, 440), Image.LANCZOS), (30, 30))
    portada.save(out / "portada_500.png")
    for k, (titulo, nombre) in enumerate((("Street, door number and the streets on each side", "Madrid: Gran Vía"),
                                          ("Neighbourhood and district, offline", "Madrid: barrio · distrito"),
                                          ("Nearest hospital: arrow and distance", "Ir: hospital"),
                                          ("Nearest police station", "Ir: comisaría")), 1):
        hoja = Image.new("RGB", (600, 660), (24, 24, 24))
        hoja.paste(render(esc[nombre]).resize((560, 560), Image.LANCZOS), (20, 20))
        ImageDraw.Draw(hoja).text((300, 620), titulo, font=roboto(26, 600), fill=GRIS, anchor="mm")
        hoja.save(out / f"ficha_{k}.png")
    print(f"escrito {out}/ (portada_500.png, ficha_1..4.png)")


def main():
    import sys
    if "--ficha" in sys.argv:
        return ficha()
    brujula = "--brujula" in sys.argv
    escenarios = ESCENARIOS_BRUJULA if brujula else ESCENARIOS
    cols = 3 if brujula else 4
    filas = math.ceil(len(escenarios) / cols)
    hoja = Image.new("RGB", (cols * (W + 20) + 20, filas * (H + 50) + 20), (24, 24, 24))
    d = ImageDraw.Draw(hoja)
    for i, (titulo, e) in enumerate(escenarios):
        x, y = 20 + (i % cols) * (W + 20), 20 + (i // cols) * (H + 50)
        hoja.paste(render(e), (x, y))
        d.text((x + W // 2, y + H + 18), titulo, font=TINY, fill=GRIS, anchor="mm")
    out = ROOT / "tools" / "out" / ("mockups-brujula.png" if brujula else "mockups.png")
    out.parent.mkdir(exist_ok=True)
    hoja.save(out)
    print(f"escrito {out}")


if __name__ == "__main__":
    main()
