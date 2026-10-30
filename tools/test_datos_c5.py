#!/usr/bin/env python3
"""Aclarado de portales y abreviatura de la variante c5 (build_callejero), sin datos de OSM.

    python3 -I tools/test_datos_c5.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_callejero as B  # noqa: E402


def portal(calle, num, x=0.0, y=0.0, suf=""):
    return dict(calle=calle, num=num, suf=suf, x=x, y=y, fuente=1)


def test_paridad():
    # Una calle numerada por las dos aceras, 1-20: con uno de cada dos, siguen las dos aceras y, en cada una, el primero
    # y el último.
    ps = [portal("Rúa Real", n, x=n, y=0 if n % 2 else 10) for n in range(1, 21)]
    quedan = B.aclarar_portales(ps, 2, lambda x, y: "15030")
    pares = sorted(p["num"] for p in quedan if p["num"] % 2 == 0)
    impares = sorted(p["num"] for p in quedan if p["num"] % 2)
    assert pares and impares, f"se pierde una acera: pares {pares}, impares {impares}"
    assert pares[0] == 2 and pares[-1] == 20 and impares[0] == 1 and impares[-1] == 19, (pares, impares)
    # Dentro de una acera, con uno de cada dos, entre dos portales que quedan hay como mucho 4 números.
    for lado in (pares, impares):
        assert all(b - a <= 4 for a, b in zip(lado, lado[1:])), lado
    assert len(quedan) < len(ps)


def test_homonimas():
    # La misma «Rúa Nova» en dos municipios: cada una se aclara aparte y conserva su primer y su último portal.
    a = [portal("Rúa Nova", n, x=n) for n in (1, 3, 5, 7, 9)]
    b = [portal("Rúa Nova", n, x=10000 + n) for n in (1, 3)]
    quedan = B.aclarar_portales(a + b, 2, lambda x, y: "15030" if x < 5000 else "15036")
    en_b = sorted(p["num"] for p in quedan if p["x"] >= 5000)
    en_a = sorted(p["num"] for p in quedan if p["x"] < 5000)
    assert en_b == [1, 3], f"el segundo municipio pierde portales: {en_b}"
    assert en_a == [1, 5, 9], en_a


def test_abreviar_sin_choque():
    nombres = ["Travesa do Porto", "Travesía do Porto", "Rúa do Franco", "Rolda de Outeiro", "Tr. Nova", "Travesa Nova"]
    ab = B.abreviaturas(nombres)
    assert ab.get("Rúa do Franco") == "R. do Franco", ab
    assert ab.get("Rolda de Outeiro") == "Rd. de Outeiro", ab
    # Travesa y Travesía darían las dos «Tr. do Porto»: se quedan largas.
    assert "Travesa do Porto" not in ab and "Travesía do Porto" not in ab, ab
    # «Travesa Nova» chocaría con una calle que ya se llama «Tr. Nova».
    assert "Travesa Nova" not in ab, ab
    assert all(B.abreviar_tipo(n) == c for n, c in ab.items())


def main():
    for f in (test_paridad, test_homonimas, test_abreviar_sin_choque):
        f()
        print(f"ok  {f.__name__}")


if __name__ == "__main__":
    main()
