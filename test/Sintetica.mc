import Toybox.Lang;

// Teselas inventadas para los tests: se empaquetan igual que las genera build_callejero.py.
// Coordenadas en metros locales de la tesela 0 (su origen está en (−BUF, −BUF) de región).
(:test)
module Sintetica {

    // tiradas: [calle, clase, area, [x0, y0, x1, y1, …]] y opcionalmente [A, B] (índices de las
    // calles que cruzan, -1 = ninguna); portales: [x, y, calle, número, sufijo]
    function tesela(nombres as Array<String>, tiradas as Array<Array>, portales as Array<Array>) as Tesela {
        var R = [] as Array<Number>;
        var V = [] as Array<Number>;
        for (var i = 0; i < tiradas.size(); i++) {
            var t = tiradas[i];
            var c = t[3] as Array<Number>;
            var n = c.size() / 2;
            var x0 = 4095;
            var y0 = 4095;
            var x1 = 0;
            var y1 = 0;
            for (var j = 0; j < n; j++) {
                var x = c[2 * j];
                var y = c[2 * j + 1];
                x0 = x < x0 ? x : x0;
                y0 = y < y0 ? y : y0;
                x1 = x > x1 ? x : x1;
                y1 = y > y1 ? y : y1;
                V.add(x | y << 12);
            }
            R.add(n | (t[0] as Number) << 12 | (t[1] as Number) << 22 | (t[2] as Number) << 24);
            R.add(x0 | y0 << 12);
            R.add(x1 | y1 << 12);
            var tr = t.size() > 4 ? t[4] as Array<Number> : [-1, -1] as Array<Number>;
            R.add((tr[0] + 1) | (tr[1] + 1) << 12);
        }
        var P = [] as Array<Number>;
        var H = [] as Array<Number>;
        for (var i = 0; i < portales.size(); i++) {
            var p = portales[i];
            P.add((p[0] as Number) | (p[1] as Number) << 12);
            H.add((p[3] as Number) | (p[4] as Number) << 12 | (p[2] as Number) << 21);
        }
        return new Tesela(0, [Callejero.FORMATO, nombres, R, V, P, H]);
    }

    function cerca(a as Float, b as Float) as Boolean {
        var d = a - b;
        return d < 0.01 && d > -0.01;
    }

    // De metros locales de la tesela 0 a metros de región.
    function x(l as Number or Float) as Float {
        return l.toFloat() - Callejero.BUF;
    }
}
