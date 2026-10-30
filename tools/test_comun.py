#!/usr/bin/env python3
"""escribir_comun con regiones de celdas de raster distintas, sobre metas sintéticas en una carpeta temporal.

    python3 -I tools/test_comun.py

c5: dos provincias (RCEL 250 y 100, ZONA 20000) no hacen morir el build común, y cada app (--solo) lleva su RCEL
y su RN. Las demás variantes, con RCEL distintos, mueren sin escribir nada: ni lo común ni la región recién hecha.
"""
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_callejero as bc  # noqa: E402


def preparar(raiz, variante, regiones):
    """regiones: {nombre: (id, zona, rcel)}. Escribe regiones.json, las metas y el .xml de cada una."""
    bc.ROOT, bc.TOOLS, bc.OUT, bc.VARIANTE = raiz, raiz / "tools", raiz / "tools" / "out", variante
    bc.OUT.mkdir(parents=True)
    (bc.TOOLS / "regiones.json").write_text(json.dumps({n: {"id": i} for n, (i, _, _) in regiones.items()}), "utf-8")
    for n, (i, zona, rcel) in regiones.items():
        meta = dict(region=n, id=i, etiqueta=n.capitalize(), idx=["t0"], zidx=[["z0", None, None, None]], cajas=None,
                    zona=zona, rcel=rcel, rn=zona // rcel, zona_propia=False, bbox=[42.0, -9.0, 43.0, -8.0])
        (bc.OUT / f"meta-{n}{bc.sufijo()}.json").write_text(json.dumps(meta), "utf-8")
        (bc.res_gen() / n).mkdir(parents=True)
        (bc.res_gen() / n / f"{n}.xml").write_text("<jsonDataResources/>\n", "utf-8")


def constante(mc, nombre):
    return int(re.search(rf"(?:const|var) {nombre}(?: as Number)? = (\d+);", mc).group(1))


def c5_dos_provincias():
    with tempfile.TemporaryDirectory() as t:
        raiz = Path(t)
        preparar(raiz, "c5", {"coruna": (21, 20000, 250), "pontevedra": (22, 20000, 100)})
        bc.escribir_comun()
        assert (bc.src_gen() / "Callejero.mc").exists() and (bc.src_gen() / "Regiones.mc").exists()
        for n, rcel in (("coruna", 250), ("pontevedra", 100)):
            bc.escribir_comun(solo=[n], salida=raiz / "app" / n)
            mc = (raiz / "app" / n / "source" / "Callejero.mc").read_text("utf-8")
            assert (constante(mc, "RCEL"), constante(mc, "RN"), constante(mc, "ZONA")) == (rcel, 20000 // rcel, 20000), n
    print("c5: el común con RCEL 250 y 100 no muere; cada app lleva el suyo")


def c_sin_escribir_a_medias():
    with tempfile.TemporaryDirectory() as t:
        preparar(Path(t), "c", {"madrid": (2, 4000, 50), "santiago": (1, 4000, 100)})
        # La región recién hecha, como la deja escribir() antes de llamar a escribir_comun.
        bc.src_gen().mkdir(parents=True)
        modulo = bc.src_gen() / "RegionMadrid.mc"
        modulo.write_text("module RegionMadrid {}\n", "utf-8")
        meta = bc.OUT / f"meta-madrid{bc.sufijo()}.json"
        try:
            bc.escribir_comun(recien=(bc.res_gen() / "madrid", modulo, meta))
        except SystemExit as e:
            assert "distint" in str(e), e
        else:
            raise AssertionError("la variante c con RCEL distintos no murió")
        restos = [p.name for p in (bc.src_gen().iterdir())] + [p.name for p in bc.res_gen().iterdir()]
        assert sorted(restos) == ["santiago"], f"quedó a medias: {sorted(restos)}"
        assert not meta.exists()
    print("c: RCEL distintos mueren sin dejar nada a medias")


def c_comprobar_antes_de_generar():
    """La comprobación de main() (antes de descargar y escribir): la región nueva frente a las ya generadas."""
    with tempfile.TemporaryDirectory() as t:
        preparar(Path(t), "c", {"santiago": (1, 4000, 100)})
        assert "distint" in (bc.comprobar_comun(bc.metas_comunes(), nueva=dict(
            region="madrid", id=2, zona=4000, rcel=50, rn=80, zona_propia=False)) or "")
        assert "mismo id" in (bc.comprobar_comun(bc.metas_comunes(), nueva=dict(
            region="madrid", id=1, zona=4000, rcel=100, rn=40, zona_propia=False)) or "")
        assert bc.comprobar_comun(bc.metas_comunes(), nueva=dict(
            region="santiago", id=1, zona=4000, rcel=50, rn=80, zona_propia=False)) is None   # se rehace a sí misma
        bc.VARIANTE = "c5"
        assert bc.comprobar_comun([], nueva=dict(region="x", id=3, zona=20000, rcel=250, rn=80, zona_propia=False)) is None
    print("c: la región nueva se comprueba antes de generarla")


def muere(f, *args, **kw):
    """El mensaje de sys.exit de f, o AssertionError si no murió."""
    try:
        f(*args, **kw)
    except SystemExit as e:
        return str(e)
    raise AssertionError(f"{f.__name__} no murió")


def solo_desconocida():
    """--solo con un nombre que no está en regiones.json (otra grafía, otra caja): antes se caía de la cuenta y
    Regiones.mc salía vacío. Ahora muere nombrándolo, sin escribir nada."""
    with tempfile.TemporaryDirectory() as t:
        raiz = Path(t)
        preparar(raiz, "normal", {"galicia": (5, 20000, 100)})
        msg = muere(bc.escribir_comun, solo=["acoruna"], salida=raiz / "app")
        assert "acoruna" in msg, msg
        msg = muere(bc.escribir_comun, solo=["galicia", "acoruna"], salida=raiz / "app")
        assert "acoruna" in msg and "galicia" not in msg, msg
        assert not (raiz / "app").exists(), "escribió algo"
        bc.escribir_comun(solo=["galicia"], salida=raiz / "app")   # la que existe, sí
        assert "Galicia" in (raiz / "app" / "source" / "Regiones.mc").read_text("utf-8")
    print("--solo: una región desconocida muere nombrándola")


def sin_metas():
    """--comun en un worktree sin tools/out/meta-*: antes escribía un Regiones.mc vacío que ni compilaba."""
    with tempfile.TemporaryDirectory() as t:
        preparar(Path(t), "normal", {})
        msg = muere(bc.escribir_comun)
        assert "meta" in msg, msg
        assert not (bc.src_gen() / "Regiones.mc").exists(), "escribió Regiones.mc"
    print("--comun sin metas muere sin escribir Regiones.mc")


if __name__ == "__main__":
    c5_dos_provincias()
    c_sin_escribir_a_medias()
    c_comprobar_antes_de_generar()
    solo_desconocida()
    sin_metas()
