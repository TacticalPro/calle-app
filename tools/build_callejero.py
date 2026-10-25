#!/usr/bin/env python3
"""Callejero de CALLE: de OpenStreetMap a teselas que el reloj carga de una en una.

    build_callejero.py --region santiago            usa la caché de Overpass si existe
    build_callejero.py --region santiago --refresh  vuelve a descargar

Solo biblioteca estándar (más curl para la descarga). Escribe:
    resources-gen/jsonData/teselas.xml + t/t<idx>.json   una tesela por celda con calles
    resources-gen/jsonData/zonas.xml + z/z<idx>.json     una zona (parroquia, lugar, barrio) por celda de ZONA m
    source-gen/Callejero.mc                              constantes, índices de recursos, sufijos
    tools/out/meta-<region>.json                         lo mismo para tools/ref.py
    tools/out/geom-<region>.json                         trozos de calle, portales, parroquias y lugares enteros
                                                         (sin teselar), para la fuerza bruta de ref.py
    tools/out/informe-<region>.txt                       cifras, emparejamiento de portales, tramos, peso por tesela, mapas

Portales del Catastro: si la región tiene caja "catastro", sus direcciones (WFS INSPIRE, en caché como
Overpass) rellenan los números que OSM no tiene; el nombre lo pone siempre la vía de OSM.

Formato de una tesela (FORMATO 3), una lista plana para no pagar objetos de Monkey C:
    [FORMATO, N, R, V, P, H]
    N  nombres de calle, con los de las calles que cruzan aunque no tengan tirada aquí;
       el índice es el id local (≤ 1023)
    R  4 números por tirada: h = nVert | calle<<12 | clase<<22 | area<<24, bbMin = x|y<<12, bbMax,
       tramo = (A+1) | (B+1)<<12, las calles que cruzan en cada extremo de su trozo (0 = ninguna)
    V  vértices de todas las tiradas seguidos, x|y<<12, en metros enteros desde la esquina SO
       de la tesela con su margen (0..TESELA+2·BUF, < 4096)
    P  portales x|y<<12, ordenados por calle (la calle va en H)
    H  paralelo a P: número | sufijo<<12 | calle<<21 (número ≤ 4095; sufijo indexa Callejero.SUF, < 512)
El FORMATO 3 (2026-10-24) amplía el 2 para las teselas grandes del fēnix 6X: 1.023 calles por tesela
(antes 255) y coordenadas de 12 bits (teselas de hasta 3,9 km; antes 1,9).

Variantes del nombre: OSM etiqueta a veces trozos de una misma calle con y sin partículas o con el tipo en
otra lengua («Calle de Alcalá» / «Calle Alcalá»; en Madrid, 368 pares que se tocan, 2026-10-24). Sin
unificar, el cambio de nombre parece un cruce (tramo falso) y el reloj puede dar «DOS CALLES» con la misma
calle. unificar_variantes() junta las vías de la misma clave que se tocan (≤ UNIR_M, en cadena) y les pone
el nombre con más longitud del grupo; las homónimas lejanas (otro pueblo) no se tocan.

Tramos: cada vía se corta en sus intersecciones (nodo OSM compartido con otra vía lineal de
nombre distinto, calzada o peatonal; sendas y áreas no cruzan). Un extremo que no es
intersección sigue la calle por nodos de grado 2 hasta la siguiente; en una bifurcación o un
fondo de saco no hay cruce. Cada trozo se simplifica por separado, conservando sus extremos.

Formato de una zona (celda de ZONA m), [FORMATO, N, RASTER, L, LN]:
    N       parroquias de la zona primero, luego los lugares
    RASTER  RN×RN celdas de RCEL m, fila a fila desde el sur, 4 por número (8 bits cada una):
            índice en N de la parroquia que contiene el centro de la celda, +1 (0 = ninguna)
    L       lugares de la zona y ZMARGEN m alrededor, x | y<<13 | tipo<<26, en metros desde la
            esquina SO de la zona menos ZMARGEN; tipo: bit 0 = lugar poblado, bit 1 = barrio,
            bit 2 = paraje (solo cuenta como lugar si no hay poblado a LUGAR_R)
    LN      paralelo a L: índice en N del nombre

Garantía (la comprueba ref.py por fuerza bruta): para un punto a menos de BUF−MAXD de la
tesela, toda vía o portal a menos de MAXD de él está en la tesela. Los recortes caen en el
borde del margen, a ≥ MAXD del punto, así que no alteran ninguna distancia que importe.
Para las zonas: todo lugar a menos de ZMARGEN (≥ LUGAR_R ≥ BARRIO_R/BARRIO_FRAC) de un punto de la
zona está en ella.
"""
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = TOOLS / "out"
CACHE = TOOLS / "cache"

# Variantes de los datos. «normal»: teselas de 500 m (fēnix 7X Pro, sin tope de recursos). «6x»: la
# compacta del fēnix 6X (API 3.4), cuya máquina virtual no admite más de 254 miembros por módulo, y
# Rez.JsonData es uno: todas las teselas, zonas y puntos de todas sus regiones tienen que caber en 254.
# Por eso usa teselas y zonas mayores (las fija "compacta" de cada región) y solo las regiones que la
# tengan. Tiene 1,25 MB de memoria (el 7X Pro, 768 KB): las teselas grandes caben.
VARIANTE = "normal"
TOPE_RECURSOS_6X = 250     # el compilador corta en 254; margen para cadenas o iconos que se añadan


def sufijo():
    return "" if VARIANTE == "normal" else "-" + VARIANTE


def res_gen():
    return ROOT / ("resources-gen" + sufijo())


def src_gen():
    return ROOT / ("source-gen" + sufijo())

FORMATO = 3
TESELA = 500        # m (la variante compacta del fēnix 6X la cambia por región: VARIANTE)
BUF = 75            # m de margen alrededor de cada tesela
MAXD = 50           # m: más lejos no hay "calle cercana"
PORTAL_R = 40       # m: radio para dar número de portal
PORTAL_ASOC = 60    # m: un portal solo se asocia a una calle que pase a esta distancia
DP_TOL = 0.75       # m: simplificación de Douglas-Peucker
# Peso por metro al elegir el nombre de una calle con variantes: manda el de la calzada. Las aceras y las
# áreas peatonales llevan a menudo otra variante, y el perímetro de un área cuenta doble (en Sol, el área
# «Calle Arenal» de 811 m le ganaba a la calle «Calle del Arenal» de 480 m, 2026-10-24).
PESO_NOMBRE = {"calzada": 1.0, "peatonal": 0.5, "senda": 0.1, "area": 0.05}
UNIR_M = 20.0       # m: dos vías de la misma clave (p. ej. «Calle de Alcalá» y «Calle Alcalá») a esta distancia
                    # son la misma calle mal etiquetada: unificar_variantes() les pone un solo nombre
PEN = [0, 0, 4]     # m de penalización por clase: calzada, peatonal, senda
MAX_VERT_RUN = 4095
MAX_NOMBRES = 1023
MAX_SUFIJOS = 511         # Madrid junta 423 (letras del Ayuntamiento y rangos y restos de OSM)
assert BUF >= MAXD + 25, "el margen debe cubrir MAXD más 25 m de holgura"

ZONA = 2000         # m: celda de zonas
RCEL = 50           # m: celda del raster de parroquias
RN = ZONA // RCEL   # celdas por lado
LUGAR_R = 1500      # m: el lugar más cercano, si está a menos de esto
BARRIO_R = 800      # m: el barrio más cercano, si está a menos de esto…
BARRIO_FRAC = 0.8   # …y a menos de esta fracción de la distancia al segundo: en la frontera no se adivina
ZMARGEN = LUGAR_R   # m de margen de lugares alrededor de la zona
assert RN * RN % 4 == 0 and ZMARGEN >= max(LUGAR_R, BARRIO_R / BARRIO_FRAC) and ZONA + 2 * ZMARGEN < 1 << 13
# El lugar es el poblado más cercano; un paraje (locality: montes, cotos, agras) solo si no hay
# poblado a LUGAR_R. En la radio se da la aldea, no el nombre del monte (2026-10-23).
LUGAR_TIPOS = {"hamlet", "village", "isolated_dwelling", "neighbourhood"}
PARAJE_TIPOS = {"locality"}
BARRIO_TIPOS = {"suburb", "quarter", "neighbourhood"}

UA = "calle-fenix (callejero sin conexión para Connect IQ)"
SERVIDORES = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]

DESCARTE = {"construction", "proposed", "abandoned", "disused", "razed", "platform", "corridor", "elevator",
            "bus_stop", "rest_area", "services", "raceway", "escape", "emergency_bay", "planned", "no"}
PEATONAL = {"pedestrian"}
SENDA = {"footway", "path", "steps", "cycleway", "bridleway"}
VIA_RAPIDA = re.compile(r"^(motorway|trunk)(_link)?$")
CON_REF = re.compile(r"^(motorway|trunk|primary|secondary|tertiary)(_link)?$")

# Sinónimos del tipo de vía (primera palabra), gallego, castellano y abreviaturas de Catastro.
TIPOS = {
    "rua": "r rua ru calle c cl cll",
    "avenida": "av avda avd avenida",
    "praza": "pr praza plaza pza pl pz prza",
    "praciña": "pracina plazuela",
    "travesa": "trav travesia travesa tr tv",
    "camino": "camino camiño camino cm cno cmno",
    "paseo": "ps paseo pso po",
    "ronda": "rda ronda rolda rd",
    "lugar": "lg lugar",
    "estrada": "ctra carretera estrada cr est",
    "glorieta": "gl glorieta rotonda",
    "costa": "costa cuesta cta",
    "calexon": "calexon callejon cjon",
    "pasaxe": "pasaxe pasaje psje",
    "urbanizacion": "urb urbanizacion",
    "poligono": "pol poligono",
    "carreiro": "carreiro sendeiro",
}
SINON = {}
for canon, alias in TIPOS.items():
    for a in alias.split():
        SINON[unicodedata.normalize("NFKD", a).encode("ascii", "ignore").decode()] = canon
CANON = set(TIPOS)
PARTICULAS = {"de", "do", "da", "dos", "das", "del", "la", "las", "los", "el", "o", "a", "os", "as", "e", "y", "d", "en"}


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def clave(nombre):
    """Clave para casar addr:street con el nombre de la vía."""
    s = re.sub(r"[^a-z0-9]+", " ", sin_tildes(nombre).lower()).split()
    if not s:
        return ""
    if s[0] in SINON:
        s[0] = SINON[s[0]]
    return " ".join([s[0]] + [t for t in s[1:] if t not in PARTICULAS])


def clave_unir(nombre):
    """Clave de unificar_variantes(): la de clave() pero sin quitar las partículas de una letra, que en
    los polígonos son nombres de calle («Rúa "E"» y «Rúa "D"» no son la misma)."""
    s = re.sub(r"[^a-z0-9]+", " ", sin_tildes(nombre).lower()).split()
    if not s:
        return ""
    if s[0] in SINON:
        s[0] = SINON[s[0]]
    return " ".join([s[0]] + [t for t in s[1:] if t not in PARTICULAS or len(t) == 1])


def clave_sin_tipo(k):
    t = k.split()
    return " ".join(t[1:]) if len(t) > 1 and t[0] in CANON else k


# ---------------------------------------------------------------- geometría


class Proy:
    """Equirectangular en metros desde la esquina SO de la región. El reloj usa la misma."""

    def __init__(self, bbox):
        s, w, n, e = bbox
        self.lat_min, self.lon_min = s, w
        phi = math.radians((s + n) / 2)
        self.ky = 111132.92 - 559.82 * math.cos(2 * phi) + 1.175 * math.cos(4 * phi) - 0.0023 * math.cos(6 * phi)
        self.kx = 111412.84 * math.cos(phi) - 93.5 * math.cos(3 * phi) + 0.118 * math.cos(5 * phi)
        self.ancho = (e - w) * self.kx
        self.alto = (n - s) * self.ky

    def xy(self, lat, lon):
        return ((lon - self.lon_min) * self.kx, (lat - self.lat_min) * self.ky)

    def latlon(self, x, y):
        return (self.lat_min + y / self.ky, self.lon_min + x / self.kx)


def dist_seg2(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    qx, qy = ax + t * dx, ay + t * dy
    return (px - qx) ** 2 + (py - qy) ** 2, qx, qy


def dist_polilinea(px, py, pts):
    """(distancia, punto más cercano) de p a la polilínea."""
    mejor = (math.inf, None, None)
    if len(pts) == 1:
        return math.hypot(px - pts[0][0], py - pts[0][1]), pts[0][0], pts[0][1]
    for i in range(len(pts) - 1):
        d2, qx, qy = dist_seg2(px, py, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        if d2 < mejor[0]:
            mejor = (d2, qx, qy)
    return math.sqrt(mejor[0]), mejor[1], mejor[2]


def dentro(px, py, anillo):
    c = False
    n = len(anillo)
    j = n - 1
    for i in range(n):
        xi, yi = anillo[i]
        xj, yj = anillo[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def douglas_peucker(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    pila = [(0, len(pts) - 1)]
    t2 = tol * tol
    while pila:
        i, j = pila.pop()
        dmax, k = 0.0, -1
        for m in range(i + 1, j):
            d2 = dist_seg2(pts[m][0], pts[m][1], pts[i][0], pts[i][1], pts[j][0], pts[j][1])[0]
            if d2 > dmax:
                dmax, k = d2, m
        if dmax > t2:
            keep[k] = True
            pila += [(i, k), (k, j)]
    return [p for p, kp in zip(pts, keep) if kp]


def liang_barsky(ax, ay, bx, by, xmin, ymin, xmax, ymax):
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, ax - xmin), (dx, xmax - ax), (-dy, ay - ymin), (dy, ymax - ay)):
        if p == 0:
            if q < 0:
                return None
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return None
                t0 = max(t0, r)
            else:
                if r < t0:
                    return None
                t1 = min(t1, r)
    return t0, t1


def sutherland_hodgman(anillo, xmin, ymin, xmax, ymax):
    def recorta(pts, dentro_f, corte):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            da, db = dentro_f(a), dentro_f(b)
            if db:
                if not da:
                    out.append(corte(a, b))
                out.append(b)
            elif da:
                out.append(corte(a, b))
        return out

    def cx(v):
        return lambda a, b: (v, a[1] + (b[1] - a[1]) * (v - a[0]) / (b[0] - a[0]))

    def cy(v):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (v - a[1]) / (b[1] - a[1]), v)

    pts = anillo[:-1] if anillo[0] == anillo[-1] else anillo[:]
    for f, c in ((lambda p: p[0] >= xmin, cx(xmin)), (lambda p: p[0] <= xmax, cx(xmax)),
                 (lambda p: p[1] >= ymin, cy(ymin)), (lambda p: p[1] <= ymax, cy(ymax))):
        pts = recorta(pts, f, c)
        if not pts:
            return []
    return pts


# ---------------------------------------------------------------- descarga


def cabecera(bbox, grande):
    """Madrid: más tiempo en el servidor (las calles van además en partes, descargar_por_partes). Pedir más
    memoria (maxsize) hace que Overpass la rechace con 502/504 cuando está cargado (2026-10-24). Santiago
    conserva la cabecera de siempre (la caché se indexa por el texto de la consulta)."""
    s, w, n, e = bbox
    return (f"[out:json][timeout:900][bbox:{s},{w},{n},{e}];" if grande
            else f"[out:json][timeout:300][bbox:{s},{w},{n},{e}];")


def consulta(bbox, grande=False):
    return cabecera(bbox, grande) + """
(
  way["highway"]["name"];
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary)(_link)?$"]["ref"];
  way["place"="square"];
  relation["place"="square"];
  relation["type"="multipolygon"]["highway"="pedestrian"];
  nwr["addr:housenumber"];
  node["entrance"];
);
out geom;"""


def consulta_zonas(bbox, niveles=("9",), grande=False):
    """Aparte de la de calles: añadir zonas no invalida la caché del callejero."""
    tipos = "|".join(sorted(LUGAR_TIPOS | PARAJE_TIPOS | BARRIO_TIPOS))
    nv = "".join(f'\n  relation["boundary"="administrative"]["admin_level"="{n}"];' for n in niveles)
    return cabecera(bbox, grande) + f"""
({nv}
  node["place"~"^({tipos})$"]["name"];
);
out geom;"""


def consulta_poi(bbox, grande=False):
    """Hospitales y comisarías, para «ir a…» (el centro de cada uno basta)."""
    return cabecera(bbox, grande) + """
(
  nwr["amenity"~"^(police|hospital)$"];
);
out center tags;"""


def descargar(region, q, refresh, vueltas=3, salir=True, servidores=None):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"overpass-{region}-{hashlib.sha1(q.encode()).hexdigest()[:12]}.json"
    if f.exists() and not refresh:
        print(f"Overpass: caché {f.name}")
        return json.loads(f.read_text("utf-8"))
    with tempfile.NamedTemporaryFile("w", suffix=".ql", delete=False) as tq:
        tq.write(q)
    # Overpass da 502/504 a ratos cuando está cargado: tres vueltas por los servidores, con espera.
    servidores = servidores or SERVIDORES
    for vuelta, url in [(v, u) for v in range(vueltas) for u in servidores]:
        if vuelta and url == servidores[0]:
            print(f"  vuelta {vuelta + 1}: espero 60 s")
            time.sleep(60)
        print(f"Overpass: descargando de {url} …")
        r = subprocess.run(["curl", "-sS", "--fail", "--max-time", "900", "-A", UA, url,
                            "--data-urlencode", f"data@{tq.name}", "-o", str(f) + ".part"])
        if r.returncode == 0:
            try:
                d = json.loads(Path(str(f) + ".part").read_text("utf-8"))
            except ValueError:
                print("  respuesta no es JSON; siguiente servidor")
                continue
            if d.get("remark", "").lower().startswith(("runtime error", "error")):
                print(f"  {d['remark']}; siguiente servidor")
                continue
            Path(str(f) + ".part").replace(f)
            return d
        print(f"  curl salió con {r.returncode}; siguiente servidor")
    if not salir:
        return None
    sys.exit("Overpass no respondió en ningún servidor; reintente más tarde.")


def descargar_por_partes(region, bbox, partes, refresh, nivel_max=2):
    """La consulta de calles de una región grande, en partes×partes cajas (Overpass corta las respuestas
    de cientos de MB). Si una caja falla, se parte en cuatro y se reintenta, hasta nivel_max veces (el
    centro de Madrid no bajó entero el 2026-10-24). Cada caja va a su caché; se juntan quitando los
    repetidos (una vía que cruza dos cajas viene entera en las dos)."""
    elems, vistos = [], set()
    fecha = [None]

    def bajar(caja, nivel, etiqueta):
        # Antes de partir, solo el servidor principal (falla rápido); el de respaldo tarda 15 min en rendirse.
        d = (descargar(region, consulta(caja, True), refresh, vueltas=2, salir=False, servidores=SERVIDORES[:1])
             if nivel < nivel_max else descargar(region, consulta(caja, True), refresh))
        if d is None:
            print(f"  {etiqueta}: no bajó entera; la parto en cuatro")
            s, w, n, e = caja
            ml, mo = round((s + n) / 2, 6), round((w + e) / 2, 6)
            for k, sub in enumerate(([s, w, ml, mo], [s, mo, ml, e], [ml, w, n, mo], [ml, mo, n, e])):
                bajar(sub, nivel + 1, f"{etiqueta}.{k + 1}")
            return
        fecha[0] = fecha[0] or d.get("osm3s", {}).get("timestamp_osm_base")
        for el in d["elements"]:
            k = (el["type"], el["id"])
            if k not in vistos:
                vistos.add(k)
                elems.append(el)
        print(f"  {etiqueta}: {len(d['elements'])} elementos; {len(elems)} en total")

    s, w, n, e = bbox
    dlat, dlon = (n - s) / partes, (e - w) / partes
    for i in range(partes):
        for j in range(partes):
            caja = [round(s + i * dlat, 6), round(w + j * dlon, 6), round(s + (i + 1) * dlat, 6), round(w + (j + 1) * dlon, 6)]
            bajar(caja, 0, f"parte {i * partes + j + 1}/{partes * partes}")
    return {"osm3s": {"timestamp_osm_base": fecha[0]}, "elements": elems}


# ---------------------------------------------------------------- vías


def nombre_via(tags, overrides):
    hw = tags.get("highway", "")
    nom = tags.get("name") or tags.get("name:gl") or tags.get("name:es")
    ref = tags.get("ref")
    if VIA_RAPIDA.match(hw) and ref:
        nom = ref.replace(";", " / ")
    elif not nom and ref:
        nom = ref.replace(";", " / ")
    if not nom:
        return None
    return overrides["nombre_mostrar"].get(nom, nom)


def claves_via(tags, mostrado):
    ks = {clave(mostrado)}
    for t in ("name", "name:gl", "name:es", "alt_name", "old_name", "official_name", "loc_name"):
        for v in (tags.get(t) or "").split(";"):
            if v.strip():
                ks.add(clave(v))
    ks.discard("")
    return ks


def extraer_vias(elems, proy, overrides, cuenta):
    """Lista de vías: dict(id, nombre, clase, area, pts, claves, bb)."""
    excl = set(overrides["excluir_vias"])
    vias = []
    for e in elems:
        tags = e.get("tags", {})
        es_plaza = tags.get("place") == "square"
        hw = tags.get("highway")
        if e["type"] == "way" and hw:
            if e["id"] in excl:
                cuenta["excluida (override)"] += 1
                continue
            if hw in DESCARTE or tags.get("indoor") == "yes":
                cuenta[f"descartada {hw if hw in DESCARTE else 'indoor'}"] += 1
                continue
            nom = nombre_via(tags, overrides)
            if not nom:
                continue
            geo = e.get("geometry") or []
            ids = e.get("nodes") or [None] * len(geo)
            pares = [(n, proy.xy(g["lat"], g["lon"])) for n, g in zip(ids, geo) if g]
            pts = [p for _, p in pares]
            if len(pts) < 2:
                continue
            area = tags.get("area") == "yes" and pts[0] == pts[-1] and len(pts) >= 4
            clase = 1 if hw in PEATONAL else 2 if hw in SENDA else 0
            # nodos y raw (sin simplificar) los usa trocear() para cortar en las intersecciones.
            vias.append(dict(id=e["id"], nombre=nom, clase=clase, area=area, pts=pts, raw=pts,
                             nodos=[n for n, _ in pares] if None not in ids else None,
                             claves=claves_via(tags, nom)))
            cuenta[f"vía {'área ' if area else ''}{['calzada', 'peatonal', 'senda'][clase]}"] += 1
        elif es_plaza or (e["type"] == "relation" and hw == "pedestrian"):
            nom = tags.get("name") or tags.get("name:gl") or tags.get("name:es")
            if not nom:
                continue
            nom = overrides["nombre_mostrar"].get(nom, nom)
            anillos = []
            if e["type"] == "way":
                anillos.append([proy.xy(g["lat"], g["lon"]) for g in e.get("geometry") or [] if g])
            else:
                for m in e.get("members", []):
                    if m.get("type") == "way" and m.get("role") in ("outer", "") and m.get("geometry"):
                        anillos.append([proy.xy(g["lat"], g["lon"]) for g in m["geometry"] if g])
                anillos = unir_anillos(anillos)
            for a in anillos:
                if len(a) >= 4 and a[0] == a[-1]:
                    vias.append(dict(id=e["id"], nombre=nom, clase=1, area=True, pts=a, claves=claves_via(tags, nom)))
                    cuenta["área plaza/peatonal"] += 1
    for v in vias:
        v["pts"] = douglas_peucker(v["pts"], DP_TOL)
        v["bb"] = caja_de(v["pts"])
    return vias


def unificar_variantes(vias, cuenta):
    """Un solo nombre por calle: las vías cuyo nombre da la misma clave_unir() y están a ≤ UNIR_M unas de otras
    (en cadena) toman el nombre con más metros del grupo, pesados por PESO_NOMBRE (a igualdad, el
    alfabético). Devuelve los
    cambios {(nombre viejo, nombre nuevo): [vías, punto de una]} para el informe."""
    por_clave = defaultdict(list)
    for i, v in enumerate(vias):
        por_clave[clave_unir(v["nombre"])].append(i)
    padre = list(range(len(vias)))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    def cerca(a, b):
        (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = a["bb"], b["bb"]
        if ax0 > bx1 + UNIR_M or bx0 > ax1 + UNIR_M or ay0 > by1 + UNIR_M or by0 > ay1 + UNIR_M:
            return False
        for u, w in ((a["pts"], b["pts"]), (b["pts"], a["pts"])):
            for px, py in u:
                if dist_polilinea(px, py, w)[0] <= UNIR_M:
                    return True
        return False

    cambios = {}
    for k, ids in por_clave.items():
        if not k or len({vias[i]["nombre"] for i in ids}) < 2:
            continue
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                if raiz(ids[x]) != raiz(ids[y]) and cerca(vias[ids[x]], vias[ids[y]]):
                    padre[raiz(ids[x])] = raiz(ids[y])
        grupos = defaultdict(list)
        for i in ids:
            grupos[raiz(i)].append(i)
        for g in grupos.values():
            metros = Counter()
            for i in g:
                pts = vias[i]["pts"]
                tipo = "area" if vias[i]["area"] else ("calzada", "peatonal", "senda")[vias[i]["clase"]]
                metros[vias[i]["nombre"]] += PESO_NOMBRE[tipo] * sum(math.dist(pts[j], pts[j + 1])
                                                                    for j in range(len(pts) - 1))
            if len(metros) < 2:
                continue
            canon = min(metros, key=lambda n: (-metros[n], orden_alfa(n)))
            for i in g:
                if vias[i]["nombre"] != canon:
                    c = cambios.setdefault((vias[i]["nombre"], canon), [0, vias[i]["pts"][0]])
                    c[0] += 1
                    vias[i]["nombre"] = canon
    cuenta["vía con el nombre de su variante mayoritaria"] += sum(c[0] for c in cambios.values())
    return cambios


def caja_de(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


# ---------------------------------------------------------------- tramos


def orden_alfa(nombre):
    return sin_tildes(nombre).lower(), nombre


def trocear(vias, cuenta):
    """Corta cada vía lineal en sus intersecciones. Devuelve los trozos (las áreas, tal cual),
    cada uno con tramo = (A, B): el nombre de la calle que cruza en cada extremo, o None."""
    lineales = [v for v in vias if not v["area"] and v.get("nodos")]
    en_nodo = defaultdict(list)          # nodo → [(índice de vía lineal, posición)]
    for vi, v in enumerate(lineales):
        for p, n in enumerate(v["nodos"]):
            en_nodo[n].append((vi, p))
    memo = {}

    def cruce(n, nombre):
        """La calle que cruza a 'nombre' en el nodo n (primero calzada, luego alfabético), o None."""
        k = (n, nombre)
        if k not in memo:
            cands = {}
            for wi, _ in en_nodo[n]:
                w = lineales[wi]
                if w["nombre"] != nombre and w["clase"] in (0, 1):
                    cands[w["nombre"]] = min(cands.get(w["nombre"], 9), w["clase"])
            memo[k] = min(cands, key=lambda c: (cands[c], orden_alfa(c))) if cands else None
        return memo[k]

    def ramas(n, nombre, salvo):
        """(vía, posición, sentido) por los que la calle 'nombre' sale del nodo n, menos 'salvo'."""
        return [(wi, q, d) for wi, q in en_nodo[n] if lineales[wi]["nombre"] == nombre
                for d in (-1, 1) if 0 <= q + d < len(lineales[wi]["nodos"]) and (wi, q, d) not in salvo]

    def seguir(n, nombre, desde):
        """Desde el extremo n de un trozo (que no es intersección), recorre la calle por sus propias
        vías hasta el primer cruce de cada rama. desde = (vía, posición, sentido) de la rama por la
        que se llegó, que no cuenta. Si se bifurca (calzadas desdobladas, una Y), vale el cruce
        solo si todas las ramas llegan al mismo; un fondo de saco no aporta ninguno."""
        hallados, vistos = set(), set()
        pila = [(wi, q, d) for wi, q, d in ramas(n, nombre, {desde})]
        while pila and len(hallados) < 2:
            wi, q, d = pila.pop()
            if (wi, q, d) in vistos:
                continue
            vistos.add((wi, q, d))
            ns = lineales[wi]["nodos"]
            q += d
            while True:
                m = ns[q]
                c = cruce(m, nombre)
                if c:
                    hallados.add(c)
                    break
                fin = q == 0 or q == len(ns) - 1
                # En un extremo, o donde otra vía de la misma calle sale de un nodo intermedio.
                otras = ramas(m, nombre, {(wi, q, -d), (wi, q, d)})
                pila += [r for r in otras if r not in vistos]
                if fin:
                    break
                vistos.add((wi, q, d))
                q += d
        return hallados.pop() if len(hallados) == 1 else None

    trozos = []
    for vi, v in enumerate(lineales):
        ns, raw, nombre = v["nodos"], v["raw"], v["nombre"]
        cortes = [0] + [p for p in range(1, len(ns) - 1) if cruce(ns[p], nombre)] + [len(ns) - 1]
        for i, j in zip(cortes, cortes[1:]):
            a = cruce(ns[i], nombre) or (seguir(ns[i], nombre, (vi, i, 1)) if i == 0 else None)
            b = cruce(ns[j], nombre) or (seguir(ns[j], nombre, (vi, j, -1)) if j == len(ns) - 1 else None)
            pts = douglas_peucker(raw[i:j + 1], DP_TOL)
            trozos.append(dict(nombre=nombre, clase=v["clase"], area=False, pts=pts, bb=caja_de(pts),
                               tramo=(a, b)))
            cuenta["trozo con tramo " + ("completo" if a and b else "de un lado" if a or b else "sin cruce")] += 1
    sin_nodos = [v for v in vias if not v["area"] and not v.get("nodos")]
    cuenta["vía sin ids de nodo (sin tramo)"] += len(sin_nodos)
    for v in sin_nodos + [v for v in vias if v["area"]]:
        trozos.append(dict(nombre=v["nombre"], clase=v["clase"], area=v["area"], pts=v["pts"], bb=v["bb"],
                           tramo=(None, None)))
    return trozos


def unir_anillos(trozos):
    """Une los trozos de un multipolígono en anillos cerrados (los que no cierran se tiran)."""
    trozos = [t for t in trozos if len(t) >= 2]
    anillos = []
    while trozos:
        a = trozos.pop()
        cambio = True
        while a[0] != a[-1] and cambio:
            cambio = False
            for i, t in enumerate(trozos):
                if t[0] == a[-1]:
                    a = a + t[1:]
                elif t[-1] == a[-1]:
                    a = a + t[::-1][1:]
                elif t[-1] == a[0]:
                    a = t + a[1:]
                elif t[0] == a[0]:
                    a = t[::-1] + a[1:]
                else:
                    continue
                trozos.pop(i)
                cambio = True
                break
        if a[0] == a[-1]:
            anillos.append(a)
    return anillos


# ---------------------------------------------------------------- portales


ENTRADA_PRIO = {"main": 0, "yes": 1, "home": 2, "staircase": 3}
ENTRADA_NO = {"emergency", "exit", "garage", "service", "delivery"}


def parse_numero(hn):
    hn = hn.strip().replace(";", "-").replace(",", "-")
    m = re.match(r"^(\d{1,4})\s*(.*)$", hn)
    if not m:
        return 0, hn.upper()
    resto = re.sub(r"\s+", " ", m.group(2).strip().upper())
    if not resto:
        return int(m.group(1)), ""
    if re.match(r"^[A-Z]$", resto):
        return int(m.group(1)), resto
    if resto[0] in "-/":
        partes = [x for x in re.split(r"[-/ ]+", resto) if x]
        if len(partes) > 1 and all(x.isdigit() for x in partes):
            return int(m.group(1)), "-" + partes[-1]  # "1;3;5;…;23" → "1-23"
        return int(m.group(1)), resto.replace(" ", "")
    return int(m.group(1)), " " + resto


class IndiceVias:
    """Rejilla de 100 m sobre los segmentos de las vías lineales, para buscar por cercanía."""

    CEL = 100.0

    def __init__(self, vias):
        self.vias = vias
        self.g = defaultdict(set)
        for i, v in enumerate(vias):
            x0, y0, x1, y1 = v["bb"]
            for cx in range(int(x0 // self.CEL), int(x1 // self.CEL) + 1):
                for cy in range(int(y0 // self.CEL), int(y1 // self.CEL) + 1):
                    self.g[(cx, cy)].add(i)

    def cerca(self, x0, y0, x1, y1, r):
        out = set()
        for cx in range(int((x0 - r) // self.CEL), int((x1 + r) // self.CEL) + 1):
            for cy in range(int((y0 - r) // self.CEL), int((y1 + r) // self.CEL) + 1):
                out |= self.g.get((cx, cy), set())
        return out


def extraer_portales(elems, proy, vias, overrides, cuenta, sin_pareja, por_lugar):
    entradas = {}
    for e in elems:
        if e["type"] == "node" and "entrance" in e.get("tags", {}):
            v = e["tags"]["entrance"]
            if v not in ENTRADA_NO:
                entradas[e["id"]] = (ENTRADA_PRIO.get(v, 4), proy.xy(e["lat"], e["lon"]))
    idx = IndiceVias(vias)
    alias = {clave(k): clave(v) for k, v in overrides["alias_calle"].items()}
    portales = []
    for e in elems:
        tags = e.get("tags", {})
        hn = tags.get("addr:housenumber")
        if not hn:
            continue
        calle = tags.get("addr:street")
        if not calle:
            cuenta["portal sin addr:street"] += 1
            if tags.get("addr:place"):
                por_lugar[tags["addr:place"]] += 1
            continue
        if e["type"] == "node":
            geo, fuente = [proy.xy(e["lat"], e["lon"])], 0
        elif e["type"] == "way":
            geo, fuente = [proy.xy(g["lat"], g["lon"]) for g in e.get("geometry") or [] if g], 2
            ent = sorted(entradas[n] for n in e.get("nodes", []) if n in entradas)
            if ent:
                geo, fuente = [ent[0][1]], 1
        else:
            geo, fuente = [], 2
            for m in e.get("members", []):
                if m.get("type") == "way" and m.get("role") in ("outer", "") and m.get("geometry"):
                    geo += [proy.xy(g["lat"], g["lon"]) for g in m["geometry"] if g]
        if not geo:
            continue
        k = clave(calle)
        k = alias.get(k, k)
        xs, ys = [p[0] for p in geo], [p[1] for p in geo]
        cand = idx.cerca(min(xs), min(ys), max(xs), max(ys), PORTAL_ASOC)

        def mas_cercana(filtro):
            mejor = None
            for i in cand:
                v = vias[i]
                if not filtro(v):
                    continue
                x0, y0, x1, y1 = v["bb"]
                if x0 - PORTAL_ASOC > max(xs) or x1 + PORTAL_ASOC < min(xs) or \
                        y0 - PORTAL_ASOC > max(ys) or y1 + PORTAL_ASOC < min(ys):
                    continue
                for p in geo:
                    d, qx, qy = dist_polilinea(p[0], p[1], v["pts"])
                    if mejor is None or d < mejor[0]:
                        mejor = (d, v, p, (qx, qy))
            return mejor if mejor and mejor[0] <= PORTAL_ASOC else None

        m = mas_cercana(lambda v: k in v["claves"])
        etapa = 1
        if not m:
            ks = clave_sin_tipo(k)
            nombres = {}
            for i in cand:
                for kv in vias[i]["claves"]:
                    if clave_sin_tipo(kv) == ks:
                        nombres.setdefault(vias[i]["nombre"], kv)
            if len(nombres) == 1:
                kv = next(iter(nombres.values()))
                m = mas_cercana(lambda v: kv in v["claves"])
                etapa = 2
        if not m:
            cuenta["portal sin pareja"] += 1
            sin_pareja[calle] += 1
            continue
        cuenta[f"portal emparejado en {etapa}ª vuelta"] += 1
        d, via, p, q = m
        if fuente == 2 and len(geo) > 1:
            # Fachada: el punto del contorno del edificio más cercano a la calle.
            anillo = geo if geo[0] == geo[-1] else geo + [geo[0]]
            _, fx, fy = dist_polilinea(q[0], q[1], anillo)
            punto = (fx, fy)
        else:
            punto = p
        num, suf = parse_numero(hn)
        portales.append(dict(x=punto[0], y=punto[1], calle=via["nombre"], num=num, suf=suf, fuente=fuente))
    # Duplicados (nodo de portal y edificio con la misma dirección): uno por calle+número a < 15 m.
    portales.sort(key=lambda p: (p["calle"], p["num"], p["suf"], p["fuente"]))
    finales = []
    for p in portales:
        if finales and any(q["calle"] == p["calle"] and q["num"] == p["num"] and q["suf"] == p["suf"]
                           and math.hypot(q["x"] - p["x"], q["y"] - p["y"]) < 15 for q in finales[-8:]):
            cuenta["portal duplicado"] += 1
            continue
        finales.append(p)
    return finales


# ---------------------------------------------------------------- Catastro

# Portales del Catastro (WFS INSPIRE de direcciones, uso libre citando la fuente) dentro de la caja
# "catastro" de la región: rellenan los números que OSM no tiene. Los nombres no se toman de ahí:
# vienen abreviados, sin artículo y a veces truncados o en castellano («RU CASTRON DOURO»,
# «PZ FUENTERRABIA»). Sirven solo para casar cada portal con la vía de OSM, que es la que da el nombre.
# Contraste en la Zona Vella (2026-10-24): ningún nombre de OSM estaba mal; faltaba en OSM el 14 %
# de los números.
CATASTRO_WFS = ("http://ovc.catastro.meh.es/INSPIRE/wfsAD.aspx?service=WFS&version=2.0.0&request=GetFeature"
                "&typeNames=ad:Address&srsName=EPSG::4326&bbox={s},{w},{n},{e},urn:ogc:def:crs:EPSG::4326")
CATASTRO_PASO = (0.0025, 0.0035)   # grados (lat, lon) por petición: unas 250 direcciones en el casco
CATASTRO_ASOC = 30    # m: el portal solo entra si pasa a esta distancia una vía de OSM de su nombre
CATASTRO_DUP = 60     # m: si OSM ya tiene esa calle y número a esta distancia, se queda el de OSM
CATASTRO_TIPO_R = 150 # m: si a esta distancia hay una vía de su nombre Y su tipo, el portal es de esa o de ninguna
CATASTRO_VECINO = 25  # m: portales de OSM de la misma calle y acera a esta distancia…
CATASTRO_SALTO = 12   # …cuyo número más próximo difiere en más de esto: el del Catastro contradice a OSM y no entra
# Abreviaturas del Catastro y sus formas castellanas cuando OSM usa la gallega oficial.
CATASTRO_ABREV = {"sto": "santo", "sta": "santa", "fte": "fonte", "vqz": "vazquez", "sn": "san",
                  "fuenterrabia": "fonterrabia"}
# Tipo de vía del Catastro → primera palabra en OSM. Desempata «TR FRANCO 2» (Travesa) de «Rúa do Franco 2».
CATASTRO_TIPO = {"RU": {"rua"}, "PZ": {"praza"}, "PC": {"pracina"}, "PÑ": {"pracina"}, "CJ": {"ruela", "calexon"},
                 "AV": {"avenida"}, "CT": {"costa"}, "TR": {"travesa"}, "CÇ": {"calzada"}, "CQ": {"canton"},
                 "PQ": {"parque"}, "CM": {"corredoira", "camino"}, "TS": {"transito"},
                 "TV": {"transito", "travesa"}, "VI": {"via"}, "CP": {"campo"}, "JR": {"xardin"}}
NS_AD = {"ad": "urn:x-inspire:specification:gmlas:Addresses:3.0", "gml": "http://www.opengis.net/gml/3.2",
         "gn": "urn:x-inspire:specification:gmlas:GeographicalNames:3.0", "xlink": "http://www.w3.org/1999/xlink"}


def _texto_catastro(s):
    """El servidor declara ISO-8859-1 pero manda UTF-8 («RAIÃ\\x91A» por «RAIÑA»). Si lo arreglan, queda igual."""
    try:
        return s.encode("latin1").decode("utf-8")
    except UnicodeError:
        return s


def leer_catastro(f):
    raiz = ET.parse(f).getroot()
    if not raiz.tag.endswith("FeatureCollection"):
        sys.exit(f"Catastro: respuesta inesperada en {f.name} ({raiz.tag}); quítela de la caché y reintente.")
    gid = "{%s}id" % NS_AD["gml"]
    href = "{%s}href" % NS_AD["xlink"]
    nombres = {}
    for tn in raiz.iter("{%s}ThoroughfareName" % NS_AD["ad"]):
        t = tn.find(".//gn:text", NS_AD)
        if t is not None and t.text:
            nombres[tn.get(gid)] = _texto_catastro(t.text.strip())
    dirs = {}
    for a in raiz.iter("{%s}Address" % NS_AD["ad"]):
        pos = a.find(".//gml:pos", NS_AD)
        des = a.find(".//ad:LocatorDesignator/ad:designator", NS_AD)
        tn = [c.get(href, "")[1:] for c in a.findall("ad:component", NS_AD) if ".TN." in c.get(href, "")]
        if pos is None or des is None or not des.text or not tn or tn[0] not in nombres:
            continue
        lat, lon = map(float, pos.text.split())
        dirs[a.get(gid)] = dict(lat=lat, lon=lon, num=des.text.strip(), calle=nombres[tn[0]])
    return dirs


def descargar_catastro(region, caja, refresh):
    s, w, n, e = caja
    dlat, dlon = CATASTRO_PASO
    CACHE.mkdir(parents=True, exist_ok=True)
    dirs, nuevas = {}, 0
    for i in range(math.ceil((n - s) / dlat - 1e-9)):
        for j in range(math.ceil((e - w) / dlon - 1e-9)):
            url = CATASTRO_WFS.format(s=round(s + i * dlat, 6), w=round(w + j * dlon, 6),
                                      n=round(min(n, s + (i + 1) * dlat), 6), e=round(min(e, w + (j + 1) * dlon), 6))
            f = CACHE / f"catastro-{region}-{hashlib.sha1(url.encode()).hexdigest()[:12]}.xml"
            if refresh or not f.exists():
                if nuevas:
                    time.sleep(1)
                r = subprocess.run(["curl", "-sS", "--fail", "--max-time", "120", "-A", UA, "-o", str(f) + ".part", url])
                if r.returncode:
                    sys.exit("Catastro no respondió; reintente más tarde o quite la caja «catastro» de la región.")
                Path(str(f) + ".part").replace(f)
                nuevas += 1
            dirs.update(leer_catastro(f))
    print(f"Catastro: {len(dirs)} direcciones ({nuevas} peticiones nuevas, el resto de la caché)")
    return [d for d in dirs.values() if s <= d["lat"] <= n and w <= d["lon"] <= e]


def _toks(s):
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes(s.replace("'", "").replace("’", "")).lower()).split()


def toks_catastro(nombre):
    """«RU FONTE DE STO ANTONIO (DO)» → ('RU', ['fonte', 'santo', 'antonio'])."""
    t = re.sub(r"\([^)]*\)", " ", nombre).split()
    return (t[0] if t else ""), [CATASTRO_ABREV.get(x, x) for x in _toks(" ".join(t[1:])) if x not in PARTICULAS]


def casa_catastro(cat, nombre_osm):
    """0 = no casa; 2 = mismas palabras; 1 = cada palabra del Catastro empieza una de OSM, en orden y desde la
    primera tras el tipo (abreviaturas, nombres truncados: «SAN MARTIÑO» → «Praza de San Martiño Pinario»)."""
    t = [x for x in _toks(nombre_osm) if x not in PARTICULAS]
    mejor = 0
    for osm in (t[1:], t):
        if not osm or not cat:
            continue
        if cat == osm or "".join(cat) == "".join(osm):
            return 2
        if osm[0].startswith(cat[0]):
            j = 1
            for x in cat[1:]:
                while j < len(osm) and not osm[j].startswith(x):
                    j += 1
                if j == len(osm):
                    break
                j += 1
            else:
                mejor = 1
    return mejor


def completar_con_catastro(dirs, proy, vias, portales, cuenta):
    """Añade los portales del Catastro que OSM no tiene. Devuelve (portales, cuántos se han añadido)."""
    idx = IndiceVias(vias)
    osm = defaultdict(list)
    por_calle = defaultdict(list)
    for p in portales:
        osm[(p["calle"], p["num"], p["suf"])].append((p["x"], p["y"]))
        por_calle[p["calle"]].append(p)
    nuevos, lejos = [], []
    for d in dirs:
        num, suf = parse_numero(d["num"])
        if not num:
            cuenta["Catastro: sin número"] += 1
            continue
        x, y = proy.xy(d["lat"], d["lon"])
        tipo, cat = toks_catastro(d["calle"])
        cands, tipo_lejos = [], False
        for i in idx.cerca(x, y, x, y, CATASTRO_TIPO_R):
            v = vias[i]
            nivel = casa_catastro(cat, v["nombre"])
            if not nivel:
                continue
            dd = dist_polilinea(x, y, v["pts"])[0]
            t = _toks(v["nombre"])
            tipo_ok = bool(t) and t[0] in CATASTRO_TIPO.get(tipo, ())
            if dd <= CATASTRO_ASOC:
                cands.append((tipo_ok, nivel, -dd, v["nombre"]))
            elif tipo_ok and dd <= CATASTRO_TIPO_R:
                tipo_lejos = True
        if not cands:
            cuenta["Catastro: sin vía de su nombre a 30 m"] += 1
            continue
        top = max(cands)[:2]
        if not top[0] and tipo_lejos:
            # «RU ALGALIA DE ABAIXO 39» junto a la Praza da Algalia de Abaixo: es de la rúa, que pasa más lejos.
            cuenta["Catastro: su tipo de vía apunta a otra calle"] += 1
            continue
        nombres = {c[3] for c in cands if c[:2] == top}
        if len(nombres) > 1:
            cuenta["Catastro: ambiguo entre vías"] += 1
            continue
        calle = nombres.pop()
        ya = osm.get((calle, num, suf), [])
        if any(math.hypot(px - x, py - y) < CATASTRO_DUP for px, py in ya):
            cuenta["Catastro: ya estaba en OSM"] += 1
            continue
        if ya:
            cuenta["Catastro: OSM lo tiene en otro sitio (manda OSM)"] += 1
            lejos.append(f"{calle} {num}{suf}")
            continue
        if any(q["calle"] == calle and q["num"] == num and q["suf"] == suf
               and math.hypot(q["x"] - x, q["y"] - y) < 15 for q in nuevos):
            continue
        acera = [q["num"] for q in por_calle[calle] if q["num"] % 2 == num % 2
                 and math.hypot(q["x"] - x, q["y"] - y) < CATASTRO_VECINO]
        if acera and min(abs(q - num) for q in acera) > CATASTRO_SALTO:
            cuenta["Catastro: contradice la numeración de OSM a su lado"] += 1
            continue
        cuenta["Catastro: portal añadido"] += 1
        nuevos.append(dict(x=x, y=y, calle=calle, num=num, suf=suf, fuente=1))
    if lejos:
        print(f"Catastro: {len(lejos)} números que OSM tiene a más de {CATASTRO_DUP} m (manda OSM): "
              + ", ".join(lejos[:12]) + (" …" if len(lejos) > 12 else ""))
    return portales + nuevos, len(nuevos)


# ---------------------------------------------------------------- Ayuntamiento de Madrid

# Callejero oficial del Ayuntamiento de Madrid (datos.madrid.es, conjunto 213605, «Relación de direcciones
# vigentes, con coordenadas»; CC BY 4.0, se cita la fuente). Trae 214.676 direcciones frente a unas 97.000
# de OSM en el término municipal. Igual que con el Catastro: el número viene de aquí, el nombre lo pone
# siempre la vía de OSM. Los nombres oficiales vienen completos y en mayúsculas («CALLE DEL 26 DE ABRIL»),
# así que casan con OSM por la misma clave normalizada que addr:street.
# Fuera: JARDÍN/PARQUE, los kilómetros y GARAJE (el garaje de una esquina da a la calle lateral con el número
# de la principal: «Princesa 25» salía en Luisa Fernanda; 2026-10-24).
AYTO_TIPOS_NDP = {"PORTAL", "FRENTE FACHADA", "PARCELA"}
AYTO_ASOC = 45        # m: el portal se casa con una vía de su nombre a esta distancia (avenidas anchas, laterales)


def _dms(s):
    """«40°26'15.32'' N» → 40.43759."""
    m = re.match(r"\s*(\d+)°(\d+)'([\d.]+)''\s*([NSEW])", s)
    if not m:
        return None
    v = int(m.group(1)) + int(m.group(2)) / 60 + float(m.group(3)) / 3600
    return -v if m.group(4) in "SW" else v


def leer_ayto_madrid(f):
    import csv
    dirs, cuenta = [], Counter()
    with open(f, encoding="latin1", newline="") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            if row["CLASE_APP"] != "NUMERO" or row["TIPO_NDP"] not in AYTO_TIPOS_NDP:
                cuenta["fuera de uso"] += 1
                continue
            lat, lon = _dms(row["LATITUD"]), _dms(row["LONGITUD"])
            if lat is None or lon is None:
                cuenta["sin coordenadas"] += 1
                continue
            calle = " ".join(x for x in (row["VIA_CLASE"], row["VIA_PAR"], row["VIA_NOMBRE_ACENTOS"]) if x.strip())
            num = row["NUMERO"].strip() + row["CALIFICADOR"].strip()
            dirs.append(dict(lat=lat, lon=lon, num=num, calle=calle, tipo=row["VIA_CLASE"].strip(),
                             garaje=row["TIPO_NDP"] == "GARAJE"))
    print(f"Ayuntamiento de Madrid: {len(dirs)} direcciones en uso ({dict(cuenta)})")
    return dirs


def completar_con_ayto(dirs, proy, vias, portales, cuenta, caja=None):
    """Añade los portales del callejero oficial que OSM no tiene, con las salvaguardas del Catastro.
    Empareja por clave (como addr:street) y, si no hay, por clave sin el tipo de vía."""
    por_clave, por_clave_st = defaultdict(list), defaultdict(list)
    for v in vias:
        for k in v["claves"]:
            por_clave[k].append(v)
            por_clave_st[clave_sin_tipo(k)].append(v)
    osm = defaultdict(list)
    por_calle = defaultdict(list)
    for p in portales:
        osm[(p["calle"], p["num"], p["suf"])].append((p["x"], p["y"]))
        por_calle[p["calle"]].append(p)
    nuevos, vistos = [], defaultdict(list)
    sin_casar = Counter()
    for d in dirs:
        num, suf = parse_numero(d["num"])
        if not num:
            cuenta["Ayto: sin número"] += 1
            continue
        x, y = proy.xy(d["lat"], d["lon"])
        if caja and not (caja[0] <= x <= caja[2] and caja[1] <= y <= caja[3]):
            cuenta["Ayto: fuera del recorte"] += 1
            continue
        k = clave(d["calle"])
        mejor = None
        for etapa, cands in ((1, por_clave.get(k, ())), (2, por_clave_st.get(clave_sin_tipo(k), ()))):
            for v in cands:
                x0, y0, x1, y1 = v["bb"]
                if x < x0 - AYTO_ASOC or x > x1 + AYTO_ASOC or y < y0 - AYTO_ASOC or y > y1 + AYTO_ASOC:
                    continue
                dd = dist_polilinea(x, y, v["pts"])[0]
                if dd <= AYTO_ASOC and (mejor is None or dd < mejor[0]):
                    mejor = (dd, v["nombre"])
            if mejor:
                cuenta[f"Ayto: casado en {etapa}ª vuelta"] += 1
                break
        if not mejor:
            cuenta["Ayto: sin vía de su nombre a 45 m"] += 1
            sin_casar[d["calle"]] += 1
            continue
        calle = mejor[1]
        ya = osm.get((calle, num, suf), [])
        if any(math.hypot(px - x, py - y) < CATASTRO_DUP for px, py in ya):
            cuenta["Ayto: ya estaba en OSM"] += 1
            continue
        if ya:
            cuenta["Ayto: OSM lo tiene en otro sitio (manda OSM)"] += 1
            continue
        if any(math.hypot(qx - x, qy - y) < 15 for qx, qy in vistos[(calle, num, suf)]):
            cuenta["Ayto: duplicado (portal y garaje juntos)"] += 1
            continue
        acera = [q["num"] for q in por_calle[calle] if q["num"] % 2 == num % 2
                 and math.hypot(q["x"] - x, q["y"] - y) < CATASTRO_VECINO]
        if acera and min(abs(q - num) for q in acera) > CATASTRO_SALTO:
            cuenta["Ayto: contradice la numeración de OSM a su lado"] += 1
            continue
        cuenta["Ayto: portal añadido"] += 1
        vistos[(calle, num, suf)].append((x, y))
        nuevos.append(dict(x=x, y=y, calle=calle, num=num, suf=suf, fuente=1))
    if sin_casar:
        print("Ayto: calles sin vía de OSM de su nombre (las 15 con más portales): "
              + ", ".join(f"{c} ({n})" for c, n in sin_casar.most_common(15)))
    completar_con_ayto.sin_casar = sin_casar
    return portales + nuevos, len(nuevos)


# ---------------------------------------------------------------- hospitales y comisarías

# Tipo de cada punto (lo lee el reloj, Ir.mc): hospital, hospital con urgencias, y la policía por cuerpo.
# Las comisarías del CNP van aparte de sus otras dependencias (DNI, divisiones, unidades centrales): para
# poner una denuncia sirve la comisaría, no la oficina de pasaportes.
POI_HOSPITAL, POI_URGENCIAS, POI_CNP, POI_LOCAL, POI_GC, POI_POLICIA, POI_CNP_OTRA = range(7)
POI_ETIQUETA = ["hospital", "hospital (urgencias)", "comisaría CNP", "policía municipal/local", "guardia civil",
                "policía (sin cuerpo)", "CNP (otra dependencia)"]
CNP_OTRA = re.compile(r"\b(division|unidad|oficina|dni|pasaporte|complejo|jefatura|tedax|cientifica|presos|formacion|"
                      r"personal|medios aereos|coordinacion|ucrif|extranjeria|general|brigada|grupo|documentacion)\b")


def tipo_policia(tags):
    """Cuerpo de un amenity=police, o None si no es una dependencia policial (oficinas de la DGT)."""
    nom = sin_tildes(" ".join(tags.get(k, "") for k in ("name", "name:es", "short_name", "short_name:es"))).lower()
    if re.search(r"\b(dgt|dxt|direccion (general|xeral) de trafico|jefatura (provincial|local) de trafico)\b", nom):
        return None
    op = sin_tildes(" ".join(tags.get(k, "") for k in ("operator", "operator:short"))).lower()
    t = nom + " " + op + " " + sin_tildes(tags.get("official_name", "") + " " + tags.get("police", "")).lower()
    if "guardia civil" in t or "garda civil" in t or "cuartel" in t:
        return POI_GC
    if ("municipal" in t or "local" in t or "ayuntamiento" in op or "concello" in op or "policia de barrio" in t
            or "agentes de movilidad" in t):
        return POI_LOCAL
    if "nacional" in t or "cnp" in t or "comisaria" in t or "dgp" in t or "brigada" in t or "direccion general de la policia" in t:
        if "comisaria" in nom and "general" not in nom:
            return POI_CNP
        return POI_CNP_OTRA if CNP_OTRA.search(nom) else POI_CNP
    return POI_POLICIA


HOSPITAL_NOMBRE = re.compile(r"\b(hospital|ciudad sanitaria|sanatorio|urgencias|complexo hospitalario)\b")


def tipo_hospital(tags):
    """Hospital, hospital con urgencias, o None si no lo es de verdad: en OSM llevan amenity=hospital
    centros de salud, de especialidades y clínicas (de estética, del pie). Entra lo que tiene urgencias o
    se llama hospital (o sanatorio, ciudad sanitaria, «Urgencias …»)."""
    nom = sin_tildes(tags.get("name") or tags.get("official_name") or "").lower()
    if tags.get("emergency") == "yes" or nom.startswith("urgencias"):
        return POI_URGENCIAS
    if tags.get("emergency") == "no" or not HOSPITAL_NOMBRE.search(nom):
        return None
    return POI_HOSPITAL


def extraer_poi(elems, proy, vias, portales, overrides, cuenta, ancho, alto):
    """Hospitales y comisarías de la región: [nombre, dirección, x, y, tipo]. La dirección es la de OSM;
    si no la tiene, la calle más cercana y su portal, como lo diría el reloj desde la puerta."""
    idx = IndiceVias([v for v in vias if not v["area"]] + [v for v in vias if v["area"]])
    por_calle = defaultdict(list)
    for p in portales:
        por_calle[p["calle"]].append(p)
    out = []
    for e in elems:
        tags = e.get("tags", {})
        am = tags.get("amenity")
        c = e.get("center") or ({"lat": e["lat"], "lon": e["lon"]} if "lat" in e else None)
        if am not in ("hospital", "police") or not c:
            continue
        x, y = proy.xy(c["lat"], c["lon"])
        if not (0 <= x <= ancho and 0 <= y <= alto):
            continue
        tipo = tipo_hospital(tags) if am == "hospital" else tipo_policia(tags)
        if tipo is None:
            cuenta[f"punto descartado ({'no es hospital' if am == 'hospital' else 'no es dependencia policial'})"] += 1
            continue
        fijo = overrides.get("poi", {}).get(f"{e['type']}/{e['id']}", {})
        if fijo.get("excluir"):
            cuenta["punto excluido (override)"] += 1
            continue
        nom = tags.get("name") or tags.get("official_name") or tags.get("operator") or POI_ETIQUETA[tipo].capitalize()
        dirc = fijo.get("direccion", "")
        if dirc:
            cuenta["punto: dirección de overrides"] += 1
        elif tags.get("addr:street"):
            dirc = tags["addr:street"] + (" " + tags["addr:housenumber"] if tags.get("addr:housenumber") else "")
        else:
            mejor = None
            for i in idx.cerca(x, y, x, y, 120):
                v = idx.vias[i]
                d = 0.0 if v["area"] and dentro(x, y, v["pts"]) else dist_polilinea(x, y, v["pts"])[0]
                if d <= 120 and (mejor is None or d < mejor[0]):
                    mejor = (d, v["nombre"])
            if mejor:
                ps = sorted(((math.hypot(p["x"] - x, p["y"] - y), p) for p in por_calle[mejor[1]]
                             if abs(p["x"] - x) < 150 and abs(p["y"] - y) < 150), key=lambda t: t[0])
                dirc = mejor[1] + (f" {ps[0][1]['num'] or ''}{ps[0][1]['suf']}".rstrip() if ps and ps[0][0] < 80 else "")
                cuenta["punto: dirección deducida de la calle más cercana"] += 1
        cuenta[f"punto: {POI_ETIQUETA[tipo]}"] += 1
        out.append([nom, dirc, int(round(x)), int(round(y)), tipo])
    # Un edificio puede venir dos veces (nodo y contorno): mismo tipo y nombre a < 80 m, uno.
    out.sort(key=lambda p: (p[4], p[0], p[2], p[3]))
    finales = []
    for p in out:
        if any(q[4] == p[4] and q[0] == p[0] and math.hypot(q[2] - p[2], q[3] - p[3]) < 80 for q in finales[-6:]):
            cuenta["punto duplicado"] += 1
            continue
        finales.append(p)
    return finales


# ---------------------------------------------------------------- zonas


def extraer_zonas(elems, proy, overrides, cuenta, zcfg):
    """Polígonos (relaciones admin_level, como anillos) y lugares (nodos place, más los barrios_extra).

    zcfg["admin_level"]: el último nivel es el polígono que se rasteriza; si hay dos, el primero es su
    padre y su nombre se añade («Sol · Centro»: barrio y distrito de Madrid). zcfg["poligono"]:
    "parroquia" (Santiago: el polígono es la parroquia y el barrio sale de los nodos) o "barrio"
    (Madrid: el polígono ES el barrio oficial y los nodos solo dan lugar)."""
    niveles = list(zcfg["admin_level"])
    nivel, padre = niveles[-1], (niveles[0] if len(niveles) > 1 else None)
    poli_barrio = zcfg["poligono"] == "barrio"
    parroquias, padres, lugares = [], [], []
    for b in overrides.get("barrios_extra", []):
        x, y = proy.xy(b["lat"], b["lon"])
        lugares.append(dict(nombre=b["nombre"], x=x, y=y, tipo=2))
        cuenta["barrio de overrides"] += 1
    for e in elems:
        tags = e.get("tags", {})
        nom = tags.get("name") or tags.get("name:gl") or tags.get("name:es")
        if not nom:
            continue
        if e["type"] == "relation" and tags.get("admin_level") in (nivel, padre):
            trozos = [[proy.xy(g["lat"], g["lon"]) for g in m["geometry"] if g]
                      for m in e.get("members", []) if m.get("type") == "way" and m.get("geometry")]
            anillos = unir_anillos(trozos)
            if not anillos:
                cuenta[f"{zcfg['poligono']} sin anillo cerrado"] += 1
                continue
            pts = [p for a in anillos for p in a]
            es_nivel = tags["admin_level"] == nivel
            (parroquias if es_nivel else padres).append(dict(nombre=nom, anillos=anillos, bb=caja_de(pts)))
            cuenta[zcfg["poligono"] if es_nivel else "polígono padre"] += 1
        elif e["type"] == "node" and tags.get("place") in LUGAR_TIPOS | PARAJE_TIPOS | BARRIO_TIPOS:
            pl = tags["place"]
            tipo = (pl in LUGAR_TIPOS) | (pl in BARRIO_TIPOS and not poli_barrio) << 1 | (pl in PARAJE_TIPOS) << 2
            if not tipo:
                continue
            x, y = proy.xy(e["lat"], e["lon"])
            lugares.append(dict(nombre=nom, x=x, y=y, tipo=tipo))
            cuenta[f"lugar {pl}"] += 1
    if padres:
        for p in parroquias:
            p["nombre"] = f"{p['nombre']} · {padre_de(p, padres) or '?'}"
    return parroquias, lugares


def padre_de(p, padres):
    """El polígono padre que contiene más puntos de muestra del polígono p (rejilla de ~1/12 de su caja)."""
    x0, y0, x1, y1 = p["bb"]
    votos = Counter()
    paso = max(25.0, min(x1 - x0, y1 - y0) / 12)
    y = y0 + paso / 2
    while y < y1:
        x = x0 + paso / 2
        while x < x1:
            if sum(dentro(x, y, a) for a in p["anillos"]) % 2 == 1:
                for q in padres:
                    bx0, by0, bx1, by1 = q["bb"]
                    if bx0 <= x <= bx1 and by0 <= y <= by1 and sum(dentro(x, y, a) for a in q["anillos"]) % 2 == 1:
                        votos[q["nombre"]] += 1
                        break
            x += paso
        y += paso
    return votos.most_common(1)[0][0] if votos else None


def rasterizar(parroquias, zcols, zfilas, cuenta):
    """G[fila][col] = índice de parroquia + 1 de la celda de RCEL m cuyo centro contiene (0 = ninguna).
    Barrido por filas con la regla par-impar sobre todos los anillos: los interiores restan solos."""
    filas, cols = zfilas * RN, zcols * RN
    G = [[0] * cols for _ in range(filas)]
    for gi, p in enumerate(parroquias):
        aristas = [(a[k], a[k + 1]) for a in p["anillos"] for k in range(len(a) - 1)]
        x0, y0, x1, y1 = p["bb"]
        for r in range(max(0, int(y0 // RCEL)), min(filas - 1, int(y1 // RCEL)) + 1):
            y = (r + 0.5) * RCEL
            xs = sorted(ax + (bx - ax) * (y - ay) / (by - ay) for (ax, ay), (bx, by) in aristas
                        if (ay > y) != (by > y))
            for k in range(0, len(xs) - 1, 2):
                c0 = max(0, math.ceil(xs[k] / RCEL - 0.5))
                c1 = min(cols - 1, math.floor(xs[k + 1] / RCEL - 0.5))
                fila = G[r]
                for c in range(c0, c1 + 1):
                    if fila[c] and fila[c] != gi + 1:
                        cuenta["celda de raster en dos parroquias"] += 1
                    else:
                        fila[c] = gi + 1
    return G


def int32(v):
    return v - (1 << 32) if v >= 1 << 31 else v


def empaquetar_zona(zc, zf, G, parroquias, lugares):
    """Zona → lista JSON [FORMATO, N, RASTER, L, LN], o None si no tiene nada."""
    zx0, zy0 = zc * ZONA, zf * ZONA
    celdas = [G[zf * RN + r][zc * RN + c] for r in range(RN) for c in range(RN)]
    presentes = sorted({g for g in celdas if g}, key=lambda g: orden_alfa(parroquias[g - 1]["nombre"]))
    ox, oy = zx0 - ZMARGEN, zy0 - ZMARGEN
    aqui = sorted((l for l in lugares if ox <= l["x"] <= zx0 + ZONA + ZMARGEN and oy <= l["y"] <= zy0 + ZONA + ZMARGEN),
                  key=lambda l: (l["x"], l["y"]))
    if not presentes and not aqui:
        return None, None
    N = [parroquias[g - 1]["nombre"] for g in presentes]
    assert len(N) < 127, f"zona {zc},{zf}: {len(N)} parroquias"
    local = {g: i + 1 for i, g in enumerate(presentes)}
    for l in aqui:
        if l["nombre"] not in N:
            N.append(l["nombre"])
    ids = {n: i for i, n in enumerate(N)}
    vals = [local.get(g, 0) for g in celdas]
    RASTER = [int32(vals[k] | vals[k + 1] << 8 | vals[k + 2] << 16 | vals[k + 3] << 24) for k in range(0, len(vals), 4)]
    L = [int(round(l["x"] - ox)) | int(round(l["y"] - oy)) << 13 | l["tipo"] << 26 for l in aqui]
    LN = [ids[l["nombre"]] for l in aqui]
    lista = [FORMATO, N, RASTER, L, LN]
    nums = len(RASTER) + len(L) + len(LN)
    est = dict(parroquias=len(presentes), lugares=len(aqui), nombres=len(N), nums=nums,
               heap=int(11 * nums + 60 * len(N)), con_parroquia=sum(1 for v in vals if v))
    return lista, est


# ---------------------------------------------------------------- teselas


def teselar(vias, portales, proy):
    cols = math.ceil(proy.ancho / TESELA)
    filas = math.ceil(proy.alto / TESELA)
    teselas = defaultdict(lambda: {"runs": [], "portales": []})

    def caja(col, fila):
        return (col * TESELA - BUF, fila * TESELA - BUF, (col + 1) * TESELA + BUF, (fila + 1) * TESELA + BUF)

    def celdas(x0, y0, x1, y1):
        for c in range(max(0, int((x0 - BUF) // TESELA)), min(cols - 1, int((x1 + BUF) // TESELA)) + 1):
            for f in range(max(0, int((y0 - BUF) // TESELA)), min(filas - 1, int((y1 + BUF) // TESELA)) + 1):
                yield c, f

    for v in vias:
        x0, y0, x1, y1 = v["bb"]
        if v["area"]:
            for c, f in celdas(x0, y0, x1, y1):
                poli = sutherland_hodgman(v["pts"], *caja(c, f))
                if len(poli) >= 3:
                    teselas[(c, f)]["runs"].append((v["nombre"], v["clase"], 1, poli + [poli[0]], v["tramo"]))
            continue
        abiertas = {}  # celda -> lista de puntos de la tirada abierta
        pts = v["pts"]
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            sx0, sy0, sx1, sy1 = min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)
            vistas = set()
            for c, f in celdas(sx0, sy0, sx1, sy1):
                r = liang_barsky(ax, ay, bx, by, *caja(c, f))
                if r is None:
                    continue
                t0, t1 = r
                pa = (ax, ay) if t0 == 0.0 else (ax + t0 * (bx - ax), ay + t0 * (by - ay))
                pb = (bx, by) if t1 == 1.0 else (ax + t1 * (bx - ax), ay + t1 * (by - ay))
                run = abiertas.get((c, f))
                if run is not None and t0 == 0.0 and run[-1] == pa:
                    run.append(pb)
                else:
                    if run is not None:
                        teselas[(c, f)]["runs"].append((v["nombre"], v["clase"], 0, run, v["tramo"]))
                    run = [pa, pb]
                abiertas[(c, f)] = run
                if t1 < 1.0:
                    teselas[(c, f)]["runs"].append((v["nombre"], v["clase"], 0, run, v["tramo"]))
                    del abiertas[(c, f)]
                vistas.add((c, f))
            for cf in list(abiertas):
                if cf not in vistas:
                    teselas[cf]["runs"].append((v["nombre"], v["clase"], 0, abiertas.pop(cf), v["tramo"]))
        for cf, run in abiertas.items():
            teselas[cf]["runs"].append((v["nombre"], v["clase"], 0, run, v["tramo"]))

    for p in portales:
        for c, f in celdas(p["x"], p["y"], p["x"], p["y"]):
            x0, y0, x1, y1 = caja(c, f)
            if x0 <= p["x"] <= x1 and y0 <= p["y"] <= y1:
                teselas[(c, f)]["portales"].append(p)
    return teselas, cols, filas


def q(v, origen):
    return max(0, min(TESELA + 2 * BUF, int(round(v - origen))))


def empaquetar(c, f, t, sufijos):
    """Tesela → lista JSON del FORMATO 2. Devuelve (lista, estadísticas)."""
    ox, oy = c * TESELA - BUF, f * TESELA - BUF
    # Orden de cadena de Python: el mismo con el que se ordenan los portales por calle.
    calles_runs = sorted({r[0] for r in t["runs"]} | {n for r in t["runs"] for n in r[4] if n})
    if len(calles_runs) > MAX_NOMBRES:
        sys.exit(f"tesela {c},{f}: {len(calles_runs)} nombres (> {MAX_NOMBRES}); reduzca TESELA")
    ids = {n: i for i, n in enumerate(calles_runs)}
    R, V = [], []
    lados = Counter()
    for nombre, clase, area, pts, (ta, tb) in sorted(t["runs"], key=lambda r: (ids[r[0]], r[1], r[3][0])):
        qp = []
        for x, y in pts:
            p = (q(x, ox), q(y, oy))
            if not qp or qp[-1] != p:
                qp.append(p)
        if area and len(qp) < 4:
            continue
        # Tiradas largas se parten compartiendo un vértice (no pasa en una tesela de 650 m, pero por si acaso).
        trozos = [qp[i:i + MAX_VERT_RUN] for i in range(0, max(1, len(qp) - 1), MAX_VERT_RUN - 1)] if not area else [qp]
        if area and len(qp) > MAX_VERT_RUN:
            sys.exit(f"tesela {c},{f}: área {nombre} con {len(qp)} vértices")
        tramo = (ids[ta] + 1 if ta else 0) | (ids[tb] + 1 if tb else 0) << 12
        for tr in trozos:
            xs, ys = [p[0] for p in tr], [p[1] for p in tr]
            R += [len(tr) | ids[nombre] << 12 | clase << 22 | area << 24,
                  min(xs) | min(ys) << 12, max(xs) | max(ys) << 12, tramo]
            V += [x | y << 12 for x, y in tr]
            if not area:
                lados[2 if ta and tb else 1 if ta or tb else 0] += 1
    P, H = [], []
    for p in sorted(t["portales"], key=lambda p: (p["calle"], p["x"], p["y"])):
        if p["calle"] not in ids:
            continue  # su calle no pasa por esta tesela: el reloj nunca lo pediría aquí
        if p["suf"] not in sufijos:
            sufijos[p["suf"]] = len(sufijos)
            if len(sufijos) > MAX_SUFIJOS + 1:
                sys.exit(f"más de {MAX_SUFIJOS} sufijos de portal distintos en la región")
        P.append(q(p["x"], ox) | q(p["y"], oy) << 12)
        H.append(min(p["num"], 0xFFF) | sufijos[p["suf"]] << 12 | ids[p["calle"]] << 21)
    lista = [FORMATO, calles_runs, R, V, P, H]
    est = dict(runs=len(R) // 4, vert=len(V), portales=len(P), nombres=len(calles_runs), lados=lados,
               nums=len(R) + len(V) + len(P) + len(H),
               bytes_nombres=sum(len(n.encode()) for n in calles_runs))
    # Calibrado con la tesela más pesada real (MemoriaTest, 2026-10-23: 50.000 B para 3.819 números
    # y 119 nombres): ~11 B por número y ~60 B por nombre. La espiga de la fase 0 daba la mitad.
    est["heap"] = int(11 * est["nums"] + 60 * len(calles_runs))
    return lista, est


# ---------------------------------------------------------------- salida


def mc_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def nombre_modulo(region):
    return "Region" + "".join(p.capitalize() for p in re.split(r"[^A-Za-z0-9]+", region) if p)


def escribir(region, cfg, proy, vias, portales, teselas, cols, filas, fecha_osm, cuenta, sin_pareja, por_lugar,
             parroquias, lugares, fecha_zonas, fuentes, pois):
    """Todo lo de la región bajo resources-gen/<region>/ (ids de recurso con su prefijo, para que convivan
    varias en la app) y su módulo source-gen/Region<Nombre>.mc. Luego rehace lo común a todas."""
    pref = cfg["prefijo"]
    rdir = res_gen() / region
    for sub in ("t", "z"):
        (rdir / sub).mkdir(parents=True, exist_ok=True)
        for viejo in (rdir / sub).glob("*.json"):
            viejo.unlink()
    sufijos = {"": 0}
    xml = ["<jsonDataResources>"]
    idx = [None] * (cols * filas)
    stats = {}
    for (c, f) in sorted(teselas, key=lambda cf: (cf[1], cf[0])):
        t = teselas[(c, f)]
        if not t["runs"]:
            continue
        lista, est = empaquetar(c, f, t, sufijos)
        if not lista[2]:
            continue
        i = f * cols + c
        (rdir / "t" / f"t{i}.json").write_text(json.dumps(lista, ensure_ascii=False, separators=(",", ":")), "utf-8")
        est["json"] = (rdir / "t" / f"t{i}.json").stat().st_size
        xml.append(f'    <jsonData id="{pref}t{i}" filename="t/t{i}.json"/>')
        idx[i] = f"t{i}"
        stats[i] = est
    mayor = max(stats, key=lambda i: stats[i]["heap"])
    suf = [s for s, _ in sorted(sufijos.items(), key=lambda kv: kv[1])]

    zcols, zfilas = math.ceil(proy.ancho / ZONA), math.ceil(proy.alto / ZONA)
    G = rasterizar(parroquias, zcols, zfilas, cuenta)
    zidx, zstats = [None] * (zcols * zfilas), {}
    for zf in range(zfilas):
        for zc in range(zcols):
            lista, est = empaquetar_zona(zc, zf, G, parroquias, lugares)
            if lista is None:
                continue
            i = zf * zcols + zc
            (rdir / "z" / f"z{i}.json").write_text(json.dumps(lista, ensure_ascii=False, separators=(",", ":")), "utf-8")
            est["json"] = (rdir / "z" / f"z{i}.json").stat().st_size
            xml.append(f'    <jsonData id="{pref}z{i}" filename="z/z{i}.json"/>')
            zidx[i] = f"z{i}"
            zstats[i] = est
    zmayor = max(zstats, key=lambda i: zstats[i]["heap"])

    # Hospitales y comisarías: [FORMATO, N, D, X, Y, T] en metros enteros de región.
    poi = [FORMATO, [p[0] for p in pois], [p[1] for p in pois], [p[2] for p in pois], [p[3] for p in pois],
           [p[4] for p in pois]]
    (rdir / "poi.json").write_text(json.dumps(poi, ensure_ascii=False, separators=(",", ":")), "utf-8")
    xml.append(f'    <jsonData id="{pref}poi" filename="poi.json"/>')
    xml.append("</jsonDataResources>")
    (rdir / f"{region}.xml").write_text("\n".join(xml) + "\n", "utf-8")

    zbarrio = cfg["zonas"]["poligono"] == "barrio"
    meta = dict(region=region, id=cfg["id"], prefijo=pref, etiqueta=cfg["etiqueta"], datos=fecha_osm, formato=FORMATO,
                fuentes=fuentes, bbox=cfg["bbox"],
                lat_min=proy.lat_min, lon_min=proy.lon_min, kx=proy.kx, ky=proy.ky, tesela=TESELA, buf=BUF,
                maxd=MAXD, portal_r=PORTAL_R, cols=cols, filas=filas, pen=PEN, suf=suf, idx=idx, t_mayor=f"t{mayor}",
                zonas=fecha_zonas, zona=ZONA, rcel=RCEL, rn=RN, zmargen=ZMARGEN, lugar_r=LUGAR_R, barrio_r=BARRIO_R,
                barrio_frac=BARRIO_FRAC, zbarrio=zbarrio,
                zcols=zcols, zfilas=zfilas, zidx=zidx, z_mayor=f"z{zmayor}", npoi=len(pois),
                control=cfg.get("control"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"meta-{region}{sufijo()}.json").write_text(json.dumps(meta, ensure_ascii=False), "utf-8")
    geom = dict(calles=[dict(n=v["nombre"], c=v["clase"], a=int(v["area"]), t=list(v["tramo"]),
                             p=[[round(x, 2), round(y, 2)] for x, y in v["pts"]]) for v in vias],
                portales=[[round(p["x"], 2), round(p["y"], 2), p["calle"], p["num"], p["suf"]] for p in portales],
                parroquias=[dict(n=p["nombre"], r=[[[round(x, 1), round(y, 1)] for x, y in a] for a in p["anillos"]])
                            for p in parroquias],
                lugares=[[round(l["x"], 1), round(l["y"], 1), l["tipo"], l["nombre"]] for l in lugares],
                poi=pois)
    (OUT / f"geom-{region}{sufijo()}.json").write_text(json.dumps(geom, ensure_ascii=False, separators=(",", ":")), "utf-8")

    def filas_de(ix, nc, nf):
        return ("," + chr(10)).join("            " + ", ".join(
            f"Rez.JsonData.{pref}{ix[f * nc + c]}" if ix[f * nc + c] else "null" for c in range(nc)) for f in range(nf))

    mod = nombre_modulo(region)
    mc = f"""import Toybox.Lang;

// GENERADO por tools/build_callejero.py ({region}, datos OSM {fecha_osm}). No editar a mano.
// Los índices se construyen al llamar a datos(): solo la región activa ocupa memoria.
module {mod} {{
    // En el orden de Callejero.activar().
    function datos() as Array {{
        return [
            {mc_str(region)}, {mc_str(cfg["etiqueta"])}, {mc_str(fecha_osm)}, {mc_str(fuentes)},
            {proy.lat_min!r}d, {proy.lon_min!r}d, {proy.kx:.6f}d, {proy.ky:.6f}d,
            {TESELA}, {cols}, {filas}, {len(stats)},
            [{", ".join(mc_str(s) for s in suf)}] as Array<String>,
            // Una entrada por celda de {TESELA} m, fila a fila desde el sur; null = sin calles.
            [
{filas_de(idx, cols, filas)}
            ] as Array<ResourceId or Null>,
            Rez.JsonData.{pref}t{mayor},
            {zcols}, {zfilas},
            // Zonas de {ZONA} m: {"barrio oficial (polígono) y lugar" if zbarrio else "parroquia (polígono), lugar y barrio (nodos)"}.
            [
{filas_de(zidx, zcols, zfilas)}
            ] as Array<ResourceId or Null>,
            Rez.JsonData.{pref}z{zmayor},
            Rez.JsonData.{pref}poi,
            {"true" if zbarrio else "false"}
        ] as Array;
    }}
}}
"""
    src_gen().mkdir(exist_ok=True)
    (src_gen() / f"{mod}.mc").write_text(mc, "utf-8")
    escribir_comun(recien=(rdir, src_gen() / f"{mod}.mc", OUT / f"meta-{region}{sufijo()}.json"))
    informe(region, proy, vias, portales, stats, cols, filas, fecha_osm, cuenta, sin_pareja, por_lugar, suf, mayor,
            zstats, zcols, zfilas, zmayor, parroquias, lugares, fecha_zonas, pois)


def escribir_comun(recien=None):
    """source-gen/Callejero.mc (constantes del generador y la región activa), source-gen/Regiones.mc (las
    regiones que hay en resources-gen/) y el ajuste «Zona» del teléfono (resources-gen/ajustes/)."""
    regiones = json.loads((TOOLS / "regiones.json").read_text("utf-8"))
    metas = []
    for nombre, cfg in regiones.items():
        f = OUT / f"meta-{nombre}{sufijo()}.json"
        if (res_gen() / nombre / f"{nombre}.xml").exists() and f.exists():
            metas.append(json.loads(f.read_text("utf-8")))
    metas.sort(key=lambda m: m["id"])
    assert len({m["id"] for m in metas}) == len(metas), "dos regiones con el mismo id"
    recursos = sum(sum(1 for v in m["idx"] if v) + sum(1 for v in m["zidx"] if v) + 1 for m in metas)
    print(f"Recursos de datos ({VARIANTE}): {recursos}"
          + (f" de {TOPE_RECURSOS_6X} posibles en el fēnix 6X" if VARIANTE == "6x" else ""))
    zonas = {(m["zona"], m["rn"]) for m in metas}
    if len(zonas) > 1:
        sys.exit(f"Las regiones de la variante {VARIANTE} tienen zonas de tamaños distintos {zonas}: Callejero.ZONA es una.")
    zona, rn = zonas.pop() if zonas else (ZONA, RN)
    if VARIANTE == "6x" and recursos > TOPE_RECURSOS_6X:
        if recien:
            # Se retira lo que se acaba de escribir: con ello dentro, el 6X no compilaría.
            import shutil
            rdir, modulo, meta = recien
            shutil.rmtree(rdir, ignore_errors=True)
            for f in (modulo, meta):
                if f.exists():
                    f.unlink()
        sys.exit(f"La variante 6x pasa del tope: {recursos} recursos > {TOPE_RECURSOS_6X}. Agrande la tesela o la zona "
                 "de alguna región (\"compacta\" en tools/regiones.json) o quite distritos.")
    cal = f"""import Toybox.Lang;

// GENERADO por tools/build_callejero.py. No editar a mano.
// Constantes del generador (iguales en todas las regiones) y la región activa, que fija activar().
module Callejero {{
    const FORMATO = {FORMATO};
    const BUF = {BUF};
    const MAXD = {MAXD};
    const PORTAL_R = {PORTAL_R};
    const PEN = {PEN} as Array<Number>;
    const ZONA = {zona};
    const RCEL = {RCEL};
    const RN = {rn};
    const ZMARGEN = {ZMARGEN};
    const LUGAR_R = {LUGAR_R};
    const BARRIO_R = {BARRIO_R};
    const BARRIO_FRAC = {BARRIO_FRAC};

    var ID as Number = 0;                 // 0 = ninguna activa todavía
    var REGION as String = "";
    var ETIQUETA as String = "";
    var DATOS as String = "";
    var FUENTES as String = "";
    var LAT_MIN as Double = 0.0d;
    var LON_MIN as Double = 0.0d;
    var KX as Double = 1.0d;
    var KY as Double = 1.0d;
    var TESELA as Number = {TESELA};
    var COLS as Number = 0;
    var FILAS as Number = 0;
    var NTESELAS as Number = 0;
    var SUF as Array<String> = [""] as Array<String>;
    var IDX as Array<ResourceId or Null> = [] as Array<ResourceId or Null>;
    var T_MAYOR as ResourceId or Null = null;
    var ZCOLS as Number = 0;
    var ZFILAS as Number = 0;
    var ZIDX as Array<ResourceId or Null> = [] as Array<ResourceId or Null>;
    var Z_MAYOR as ResourceId or Null = null;
    var POI as ResourceId or Null = null;
    var ZBARRIO as Boolean = false;       // el polígono de las zonas es el barrio (Madrid), no la parroquia

    // Sin región activa (los tests miden así lo que ocupan los índices de cada una).
    function soltar() as Void {{
        IDX = [] as Array<ResourceId or Null>;
        ZIDX = [] as Array<ResourceId or Null>;
        ID = 0;
    }}

    // d: lo que devuelve Region<Nombre>.datos(). Suelta los índices de la anterior antes de crear los nuevos.
    function activar(id as Number, d as Array) as Void {{
        soltar();
        ID = id;
        REGION = d[0] as String;
        ETIQUETA = d[1] as String;
        DATOS = d[2] as String;
        FUENTES = d[3] as String;
        LAT_MIN = d[4] as Double;
        LON_MIN = d[5] as Double;
        KX = d[6] as Double;
        KY = d[7] as Double;
        TESELA = d[8] as Number;
        COLS = d[9] as Number;
        FILAS = d[10] as Number;
        NTESELAS = d[11] as Number;
        SUF = d[12] as Array<String>;
        IDX = d[13] as Array<ResourceId or Null>;
        T_MAYOR = d[14] as ResourceId;
        ZCOLS = d[15] as Number;
        ZFILAS = d[16] as Number;
        ZIDX = d[17] as Array<ResourceId or Null>;
        Z_MAYOR = d[18] as ResourceId;
        POI = d[19] as ResourceId;
        ZBARRIO = d[20] as Boolean;
    }}
}}
"""
    (src_gen() / "Callejero.mc").write_text(cal, "utf-8")
    casos = "\n".join(f"""        {"if" if k == 0 else "} else if"} (id == {m['id']}) {{
            return {nombre_modulo(m['region'])}.datos();""" for k, m in enumerate(metas))
    cajas = ",\n".join(f"        {m['bbox'][0]!r}d, {m['bbox'][1]!r}d, {m['bbox'][2]!r}d, {m['bbox'][3]!r}d"
                       for m in metas)
    reg = f"""import Toybox.Lang;

// GENERADO por tools/build_callejero.py con las regiones de resources-gen/. No editar a mano.
module Regiones {{
    // Id estable de cada región (es el valor del ajuste «Zona»; 0 = automática) y su nombre.
    const IDS = [{", ".join(str(m["id"]) for m in metas)}] as Array<Number>;
    const ETIQUETAS = [{", ".join(mc_str(m["etiqueta"]) for m in metas)}] as Array<String>;
    // Caja de cada una (sur, oeste, norte, este), en grados: la automática elige la que contiene la posición.
    const CAJAS = [
{cajas}
    ] as Array<Double>;

    function datos(id as Number) as Array or Null {{
{casos}
        }}
        return null;
    }}
}}
"""
    (src_gen() / "Regiones.mc").write_text(reg, "utf-8")

    # Ajuste del teléfono (solo en la versión de la tienda): la misma lista que el menú del reloj.
    adir = res_gen() / "ajustes"
    adir.mkdir(parents=True, exist_ok=True)
    (adir / "propiedades.xml").write_text("""<resources>
    <properties>
        <property id="zona" type="number">0</property>
    </properties>
</resources>
""", "utf-8")
    entradas = "\n".join(f'            <listEntry value="{m["id"]}">@Strings.Zona{m["id"]}</listEntry>' for m in metas)
    (adir / "ajustes.xml").write_text(f"""<resources>
    <settings>
        <setting propertyKey="@Properties.zona" title="@Strings.AjusteZona">
            <settingConfig type="list">
                <listEntry value="0">@Strings.Zona0</listEntry>
{entradas}
            </settingConfig>
        </setting>
    </settings>
</resources>
""", "utf-8")
    cadenas = "\n".join(f'    <string id="Zona{m["id"]}">{m["etiqueta"]}</string>' for m in metas)
    (adir / "cadenas.xml").write_text(f"""<strings>
    <string id="AjusteZona">Zona del callejero</string>
    <string id="Zona0">Automática (según la posición)</string>
{cadenas}
</strings>
""", "utf-8")
    print(f"Regiones en la app: {', '.join(m['etiqueta'] for m in metas)}")


def informe(region, proy, vias, portales, stats, cols, filas, fecha_osm, cuenta, sin_pareja, por_lugar, suf, mayor,
            zstats, zcols, zfilas, zmayor, parroquias, lugares, fecha_zonas, pois):
    L = [f"Callejero {region} — datos OSM {fecha_osm} — generado {date.today().isoformat()}",
         f"Región {proy.ancho / 1000:.1f} × {proy.alto / 1000:.1f} km; rejilla {cols} × {filas} de {TESELA} m "
         f"(margen {BUF} m, MAXD {MAXD} m, portal {PORTAL_R} m)", ""]
    L.append("Recuento:")
    for k, v in sorted(cuenta.items()):
        L.append(f"  {k:<34} {v:>7}")
    L.append(f"  {'trozos de calle tras cortar':<34} {len(vias):>7}")
    L.append(f"  {'nombres distintos':<34} {len({v['nombre'] for v in vias}):>7}")
    L.append(f"  {'portales finales':<34} {len(portales):>7}")
    L.append(f"  {'sufijos distintos':<34} {len(suf):>7}")
    emp = sum(v for k, v in cuenta.items() if k.startswith("portal emparejado"))
    tot = emp + cuenta["portal sin pareja"]
    if tot:
        L.append(f"  emparejados {emp}/{tot} = {100 * emp / tot:.1f} %")
    L += ["", "addr:street sin pareja (las 40 más frecuentes; candidatas a overrides):"]
    for k, v in sin_pareja.most_common(40):
        L.append(f"  {v:>4}  {k}")
    if por_lugar:
        L += ["", f"Portales con addr:place en vez de addr:street (no se usan): {sum(por_lugar.values())}"]
        for k, v in por_lugar.most_common(10):
            L.append(f"  {v:>4}  {k}")
    lados = sum((s["lados"] for s in stats.values()), Counter())
    tot = sum(lados.values())
    L += ["", f"Tramo de las tiradas lineales de las teselas ({tot}): completo {100 * lados[2] / tot:.1f} % · "
              f"un solo lado {100 * lados[1] / tot:.1f} % · ninguno {100 * lados[0] / tot:.1f} %"]
    zh = sorted(s["heap"] for s in zstats.values())
    celdas = len(zstats) * RN * RN
    L += ["", f"Zonas (datos OSM {fecha_zonas}): {len(zstats)} de {zcols * zfilas} celdas de {ZONA} m; "
              f"{len(parroquias)} parroquias, {sum(l['tipo'] & 1 for l in lugares)} lugares poblados, "
              f"{sum(l['tipo'] >> 2 & 1 for l in lugares)} parajes, {sum(l['tipo'] >> 1 & 1 for l in lugares)} barrios",
          f"  raster de {RCEL} m con parroquia: {100 * sum(s['con_parroquia'] for s in zstats.values()) / celdas:.1f} % "
          f"de las celdas de las zonas",
          f"  heap estimado por zona: máx {zh[-1] / 1024:.1f} KB (Z_MAYOR = z{zmayor}, {zstats[zmayor]['lugares']} lugares) · "
          f"media {sum(zh) / len(zh) / 1024:.1f} KB; JSON total {sum(s['json'] for s in zstats.values()) / 1024:.0f} KB"]
    hs = sorted(s["heap"] for s in stats.values())
    js = sum(s["json"] for s in stats.values())
    L += ["", f"Teselas con calles: {len(stats)} de {cols * filas}; JSON total {js / 1024:.0f} KB",
          f"Heap estimado por tesela: máx {hs[-1] / 1024:.1f} KB · p95 {hs[int(.95 * len(hs))] / 1024:.1f} KB · "
          f"media {sum(hs) / len(hs) / 1024:.1f} KB (T_MAYOR = t{mayor})", "", "Las 10 más pesadas:"]
    for i in sorted(stats, key=lambda i: -stats[i]["heap"])[:10]:
        s = stats[i]
        c, f = i % cols, i // cols
        lat, lon = proy.latlon((c + .5) * TESELA, (f + .5) * TESELA)
        L.append(f"  t{i:<5} {lat:.5f},{lon:.5f}  heap~{s['heap'] / 1024:5.1f} KB  json {s['json'] / 1024:5.1f} KB  "
                 f"runs {s['runs']:>4} vért {s['vert']:>5} portales {s['portales']:>4} nombres {s['nombres']:>3}")

    tipos = Counter(p[4] for p in pois)
    L += ["", f"Hospitales y comisarías: {len(pois)} — " + ", ".join(f"{POI_ETIQUETA[t]} {n}" for t, n in sorted(tipos.items())),
          f"  sin dirección: {sum(1 for p in pois if not p[1])}"]

    def mapa(titulo, fn):
        L.extend(["", titulo + " (norte arriba):"])
        for f in range(filas - 1, -1, -1):
            L.append("  " + "".join(fn(stats.get(f * cols + c)) for c in range(cols)))

    mapa("Densidad de vértices  (. <200  : <800  # ≥800)",
         lambda s: " " if not s else "." if s["vert"] < 200 else ":" if s["vert"] < 800 else "#")
    mapa("Portales  (· ninguno  . <20  : <100  # ≥100)",
         lambda s: " " if not s else "·" if s["portales"] == 0 else "." if s["portales"] < 20 else
         ":" if s["portales"] < 100 else "#")
    texto = "\n".join(L) + "\n"
    (OUT / f"informe-{region}{sufijo()}.txt").write_text(texto, "utf-8")
    print("\n".join(L[:len(L) if len(L) < 40 else 30]))
    print(f"… informe completo en tools/out/informe-{region}{sufijo()}.txt")


def caja_distritos(region, cfg, distritos, margen_m, refresh):
    """Caja (sur, oeste, norte, este) que envuelve los distritos dados (polígonos del nivel padre de las
    zonas, admin_level 9 en Madrid) más margen_m: la región compacta de un fēnix 6X que no cabe entera."""
    dz = descargar(region, consulta_zonas(cfg["bbox"], tuple(cfg["zonas"]["admin_level"]), bool(cfg.get("grande"))),
                   refresh)
    nivel = cfg["zonas"]["admin_level"][0]
    # Cada distrito, por id de relación de OSM (número) o por nombre; un nombre que se repite (hay «Centro»
    # en Getafe y en Leganés) hay que darlo por id.
    rels = [e for e in dz["elements"] if e["type"] == "relation" and e.get("tags", {}).get("admin_level") == nivel]
    elegidas = []
    for d in distritos:
        if isinstance(d, int):
            cand = [e for e in rels if e["id"] == d]
        else:
            cand = [e for e in rels if sin_tildes(e["tags"].get("name", "")).lower() == sin_tildes(d).lower()]
        if len(cand) != 1:
            sys.exit(f"Distrito {d!r}: {len(cand)} relaciones con ese nombre o id "
                     f"({', '.join(str(e['id']) for e in cand)}); dé el id en tools/regiones.json.")
        elegidas.append(cand[0])
    lats, lons = [], []
    for e in elegidas:
        for m in e.get("members", []):
            for g in m.get("geometry") or []:
                if g:
                    lats.append(g["lat"])
                    lons.append(g["lon"])
    dlat = margen_m / 111132.0
    dlon = margen_m / (111320.0 * math.cos(math.radians((min(lats) + max(lats)) / 2)))
    return [round(min(lats) - dlat, 5), round(min(lons) - dlon, 5), round(max(lats) + dlat, 5), round(max(lons) + dlon, 5)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--region", default="santiago")
    ap.add_argument("--refresh", action="store_true", help="vuelve a descargar de Overpass")
    ap.add_argument("--comun", action="store_true", help="solo rehace Callejero.mc, Regiones.mc y el ajuste")
    ap.add_argument("--variante", choices=("normal", "6x"), default="normal",
                    help="6x: datos compactos para el fēnix 6X (resources-gen-6x/, source-gen-6x/)")
    a = ap.parse_args()
    global VARIANTE, TESELA, ZONA, RN
    VARIANTE = a.variante
    if a.comun:
        escribir_comun()
        return
    regiones = json.loads((TOOLS / "regiones.json").read_text("utf-8"))
    cfg = dict(regiones[a.region])
    grande = bool(cfg.get("grande"))
    overrides = json.loads((TOOLS / cfg["overrides"]).read_text("utf-8"))
    bbox_datos = cfg["bbox"]            # la descarga es siempre la de la región entera (y su caché)
    if VARIANTE == "6x":
        comp = cfg.get("compacta")
        if not comp:
            sys.exit(f"La región {a.region} no tiene \"compacta\" en tools/regiones.json: no va en el fēnix 6X.")
        TESELA, ZONA = comp["tesela"], comp["zona"]
        RN = ZONA // RCEL
        assert TESELA + 2 * BUF < 4096 and RN * RN % 4 == 0 and ZONA + 2 * ZMARGEN < 1 << 13
        if comp.get("distritos"):
            cfg["bbox"] = caja_distritos(a.region, cfg, comp["distritos"], comp.get("margen_m", 500), a.refresh)
            cfg["etiqueta"] = comp.get("etiqueta", cfg["etiqueta"])
        print(f"Variante 6x de {a.region}: teselas de {TESELA} m, zonas de {ZONA} m, caja {cfg['bbox']}")
    proy = Proy(cfg["bbox"])
    d = (descargar_por_partes(a.region, bbox_datos, cfg["partes"], a.refresh) if cfg.get("partes")
         else descargar(a.region, consulta(bbox_datos, grande), a.refresh))
    fecha_osm = (d.get("osm3s", {}).get("timestamp_osm_base") or "")[:10] or date.today().isoformat()
    elems = d["elements"]
    del d
    cuenta, sin_pareja, por_lugar = Counter(), Counter(), Counter()
    vias = extraer_vias(elems, proy, overrides, cuenta)
    variantes = unificar_variantes(vias, cuenta)
    (OUT / f"variantes-{a.region}{sufijo()}.txt").write_text(
        "Nombres unificados (vías  viejo → nuevo  en lat,lon), build_callejero.unificar_variantes\n" +
        "".join(f"{n:>4}  {v} → {c}  en {'%.5f,%.5f' % proy.latlon(*pt)}\n"
                for (v, c), (n, pt) in sorted(variantes.items(), key=lambda x: (-x[1][0], x[0]))),
        "utf-8")
    lineales = [v for v in vias if not v["area"]]
    # Los portales se casan con las vías enteras (como en la v1); se teselan los trozos.
    portales = extraer_portales(elems, proy, lineales + [v for v in vias if v["area"]], overrides, cuenta,
                                sin_pareja, por_lugar)
    del elems
    fuentes = "OSM"
    if cfg.get("catastro"):
        dirs = descargar_catastro(a.region, cfg["catastro"], a.refresh)
        portales, n = completar_con_catastro(dirs, proy, lineales + [v for v in vias if v["area"]], portales, cuenta)
        if n:
            fuentes = "OSM + Catastro"
    if cfg.get("portales_ayto_madrid"):
        dirs = leer_ayto_madrid(CACHE / cfg["portales_ayto_madrid"])
        portales, n = completar_con_ayto(dirs, proy, lineales + [v for v in vias if v["area"]], portales, cuenta)
        if n:
            fuentes = "OSM + Ayto. Madrid"
    # El número va en 12 bits (≤ 4095): lo que pasa de ahí son kilómetros o errores de etiquetado.
    cuenta["portal con número > 4095 (fuera)"] += sum(1 for p in portales if p["num"] > 0xFFF)
    portales = [p for p in portales if p["num"] <= 0xFFF]
    dp = descargar(a.region, consulta_poi(bbox_datos, grande), a.refresh)
    pois = extraer_poi(dp["elements"], proy, vias, portales, overrides, cuenta, proy.ancho, proy.alto)
    trozos = trocear(vias, cuenta)
    dz = descargar(a.region, consulta_zonas(bbox_datos, tuple(cfg["zonas"]["admin_level"]), grande), a.refresh)
    fecha_zonas = (dz.get("osm3s", {}).get("timestamp_osm_base") or "")[:10] or date.today().isoformat()
    parroquias, lugares = extraer_zonas(dz["elements"], proy, overrides, cuenta, cfg["zonas"])
    teselas, cols, filas = teselar(trozos, portales, proy)
    escribir(a.region, cfg, proy, trozos, portales, teselas, cols, filas, fecha_osm, cuenta, sin_pareja, por_lugar,
             parroquias, lugares, fecha_zonas, fuentes, pois)


if __name__ == "__main__":
    main()
