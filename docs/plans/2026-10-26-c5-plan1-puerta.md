# C5 · Plan 1 — La puerta: FORMATO 5 y su lector en el fēnix 5

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** comprobar en el simulador del fēnix 5, con la tesela más pesada real de Galicia, que el FORMATO 5 (tesela en bytes, cargada de un base64) da los mismos resultados que el FORMATO 4, cabe en la memoria y deja margen ×2 sobre el watchdog de 120.000 instrucciones. Es la condición previa de todo lo demás (especificación `docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md`, *Riesgos*).

**Architecture:**
- **Python:** `tools/formato5.py` convierte una tesela del FORMATO 4 (la lista de `build_callejero.empaquetar`) en bytes, y de vuelta. `tools/puerta_c5.py` toma la tesela más pesada de Galicia, la escribe en base64 como recurso y calcula con `ref.Tes` lo que debe responder el reloj.
- **Reloj:** el lector nuevo vive en `source-c5/`, con la misma interfaz que `source/Tesela.mc` y `source/Buscador.mc`. Lo prueba `puerta/`, un proyecto de tests aparte con un `Callejero` mínimo. **No se toca nada de lo existente:** la integración en la app es el plan 2.

**Tech Stack:** Python 3 (biblioteca estándar), Monkey C (SDK 9.3, `fenix5`, API 3.1), `monkeyc`/`monkeydo`, `StringUtil.convertEncodedString`.

**Plan 2 (después de la puerta, aparte):**
- variante `c5` en `build_callejero.py`: demarcación, rural sin cortes, unidad por tesela, zonas de 20 km en dos niveles y reparto en dos módulos;
- `ref.py` con FORMATO 5;
- `Resultado` y `Estado` sacados de `Buscador.mc` a su propio fichero, y `rellenar`/`consultar` en el lector `c5`;
- anotaciones `(:f4)`/`(:c5)`, `tienda.py` y `catalogo.json`;
- fuerza bruta, memoria en modo app y el `.prg` de campo.

**Convivencia (obligatoria):** otras sesiones trabajan en `~/code/calle-fenix` (Cataluña y Barcelona, sin commit) y la coordinadora de Murcia y Valencia fusiona ramas.
- Todo este plan se hace en el worktree `~/code/calle-c5` (rama `c5-galicia`). Los commits, siempre con `git add <ruta>` explícita, nunca `-a` ni `.`.
- Simulador: candado `/tmp/calles-sim.lock`. Se coge con `until mkdir /tmp/calles-sim.lock 2>/dev/null; do sleep 20; done; echo "calle-c5 $$" > /tmp/calles-sim.lock/quien` y se suelta con `mv /tmp/calles-sim.lock /tmp/calles-sim.lock-liberado-$(date +%s)`, también si algo falla. `rm` lo bloquea un hook.
- Los datos generados (`resources-gen/`, `tools/out/`) no están en git: se leen del árbol principal, `~/code/calle-fenix`.

---

## Mapa de ficheros

| Fichero | Qué hace |
|---|---|
| `tools/formato5.py` (nuevo) | `codificar(lista4, u)` → bytes; `decodificar(bytes)` → `(lista4, u, K)`; `indice_k` |
| `tools/test_formato5.py` (nuevo) | ida y vuelta sobre todas las teselas de una carpeta, y K contra `ref.Tes` |
| `tools/puerta_c5.py` (nuevo) | genera `puerta/resources-gen/tesela.json` y `tesela.xml`, `puerta/source-gen/Callejero.mc` y `puerta/source-gen/PuertaDatos.mc` |
| `source-c5/Tesela.mc` (nuevo) | `class Tesela` y `module Teselas` del FORMATO 5 (la interfaz de `source/Tesela.mc`) |
| `source-c5/Buscador.mc` (nuevo) | `module Buscador` del FORMATO 5: `buscar`, `portal`, `textoNumero`, `escape` |
| `puerta/manifest.xml`, `puerta/monkey.jungle`, `puerta/source/PuertaApp.mc`, `puerta/source/PuertaTest.mc` (nuevos) | proyecto de tests de la puerta, solo `fenix5` |
| `.gitignore` | `puerta/source-gen/` y `puerta/resources-gen/` |

## FORMATO 5 (referencia para todas las tareas)

Palabras de 32 bits **little-endian**. Así los 4 bytes de cada CB salen sueltos y en orden: x0, y0, x1, y1.

```
cabecera, 11 palabras (bytes 0–43):
  0: FORMATO (5) | U << 8 | PB << 16     U: metros por unidad (1, 2 o 4)
  1: NC          2: bytes de S
  3..10: palabras de O, C, CB, K, R, V, P, E
S: UTF-8, rellenada con ceros hasta múltiplo de 4
O, C, CB, K, R, V, P, E: palabras (O, C, CB, R, V, P, E como en el FORMATO 4)
K (nuevo): NC + 1 palabras; K[k] = bit de V donde empiezan los vértices de la calle k
```

**Límite del compilador (medido el 2026-10-26):** un `<string>` no pasa de **32.767 caracteres**. En base64 son
~24.570 bytes de tesela, así que el tope de la tesela `c5` es de 24.000 bytes (lo mismo da el pico de memoria).
Un `jsonData` con una cadena no tiene ese límite.

Desplazamientos en bytes que usa el reloj:
- u16 k de O en `oO + 2k`;
- R de la calle k (u16) en `oC + 4k` y su primer portal (u16) en `oC + 4k + 2`;
- caja de la calle k: bytes `oCB + 4k` … `+3`;
- palabra r de R en `oR + 4r`.

---

### Task 0: Worktree

**Files:** ninguno.

- [ ] **Step 1: Crear el worktree desde `main`**

```bash
git -C ~/code/calle-fenix worktree add ~/code/calle-c5 -b c5-galicia main
cd ~/code/calle-c5 && git log --oneline -1
```
Esperado: el último commit de `main`, con este plan dentro: `docs/plans/2026-10-26-c5-plan1-puerta.md` existe.

- [ ] **Step 2: Comprobar que están los datos de Galicia en el árbol principal**

```bash
ls ~/code/calle-fenix/resources-gen/galicia/t | wc -l
python3 -c "import json;print(json.load(open('$HOME/code/calle-fenix/tools/out/meta-galicia.json'))['t_mayor'])"
```
Esperado: `1780` y `t412`. Si falta algo, **parar**: hay que regenerar Galicia en el árbol principal (`REGION=galicia ./ciq.sh datos`, que tarda ~20 min), y eso es cosa del autor o de la sesión que tenga ese árbol.

---

### Task 1: `tools/formato5.py` con su prueba de ida y vuelta

**Files:**
- Create: `tools/test_formato5.py`
- Create: `tools/formato5.py`

- [ ] **Step 1: Escribir la prueba**

`tools/test_formato5.py`:
```python
#!/usr/bin/env python3
"""Ida y vuelta del FORMATO 5 sobre teselas reales del FORMATO 4, y K contra la referencia (ref.Tes).

    python3 -I tools/test_formato5.py ~/code/calle-fenix/resources-gen/galicia/t
"""
import json
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
        cuatro = F5.codificar(t, 4)
        assert F5.decodificar(cuatro)[1] == 4, f"{f.name}: U = 4"
        n += 1
        mayor = max(mayor, (len(b), f.name))
    assert n > 0, f"no hay teselas en {carpeta}"
    print(f"FORMATO 5: {n} teselas ida y vuelta OK; la mayor, {mayor[1]}, {mayor[0]} bytes")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Ejecutarla y ver que falla**

```bash
cd ~/code/calle-c5 && python3 -I tools/test_formato5.py ~/code/calle-fenix/resources-gen/galicia/t
```
Esperado: `ModuleNotFoundError: No module named 'formato5'`.

- [ ] **Step 3: Escribir `tools/formato5.py`**

```python
#!/usr/bin/env python3
"""FORMATO 5: una tesela del FORMATO 4 (la lista de build_callejero.empaquetar) en bytes, para los relojes de
128 KB (variante c5). Especificación: docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md.

Palabras de 32 bits little-endian (los 4 bytes de cada CB quedan sueltos: x0, y0, x1, y1):
  cabecera (CABECERA palabras): FORMATO | U << 8 | PB << 16, NC, bytes de S, y cuántas palabras tienen
  O, C, CB, K, R, V, P y E; luego S (UTF-8, rellenada a múltiplo de 4) y esas tablas, en ese orden.
U: metros por unidad de las coordenadas de la tesela (1 en ciudad, 4 en el rural; el contenido ya viene en
esas unidades). K (nuevo): por calle, y una más al final, el bit de V donde empiezan los vértices de su
primera tirada: la búsqueda salta una calle lejana sin recorrer sus tiradas.
"""
import struct

FORMATO = 5
CABECERA = 11


def _palabras(ws):
    return struct.pack(f"<{len(ws)}I", *[w & 0xFFFFFFFF for w in ws])


def indice_k(nc, C, R):
    """K: el bit de V de la primera tirada de cada calle (NC + 1), recorriendo R como el reloj."""
    K, o, r = [], 0, 0
    for k in range(nc + 1):
        hasta = C[k] & 0xFFFF       # offset en R de la primera tirada de la calle k
        while r < hasta:
            h1 = R[r + 1] & 0xFFFFFFFF
            nv, paso = h1 >> 26, 2
            if nv == 0:
                nv, paso = R[r + 2], 3
            o += (nv - 1) * 2 * (h1 & 0xF)
            r += paso
        K.append(o)
    return K


def codificar(lista, u=1):
    """Tesela del FORMATO 4 → bytes del FORMATO 5."""
    fmt, nc, pb, S, O, C, CB, R, V, P, E = lista
    assert fmt == 4 and u in (1, 2, 4), (fmt, u)
    s = S.encode("utf-8")
    tablas = [O, C, CB, indice_k(nc, C, R), R, V, P, E]
    cab = [FORMATO | u << 8 | pb << 16, nc, len(s)] + [len(x) for x in tablas]
    assert len(cab) == CABECERA
    return _palabras(cab) + s + b"\0" * (-len(s) % 4) + b"".join(_palabras(x) for x in tablas)


def decodificar(b):
    """Bytes del FORMATO 5 → (lista del FORMATO 4, U, K). Los números, con signo, como en el JSON."""
    cab = struct.unpack_from(f"<{CABECERA}I", b, 0)
    assert cab[0] & 0xFF == FORMATO, cab[0] & 0xFF
    u, pb, nc, ls = (cab[0] >> 8) & 0xFF, (cab[0] >> 16) & 0xFF, cab[1], cab[2]
    p = 4 * CABECERA
    S = b[p:p + ls].decode("utf-8")
    p += ls + (-ls % 4)
    tablas = []
    for m in cab[3:]:
        tablas.append([w - (1 << 32) if w >= 1 << 31 else w for w in struct.unpack_from(f"<{m}I", b, p)])
        p += 4 * m
    assert p == len(b), (p, len(b))
    O, C, CB, K, R, V, P, E = tablas
    return [4, nc, pb, S, O, C, CB, R, V, P, E], u, K
```

- [ ] **Step 4: Ejecutar la prueba**

```bash
cd ~/code/calle-c5 && python3 -I tools/test_formato5.py ~/code/calle-fenix/resources-gen/galicia/t
```
Esperado: `FORMATO 5: 1780 teselas ida y vuelta OK; la mayor, t….json, ~24000 bytes`.

- [ ] **Step 5: Commit**

```bash
cd ~/code/calle-c5 && git add tools/formato5.py tools/test_formato5.py && git commit -m "FORMATO 5: la tesela en bytes, con su índice de salto K, e ida y vuelta sobre Galicia"
```

---

### Task 2: El generador de la puerta y sus tests (fallan hasta tener el lector)

**Files:**
- Create: `tools/puerta_c5.py`
- Create: `puerta/manifest.xml`, `puerta/monkey.jungle`, `puerta/source/PuertaApp.mc`, `puerta/source/PuertaTest.mc`
- Modify: `.gitignore` (añadir al final)

- [ ] **Step 1: Escribir `tools/puerta_c5.py`**

```python
#!/usr/bin/env python3
"""Puerta del plan c5 (docs/plans/2026-10-26-c5-plan1-puerta.md): la tesela más pesada de una región en
FORMATO 5, lo que debe dar el reloj en 40 puntos y el punto más denso, para medir el watchdog.

    python3 -I tools/puerta_c5.py ~/code/calle-fenix/resources-gen/galicia ~/code/calle-fenix/tools/out/meta-galicia.json

Escribe puerta/resources-gen/tesela.json y tesela.xml, puerta/source-gen/Callejero.mc y puerta/source-gen/PuertaDatos.mc.
La tesela va como jsonData con una cadena base64, no como <string>: un recurso de texto no pasa de 32.767 caracteres
(≈ 24.570 bytes de tesela) y t412 tiene 24.632; el jsonData no tiene ese límite, y se carga igual (Teselas.bytes).
Lo esperado sale de ref.Tes (la referencia Python del FORMATO 4) sobre la misma tesela: si el reloj coincide,
el FORMATO 5 y su lector dicen lo mismo que el FORMATO 4.
"""
import base64
import json
import math
import random
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import formato5 as F5  # noqa: E402
import ref  # noqa: E402

PUERTA = TOOLS.parent / "puerta"
LEJOS = 1.0e9
AMBIGUO = 0.2   # m: dos calles o dos portales más parecidos que esto pueden cambiar de orden en Float de 32 bits


def mejores(tes, px, py, meta):
    """Distancia de cada calle al punto (m de la tesela) con su penalización, o LEJOS si pasa de MAXD:
    lo que deja Buscador.buscar en t.mejor para las calles que importan."""
    mejor = [LEJOS] * tes.nc
    for _r, k, clase, area, _ext, vs, _a, _b in tes.tiradas():
        if area and ref.dentro(px, py, vs):
            d = 0.0
        else:
            d2 = (px - vs[0][0]) ** 2 + (py - vs[0][1]) ** 2
            for (ax, ay), (bx, by) in zip(vs, vs[1:]):
                d2 = min(d2, ref.dseg2(px, py, ax, ay, bx, by))
            d = math.sqrt(d2)
        mejor[k] = min(mejor[k], d + meta["pen"][clase])
    return [d if d <= meta["maxd"] else LEJOS for d in mejor]


def dos(mejor):
    """[s1, s2] como Buscador.buscar: el primero gana los empates."""
    s1 = s2 = -1
    for i, d in enumerate(mejor):
        if s1 < 0 or d < mejor[s1]:
            s1, s2 = i, s1
        elif s2 < 0 or d < mejor[s2]:
            s2 = i
    return s1, s2


def portal(tes, k, px, py, meta):
    """(texto del portal más cercano de la calle k a menos de PORTAL_R, o "", y si hay empate dudoso)."""
    r2 = meta["portal_r"] ** 2
    ds = sorted(((px - x) ** 2 + (py - y) ** 2, j, txt) for j, (x, y, txt) in enumerate(tes.portales(k)))
    ds = [d for d in ds if d[0] <= r2]
    if not ds:
        return "", False
    dudoso = len(ds) > 1 and math.sqrt(ds[1][0]) - math.sqrt(ds[0][0]) < AMBIGUO
    return ds[0][2], dudoso


def puntos(tes, caja, meta, n=40, semilla=7):
    """n puntos en la caja (m de la tesela, en múltiplos de 0,25 m: exactos en Float), 30 junto a vértices."""
    rnd = random.Random(semilla)
    x0, y0, x1, y1 = caja
    verts = [v for t in tes.tiradas() for v in t[5]]
    out = []
    while len(out) < n:
        if len(out) < 30:
            vx, vy = rnd.choice(verts)
            px, py = vx + rnd.uniform(-25, 25), vy + rnd.uniform(-25, 25)
        else:
            px, py = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        px, py = round(px * 4) / 4, round(py * 4) / 4
        if not (x0 <= px <= x1 and y0 <= py <= y1):
            continue
        m = mejores(tes, px, py, meta)
        s1, s2 = dos(m)
        if s2 >= 0 and m[s2] < LEJOS and m[s2] - m[s1] < AMBIGUO:
            continue
        calle = tes.nombres[s1] if m[s1] < LEJOS else ""
        num, dudoso = portal(tes, s1, px, py, meta) if calle else ("", False)
        if dudoso:
            continue
        calle2 = tes.nombres[s2] if s2 >= 0 and m[s2] < LEJOS else ""
        out.append((px, py, calle, m[s1] if calle else -1.0, num, calle2))
    return out


def centro_denso(tes, caja, meta):
    """El punto de la rejilla de 25 m con más calles que pasan el filtro de las cajas (CB): el peor para el watchdog."""
    M, U = meta["maxd"] + 1, meta["cb_u"]
    cajas = [(w & 0xFF, (w >> 8) & 0xFF, (w >> 16) & 0xFF, (w >> 24) & 0xFF) for w in (c & 0xFFFFFFFF for c in tes.CB)]
    x0, y0, x1, y1 = caja
    mejor = (-1, 0, 0)
    for gx in range(int(x0), int(x1) + 1, 25):
        for gy in range(int(y0), int(y1) + 1, 25):
            n = sum(1 for a0, b0, a1, b1 in cajas
                    if not (gx + M < a0 * U or gx - M > a1 * U or gy + M < b0 * U or gy - M > b1 * U))
            mejor = max(mejor, (n, gx, gy))
    return mejor


def main():
    rdir, meta = Path(sys.argv[1]).expanduser(), json.loads(Path(sys.argv[2]).expanduser().read_text("utf-8"))
    nombre = meta["t_mayor"]                        # "t412"
    i = int(nombre[1:])
    t = json.loads((rdir / "t" / f"{nombre}.json").read_text("utf-8"))
    cj = json.loads((rdir / "cajas.json").read_text("utf-8"))
    U = meta["tesela"]
    a, b = cj[2 * i] & 0xFFFFFFFF, cj[2 * i + 1] & 0xFFFFFFFF
    caja = [(a & 0xFFFF) * U, (a >> 16) * U, (b & 0xFFFF) * U, (b >> 16) * U]   # m de región, sin margen
    buf = meta["buf"]
    local = (buf, buf, buf + caja[2] - caja[0], buf + caja[3] - caja[1])         # m de la tesela
    b5 = F5.codificar(t, 1)
    assert F5.decodificar(b5)[0] == t
    tes = ref.Tes(t)
    ps = puntos(tes, local, meta)
    n_cb, cx, cy = centro_denso(tes, local, meta)
    ox, oy = caja[0] - buf, caja[1] - buf

    (PUERTA / "resources-gen").mkdir(parents=True, exist_ok=True)
    (PUERTA / "source-gen").mkdir(parents=True, exist_ok=True)
    (PUERTA / "resources-gen" / "tesela.json").write_text(json.dumps(base64.b64encode(b5).decode()), "utf-8")
    (PUERTA / "resources-gen" / "tesela.xml").write_text(
        '<resources>\n    <jsonData id="TeselaPuerta" filename="tesela.json"/>\n</resources>\n', "utf-8")
    pen = ", ".join(str(p) for p in meta["pen"])
    (PUERTA / "source-gen" / "Callejero.mc").write_text(f"""import Toybox.Lang;

// GENERADO por tools/puerta_c5.py: las constantes de {meta['region']} que usa el lector del FORMATO 5. No editar.
module Callejero {{
    const FORMATO = 4;
    const BUF = {buf};
    const MAXD = {meta['maxd']};
    const PORTAL_R = {meta['portal_r']};
    const PEN = [{pen}] as Array<Number>;
    const EXT_U = {meta['ext_u']};
    const EXT_SIN = {meta['ext_sin']};
    const CB_U = {meta['cb_u']};
    var TESELA as Number = {U};
    var COLS as Number = 0;
    var FILAS as Number = 0;
    var IDX as Array<ResourceId or Null> = [] as Array<ResourceId or Null>;
    var CAJAS as ResourceId or Null = null;
}}
""", "utf-8")
    filas = ",\n".join(f'        [{ox + px:.2f}, {oy + py:.2f}, {ref.mc(c)}, {d:.3f}, {ref.mc(nm)}, {ref.mc(c2)}]'
                       for px, py, c, d, nm, c2 in ps)
    (PUERTA / "source-gen" / "PuertaDatos.mc").write_text(f"""import Toybox.Lang;

// GENERADO por tools/puerta_c5.py ({meta['region']} {nombre}, datos OSM {meta['datos']}). No editar a mano.
module PuertaDatos {{
    const ETIQUETA = "{meta['region']} {nombre}: {len(b5)} bytes, {t[1]} calles";
    const CAJA = [{', '.join(str(v) for v in caja)}] as Array<Number>;
    // El punto con más calles tras el filtro de cajas ({n_cb}): el peor caso del watchdog.
    const CENTRO = [{ox + cx:.2f}, {oy + cy:.2f}] as Array<Float>;
    // [x, y (m de región), calle ("" = ninguna a menos de MAXD), d1 (-1 si no hay), portal ("" = ninguno), calle 2]
    const PUNTOS = [
{filas}
    ] as Array<Array>;
}}
""", "utf-8")
    print(f"puerta: {nombre}, {len(b5)} bytes ({len(base64.b64encode(b5))} en base64), {t[1]} calles, "
          f"{len(ps)} puntos, centro denso con {n_cb} calles")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Ejecutarlo**

```bash
cd ~/code/calle-c5 && python3 -I tools/puerta_c5.py ~/code/calle-fenix/resources-gen/galicia ~/code/calle-fenix/tools/out/meta-galicia.json && head -c 300 puerta/source-gen/PuertaDatos.mc
```
Esperado: `puerta: t412, ~24000 bytes (~32000 en base64), 262 calles, 40 puntos, centro denso con N calles`, y el módulo con sus constantes.

- [ ] **Step 3: El proyecto de tests**

`puerta/manifest.xml`:
```xml
<?xml version="1.0"?>
<iq:manifest version="3" xmlns:iq="http://www.garmin.com/xml/connectiq">
    <iq:application id="c5c5c5c5c5c5c5c5c5c5c5c5c5c5c501" type="watch-app" name="@Strings.AppName"
        entry="PuertaApp" launcherIcon="@Drawables.LauncherIcon" minApiLevel="3.1.0">
        <iq:products>
            <iq:product id="fenix5"/>
        </iq:products>
        <iq:permissions/>
        <iq:languages>
            <iq:language>spa</iq:language>
        </iq:languages>
        <iq:barrels/>
    </iq:application>
</iq:manifest>
```

`puerta/monkey.jungle`:
```
# Puerta del plan c5: el lector del FORMATO 5 (../source-c5) con un Callejero mínimo y la tesela más pesada de
# Galicia (tools/puerta_c5.py). Sin el resto de la app: solo tests.
project.manifest = manifest.xml
base.sourcePath = source;source-gen;../source-c5
base.resourcePath = ../resources;resources-gen
```

`puerta/source/PuertaApp.mc`:
```monkeyc
import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

// Solo existe para que los tests de la puerta tengan una app que los lleve.
class PuertaApp extends Application.AppBase {
    function initialize() {
        AppBase.initialize();
    }

    function getInitialView() as [WatchUi.Views] or [WatchUi.Views, WatchUi.InputDelegates] {
        return [new WatchUi.View()];
    }
}
```

`puerta/source/PuertaTest.mc`:
```monkeyc
import Toybox.Lang;
import Toybox.StringUtil;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

// Puerta del plan c5 (docs/plans/2026-10-26-c5-plan1-puerta.md): la tesela más pesada de Galicia en FORMATO 5,
// leída en el fēnix 5. Lo esperado lo calcula tools/puerta_c5.py con la referencia Python del FORMATO 4.
module Puerta {
    function tesela() as Tesela {
        return new Tesela(0, Teselas.bytes(Rez.JsonData.TeselaPuerta), PuertaDatos.CAJA);
    }

    function libre() as Number {
        return System.getSystemStats().freeMemory;
    }

    // La parte de la cadena del Localizador que toca la tesela, n veces seguidas en un mismo evento:
    // cargar el base64, convertirlo, buscar y los dos portales.
    function cadena(n as Number) as Number {
        var x = PuertaDatos.CENTRO[0];
        var y = PuertaDatos.CENTRO[1];
        var hechas = 0;
        for (var k = 0; k < n; k++) {
            var t = tesela();
            var s = Buscador.buscar(t, x, y);
            if (s[0] >= 0) {
                Buscador.portal(t, s[0], x, y);
                hechas++;
            }
            if (s[1] >= 0) {
                Buscador.portal(t, s[1], x, y);
            }
            t = null;   // como en el Localizador: la tesela anterior se suelta antes de cargar otra
        }
        return hechas;
    }
}

(:test)
function puertaVectores(logger as Test.Logger) as Boolean {
    var t = Puerta.tesela();
    var P = PuertaDatos.PUNTOS;
    var ok = true;
    for (var i = 0; i < P.size(); i++) {
        var c = P[i];
        var x = c[0] as Float;
        var y = c[1] as Float;
        var s = Buscador.buscar(t, x, y);
        var a = s[0];
        var b = s[1];
        var calle = a >= 0 && t.mejor[a] <= Callejero.MAXD ? t.nombre(a) : "";
        var d1 = calle.equals("") ? -1.0 : t.mejor[a];
        var num = "";
        if (!calle.equals("")) {
            var p = Buscador.portal(t, a, x, y);
            num = p == null ? "" : p[0] as String;
        }
        var calle2 = b >= 0 && t.mejor[b] <= Callejero.MAXD ? t.nombre(b) : "";
        var bien = calle.equals(c[2]) && (d1 - (c[3] as Float)).abs() < 0.1 && num.equals(c[4]) && calle2.equals(c[5]);
        if (!bien) {
            logger.error("punto " + i + ": esperaba " + c[2] + " " + c[3] + " nº" + c[4] + " / " + c[5] + "; dice "
                + calle + " " + d1 + " nº" + num + " / " + calle2);
            ok = false;
        }
    }
    logger.debug("PUERTA " + PuertaDatos.ETIQUETA + ": " + P.size() + " puntos");
    return ok;
}

(:test)
function puertaMemoria(logger as Test.Logger) as Boolean {
    var l0 = Puerta.libre();
    var s = WatchUi.loadResource(Rez.JsonData.TeselaPuerta) as String;
    var l1 = Puerta.libre();
    var b = StringUtil.convertEncodedString(s, {
        :fromRepresentation => StringUtil.REPRESENTATION_STRING_BASE64,
        :toRepresentation => StringUtil.REPRESENTATION_BYTE_ARRAY
    }) as ByteArray;
    var l2 = Puerta.libre();
    s = null;
    var t = new Tesela(0, b, PuertaDatos.CAJA);
    b = null;
    var l3 = Puerta.libre();
    var pico = l0 - l2;
    logger.debug("PUERTA memoria: base64 " + (l0 - l1) + " B, ByteArray " + (l1 - l2) + " B, pico " + pico
        + " B; tesela lista " + (l0 - l3) + " B (" + t.nc + " calles, " + t.S.length() + " letras)");
    // La app sin tesela deja ~62 KB libres en los de 128 KB (especificación del FORMATO 4): el pico, por debajo de 58 KB.
    return pico < 58 * 1024;
}

(:test)
function puertaWatchdog1(logger as Test.Logger) as Boolean {
    var t0 = System.getTimer();
    var n = Puerta.cadena(1);
    logger.debug("PUERTA cadena ×1: " + (System.getTimer() - t0) + " ms");
    return n == 1;
}

(:test)
function puertaWatchdog2(logger as Test.Logger) as Boolean {
    var t0 = System.getTimer();
    var n = Puerta.cadena(2);
    logger.debug("PUERTA cadena ×2: " + (System.getTimer() - t0) + " ms");
    return n == 2;
}
```

Al final de `.gitignore`:
```
# Puerta del plan c5: los genera tools/puerta_c5.py desde los datos locales
puerta/source-gen/
puerta/resources-gen/
```

- [ ] **Step 4: Compilar y ver que falla**

```bash
cd ~/code/calle-c5 && export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH" && SDK="$(tr -d '\n' < "$HOME/Library/Application Support/Garmin/ConnectIQ/current-sdk.cfg")" && mkdir -p bin && "$SDK/bin/monkeyc" -d fenix5 -f puerta/monkey.jungle -y ~/.garmin/developer_key.der -o bin/puerta.prg -t -w 2>&1 | tail -5
```
Esperado: error de compilación porque `Tesela`, `Teselas` y `Buscador` no existen (falta `source-c5/`).

- [ ] **Step 5: Commit**

```bash
cd ~/code/calle-c5 && git add tools/puerta_c5.py puerta/manifest.xml puerta/monkey.jungle puerta/source/PuertaApp.mc puerta/source/PuertaTest.mc .gitignore && git commit -m "Puerta c5: la tesela más pesada de Galicia en FORMATO 5 y los tests que debe pasar el fēnix 5"
```

---

### Task 3: `source-c5/Tesela.mc`

**Files:**
- Create: `source-c5/Tesela.mc`

- [ ] **Step 1: Escribirlo**

```monkeyc
import Toybox.Lang;
import Toybox.StringUtil;
import Toybox.WatchUi;

// Una tesela del FORMATO 5 (tools/formato5.py): la del FORMATO 4 en bytes, para los relojes de 128 KB (variante
// c5). Mismo contenido y misma interfaz que source/Tesela.mc, pero las tablas se leen del ByteArray B: en
// reposo ocupa 4 B por número en lugar de 5, y al cargar se pasa por el texto base64 (pico ~2,3 veces B).
// Las coordenadas de la tesela van en unidades de u m (1 en ciudad, 4 en el rural); x, y, ox… en metros.
class Tesela {
    var idx as Number;
    var ox as Float;    // esquina SO de la tesela con su margen, en metros de región
    var oy as Float;
    var x1 as Float;    // esquina NE sin el margen
    var y1 as Float;
    var u as Number;    // metros por unidad
    var nc as Number;
    var pb as Number;
    var S as String;
    var B as ByteArray;
    var oO as Number;   // dónde empieza cada tabla en B, en bytes
    var oC as Number;
    var oCB as Number;
    var oK as Number;
    var oR as Number;
    var oV as Number;
    var oP as Number;
    var oE as Number;
    var nE as Number;   // palabras de E (pares índice, valor)
    var mejor as Array<Float>;
    var mejorRun as Array<Number>;

    // caja: [x0, y0, x1, y1] de la tesela sin margen, en metros de región (Teselas.caja).
    function initialize(i as Number, b as ByteArray, caja as Array<Number>) {
        var h = Teselas.palabra(b, 0);
        if ((h & 0xFF) != Teselas.FORMATO) {
            throw new Lang.InvalidValueException("tesela con formato " + (h & 0xFF));
        }
        u = (h >> 8) & 0xFF;
        pb = (h >> 16) & 0xFF;
        nc = Teselas.palabra(b, 4);
        var ls = Teselas.palabra(b, 8);
        var p = 4 * Teselas.CABECERA;
        S = StringUtil.convertEncodedString(b.slice(p, p + ls), {
            :fromRepresentation => StringUtil.REPRESENTATION_BYTE_ARRAY,
            :toRepresentation => StringUtil.REPRESENTATION_STRING_PLAIN_TEXT
        }) as String;
        p += (ls + 3) & ~3;
        oO = p;
        p += 4 * Teselas.palabra(b, 12);
        oC = p;
        p += 4 * Teselas.palabra(b, 16);
        oCB = p;
        p += 4 * Teselas.palabra(b, 20);
        oK = p;
        p += 4 * Teselas.palabra(b, 24);
        oR = p;
        p += 4 * Teselas.palabra(b, 28);
        oV = p;
        p += 4 * Teselas.palabra(b, 32);
        oP = p;
        p += 4 * Teselas.palabra(b, 36);
        oE = p;
        nE = Teselas.palabra(b, 40);
        B = b;
        idx = i;
        var m = Callejero.BUF * u;
        ox = (caja[0] - m).toFloat();
        oy = (caja[1] - m).toFloat();
        x1 = caja[2].toFloat();
        y1 = caja[3].toFloat();
        mejor = new Array<Float>[nc];
        mejorRun = new Array<Number>[nc];
    }

    // Dónde empieza en S el nombre k.
    function inicio(k as Number) as Number {
        var q = oO + 2 * k;
        return B[q] | (B[q + 1] << 8);
    }

    // El nombre k: una calle (k < nc) o un sufijo de portal.
    function nombre(k as Number) as String {
        return S.substring(inicio(k), inicio(k + 1) - 1) as String;
    }

    // [A, B]: las calles que cruzan en los extremos del trozo más cercano de la calle s en la última búsqueda.
    function tramo(s as Number) as Array<String or Null> {
        var r = mejorRun[s];
        if (r == null || r < 0) {
            return [null, null] as Array<String or Null>;
        }
        var h = Teselas.palabra(B, oR + 4 * (r + 1));
        var a = (h >> 6) & 0x3FF;
        var b = (h >> 16) & 0x3FF;
        return [a > 0 ? nombre(a - 1) : null, b > 0 ? nombre(b - 1) : null] as Array<String or Null>;
    }

    // Como en el FORMATO 4: vale mientras el punto no salga de la tesela más la holgura (BUF − MAXD).
    function cubre(x as Float, y as Float) as Boolean {
        var h = Callejero.BUF - Callejero.MAXD;
        var m = Callejero.BUF * u;
        var x0 = ox + m;
        var y0 = oy + m;
        return x >= x0 - h && x <= x1 + h && y >= y0 - h && y <= y1 + h;
    }

    // Índice de la calle con ese nombre, o -1.
    function indiceDe(n as String) as Number {
        var p = S.find("\n" + n + "\n");
        if (p == null) {
            return -1;
        }
        p += 1;
        var lo = 0;
        var hi = nc - 1;
        while (lo <= hi) {
            var mid = (lo + hi) / 2;
            var v = inicio(mid);
            if (v == p) {
                return mid;
            } else if (v < p) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        return -1;
    }
}

module Teselas {
    const FORMATO = 5;
    const CABECERA = 11;    // palabras de la cabecera (tools/formato5.py)

    // La palabra de 32 bits little-endian que empieza en el byte k.
    function palabra(b as ByteArray, k as Number) as Number {
        return b[k] | (b[k + 1] << 8) | (b[k + 2] << 16) | (b[k + 3] << 24);
    }

    // El recurso (texto base64, en Rez.Strings o en un jsonData) como bytes. El texto se suelta al volver.
    function bytes(rid as ResourceId) as ByteArray {
        var s = WatchUi.loadResource(rid) as String;
        return StringUtil.convertEncodedString(s, {
            :fromRepresentation => StringUtil.REPRESENTATION_STRING_BASE64,
            :toRepresentation => StringUtil.REPRESENTATION_BYTE_ARRAY
        }) as ByteArray;
    }

    // null si la celda no tiene calles.
    function cargar(i as Number) as Tesela or Null {
        var rid = Callejero.IDX[i];
        if (rid == null) {
            return null;
        }
        return new Tesela(i, bytes(rid), caja(i));
    }

    // [x0, y0, x1, y1] de la tesela i sin margen, en metros de región (igual que en el FORMATO 4).
    function caja(i as Number) as Array<Number> {
        var T = Callejero.TESELA;
        var rc = Callejero.CAJAS;
        if (rc == null) {
            var c = (i % Callejero.COLS) * T;
            var f = (i / Callejero.COLS) * T;
            return [c, f, c + T, f + T] as Array<Number>;
        }
        var cajas = WatchUi.loadResource(rc) as Array<Number>;
        var a = cajas[2 * i];
        var b = cajas[2 * i + 1];
        return [(a & 0xFFFF) * T, ((a >> 16) & 0xFFFF) * T, (b & 0xFFFF) * T, ((b >> 16) & 0xFFFF) * T] as Array<Number>;
    }
}
```

- [ ] **Step 2: Compilar**

Con el mismo comando del Task 2, paso 4. Esperado: ya no falta `Tesela` ni `Teselas`; sigue faltando `Buscador`.

- [ ] **Step 3: Commit**

```bash
cd ~/code/calle-c5 && git add source-c5/Tesela.mc && git commit -m "c5: Tesela y Teselas del FORMATO 5 (tablas leídas del ByteArray)"
```

---

### Task 4: `source-c5/Buscador.mc`

**Files:**
- Create: `source-c5/Buscador.mc`

- [ ] **Step 1: Escribirlo**

Es el mismo algoritmo que `source/Buscador.mc`, con tres cambios. La caja gruesa se lee en bytes sueltos. Una calle lejana no se recorre, porque K da dónde empiezan sus vértices. Las distancias se calculan en unidades de la tesela y se pasan a metros al final. En el bucle de vértices, la lectura de palabras va en línea, para ahorrarse la llamada a `Teselas.palabra`, que es el camino caliente. `Resultado`, `consultar` y `rellenar` llegan en el plan 2, cuando `Resultado` salga de `source/Buscador.mc`.

```monkeyc
import Toybox.Lang;
import Toybox.Math;

// La calle más cercana dentro de una tesela del FORMATO 5. El algoritmo es el de source/Buscador.mc (y el de
// Ref.buscar() de tools/ref.py); cambia cómo se leen las tablas. Las calles lejanas se descartan por su caja
// gruesa (4 bytes) sin recorrerlas: K da dónde empiezan sus vértices.
module Buscador {
    const LEJOS = 1.0e9;

    // Rellena t.mejor (metros, con la penalización de su clase) y t.mejorRun; devuelve [s1, s2] o -1.
    function buscar(t as Tesela, x as Float, y as Float) as Array<Number> {
        var u = t.u;
        var uf = u.toFloat();
        var px = (x - t.ox) / uf;
        var py = (y - t.oy) / uf;
        var maxd = Callejero.MAXD.toFloat() / uf;
        var maxd2 = maxd * maxd;
        var mejor = t.mejor;
        var mejorRun = t.mejorRun;
        for (var i = 0; i < mejor.size(); i++) {
            mejor[i] = LEJOS;
            mejorRun[i] = -1;
        }
        var B = t.B;
        var oC = t.oC;
        var oCB = t.oCB;
        var oK = t.oK;
        var oR = t.oR;
        var oV = t.oV;
        var U = Callejero.CB_U;
        var pxi = px.toNumber();
        var pyi = py.toNumber();
        var M = Callejero.MAXD / u + 1;
        for (var calle = 0; calle < t.nc; calle++) {
            var q = oCB + 4 * calle;
            if (pxi + M < B[q] * U || pxi - M > B[q + 2] * U || pyi + M < B[q + 1] * U || pyi - M > B[q + 3] * U) {
                continue;
            }
            q = oC + 4 * calle;
            var r = B[q] | (B[q + 1] << 8);
            var fin = B[q + 4] | (B[q + 5] << 8);
            var o = Teselas.palabra(B, oK + 4 * calle);
            while (r < fin) {
                var a = oR + 4 * r;
                var h0 = B[a] | (B[a + 1] << 8) | (B[a + 2] << 16) | (B[a + 3] << 24);
                var h1 = B[a + 4] | (B[a + 5] << 8) | (B[a + 6] << 16) | (B[a + 7] << 24);
                var nv = (h1 >> 26) & 0x3F;
                var ro = r;
                if (nv == 0) {
                    nv = B[a + 8] | (B[a + 9] << 8) | (B[a + 10] << 16) | (B[a + 11] << 24);
                    r += 3;
                } else {
                    r += 2;
                }
                var w = h1 & 0xF;
                var ax = (h0 & 0x1FFF).toFloat();
                var ay = ((h0 >> 13) & 0x1FFF).toFloat();
                var ext = (h0 >> 26) & 0x1F;
                if (ext != Callejero.EXT_SIN) {
                    var e = (ext * Callejero.EXT_U).toFloat();
                    var dx = (px > ax ? px - ax : ax - px) - e;
                    var dy = (py > ay ? py - ay : ay - py) - e;
                    dx = dx > 0.0 ? dx : 0.0;
                    dy = dy > 0.0 ? dy : 0.0;
                    if (dx * dx + dy * dy > maxd2) {
                        o += (nv - 1) * 2 * w;
                        continue;
                    }
                }
                var area = ((h0 >> 31) & 1) == 1;
                var dentro = false;
                var k2 = 2 * w;
                var mk = (1 << k2) - 1;
                var mw = (1 << w) - 1;
                var medio = 1 << (w - 1);
                var d2 = (px - ax) * (px - ax) + (py - ay) * (py - ay);
                for (var j = 1; j < nv; j++) {
                    // 2w bits del flujo desde el bit o: dx en los w bajos, dy en los w altos.
                    var i = oV + 4 * (o >> 5);
                    var s = o & 31;
                    var v = (B[i] | (B[i + 1] << 8) | (B[i + 2] << 16) | (B[i + 3] << 24)) >> s;
                    if (s + k2 > 32) {
                        var v2 = B[i + 4] | (B[i + 5] << 8) | (B[i + 6] << 16) | (B[i + 7] << 24);
                        v = (v & ((1 << (32 - s)) - 1)) | (v2 << (32 - s));
                    }
                    v = v & mk;
                    o += k2;
                    var ddx = v & mw;
                    var ddy = (v >> w) & mw;
                    var bx = ax + (ddx >= medio ? ddx - (mw + 1) : ddx).toFloat();
                    var by = ay + (ddy >= medio ? ddy - (mw + 1) : ddy).toFloat();
                    var sx = bx - ax;
                    var sy = by - ay;
                    var l2 = sx * sx + sy * sy;
                    var tt = 0.0;
                    if (l2 > 0.0) {
                        tt = ((px - ax) * sx + (py - ay) * sy) / l2;
                        tt = tt < 0.0 ? 0.0 : (tt > 1.0 ? 1.0 : tt);
                    }
                    var ex = px - (ax + tt * sx);
                    var ey = py - (ay + tt * sy);
                    var e2 = ex * ex + ey * ey;
                    if (e2 < d2) {
                        d2 = e2;
                    }
                    if (area && ((ay > py) != (by > py)) && px < sx * (py - ay) / sy + ax) {
                        dentro = !dentro;
                    }
                    ax = bx;
                    ay = by;
                }
                var d = dentro ? 0.0 : Math.sqrt(d2).toFloat() * uf;
                d += Callejero.PEN[(h1 >> 4) & 3];
                if (d < mejor[calle]) {
                    mejor[calle] = d;
                    mejorRun[calle] = ro;
                }
            }
        }
        var s1 = -1;
        var s2 = -1;
        for (var i = 0; i < mejor.size(); i++) {
            if (s1 < 0 || mejor[i] < mejor[s1]) {
                s2 = s1;
                s1 = i;
            } else if (s2 < 0 || mejor[i] < mejor[s2]) {
                s2 = i;
            }
        }
        return [s1, s2] as Array<Number>;
    }

    // [texto del número, distancia en m] del portal más cercano de la calle s a menos de PORTAL_R, o null.
    function portal(t as Tesela, s as Number, x as Float, y as Float) as Array or Null {
        var B = t.B;
        var q = t.oC + 4 * s;
        var j0 = B[q + 2] | (B[q + 3] << 8);
        var j1 = B[q + 6] | (B[q + 7] << 8);
        var pb = t.pb;
        var m = (1 << pb) - 1;
        var uf = t.u.toFloat();
        var px = (x - t.ox) / uf;
        var py = (y - t.oy) / uf;
        var rr = Callejero.PORTAL_R.toFloat() / uf;
        var r2 = rr * rr;
        var mejorJ = -1;
        var mejorD2 = r2;
        for (var j = j0; j < j1; j++) {
            var w = Teselas.palabra(B, t.oP + 4 * j);
            var dx = px - (w & m).toFloat();
            var dy = py - ((w >> pb) & m).toFloat();
            var d2 = dx * dx + dy * dy;
            if (mejorJ < 0 ? d2 <= r2 : d2 < mejorD2) {
                mejorD2 = d2;
                mejorJ = j;
            }
        }
        if (mejorJ < 0) {
            return null;
        }
        return [textoNumero(t, j0, mejorJ), Math.sqrt(mejorD2).toFloat() * uf];
    }

    // El número del portal j, cuya calle empieza en j0: suma de saltos desde el primero, o el último escape.
    function textoNumero(t as Tesela, j0 as Number, j as Number) as String {
        var d = 2 * t.pb;
        var esc = (1 << (29 - d)) - 1;
        var n = 0;
        var sc = 0;
        for (var i = j0; i <= j; i++) {
            var w = Teselas.palabra(t.B, t.oP + 4 * i);
            var salto = (w >> d) & esc;
            sc = (w >> 29) & 7;
            if (salto == esc && sc == 7) {
                var e = escape(t, i);
                n = e & 0xFFF;
                sc = (e >> 12) & 0x3FF;
            } else {
                n += salto;
            }
        }
        var suf = sc > 0 ? t.nombre(t.nc + sc - 1) : "";
        return n == 0 ? suf : n.toString() + suf;
    }

    // Número y sufijo del portal i en la tabla de escapes (pares índice, valor; ordenada por índice).
    function escape(t as Tesela, i as Number) as Number {
        var lo = 0;
        var hi = t.nE / 2 - 1;
        while (lo <= hi) {
            var mid = (lo + hi) / 2;
            var v = Teselas.palabra(t.B, t.oE + 8 * mid);
            if (v == i) {
                return Teselas.palabra(t.B, t.oE + 8 * mid + 4);
            } else if (v < i) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        throw new Lang.InvalidValueException("portal " + i + " sin escape");
    }
}
```

- [ ] **Step 2: Compilar**

Con el mismo comando del Task 2, paso 4. Esperado: `BUILD SUCCESSFUL`.

- [ ] **Step 3: Commit**

```bash
cd ~/code/calle-c5 && git add source-c5/Buscador.mc && git commit -m "c5: Buscador del FORMATO 5 (cajas por bytes, salto por K, unidades de la tesela)"
```

---

### Task 5: Pasar la puerta en el simulador del fēnix 5

**Files:** ninguno (solo se ejecuta).

- [ ] **Step 1: Coger el candado, ejecutar y soltarlo**

```bash
cd ~/code/calle-c5 && until mkdir /tmp/calles-sim.lock 2>/dev/null; do sleep 20; done; echo "calle-c5 $$ $(date +%H:%M)" > /tmp/calles-sim.lock/quien
export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"; SDK="$(tr -d '\n' < "$HOME/Library/Application Support/Garmin/ConnectIQ/current-sdk.cfg")"
pgrep -f ConnectIQ.app >/dev/null || { open "$SDK/bin/ConnectIQ.app"; sleep 5; }
"$SDK/bin/monkeydo" bin/puerta.prg fenix5 -t 2>&1 | tee bin/puerta.log | grep -E "PUERTA|ERROR|PASS|FAIL|Watchdog|Tripped"
mv /tmp/calles-sim.lock /tmp/calles-sim.lock-liberado-$(date +%s)
```
Esperado: los 4 tests en `PASS`, y las líneas `PUERTA` con la memoria (pico) y los milisegundos de la cadena ×1 y ×2.

- [ ] **Step 2: Si `puertaVectores` falla**

Es un error del lector, no de la idea. Hay que comparar la línea `ERROR` con `tools/formato5.py` y con la sección *FORMATO 5* de este plan: offsets, little-endian y K. El fallo se reproduce en Python antes de tocar el `.mc`: `decodificar` y `ref.Tes` sobre `t412`. Corregir y volver al paso 1.

- [ ] **Step 3: Leer el resultado contra los criterios**

| Test | Pasa | Si no pasa |
|---|---|---|
| `puertaVectores` | 40/40 | paso 2 |
| `puertaMemoria` | pico < 58 KB | tope de la tesela c5 a 22 KB de bytes en el plan 2 (más teselas; hay sitio) |
| `puertaWatchdog1` | PASS | **no-go para bytes en ciudad:** se aplica la salida de la especificación (ciudad en FORMATO 4) |
| `puertaWatchdog2` | PASS (margen ≥ ×2; la especificación pide ×1,5) | si solo pasa ×1: añadir un test con la cadena ×1 más una `Buscador.buscar` extra en el mismo evento (≈ ×1,5) y decidir con el autor |

---

### Task 6: Dejar el resultado escrito y decidir

**Files:**
- Modify: `docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md` (añadir al final una sección «Resultado de la puerta»)

- [ ] **Step 1: Añadir a la especificación**

Al final, con las cifras reales de `bin/puerta.log`:
```markdown
## Resultado de la puerta (plan 1, AAAA-MM-DD)

| Medida | Resultado |
|---|---|
| Tesela | galicia t412: N bytes (N en base64), 262 calles |
| Vectores | 40/40 iguales al FORMATO 4 (ref.Tes) |
| Memoria | base64 N B · ByteArray N B · pico N B · tesela lista N B |
| Cadena ×1 / ×2 | N ms / N ms, sin watchdog (o: watchdog en …) |

Decisión: … (sigue el plan 2 / salida de la especificación).
```

- [ ] **Step 2: Commit**

```bash
cd ~/code/calle-c5 && git add docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md && git commit -m "Especificación c5: resultado de la puerta en el fēnix 5"
```

- [ ] **Step 3: Avisar**

Hay que avisar a dos personas:
- **Al autor:** el resultado, con la tabla, y si se sigue con el plan 2.
- **A la coordinadora**: los commits de la rama `c5-galicia`. Este plan no toca ningún fichero existente salvo `.gitignore` y la especificación.
