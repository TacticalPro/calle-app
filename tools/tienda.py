#!/usr/bin/env python3
"""Prepara la compilación de una app del catálogo de la Connect IQ Store (tools/catalogo.json).

Cada zona es una app aparte en la tienda, con su id, su nombre y sus relojes. Este script escribe en
bin/tienda/<app>/ el manifiesto (id, nombre y relojes del catálogo), un monkey.jungle con las rutas
ajustadas a esa carpeta y el recurso con el nombre de la app. Antes comprueba que los datos generados
para cada reloj tengan exactamente las zonas de la app: si no, para.

Lo llama `APP=<app> ./ciq.sh tienda`, que compila con lo que este script deja. Imprime la carpeta.

Variante c5 (las apps por provincia de Galicia para los de 128 KB: "variante" c5 en el catálogo): el reloj compila
source/*.mc menos Zonas.mc, más source-c5/Zonas.mc (zonas en árbol), con sourcePath por fichero, y sus tests
generados de test-gen-c5/<zona>/. La lista sale de source/ cada vez: un fichero nuevo del común no se queda fuera.

Con --beta (`APP=<app> ./ciq.sh beta`): la beta privada de esa app, con su "beta_id" (otro id, que no se cambia
nunca) y sus "beta_relojes" (por defecto, solo el fēnix 7X Pro), en bin/tienda/<app>-beta/.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBIR = "../../../"  # de bin/tienda/<app>/ a la raíz


def rutas_jungle(jungle):
    """{'base' o reloj: [carpetas de sourcePath]} de monkey.jungle."""
    rutas = {}
    for linea in jungle.splitlines():
        m = re.match(r"^(\w+)\.sourcePath\s*=\s*(.+)$", linea.strip())
        if m:
            rutas[m.group(1)] = [c.strip() for c in m.group(2).split(";")]
    return rutas


# Ficheros de source-c5/ que sustituyen a los de source/ en la variante c5 (los demás de source-c5/, el lector del
# FORMATO 5, no se compilan). Una app puede añadir los suyos con "c5_fuentes" en el catálogo (A Coruña: Localizador.mc,
# la zona con la tesela soltada).
C5_PROPIOS = ["Zonas.mc"]


def fuentes_c5(propios):
    """sourcePath de la variante c5 en lugar de «source»: los ficheros de source/ menos los propios, y estos desde
    source-c5/."""
    comunes = sorted(f.name for f in (ROOT / "source").glob("*.mc"))
    assert all(f in comunes and (ROOT / "source-c5" / f).exists() for f in propios), propios
    return [f"source/{f}" for f in comunes if f not in propios] + [f"source-c5/{f}" for f in propios]


def zonas_generadas(carpetas):
    """Zonas con Region<Nombre>.mc en las carpetas source-gen*."""
    zonas = set()
    for c in carpetas:
        if c.startswith("source-gen"):
            for f in (ROOT / c).glob("Region*.mc"):
                if f.stem != "Regiones":
                    zonas.add(f.stem[len("Region"):].lower())
    return zonas


def solo_zonas(carpeta, zonas, out):
    """Callejero.mc, Regiones.mc y el ajuste «Zona» con solo las zonas de la app, más sus Region<Nombre>.mc,
    en out/gen-<variante>/. Las teselas no se tocan: el jungle de la app apunta a resources-gen*/<zona>/.
    Devuelve la carpeta, relativa a out."""
    variante = carpeta[len("source-gen-"):] if carpeta != "source-gen" else "normal"
    gen = out / f"gen-{variante}"
    if gen.exists():
        shutil.rmtree(gen)
    subprocess.run([sys.executable, "-I", str(ROOT / "tools/build_callejero.py"), "--comun", "--variante", variante,
                    "--solo", ",".join(zonas), "--salida", str(gen)], check=True, stdout=sys.stderr)
    for f in (ROOT / carpeta).glob("Region*.mc"):
        if f.stem[len("Region"):].lower() in zonas:
            shutil.copy(f, gen / "source" / f.name)
    return gen.name


def main():
    beta = "--beta" in sys.argv[2:]
    if len(sys.argv) != 2 + beta:
        sys.exit("uso: tienda.py <app de tools/catalogo.json> [--beta]")
    clave = sys.argv[1]
    app = json.loads((ROOT / "tools/catalogo.json").read_text("utf-8")).get(clave)
    if not isinstance(app, dict) or not re.fullmatch(r"[0-9a-f]{32}", app.get("id", "")):
        sys.exit(f"{clave}: no está en tools/catalogo.json o no tiene un id válido")
    if beta:
        if not re.fullmatch(r"[0-9a-f]{32}", app.get("beta_id", "")) or app["beta_id"] == app["id"]:
            sys.exit(f"{clave}: sin \"beta_id\" propio en tools/catalogo.json")
        app = dict(app, id=app["beta_id"], relojes=app.get("beta_relojes", ["fenix7xpro"]))

    jungle = (ROOT / "monkey.jungle").read_text("utf-8")
    # "variante" de la app: {reloj: variante} cuyos datos lleva ese reloj en esta app, aunque el jungle diga otra
    # (Galicia lleva el 6X Pro en la b; Madrid, en la c). Se rehacen sus rutas desde las de base.
    base = {k: re.search(rf"^base\.{k}\s*=\s*(.+)$", jungle, re.M).group(1) for k in ("sourcePath", "resourcePath")}
    for reloj, v in app.get("variante", {}).items():
        if reloj not in app["relojes"] or v not in ("normal", "6x", "c", "b", "c5"):
            sys.exit(f"{clave}: variante «{v}» para «{reloj}», que no está en sus relojes o no existe")
        if v == "c5" and len(app["zonas"]) != 1:
            sys.exit(f"{clave}: la variante c5 es de una sola zona (una provincia por app)")
        suf = "" if v == "normal" else "-" + v

        def ruta(c):
            c = re.sub(r"^(source|test|resources)-gen(-\w+)?$", rf"\1-gen{suf}", c.strip())
            if v == "c5" and c == "source":
                return ";".join(fuentes_c5(C5_PROPIOS + app.get("c5_fuentes", [])))
            if v == "c5" and c == "test-gen-c5":
                return f"{c}/{app['zonas'][0]}"
            return c

        jungle = re.sub(rf"^{reloj}\.(sourcePath|resourcePath)\s*=.*\n?", "", jungle, flags=re.M)
        jungle += "".join(f"\n{reloj}.{k} = " + ";".join(ruta(c) for c in base[k].split(";"))
                          for k in ("sourcePath", "resourcePath")) + "\n"
    rutas = rutas_jungle(jungle)
    out = ROOT / "bin" / "tienda" / (clave + ("-beta" if beta else ""))
    filtro = {}   # carpeta source-gen* con más zonas que la app → carpeta de out con solo las de la app
    for reloj in app["relojes"]:
        carpetas = rutas.get(reloj, rutas["base"])
        zonas = zonas_generadas(carpetas)
        if not set(app["zonas"]) <= zonas:
            sys.exit(f"{reloj}: los datos generados tienen {sorted(zonas)} y «{app['nombre']}» lleva "
                     f"{sorted(app['zonas'])}. Regenere los datos de ese reloj antes de empaquetar.")
        if zonas != set(app["zonas"]):
            for c in carpetas:
                if c.startswith("source-gen") and c not in filtro:
                    filtro[c] = solo_zonas(c, app["zonas"], out)
    (out / "res" / "strings").mkdir(parents=True, exist_ok=True)

    manifiesto = (ROOT / "manifest.xml").read_text("utf-8")
    manifiesto, n_id = re.subn(r'(<iq:application id=")[0-9a-f]{32}', r"\g<1>" + app["id"], manifiesto)
    manifiesto, n_nombre = re.subn(r'name="@Strings\.AppName"', 'name="@Strings.NombreTienda"', manifiesto)
    productos = "".join(f'\n            <iq:product id="{r}"/>' for r in app["relojes"])
    manifiesto, n_prod = re.subn(r"(<iq:products>).*?(\n\s*</iq:products>)", r"\g<1>" + productos + r"\g<2>",
                                 manifiesto, flags=re.S)
    if (n_id, n_nombre, n_prod) != (1, 1, 1):
        sys.exit("No pude poner el id, el nombre o los relojes en el manifiesto")
    (out / "manifest.xml").write_text(manifiesto, "utf-8")

    lineas = []
    for linea in jungle.splitlines():
        m = re.match(r"^(\w+\.(sourcePath|resourcePath))\s*=\s*(.+)$", linea.strip())
        if m:
            carpetas = []
            for c in (c.strip() for c in m.group(3).split(";")):
                fuente = c.replace("resources-gen", "source-gen", 1)
                if c in filtro:
                    carpetas.append(filtro[c] + "/source")
                elif c.startswith("resources-gen") and fuente in filtro:
                    carpetas += [f"{SUBIR}{c}/{z}" for z in app["zonas"]] + [filtro[fuente] + "/res"]
                else:
                    carpetas.append(SUBIR + c)
            if m.group(2) == "resourcePath":
                carpetas.append("res")
            linea = f"{m.group(1)} = {';'.join(carpetas)}"
        lineas.append(linea)
    # El icono a la medida de cada reloj (resources-<reloj>/, tools/caratula.py --instalar): el compilador solo lo
    # busca junto a un «resources» al lado del jungle, no en ../../../resources; aquí se añade a mano.
    propias = {m.group(1) for m in (re.match(r"^(\w+)\.resourcePath", l.strip()) for l in lineas) if m}
    for r in app["relojes"]:
        if (ROOT / f"resources-{r}").is_dir() and r not in propias:
            lineas.append(f"{r}.resourcePath = $(base.resourcePath);{SUBIR}resources-{r}")
    (out / "monkey.jungle").write_text("\n".join(lineas) + "\n", "utf-8")

    (out / "res" / "strings" / "strings.xml").write_text(
        f'<resources>\n    <string id="NombreTienda">{app["nombre"]}</string>\n</resources>\n', "utf-8")
    print(out)


if __name__ == "__main__":
    main()
