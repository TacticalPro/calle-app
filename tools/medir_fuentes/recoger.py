#!/usr/bin/env python3
"""Junta la salida de los tests de tools/medir_fuentes (un fichero out-<reloj>.txt por reloj) en
tools/fonts/metricas.json: {reloj: {fuente: {h, asc, desc, w: {carácter: px}}}}. Comprueba que los
anchos por carácter suman lo que el reloj mide para una frase entera."""
import json
import re
import sys
from pathlib import Path

CHARS = (" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
         "áéíóúÁÉÍÓÚñÑüÜçÇºª·…—–àèòïÏ")
FRASE = "Calle de la Princesa"


def main():
    res = {}
    for f in sys.argv[1:-1]:
        reloj = Path(f).stem.removeprefix("out-")
        txt = Path(f).read_text()
        d = {}
        for m in re.finditer(r"MED (\w+) h=(\d+) asc=(\d+) desc=(\d+) w=([\d,]+)", txt):
            ws = [int(x) for x in m.group(5).strip(",").split(",")]
            assert len(ws) == len(CHARS), (reloj, m.group(1), len(ws))
            d[m.group(1)] = dict(h=int(m.group(2)), asc=int(m.group(3)), desc=int(m.group(4)), w=dict(zip(CHARS, ws)))
        for m in re.finditer(r"MED (\w+) par=(\d+)", txt):
            suma = sum(d[m.group(1)]["w"][c] for c in FRASE)
            if m.group(1) != "numberMild" and suma != int(m.group(2)):
                sys.exit(f"{reloj} {m.group(1)}: los anchos suman {suma} y el reloj mide {m.group(2)}")
        if len(d) != 6:
            sys.exit(f"{reloj}: faltan fuentes ({len(d)}/6); ¿falló el test?")
        res[reloj] = d
    Path(sys.argv[-1]).write_text(json.dumps(res, ensure_ascii=False, sort_keys=True))
    print(f"escrito {sys.argv[-1]} ({len(res)} relojes)")


if __name__ == "__main__":
    main()
