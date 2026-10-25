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
    function buscar(t as Tesela, x as Float, y as Float) as Array<Number> {
        var px = x - t.ox;
        var py = y - t.oy;
        var maxd2 = (Callejero.MAXD * Callejero.MAXD).toFloat();
        var mejor = t.mejor;
        var mejorRun = t.mejorRun;
        for (var i = 0; i < mejor.size(); i++) {
            mejor[i] = LEJOS;
            mejorRun[i] = -1;
        }
        var R = t.R;
        var V = t.V;
        var nr = R.size() / 4;
        var k = 0;
        for (var r = 0; r < nr; r++) {
            var h = R[4 * r];
            var n = h & 0xFFF;
            var bmin = R[4 * r + 1];
            var bmax = R[4 * r + 2];
            var bx0 = (bmin & 0xFFF).toFloat();
            var by0 = (bmin >> 12).toFloat();
            var bx1 = (bmax & 0xFFF).toFloat();
            var by1 = (bmax >> 12).toFloat();
            var dx = px < bx0 ? bx0 - px : (px > bx1 ? px - bx1 : 0.0);
            var dy = py < by0 ? by0 - py : (py > by1 ? py - by1 : 0.0);
            if (dx * dx + dy * dy > maxd2) {
                k += n;
                continue;
            }
            var area = ((h >> 24) & 1) == 1;
            var dentro = false;
            var v = V[k];
            var ax = (v & 0xFFF).toFloat();
            var ay = (v >> 12).toFloat();
            var d2 = (px - ax) * (px - ax) + (py - ay) * (py - ay);
            for (var j = 1; j < n; j++) {
                v = V[k + j];
                var bx = (v & 0xFFF).toFloat();
                var by = (v >> 12).toFloat();
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
            d += Callejero.PEN[(h >> 22) & 3];
            var calle = (h >> 12) & 0x3FF;
            if (d < mejor[calle]) {
                mejor[calle] = d;
                mejorRun[calle] = r;
            }
            k += n;
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
    // ninguno a menos de PORTAL_R. Los portales están ordenados por calle (que va en H, bits 21-30):
    // búsqueda binaria del primero.
    function portal(t as Tesela, s as Number, x as Float, y as Float) as Array or Null {
        var P = t.P;
        var H = t.H;
        var lo = 0;
        var hi = P.size();
        while (lo < hi) {
            var mid = (lo + hi) / 2;
            if (((H[mid] >> 21) & 0x3FF) < s) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        var px = x - t.ox;
        var py = y - t.oy;
        var r2 = (Callejero.PORTAL_R * Callejero.PORTAL_R).toFloat();
        var mejorJ = -1;
        var mejorD2 = r2;
        for (var j = lo; j < P.size() && ((H[j] >> 21) & 0x3FF) == s; j++) {
            var dx = px - (P[j] & 0xFFF).toFloat();
            var dy = py - ((P[j] >> 12) & 0xFFF).toFloat();
            var d2 = dx * dx + dy * dy;
            if (mejorJ < 0 ? d2 <= r2 : d2 < mejorD2) {
                mejorD2 = d2;
                mejorJ = j;
            }
        }
        if (mejorJ < 0) {
            return null;
        }
        return [textoNumero(t.H[mejorJ]), Math.sqrt(mejorD2).toFloat()];
    }

    function textoNumero(h as Number) as String {
        var n = h & 0xFFF;
        var suf = Callejero.SUF[(h >> 12) & 0x1FF];
        return n == 0 ? suf : n.toString() + suf;
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
        r.calle1 = t.nombres[a];
        r.d1 = t.mejor[a];
        var p = portal(t, a, x, y);
        r.num1 = p != null ? p[0] as String : null;
        r.dn1 = p != null ? p[1] as Float : 0.0;
        var tr = t.tramo(a);
        r.tramoA = tr[0];
        r.tramoB = tr[1];
        if (b >= 0 && t.mejor[b] <= Callejero.MAXD) {
            r.calle2 = t.nombres[b];
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
