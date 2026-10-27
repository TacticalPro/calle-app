import Toybox.Lang;
import Toybox.WatchUi;

// Parroquia, lugar y barrio de un punto (formato en tools/build_callejero.py). Una zona cargada
// a la vez, aparte de la tesela de calles: la anterior se suelta antes de cargar la siguiente.
// Es el mismo algoritmo que Ref.zona() de tools/ref.py, que lo valida contra los límites reales.
//
// Versión de la c5 (apps por provincia de los relojes de 128 KB; plan 4 de la c5, 2026-10-27): la compilan en
// lugar de source/Zonas.mc (sourcePath por fichero, tools/tienda.py). Lo único distinto es que las zonas van en
// árbol cuaternario: Callejero.ZIDX tiene una entrada por celda de Callejero.ZONA m, y cada una es null, la zona
// o la lista de sus cuatro hijos (SO, SE, NO, NE), de la mitad de lado, hasta 2,5 km. Cada zona lleva su lado al
// final (z[10]). Así ninguna pasa del tope de 13 KB sin repetir los lugares del margen en zonas pequeñas donde no
// hace falta.
module Zonas {
    var _clave as Number = -1;  // raíz × 1024 + camino en el árbol de la zona cargada; -1, ninguna
    var _z as Array or Null = null;
    var _reg as Number = 0;     // región de la zona cargada (Callejero.ID)

    // [parroquia, lugar, barrio] (String o null cada uno) del punto en metros de región;
    // null si cae fuera de la rejilla de zonas. Donde el polígono es el barrio oficial (Madrid,
    // Callejero.ZBARRIO), va en barrio y no hay parroquia.
    // Suelta la zona cargada (el Localizador lo hace antes de cargar una tesela: cargar un recurso pide
    // el doble de su tamaño, y en los relojes de 128 KB no sobra).
    function soltar() as Void {
        _z = null;
        _clave = -1;
    }

    function consultar(x as Float, y as Float) as Array<String or Null> or Null {
        var r = _consultar(x, y);
        if (r != null && Callejero.ZBARRIO) {
            return [null, r[1], r[0]] as Array<String or Null>;
        }
        return r;
    }

    function _consultar(x as Float, y as Float) as Array<String or Null> or Null {
        if (_reg != Callejero.ID) {
            _z = null;
            _clave = -1;
            _reg = Callejero.ID;
        }
        if (x < 0.0 || y < 0.0) {
            return null;
        }
        var lado = Callejero.ZONA;
        var zc = (x / lado).toNumber();
        var zf = (y / lado).toNumber();
        if (zc >= Callejero.ZCOLS || zf >= Callejero.ZFILAS) {
            return null;
        }
        var i = zf * Callejero.ZCOLS + zc;
        // Se baja por el árbol hasta la hoja que contiene el punto; el camino (1-4 por nivel) la identifica.
        var n = Callejero.ZIDX[i];
        var ox = zc * lado;
        var oy = zf * lado;
        var camino = 0;
        while (n instanceof Array) {
            lado = lado / 2;
            var h = (x - ox >= lado ? 1 : 0) + (y - oy >= lado ? 2 : 0);
            ox += (h & 1) * lado;
            oy += (h >> 1) * lado;
            camino = camino * 5 + h + 1;
            n = (n as Array)[h];
        }
        var clave = i * 1024 + camino;
        if (clave != _clave) {
            _z = null;   // soltar la anterior antes de cargar: nunca dos en memoria
            _clave = clave;
            if (n != null) {
                var d = WatchUi.loadResource(n as ResourceId) as Array;
                if (d[0] != Callejero.FORMATO) {
                    throw new Lang.InvalidValueException("zona con formato " + d[0]);
                }
                _z = d;
            }
        }
        var z = _z;
        if (z == null) {
            return [null, null, null] as Array<String or Null>;
        }
        return buscar(z, x - ox.toFloat(), y - oy.toFloat());
    }

    // x, y en metros desde la esquina SO de la zona (los tests la llaman con zonas sintéticas).
    //   parroquia: la de la celda del raster;
    //   lugar: el poblado más cercano a menos de LUGAR_R; si no hay, el paraje más cercano;
    //   barrio: el más cercano a menos de BARRIO_R, si además está a menos de BARRIO_FRAC de
    //   la distancia al segundo (en la frontera entre dos no se adivina).
    // z: [FORMATO, S, O, F, RL, L, LN, H, FZ, ZU, lado] (tools/build_callejero.py); sin lado (las zonas sintéticas de
    // los tests), Callejero.ZONA.
    function buscar(z as Array, x as Float, y as Float) as Array<String or Null> {
        var S = z[1] as String;
        var O = z[2] as Array<Number>;
        var F = z[3] as Array<Number>;
        var RL = z[4] as Array<Number>;
        var L = z[5] as Array<Number>;
        var LN = z[6] as Array<Number>;
        var zu = z.size() > 9 ? z[9] as Number : 1;   // metros por unidad de L (variante b: 2)
        var lado = z.size() > 10 ? z[10] as Number : Callejero.ZONA;
        var rn = lado / Callejero.RCEL;
        var c = (x / Callejero.RCEL).toNumber();
        var r = (y / Callejero.RCEL).toNumber();
        c = c >= rn ? rn - 1 : c;
        r = r >= rn ? rn - 1 : r;
        // La fila r va de su primer tramo al de la siguiente; se avanza hasta el que cubre la columna c.
        var k = par16(F, r);
        var k1 = par16(F, r + 1);
        var v = 0;
        var col = 0;
        while (k < k1) {
            var t = par16(RL, k);
            col += (t >> 8) & 0xFF;
            if (c < col) {
                v = t & 0xFF;
                break;
            }
            k++;
        }

        var px = x + Callejero.ZMARGEN;
        var py = y + Callejero.ZMARGEN;
        var rl2 = (Callejero.LUGAR_R * Callejero.LUGAR_R).toFloat();
        var jl = -1;          // poblado
        var dl = 0.0;
        var jp = -1;          // paraje
        var dp = 0.0;
        var jb = -1;          // barrio, y el segundo más cercano
        var db = 0.0;
        var db2 = Buscador.LEJOS;
        // Solo cuentan los lugares a ZMARGEN m del punto en x y en y: es el radio del lugar y cubre el barrio
        // (BARRIO_R / BARRIO_FRAC), así que lo de fuera no cambia el resultado. L va por franjas de H m desde el
        // sur y, dentro de cada una, por x (FZ: dónde empieza cada franja); se recorren las franjas que tocan y,
        // en cada una, el tramo de x, buscado por bisección. Recorrer L entera hacía saltar el watchdog en el 7X
        // Pro con Galicia (zonas de 10 km con hasta 3.032 lugares, ERA del 2026-10-25). Datos sin franjas: una
        // sola, ordenada por x.
        var R = Callejero.ZMARGEN.toFloat();
        var xmin = px - R;
        var xmax = px + R;
        var s0 = 0;
        var s1 = 0;
        var FZ = null as Array<Number> or Null;
        if (z.size() > 8) {
            var H = z[7] as Number;
            FZ = z[8] as Array<Number>;
            var nf = (lado + 2 * Callejero.ZMARGEN + H - 1) / H;   // franjas
            s0 = ((py - R) / H).toNumber();
            s1 = ((py + R) / H).toNumber();
            s0 = s0 < 0 ? 0 : s0;
            s1 = s1 > nf - 1 ? nf - 1 : s1;
        }
        for (var sf = s0; sf <= s1; sf++) {
            var lo = FZ == null ? 0 : par16(FZ, sf);
            var fin = FZ == null ? L.size() : par16(FZ, sf + 1);
            var hi = fin;
            while (lo < hi) {
                var m = (lo + hi) / 2;
                if (((L[m] & 0x3FFF) * zu).toFloat() < xmin) {
                    lo = m + 1;
                } else {
                    hi = m;
                }
            }
            for (var j = lo; j < fin; j++) {
                var p = L[j];
                var lx = ((p & 0x3FFF) * zu).toFloat();
                if (lx > xmax) {
                    break;
                }
                var dx = px - lx;
                var dy = py - (((p >> 14) & 0x3FFF) * zu).toFloat();
                var d2 = dx * dx + dy * dy;
                var tipo = (p >> 28) & 7;
                if ((tipo & 1) != 0 && d2 <= rl2 && (jl < 0 || d2 < dl)) {
                    jl = j;
                    dl = d2;
                }
                if ((tipo & 4) != 0 && d2 <= rl2 && (jp < 0 || d2 < dp)) {
                    jp = j;
                    dp = d2;
                }
                if ((tipo & 2) != 0) {
                    if (jb < 0 || d2 < db) {
                        if (jb >= 0) {
                            db2 = db;
                        }
                        jb = j;
                        db = d2;
                    } else if (d2 < db2) {
                        db2 = d2;
                    }
                }
            }
        }
        var lugar = jl >= 0 ? nombre(S, O, par16(LN, jl)) : (jp >= 0 ? nombre(S, O, par16(LN, jp)) : null);
        var f2 = Callejero.BARRIO_FRAC * Callejero.BARRIO_FRAC;
        var barrio = jb >= 0 && db <= (Callejero.BARRIO_R * Callejero.BARRIO_R).toFloat() && db <= f2 * db2
            ? nombre(S, O, par16(LN, jb)) : null;
        return [v > 0 ? nombre(S, O, v - 1) : null, lugar, barrio] as Array<String or Null>;
    }

    // El entero de 16 bits k de un array con 2 por número.
    function par16(A as Array<Number>, k as Number) as Number {
        return (A[k >> 1] >> ((k & 1) * 16)) & 0xFFFF;
    }

    // El nombre k de una cadena "\n"-separada con sus inicios O (como en las teselas).
    function nombre(S as String, O as Array<Number>, k as Number) as String {
        return S.substring(par16(O, k), par16(O, k + 1) - 1) as String;
    }
}
