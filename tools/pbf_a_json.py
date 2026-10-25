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
Sin la caja de la región: el extracto ya viene recortado al polígono de la comunidad.

Necesita pyosmium (`python3 -m venv .venv && .venv/bin/pip install osmium`); el generador sigue siendo
solo biblioteca estándar.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import osmium

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "tools" / "cache"
sys.path.insert(0, str(ROOT / "tools"))
from build_callejero import BARRIO_TIPOS, LUGAR_TIPOS, PARAJE_TIPOS  # noqa: E402

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

    def __init__(self, niveles):
        super().__init__()
        self.niveles = niveles
        self.rels = {"calles": [], "zonas": [], "poi": []}
        self.miembros = set()

    def relation(self, r):
        t = dict(r.tags)
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

    r = Relaciones(niveles)
    r.apply_file(str(pbf))
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
    for destino, elems in o.out.items():
        f = CACHE / f"pbf-{a.region}-{destino}.json"
        f.write_text(json.dumps({"osm3s": {"timestamp_osm_base": fecha}, "elements": elems}, ensure_ascii=False,
                                separators=(",", ":")), "utf-8")
        print(f"escrito {f.relative_to(ROOT)}: {len(elems)} elementos ({f.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
