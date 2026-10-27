#!/usr/bin/env python3
"""Memoria de una app de la c5 (plan 4) con la app real en modo app: prepara su compilación de medida.

Escribe, junto al jungle de la app (tools/tienda.py, bin/tienda/<app>/), medida.jungle y medida-src/MedidaPuntos.mc.
medida.jungle es el de la app con medida/Gps.mc en lugar de source/Gps.mc: un GPS falso que lleva la app a los puntos
de MedidaPuntos, uno cada 4 s, y escribe la memoria en uso tras cada uno. Los puntos son un arranque rural, los pares
(tesela, zona) más pesados que conviven en un punto (tools/ref.py --par-mayor) y los centros de la tesela y la zona
más pesadas. Imprime la carpeta.

    python3 -I tools/medida_c5.py coruna
    python3 -I tools/medida_c5.py coruna --escalera   (en lugar de los pares: el centro de una tesela de cada KB, de 12
                                                       a 28, de menor a mayor, con la zona de ese punto)
    monkeyc -d fenix5 -f bin/tienda/coruna/medida.jungle -o bin/medida-coruna.prg -y <clave> -r -O 2 -w
    monkeydo bin/medida-coruna.prg fenix5        (sin -t: modo app; se busca «MEDIDA» y «Out Of Memory»)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import ref as R  # noqa: E402


# Escenas de la ficha de la tienda (2026-10-27, tools/ref.py --variante c5): portal a 5 m hacia la calle, o el lugar.
FICHA = {
    "coruna": [("A Coruña: Rúa Real 26", 43.37, -8.399937),
               ("Aldea: Sisto (Brates)", 43.001927, -8.200776),
               ("Santiago: Rúa do Franco 33", 42.878178, -8.545313),
               ("Ferrol: Rúa Bon Xesús 13", 43.502019, -8.198472)],
    "pontevedra": [("Vigo: Rúa Real 12", 42.239131, -8.727168),
                   ("Aldea: Buezas (Nantes)", 42.418027, -8.798312),
                   ("Pontevedra: Rúa dos Campos 19", 42.44106, -8.626043)],
}


def textos_largos(ref, tope=24000):
    """[(nombre, lat, lon)]: la calle con portal de nombre más largo, la calle con el tramo más largo y el lugar con la
    parroquia y el lugar más largos, en teselas de ≤ tope B de heap estimado."""
    g, _, _ = ref._geom()

    def ligera(x, y):
        n = ref.m["idx"][ref.celda(x, y)]
        return n and R.heap_tesela(json.loads((ref.tdir / f"{n}.json").read_text("utf-8"))) <= tope

    out = []
    for p in sorted(g["portales"], key=lambda p: -len(p[2]))[:80]:
        b = ref.buscar(p[0], p[1])
        if ligera(p[0], p[1]) and b["estado"] == "OK" and b["s1"] == p[2]:
            out.append((f"calle larga: {p[2]}", *ref.latlon(p[0], p[1])))
            break
    for c in sorted((c for c in g["calles"] if c["t"] and all(c["t"]) and not c["a"]),
                    key=lambda c: -(len(c["n"]) + sum(len(t) for t in c["t"])))[:80]:
        x, y = R._mitad(c)
        b = ref.buscar(x, y)
        if ligera(x, y) and b["estado"] == "OK" and b["s1"] == c["n"]:
            out.append((f"tramo largo: {c['n']}", *ref.latlon(x, y)))
            break
    mejor = None
    for l in g["lugares"]:
        x, y = l[0] + 30, l[1] + 30
        z = ref.zona(x, y, vista=True)
        if z and z[0] and z[1] and (mejor is None or len(z[0]) + len(z[1]) > mejor[0]) and ligera(x, y):
            mejor = (len(z[0]) + len(z[1]), f"parroquia y lugar largos: {z[0]} · {z[1]}", x, y)
    out.append((mejor[1], *ref.latlon(mejor[2], mejor[3])))
    return out


def main():
    escalera = "--escalera" in sys.argv[2:]
    primera = next((a[len("--primera="):] for a in sys.argv[2:] if a.startswith("--primera=")), None)
    capturas = "--capturas" in sys.argv[2:]
    ruta = "--ruta" in sys.argv[2:]
    ficha = "--ficha" in sys.argv[2:]
    if len(sys.argv) != 2 + escalera + bool(primera) + capturas + ruta + ficha:
        sys.exit("uso: medida_c5.py <app de tools/catalogo.json> [--escalera | --primera=t<n> | --capturas | --ruta | --ficha]")
    clave = sys.argv[1]
    app = json.loads((ROOT / "tools/catalogo.json").read_text("utf-8"))[clave]
    if set(app.get("variante", {}).values()) != {"c5"} or len(app["zonas"]) != 1:
        sys.exit(f"{clave}: no es una app de la c5")
    region = app["zonas"][0]
    d = Path(subprocess.run([sys.executable, "-I", str(ROOT / "tools/tienda.py"), clave], check=True,
                            capture_output=True, text=True).stdout.strip())
    ref = R.Ref(region, "c5")
    puntos = []
    rural = next(p for p in json.loads((ROOT / f"tools/puntos_control-{region}.json").read_text("utf-8"))
                 if p["id"] == "rural")
    m = ref.m
    if ficha:
        # Las escenas de la ficha de la tienda (docs/tienda/calle-<app>.md): sitios públicos, lo que dicen los datos.
        # La última es desde donde se mira el hospital con urgencias más cercano (el menú se abre al final).
        puntos += FICHA[clave]
    elif ruta:
        # En coche: una vuelta de 60 fixes cada 10 s (10 min) en un círculo de 1,5 km alrededor del punto del peor par,
        # cada fix pegado al vértice de calle más cercano (≈ 160 m entre fixes: la zona se consulta en casi todos).
        import math
        g, _, _ = ref._geom()
        _, _, _, _, la0, lo0 = R.pares_mayores(ref, 1)[0]
        cx, cy = ref.xy(la0, lo0)
        verts = [q for c in g["calles"] if not c["a"] for q in c["p"]
                 if abs(q[0] - cx) < 2500 and abs(q[1] - cy) < 2500]
        for k in range(60):
            a = 2 * math.pi * k / 60
            px, py = cx + 1500 * math.cos(a), cy + 1500 * math.sin(a)
            q = min(verts, key=lambda q: (q[0] - px) ** 2 + (q[1] - py) ** 2)
            puntos.append((f"ruta {k}", *ref.latlon(*q)))
    elif capturas:
        # Los textos más largos de verdad (calle, tramo, parroquia y lugar), en teselas de ≤ 24 KB (el arranque en frío
        # no aguanta las de 28 KB); al final, el menú. Un paso cada 12 s, para capturar y moverse con las teclas.
        puntos += textos_largos(ref)
    elif primera:
        # Arranque en frío en el centro de esa tesela: la primera carga paga además la retención del primer recurso.
        x0, y0, x1, y1 = m["cajas"][int(primera[1:])]
        x, y = (x0 + x1) / 2, (y0 + y1) / 2
        hoja = ref.hoja(x, y)[0]
        hz = R.heap_zona(json.loads((ref.zdir / f"{hoja}.json").read_text("utf-8"))) if hoja else 0
        ht = R.heap_tesela(json.loads((ref.tdir / f"{primera}.json").read_text("utf-8")))
        puntos.append((f"primera {primera} {ht} B + {hoja} {hz} B = {ht + hz} B", *ref.latlon(x, y)))
    elif escalera:
        ts = []
        for ti, nom in enumerate(m["idx"][:-1]):
            if nom:
                x0, y0, x1, y1 = m["cajas"][ti]
                x, y = (x0 + x1) / 2, (y0 + y1) / 2
                hoja = ref.hoja(x, y)[0]
                hz = R.heap_zona(json.loads((ref.zdir / f"{hoja}.json").read_text("utf-8"))) if hoja else 0
                ts.append((R.heap_tesela(json.loads((ref.tdir / f"{nom}.json").read_text("utf-8"))), nom, hoja, hz, x, y))
        for kb in range(12, 29):
            ht, nom, hoja, hz, x, y = min(ts, key=lambda t: abs(t[0] - kb * 1024))
            if not any(n.startswith(f"{nom} ") for n, _, _ in puntos):
                puntos.append((f"{nom} {ht} B + {hoja} {hz} B = {ht + hz} B", *ref.latlon(x, y)))
    else:
        puntos.append(("arranque rural", rural["lat"], rural["lon"]))
        for t, z, ht, hz, lat, lon in R.pares_mayores(ref, 3):
            puntos.append((f"par {t} {ht} B + {z} {hz} B = {ht + hz} B", lat, lon))
        ti = int(m["t_mayor"][1:])
        x0, y0, x1, y1 = m["cajas"][ti]
        puntos.append((f"centro de T_MAYOR {m['t_mayor']}", *ref.latlon((x0 + x1) / 2, (y0 + y1) / 2)))
        puntos.append((f"centro de Z_MAYOR {m['z_mayor']}", *ref.latlon(*m["z_mayor_xy"])))
    src = d / "medida-src"
    src.mkdir(exist_ok=True)
    (src / "MedidaPuntos.mc").write_text(
        "import Toybox.Lang;\n\n// GENERADO por tools/medida_c5.py. No editar a mano.\nmodule MedidaPuntos {\n"
        f"    const PASO_MS = {12000 if capturas or ficha else 10000 if ruta else 4000};\n"
        f"    const MENU = {'true' if capturas or ficha else 'false'};\n"
        "    const NOMBRES = [" + ", ".join(R.mc(n) for n, _, _ in puntos) + "] as Array<String>;\n"
        "    const PUNTOS = [" + ", ".join(f"{la!r}d, {lo!r}d" for _, la, lo in puntos) + "] as Array<Double>;\n}\n",
        "utf-8")
    jungle, n = re.subn(r"\.\./\.\./\.\./source/Gps\.mc", "../../../medida/Gps.mc",
                        (d / "monkey.jungle").read_text("utf-8"))
    if n != len(app["relojes"]):
        sys.exit(f"esperaba cambiar source/Gps.mc en {len(app['relojes'])} relojes y fueron {n}")
    jungle = re.sub(r"^(\w+\.sourcePath = .*medida/Gps\.mc.*)$", r"\1;medida-src", jungle, flags=re.M)
    (d / "medida.jungle").write_text(jungle, "utf-8")
    for n_, la, lo in puntos:
        print(f"  {n_}  ({la:.6f}, {lo:.6f})", file=sys.stderr)
    print(d)


if __name__ == "__main__":
    main()
