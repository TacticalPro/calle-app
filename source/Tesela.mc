import Toybox.Lang;
import Toybox.WatchUi;

// Una tesela del callejero (FORMATO 4, en tools/build_callejero.py). El reloj tiene
// una sola cargada: la anterior se suelta antes de cargar la siguiente.
class Tesela {
    var idx as Number;
    var ox as Float;    // esquina SO de la tesela con su margen, en metros de región
    var oy as Float;
    var x1 as Float;    // esquina NE sin el margen
    var y1 as Float;
    var nc as Number;   // calles (los nombres siguientes en S son sufijos de portal)
    var pb as Number;   // bits por coordenada de portal (12, o 13 en las teselas de más de 4.095 m)
    var S as String;    // "\n" + cada nombre + "\n"
    var O as Array<Number>;
    var C as Array<Number>;
    var CB as Array<Number>;
    var R as Array<Number>;
    var V as Array<Number>;
    var P as Array<Number>;
    var E as Array<Number>;
    var mejor as Array<Float>;      // distancia por calle de la última búsqueda
    var mejorRun as Array<Number>;  // y su tirada más cercana (offset en R): de ella sale el tramo

    // caja: [x0, y0, x1, y1] de la tesela sin margen, en metros de región (Teselas.caja).
    function initialize(i as Number, datos as Array, caja as Array<Number>) {
        if (datos[0] != Callejero.FORMATO) {
            throw new Lang.InvalidValueException("tesela con formato " + datos[0]);
        }
        idx = i;
        ox = (caja[0] - Callejero.BUF).toFloat();
        oy = (caja[1] - Callejero.BUF).toFloat();
        x1 = caja[2].toFloat();
        y1 = caja[3].toFloat();
        nc = datos[1] as Number;
        pb = datos[2] as Number;
        S = datos[3] as String;
        O = datos[4] as Array<Number>;
        C = datos[5] as Array<Number>;
        CB = datos[6] as Array<Number>;
        R = datos[7] as Array<Number>;
        V = datos[8] as Array<Number>;
        P = datos[9] as Array<Number>;
        E = datos[10] as Array<Number>;
        mejor = new Array<Float>[nc];
        mejorRun = new Array<Number>[nc];
    }

    // Dónde empieza en S el nombre k.
    function inicio(k as Number) as Number {
        return (O[k >> 1] >> ((k & 1) * 16)) & 0xFFFF;
    }

    // El nombre k: una calle (k < nc) o un sufijo de portal.
    function nombre(k as Number) as String {
        return S.substring(inicio(k), inicio(k + 1) - 1) as String;
    }

    // [A, B]: las calles que cruzan en los extremos del trozo más cercano de la calle s en la
    // última búsqueda (null = ninguna). Tal cual vienen del callejero, sin ordenar ni depurar.
    function tramo(s as Number) as Array<String or Null> {
        var r = mejorRun[s];
        if (r == null || r < 0) {
            return [null, null] as Array<String or Null>;
        }
        var h = R[r + 1];
        var a = (h >> 6) & 0x3FF;
        var b = (h >> 16) & 0x3FF;
        return [a > 0 ? nombre(a - 1) : null, b > 0 ? nombre(b - 1) : null] as Array<String or Null>;
    }

    // Sigue valiendo mientras el punto no salga de la tesela más la holgura (BUF − MAXD):
    // ahí dentro tiene todas las calles a menos de MAXD. Evita recargar en los bordes.
    function cubre(x as Float, y as Float) as Boolean {
        var h = Callejero.BUF - Callejero.MAXD;
        var x0 = ox + Callejero.BUF;
        var y0 = oy + Callejero.BUF;
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
    // null si la celda no tiene calles (entonces no hay ninguna a menos de MAXD).
    function cargar(i as Number) as Tesela or Null {
        var rid = Callejero.IDX[i];
        if (rid == null) {
            return null;
        }
        return new Tesela(i, WatchUi.loadResource(rid) as Array, caja(i));
    }

    // [x0, y0, x1, y1] de la tesela i sin margen, en metros de región.
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
