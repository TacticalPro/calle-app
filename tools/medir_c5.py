"""Medición exploratoria de Galicia en los relojes de 128 KB (2026-10-26), la que fundamenta la especificación
docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md. NO es parte del generador: el plan 2 lleva su lógica
(zona urbana por INE, encadenar() de las vías rurales, zonas sin parajes fuera) a build_callejero.py.

    python3 tools/medir_c5.py ~/code/calle-fenix combinado:4:8           (URBANA=15 para los 15 municipios)
    python3 tools/medir_c5.py ~/code/calle-fenix teselas:4 | palancas:4:8:0 | zonas | zonas2

Importa build_callejero.py del árbol que se le pase (necesita su tools/cache con pbf-galicia-*.json y el Catastro).
Tarda de 2 a 20 min según el modo.
"""
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

copia = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(copia / "tools"))
import build_callejero as B  # noqa: E402

# INE de los municipios (provincia + municipio): A Coruña, Santiago, Ferrol, Lugo, Ourense, Pontevedra, Vigo
URBANA = {"15030": "A Coruña", "15078": "Santiago", "15036": "Ferrol", "27028": "Lugo",
          "32054": "Ourense", "36038": "Pontevedra", "36057": "Vigo"}
if os.environ.get("URBANA") == "15":
    URBANA.update({"15054": "Narón", "15073": "Ribeira", "27031": "Monforte de Lemos", "27066": "Viveiro",
                   "36024": "Lalín", "36026": "Marín", "36060": "Vilagarcía de Arousa", "36045": "Redondela"})

t0 = time.time()


def log(*a):
    print(f"[{time.time() - t0:6.0f}s]", *a, flush=True)


B.VARIANTE = "c"
B.KD = True
B.ZONA, B.KD_TOPE = 10000, 26 * 1024
B.TESELA = B.KD_PASO
B.RN = B.ZONA // B.RCEL

regiones = json.loads((B.TOOLS / "regiones.json").read_text("utf-8"))
cfg = dict(regiones["galicia"])
overrides = json.loads((B.TOOLS / cfg["overrides"]).read_text("utf-8"))
proy = B.Proy(cfg["bbox"])
d = B.leer_pbf("galicia", "calles")
elems = d["elements"]
del d
cuenta, sin_pareja, por_lugar = Counter(), Counter(), Counter()
vias = B.extraer_vias(elems, proy, overrides, cuenta)
B.unificar_variantes(vias, cuenta)
lineales = [v for v in vias if not v["area"]]
portales = B.extraer_portales(elems, proy, lineales + [v for v in vias if v["area"]], overrides, cuenta,
                              sin_pareja, por_lugar)
del elems
dirs = B.descargar_catastro("galicia", cfg["catastro"], False)
portales, _ = B.completar_con_catastro(dirs, proy, lineales + [v for v in vias if v["area"]], portales, cuenta)
portales = [p for p in portales if p["num"] <= 0xFFF]
trozos = B.trocear(vias, cuenta)
log(f"vías {len(vias)}, trozos {len(trozos)}, portales {len(portales)}")

# Zona urbana: unión de las parroquias (admin_level 9) cuyo ref:ine empieza por el municipio.
dz = B.leer_pbf("galicia", "zonas")
anillos, por_muni = [], Counter()
for e in dz["elements"]:
    if e["type"] != "relation":
        continue
    ine = (e.get("tags", {}).get("ref:ine") or "")[:5]
    if ine not in URBANA:
        continue
    por_muni[URBANA[ine]] += 1
    tr = [[proy.xy(g["lat"], g["lon"]) for g in m["geometry"] if g]
          for m in e.get("members", []) if m.get("type") == "way" and m.get("role") in ("outer", "")
          and m.get("geometry")]
    for a in B.unir_anillos(tr):
        if len(a) >= 4:
            anillos.append((B.caja_de(a), a))
log("parroquias por municipio:", dict(por_muni), "anillos", len(anillos))


def en_zona_urbana(x, y):
    return any(bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3] and B.dentro(x, y, a) for bb, a in anillos)


dentro_p = [p for p in portales if en_zona_urbana(p["x"], p["y"])]
log(f"portales dentro {len(dentro_p)} / {len(portales)}")
cx = lambda v: ((v["bb"][0] + v["bb"][2]) / 2, (v["bb"][1] + v["bb"][3]) / 2)  # noqa: E731
n_dentro_v = sum(1 for v in trozos if en_zona_urbana(*cx(v)))
log(f"trozos con el centro dentro {n_dentro_v} / {len(trozos)}")

res = {"portales": len(portales), "portales_dentro": len(dentro_p), "trozos": len(trozos),
       "trozos_dentro": n_dentro_v, "parroquias_urbana": dict(por_muni)}


modo = sys.argv[2]


class P2:
    pass


def escalar(f):
    """Simula un formato con unidades de f m: divide todas las coordenadas por f."""
    tz = []
    for v in trozos:
        w = dict(v)
        w["pts"] = [(x / f, y / f) for x, y in v["pts"]]
        w["bb"] = tuple(c / f for c in v["bb"])
        if "raw" in w:
            w["raw"] = w["pts"]
        tz.append(w)
    pz = []
    for p in dentro_p:
        w = dict(p)
        w["x"], w["y"] = p["x"] / f, p["y"] / f
        pz.append(w)
    pr = P2()
    pr.ancho, pr.alto = proy.ancho / f, proy.alto / f
    return tz, pz, pr


def encadenar(vs):
    """Vías lineales de la misma calle que se tocan por un extremo (mismo nodo) → una sola polilínea."""
    por_ext = defaultdict(list)
    for i, v in enumerate(vs):
        if v.get("nodos"):
            por_ext[(v["nombre"], v["nodos"][0])].append(i)
            por_ext[(v["nombre"], v["nodos"][-1])].append(i)
    usada, salida = [False] * len(vs), []
    for i, v in enumerate(vs):
        if usada[i]:
            continue
        usada[i] = True
        if not v.get("nodos"):
            salida.append(dict(v))
            continue
        ns, pts = list(v["nodos"]), list(v["raw"])
        for lado in (1, 0):
            while True:
                n = ns[-1] if lado else ns[0]
                cand = [j for j in por_ext[(v["nombre"], n)] if not usada[j]]
                if not cand:
                    break
                j = cand[0]
                usada[j] = True
                w = vs[j]
                wn, wp = list(w["nodos"]), list(w["raw"])
                if lado:
                    if wn[0] != n:
                        wn, wp = wn[::-1], wp[::-1]
                    ns += wn[1:]
                    pts += wp[1:]
                else:
                    if wn[-1] != n:
                        wn, wp = wn[::-1], wp[::-1]
                    ns = wn[:-1] + ns
                    pts = wp[:-1] + pts
        salida.append(dict(v, nodos=ns, raw=pts, pts=pts))
    return salida


if modo.startswith("combinado"):
    # combinado:<f>:<dp>: medida 2 (rural sin cortar en los cruces, vías encadenadas, DP) + medida 1 (zonas sin
    # parajes fuera de la zona urbana)
    _, f, dp = modo.split(":")
    f, dp = int(f), float(dp)
    urb = [t for t in trozos if en_zona_urbana(*cx(t))]
    rur_v = [v for v in vias if not v["area"] and v["clase"] != 2 and not en_zona_urbana(*cx(v))]
    rur_a = [t for t in trozos if t["area"] and not en_zona_urbana(*cx(t))]
    cad = encadenar(rur_v)
    rur = []
    for v in cad:
        pts = B.douglas_peucker(v["raw"], dp)
        rur.append(dict(nombre=v["nombre"], clase=v["clase"], area=False, pts=pts, bb=B.caja_de(pts),
                        tramo=(None, None)))
    log(f"rural: vías {len(rur_v)} -> encadenadas {len(cad)}; trozos rurales antes "
        f"{len(trozos) - len(urb)}; vértices {sum(len(v['pts']) for v in rur)}")
    trozos = urb + rur + rur_a
    tz, pz, pr = escalar(f)
    t1 = time.time()
    ts, cajas = B.teselar_kd(tz, pz, pr, B.KD_TOPE)
    heaps, comp = [], {"ciudad": Counter(), "rural": Counter()}
    for i, c in enumerate(cajas):
        lista, est = B.empaquetar(c, ts[i], {})
        heaps.append(est["heap"])
        _, n, pb, S_, O_, C_, CB_, R_, V_, P_, E_ = lista
        m = comp["ciudad" if en_zona_urbana((c[0] + c[2]) / 2 * f, (c[1] + c[3]) / 2 * f) else "rural"]
        m["teselas"] += 1
        m["nombres_cadena"] += len(S_.encode())
        m["indices_por_calle"] += 5 * (len(O_) + len(C_) + len(CB_)) + 10 * n
        m["tramos_R"] += 5 * len(R_)
        m["vertices_V"] += 5 * len(V_)
        m["portales_P"] += 5 * (len(P_) + len(E_))
        m["heap"] += est["heap"]
    for k, m in comp.items():
        log(k, {a: (b // 1024 if a != "teselas" else b) for a, b in m.items()}, "(KB)")
    heaps.sort()
    r = dict(modo=modo, n=len(ts), heap_max=heaps[-1], heap_med=heaps[len(heaps) // 2],
             heap_total_kb=sum(heaps) // 1024, s=int(time.time() - t1))
    log("teselas", r)
    res["teselas"] = r
    parroquias, lugares = B.extraer_zonas(dz["elements"], proy, overrides, cuenta, cfg["zonas"])
    n0 = len(lugares)
    lugares = [l for l in lugares if l["tipo"] != 4 or en_zona_urbana(l["x"], l["y"])]
    log(f"lugares {n0} -> {len(lugares)} (sin parajes fuera de la zona urbana)")
    for zona, rcel in ((10000, 50), (20000, 100)):
        B.ZONA, B.RCEL = zona, rcel
        B.RN = zona // rcel
        zcols, zfilas = math.ceil(proy.ancho / zona), math.ceil(proy.alto / zona)
        G = B.rasterizar(parroquias, zcols, zfilas, Counter())
        hs = []
        for zf in range(zfilas):
            for zc in range(zcols):
                lista, est = B.empaquetar_zona(zc, zf, G, parroquias, lugares)
                if lista is not None:
                    hs.append(est["heap"])
        hs.sort()
        r = dict(n=len(hs), heap_max=hs[-1], heap_med=hs[len(hs) // 2], total_kb=sum(hs) // 1024,
                 mayores_26kb=sum(h > 26 * 1024 for h in hs))
        log(f"zonas {zona} m", r)
        res[f"zonas_{zona}"] = r
elif modo.startswith("palancas"):
    # palancas:<f>:<dp_rural_m>:<sendas 0|1>: trazado rural simplificado y, si sendas=0, sin sendas rurales
    _, f, dp, sendas = modo.split(":")
    f, dp, sendas = int(f), float(dp), sendas == "1"
    nuevos, nv0, nv1 = [], 0, 0
    for v in trozos:
        if en_zona_urbana(*cx(v)):
            nuevos.append(v)
            continue
        if not sendas and v["clase"] == 2:
            continue
        w = dict(v)
        nv0 += len(v["pts"])
        w["pts"] = v["pts"] if v["area"] else B.douglas_peucker(v["pts"], dp)
        nv1 += len(w["pts"])
        w["bb"] = B.caja_de(w["pts"])
        nuevos.append(w)
    log(f"rurales: vértices {nv0} -> {nv1}; trozos {len(trozos)} -> {len(nuevos)}")
    trozos = nuevos
    tz, pz, pr = escalar(f)
    t1 = time.time()
    ts, cajas = B.teselar_kd(tz, pz, pr, B.KD_TOPE)
    heaps = sorted(B.empaquetar(c, ts[i], {})[1]["heap"] for i, c in enumerate(cajas))
    comp = {"ciudad": Counter(), "rural": Counter()}
    for i, c in enumerate(cajas):
        lista, est = B.empaquetar(c, ts[i], {})
        _, n, pb, S_, O_, C_, CB_, R_, V_, P_, E_ = lista
        k = "ciudad" if en_zona_urbana((c[0] + c[2]) / 2 * f, (c[1] + c[3]) / 2 * f) else "rural"
        m = comp[k]
        m["teselas"] += 1
        m["nombres_cadena"] += len(S_.encode())
        m["indices_por_calle"] += 5 * (len(O_) + len(C_) + len(CB_)) + 10 * n
        m["tramos_R"] += 5 * len(R_)
        m["vertices_V"] += 5 * len(V_)
        m["portales_P"] += 5 * (len(P_) + len(E_))
        m["calles"] += n
        m["heap"] += est["heap"]
    for k, m in comp.items():
        log(k, {a: (b // 1024 if a not in ("teselas", "calles") else b) for a, b in m.items()}, "(KB)")
    r = dict(modo=modo, n=len(ts), heap_max=heaps[-1], heap_med=heaps[len(heaps) // 2],
             heap_total_kb=sum(heaps) // 1024, s=int(time.time() - t1))
    log("teselas", r)
    res["teselas"] = r
elif modo == "zonas2":
    parroquias, lugares = B.extraer_zonas(dz["elements"], proy, overrides, cuenta, cfg["zonas"])
    log(f"parroquias {len(parroquias)}, lugares {len(lugares)}")
    B.ZONA, B.RCEL = 20000, 100
    B.RN = 200
    zcols, zfilas = math.ceil(proy.ancho / B.ZONA), math.ceil(proy.alto / B.ZONA)
    G = B.rasterizar(parroquias, zcols, zfilas, Counter())
    comp = Counter()
    for zf in range(zfilas):
        for zc in range(zcols):
            lista, est = B.empaquetar_zona(zc, zf, G, parroquias, lugares)
            if lista is None:
                continue
            comp["raster_tramos_B"] += 5 * len(lista[4])
            comp["lugares_B"] += 5 * (len(lista[5]) + len(lista[6]))
            comp["nombres_B"] += len(lista[1].encode()) + 5 * len(lista[2])
            comp["total_heap_B"] += est["heap"]
    log("composición zonas 20 km", {k: v // 1024 for k, v in comp.items()}, "(KB)")
    res["zonas2"] = {k: v // 1024 for k, v in comp.items()}
elif modo.startswith("teselas"):
    f = int(modo.split(":")[1])
    tz, pz, pr = escalar(f)
    t1 = time.time()
    ts, cajas = B.teselar_kd(tz, pz, pr, B.KD_TOPE)
    heaps = sorted(B.empaquetar(c, ts[i], {})[1]["heap"] for i, c in enumerate(cajas))
    r = dict(unidad_m=f, lado_max_real_m=7800 * f, n=len(ts), heap_max=heaps[-1], heap_med=heaps[len(heaps) // 2],
             heap_total_kb=sum(heaps) // 1024, s=int(time.time() - t1))
    log("teselas", r)
    res["teselas"] = r
else:
    parroquias, lugares = B.extraer_zonas(dz["elements"], proy, overrides, cuenta, cfg["zonas"])
    del dz
    for zona, rcel in ((10000, 50), (20000, 100), (25000, 100)):
        B.ZONA, B.RCEL = zona, rcel
        B.RN = zona // rcel
        zcols, zfilas = math.ceil(proy.ancho / zona), math.ceil(proy.alto / zona)
        G = B.rasterizar(parroquias, zcols, zfilas, Counter())
        hs = []
        for zf in range(zfilas):
            for zc in range(zcols):
                lista, est = B.empaquetar_zona(zc, zf, G, parroquias, lugares)
                if lista is not None:
                    hs.append(est["heap"])
        hs.sort()
        r = dict(n=len(hs), heap_max=hs[-1], heap_med=hs[len(hs) // 2], mayores_26kb=sum(h > 26 * 1024 for h in hs))
        log(f"zonas {zona} m (raster {rcel} m)", r)
        res[f"zonas_{zona}"] = r

(Path(__file__).parent / "out").mkdir(exist_ok=True)
(Path(__file__).parent / "out" / f"medicion_c5_{modo.replace(':', '_')}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
log("fin")
