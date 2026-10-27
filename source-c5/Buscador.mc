import Toybox.Lang;
import Toybox.Math;

// La calle más cercana dentro de una tesela del FORMATO 5. El algoritmo es el de source/Buscador.mc (y el de
// Ref.buscar() de tools/ref.py); cambia cómo se leen las tablas. Las calles lejanas se descartan por su caja
// gruesa (4 bytes) sin recorrerlas: K da dónde empiezan sus vértices.
module Buscador {
    const LEJOS = 1.0e9;

    // Rellena t.mejor (metros, con la penalización de su clase) y t.mejorRun; devuelve [s1, s2] o -1.
    function buscar(t as Tesela, x as Float, y as Float) as Array<Number> {
        var u = t.u;
        var uf = u.toFloat();
        var px = (x - t.ox) / uf;
        var py = (y - t.oy) / uf;
        var maxd = Callejero.MAXD.toFloat() / uf;
        var maxd2 = maxd * maxd;
        var mejor = t.mejor;
        var mejorRun = t.mejorRun;
        for (var i = 0; i < mejor.size(); i++) {
            mejor[i] = LEJOS;
            mejorRun[i] = -1;
        }
        var B = t.B;
        var oC = t.oC;
        var oCB = t.oCB;
        var oK = t.oK;
        var oR = t.oR;
        var oV = t.oV;
        var U = Callejero.CB_U;
        var pxi = px.toNumber();
        var pyi = py.toNumber();
        var M = Callejero.MAXD / u + 1;
        for (var calle = 0; calle < t.nc; calle++) {
            var q = oCB + 4 * calle;
            if (pxi + M < B[q] * U || pxi - M > B[q + 2] * U || pyi + M < B[q + 1] * U || pyi - M > B[q + 3] * U) {
                continue;
            }
            q = oC + 4 * calle;
            var r = B[q] | (B[q + 1] << 8);
            var fin = B[q + 4] | (B[q + 5] << 8);
            var o = Teselas.palabra(B, oK + 4 * calle);
            while (r < fin) {
                var a = oR + 4 * r;
                var h0 = B[a] | (B[a + 1] << 8) | (B[a + 2] << 16) | (B[a + 3] << 24);
                var h1 = B[a + 4] | (B[a + 5] << 8) | (B[a + 6] << 16) | (B[a + 7] << 24);
                var nv = (h1 >> 26) & 0x3F;
                var ro = r;
                if (nv == 0) {
                    nv = B[a + 8] | (B[a + 9] << 8) | (B[a + 10] << 16) | (B[a + 11] << 24);
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
                    var i = oV + 4 * (o >> 5);
                    var s = o & 31;
                    var v = (B[i] | (B[i + 1] << 8) | (B[i + 2] << 16) | (B[i + 3] << 24)) >> s;
                    if (s + k2 > 32) {
                        var v2 = B[i + 4] | (B[i + 5] << 8) | (B[i + 6] << 16) | (B[i + 7] << 24);
                        v = (v & ((1 << (32 - s)) - 1)) | (v2 << (32 - s));
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
                var d = dentro ? 0.0 : Math.sqrt(d2).toFloat() * uf;
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

    // [texto del número, distancia en m] del portal más cercano de la calle s a menos de PORTAL_R, o null.
    function portal(t as Tesela, s as Number, x as Float, y as Float) as Array or Null {
        var B = t.B;
        var q = t.oC + 4 * s;
        var j0 = B[q + 2] | (B[q + 3] << 8);
        var j1 = B[q + 6] | (B[q + 7] << 8);
        var pb = t.pb;
        var m = (1 << pb) - 1;
        var uf = t.u.toFloat();
        var px = (x - t.ox) / uf;
        var py = (y - t.oy) / uf;
        var rr = Callejero.PORTAL_R.toFloat() / uf;
        var r2 = rr * rr;
        var mejorJ = -1;
        var mejorD2 = r2;
        for (var j = j0; j < j1; j++) {
            var w = Teselas.palabra(B, t.oP + 4 * j);
            var dx = px - (w & m).toFloat();
            var dy = py - ((w >> pb) & m).toFloat();
            var d2 = dx * dx + dy * dy;
            if (mejorJ < 0 ? d2 <= r2 : d2 < mejorD2) {
                mejorD2 = d2;
                mejorJ = j;
            }
        }
        if (mejorJ < 0) {
            return null;
        }
        return [textoNumero(t, j0, mejorJ), Math.sqrt(mejorD2).toFloat() * uf];
    }

    // El número del portal j, cuya calle empieza en j0: suma de saltos desde el primero, o el último escape.
    function textoNumero(t as Tesela, j0 as Number, j as Number) as String {
        var d = 2 * t.pb;
        var esc = (1 << (29 - d)) - 1;
        var n = 0;
        var sc = 0;
        for (var i = j0; i <= j; i++) {
            var w = Teselas.palabra(t.B, t.oP + 4 * i);
            var salto = (w >> d) & esc;
            sc = (w >> 29) & 7;
            if (salto == esc && sc == 7) {
                var e = escape(t, i);
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
    function escape(t as Tesela, i as Number) as Number {
        var lo = 0;
        var hi = t.nE / 2 - 1;
        while (lo <= hi) {
            var mid = (lo + hi) / 2;
            var v = Teselas.palabra(t.B, t.oE + 8 * mid);
            if (v == i) {
                return Teselas.palabra(t.B, t.oE + 8 * mid + 4);
            } else if (v < i) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        throw new Lang.InvalidValueException("portal " + i + " sin escape");
    }
}
