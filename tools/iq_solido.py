#!/usr/bin/env python3
"""Reempaqueta un .iq del SDK en 7z sólido, con el mismo contenido, fichero a fichero.

    tools/iq_solido.py ENTRADA.iq SALIDA.iq

Por qué (P98, 2026-10-30): el 7z que escribe monkeyc comprime cada fichero por separado, y un .iq con muchos relojes
lleva el mismo callejero decenas de veces. Calles Galicia con 54 relojes pesaba 428.449.046 B (66 piezas, 11 .prg
distintos) y el portal no admite más de 400 MB. En sólido, con las piezas iguales seguidas y el diccionario de 64 MiB
de lzma2 nivel 9, son 17.360.177 B. La firma no se toca: la de cada .prg va dentro de manifest.xml y manifest.sig2
firma ese manifest.xml, así que el envoltorio puede cambiar sin volver a firmar nada.

Falla cerrada: rc 1 y sin SALIDA si
  - la entrada no se lee, está vacía o le falta manifest.xml, manifest.sig2 o dev_key.pub;
  - la firma de manifest.sig2 no da «Verified OK» con dev_key.pub (en la entrada y en la salida);
  - la salida, extraída de nuevo, no tiene exactamente los mismos ficheros con el mismo sha1 uno a uno;
  - iq_limpio.py no da 0 sobre la salida (rutas del Mac). Se busca en IQ_LIMPIO o en el PATH; sin él, falla.
SALIDA no puede existir antes: se escribe en SALIDA.parcial y solo se renombra cuando todo pasa.
Solo herramientas del sistema: bsdtar (libarchive) y openssl. La prueba en los dos sentidos, en ./ciq.sh guarda-test.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FIJOS = ["manifest.xml", "manifest.sig2", "dev_key.pub"]
OPCIONES = "7zip:compression=lzma2,7zip:compression-level=9"


class Fallo(Exception):
    pass


def orden(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def extraer(iq, dst):
    r = orden(["bsdtar", "-xf", str(iq), "-C", str(dst)])
    if r.returncode:
        raise Fallo(f"bsdtar no puede leer {iq}: {r.stderr.strip()}")


def huellas(d):
    """{ruta relativa: sha1} de todos los ficheros de d. Un enlace o algo que no sea fichero ni carpeta, falla."""
    h = {}
    for p in sorted(d.rglob("*")):
        if p.is_symlink() or not (p.is_file() or p.is_dir()):
            raise Fallo(f"{p.relative_to(d)} no es un fichero normal")
        if p.is_file():
            h[p.relative_to(d).as_posix()] = hashlib.sha1(p.read_bytes()).hexdigest()
    return h


def lista(h):
    """Los fijos primero; después cada pieza entera, con las piezas ordenadas por el sha1 de su .prg para que las
    iguales queden seguidas, dentro del diccionario."""
    piezas = {}
    for f in h:
        if "/" in f:
            piezas.setdefault(f.split("/", 1)[0], []).append(f)
    sueltos = sorted(f for f in h if "/" not in f and f not in FIJOS)

    def clave(p):
        prg = sorted(f for f in piezas[p] if f.endswith(".prg"))
        return (h[prg[0]] if prg else "", p)

    out = [f for f in FIJOS if f in h] + sueltos
    for p in sorted(piezas, key=clave):
        out += sorted(piezas[p], key=lambda f: (not f.endswith(".prg"), f))
    return out


def empaquetar(d, ficheros, dst):
    r = orden(["bsdtar", "--format", "7zip", "--options", OPCIONES, "-cf", str(dst), "-T", "-"],
              cwd=d, input="\n".join(ficheros) + "\n")
    if r.returncode:
        raise Fallo(f"bsdtar no pudo escribir {dst}: {r.stderr.strip()}")


def firma(d):
    falta = [f for f in FIJOS if not (d / f).is_file()]
    if falta:
        raise Fallo(f"faltan {', '.join(falta)}")
    r = orden(["openssl", "dgst", "-sha256", "-verify", str(d / "dev_key.pub"), "-keyform", "DER",
               "-signature", str(d / "manifest.sig2"), str(d / "manifest.xml")])
    if r.returncode or r.stdout.strip() != "Verified OK":
        raise Fallo(f"la firma de manifest.sig2 no verifica: {(r.stdout + r.stderr).strip()}")
    return r.stdout.strip()


def limpio(iq):
    exe = os.environ.get("IQ_LIMPIO") or shutil.which("iq_limpio.py")
    if not exe:
        raise Fallo("no encuentro iq_limpio.py (ni en IQ_LIMPIO ni en el PATH)")
    r = orden([exe, str(iq)])
    if r.returncode:
        raise Fallo(f"iq_limpio.py sale con {r.returncode}: {(r.stdout + r.stderr).strip()}")
    return r.stdout.strip()


def solido(ent, sal):
    """Devuelve las líneas del informe; si algo falla, Fallo, y no queda ni SALIDA ni SALIDA.parcial."""
    parcial = sal.with_name(sal.name + ".parcial")
    if sal.exists() or parcial.exists():
        raise Fallo(f"{sal} o {parcial.name} ya existe: no se pisa")
    if not ent.is_file() or ent.stat().st_size == 0:
        raise Fallo(f"{ent} no existe o está vacío")
    hecho = False
    try:
        with tempfile.TemporaryDirectory() as t:
            a, b = Path(t, "a"), Path(t, "b")
            a.mkdir()
            b.mkdir()
            extraer(ent, a)
            h = huellas(a)
            if not h:
                raise Fallo(f"{ent} no tiene nada dentro")
            firma(a)
            ficheros = lista(h)
            if sorted(ficheros) != sorted(h):
                raise Fallo("la lista de empaquetado no es la de la entrada")
            empaquetar(a, ficheros, parcial)
            extraer(parcial, b)
            h2 = huellas(b)
            if h2 != h:
                faltan, sobran = sorted(set(h) - set(h2)), sorted(set(h2) - set(h))
                distintos = sorted(f for f in set(h) & set(h2) if h[f] != h2[f])
                raise Fallo(f"la salida no es la entrada: faltan {faltan}, sobran {sobran}, distintos {distintos}")
            v = firma(b)
            l = limpio(parcial)
        os.replace(parcial, sal)
        hecho = True
    finally:
        if not hecho and parcial.exists():
            parcial.unlink()
    sha = hashlib.sha1(sal.read_bytes()).hexdigest()
    return [f"entrada  {ent}: {ent.stat().st_size:,} B".replace(",", "."),
            f"salida   {sal}: {sal.stat().st_size:,} B, sha1 {sha}".replace(",", "."),
            f"ficheros {len(h)}, todos con el mismo sha1 que en la entrada",
            f"firma    manifest.sig2 con dev_key.pub: {v}",
            f"rutas    iq_limpio.py: {l}"]


def main(argv):
    if len(argv) != 2:
        print("uso: iq_solido.py ENTRADA.iq SALIDA.iq", file=sys.stderr)
        return 2
    try:
        informe = solido(Path(argv[0]), Path(argv[1]))
    except (Fallo, OSError, subprocess.SubprocessError) as e:
        print(f"iq_solido: {e}. No dejo salida.", file=sys.stderr)
        return 1
    print("\n".join(informe))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
