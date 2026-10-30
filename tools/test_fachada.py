#!/usr/bin/env python3
"""El portal de un edificio no salta de esquina por simplificar la calle.

    python3 -I tools/test_fachada.py

extraer_portales pone el portal de un edificio en el punto de su contorno más cercano a la calle. Con dos esquinas casi a
la misma distancia, la simplificación de Douglas-Peucker (un quiebro de 0,7 m que DP_TOL = 0,75 borra) basta para
cambiar de esquina: el portal se movía unos 20 m. En Madrid le pasaba al 1,4 % de los portales, y en Galicia al 1,9 %
(a más de 5 m; estudio de precisión, 2026-10-30). El emparejamiento se hace con la calle sin simplificar.
"""
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_callejero as bc  # noqa: E402


class Plano:
    """Proyección de prueba: lat y lon ya son metros (y, x)."""

    def xy(self, lat, lon):
        return lon, lat


def via(nombre, raw):
    pts = bc.douglas_peucker(raw, bc.DP_TOL)
    return dict(id=1, nombre=nombre, clase=0, area=False, pts=pts, raw=raw, hw="residential",
                claves={bc.clave(nombre)}, bb=bc.caja_de(pts))


def edificio(nombre, num, anillo):
    return dict(type="way", id=2, nodes=list(range(10, 10 + len(anillo))),
                tags={"addr:housenumber": num, "addr:street": nombre},
                geometry=[dict(lat=y, lon=x) for x, y in anillo])


def portal(v, e):
    return bc.extraer_portales([e], Plano(), [v], dict(alias_calle={}), Counter(), Counter(), Counter())


def main():
    nombre = "Rúa da Proba"
    raw = [(0.0, 0.0), (45.0, 0.7), (100.0, 0.0)]          # el quiebro de 0,7 m, por debajo de DP_TOL
    v = via(nombre, raw)
    assert v["pts"] == [(0.0, 0.0), (100.0, 0.0)], "DP_TOL ya no borra el quiebro: el test no prueba nada"
    # Fachada casi paralela a la calle: con la calle recta, la esquina de x = 60 queda 2 cm más cerca; con el
    # quiebro, la de x = 40.
    e = edificio(nombre, "7", [(40.0, 10.0), (60.0, 9.98), (60.0, 20.0), (40.0, 20.0), (40.0, 10.0)])
    exacta = dict(v, pts=raw, bb=bc.caja_de(raw))
    (p,) = portal(v, e)
    (q,) = portal(exacta, e)
    d = math.hypot(p["x"] - q["x"], p["y"] - q["y"])
    print(f"portal con la calle simplificada ({p['x']:.1f}, {p['y']:.1f}); con la exacta ({q['x']:.1f}, {q['y']:.1f}); "
          f"a {d:.1f} m")
    if d > 1.0:
        sys.exit("FALLA: la simplificación de la calle mueve el portal de esquina")
    print("ok: el portal no depende de la simplificación de la calle")


if __name__ == "__main__":
    main()
