#!/usr/bin/env python3
"""ref.abreviar_tipo usa build_callejero sin tocar sys.path y lo carga una sola vez.

    python3 -I tools/test_ref_import.py
"""
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import ref  # noqa: E402

sys.path.remove(str(TOOLS))

# Cada carga de un módulo ejecuta su código con exec: el gancho de auditoría las cuenta, se cargue como se cargue.
cargas = []
sys.addaudithook(lambda ev, args: ev == "exec" and getattr(args[0], "co_filename", "").endswith(
    "build_callejero.py") and cargas.append(args[0].co_filename))


def main():
    antes = list(sys.path)
    for _ in range(3):
        assert ref.abreviar_tipo("Rúa do Franco") == "R. do Franco"
        assert ref.abreviar_tipo("Travesía da Paz") == "Tr. da Paz"
        assert ref.abreviar_tipo("Franco") == "Franco"
    assert sys.path == antes, f"sys.path ha cambiado: delante {sys.path[:len(sys.path) - len(antes)]}"
    assert len(cargas) == 1, f"build_callejero cargado {len(cargas)} veces"
    print("ok: abreviar_tipo sin tocar sys.path; build_callejero cargado una vez")


if __name__ == "__main__":
    main()
