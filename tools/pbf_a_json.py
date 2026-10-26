#!/usr/bin/env python3
"""Extracto .osm.pbf (Geofabrik) → las tres respuestas de Overpass que lee build_callejero.py.

    .venv/bin/python tools/pbf_a_json.py --region galicia

Para regiones demasiado grandes para Overpass (Galicia entera, 2026-10-25: el servidor público devolvía 502 una
y otra vez, y las 16 partes de las parroquias no terminaban de bajar). Lee el fichero "pbf" de la región en
tools/regiones.json (relativo a tools/cache/) y escribe en tools/cache/:
    pbf-<region>-calles.json   lo de consulta(): vías con nombre, plazas, peatonales, portales y entradas
    pbf-<region>-zonas.json    lo de consulta_zonas(): relaciones administrativas de los niveles de la región
                               y los lugares con nombre
    pbf-<region>-poi.json      lo de consulta_poi(): hospitales y comisarías, con su centro
Con el mismo formato que «out geom» y «out center tags» de Overpass: vías con "nodes" y "geometry",
relaciones con "members" (y la "geometry" de cada vía miembro), centros como el de Overpass (el de la caja).
Sin la caja de la región: el extracto ya viene recortado al polígono de la comunidad. Con "pbf_recorte"
en la región (Barcelona, del extracto de Cataluña), se queda solo lo que toca su caja. Con "pbf_poligono"
(Comunitat Valenciana, 2026-10-26), se queda solo lo que toca el polígono de su relación "area_osm", sacado del
propio extracto: el de Geofabrik lleva un borde de lugares y términos de las provincias vecinas (Murcia, Teruel,
Cuenca, Albacete, Tarragona). Las vías y portales cuentan si tienen un nodo dentro, como el filtro de área de
Overpass; los términos (que comparten la frontera con el vecino y en la costa se meten en el mar), si más de la
mitad de su superficie cae dentro (rejilla de 40 × 40 puntos sobre su caja).

Necesita pyosmium (`python3 -m venv .venv && .venv/bin/pip install osmium`); el generador sigue siendo
solo biblioteca estándar.
"""
import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import osmium

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "tools" / "cache"
sys.path.insert(0, str(ROOT / "tools"))
from build_callejero import BARRIO_TIPOS, LUGAR_TIPOS, PARAJE_TIPOS, unir_anillos  # noqa: E402

MAYOR_REF = re.compile(r"^(motorway|trunk|primary|secondary|tertiary)(_link)?$")
PLACE = LUGAR_TIPOS | PARAJE_TIPOS | BARRIO_TIPOS


def es_calle_way(t):
    hw = t.get("highway")
    return bool((hw and ("name" in t or (MAYOR_REF.match(hw) and "ref" in t)))
                or t.get("place") == "square" or "addr:housenumber" in t)


def es_calle_rel(t):
    return bool(t.get("place") == "square" or (t.get("type") == "multipolygon" and t.get("highway") == "pedestrian")
                or "addr:housenumber" in t)


def es_poi(t):
    return t.get("amenity") in ("police", "hospital")


class Relaciones(osmium.SimpleHandler):
    """Primera pasada: las relaciones que interesan y las vías miembro cuya geometría hará falta."""

    def __init__(self, niveles, area=None):
        super().__init__()
        self.niveles = niveles
        self.rels = {"calles": [], "zonas": [], "poi": []}
        self.miembros = set()
        self.region, self.borde = area, []    # "pbf_poligono": la relación de la región y sus vías exteriores

    def relation(self, r):
        t = dict(r.tags)
        if r.id == self.region:
            self.borde = [m.ref for m in r.members if m.type == "w" and m.role in ("outer", "")]
            self.miembros.update(self.borde)
        destinos = []
        if es_calle_rel(t):
            destinos.append("calles")
        if t.get("boundary") == "administrative" and t.get("admin_level") in self.niveles:
            destinos.append("zonas")
        if es_poi(t):
            destinos.append("poi")
        if not destinos:
            return
        e = {"type": "relation", "id": r.id, "tags": t,
             "members": [{"type": {"n": "node", "w": "way", "r": "relation"}[m.type], "ref": m.ref, "role": m.role}
                         for m in r.members]}
        for m in e["members"]:
            if m["type"] == "way":
                self.miembros.add(m["ref"])
        for d in destinos:
            self.rels[d].append(e)


class Resto(osmium.SimpleHandler):
    """Segunda pasada, con las posiciones de los nodos: nodos, vías y la geometría de las vías miembro."""

    def __init__(self, miembros):
        super().__init__()
        self.miembros = miembros
        self.geom = {}
        self.out = {"calles": [], "zonas": [], "poi": []}

    def node(self, n):
        t = dict(n.tags)
        if not t or not n.location.valid():
            return
        e = None

        def el():
            return {"type": "node", "id": n.id, "lat": round(n.location.lat, 7), "lon": round(n.location.lon, 7),
                    "tags": t}
        if "addr:housenumber" in t or "entrance" in t:
            e = el()
            self.out["calles"].append(e)
        if t.get("place") in PLACE and "name" in t:
            self.out["zonas"].append(e or el())
        if es_poi(t):
            self.out["poi"].append(e or el())

    def way(self, w):
        t = dict(w.tags)
        calle, poi, miembro = es_calle_way(t), es_poi(t), w.id in self.miembros
        if not (calle or poi or miembro):
            return
        geo = [{"lat": round(nd.location.lat, 7), "lon": round(nd.location.lon, 7)} if nd.location.valid() else None
               for nd in w.nodes]
        if miembro:
            self.geom[w.id] = geo
        if calle:
            self.out["calles"].append({"type": "way", "id": w.id, "nodes": [nd.ref for nd in w.nodes],
                                       "geometry": geo, "tags": t})
        if poi:
            c = centro(geo)
            if c:
                self.out["poi"].append({"type": "way", "id": w.id, "center": c, "tags": t})


class Poligono:
    """Punto dentro de los anillos (lon, lat), par-impar. Celdas de paso grados: las que no cruza ninguna arista
    se clasifican una vez por su centro; en las demás, el rayo solo con las aristas de su fila."""

    def __init__(self, anillos, paso=0.01):
        self.filas, self.borde, self.memo = defaultdict(list), set(), {}
        self.PASO = p = paso
        for a in anillos:
            for (x0, y0), (x1, y1) in zip(a, a[1:]):
                for f in range(math.floor(min(y0, y1) / p), math.floor(max(y0, y1) / p) + 1):
                    self.filas[f].append((x0, y0, x1, y1))
                n = int(max(abs(x1 - x0), abs(y1 - y0)) / (p / 4)) + 1
                for k in range(n + 1):
                    self.borde.add((math.floor((x0 + k / n * (x1 - x0)) / p), math.floor((y0 + k / n * (y1 - y0)) / p)))

    def _rayo(self, x, y):
        c = False
        for x0, y0, x1, y1 in self.filas.get(math.floor(y / self.PASO), ()):
            if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
                c = not c
        return c

    def dentro(self, g):
        if not g:
            return False
        return self.dentro_xy(g["lon"], g["lat"])

    def dentro_xy(self, x, y):
        cel = (math.floor(x / self.PASO), math.floor(y / self.PASO))
        if cel in self.borde:
            return self._rayo(x, y)
        if cel not in self.memo:
            self.memo[cel] = self._rayo((cel[0] + .5) * self.PASO, (cel[1] + .5) * self.PASO)
        return self.memo[cel]


def centro(geo):
    """El de Overpass («out center»): el centro de la caja."""
    g = [p for p in geo if p]
    if not g:
        return None
    la, lo = [p["lat"] for p in g], [p["lon"] for p in g]
    return {"lat": round((min(la) + max(la)) / 2, 7), "lon": round((min(lo) + max(lo)) / 2, 7)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--region", required=True)
    a = ap.parse_args()
    cfg = json.loads((ROOT / "tools" / "regiones.json").read_text("utf-8"))[a.region]
    pbf = CACHE / cfg["pbf"]
    m = re.search(r"-(\d{2})(\d{2})(\d{2})\.osm\.pbf$", pbf.name)
    fecha = f"20{m.group(1)}-{m.group(2)}-{m.group(3)}T00:00:00Z" if m else None
    niveles = set(cfg["zonas"]["admin_level"])

    area = cfg.get("area_osm") if cfg.get("pbf_poligono") else None
    r = Relaciones(niveles, area)
    r.apply_file(str(pbf))
    if area and not r.borde:
        sys.exit(f"pbf_poligono: la relación {area} no está en {pbf.name}")
    print(f"relaciones: {', '.join(f'{k} {len(v)}' for k, v in r.rels.items())}; {len(r.miembros)} vías miembro")
    o = Resto(r.miembros)
    o.apply_file(str(pbf), locations=True, idx="flex_mem")

    for destino, rels in r.rels.items():
        for e in rels:
            geo_rel = []
            for mm in e["members"]:
                if mm["type"] == "way" and mm["ref"] in o.geom:
                    mm["geometry"] = o.geom[mm["ref"]]
                    geo_rel += mm["geometry"]
            if destino == "poi":
                c = centro(geo_rel)
                if c:
                    o.out["poi"].append({"type": "relation", "id": e["id"], "center": c, "tags": e["tags"]})
            else:
                o.out[destino].append(e)
    if cfg.get("pbf_recorte"):
        # Una región dentro de un extracto mayor (Barcelona en el de Cataluña): se queda lo que toca su caja.
        s_, w_, n_, e_ = cfg["bbox"]

        def dentro(g):
            return g and s_ <= g["lat"] <= n_ and w_ <= g["lon"] <= e_

        def toca(e):
            if e["type"] == "node":
                return dentro(e)
            if "center" in e:
                return dentro(e["center"])
            if e["type"] == "way":
                return any(dentro(g) for g in e.get("geometry") or [])
            return any(dentro(g) for mm in e.get("members", []) for g in mm.get("geometry") or [])
        for destino in o.out:
            antes = len(o.out[destino])
            o.out[destino] = [e for e in o.out[destino] if toca(e)]
            print(f"recorte a la caja: {destino} {antes} → {len(o.out[destino])}")
    if area:
        anillos = unir_anillos([[(g["lon"], g["lat"]) for g in o.geom.get(w) or [] if g] for w in r.borde])
        if not anillos:
            sys.exit(f"pbf_poligono: la relación {area} no forma ningún anillo cerrado")
        pol = Poligono(anillos)

        def nodos(e):
            if e["type"] == "node":
                return [e]
            if "center" in e:
                return [e["center"]]
            if e["type"] == "way":
                return [g for g in e.get("geometry") or [] if g]
            return [g for mm in e.get("members", []) for g in mm.get("geometry") or [] if g]

        def toca(e):
            if e["type"] == "relation" and e["tags"].get("boundary") == "administrative":
                propios = unir_anillos([[(g["lon"], g["lat"]) for g in mm.get("geometry") or [] if g]
                                        for mm in e["members"] if mm["type"] == "way"])
                if not propios:
                    return False
                xs, ys = [p[0] for a in propios for p in a], [p[1] for a in propios for p in a]
                x0, y0, dx, dy = min(xs), min(ys), (max(xs) - min(xs)) / 40, (max(ys) - min(ys)) / 40
                suyo = Poligono(propios, max(dx, dy, 1e-4) * 2)
                muestras = [(x0 + (i + .5) * dx, y0 + (j + .5) * dy) for i in range(40) for j in range(40)]
                muestras = [m for m in muestras if suyo.dentro_xy(*m)]
                return sum(pol.dentro_xy(*m) for m in muestras) * 2 > len(muestras)
            return any(map(pol.dentro, nodos(e)))
        print(f"polígono de la relación {area}: {len(anillos)} anillos")
        for destino in o.out:
            antes = len(o.out[destino])
            o.out[destino] = [e for e in o.out[destino] if toca(e)]
            print(f"recorte al polígono: {destino} {antes} → {len(o.out[destino])}")
    for destino, elems in o.out.items():
        f = CACHE / f"pbf-{a.region}-{destino}.json"
        f.write_text(json.dumps({"osm3s": {"timestamp_osm_base": fecha}, "elements": elems}, ensure_ascii=False,
                                separators=(",", ":")), "utf-8")
        print(f"escrito {f.relative_to(ROOT)}: {len(elems)} elementos ({f.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
