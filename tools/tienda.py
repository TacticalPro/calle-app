#!/usr/bin/env python3
"""Prepara la compilación de una app del catálogo de la Connect IQ Store (tools/catalogo.json).

Cada zona es una app aparte en la tienda, con su id, su nombre y sus relojes. Este script escribe en
bin/tienda/<app>/ el manifiesto (id, nombre y relojes del catálogo), un monkey.jungle con las rutas
ajustadas a esa carpeta y el recurso con el nombre de la app. Antes comprueba que los datos generados
para cada reloj tengan exactamente las zonas de la app: si no, para.

Lo llama `APP=<app> ./ciq.sh tienda`, que compila con lo que este script deja. Imprime la carpeta.
"""
import json
import re
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


def zonas_generadas(carpetas):
    """Zonas con Region<Nombre>.mc en las carpetas source-gen*."""
    zonas = set()
    for c in carpetas:
        if c.startswith("source-gen"):
            for f in (ROOT / c).glob("Region*.mc"):
                if f.stem != "Regiones":
                    zonas.add(f.stem[len("Region"):].lower())
    return zonas


def main():
    if len(sys.argv) != 2:
        sys.exit("uso: tienda.py <app de tools/catalogo.json>")
    clave = sys.argv[1]
    app = json.loads((ROOT / "tools/catalogo.json").read_text("utf-8")).get(clave)
    if not isinstance(app, dict) or not re.fullmatch(r"[0-9a-f]{32}", app.get("id", "")):
        sys.exit(f"{clave}: no está en tools/catalogo.json o no tiene un id válido")

    jungle = (ROOT / "monkey.jungle").read_text("utf-8")
    rutas = rutas_jungle(jungle)
    for reloj in app["relojes"]:
        zonas = zonas_generadas(rutas.get(reloj, rutas["base"]))
        if zonas != set(app["zonas"]):
            sys.exit(f"{reloj}: los datos generados tienen {sorted(zonas)} y «{app['nombre']}» lleva "
                     f"{sorted(app['zonas'])}. Regenere los datos de ese reloj antes de empaquetar.")

    out = ROOT / "bin" / "tienda" / clave
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
            carpetas = [SUBIR + c.strip() for c in m.group(3).split(";")]
            if m.group(2) == "resourcePath":
                carpetas.append("res")
            linea = f"{m.group(1)} = {';'.join(carpetas)}"
        lineas.append(linea)
    (out / "monkey.jungle").write_text("\n".join(lineas) + "\n", "utf-8")

    (out / "res" / "strings" / "strings.xml").write_text(
        f'<resources>\n    <string id="NombreTienda">{app["nombre"]}</string>\n</resources>\n', "utf-8")
    print(out)


if __name__ == "__main__":
    main()
