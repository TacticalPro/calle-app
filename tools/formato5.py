#!/usr/bin/env python3
"""FORMATO 5: una tesela del FORMATO 4 (la lista de build_callejero.empaquetar) en bytes, para los relojes de
128 KB (variante c5). Especificación: docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md.

Palabras de 32 bits little-endian (los 4 bytes de cada CB quedan sueltos: x0, y0, x1, y1):
  cabecera (CABECERA palabras): FORMATO | U << 8 | PB << 16, NC, bytes de S, y cuántas palabras tienen
  O, C, CB, K, R, V, P y E; luego S (UTF-8, rellenada a múltiplo de 4) y esas tablas, en ese orden.
U: metros por unidad de las coordenadas de la tesela (1 en ciudad, 4 en el rural; el contenido ya viene en
esas unidades). K (nuevo): por calle, y una más al final, el bit de V donde empiezan los vértices de su
primera tirada: la búsqueda salta una calle lejana sin recorrer sus tiradas.
O: como en el FORMATO 4 (2 por número, 16 bits), pero en BYTES de S y no en caracteres: el reloj lee cada
nombre de los bytes cuando lo necesita, sin guardar S como String (plan 2). Las calles van en orden de bytes
UTF-8, que es el de sorted() en build_callejero.empaquetar: Tesela.indiceDe busca por bisección.
"""
import struct

FORMATO = 5
CABECERA = 11


def _palabras(ws):
    return struct.pack(f"<{len(ws)}I", *[w & 0xFFFFFFFF for w in ws])


def _int32(v):
    return v - (1 << 32) if v >= 1 << 31 else v


def inicios(S, en_bytes):
    """O de S ("\\n" + cada nombre + "\\n"): dónde empieza cada nombre y uno final, 2 por número. En caracteres
    (FORMATO 4, el de build_callejero.cadena_nombres) o en bytes UTF-8 (FORMATO 5)."""
    offs, pos = [], 1
    for e in S[1:].split("\n")[:-1]:
        offs.append(pos)
        pos += (len(e.encode("utf-8")) if en_bytes else len(e)) + 1
    offs.append(pos)
    assert pos < 1 << 16, pos
    if len(offs) % 2:
        offs.append(0)
    return [_int32(offs[j] | offs[j + 1] << 16) for j in range(0, len(offs), 2)]


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
    assert O == inicios(S, False), "O no corresponde a S"
    tablas = [inicios(S, True), C, CB, indice_k(nc, C, R), R, V, P, E]
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
    O5, C, CB, K, R, V, P, E = tablas
    assert O5 == inicios(S, True), "O del FORMATO 5 no corresponde a S"
    return [4, nc, pb, S, inicios(S, False), C, CB, R, V, P, E], u, K
