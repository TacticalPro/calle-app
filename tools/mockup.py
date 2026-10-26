#!/usr/bin/env python3
"""Maquetas de CALLE sin simulador (no hay permiso de captura de pantalla), para cada pantalla.

Replica las cotas de source/VistaCalle.mc y source/VistaIr.mc, escaladas como L.y() (cotas de la
pantalla de 280 px por alto/280), y el reparto en líneas de source/Texto.mc.
- Fuentes vectoriales (fēnix 7 y 8): Roboto Condensed Bold al tamaño escalado, como en el reloj.
- Fuentes de sistema: alto y ancho por carácter medidos en el simulador de cada reloj
  (tools/fonts/metricas.json, ./ciq.sh fuentes). El reparto en líneas y los recortes salen como en el
  reloj; el dibujo de las letras es Roboto Condensed ajustada a ese ancho: lo fiel es el reparto.
Los menús (anotaciones y acciones) son Menu2 del sistema: su maqueta es aproximada.

    tools/mockup.py                  todos los escenarios en el 7X Pro → tools/out/mockups.png
    tools/mockup.py --reloj fenix5s  en otro reloj                     → tools/out/mockups-fenix5s.png
    tools/mockup.py --todos          una hoja por reloj y la comparativa → tools/out/pantallas.png
    tools/mockup.py --brujula        la guía con y sin anillo          → tools/out/mockups-brujula.png
    tools/mockup.py --ficha          imágenes de la tienda (7X Pro)    → docs/tienda/
    tools/mockup.py --ficha galicia  las de CALLE Galicia               → docs/tienda/galicia/
    tools/mockup.py --ficha murcia   las de Calles Murcia               → docs/tienda/murcia/
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FUENTE = ROOT / "tools" / "fonts" / "RobotoCondensed.ttf"
METRICAS = json.loads((ROOT / "tools" / "fonts" / "metricas.json").read_text())
BLANCO, GRIS, GRIS_OSC = (255, 255, 255), (0xAA, 0xAA, 0xAA), (0x55, 0x55, 0x55)
AMARILLO, ROJO, VERDE, NARANJA = (0xFF, 0xAA, 0x00), (0xFF, 0, 0), (0, 0xFF, 0), (0xFF, 0x55, 0)

# Un perfil por juego de fuentes distinto (los 5X y 5 Plus miden como el 5; el 6 Pro, como el 6).
# reloj: (pantalla, tiene vectoriales, rótulo)
RELOJES = {
    "fenix5s": (218, False, "fēnix 5S · 218"),
    "fenix5": (240, False, "fēnix 5 / 5X / 5 Plus · 240"),
    "fenix6s": (240, False, "fēnix 6S · 240"),
    "fenix7s": (240, True, "fēnix 7S · 240"),
    "fenix6": (260, False, "fēnix 6 · 260"),
    "fenix7": (260, True, "fēnix 7 · 260"),
    "fenix6xpro": (280, False, "fēnix 6X · 280"),
    "fenix7xpro": (280, True, "fēnix 7X · 280"),
    "fenix843mm": (416, True, "fēnix 8 43 mm · 416"),
    "fenix847mm": (454, True, "fēnix 8 47 mm · 454"),
}
ANILLO_R, ANILLO_RI = 133, 128   # source/L.mc
HORA_Y, HORA_PX, HORA_MAX, SUB_Y, NOMBRE_Y, NOMBRE_Y_SUB = 36, 52, 50, 66, 58, 76
ARCO_PX, PASTILLA_H, PIE_Y, NUM_PX = 5, 38, 244, 40
# Caras de la v3.4 (P73): las TTF del propio SDK. El reloj no dibuja cada cara al tamaño pedido: medido en el
# simulador del 7X Pro (test fuentesV34), Noto Sans sale como la TTF (187 px frente a 190) y Bionic al 79 %.
FUENTES_SDK = Path.home() / "Library/Application Support/Garmin/ConnectIQ/Fonts"
NOTO, BIONIC = ("NotoSansSC-Medium-3.ttf", 0.99), ("Bionic_Bold_Number_Only.ttf", 0.79)
CIFRAS = set(" #%+-./0123456789:°")


def roboto(size, peso=700):
    f = ImageFont.truetype(str(FUENTE), max(1, round(size)))
    f.set_variation_by_axes([peso])
    return f


class Vectorial:
    """Graphics.getVectorFont de RobotoCondensedBold: el reloj mide su alto igual al tamaño."""

    def __init__(self, px):
        self.ttf = roboto(px)
        self.h = px

    def getlength(self, txt):
        return self.ttf.getlength(txt)

    def dibujar(self, d, xy, txt, fill, anchor):
        d.text(xy, txt, font=self.ttf, fill=fill, anchor=anchor)


class Cara(Vectorial):
    """Graphics.getVectorFont de otra cara: el alto que da el reloj es el tamaño pedido; el dibujo, la TTF a escala."""

    def __init__(self, cara, px):
        archivo, k = cara
        self.ttf = ImageFont.truetype(str(FUENTES_SDK / archivo), max(1, round(px * k)))
        self.h = px


class Sistema:
    """Una fuente de sistema con las métricas del reloj. Los anclajes son los de drawText:
    "ma" = centrado con y en lo alto de la celda; "mm" y "lm" = celda centrada en y."""

    def __init__(self, m, peso):
        self.h, self.asc, self.w = m["h"], m["asc"], m["w"]
        frase = "Calle de la Princesa"
        objetivo = sum(self.w.get(c, 0) for c in frase)
        size = self.h
        for _ in range(6):   # el tamaño de la Roboto que da el mismo ancho a la frase
            size *= objetivo / max(1.0, roboto(size, peso).getlength(frase))
        self.ttf = roboto(size, peso)

    def getlength(self, txt):
        return sum(self.w.get(c, self.w["n"]) for c in txt)

    def dibujar(self, d, xy, txt, fill, anchor):
        x, y = xy
        top = y if anchor[1] == "a" else y - self.h // 2
        w = self.getlength(txt)
        x0 = x - w / 2 if anchor[0] == "m" else x
        # Cada letra en su sitio medido: el ancho total es el del reloj.
        for c in txt:
            d.text((x0, top + self.asc), c, font=self.ttf, fill=fill, anchor="ls")
            x0 += self.w.get(c, self.w["n"])


# El reloj en uso (usar()): pantalla, escala y fuentes.
W = H = 280
S = 1.0
F = {}


def usar(reloj):
    global W, H, S, F
    W = H = RELOJES[reloj][0]
    S = H / 280.0
    m = METRICAS[reloj]
    sis = {k: Sistema(m[k], 400 if (k == "xtiny" and reloj.startswith("fenix5")) else 700)
           for k in ("xtiny", "tiny", "small", "medium", "large", "numberMild")}
    F = dict(sis)
    if RELOJES[reloj][1]:
        n = {px: Cara(NOTO, ly(px)) for px in (22, 24, 25, 28, 32)}
        F["grande"] = [n[32], n[28], n[25], n[22], sis["small"]]
        F["media"] = [n[28], n[25], n[22], sis["tiny"]]
        F["num"], F["letra"], F["hora"] = Cara(BIONIC, ly(NUM_PX)), n[24], Cara(BIONIC, ly(HORA_PX))
        F["dist"], F["nombre"] = Vectorial(ly(38)), n[25]
        F["ph"] = ly(PASTILLA_H)
    else:
        F["grande"] = [sis["large"], sis["medium"], sis["small"], sis["tiny"]]
        F["media"] = [sis["medium"], sis["small"], sis["tiny"]]
        F["num"] = sis["numberMild"] if sis["numberMild"].h <= ly(40) else sis["medium"]
        F["letra"], F["dist"], F["nombre"] = sis["small"], sis["large"], sis["small"]
        F["ph"] = max(ly(PASTILLA_H), F["num"].h + ly(4))
        # Fuentes.hora(): la más alta de sistema que no pase de L.y(HORA_MAX).
        cands = [sis[k] for k in ("numberMild", "large", "medium") if sis[k].h <= ly(HORA_MAX)]
        F["hora"] = max(cands, key=lambda f: f.h) if cands else sis["medium"]


def ly(v):
    """L.y(): una cota de la pantalla de 280 en la pantalla en uso (redondeo simétrico)."""
    r = v * S
    return int(r - 0.5) if r < 0 else int(r + 0.5)


def texto(d, xy, txt, f, fill, anchor="mm"):
    f.dibujar(d, xy, txt, fill, anchor)


TIPOS = dict(zip(*[iter("Rúa R. Avenida Av. Praza Pr. Praciña Prc. Travesa Tr. Travesía Tr. Camiño Cm. Calle C/ "
                        "Plaza Pl. Paseo P.º Rolda Rd. Ronda Rd. Estrada Estr. Carretera Ctra. Corredoira Corr. "
                        "Costa Cta. Glorieta Gl. Lugar Lg. Urbanización Urb. Polígono Pol. Pasaxe Psx. "
                        "Ruela Rla.".split())] * 2))


def corta(n):
    t, _, resto = n.partition(" ")
    return TIPOS[t] + " " + resto if t in TIPOS and resto else n


def ancho_r(y0, y1, r, margen):
    """Texto.anchoR(): ancho de la franja [y0, y1] dentro de un círculo de radio r centrado."""
    c = H // 2
    d = max(abs(y0 - c), abs(y1 - c))
    return 0 if d >= r else int(2 * math.sqrt(r * r - d * d)) - 2 * ly(margen)


def ancho_franja(y0, y1, margen):
    return ancho_r(y0, y1, W // 2, margen)


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
        a = f.h
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


def recortar(txt, f, w):
    while txt and f.getlength(txt) > w:
        txt = txt[:-2] + "…"
    return txt


def caja(d, nombre, fuentes, max_lineas, y0, y1, color):
    c = colocar(nombre, fuentes, max_lineas, y0, y1)
    if not c:
        f = F["tiny"]
        texto(d, (W // 2, (y0 + y1) // 2), recortar(corta(nombre), f, ancho_franja(y0, y1, 12)), f, color)
        return
    f, lineas, top, lh = c
    for i, ln in enumerate(lineas):
        texto(d, (W // 2, top + i * lh), ln, f, color, "ma")


def mayus(t):
    return t.upper()


def estado(d, e):
    """La hora en grande bajo el arco de calidad del GPS; si el dato es viejo, su edad debajo en ámbar, en lugar
    del barrio."""
    pen = ly(ARCO_PX)
    r = W // 2 - pen // 2 - 1
    d.arc((W // 2 - r - pen // 2, H // 2 - r - pen // 2, W // 2 + r + pen // 2, H // 2 + r + pen // 2), 225, 315,
          fill=e.get("punto", VERDE), width=pen)
    texto(d, (W // 2, ly(HORA_Y)), "23:41", F["hora"], BLANCO)
    if e.get("edad") and "detalle" not in e:
        linea(d, ly(SUB_Y), mayus(e["edad"]), AMARILLO)


def linea(d, y, txt, color, margen=10):
    """VistaCalle.linea(): una línea XTINY recortada al ancho de la franja (la franja crece con la fuente)."""
    f = F["xtiny"]
    med = max(ly(11), f.h // 2)
    texto(d, (W // 2, y), recortar(txt, f, ancho_franja(y - med, y + med, margen)), f, color)


def pie(d, y, txt, color):
    """VistaCalle.pie(): si la pantalla redonda lo corta, sube hasta caber."""
    f = F["xtiny"]
    while y > H // 2 and ancho_franja(y - f.h // 2, y + f.h // 2, 4) < f.getlength(txt):
        y -= 2
    texto(d, (W // 2, y), txt, f, color)


def exceso():
    """VistaCalle._ex: lo que la XTINY pasa de la proporcional (19 px en 280)."""
    return max(0, F["xtiny"].h - ly(19))


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
    ex = exceso()
    y0sub = ly(NOMBRE_Y_SUB) + ex // 2 if e.get("barrio") or e.get("edad") else ly(NOMBRE_Y)
    if "aviso" in e:
        titulo, color, sub = e["aviso"]
        texto(d, (W // 2, ly(112)), titulo, F["media"][0], color)
        linea(d, ly(152), sub, GRIS)
        if e.get("pie"):
            pie(d, ly(236), e["pie"], GRIS)
    elif "lugar" in e:
        linea(d, ly(SUB_Y), "SIN CALLE A 50 M", AMARILLO)
        caja(d, e["lugar"], F["media"], 2, ly(86), ly(146), col)
        linea(d, ly(164), mayus(e["sub"]), GRIS)
        pie(d, ly(236), e["pie"], GRIS)
    elif "detalle" in e:
        paso = max(ly(26), F["xtiny"].h)
        for i, ln in enumerate(e["detalle"]):
            texto(d, (W // 2, ly(SUB_Y + 2) + i * paso), ln, F["xtiny"], BLANCO)
    elif "lista" in e:
        texto(d, (W // 2, ly(62)), "Anotaciones", F["small"], BLANCO)
        for i, (et, sub) in enumerate(e["lista"]):
            y = ly(96 + i * 58)
            if i == 0:
                d.rounded_rectangle((ly(18), y - ly(6), W - ly(18), y + ly(46)), ly(8), outline=GRIS_OSC)
            texto(d, (W // 2, y + ly(10)), recortar(corta(et), F["tiny"], W - ly(44)), F["tiny"], BLANCO)
            texto(d, (W // 2, y + ly(34)), recortar(sub, F["xtiny"], W - ly(44)), F["xtiny"], GRIS)
    elif "calle2" in e and not e.get("cruce"):
        top = ly(NOMBRE_Y_SUB) + ex // 2 if e.get("edad") else ly(NOMBRE_Y)
        caja(d, e["calle1"], F["media"], 2, top, ly(116), col)
        numc = GRIS if e.get("edad") else AMARILLO
        if e.get("num1"):
            texto(d, (W // 2, ly(117)), e["num1"], F["xtiny"], numc, "ma")
        d.line((W // 2 - ly(90), ly(146), W // 2 + ly(90), ly(146)), fill=GRIS_OSC)
        caja(d, e["calle2"], F["media"], 2, ly(152), ly(214) - ex, col)
        if e.get("num2"):
            texto(d, (W // 2, ly(215) - ex), e["num2"], F["xtiny"], numc, "ma")
        pie(d, ly(252), "DOS CALLES", AMARILLO)
    else:
        una(d, e, col, ex)
    if e.get("anotado"):
        txt, color = e["anotado"]
        x = ly(24)
        d.rounded_rectangle((x, ly(108), W - x, ly(108) + ly(64)), ly(12), fill=(0, 0, 0), outline=color, width=ly(3))
        texto(d, (W // 2, ly(140)), recortar(txt, F["small"], W - ly(64)), F["small"], BLANCO)
    return redondo(img)


def franja_una(e, ex):
    """VistaCalle.franjaUna(): de abajo arriba, el pie con su rótulo, la pastilla y el nombre."""
    paso = ly(19) + ex
    t = e.get("tramo")
    rot = l1 = l2 = 0
    if e.get("cruce"):
        l1 = ly(PIE_Y) - paso // 2
        rot = l1 - paso
    elif t:
        l2 = ly(PIE_Y) if len(t) == 2 else 0
        l1 = l2 - paso if len(t) == 2 else ly(PIE_Y) - paso // 2
        rot = l1 - paso
    ph = F["ph"]
    pc = rot - paso // 2 - ly(4) - ph // 2 if rot else ly(196)
    y1 = pc - ph // 2 - ly(4) if e.get("num1") else (rot - paso // 2 - ly(4) if rot else ly(200))
    return y1, pc, rot, l1, l2


def pastilla(d, cy, num, viejo):
    """VistaCalle.pastilla(): cifras en Bionic, la letra en la de nombres; aproximado («~»), solo el borde."""
    aprox = num.startswith("~")
    num = num.split()[-1]
    k = 0
    while k < len(num) and num[k] in CIFRAS:
        k += 1
    a, b = num[:k], num[k:]
    wa = F["num"].getlength(a) if a else 0
    wb = F["letra"].getlength(b) if b else 0
    w, pad, ph = wa + wb, ly(14), F["ph"]
    caja_ = (W // 2 - w / 2 - pad, cy - ph // 2, W // 2 + w / 2 + pad, cy + ph // 2)
    if aprox:
        tinta = GRIS if viejo else AMARILLO
        d.rounded_rectangle(caja_, ly(8), outline=tinta, width=ly(3))
    else:
        d.rounded_rectangle(caja_, ly(8), fill=GRIS_OSC if viejo else AMARILLO)
        tinta = GRIS if viejo else (0, 0, 0)
    x = W // 2 - w / 2
    if a:
        texto(d, (x, cy), a, F["num"], tinta, "lm")
    if b:
        texto(d, (x + wa, cy), b, F["letra"], tinta, "lm")


def una(d, e, col, ex):
    viejo = bool(e.get("edad"))
    if e.get("barrio") and not viejo:
        linea(d, ly(SUB_Y), mayus(e["barrio"]), GRIS)
    top = ly(NOMBRE_Y_SUB) + ex // 2 if e.get("barrio") or viejo else ly(NOMBRE_Y)
    y1, pc, rot, l1, l2 = franja_una(e, ex)
    caja(d, e["calle1"], F["grande"], 3, top, y1, col)
    if e.get("num1"):
        pastilla(d, pc, e["num1"], viejo)
    ambar = GRIS_OSC if viejo else AMARILLO
    t = e.get("tramo")
    if e.get("cruce"):
        linea(d, rot, "ESQUINA", ambar)
        linea(d, l1, corta(e["cruce"]), col)
    elif t:
        linea(d, rot, "ENTRE" if len(t) == 2 else "CERCA DE", ambar)
        linea(d, l1, corta(t[0]), GRIS)
        if len(t) == 2:
            linea(d, l2, corta(t[1]), GRIS)


def redondo(img):
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, W - 1, H - 1), fill=255)
    fondo = Image.new("RGB", (W, H), (40, 40, 40))
    fondo.paste(img, (0, 0), mask)
    return fondo


def flecha(d, cy, ang, color, k=None):
    c, s_ = math.cos(ang), math.sin(ang)
    k = S if k is None else k
    forma = [(x * k, y * k) for x, y in ((0, -40), (27, 22), (0, 9), (-27, 22))]
    pts = [(W // 2 + x * c - y * s_, cy + x * s_ + y * c) for x, y in forma]
    d.polygon(pts, fill=color, outline=BLANCO, width=ly(2))


def ir(e):
    """La guía de la v3, antes del anillo (solo para la comparación de --brujula)."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    nombre, dirc, tipo, dist, ang, card, i, n = e["ir"]
    color = (0xFF, 0, 0) if tipo.startswith("HOSPITAL") else (0, 0x55, 0xFF)
    texto(d, (W // 2, ly(24)), f"23:41   {i}/{n}", F["xtiny"], GRIS)
    texto(d, (W // 2, ly(48)), tipo, F["xtiny"], color)
    f = F["nombre"]
    lineas = partir(nombre, f, [ancho_franja(ly(60), ly(108), 10)] * 2) or [nombre[:24] + "…"]
    for k, ln in enumerate(lineas):
        texto(d, (W // 2, ly(84) + (k - (len(lineas) - 1) / 2) * f.h), ln, f, BLANCO)
    flecha(d, ly(152), ang, color)
    texto(d, (W // 2, ly(208)), dist, F["dist"], BLANCO)
    linea(d, ly(238), corta(dirc), GRIS)
    texto(d, (W // 2, ly(258)), f"línea recta · {card}", F["xtiny"], GRIS_OSC)
    return redondo(img)


# Anillo de brújula (v3.1, 2026-10-24; source/Anillo.mc; referencia: Pin Point — Location and Share). Ocupa la franja
# exterior: el texto vive dentro de ANILLO_RI y el anillo gira con el rumbo del reloj.
AZUL = (0, 0x55, 0xFF)
OSCURO = {ROJO: (0xAA, 0, 0), AZUL: (0, 0, 0xAA), VERDE: (0, 0xAA, 0)}   # el círculo, en el tono oscuro del destino


def punto(a, r):
    """Punto a r px del centro en el ángulo a (radianes, 0 = arriba, horario)."""
    return (W / 2 + r * math.sin(a), H / 2 - r * math.cos(a))


def anillo(d, rumbo, destino, color):
    """Círculo fino (tono oscuro del destino), marcas cada 10° (cada 30°, más largas), triángulos en los cardinales
    (N rojo y mayor) y el destino como una bola de su color. rumbo y destino en grados; el anillo gira con el rumbo."""
    c, r = W / 2, ly(ANILLO_R)
    d.ellipse((c - r, c - r, c + r, c + r), outline=OSCURO.get(color, GRIS_OSC), width=1)
    for k in range(36):
        if k % 9 == 0:
            continue
        a = math.radians(k * 10 - rumbo)
        if k % 3 == 0:
            d.line([punto(a, r - ly(4)), punto(a, r + ly(5))], fill=GRIS, width=ly(2))
        else:
            d.line([punto(a, r - ly(2)), punto(a, r + ly(2))], fill=GRIS_OSC, width=ly(1))
    for k in range(4):
        a = math.radians(k * 90 - rumbo)
        punta, base, medio, col = (r - ly(10), r + ly(6), ly(8), ROJO) if k == 0 else (r - ly(5), r + ly(5), ly(5), GRIS)
        bx, by = punto(a, base)
        tx, ty = math.cos(a), math.sin(a)          # tangente al anillo
        d.polygon([punto(a, punta), (bx + medio * tx, by + medio * ty), (bx - medio * tx, by - medio * ty)], fill=col)
    if destino is not None:
        x, y = punto(math.radians(destino - rumbo), r)
        b = ly(7)
        d.ellipse((x - b, y - b, x + b, y + b), fill=color, outline=BLANCO, width=ly(2))


def linea_in(d, y, txt, color):
    """VistaIr.linea(): XTINY recortada al ancho que deja el anillo."""
    f = F["xtiny"]
    med = max(ly(9), f.h // 2)
    texto(d, (W // 2, y), recortar(txt, f, ancho_r(y - med, y + med, ly(ANILLO_RI), 4)), f, color)


def ir_anillo(e):
    """VistaIr con el anillo."""
    a = e["anillo"]
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    llegado = a.get("llegado")
    anillo(d, a["rumbo"], None if llegado else a["destino"], a["color"])
    y_hora, y_tipo, y_nombre, y_flecha, y_dist, y_dir, y_pie, k_flecha, n_lineas = alturas_ir()
    texto(d, (W // 2, y_hora), f"23:41  {a['i']}/{a['n']}", F["xtiny"], GRIS)
    linea_in(d, y_tipo, a["tipo"], a["color"])
    # El nombre: fitTextToArea en el ancho de su franja y dos líneas de alto.
    f = F["nombre"]
    aw = ancho_r(y_nombre - n_lineas * f.h // 2, y_nombre + n_lineas * f.h // 2, ly(ANILLO_RI), 4)
    nombre = corta(a["nombre"])
    lineas = partir(nombre, f, [aw] * n_lineas) or [recortar(nombre, f, aw)]

    for k, ln in enumerate(lineas):
        texto(d, (W // 2, y_nombre + (k - (len(lineas) - 1) / 2) * f.h), ln, f, BLANCO)
    if llegado:
        texto(d, (W // 2, y_flecha), "HA LLEGADO", F["medium"], VERDE)
    else:
        flecha(d, y_flecha, math.radians(a["destino"] - a["rumbo"]), a["color"], k_flecha)
    texto(d, (W // 2, y_dist), a["dist"], F["dist"], BLANCO)
    linea_in(d, y_dir, corta(a["dir"]), GRIS)
    card = "N NE E SE S SO O NO".split()[round((a["destino"] or 0) / 45) % 8]
    hx = F["xtiny"].h
    pw = ancho_r(y_pie - hx // 2, y_pie + hx // 2, ly(ANILLO_RI), 4)
    pies = ["línea recta · " + card, "recta · " + card, card]
    k = 0
    while k < len(pies) - 1 and F["xtiny"].getlength(pies[k]) > pw:
        k += 1
    texto(d, (W // 2, y_pie), pies[k], F["xtiny"], GRIS_OSC)
    return redondo(img)


def alturas_ir():
    """VistaIr.onLayout(): las alturas de la guía apiladas por el alto real de las fuentes."""
    hx, nh, dh = F["xtiny"].h, F["nombre"].h, F["dist"].h
    hora = ly(30)
    tipo = max(ly(52), hora + hx)
    nombre_top = tipo + hx // 2
    pie_ = ly(245)
    dir_ = min(ly(226), pie_ - hx)
    dist = min(ly(200), dir_ - hx // 2 - dh // 2 + ly(6))
    abajo = dist - dh // 2
    lineas = 2
    k = (abajo - nombre_top - 2 * nh - 4) / 62.0
    if k < 0.7 * S:
        lineas = 1
        k = (abajo - nombre_top - nh - 4) / 62.0
    arriba = nombre_top + lineas * nh
    k = min(k, S)
    return hora, tipo, nombre_top + lineas * nh // 2, (arriba + abajo) // 2 + int(9 * k), dist, dir_, pie_, k, lineas



def acciones(e):
    """Menú de una anotación: «Ir aquí» y «Borrar» (Menu2: título arriba, la opción con foco enmarcada)."""
    titulo, items = e["acciones"]
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    linea(d, ly(62), corta(titulo), BLANCO)
    for i, (et, sub) in enumerate(items):
        y = ly(100 + i * 64)
        if i == 0:
            d.rounded_rectangle((ly(18), y - ly(8), W - ly(18), y + ly(48)), ly(8), outline=GRIS_OSC)
        texto(d, (W // 2, y + ly(10)), et, F["small"], BLANCO)
        texto(d, (W // 2, y + ly(34)), sub, F["xtiny"], GRIS)
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
    ("Sin calle, sin lugar", dict(aviso=("SIN CALLE", BLANCO, "PARROQUIA DE CALO"), pie="29T 531794 4739311")),
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


# CALLE Galicia: lo que dicen los datos reales (tools/ref.py --region galicia) en sitios públicos, 2026-10-25.
ESCENAS_GALICIA = [
    ("Santiago: Rúa do Franco", FRANCO),
    ("A Coruña: Rúa Real", dict(calle1="Rúa Real", num1="nº 26", barrio="A Pescaría",
                                tramo=("Rúa Alcalde Canuto Berea", "Rúa Torreiro"))),
    ("Aldea y parroquia", dict(lugar="O Carrio", sub="parroquia de Camposancos", pie="29T 569563 4733404")),
    # Desde la Rúa dos Campos (Pontevedra): el de urgencias más cercano está a 1,5 km, rumbo 145°. (El Lucus
    # Augusti de Lugo no cabe entero en la línea: el escaparate pide un nombre que se lea.)
    ("Pontevedra: hospital", dict(anillo=dict(nombre="Hospital Montecelo", dir="Estrada Mourente",
                                              tipo="HOSPITAL · URGENCIAS", color=ROJO, dist="1,5 km", rumbo=0,
                                              destino=145, i=1, n=8))),
]
# Calles Murcia: lo que dicen los datos reales (tools/ref.py --region murcia) en sitios públicos, 2026-10-26.
ESCENAS_MURCIA = [
    ("Murcia: Calle Trapería", dict(calle1="Calle Trapería", num1="nº 19", tramo=("Calle Andrés Baquero", "Calle Platería"))),
    ("Cartagena: Calle Mayor", dict(calle1="Calle Mayor", num1="nº 14", barrio="Casco Antiguo",
                                    tramo=("Calle Medieras", "Calle Andino"))),
    ("Pedanía y término", dict(lugar="El Moral", sub="término de Caravaca de la Cruz", pie="30S 569078 4205422")),
    # Desde la calle San José (Yecla, centro): el de urgencias más cercano está a 660 m, rumbo 73°. (El Morales
    # Meseguer, desde la Gran Vía de Murcia, no cabe: «Hospital General Universitario…» se corta.)
    ("Yecla: hospital", dict(anillo=dict(nombre="Hospital Virgen del Castillo", dir="Avenida de la Feria",
                                         tipo="HOSPITAL · URGENCIAS", color=ROJO, dist="660 m", rumbo=0, destino=73,
                                         i=1, n=8))),
]
FICHAS = {
    "madrid": ("", ESCENARIOS, None, (("Street, door number and the streets on each side", "Madrid: Gran Vía"),
                                                   ("Neighbourhood and district, offline", "Madrid: barrio · distrito"),
                                                   ("Nearest hospital: arrow and distance", "Ir: hospital"),
                                                   ("Nearest police station", "Ir: comisaría"))),
    "galicia": ("galicia", ESCENAS_GALICIA, None,
                (("Street, door number and the streets on each side", "Santiago: Rúa do Franco"),
                 ("Cities and towns: street, number and neighbourhood", "A Coruña: Rúa Real"),
                 ("Outside town: village and parish", "Aldea y parroquia"),
                 ("Nearest hospital with A&E: arrow and distance", "Pontevedra: hospital"))),
    "murcia": ("murcia", ESCENAS_MURCIA, None,
               (("Street, door number and the streets on each side", "Murcia: Calle Trapería"),
                ("Cities and towns: street, number and neighbourhood", "Cartagena: Calle Mayor"),
                ("Outside town: hamlet and municipality", "Pedanía y término"),
                ("Nearest hospital with A&E: arrow and distance", "Yecla: hospital"))),
}


def ficha(app="madrid"):
    """Imágenes de la ficha de la Connect IQ Store en docs/tienda/ (Madrid) o docs/tienda/<app>/: portada de 500×500
    y cuatro pantallas a doble tamaño (560×560) con su rótulo, en el 7X Pro. Solo sitios públicos."""
    usar("fenix7xpro")
    sub, escenas, portada_de, pantallas = FICHAS[app]
    out = ROOT / "docs" / "tienda" / sub
    out.mkdir(parents=True, exist_ok=True)
    esc = dict(escenas)
    if portada_de:   # si no, la portada es la carátula de tools/caratula.py --instalar (Galicia y Madrid)
        portada = Image.new("RGB", (500, 500), (24, 24, 24))
        portada.paste(render(esc[portada_de]).resize((440, 440), Image.LANCZOS), (30, 30))
        portada.save(out / "portada_500.png")
    for k, (titulo, nombre) in enumerate(pantallas, 1):
        hoja = Image.new("RGB", (600, 660), (24, 24, 24))
        hoja.paste(render(esc[nombre]).resize((560, 560), Image.LANCZOS), (20, 20))
        ImageDraw.Draw(hoja).text((300, 620), titulo, font=roboto(26, 600), fill=GRIS, anchor="mm")
        hoja.save(out / f"ficha_{k}.png")
    print(f"escrito {out}/ (portada_500.png, ficha_1..4.png)")


def hoja(reloj, escenarios, cols, nombre):
    """Todos los escenarios en un reloj, a su tamaño real."""
    usar(reloj)
    rot = roboto(22, 500)
    filas = math.ceil(len(escenarios) / cols)
    img = Image.new("RGB", (cols * (W + 20) + 20, filas * (H + 50) + 60), (24, 24, 24))
    d = ImageDraw.Draw(img)
    d.text((20, 30), RELOJES[reloj][2], font=roboto(26, 600), fill=BLANCO, anchor="lm")
    for i, (titulo, e) in enumerate(escenarios):
        x, y = 20 + (i % cols) * (W + 20), 60 + (i // cols) * (H + 50)
        img.paste(render(e), (x, y))
        d.text((x + W // 2, y + H + 18), titulo, font=rot, fill=GRIS, anchor="mm")
    out = ROOT / "tools" / "out" / nombre
    out.parent.mkdir(exist_ok=True)
    img.save(out)
    print(f"escrito {out}")


# La comparativa: los escenarios que más aprietan la pantalla, en todos los relojes y a su tamaño real.
COMPARATIVA = ["Tramo y barrio", "Madrid: barrio · distrito", "Dato viejo (edad)", "Muy largo", "Esquina", "Dos calles",
               "Sin calle: lugar", "Fuera de zona", "START: anotado", "Detalle", "Ir: hospital", "Ir: llegada"]


def comparativa():
    esc = dict(ESCENARIOS)
    relojes = list(RELOJES)
    anchos = [RELOJES[r][0] for r in relojes]
    alto_fila = max(anchos) + 30
    img = Image.new("RGB", (220 + sum(anchos) + 20 * len(anchos), 50 + len(COMPARATIVA) * alto_fila), (24, 24, 24))
    d = ImageDraw.Draw(img)
    rot = roboto(20, 600)
    x = 220
    for r, a in zip(relojes, anchos):
        d.text((x + a // 2, 25), RELOJES[r][2], font=rot, fill=BLANCO, anchor="mm")
        x += a + 20
    for fi, nombre in enumerate(COMPARATIVA):
        y = 50 + fi * alto_fila
        d.text((20, y + alto_fila // 2), nombre, font=rot, fill=GRIS, anchor="lm")
        x = 220
        for r, a in zip(relojes, anchos):
            usar(r)
            img.paste(render(esc[nombre]), (x, y + (max(anchos) - a) // 2))
            x += a + 20
    out = ROOT / "tools" / "out" / "pantallas.png"
    img.save(out)
    print(f"escrito {out}")


def main():
    import sys
    args = sys.argv[1:]
    if "--ficha" in args:
        i = args.index("--ficha")
        return ficha(args[i + 1] if i + 1 < len(args) and not args[i + 1].startswith("--") else "madrid")
    if "--brujula" in args:
        return hoja("fenix7xpro", ESCENARIOS_BRUJULA, 3, "mockups-brujula.png")
    if "--todos" in args:
        for r in RELOJES:
            hoja(r, ESCENARIOS, 5, f"mockups-{r}.png")
        return comparativa()
    reloj = args[args.index("--reloj") + 1] if "--reloj" in args else "fenix7xpro"
    if reloj not in RELOJES:
        sys.exit(f"reloj desconocido: {reloj} (hay: {', '.join(RELOJES)})")
    hoja(reloj, ESCENARIOS, 4, "mockups.png" if reloj == "fenix7xpro" else f"mockups-{reloj}.png")


if __name__ == "__main__":
    main()
