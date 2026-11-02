#!/usr/bin/env python3
"""El banner de la tienda (tools/banner.py): los diez, a la norma del portal, y las comprobaciones cerradas.

    python3 -I tools/test_banner.py

Genera los diez (galicia, madrid, coruna, pontevedra y valencia × es y en) en una carpeta temporal, no en
docs/tienda/, y comprueba medida, PNG y peso; los cuatro de Galicia y Madrid, byte a byte con los aprobados.
Una medida mala, un tope bajo, un lema o un rótulo que no caben mueren sin escribir nada.
"""
import hashlib
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import banner as B  # noqa: E402
from PIL import Image  # noqa: E402


# Los aprobados por el autor el 2026-10-30: no cambian al añadir regiones.
SHA1 = {("galicia", "es"): "6eb1374e8803a793ff7714cc0f3568a83da1509d",
        ("galicia", "en"): "ff02f1b977f99ba93081cbc1ddcddb0416bf4f94",
        ("madrid", "es"): "49999b1d00616c351d2b777038ebb38341dfa7dd",
        ("madrid", "en"): "be4c9d5972b6dbe58cdb5fff1ac5ef861308dc90"}


def muere(f, *a):
    try:
        f(*a)
    except SystemExit as e:
        return str(e)
    raise AssertionError("no murió")


def los_diez():
    salidas = B.SALIDAS
    with tempfile.TemporaryDirectory() as t:
        B.SALIDAS = {r: Path(t) / r for r in salidas}
        for region in B.SALIDAS:
            for idioma in B.LEMAS:
                out = B.salida(region, idioma)
                B.escribir(B.banner(region, idioma), out)
                with Image.open(out) as im:
                    assert im.size == (1440, 720), im.size
                    assert im.format == "PNG", im.format
                assert os.path.getsize(out) <= 2_048_000, os.path.getsize(out)
                assert B.comprobar(out) == []
                if (region, idioma) in SHA1:
                    assert hashlib.sha1(out.read_bytes()).hexdigest() == SHA1[region, idioma], (region, idioma)
        assert sorted(p.name for p in Path(t).rglob("*.png")) == ["banner_en.png"] * 5 + ["banner_es.png"] * 5
    B.SALIDAS = salidas
    print("los diez: 1440×720, PNG, bajo 2.048.000 B; Galicia y Madrid, los mismos bytes que los aprobados")


def medida_mala():
    with tempfile.TemporaryDirectory() as t:
        out = Path(t) / "banner_es.png"
        msg = muere(B.escribir, Image.new("RGB", (1400, 720)), out)
        assert "medida 1400×720" in msg and "proporción" in msg, msg
        assert not list(Path(t).iterdir()), list(Path(t).iterdir())
        msg = muere(B.escribir, Image.new("RGB", (1440, 760)), out)
        assert "medida 1440×760" in msg, msg
        assert not list(Path(t).iterdir()), list(Path(t).iterdir())
    print("medida mala: muere sin escribir")


def tope_bajo():
    with tempfile.TemporaryDirectory() as t:
        out = Path(t) / "banner_es.png"
        msg = muere(B.escribir, Image.new("RGB", B.MEDIDA, (9, 9, 9)), out, 10)
        assert "peso" in msg and "tope de 10 B" in msg, msg
        assert not list(Path(t).iterdir()), list(Path(t).iterdir())
    print("tope bajo: muere sin escribir")


def no_png():
    with tempfile.TemporaryDirectory() as t:
        jpg = Path(t) / "x.jpg"
        Image.new("RGB", B.MEDIDA).save(jpg, "JPEG")
        assert B.comprobar(jpg) == ["formato JPEG, no PNG"], B.comprobar(jpg)
    print("JPEG: no pasa")


def lema_largo():
    lemas = dict(B.LEMAS)
    try:
        B.LEMAS["en"] = "STREET NAME AND DOOR NUMBER, NO SIGNAL"
        msg = muere(B.banner, "madrid", "en")
        assert "no cabe" in msg, msg
    finally:
        B.LEMAS.clear()
        B.LEMAS.update(lemas)
    print("lema más ancho que el es: muere")


def rotulo_largo():
    titulos = dict(B.C.TITULOS)
    try:
        B.C.TITULOS["coruna"] = "PROVINCIA DA CORUÑA E MAIS AS RÍAS ALTAS"
        msg = muere(B.banner, "coruna", "es")
        assert "rótulo" in msg and "no cabe" in msg, msg
    finally:
        B.C.TITULOS.clear()
        B.C.TITULOS.update(titulos)
    print("rótulo que no cabe ni apretado: muere")


if __name__ == "__main__":
    medida_mala()
    tope_bajo()
    no_png()
    lema_largo()
    rotulo_largo()
    los_diez()
