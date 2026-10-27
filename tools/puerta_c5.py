#!/usr/bin/env python3
"""Puerta del plan c5 (docs/plans/2026-10-26-c5-plan1-puerta.md): la tesela más pesada de una región en
FORMATO 5, lo que debe dar el reloj en 40 puntos y el punto más denso, para medir el watchdog.

    python3 -I tools/puerta_c5.py ~/code/calle-fenix/resources-gen/galicia ~/code/calle-fenix/tools/out/meta-galicia.json [modo]

Modo de la puerta como app (puerta/app.jungle): teselas (por defecto, escalera FORMATO 5), zonas:K
(la tesela K de la escalera y, con ella cargada, las zonas), previa:K (lo mismo tras cargar y soltar la tesela 0), f4
(escalera de teselas FORMATO 4), b64:K (zonas:K con una conversión base64 de 1 KB antes del lastre), hueco[:J] (el mayor
ByteArray que se deja reservar, tras J teselas de la escalera), modulos (¿se paga otra vez la retención del primer
recurso al leer Rez.Strings?), f4z:J (la tesela F4 J como primera y las zonas) o trozos:1|2|3 (t412 en 4 trozos:
concatenados, Array<ByteArray>, o los 4 en un jsonData). Con «+frag» al final, el lastre va en trozos de 256 B.

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
import shutil
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


ESCALERA_KB = (6, 8, 10, 12, 14, 16, 18, 20)


def zonas_escalera(rdir):
    """[(heap estimado, fichero)]: la zona real (FORMATO 4) más cercana a cada peso de ESCALERA_KB, con el heap
    estimado de build_callejero.empaquetar_zona. El modo app las carga de menor a mayor con la tesela en memoria."""
    hs = []
    for f in sorted((rdir / "z").glob("z*.json")):
        z = json.loads(f.read_text("utf-8"))
        nums = sum(len(x) if isinstance(x, list) else 1 for x in z[2:])
        hs.append((int(5 * (nums + 7) + len(z[1].encode()) + 20), f))
    out = []
    for kb in ESCALERA_KB:
        h, f = min(hs, key=lambda e: abs(e[0] - kb * 1024))
        if not out or out[-1][0] != h:
            out.append((h, f))
    return out


TESELAS_OBJ = (12000, 14000, 16000, 18000, 20000, 22000, 24000)


def teselas_escalera(rdir, cj, U):
    """[(bytes, nombre, caja)] en orden creciente: la tesela (FORMATO 5) más cercana a cada tamaño de TESELAS_OBJ, sin
    repetir, y al final la mayor. caja = [x0, y0, x1, y1] en m de región, sin margen."""
    tam = []
    for f in sorted((rdir / "t").glob("t*.json")):
        tam.append((len(F5.codificar(json.loads(f.read_text("utf-8")), 1)), f.stem))
    elegidas = []
    for obj in TESELAS_OBJ:
        e = min(tam, key=lambda e: abs(e[0] - obj))
        if e not in elegidas:
            elegidas.append(e)
    mayor = max(tam)
    if mayor not in elegidas:
        elegidas.append(mayor)
    out = []
    for n, nombre in sorted(elegidas):
        i = int(nombre[1:])
        a, b = cj[2 * i] & 0xFFFFFFFF, cj[2 * i + 1] & 0xFFFFFFFF
        out.append((n, nombre, [(a & 0xFFFF) * U, (a >> 16) * U, (b & 0xFFFF) * U, (b >> 16) * U]))
    return out


F4_OBJ = (14000, 18000, 22000, 26000, 28000, 30000, 32000)


def f4_escalera(rdir):
    """[(heap estimado, fichero)]: teselas FORMATO 4 (JSON tal cual) de heap estimado más cercano a F4_OBJ, sin repetir.
    Heap: la fórmula de build_callejero.empaquetar."""
    hs = []
    for f in sorted((rdir / "t").glob("t*.json")):
        t = json.loads(f.read_text("utf-8"))
        nums = sum(len(x) for x in t[4:11])
        hs.append((int(5 * (nums + 10) + len(t[3].encode()) + 20 + 10 * t[1]), f))
    out = []
    for obj in F4_OBJ:
        e = min(hs, key=lambda e: abs(e[0] - obj))
        if e not in out:
            out.append(e)
    if max(hs)[0] < F4_OBJ[-1] - 1000:
        # Ninguna real llega al último objetivo: una sintética, la mayor más los arrays de otra, solo para medir la
        # carga (el modo f4 no la lee). Va a tools/out, fuera de git.
        h0, f0 = max(hs)
        t = json.loads(f0.read_text("utf-8"))
        for h, f in sorted(hs, reverse=True):
            o = json.loads(f.read_text("utf-8"))
            nums = sum(len(x) for x in o[4:11])
            extra = int(5 * nums + len(o[3].encode()) + 10 * o[1])
            if h0 + extra <= F4_OBJ[-1] + 500:
                break
        for x in range(4, 11):
            t[x] = t[x] + o[x]
        t[3] = t[3] + o[3]
        t[1] = t[1] + o[1]
        nums = sum(len(x) for x in t[4:11])
        hsint = int(5 * (nums + 10) + len(t[3].encode()) + 20 + 10 * t[1])
        sint = Path(__file__).resolve().parent / "out" / "f4-sintetica.json"
        sint.parent.mkdir(exist_ok=True)
        sint.write_text(json.dumps(t, ensure_ascii=False, separators=(",", ":")), "utf-8")
        out.append((hsint, sint))
    return sorted(out, key=lambda e: e[0])


def main():
    modo = sys.argv[3] if len(sys.argv) > 3 else "teselas"
    frag = modo.endswith("+frag")                   # lastre en trozos pequeños, como el heap de la app real
    base, _, arg = modo.removesuffix("+frag").partition(":")
    codigos = {"teselas": 0, "zonas": 1, "previa": 2, "f4": 3, "b64": 4, "hueco": 5, "modulos": 6, "f4z": 7, "trozos": 8}
    if base not in codigos or (base in ("zonas", "previa", "b64", "f4z", "trozos") and not arg.isdigit()):
        sys.exit(f"modo desconocido: {modo} (teselas, zonas:K, previa:K, f4, b64:K, hueco[:J], modulos, f4z:J, "
                 f"trozos:1|2|3; +frag al final para el lastre en trozos)")
    app_modo, app_tesela = codigos[base], int(arg or 0)
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
    # Salida C: la tesela en 4 trozos de base64 (cada uno, bytes múltiplo de 3), sueltos y en un solo jsonData.
    n3 = (len(b5) // 4 + 2) // 3 * 3
    trozos = [base64.b64encode(b5[k:k + n3]).decode() for k in range(0, len(b5), n3)]
    for k, tz in enumerate(trozos):
        (PUERTA / "resources-gen" / f"trozo{k}.json").write_text(json.dumps(tz), "utf-8")
    (PUERTA / "resources-gen" / "trozos.json").write_text(json.dumps(trozos), "utf-8")
    (PUERTA / "resources-gen" / "trozos.xml").write_text(
        "<resources>\n" + "".join(f'    <jsonData id="Trozo{k}" filename="trozo{k}.json"/>\n' for k in range(len(trozos)))
        + '    <jsonData id="Trozos" filename="trozos.json"/>\n</resources>\n', "utf-8")
    zs = zonas_escalera(rdir)
    for k, (_h, f) in enumerate(zs):
        shutil.copyfile(f, PUERTA / "resources-gen" / f"zona{k}.json")
    (PUERTA / "resources-gen" / "zonas.xml").write_text(
        "<resources>\n" + "".join(f'    <jsonData id="ZonaPrueba{k}" filename="zona{k}.json"/>\n'
                                  for k in range(len(zs))) + "</resources>\n", "utf-8")
    ts = teselas_escalera(rdir, cj, U)
    for k, (_n, nm, _c) in enumerate(ts):
        bk = F5.codificar(json.loads((rdir / "t" / f"{nm}.json").read_text("utf-8")), 1)
        (PUERTA / "resources-gen" / f"tesela{k}.json").write_text(json.dumps(base64.b64encode(bk).decode()), "utf-8")
    (PUERTA / "resources-gen" / "teselas.xml").write_text(
        "<resources>\n" + "".join(f'    <jsonData id="TeselaPrueba{k}" filename="tesela{k}.json"/>\n'
                                  for k in range(len(ts))) + "</resources>\n", "utf-8")
    f4 = f4_escalera(rdir)
    for j, (_h, f) in enumerate(f4):
        shutil.copyfile(f, PUERTA / "resources-gen" / f"f4_{j}.json")
    (PUERTA / "resources-gen" / "teselasf4.xml").write_text(
        "<resources>\n" + "".join(f'    <jsonData id="TeselaF4_{j}" filename="f4_{j}.json"/>\n'
                                  for j in range(len(f4))) + "</resources>\n", "utf-8")
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
    // Escalera del modo app: zonas reales de {meta['region']} ({', '.join(f.stem for _h, f in zs)}), heap estimado.
    const ZONAS_EST = [{', '.join(str(h) for h, _f in zs)}] as Array<Number>;

    // Escalera de teselas del modo app ({', '.join(nm for _n, nm, _c in ts)}): bytes, caja (m de región) y centro de la caja.
    const TESELAS_BYTES = [{', '.join(str(n) for n, _nm, _c in ts)}] as Array<Number>;
    const TESELAS_CAJA = [{', '.join('[' + ', '.join(str(v) for v in c) + ']' for _n, _nm, c in ts)}] as Array<Array<Number>>;
    const TESELAS_CENTRO = [{', '.join(f'[{(c[0] + c[2]) / 2:.1f}, {(c[1] + c[3]) / 2:.1f}]' for _n, _nm, c in ts)}] as Array<Array<Float>>;
    const APP_MODO = {app_modo};
    const APP_TESELA = {app_tesela};
    const APP_FRAG = {str(frag).lower()};
    // 768 bytes de la tesela en base64 (1.024 caracteres): la conversión de prueba del modo b64.
    const B64_1K = "{base64.b64encode(b5[:768]).decode()}";

    function trozos() as Array<ResourceId> {{
        return [{', '.join(f'Rez.JsonData.Trozo{k}' for k in range(len(trozos)))}] as Array<ResourceId>;
    }}

    // Teselas FORMATO 4 en JSON ({', '.join(f.stem for _h, f in f4)}), heap estimado.
    const F4_EST = [{', '.join(str(h) for h, _f in f4)}] as Array<Number>;

    function teselasF4() as Array<ResourceId> {{
        return [{', '.join(f'Rez.JsonData.TeselaF4_{j}' for j in range(len(f4)))}] as Array<ResourceId>;
    }}

    function teselas() as Array<ResourceId> {{
        return [{', '.join(f'Rez.JsonData.TeselaPrueba{k}' for k in range(len(ts)))}] as Array<ResourceId>;
    }}

    function zonas() as Array<ResourceId> {{
        return [{', '.join(f'Rez.JsonData.ZonaPrueba{k}' for k in range(len(zs)))}] as Array<ResourceId>;
    }}
}}
""", "utf-8")
    print(f"puerta: {nombre}, {len(b5)} bytes ({len(base64.b64encode(b5))} en base64), {t[1]} calles, "
          f"{len(ps)} puntos, centro denso con {n_cb} calles; zonas {[h for h, _f in zs]}; "
          f"teselas {[n for n, _nm, _c in ts]}; f4 {[h for h, _f in f4]}; trozos {[len(x) for x in trozos]}; modo {modo}")


if __name__ == "__main__":
    main()
