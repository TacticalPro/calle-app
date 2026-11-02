#!/usr/bin/env python3
"""tipo_estacion: solo dos tipos, comisaría y cuartel; lo que no es ninguno de los dos, fuera.

    python3 -I tools/test_poi.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_callejero as bc  # noqa: E402

C, Q = bc.POI_COMISARIA, bc.POI_CUARTEL
CASOS = [
    ({"name": "Comisaría de Distrito Centro"}, C),
    ({"name": "Comissaria de Ejemplo"}, C),
    ({"name": "Jefatura Superior de Ejemplo"}, C),
    ({"name": "Guàrdia Urbana de Ejemplo"}, C),
    ({"name": "Unitat Territorial del Districte de Ejemplo"}, C),
    ({"name": "Unidad Integral de Distrito Centro"}, C),
    ({}, C),                                            # sin nombre: amenity=police es una comisaría en OSM
    ({"name": "Cuartel de Ejemplo"}, Q),
    ({"name": "Casa Cuartel de Ejemplo"}, Q),
    ({"name": "Oficina de Tramitación del DNIe y Pasaporte"}, None),
    ({"name": "Oficina documentació"}, None),
    ({"name": "Unidad Canina"}, None),
    ({"name": "Comisaría General de Ejemplo"}, None),
    ({"name": "Complejo de Ejemplo"}, None),
    ({"name": "Agentes de Movilidad - Base Centro"}, None),
    ({"name": "Protección Civil de Ejemplo"}, None),
    ({"name": "Duana"}, None),
    ({"name": "Jefatura Provincial de Tráfico"}, None),
]


def main():
    malos = [(t, q, bc.tipo_estacion(t)) for t, q in CASOS if bc.tipo_estacion(t) != q]
    for t, q, r in malos:
        print(f"MAL {t}: esperaba {q}, da {r}")
    tipos = {bc.POI_HOSPITAL, bc.POI_URGENCIAS, C, Q}
    if set(bc.POI_ETIQUETA) != tipos or {C, Q} & {3, 5, 6}:
        print("MAL los números: 3, 5 y 6 son de datos de antes y no se dan")
        malos.append(None)
    print(f"test_poi: {len(CASOS) - len(malos)}/{len(CASOS)}" if malos else f"test_poi: {len(CASOS)}/{len(CASOS)} OK")
    return 1 if malos else 0


if __name__ == "__main__":
    sys.exit(main())
