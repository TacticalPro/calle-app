import Toybox.Lang;

// Teselas inventadas para los tests: se empaquetan igual que las genera build_callejero.py (FORMATO 4).
// Coordenadas en metros locales de la tesela 0 (su origen está en (−BUF, −BUF) de región).
(:test)
module Sintetica {
    const LADO = 500;   // m: la tesela sintética cubre (0, 0)–(LADO, LADO) de región

    // tiradas: [calle, clase, area, [x0, y0, x1, y1, …]] y opcionalmente [A, B] (índices de las
    // calles que cruzan, -1 = ninguna); portales: [x, y, calle, número, sufijo ("" o 0 = ninguno)].
    // La extensión de cada tirada se calcula como en el generador; con más de 30·EXT_U m, va sin cota (EXT_SIN).
    function tesela(nombres as Array<String>, tiradas as Array<Array>, portales as Array<Array>) as Tesela {
        var nc = nombres.size();
        var sufs = [] as Array<String>;
        for (var i = 0; i < portales.size(); i++) {
            var s = portales[i][4];
            if (s instanceof String && !(s as String).equals("") && sufs.indexOf(s) < 0) {
                sufs.add(s as String);
            }
        }
        var R = [] as Array<Number>;
        var V = [0] as Array<Number>;
        var bit = [0] as Array<Number>;
        var P = [] as Array<Number>;
        var E = [] as Array<Number>;
        var C = [] as Array<Number>;
        var CB = [] as Array<Number>;
        var U = Callejero.CB_U;
        for (var k = 0; k < nc; k++) {
            C.add(R.size() | P.size() << 16);
            // Caja gruesa de la calle, como el generador (hacia fuera; sin tiradas, vacía).
            var bx0 = 8191;
            var by0 = 8191;
            var bx1 = -1;
            var by1 = -1;
            for (var i = 0; i < tiradas.size(); i++) {
                var t = tiradas[i];
                if (t[0] != k) {
                    continue;
                }
                var c = t[3] as Array<Number>;
                var n = c.size() / 2;
                for (var j = 0; j < n; j++) {
                    bx0 = c[2 * j] < bx0 ? c[2 * j] : bx0;
                    by0 = c[2 * j + 1] < by0 ? c[2 * j + 1] : by0;
                    bx1 = c[2 * j] > bx1 ? c[2 * j] : bx1;
                    by1 = c[2 * j + 1] > by1 ? c[2 * j + 1] : by1;
                }
                var w = 1;
                var ext = 0;
                for (var j = 1; j < n; j++) {
                    var ex = c[2 * j] - c[0];
                    var ey = c[2 * j + 1] - c[1];
                    ex = ex < 0 ? -ex : ex;
                    ey = ey < 0 ? -ey : ey;
                    ext = ex > ext ? ex : ext;
                    ext = ey > ext ? ey : ext;
                    w = ancho(w, c[2 * j] - c[2 * j - 2]);
                    w = ancho(w, c[2 * j + 1] - c[2 * j - 1]);
                }
                var tr = t.size() > 4 ? t[4] as Array<Number> : [-1, -1] as Array<Number>;
                ext = (ext + Callejero.EXT_U - 1) / Callejero.EXT_U;
                ext = ext < Callejero.EXT_SIN ? ext : Callejero.EXT_SIN;
                R.add(c[0] | c[1] << 13 | ext << 26 | (t[2] as Number) << 31);
                R.add(w | (t[1] as Number) << 4 | (tr[0] + 1) << 6 | (tr[1] + 1) << 16 | (n <= 63 ? n : 0) << 26);
                if (n > 63) {
                    R.add(n);
                }
                var m = (1 << w) - 1;
                for (var j = 1; j < n; j++) {
                    poner(V, bit, (c[2 * j] - c[2 * j - 2]) & m, w);
                    poner(V, bit, (c[2 * j + 1] - c[2 * j - 1]) & m, w);
                }
            }
            CB.add(bx1 < 0 ? 0xFF | 0xFF << 8
                : bx0 / U | (by0 / U) << 8 | ((bx1 + U - 1) / U) << 16 | ((by1 + U - 1) / U) << 24);
            // Portales de la calle k por número.
            var suyos = [] as Array<Array>;
            for (var i = 0; i < portales.size(); i++) {
                if (portales[i][2] == k) {
                    var p = portales[i];
                    var pos = 0;
                    while (pos < suyos.size() && (suyos[pos][3] as Number) <= (p[3] as Number)) {
                        pos++;
                    }
                    suyos = suyos.slice(0, pos).addAll([p]).addAll(suyos.slice(pos, null));
                }
            }
            var prev = 0;
            for (var i = 0; i < suyos.size(); i++) {
                var p = suyos[i];
                var num = p[3] as Number;
                var s = p[4];
                var sc = s instanceof String ? sufs.indexOf(s) + 1 : 0;
                var salto = num - prev;
                if (salto >= 0 && salto < 31 && sc < 7) {     // pb = 12: salto de 5 bits
                    P.add((p[0] as Number) | (p[1] as Number) << 12 | salto << 24 | sc << 29);
                } else {
                    E.add(P.size());
                    E.add(num | sc << 12);
                    P.add((p[0] as Number) | (p[1] as Number) << 12 | 31 << 24 | 7 << 29);
                }
                prev = num;
            }
        }
        C.add(R.size() | P.size() << 16);
        var todos = nombres.slice(0, null).addAll(sufs);
        var S = "\n";
        var offs = [] as Array<Number>;
        for (var i = 0; i < todos.size(); i++) {
            offs.add(S.length());
            S += todos[i] + "\n";
        }
        offs.add(S.length());
        if (offs.size() % 2 == 1) {
            offs.add(0);
        }
        var O = [] as Array<Number>;
        for (var i = 0; i < offs.size(); i += 2) {
            O.add(offs[i] | offs[i + 1] << 16);
        }
        return new Tesela(0, [Callejero.FORMATO, nc, 12, S, O, C, CB, R, V, P, E], [0, 0, LADO, LADO] as Array<Number>);
    }

    // Bits para guardar d en complemento a dos (al menos w).
    function ancho(w as Number, d as Number) as Number {
        while (d < -(1 << (w - 1)) || d >= 1 << (w - 1)) {
            w++;
        }
        return w;
    }

    // Añade los k bits bajos de v al flujo V (bit[0]: bits escritos).
    function poner(V as Array<Number>, bit as Array<Number>, v as Number, k as Number) as Void {
        while (k > 0) {
            var i = bit[0] >> 5;
            var s = bit[0] & 31;
            if (i == V.size()) {
                V.add(0);
            }
            var cabe = 32 - s < k ? 32 - s : k;
            V[i] = V[i] | ((v & ((1 << cabe) - 1)) << s);
            v = v >> cabe;
            k -= cabe;
            bit[0] = bit[0] + cabe;
        }
    }

    function cerca(a as Float, b as Float) as Boolean {
        var d = a - b;
        return d < 0.01 && d > -0.01;
    }

    // De metros locales de la tesela 0 a metros de región.
    function x(l as Number or Float) as Float {
        return l.toFloat() - Callejero.BUF;
    }

    // Zona con la parroquia 1 (N[0]) en la mitad oeste del raster y la 2 (N[1]) en la este, empaquetada como
    // la escribe build_callejero.py: [FORMATO, S, O, F, RL, L, LN].
    function zona(N as Array<String>, L as Array<Number>, LN as Array<Number>) as Array {
        var rn = Callejero.RN;
        var F = [] as Array<Number>;
        var RL = [] as Array<Number>;
        for (var r = 0; r < rn; r++) {
            F.add(RL.size());
            RL.add(1 | (rn / 2) << 8);
            RL.add(2 | (rn - rn / 2) << 8);
        }
        F.add(RL.size());
        var c = cadena(N);
        return [Callejero.FORMATO, c[0], c[1], pares(F), pares(RL), L, pares(LN)] as Array;
    }

    function pares(vs as Array<Number>) as Array<Number> {
        var out = [] as Array<Number>;
        for (var i = 0; i < vs.size(); i += 2) {
            out.add(vs[i] | (i + 1 < vs.size() ? vs[i + 1] : 0) << 16);
        }
        return out;
    }

    // Hospitales y comisarías como el recurso <prefijo>poi: [FORMATO, SN, ON, SD, OD, XY, T].
    function puntos(N as Array<String>, D as Array<String>, X as Array<Number>, Y as Array<Number>,
            T as Array<Number>) as Array {
        var XY = [] as Array<Number>;
        var TT = [] as Array<Number>;
        for (var i = 0; i < X.size(); i++) {
            XY.add(X[i] | Y[i] << 16);
            if (i % 4 == 0) {
                TT.add(0);
            }
            TT[i / 4] = TT[i / 4] | T[i] << ((i % 4) * 8);
        }
        var n = cadena(N);
        var d = cadena(D);
        return [Callejero.FORMATO, n[0], n[1], d[0], d[1], XY, TT] as Array;
    }

    // [S, O] de unos nombres, como cadena_nombres() del generador.
    function cadena(N as Array<String>) as Array {
        var S = "\n";
        var offs = [] as Array<Number>;
        for (var i = 0; i < N.size(); i++) {
            offs.add(S.length());
            S += N[i] + "\n";
        }
        offs.add(S.length());
        return [S, pares(offs)] as Array;
    }
}
