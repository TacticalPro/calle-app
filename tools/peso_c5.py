#!/usr/bin/env python3
"""Reparto del peso de una app de la c5 por sección del FORMATO 4 (C18, 2026-10-29).

Lee resources-gen-c5/<region>/ (t/*.json, z/*.json, poi.json, cajas.json) y estima lo que pesa cada sección con la
convención de la medición del 2026-10-28: 5 B por número y bytes + 3 por cadena. Da los totales por bloque y por sección,
el reparto rural/urbano de las teselas (U = 4 m / 1 m, en los bits altos de PB), las tiradas que se parten por los
topes del generador (ext = RUN_EXT_MAX, nv = RUN_NV_MAX), los nombres repetidos entre teselas y entre hojas de zona,
y las calles que solo cruzan (en S sin tirada en la tesela). No toca nada: solo lee.

    python3 -I tools/peso_c5.py coruna                              tablas en Markdown
    python3 -I tools/peso_c5.py coruna --prg bin/calle-release.prg  además, la diferencia con el .prg real

La estimación es la del heap del reloj, no la del fichero: el .prg guarda los recursos en otro formato y la
diferencia con la suma (más el código) es el coste fijo de empaquetar cada recurso. Por eso se compara con --prg.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NUM = 5          # B por número en un Array del reloj (medición del 2026-10-28)
CAD = 3          # B de más por cadena, además de sus bytes (medición del 2026-10-28)
RUN_EXT_MAX = 30  # tools/build_callejero.py: las tiradas lineales se parten al llegar aquí (240 m)
RUN_EXT_SIN = 31  # área sin cota
RUN_NV_MAX = 63   # vértices por tirada en la cabecera

T_SEC = ["cab", "S", "O", "C", "CB", "R", "V", "P", "E", "K"]
Z_SEC = ["cab", "S", "O", "F", "RL", "L", "LN", "FZ", "fin"]


def peso(x):
    """Bytes estimados de un elemento de la lista JSON: número, cadena o lista de números."""
    if isinstance(x, str):
        return len(x.encode("utf-8")) + CAD
    if isinstance(x, list):
        return NUM * len(x)
    return NUM


def nombres(s):
    """Los nombres de S ("\\n" + nombre + "\\n" …), en orden."""
    return [n for n in s.split("\n") if n]


def u32(v):
    return v & 0xFFFFFFFF


def tiradas(R):
    """Cabeceras de R: [(ext, area, nv, numeros)] por tirada."""
    out, i = [], 0
    while i < len(R):
        h1, h2 = u32(R[i]), u32(R[i + 1])
        ext, area, nv = (h1 >> 26) & 0x1F, (h1 >> 31) & 1, (h2 >> 26) & 0x3F
        if nv == 0:
            out.append((ext, area, R[i + 2], 3))
            i += 3
        else:
            out.append((ext, area, nv, 2))
            i += 2
    return out


def kb(b):
    return f"{b / 1024:,.0f}".replace(",", ".")


def pct(b, total):
    return f"{100 * b / total:.1f} %" if total else "—"


def teselas(rdir):
    tot = Counter()
    por_u = {1: Counter(), 4: Counter()}
    runs = Counter()
    nom_calles = Counter()   # nombre → nº de teselas en que aparece
    bytes_nombre = {}
    cruzan = Counter()
    ficheros = sorted(rdir.glob("t/*.json"), key=lambda p: int(p.stem[1:]))
    for f in ficheros:
        d = json.loads(f.read_text("utf-8"))
        FORMATO, NC, PBU, S, O, C, CB, R, V, P, E = d[:11]
        K = d[11] if len(d) > 11 else []
        u = (PBU >> 8) or 1
        secs = {"cab": 3 * NUM, "S": peso(S), "O": peso(O), "C": peso(C), "CB": peso(CB), "R": peso(R),
                "V": peso(V), "P": peso(P), "E": peso(E), "K": peso(K)}
        tot.update(secs)
        por_u.setdefault(u, Counter()).update(secs)
        por_u[u]["teselas"] += 1
        tot["disco"] += f.stat().st_size
        # tiradas
        ts = tiradas(R)
        clave = "rural" if u > 1 else "urbana"
        runs[f"n {clave}"] += len(ts)
        for ext, area, nv, nn in ts:
            runs["n"] += 1
            runs["vértices"] += nv
            runs["cabecera B"] += nn * NUM
            if area:
                runs["áreas"] += 1
            else:
                runs["lineales"] += 1
                if ext >= RUN_EXT_MAX and ext != RUN_EXT_SIN:
                    runs["lineales con ext al tope"] += 1
                    runs[f"ext al tope {clave}"] += 1
                if nv >= RUN_NV_MAX:
                    runs["lineales con nv al tope"] += 1
        # nombres y calles que solo cruzan
        ns = nombres(S)
        calles, sufijos = ns[:NC], ns[NC:]
        tot["sufijos B"] += sum(len(x.encode()) + 1 for x in sufijos)
        for i, n in enumerate(calles):
            nom_calles[n] += 1
            bytes_nombre[n] = len(n.encode()) + 1
            off0, off1 = C[i] & 0xFFFF, C[i + 1] & 0xFFFF
            if off1 == off0:
                cruzan["n"] += 1
                cruzan["B en S"] += len(n.encode()) + 1
                cruzan["B en C+CB+K"] += 3 * NUM
        tot["calles"] += NC
    rep = sum((c - 1) * bytes_nombre[n] for n, c in nom_calles.items() if c > 1)
    return len(ficheros), tot, por_u, runs, cruzan, rep, nom_calles


def zonas(rdir):
    tot = Counter()
    nom = Counter()
    bytes_nombre = {}
    ficheros = sorted(rdir.glob("z/*.json"))
    for f in ficheros:
        d = json.loads(f.read_text("utf-8"))
        FORMATO, S, O, F, RL, L, LN, H, FZ = d[:9]
        secs = {"cab": NUM, "S": peso(S), "O": peso(O), "F": peso(F), "RL": peso(RL), "L": peso(L),
                "LN": peso(LN), "FZ": peso(FZ) + NUM, "fin": NUM * max(0, len(d) - 9)}
        tot.update(secs)
        tot["disco"] += f.stat().st_size
        tot["lugares"] += len(L)
        en_hoja = Counter()
        for n in nombres(S):
            nom[n] += 1
            en_hoja[n] += 1
            bytes_nombre[n] = len(n.encode()) + 1
            tot["nombres"] += 1
        # la misma cadena más de una vez dentro de la hoja (LN ya indexa S: quitarla no toca el lector)
        tot["repetidos en la hoja B"] += sum((c - 1) * bytes_nombre[n] for n, c in en_hoja.items() if c > 1)
        tot["repetidos en la hoja O B"] += sum((c - 1) for c in en_hoja.values() if c > 1) * NUM // 2
    rep = sum((c - 1) * bytes_nombre[n] for n, c in nom.items() if c > 1)
    return len(ficheros), tot, rep


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("region")
    ap.add_argument("--prg", help=".prg real del fēnix 5, para la diferencia con la suma estimada")
    a = ap.parse_args()
    rdir = ROOT / "resources-gen-c5" / a.region
    if not rdir.is_dir():
        sys.exit(f"no hay datos en {rdir}: VARIANTE=c5 REGION={a.region} ./ciq.sh datos")

    nt, tt, por_u, runs, cruzan, rep_t, nom_calles = teselas(rdir)
    nz, tz, rep_z = zonas(rdir)
    otros = {f.name: peso(json.loads(f.read_text("utf-8"))) if f.name == "cajas.json"
             else sum(peso(x) for x in json.loads(f.read_text("utf-8")))
             for f in rdir.glob("*.json")}
    t_total = sum(tt[s] for s in T_SEC)
    z_total = sum(tz[s] for s in Z_SEC)
    total = t_total + z_total + sum(otros.values())

    print(f"## Reparto estimado de `{a.region}` (c5) — {nt} teselas, {nz} hojas de zona; "
          f"{NUM} B por número, cadena = bytes + {CAD}\n")
    print("| Bloque | KB | % |\n|---|---|---|")
    print(f"| Teselas | {kb(t_total)} | {pct(t_total, total)} |")
    print(f"| Zonas | {kb(z_total)} | {pct(z_total, total)} |")
    for k, v in sorted(otros.items()):
        print(f"| `{k}` | {kb(v)} | {pct(v, total)} |")
    print(f"| **Total estimado** | **{kb(total)}** | 100 % |")
    print(f"| JSON en disco (teselas + zonas) | {kb(tt['disco'] + tz['disco'])} | — |")
    if a.prg:
        p = Path(a.prg).stat().st_size
        print(f"| `.prg` real `{Path(a.prg).name}` | {kb(p)} ({p:,} B) | diferencia con la suma: "
              f"{kb(p - total)} KB, {pct(p - total, p)} del `.prg` |".replace(",", "."))

    rural, urb = por_u.get(4, Counter()), por_u.get(1, Counter())
    print(f"\n### Teselas por sección (rurales U = 4 m: {rural['teselas']} · urbanas U = 1 m: {urb['teselas']})\n")
    print("| Sección | KB | % teselas | rural KB | urbana KB |\n|---|---|---|---|---|")
    for s in T_SEC:
        print(f"| {s} | {kb(tt[s])} | {pct(tt[s], t_total)} | {kb(rural[s])} | {kb(urb[s])} |")
    print(f"| **Total** | **{kb(t_total)}** | 100 % | {kb(sum(rural[s] for s in T_SEC))} | "
          f"{kb(sum(urb[s] for s in T_SEC))} |")

    print("\n### Tiradas (cabeceras R)\n")
    print("| Qué | Valor |\n|---|---|")
    print(f"| Tiradas | {runs['n']:,} (rurales {runs['n rural']:,} · urbanas {runs['n urbana']:,}; "
          f"lineales {runs['lineales']:,} · áreas {runs['áreas']:,}) |".replace(",", "."))
    print(f"| Cabeceras | {kb(runs['cabecera B'])} KB |")
    print(f"| Vértices | {runs['vértices']:,} ({runs['vértices'] / max(1, runs['n']):.1f} por tirada) |"
          .replace(",", "."))
    print(f"| Lineales con `ext` al tope de {RUN_EXT_MAX} (partidas por los 240 m) | "
          f"{runs['lineales con ext al tope']:,} (rurales {runs['ext al tope rural']:,} · urbanas "
          f"{runs['ext al tope urbana']:,}) → cota del ahorro si no se partieran: "
          f"{kb(runs['lineales con ext al tope'] * 2 * NUM)} KB |".replace(",", "."))
    print(f"| Lineales con {RUN_NV_MAX} vértices (partidas por el tope de vértices) | "
          f"{runs['lineales con nv al tope']:,} |".replace(",", "."))

    print("\n### Nombres de las teselas\n")
    print("| Qué | Valor |\n|---|---|")
    print(f"| Entradas de calle (NC sumado) | {tt['calles']:,}; nombres distintos {len(nom_calles):,} |"
          .replace(",", "."))
    print(f"| Repetidos entre teselas (misma cadena en más de una) | {kb(rep_t)} KB de S |")
    print(f"| Calles que solo cruzan (sin tirada en la tesela) | {cruzan['n']:,}: {kb(cruzan['B en S'])} KB en S "
          f"+ {kb(cruzan['B en C+CB+K'])} KB en C, CB y K |".replace(",", "."))
    print(f"| Sufijos de portal en S | {kb(tt['sufijos B'])} KB |")

    print(f"\n### Zonas por sección ({nz} hojas; {tz['lugares']:,} lugares, {tz['nombres']:,} nombres)\n"
          .replace(",", "."))
    print("| Sección | KB | % zonas |\n|---|---|---|")
    for s in Z_SEC:
        print(f"| {s} | {kb(tz[s])} | {pct(tz[s], z_total)} |")
    print(f"| **Total** | **{kb(z_total)}** | 100 % |")
    print(f"\nNombres repetidos entre hojas de zona: {kb(rep_z)} KB de S. **Dentro de una misma hoja** (misma cadena "
          f"para varios lugares; LN ya indexa S, así que quitarla no toca el lector): "
          f"{kb(tz['repetidos en la hoja B'])} KB de S + {kb(tz['repetidos en la hoja O B'])} KB de O.")


if __name__ == "__main__":
    main()
