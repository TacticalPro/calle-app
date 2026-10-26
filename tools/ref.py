#!/usr/bin/env python3
"""Referencia de CALLE en Python: lo mismo que hará el reloj, escrito aparte del generador.

    ref.py --region santiago                      autotest: fuerza bruta (calles, portales, tramos,
                                                  zonas) + puntos de control
    ref.py --region santiago --punto 42.88 -8.54  qué diría el reloj en ese sitio
    ref.py --region santiago --derivar            (re)escribe tools/puntos_control-<region>.json
    ref.py --region santiago --gen-tests          escribe test-gen/VectoresTest.mc

Lee solo lo que lee el reloj (las teselas y sus constantes, en tools/out/meta-<region>.json)
y, para la fuerza bruta, las calles enteras sin teselar (tools/out/geom-<region>.json).
No importa nada de build_callejero.py: si los dos coinciden, no es por compartir un error.
"""
import argparse
import json
import math
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = TOOLS / "out"
TOL = 1.0  # m: la cuantización a metro entero de las teselas mueve las distancias menos que esto
# Dos portales, cada uno redondeado al metro (hasta 0,71 m), pueden cambiar su diferencia de distancias hasta
# 2 · 0,71 ≈ 1,41 m: más cerca que eso, el orden entre ellos no se compara (Barcelona, 2026-10-26: el 30 y el 32
# de Fastenrath a 4,9 y 6,0 m).
TOL_PORTAL = 1.5


def dseg2(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    ex, ey = px - (ax + t * dx), py - (ay + t * dy)
    return ex * ex + ey * ey


def dentro(px, py, pts):
    c = False
    j = len(pts) - 1
    for i in range(len(pts)):
        (xi, yi), (xj, yj) = pts[i], pts[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def bits(V, o, k):
    """k bits del flujo V desde el bit o (como Buscador en el reloj)."""
    i, s = o >> 5, o & 31
    w = (V[i] & 0xFFFFFFFF) >> s
    if s + k > 32:
        w |= (V[i + 1] & 0xFFFFFFFF) << (32 - s)
    return w & ((1 << k) - 1)


def con_signo(v, w):
    return v - (1 << w) if v >= 1 << (w - 1) else v


class Tes:
    """Una tesela del FORMATO 4 (tools/build_callejero.py), desempaquetada a la manera del reloj."""

    def __init__(self, t):
        fmt, self.nc, self.pb, self.S, O, self.C, self.CB, self.R, self.V, self.P, E = t[:11]
        self.fmt = fmt
        # Variante b: la unidad de la tesela va en los bits altos de PB (sin ellos, 1 m) y K, al final, solo
        # acelera el reloj (salta las calles lejanas); aquí se recorren todas.
        self.u = (self.pb >> 8) or 1
        self.pb &= 0xFF
        n = self.S.count("\n") - 1
        offs = [(O[j // 2] >> (16 * (j % 2))) & 0xFFFF for j in range(n + 1)]
        self.nombres = [self.S[offs[k]:offs[k + 1] - 1] for k in range(n)]
        self.E = {E[j]: E[j + 1] for j in range(0, len(E), 2)}

    def c(self, k):
        v = self.C[k] & 0xFFFFFFFF
        return v & 0xFFFF, v >> 16

    def tiradas(self):
        """(offset en R, calle, clase, área, ext, vértices, A, B) de cada tirada, en orden."""
        R, k, o, r, out = self.R, 0, 0, 0, []
        while r < len(R):
            while self.c(k + 1)[0] <= r:
                k += 1
            h0, h1 = R[r] & 0xFFFFFFFF, R[r + 1] & 0xFFFFFFFF
            x, y, ext, area = h0 & 0x1FFF, (h0 >> 13) & 0x1FFF, (h0 >> 26) & 0x1F, h0 >> 31
            w, clase, a, b, nv = h1 & 0xF, (h1 >> 4) & 3, (h1 >> 6) & 0x3FF, (h1 >> 16) & 0x3FF, h1 >> 26
            paso = 2
            if nv == 0:
                nv, paso = R[r + 2], 3
            vs = [(x, y)]
            for _ in range(nv - 1):
                d = bits(self.V, o, 2 * w)
                o += 2 * w
                x += con_signo(d & ((1 << w) - 1), w)
                y += con_signo(d >> w, w)
                vs.append((x, y))
            out.append((r, k, clase, area, ext, vs, a, b))
            r += paso
        return out

    def portales(self, k):
        """[(x, y, texto)] de los portales de la calle k."""
        p0, p1 = self.c(k)[1], self.c(k + 1)[1]
        out, num = [], 0
        for j in range(p0, p1):
            w = self.P[j] & 0xFFFFFFFF
            pb = self.pb
            esc = (1 << (29 - 2 * pb)) - 1
            salto, sc = (w >> 2 * pb) & esc, w >> 29
            if salto == esc and sc == 7:
                e = self.E[j]
                num, sc = e & 0xFFF, e >> 12
            else:
                num += salto
            suf = self.nombres[self.nc + sc - 1] if sc else ""
            m = (1 << pb) - 1
            out.append((w & m, (w >> pb) & m, suf if num == 0 else f"{num}{suf}"))
        return out


class Ref:
    def __init__(self, region, variante="normal"):
        suf = "" if variante == "normal" else "-" + variante
        self.suf = suf
        self.m = json.loads((OUT / f"meta-{region}{suf}.json").read_text("utf-8"))
        self.tdir = ROOT / f"resources-gen{suf}" / region / "t"
        self.zdir = ROOT / f"resources-gen{suf}" / region / "z"
        self._t = {}
        self._z = {}
        self._g = None

    # --- lo que hace el reloj

    def xy(self, lat, lon):
        m = self.m
        return (lon - m["lon_min"]) * m["kx"], (lat - m["lat_min"]) * m["ky"]

    def latlon(self, x, y):
        m = self.m
        return m["lat_min"] + y / m["ky"], m["lon_min"] + x / m["kx"]

    def celda(self, x, y):
        m = self.m
        if x < 0 or y < 0:
            return -1
        c, f = int(x // m["tesela"]), int(y // m["tesela"])
        if c >= m["cols"] or f >= m["filas"]:
            return -1
        if not m.get("cajas"):
            return f * m["cols"] + c
        # Teselas adaptativas (variante c): la caja que lo contiene; si ninguna, la entrada null del final.
        return next((k for k, (x0, y0, x1, y1) in enumerate(m["cajas"]) if x0 <= x < x1 and y0 <= y < y1),
                    len(m["cajas"]))

    def caja(self, i):
        m = self.m
        if m.get("cajas"):
            return m["cajas"][i]
        T, cols = m["tesela"], m["cols"]
        return ((i % cols) * T, (i // cols) * T, (i % cols + 1) * T, (i // cols + 1) * T)

    def tesela(self, i):
        if i not in self._t:
            nom = self.m["idx"][i]
            self._t[i] = None if nom is None else Tes(json.loads((self.tdir / f"{nom}.json").read_text("utf-8")))
        return self._t[i]

    def buscar(self, x, y, i=None):
        """Búsqueda en UNA tesela (la de la celda, o la i dada si el reloj aún conserva la anterior)."""
        m = self.m
        if i is None:
            i = self.celda(x, y)
            if i < 0:
                return dict(estado="FUERA")
        t = self.tesela(i)
        if t is None:
            return dict(estado="LEJOS", tesela=i)
        assert t.fmt == m["formato"]
        N = t.nombres[:t.nc]
        B, MAXD = m["buf"], m["maxd"]
        caja = self.caja(i)
        u = t.u                       # todo en unidades de la tesela; las distancias, de vuelta en metros
        px, py = (x - (caja[0] - B)) / u, (y - (caja[1] - B)) / u
        best = [math.inf] * len(N)
        brun = [-1] * len(N)          # la tirada más cercana de cada calle (la primera, si empatan)
        tramos = {}                   # offset en R → (A, B)
        vistas = []                   # (calle, d, tramo) de cada tirada medida
        pxi, pyi, M, U = int(px), int(py), -(-MAXD // u) + 1, m["cb_u"]
        maxd_u = MAXD / u
        for r, calle, clase, area, ext, vs, a, b in t.tiradas():
            tramos[r] = (a, b)
            # Como el reloj: la caja gruesa de la calle descarta todas sus tiradas de un golpe.
            cb = t.CB[calle] & 0xFFFFFFFF
            if (pxi + M < (cb & 0xFF) * U or pxi - M > ((cb >> 16) & 0xFF) * U
                    or pyi + M < ((cb >> 8) & 0xFF) * U or pyi - M > (cb >> 24) * U):
                continue
            # El mismo descarte que el reloj: todos los vértices están a ≤ ext·EXT_U del primero.
            if ext != m["ext_sin"]:
                e = ext * m["ext_u"]
                dx = max(0.0, abs(px - vs[0][0]) - e)
                dy = max(0.0, abs(py - vs[0][1]) - e)
                if dx * dx + dy * dy > maxd_u * maxd_u:
                    continue
            n = len(vs)
            if n == 1:
                d2 = (px - vs[0][0]) ** 2 + (py - vs[0][1]) ** 2
            else:
                d2 = min(dseg2(px, py, *vs[j], *vs[j + 1]) for j in range(n - 1))
            d = (0.0 if area and dentro(px, py, vs) else math.sqrt(d2) * u) + m["pen"][clase]
            if d < best[calle]:
                best[calle], brun[calle] = d, r
            vistas.append((calle, d, (a, b)))
        orden = sorted(range(len(N)), key=lambda s: best[s])
        if not orden or best[orden[0]] > MAXD:
            return dict(estado="LEJOS", tesela=i, u=u, s1=N[orden[0]] if orden else None,
                        d1=best[orden[0]] if orden else math.inf)
        s1 = orden[0]
        s2 = orden[1] if len(orden) > 1 and best[orden[1]] <= MAXD else None

        def portal(s):
            mejor = None
            for qx, qy, texto in t.portales(s):
                d = math.hypot(px - qx, py - qy) * u
                if d <= m["portal_r"] and (mejor is None or d < mejor[1]):
                    mejor = (texto, d)
            return mejor

        def tramo(s):
            a, b = tramos[brun[s]]
            return (N[a - 1] if a else None, N[b - 1] if b else None)

        t_s1 = tramos[brun[s1]]
        t1_margen = min([d - best[s1] for c, d, tr in vistas if c == s1 and tr != t_s1] + [math.inf])
        return dict(estado="OK", tesela=i, u=u, s1=N[s1], d1=best[s1], p1=portal(s1), t1=tramo(s1), t1_margen=t1_margen,
                    s2=N[s2] if s2 is not None else None, d2=best[s2] if s2 is not None else None,
                    p2=portal(s2) if s2 is not None else None)

    def zona(self, x, y, margen=False, vista=False):
        """(polígono, lugar, barrio) en bruto: raster de la zona y lugar más cercano. Con vista=True, como
        lo enseña el reloj (Zonas.consultar): donde el polígono es el barrio oficial (Madrid, meta
        zbarrio), (None, lugar, polígono). None si el punto cae fuera de la rejilla de zonas. Con
        margen=True añade, de cuarto, a cuántos metros está el empate más cercano (borde de celda,
        radio, otro lugar o la regla del barrio)."""
        r = self._zona(x, y, margen)
        if vista and r is not None and self.m.get("zbarrio"):
            return (None, r[1], r[0]) + r[3:]
        return r

    def _zona(self, x, y, margen):
        m = self.m
        if x < 0 or y < 0:
            return None
        zc, zf = int(x // m["zona"]), int(y // m["zona"])
        if zc >= m["zcols"] or zf >= m["zfilas"]:
            return None
        nom = m["zidx"][zf * m["zcols"] + zc]
        if nom is None:
            return (None, None, None)
        if nom not in self._z:
            self._z[nom] = json.loads((self.zdir / f"{nom}.json").read_text("utf-8"))
        fmt, S, O, F, RL, L, LN = self._z[nom][:7]   # H y FZ (franjas) solo aceleran el reloj
        zu = self._z[nom][9] if len(self._z[nom]) > 9 else 1   # unidad de los lugares (variante b)
        assert fmt == m["formato"]

        def par16(A, k):
            return (A[k >> 1] >> (16 * (k & 1))) & 0xFFFF

        n = S.count("\n") - 1
        N = [S[par16(O, k):par16(O, k + 1) - 1] for k in range(n)]
        LN = [par16(LN, j) for j in range(len(L))]
        ox, oy = zc * m["zona"], zf * m["zona"]
        c = min(m["rn"] - 1, int((x - ox) // m["rcel"]))
        r = min(m["rn"] - 1, int((y - oy) // m["rcel"]))
        v, col = 0, 0
        for k in range(par16(F, r), par16(F, r + 1)):
            t = par16(RL, k)
            col += t >> 8
            if c < col:
                v = t & 0xFF
                break
        lx0, ly0 = ox - m["zmargen"], oy - m["zmargen"]
        mejor = {}   # bit → (d, nombre)
        d2b = math.inf   # el segundo barrio más cercano
        for j, p in enumerate(L):
            d = math.hypot(x - (lx0 + (p & 0x3FFF) * zu), y - (ly0 + ((p >> 14) & 0x3FFF) * zu))
            for bit, radio in ((1, m["lugar_r"]), (2, math.inf), (4, m["lugar_r"])):
                if (p >> 28) & bit and d <= radio:
                    if d < mejor.get(bit, (math.inf,))[0]:
                        if bit == 2:
                            d2b = mejor.get(2, (math.inf,))[0]
                        mejor[bit] = (d, N[LN[j]])
                    elif bit == 2 and d < d2b:
                        d2b = d
        lugar = mejor.get(1) or mejor.get(4)
        b = mejor.get(2)
        barrio = b[1] if b and b[0] <= m["barrio_r"] and b[0] <= m["barrio_frac"] * d2b else None
        res = (N[v - 1] if v else None, lugar[1] if lugar else None, barrio)
        if not margen:
            return res
        fx, fy = (x - ox) / m["rcel"], (y - oy) / m["rcel"]
        ms = [abs(fx - round(fx)) * m["rcel"], abs(fy - round(fy)) * m["rcel"]]
        ds = {1: [], 2: [], 4: []}
        for p in L:
            d = math.hypot(x - (lx0 + (p & 0x3FFF) * zu), y - (ly0 + ((p >> 14) & 0x3FFF) * zu))
            for bit in ds:
                if (p >> 28) & bit:
                    ds[bit].append(d)
        for bit, radio in ((1, m["lugar_r"]), (2, m["barrio_r"]), (4, m["lugar_r"])):
            c = sorted(ds[bit])
            if c:
                ms.append(abs(c[0] - radio))
                if len(c) > 1:
                    ms.append(c[1] - c[0])
                    if bit == 2:
                        ms.append(abs(m["barrio_frac"] * c[1] - c[0]))
        return res + (min(ms),)

    def _zgeom(self):
        """Parroquias con su caja y una rejilla de 100 m de las aristas de sus límites."""
        if not hasattr(self, "_zg"):
            g, _, _ = self._geom()
            aristas = defaultdict(list)
            for p in g["parroquias"]:
                pts = [q for a in p["r"] for q in a]
                p["bb"] = (min(q[0] for q in pts), min(q[1] for q in pts), max(q[0] for q in pts), max(q[1] for q in pts))
                for a in p["r"]:
                    for j in range(len(a) - 1):
                        (ax, ay), (bx, by) = a[j], a[j + 1]
                        for gx in range(int(min(ax, bx) // 100), int(max(ax, bx) // 100) + 1):
                            for gy in range(int(min(ay, by) // 100), int(max(ay, by) // 100) + 1):
                                aristas[(gx, gy)].append((ax, ay, bx, by))
            self._zg = (g["parroquias"], aristas, g["lugares"])
        return self._zg

    def zona_global(self, x, y):
        """La verdad: punto en polígono sobre los límites reales y lugar más cercano entre todos.
        Devuelve también la distancia al límite de parroquia más cercano y los márgenes de empate."""
        parroquias, aristas, lugares = self._zgeom()
        m = self.m
        par = None
        for p in parroquias:
            x0, y0, x1, y1 = p["bb"]
            if x0 <= x <= x1 and y0 <= y <= y1 and sum(dentro(x, y, a) for a in p["r"]) % 2 == 1:
                par = p["n"]
                break
        dlim = math.inf
        for gx in range(int(x // 100) - 1, int(x // 100) + 2):
            for gy in range(int(y // 100) - 1, int(y // 100) + 2):
                for ax, ay, bx, by in aristas.get((gx, gy), ()):
                    dlim = min(dlim, math.sqrt(dseg2(x, y, ax, ay, bx, by)))
        res = {}
        for bit, radio in ((1, m["lugar_r"]), (2, m["barrio_r"]), (4, m["lugar_r"])):
            c = sorted((math.hypot(x - lx, y - ly), nombre) for lx, ly, tipo, nombre in lugares if tipo & bit)
            dentro_r = [t for t in c if t[0] <= radio]
            margen = min([abs(c[0][0] - radio)] + ([c[1][0] - c[0][0]] if len(c) > 1 else [])) if c else math.inf
            nombre = dentro_r[0][1] if dentro_r else None
            if bit == 2 and c:
                d2 = c[1][0] if len(c) > 1 else math.inf
                margen = min(margen, abs(m["barrio_frac"] * d2 - c[0][0]))
                if c[0][0] > m["barrio_frac"] * d2:
                    nombre = None
            res[bit] = (nombre, margen)
        lugar = res[1][0] or res[4][0]
        margen = res[1][1] if res[1][0] else min(res[1][1], res[4][1])
        return dict(parroquia=par, dlim=dlim, lugar=lugar, barrio=res[2][0], margen_lugar=margen,
                    margen_barrio=res[2][1])

    # --- fuerza bruta sobre las calles enteras

    def _geom(self):
        if self._g is None:
            g = json.loads((OUT / f"geom-{self.m['region']}{self.suf}.json").read_text("utf-8"))
            rej = defaultdict(list)
            for c in g["calles"]:
                xs, ys = [p[0] for p in c["p"]], [p[1] for p in c["p"]]
                c["bb"] = (min(xs), min(ys), max(xs), max(ys))
                for gx in range(int(c["bb"][0] // 100), int(c["bb"][2] // 100) + 1):
                    for gy in range(int(c["bb"][1] // 100), int(c["bb"][3] // 100) + 1):
                        rej[(gx, gy)].append(c)
            prej = defaultdict(list)
            for p in g["portales"]:
                prej[(int(p[0] // 100), int(p[1] // 100))].append(p)
            self._g = (g, rej, prej)
        return self._g

    def global_(self, x, y, radio=None):
        g, rej, prej = self._geom()
        r = radio or self.m["maxd"] + 10
        vistos, best, tramos = set(), {}, {}
        for gx in range(int((x - r) // 100), int((x + r) // 100) + 1):
            for gy in range(int((y - r) // 100), int((y + r) // 100) + 1):
                for c in rej.get((gx, gy), ()):
                    if id(c) in vistos:
                        continue
                    vistos.add(id(c))
                    x0, y0, x1, y1 = c["bb"]
                    if x < x0 - r or x > x1 + r or y < y0 - r or y > y1 + r:
                        continue
                    p = c["p"]
                    d2 = (x - p[0][0]) ** 2 + (y - p[0][1]) ** 2 if len(p) == 1 else \
                        min(dseg2(x, y, *p[j], *p[j + 1]) for j in range(len(p) - 1))
                    d = 0.0 if c["a"] and dentro(x, y, p) else math.sqrt(d2)
                    e = d + self.m["pen"][c["c"]]
                    tramos.setdefault(c["n"], []).append((e, tuple(c["t"])))
                    if e < best.get(c["n"], math.inf):
                        best[c["n"]] = e
        orden = sorted(best, key=best.get)

        def portal(nombre):
            mejor = []
            for gx in range(int((x - 50) // 100), int((x + 50) // 100) + 1):
                for gy in range(int((y - 50) // 100), int((y + 50) // 100) + 1):
                    for p in prej.get((gx, gy), ()):
                        if p[2] == nombre:
                            mejor.append((math.hypot(x - p[0], y - p[1]), p))
            mejor.sort(key=lambda t: t[0])
            return mejor[:2]

        def tramo(nombre, tol=TOL):
            """El tramo del trozo más cercano, o None si otro trozo con otro tramo está a menos de tol."""
            ts = sorted(tramos.get(nombre, ()), key=lambda t: t[0])
            if not ts:
                return None
            otros = [e for e, t in ts if t != ts[0][1]]
            return ts[0][1] if not otros or otros[0] - ts[0][0] > tol else None

        return best, orden, portal, tramo


def describir(r, z=None):
    if r["estado"] == "FUERA":
        return "FUERA DE ZONA"
    par, lugar, barrio = z or (None, None, None)
    if r["estado"] == "LEJOS":
        return (f"{lugar or 'SIN CALLE'}" + (f" (parroquia de {par})" if par else f" ({barrio})" if barrio else "")
                + f" — sin calle a 50 m (la más cercana: {r.get('s1')} a {r.get('d1', math.inf):.0f} m)")
    s = (f"[{barrio}] " if barrio else "") + f"{r['s1']}  ({r['d1']:.1f} m)"
    if r["p1"]:
        s += f"  nº {r['p1'][0]} a {r['p1'][1]:.0f} m"
    a, b = r["t1"]
    if a and b and a != b:
        s += f"  entre {a} y {b}"
    elif a or b:
        s += f"  cerca de {a or b}"
    if r["s2"]:
        s += f"\n   2ª: {r['s2']}  ({r['d2']:.1f} m)" + (f"  nº {r['p2'][0]}" if r["p2"] else "")
    return s


# ---------------------------------------------------------------- autotests


def fuerza_bruta(ref, n, semilla=1):
    """La garantía de las teselas: buscar en una tesela da lo mismo que buscar en todo."""
    m = ref.m
    rnd = random.Random(semilla)
    g, _, _ = ref._geom()
    ancho, alto = m["cols"] * m["tesela"], m["filas"] * m["tesela"]
    largas = [c for c in g["calles"] if len(c["p"]) > 1]
    T, SL = m["tesela"], m["buf"] - m["maxd"]
    fallos, comparados, portales_ok, portales_cmp = [], 0, 0, 0
    tramos_cmp = 0
    for k in range(n):
        if k % 2 == 0:  # mitad al azar en la región, mitad cerca de una calle
            x, y = rnd.uniform(0, ancho), rnd.uniform(0, alto)
        else:
            c = rnd.choice(largas)
            j = rnd.randrange(len(c["p"]) - 1)
            t = rnd.random()
            (ax, ay), (bx, by) = c["p"][j], c["p"][j + 1]
            x = ax + t * (bx - ax) + rnd.uniform(-60, 60)
            y = ay + t * (by - ay) + rnd.uniform(-60, 60)
        i = ref.celda(x, y)
        if i < 0:
            continue
        best, orden, portal, tramo_g = ref.global_(x, y)
        # La tesela propia y, si el punto cae en la holgura de una vecina, también la vecina:
        # el reloj conserva la tesela anterior mientras no se salga de esa holgura.
        cands = [i]
        if m.get("cajas"):
            cands += [k for k, (x0, y0, x1, y1) in enumerate(m["cajas"])
                      if k != i and x0 - SL <= x <= x1 + SL and y0 - SL <= y <= y1 + SL]
        else:
            c0, f0 = i % m["cols"], i // m["cols"]
            for dc, df in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                c1, f1 = c0 + dc, f0 + df
                if 0 <= c1 < m["cols"] and 0 <= f1 < m["filas"]:
                    if c1 * T - SL <= x <= (c1 + 1) * T + SL and f1 * T - SL <= y <= (f1 + 1) * T + SL:
                        cands.append(f1 * m["cols"] + c1)
        for ti in cands:
            r = ref.buscar(x, y, ti)
            # Con unidad de U m (variante b), la cuantización mueve las distancias hasta ~0,71·U m.
            u = r.get("u", 1)
            tol, tol_portal = TOL * u, TOL_PORTAL * u
            g1 = best[orden[0]] if orden else math.inf
            if g1 <= m["maxd"] - tol:
                comparados += 1
                if r["estado"] != "OK":
                    fallos.append((x, y, ti, f"tesela dice {r['estado']} y la calle {orden[0]} está a {g1:.1f} m"))
                    continue
                if r["s1"] != orden[0] and abs(best.get(r["s1"], math.inf) - g1) > tol:
                    fallos.append((x, y, ti, f"tesela {r['s1']} ({r['d1']:.1f}) ≠ global {orden[0]} ({g1:.1f})"))
                elif abs(r["d1"] - g1) > tol:
                    fallos.append((x, y, ti, f"distancia {r['d1']:.2f} ≠ {g1:.2f}"))
                elif r["s1"] == orden[0]:
                    tg = tramo_g(orden[0], tol)
                    if tg is not None:
                        tramos_cmp += 1
                        if tuple(r["t1"]) != tg:
                            fallos.append((x, y, ti, f"tramo {r['t1']} ≠ global {tg}"))
                    ps = portal(orden[0])
                    if ps and ps[0][0] <= m["portal_r"] - tol and (len(ps) == 1 or ps[1][0] - ps[0][0] > tol_portal):
                        portales_cmp += 1
                        esperado = ps[0][1][4] if ps[0][1][3] == 0 else f"{ps[0][1][3]}{ps[0][1][4]}"
                        if r["p1"] and r["p1"][0] == esperado:
                            portales_ok += 1
                        else:
                            fallos.append((x, y, ti, f"portal {r['p1']} ≠ {esperado}"))
            elif g1 > m["maxd"] + tol and r["estado"] == "OK":
                fallos.append((x, y, ti, f"tesela da {r['s1']} a {r['d1']:.1f} m y lo más cercano está a {g1:.1f}"))
    fuerza_bruta.tramos = tramos_cmp
    return comparados, fallos, portales_cmp, portales_ok


def zonas_bruta(ref, n, semilla=2):
    """El reloj (raster + lugares de la zona) frente a la verdad (límites reales, todos los lugares).
    La parroquia solo puede fallar a menos de 50 m de un límite; lugar y barrio, solo en empates."""
    m = ref.m
    rnd = random.Random(semilla)
    ancho, alto = m["cols"] * m["tesela"], m["filas"] * m["tesela"]
    fallos, cuenta = [], dict(parroquia=0, lugar=0, barrio=0, cerca_limite=0)
    for _ in range(n):
        x, y = rnd.uniform(0, min(ancho, m["zcols"] * m["zona"])), rnd.uniform(0, min(alto, m["zfilas"] * m["zona"]))
        z = ref.zona(x, y)
        v = ref.zona_global(x, y)
        cuenta["parroquia"] += v["parroquia"] is not None
        if z[0] != v["parroquia"]:
            if v["dlim"] < 50:
                cuenta["cerca_limite"] += 1
            else:
                fallos.append((x, y, f"parroquia {z[0]} ≠ {v['parroquia']} a {v['dlim']:.0f} m del límite"))
        if z[1] != v["lugar"] and v["margen_lugar"] > 1.5:
            fallos.append((x, y, f"lugar {z[1]} ≠ {v['lugar']}"))
        cuenta["lugar"] += v["lugar"] is not None
        if z[2] != v["barrio"] and v["margen_barrio"] > 1.5:
            fallos.append((x, y, f"barrio {z[2]} ≠ {v['barrio']}"))
        cuenta["barrio"] += v["barrio"] is not None
    return cuenta, fallos


def derivar_control(ref, region):
    """Puntos de control con nombre, sacados de los datos (la verdad de campo es la prueba en la muñeca).
    Si la región trae "control" en tools/regiones.json, se derivan de esa lista; si no, los de Santiago."""
    if ref.m.get("control"):
        return derivar_control_cfg(ref, region, ref.m["control"])
    g, _, _ = ref._geom()
    m = ref.m
    puntos = []

    def calle(nombre):
        cs = [c for c in g["calles"] if c["n"] == nombre and len(c["p"]) > 1 and not c["a"]]
        if not cs:
            sys.exit(f"no existe la calle {nombre!r} en los datos")
        return max(cs, key=lambda c: sum(math.dist(c["p"][j], c["p"][j + 1]) for j in range(len(c["p"]) - 1)))

    def mitad(c):
        L = [math.dist(c["p"][j], c["p"][j + 1]) for j in range(len(c["p"]) - 1)]
        objetivo, acc = sum(L) / 2, 0.0
        for j, l in enumerate(L):
            if acc + l >= objetivo:
                t = (objetivo - acc) / l if l else 0
                (ax, ay), (bx, by) = c["p"][j], c["p"][j + 1]
                return ax + t * (bx - ax), ay + t * (by - ay)
            acc += l

    def anadir(id_, x, y, nota):
        lat, lon = ref.latlon(x, y)
        puntos.append(dict(id=id_, lat=round(lat, 7), lon=round(lon, 7), nota=nota))

    # Un portal: 5 m desde la fachada hacia la calle.
    p = next(p for p in g["portales"] if p[2] == "Rúa do Vilar" and p[3] == 44 and p[4] == "")
    c = calle("Rúa do Vilar")
    _, q = min(((dseg2(p[0], p[1], *c["p"][j], *c["p"][j + 1]), j) for j in range(len(c["p"]) - 1)))
    (ax, ay), (bx, by) = c["p"][q], c["p"][q + 1]
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    qx, qy = ax + t * dx, ay + t * dy
    dd = math.hypot(qx - p[0], qy - p[1])
    anadir("portal", p[0] + (qx - p[0]) * min(1, 5 / dd), p[1] + (qy - p[1]) * min(1, 5 / dd),
           "Rúa do Vilar 44, 5 m desde el portal hacia la calle")
    # Centro de la Praza do Obradoiro (área).
    a = max((c for c in g["calles"] if c["n"] == "Praza do Obradoiro" and c["a"]), key=lambda c: len(c["p"]))
    xs, ys = [q[0] for q in a["p"][:-1]], [q[1] for q in a["p"][:-1]]
    anadir("obradoiro", sum(xs) / len(xs), sum(ys) / len(ys), "centro de la plaza")
    for id_, nombre in (("franco", "Rúa do Franco"), ("vilar", "Rúa do Vilar"), ("galicia", "Praza de Galicia"),
                        ("horreo", "Rúa do Hórreo"), ("lugo", "Avenida de Lugo"),
                        ("aeropuerto", "Acceso Terminal Aeroporto")):
        x, y = mitad(calle(nombre))
        anadir(id_, x, y, f"mitad de {nombre}")
    # Conxo y Fontiñas: la calle con nombre más cercana al centro de cada barrio.
    for id_, lat, lon in (("conxo", 42.8650, -8.5560), ("fontinas", 42.8850, -8.5235)):
        x, y = ref.xy(lat, lon)
        best, orden, _, _ = ref.global_(x, y, radio=400)
        x, y = mitad(calle(orden[0]))
        anadir(id_, x, y, f"mitad de {orden[0]}")
    # Un cruce: vértice compartido por Rúa do Franco y otra calle.
    franco = {tuple(q) for c in g["calles"] if c["n"] == "Rúa do Franco" for q in c["p"]}
    otro = next((tuple(q), c["n"]) for c in g["calles"] if c["n"] != "Rúa do Franco" and not c["a"]
                for q in c["p"] if tuple(q) in franco)
    anadir("cruce", otro[0][0], otro[0][1], f"cruce de Rúa do Franco con {otro[1]}")
    # Lejos: el primer punto de una rejilla sin nada a 200 m.
    for f in range(m["filas"]):
        x, y = 0.5 * m["tesela"], (f + 0.5) * m["tesela"]
        best, orden, _, _ = ref.global_(x, y, radio=200)
        if not orden or best[orden[0]] > 200:
            anadir("lejos", x, y, "sin calles a 200 m")
            break
    puntos.append(dict(id="fuera", lat=43.0, lon=-8.5, nota="al norte de la región"))
    # Lo esperado lo da la fuerza bruta global, no la búsqueda por teselas.
    for p in puntos:
        x, y = ref.xy(p["lat"], p["lon"])
        if ref.celda(x, y) < 0:
            p["espera"] = "FUERA"
            continue
        best, orden, portal, _ = ref.global_(x, y)
        if not orden or best[orden[0]] > m["maxd"]:
            p["espera"] = "LEJOS"
            continue
        p["espera"] = orden[0]
        if len(orden) > 1 and best[orden[1]] - best[orden[0]] < 8:
            p["tambien"] = orden[1]
        ps = portal(orden[0])
        if ps and ps[0][0] <= m["portal_r"]:
            p["num"] = ps[0][1][4] if ps[0][1][3] == 0 else f"{ps[0][1][3]}{ps[0][1][4]}"
    f = TOOLS / f"puntos_control-{region}.json"
    f.write_text(json.dumps(puntos, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"escrito {f.relative_to(ROOT)} ({len(puntos)} puntos)")


def _larga(g, nombre, cerca=None, radio=2000.0):
    """La calle más larga con ese nombre; con cerca (x, y), solo entre las que pasan a radio m: en una región grande
    (Galicia) hay homónimas en otras ciudades (la «Rúa do Franco» más larga es la de Lugo, no la de Santiago)."""
    cs = [c for c in g["calles"] if c["n"] == nombre and len(c["p"]) > 1 and not c["a"]
          and (cerca is None or min(math.dist(q, cerca) for q in c["p"]) <= radio)]
    if not cs:
        sys.exit(f"no existe la calle {nombre!r} en los datos")
    return max(cs, key=lambda c: sum(math.dist(c["p"][j], c["p"][j + 1]) for j in range(len(c["p"]) - 1)))


def _mitad(c):
    L = [math.dist(c["p"][j], c["p"][j + 1]) for j in range(len(c["p"]) - 1)]
    objetivo, acc = sum(L) / 2, 0.0
    for j, l in enumerate(L):
        if acc + l >= objetivo:
            t = (objetivo - acc) / l if l else 0
            (ax, ay), (bx, by) = c["p"][j], c["p"][j + 1]
            return ax + t * (bx - ax), ay + t * (by - ay)
        acc += l


def derivar_control_cfg(ref, region, specs):
    """Tipos: "portal" (5 m desde el portal calle+num hacia la calle), "area" (centro de una plaza),
    "mitad" (mitad de la calle más larga con ese nombre), "cerca" (mitad de la calle más cercana a lat/lon),
    "cruce" (un vértice que la calle comparte con otra), "lejos" (sin calles a 200 m) y "fuera" (lat/lon)."""
    g, _, _ = ref._geom()
    m = ref.m
    puntos = []

    def anadir(id_, x, y, nota):
        lat, lon = ref.latlon(x, y)
        puntos.append(dict(id=id_, lat=round(lat, 7), lon=round(lon, 7), nota=nota))

    for sp in specs:
        t, id_ = sp["tipo"], sp["id"]
        if t == "portal":
            p = next((p for p in g["portales"] if p[2] == sp["calle"] and p[3] == sp["num"] and p[4] == ""), None)
            if p is None:
                sys.exit(f"no hay portal {sp['calle']} {sp['num']} en los datos")
            # El trozo de la calle más cercano al portal (no el más largo: puede estar en otra punta).
            cs = [c for c in g["calles"] if c["n"] == sp["calle"] and len(c["p"]) > 1 and not c["a"]]
            _, q, c = min(((dseg2(p[0], p[1], *c["p"][j], *c["p"][j + 1]), j, c) for c in cs
                           for j in range(len(c["p"]) - 1)), key=lambda t: t[0])
            (ax, ay), (bx, by) = c["p"][q], c["p"][q + 1]
            dx, dy = bx - ax, by - ay
            tt = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
            qx, qy = ax + tt * dx, ay + tt * dy
            dd = math.hypot(qx - p[0], qy - p[1]) or 1
            anadir(id_, p[0] + (qx - p[0]) * min(1, 5 / dd), p[1] + (qy - p[1]) * min(1, 5 / dd),
                   f"{sp['calle']} {sp['num']}, 5 m desde el portal hacia la calle")
        elif t == "area":
            a = max((c for c in g["calles"] if c["n"] == sp["calle"] and c["a"]), key=lambda c: len(c["p"]))
            xs, ys = [q[0] for q in a["p"][:-1]], [q[1] for q in a["p"][:-1]]
            anadir(id_, sum(xs) / len(xs), sum(ys) / len(ys), f"centro de {sp['calle']}")
        elif t == "mitad":
            x, y = _mitad(_larga(g, sp["calle"], ref.xy(sp["lat"], sp["lon"]) if "lat" in sp else None))
            anadir(id_, x, y, f"mitad de {sp['calle']}")
        elif t == "cerca":
            x, y = ref.xy(sp["lat"], sp["lon"])
            best, orden, _, _ = ref.global_(x, y, radio=400)
            # La más cercana que sea calle (no solo área) aquí: junto a una plaza que en OSM es solo área (Barcelona,
            # «Plaça de Pau Casals»), no hay calle lineal con ese nombre que partir por la mitad, aunque la haya en
            # otro municipio.
            lineales = {c["n"] for c in g["calles"] if not c["a"] and len(c["p"]) > 1
                        and min(math.dist(q, (x, y)) for q in c["p"]) <= 2000.0}
            n = next(n for n in orden if n in lineales)
            x, y = _mitad(_larga(g, n, (x, y)))
            anadir(id_, x, y, f"mitad de {n}")
        elif t == "cruce":
            propia = {tuple(q) for c in g["calles"] if c["n"] == sp["calle"] for q in c["p"]}
            otro = next((tuple(q), c["n"]) for c in g["calles"] if c["n"] != sp["calle"] and not c["a"]
                        for q in c["p"] if tuple(q) in propia)
            anadir(id_, otro[0][0], otro[0][1], f"cruce de {sp['calle']} con {otro[1]}")
        elif t == "lejos":
            for f in range(m["filas"]):
                for col in range(m["cols"]):
                    x, y = (col + 0.5) * m["tesela"], (f + 0.5) * m["tesela"]
                    best, orden, _, _ = ref.global_(x, y, radio=200)
                    if (not orden or best[orden[0]] > 200) and ref.zona(x, y) and ref.zona(x, y)[0]:
                        break
                else:
                    continue
                anadir(id_, x, y, "sin calles a 200 m")
                break
        elif t == "fuera":
            puntos.append(dict(id=id_, lat=sp["lat"], lon=sp["lon"], nota="fuera de la región"))
    for p in puntos:
        x, y = ref.xy(p["lat"], p["lon"])
        if ref.celda(x, y) < 0:
            p["espera"] = "FUERA"
            continue
        best, orden, portal, _ = ref.global_(x, y)
        if not orden or best[orden[0]] > m["maxd"]:
            p["espera"] = "LEJOS"
            continue
        p["espera"] = orden[0]
        if len(orden) > 1 and best[orden[1]] - best[orden[0]] < 8:
            p["tambien"] = orden[1]
        ps = portal(orden[0])
        if ps and ps[0][0] <= m["portal_r"]:
            p["num"] = ps[0][1][4] if ps[0][1][3] == 0 else f"{ps[0][1][3]}{ps[0][1][4]}"
    f = TOOLS / f"puntos_control-{region}.json"
    f.write_text(json.dumps(puntos, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"escrito {f.relative_to(ROOT)} ({len(puntos)} puntos)")


def control(ref, region):
    f = TOOLS / f"puntos_control-{region}.json"
    if not f.exists():
        derivar_control(ref, region)
    fallos = 0
    for p in json.loads(f.read_text("utf-8")):
        if ref.suf and p["espera"] != "FUERA" and ref.celda(*ref.xy(p["lat"], p["lon"])) < 0:
            print(f"  --  {p['id']:<12} fuera de la variante{ref.suf} (región recortada)")
            continue
        r = ref.buscar(*ref.xy(p["lat"], p["lon"]))
        if p["espera"] in ("FUERA", "LEJOS"):
            ok = r["estado"] == p["espera"]
        else:
            ok = r["estado"] == "OK" and (r["s1"] == p["espera"] or
                                          (p.get("tambien") and {r["s1"], r["s2"]} == {p["espera"], p["tambien"]}))
            if ok and p.get("num"):
                ok = bool(r["p1"]) and r["p1"][0] == p["num"] or r["s1"] != p["espera"]
        fallos += not ok
        x, y = ref.xy(p["lat"], p["lon"])
        print(f"  {'OK ' if ok else 'MAL'} {p['id']:<12} {describir(r, ref.zona(x, y, vista=True)).splitlines()[0]}"
              + ("" if ok else f"   ← esperaba {p['espera']} {p.get('num', '')}"))
    return fallos


# ---------------------------------------------------------------- vectores para Monkey C


def mc(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def gen_tests(ref, region, n=40, semilla=3):
    """Vectores [id, lat, lon, calle1 ("" lejos, "FUERA"), d1, nº, tramo A, tramo B, barrio, lugar, parroquia]
    ("" = ninguno), sin casos al filo de un umbral ni de un empate."""
    m = ref.m
    rnd = random.Random(semilla)
    g, _, _ = ref._geom()
    vec = []
    for p in json.loads((TOOLS / f"puntos_control-{region}.json").read_text("utf-8")):
        if ref.suf and p["espera"] != "FUERA" and ref.celda(*ref.xy(p["lat"], p["lon"])) < 0:
            continue
        vec.append((p["id"], p["lat"], p["lon"]))
    largas = [c for c in g["calles"] if len(c["p"]) > 1]
    while len(vec) < n + 12:
        c = rnd.choice(largas)
        j = rnd.randrange(len(c["p"]) - 1)
        t = rnd.random()
        (ax, ay), (bx, by) = c["p"][j], c["p"][j + 1]
        x, y = ax + t * (bx - ax) + rnd.uniform(-30, 30), ay + t * (by - ay) + rnd.uniform(-30, 30)
        if ref.celda(x, y) < 0:
            continue
        r = ref.buscar(x, y)
        if r["estado"] != "OK":
            continue
        if r["d2"] is not None and r["d2"] - r["d1"] < 0.5:
            continue
        if abs(r["d1"] - m["maxd"]) < 0.5 or (r["p1"] and abs(r["p1"][1] - m["portal_r"]) < 0.5):
            continue
        z = ref.zona(x, y, margen=True)
        if r["t1_margen"] < 0.5 or z is None or len(z) < 4 or z[3] < 0.5:   # (None, None, None): zona sin recurso
            continue
        lat, lon = ref.latlon(x, y)
        vec.append((f"azar{len(vec)}", round(lat, 7), round(lon, 7)))
    # Puntos sin calle a 50 m (monte, agras): lugar y parroquia.
    ancho, alto = m["cols"] * m["tesela"], m["filas"] * m["tesela"]
    rurales = 0
    while rurales < 10:
        x, y = rnd.uniform(0, ancho), rnd.uniform(0, alto)
        if ref.celda(x, y) < 0 or ref.buscar(x, y)["estado"] != "LEJOS":
            continue
        z = ref.zona(x, y, margen=True)
        if z is None or len(z) < 4 or z[3] < 0.5 or z[0] is None:
            continue
        lat, lon = ref.latlon(x, y)
        vec.append((f"rural{rurales}", round(lat, 7), round(lon, 7)))
        rurales += 1
    filas = []
    for id_, lat, lon in vec:
        x, y = ref.xy(lat, lon)
        r = ref.buscar(x, y)
        z = ref.zona(x, y, vista=True) or (None, None, None)
        par, lugar, barrio = (v or "" for v in z)
        if r["estado"] == "FUERA":
            filas.append((id_, lat, lon, "FUERA", -1.0, "", "", "", "", "", ""))
        elif r["estado"] == "LEJOS":
            filas.append((id_, lat, lon, "", -1.0, "", "", "", barrio, lugar, par))
        else:
            ta, tb = (v or "" for v in r["t1"])
            filas.append((id_, lat, lon, r["s1"], round(r["d1"], 3), r["p1"][0] if r["p1"] else "",
                          ta, tb, barrio, lugar, par))
    cfg = json.loads((TOOLS / "regiones.json").read_text("utf-8"))[region]
    mod = "".join(x.capitalize() for x in region.replace("-", " ").replace("_", " ").split())
    pref = cfg["prefijo"].upper()
    L = ["import Toybox.Lang;", "import Toybox.Test;", "",
         f"// GENERADO por tools/ref.py --gen-tests ({region}, datos OSM {m['datos']}). No editar a mano.",
         "// [id, lat, lon, calle esperada (\"\" = sin calle, \"FUERA\"), d1 (m), nº, tramo A, tramo B,",
         "//  barrio, lugar, parroquia] (\"\" = ninguno)"]
    for k in range(0, len(filas), 5):
        L += ["", "(:test)", f"function vectores{pref}{k // 5:02d}(logger as Test.Logger) as Boolean {{",
              f"    return Vectores.comprobar(logger, {cfg['id']}, ["]
        L += ["        [" + ", ".join([mc(f[0]), f"{f[1]!r}d", f"{f[2]!r}d", mc(f[3]), repr(f[4])]
                              + [mc(v) for v in f[5:]]) + "]," for f in filas[k:k + 5]]
        L += ["    ] as Array<Array>);", "}"]
    # Paseo por una calle (la "ruta" de la región; en Santiago, la Rúa do Franco), un fix cada 2 m con
    # ruido lateral de ±3 m: la histéresis no debe hacer bailar el nombre (sustituye a reproducir un GPX).
    calle_ruta = cfg.get("ruta", "Rúa do Franco")
    c = max((c for c in g["calles"] if c["n"] == calle_ruta and len(c["p"]) > 1),
            key=lambda c: sum(math.dist(c["p"][j], c["p"][j + 1]) for j in range(len(c["p"]) - 1)))
    ruta = []
    for j in range(len(c["p"]) - 1):
        (ax, ay), (bx, by) = c["p"][j], c["p"][j + 1]
        L_ = math.dist((ax, ay), (bx, by))
        nx, ny = (-(by - ay) / L_, (bx - ax) / L_) if L_ else (0, 0)
        for k in range(int(L_ // 2)):
            t = k * 2 / L_
            ruido = rnd.uniform(-3, 3)
            ruta.append(ref.latlon(ax + t * (bx - ax) + nx * ruido, ay + t * (by - ay) + ny * ruido))
    L += ["", f"// Paseo por {calle_ruta} con ruido: el nombre no debe bailar.", "(:test)",
          f"function ruta{mod}(logger as Test.Logger) as Boolean {{",
          f"    return Vectores.ruta(logger, {mc(calle_ruta)}, ["]
    L += ["        " + ", ".join(f"{la!r}d, {lo!r}d" for la, lo in ruta[k:k + 4]) + ","
          for k in range(0, len(ruta), 4)]
    L += ["    ] as Array<Double>);", "}"]
    # Cadena completa del reloj en un punto, en una sola llamada y desde cero (tesela, calle, zona y lugar), como al
    # abrir la app: el watchdog cuenta la suma. Por separado cabía y el 7X Pro con Galicia se cerraba (ERA,
    # 2026-10-25). Los puntos de control, el centro de la tesela más pesada y el de la zona más pesada.
    cad = [(p["id"], p["lat"], p["lon"]) for p in json.loads((TOOLS / f"puntos_control-{region}.json").read_text("utf-8"))
           if p["espera"] != "FUERA" and ref.celda(*ref.xy(p["lat"], p["lon"])) >= 0]
    ti = int(m["t_mayor"][1:])
    if m.get("cajas"):
        x0, y0, x1, y1 = m["cajas"][ti]
    else:
        x0, y0 = (ti % m["cols"]) * m["tesela"], (ti // m["cols"]) * m["tesela"]
        x1, y1 = x0 + m["tesela"], y0 + m["tesela"]
    zi = int(m["z_mayor"][1:])
    zx, zy = (zi % m["zcols"] + 0.5) * m["zona"], (zi // m["zcols"] + 0.5) * m["zona"]
    for id_, (x, y) in (("tmayor", ((x0 + x1) / 2, (y0 + y1) / 2)), ("zmayor", (zx, zy))):
        if ref.celda(x, y) >= 0:
            cad.append((id_, *[round(v, 7) for v in ref.latlon(x, y)]))
    for id_, lat, lon in cad:
        L += ["", "(:test)", f"function cadena{mod}_{re.sub(r'[^A-Za-z0-9]', '_', id_)}(logger as Test.Logger) as Boolean {{",
              f"    return Vectores.cadena(logger, {cfg['id']}, {lat!r}d, {lon!r}d);", "}"]
    out = ROOT / f"test-gen{ref.suf}" / f"Vectores{mod}Test.mc"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(L) + "\n", "utf-8")
    print(f"escrito {out.relative_to(ROOT)} ({len(filas)} vectores, ruta de {len(ruta)} fixes)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--region", default="santiago")
    ap.add_argument("--punto", nargs=2, type=float, metavar=("LAT", "LON"))
    ap.add_argument("--derivar", action="store_true")
    ap.add_argument("--gen-tests", action="store_true")
    ap.add_argument("--n", type=int, default=10000, help="puntos de la fuerza bruta")
    ap.add_argument("--variante", choices=("normal", "6x", "c", "b"), default="normal")
    a = ap.parse_args()
    ref = Ref(a.region, a.variante)
    if a.punto:
        x, y = ref.xy(*a.punto)
        print(describir(ref.buscar(x, y), ref.zona(x, y, vista=True)))
        return
    if a.derivar:
        derivar_control(ref, a.region)
        return
    print(f"Fuerza bruta ({a.n} puntos, datos OSM {ref.m['datos']}):")
    comparados, fallos, pc, pok = fuerza_bruta(ref, a.n)
    print(f"  {comparados} comparaciones con calle a ≤ {ref.m['maxd']} m; {len(fallos)} discrepancias; "
          f"portales {pok}/{pc}; tramos comparados {fuerza_bruta.tramos}")
    for x, y, ti, msg in fallos[:15]:
        lat, lon = ref.latlon(x, y)
        print(f"   {lat:.6f},{lon:.6f} t{ti}: {msg}")
    nz = max(1, a.n // 5)
    print(f"Zonas ({nz} puntos al azar, datos OSM {ref.m['zonas']}):")
    cz, fz = zonas_bruta(ref, nz)
    print(f"  con parroquia {cz['parroquia']}, con lugar {cz['lugar']}, con barrio {cz['barrio']}; "
          f"{cz['cerca_limite']} parroquias distintas a < 50 m de un límite (admitido); {len(fz)} discrepancias")
    for x, y, msg in fz[:15]:
        lat, lon = ref.latlon(x, y)
        print(f"   {lat:.6f},{lon:.6f}: {msg}")
    fallos += fz
    print("Puntos de control:")
    malos = control(ref, a.region)
    if a.gen_tests:
        gen_tests(ref, a.region)
    sys.exit(1 if fallos or malos else 0)


if __name__ == "__main__":
    main()
