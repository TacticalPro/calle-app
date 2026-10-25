#!/usr/bin/env python3
"""Espiga de la fase 0: teselas ficticias para medir memoria y tiempos en el simulador.

    espiga.py --n 1700 --mayor 3     1.700 recursos mínimos + una tesela 3× la estimada
    espiga.py --n 0                  solo la tesela pesada (para restar el coste del índice)

Escribe resources-gen/ y source-gen/ con el MISMO formato que build_callejero.py,
así que lo que se mide aquí vale para los datos reales. El generador real los pisa.
"""
import argparse
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORMATO = 1

# Estimación de la tesela más densa del casco (500 m + margen de 75 m).
EST = {"runs": 400, "vert": 2000, "port": 500, "nombres": 70}

NOMBRES = ["Rúa do Franco", "Rúa do Vilar", "Praza do Obradoiro", "Rúa de San Pedro de Mezonzo",
           "Avenida de Xoán XXIII", "Rúa das Orfas", "Travesa da Universidade",
           "Praza de Galicia", "Rúa do Hórreo", "Avenida de Lugo", "Camiño da Ponte de Sar"]


def tesela_pesada(f, rng):
    runs, vert = EST["runs"] * f, EST["vert"] * f
    port, nom = EST["port"] * f, min(255, EST["nombres"] * f)
    nombres = [f"{NOMBRES[i % len(NOMBRES)]} {i}" for i in range(nom)]
    R, V = [], []
    per = vert // runs
    for r in range(runs):
        n = per
        calle = r % nom
        pts = [(rng.randrange(650), rng.randrange(650)) for _ in range(n)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        R += [n | calle << 12, min(xs) | min(ys) << 11, max(xs) | max(ys) << 11]
        V += [x | y << 11 for x, y in pts]
    P = sorted(rng.randrange(650) | rng.randrange(650) << 11 | (rng.randrange(nom) << 22) for _ in range(port))
    H = [rng.randrange(1, 200) | (rng.randrange(3) << 14) for _ in range(port)]
    return [FORMATO, nombres, R, V, P, H]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1700)
    ap.add_argument("--mayor", type=int, default=3)
    a = ap.parse_args()
    rng = random.Random(7)

    jd = ROOT / "resources-gen" / "jsonData"
    (jd / "t").mkdir(parents=True, exist_ok=True)
    for viejo in (jd / "t").glob("*.json"):
        viejo.unlink()
    xml = ['<jsonDataResources>']
    pesada = tesela_pesada(a.mayor, rng)
    (jd / "t" / "tmayor.json").write_text(json.dumps(pesada, ensure_ascii=False, separators=(",", ":")), "utf-8")
    xml.append('    <jsonData id="tmayor" filename="t/tmayor.json"/>')
    for i in range(a.n):
        (jd / "t" / f"t{i}.json").write_text(json.dumps([FORMATO, ["Rúa X"], [1, 0, 0], [0], [], []]), "utf-8")
        xml.append(f'    <jsonData id="t{i}" filename="t/t{i}.json"/>')
    xml.append('</jsonDataResources>')
    (jd / "teselas.xml").write_text("\n".join(xml) + "\n", "utf-8")

    elems = sum(len(x) for x in pesada[2:])
    idx = ", ".join(f"Rez.JsonData.t{i}" for i in range(a.n)) or ""
    mc = f"""import Toybox.Lang;

// GENERADO por tools/espiga.py (fase 0). No editar: lo pisa build_callejero.py.
module Callejero {{
    const REGION = "espiga";
    const FORMATO = {FORMATO};
    const T_MAYOR = Rez.JsonData.tmayor;
    const MAYOR_ELEMS = {elems};
    const MAYOR_NOMBRES = {len(pesada[1])};
    const IDX = [{idx}] as Array<ResourceId or Null>;
}}
"""
    (ROOT / "source-gen").mkdir(exist_ok=True)
    (ROOT / "source-gen" / "Callejero.mc").write_text(mc, "utf-8")
    kb = (jd / "t" / "tmayor.json").stat().st_size / 1024
    print(f"espiga: {a.n} recursos + tmayor ({elems} números, {len(pesada[1])} nombres, {kb:.0f} KB JSON)")


if __name__ == "__main__":
    main()
