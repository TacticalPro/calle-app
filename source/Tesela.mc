import Toybox.Lang;
import Toybox.WatchUi;

// Una tesela del callejero (FORMATO 3, en tools/build_callejero.py). El reloj tiene
// una sola cargada: la anterior se suelta antes de cargar la siguiente.
class Tesela {
    var idx as Number;
    var ox as Float;    // esquina SO de la tesela con su margen, en metros de región
    var oy as Float;
    var nombres as Array<String>;
    var R as Array<Number>;
    var V as Array<Number>;
    var P as Array<Number>;
    var H as Array<Number>;
    var mejor as Array<Float>;      // distancia por calle de la última búsqueda
    var mejorRun as Array<Number>;  // y su tirada más cercana: de ella sale el tramo

    function initialize(i as Number, datos as Array) {
        if (datos[0] != Callejero.FORMATO) {
            throw new Lang.InvalidValueException("tesela con formato " + datos[0]);
        }
        idx = i;
        ox = ((i % Callejero.COLS) * Callejero.TESELA - Callejero.BUF).toFloat();
        oy = ((i / Callejero.COLS) * Callejero.TESELA - Callejero.BUF).toFloat();
        nombres = datos[1] as Array<String>;
        R = datos[2] as Array<Number>;
        V = datos[3] as Array<Number>;
        P = datos[4] as Array<Number>;
        H = datos[5] as Array<Number>;
        mejor = new Array<Float>[nombres.size()];
        mejorRun = new Array<Number>[nombres.size()];
    }

    // [A, B]: las calles que cruzan en los extremos del trozo más cercano de la calle s en la
    // última búsqueda (null = ninguna). Tal cual vienen del callejero, sin ordenar ni depurar.
    function tramo(s as Number) as Array<String or Null> {
        var r = mejorRun[s];
        if (r == null || r < 0) {
            return [null, null] as Array<String or Null>;
        }
        var t = R[4 * r + 3];
        var a = t & 0xFFF;
        var b = (t >> 12) & 0xFFF;
        return [a > 0 ? nombres[a - 1] : null, b > 0 ? nombres[b - 1] : null] as Array<String or Null>;
    }

    // Sigue valiendo mientras el punto no salga de la tesela más la holgura (BUF − MAXD):
    // ahí dentro tiene todas las calles a menos de MAXD. Evita recargar en los bordes.
    function cubre(x as Float, y as Float) as Boolean {
        var h = Callejero.BUF - Callejero.MAXD;
        var x0 = ox + Callejero.BUF;
        var y0 = oy + Callejero.BUF;
        return x >= x0 - h && x <= x0 + Callejero.TESELA + h && y >= y0 - h && y <= y0 + Callejero.TESELA + h;
    }

    function indiceDe(nombre as String) as Number {
        for (var i = 0; i < nombres.size(); i++) {
            if (nombres[i].equals(nombre)) {
                return i;
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
        return new Tesela(i, WatchUi.loadResource(rid) as Array);
    }
}
