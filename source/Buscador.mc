import Toybox.Lang;
import Toybox.Math;

enum Estado {
    EST_BUSCANDO,   // aún sin posición
    EST_OK,
    EST_LEJOS,      // ninguna calle a menos de MAXD
    EST_FUERA       // fuera de la región del callejero
}

// Lo que sale de una búsqueda, sin histéresis ni ambigüedad (eso es del Localizador).
class Resultado {
    var estado as Estado = EST_LEJOS;
    var calle1 as String or Null = null;
    var d1 as Float = 0.0;
    var num1 as String or Null = null;
    var dn1 as Float = 0.0;
    var calle2 as String or Null = null;
    var d2 as Float = 0.0;
    var num2 as String or Null = null;
    var dn2 as Float = 0.0;
    var tramoA as String or Null = null;   // calles que cruzan en los extremos del trozo de calle1
    var tramoB as String or Null = null;

    function initialize() {
    }
}

// La calle más cercana dentro de una tesela. Todo en Float y metros locales de la tesela.
// Es el mismo algoritmo que Ref.buscar() de tools/ref.py, que lo valida por fuerza bruta.
module Buscador {
    const LEJOS = 1.0e9;

    // Rellena t.mejor (distancia por calle, con la penalización de su clase) y t.mejorRun (su
    // tirada más cercana, la primera si empatan) y devuelve [s1, s2]: las dos calles más cercanas, o -1.
    // Las tiradas van ordenadas por calle (t.C marca dónde empieza cada una) y sus vértices, desde el
    // segundo, en el flujo de bits t.V: hay que avanzar por él aunque la tirada se descarte.
    function buscar(t as Tesela, x as Float, y as Float) as Array<Number> {
        var px = x - t.ox;
        var py = y - t.oy;
        var maxd = Callejero.MAXD.toFloat();
        var maxd2 = maxd * maxd;
        var mejor = t.mejor;
        var mejorRun = t.mejorRun;
        for (var i = 0; i < mejor.size(); i++) {
            mejor[i] = LEJOS;
            mejorRun[i] = -1;
        }
        var R = t.R;
        var V = t.V;
        var C = t.C;
        var CB = t.CB;
        var U = Callejero.CB_U;
        var pxi = px.toNumber();
        var pyi = py.toNumber();
        var M = Callejero.MAXD + 1;
        var o = 0;                  // bit de V
        var r = 0;
        for (var calle = 0; calle < t.nc; calle++) {
            var fin = C[calle + 1] & 0xFFFF;    // offset en R de la primera tirada de la calle siguiente
            var b = CB[calle];
            if (pxi + M < (b & 0xFF) * U || pxi - M > ((b >> 16) & 0xFF) * U
                    || pyi + M < ((b >> 8) & 0xFF) * U || pyi - M > ((b >> 24) & 0xFF) * U) {
                // Calle lejana: solo se avanza el flujo de vértices hasta la siguiente.
                while (r < fin) {
                    var g = R[r + 1];
                    var n = (g >> 26) & 0x3F;
                    if (n == 0) {
                        n = R[r + 2];
                        r += 3;
                    } else {
                        r += 2;
                    }
                    o += (n - 1) * 2 * (g & 0xF);
                }
                continue;
            }
            while (r < fin) {
                var h0 = R[r];
                var h1 = R[r + 1];
                var nv = (h1 >> 26) & 0x3F;
                var ro = r;
                if (nv == 0) {
                    nv = R[r + 2];
                    r += 3;
                } else {
                    r += 2;
                }
                var w = h1 & 0xF;
                var ax = (h0 & 0x1FFF).toFloat();
                var ay = ((h0 >> 13) & 0x1FFF).toFloat();
                var ext = (h0 >> 26) & 0x1F;
                if (ext != Callejero.EXT_SIN) {
                    var e = (ext * Callejero.EXT_U).toFloat();
                    var dx = (px > ax ? px - ax : ax - px) - e;
                    var dy = (py > ay ? py - ay : ay - py) - e;
                    dx = dx > 0.0 ? dx : 0.0;
                    dy = dy > 0.0 ? dy : 0.0;
                    if (dx * dx + dy * dy > maxd2) {
                        o += (nv - 1) * 2 * w;
                        continue;
                    }
                }
                var area = ((h0 >> 31) & 1) == 1;
                var dentro = false;
                var k2 = 2 * w;
                var mk = (1 << k2) - 1;
                var mw = (1 << w) - 1;
                var medio = 1 << (w - 1);
                var d2 = (px - ax) * (px - ax) + (py - ay) * (py - ay);
                for (var j = 1; j < nv; j++) {
                    // 2w bits del flujo desde el bit o: dx en los w bajos, dy en los w altos.
                    var i = o >> 5;
                    var s = o & 31;
                    var v = V[i] >> s;
                    if (s + k2 > 32) {
                        v = (v & ((1 << (32 - s)) - 1)) | (V[i + 1] << (32 - s));
                    }
                    v = v & mk;
                    o += k2;
                    var ddx = v & mw;
                    var ddy = (v >> w) & mw;
                    var bx = ax + (ddx >= medio ? ddx - (mw + 1) : ddx).toFloat();
                    var by = ay + (ddy >= medio ? ddy - (mw + 1) : ddy).toFloat();
                    var sx = bx - ax;
                    var sy = by - ay;
                    var l2 = sx * sx + sy * sy;
                    var tt = 0.0;
                    if (l2 > 0.0) {
                        tt = ((px - ax) * sx + (py - ay) * sy) / l2;
                        tt = tt < 0.0 ? 0.0 : (tt > 1.0 ? 1.0 : tt);
                    }
                    var ex = px - (ax + tt * sx);
                    var ey = py - (ay + tt * sy);
                    var e2 = ex * ex + ey * ey;
                    if (e2 < d2) {
                        d2 = e2;
                    }
                    if (area && ((ay > py) != (by > py)) && px < sx * (py - ay) / sy + ax) {
                        dentro = !dentro;
                    }
                    ax = bx;
                    ay = by;
                }
                var d = dentro ? 0.0 : Math.sqrt(d2).toFloat();
                d += Callejero.PEN[(h1 >> 4) & 3];
                if (d < mejor[calle]) {
                    mejor[calle] = d;
                    mejorRun[calle] = ro;
                }
            }
        }
        var s1 = -1;
        var s2 = -1;
        for (var i = 0; i < mejor.size(); i++) {
            if (s1 < 0 || mejor[i] < mejor[s1]) {
                s2 = s1;
                s1 = i;
            } else if (s2 < 0 || mejor[i] < mejor[s2]) {
                s2 = i;
            }
        }
        return [s1, s2] as Array<Number>;
    }

    // [texto del número, distancia] del portal más cercano de la calle s, o null si no hay
    // ninguno a menos de PORTAL_R. Los portales de cada calle van seguidos (t.C dice dónde).
    function portal(t as Tesela, s as Number, x as Float, y as Float) as Array or Null {
        var P = t.P;
        var j0 = (t.C[s] >> 16) & 0xFFFF;
        var j1 = (t.C[s + 1] >> 16) & 0xFFFF;
        var pb = t.pb;
        var m = (1 << pb) - 1;
        var px = x - t.ox;
        var py = y - t.oy;
        var r2 = (Callejero.PORTAL_R * Callejero.PORTAL_R).toFloat();
        var mejorJ = -1;
        var mejorD2 = r2;
        for (var j = j0; j < j1; j++) {
            var dx = px - (P[j] & m).toFloat();
            var dy = py - ((P[j] >> pb) & m).toFloat();
            var d2 = dx * dx + dy * dy;
            if (mejorJ < 0 ? d2 <= r2 : d2 < mejorD2) {
                mejorD2 = d2;
                mejorJ = j;
            }
        }
        if (mejorJ < 0) {
            return null;
        }
        return [textoNumero(t, j0, mejorJ), Math.sqrt(mejorD2).toFloat()];
    }

    // El número del portal j, cuya calle empieza en j0: suma de saltos desde el primero, o el último escape.
    function textoNumero(t as Tesela, j0 as Number, j as Number) as String {
        var P = t.P;
        var d = 2 * t.pb;
        var esc = (1 << (29 - d)) - 1;     // el salto ocupa los bits de 2·pb a 28
        var n = 0;
        var sc = 0;
        for (var i = j0; i <= j; i++) {
            var salto = (P[i] >> d) & esc;
            sc = (P[i] >> 29) & 7;
            if (salto == esc && sc == 7) {
                var e = escape(t.E, i);
                n = e & 0xFFF;
                sc = (e >> 12) & 0x3FF;
            } else {
                n += salto;
            }
        }
        var suf = sc > 0 ? t.nombre(t.nc + sc - 1) : "";
        return n == 0 ? suf : n.toString() + suf;
    }

    // Número y sufijo del portal i en la tabla de escapes (pares índice, valor; ordenada por índice).
    function escape(E as Array<Number>, i as Number) as Number {
        var lo = 0;
        var hi = E.size() / 2 - 1;
        while (lo <= hi) {
            var mid = (lo + hi) / 2;
            var v = E[2 * mid];
            if (v == i) {
                return E[2 * mid + 1];
            } else if (v < i) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        throw new Lang.InvalidValueException("portal " + i + " sin escape");
    }

    // Búsqueda completa sin estado: las dos calles más cercanas y sus portales.
    function consultar(t as Tesela, x as Float, y as Float) as Resultado {
        var r = new Resultado();
        var s = buscar(t, x, y);
        if (s[0] < 0 || t.mejor[s[0]] > Callejero.MAXD) {
            r.estado = EST_LEJOS;
            return r;
        }
        r.estado = EST_OK;
        rellenar(r, t, s[0], s[1], x, y);
        return r;
    }

    // Pone en r la calle a (y b, si está a menos de MAXD) con sus portales.
    function rellenar(r as Resultado, t as Tesela, a as Number, b as Number, x as Float, y as Float) as Void {
        r.calle1 = t.nombre(a);
        r.d1 = t.mejor[a];
        var p = portal(t, a, x, y);
        r.num1 = p != null ? p[0] as String : null;
        r.dn1 = p != null ? p[1] as Float : 0.0;
        var tr = t.tramo(a);
        r.tramoA = tr[0];
        r.tramoB = tr[1];
        if (b >= 0 && t.mejor[b] <= Callejero.MAXD) {
            r.calle2 = t.nombre(b);
            r.d2 = t.mejor[b];
            p = portal(t, b, x, y);
            r.num2 = p != null ? p[0] as String : null;
            r.dn2 = p != null ? p[1] as Float : 0.0;
        } else {
            r.calle2 = null;
            r.num2 = null;
        }
    }
}
