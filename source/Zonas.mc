import Toybox.Lang;
import Toybox.WatchUi;

// Parroquia, lugar y barrio de un punto (formato en tools/build_callejero.py). Una zona cargada
// a la vez, aparte de la tesela de calles: la anterior se suelta antes de cargar la siguiente.
// Es el mismo algoritmo que Ref.zona() de tools/ref.py, que lo valida contra los límites reales.
module Zonas {
    var _idx as Number = -1;
    var _z as Array or Null = null;
    var _reg as Number = 0;     // región de la zona cargada (Callejero.ID)

    // [parroquia, lugar, barrio] (String o null cada uno) del punto en metros de región;
    // null si cae fuera de la rejilla de zonas. Donde el polígono es el barrio oficial (Madrid,
    // Callejero.ZBARRIO), va en barrio y no hay parroquia.
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
            _idx = -1;
            _reg = Callejero.ID;
        }
        if (x < 0.0 || y < 0.0) {
            return null;
        }
        var zc = (x / Callejero.ZONA).toNumber();
        var zf = (y / Callejero.ZONA).toNumber();
        if (zc >= Callejero.ZCOLS || zf >= Callejero.ZFILAS) {
            return null;
        }
        var i = zf * Callejero.ZCOLS + zc;
        if (i != _idx) {
            _z = null;   // soltar la anterior antes de cargar: nunca dos en memoria
            _idx = i;
            var rid = Callejero.ZIDX[i];
            if (rid != null) {
                var d = WatchUi.loadResource(rid) as Array;
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
        return buscar(z, x - (zc * Callejero.ZONA).toFloat(), y - (zf * Callejero.ZONA).toFloat());
    }

    // x, y en metros desde la esquina SO de la zona (los tests la llaman con zonas sintéticas).
    //   parroquia: la de la celda del raster;
    //   lugar: el poblado más cercano a menos de LUGAR_R; si no hay, el paraje más cercano;
    //   barrio: el más cercano a menos de BARRIO_R, si además está a menos de BARRIO_FRAC de
    //   la distancia al segundo (en la frontera entre dos no se adivina).
    function buscar(z as Array, x as Float, y as Float) as Array<String or Null> {
        var N = z[1] as Array<String>;
        var RA = z[2] as Array<Number>;
        var L = z[3] as Array<Number>;
        var LN = z[4] as Array<Number>;
        var rn = Callejero.RN;
        var c = (x / Callejero.RCEL).toNumber();
        var r = (y / Callejero.RCEL).toNumber();
        c = c >= rn ? rn - 1 : c;
        r = r >= rn ? rn - 1 : r;
        var k = r * rn + c;
        var v = (RA[k / 4] >> (8 * (k % 4))) & 0xFF;

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
        for (var j = 0; j < L.size(); j++) {
            var p = L[j];
            var dx = px - (p & 0x1FFF).toFloat();
            var dy = py - ((p >> 13) & 0x1FFF).toFloat();
            var d2 = dx * dx + dy * dy;
            var tipo = p >> 26;
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
        var lugar = jl >= 0 ? N[LN[jl]] : (jp >= 0 ? N[LN[jp]] : null);
        var f2 = Callejero.BARRIO_FRAC * Callejero.BARRIO_FRAC;
        var barrio = jb >= 0 && db <= (Callejero.BARRIO_R * Callejero.BARRIO_R).toFloat() && db <= f2 * db2
            ? N[LN[jb]] : null;
        return [v > 0 ? N[v - 1] : null, lugar, barrio] as Array<String or Null>;
    }
}
