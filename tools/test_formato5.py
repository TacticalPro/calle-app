#!/usr/bin/env python3
"""Ida y vuelta del FORMATO 5 sobre teselas reales del FORMATO 4, y K contra la referencia (ref.Tes).

    python3 -I tools/test_formato5.py ~/code/calle-fenix/resources-gen/galicia/t
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import formato5 as F5  # noqa: E402
import ref  # noqa: E402


def main():
    carpeta = Path(sys.argv[1]).expanduser()
    n, mayor = 0, (0, "")
    for f in sorted(carpeta.glob("t*.json")):
        t = json.loads(f.read_text("utf-8"))
        b = F5.codificar(t)
        t2, u, K = F5.decodificar(b)
        assert t2 == t, f"{f.name}: la vuelta no da la misma tesela"
        assert u == 1 and len(b) % 4 == 0, f.name
        # K[k] es la suma de los bits de vértices de las calles anteriores, contada sobre las tiradas de ref.Tes.
        nc, R = t[1], t[7]
        bits = [0] * nc
        for r, k, _c, _a, _e, vs, _A, _B in ref.Tes(t).tiradas():
            bits[k] += (len(vs) - 1) * 2 * (R[r + 1] & 0xF)
        acum = 0
        for k in range(nc):
            assert K[k] == acum, f"{f.name}: K[{k}] = {K[k]}, esperaba {acum}"
            acum += bits[k]
        assert K[nc] == acum, f"{f.name}: K final"
        # O del FORMATO 5: dónde empieza cada nombre en BYTES de S (el reloj los lee de B sin pasar S a String),
        # y las calles en orden de bytes UTF-8 (Tesela.indiceDe busca por bisección comparando bytes).
        cab = struct.unpack_from(f"<{F5.CABECERA}I", b, 0)
        ls = cab[2]
        p = 4 * F5.CABECERA
        sb = b[p:p + ls]
        O5 = struct.unpack_from(f"<{cab[3]}I", b, p + ls + (-ls % 4))
        ini = [(O5[j // 2] >> (16 * (j % 2))) & 0xFFFF for j in range(2 * len(O5))]
        nombres = t[3][1:].split("\n")[:-1]
        for k, nom in enumerate(nombres):
            assert sb[ini[k]:ini[k + 1] - 1].decode("utf-8") == nom, f"{f.name}: nombre {k} ({nom}) mal en bytes"
        calles = [nom.encode("utf-8") for nom in nombres[:nc]]
        assert calles == sorted(calles) and len(set(calles)) == nc, f"{f.name}: calles fuera del orden de bytes"
        cuatro = F5.codificar(t, 4)
        assert F5.decodificar(cuatro)[1] == 4, f"{f.name}: U = 4"
        n += 1
        mayor = max(mayor, (len(b), f.name))
    assert n > 0, f"no hay teselas en {carpeta}"
    print(f"FORMATO 5: {n} teselas ida y vuelta OK; la mayor, {mayor[1]}, {mayor[0]} bytes")


if __name__ == "__main__":
    main()
