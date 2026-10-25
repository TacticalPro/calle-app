import Toybox.Lang;
import Toybox.Test;

// Zonas sintéticas: raster, poblado antes que paraje, y barrio solo si es claramente el más cercano.
(:test)
function zonasReglas(logger as Test.Logger) as Boolean {
    var M = Callejero.ZMARGEN;
    var rn = Callejero.RN;
    // Parroquia 1 en la mitad oeste del raster, 2 en la este.
    var vals = [] as Array<Number>;
    for (var k = 0; k < rn * rn; k++) {
        vals.add((k % rn) < rn / 2 ? 1 : 2);
    }
    var RA = [] as Array<Number>;
    for (var k = 0; k < vals.size(); k += 4) {
        RA.add(vals[k] | vals[k + 1] << 8 | vals[k + 2] << 16 | vals[k + 3] << 24);
    }
    var N = ["Oeste", "Este", "Aldea", "Monte", "Barrio A", "Barrio B"] as Array<String>;
    var L = [
        (M + 200) | (M + 200) << 13 | 1 << 26,     // poblado
        (M + 120) | (M + 120) << 13 | 4 << 26,     // paraje, más cerca
        (M + 1000) | (M + 1000) << 13 | 2 << 26,   // barrio A
        (M + 1500) | (M + 1000) << 13 | 2 << 26    // barrio B, a 500 m de A
    ] as Array<Number>;
    var LN = [2, 3, 4, 5] as Array<Number>;
    var z = [Callejero.FORMATO, N, RA, L, LN] as Array;
    var a = Zonas.buscar(z, 100.0, 100.0);      // oeste; el paraje está más cerca, pero manda el poblado
    var b = Zonas.buscar(z, (Callejero.ZONA - 10).toFloat(), 100.0);     // este (zona de 2 km, o 4 km en el 6X)
    var c = Zonas.buscar(z, 1050.0, 1000.0);    // claramente en A
    var d = Zonas.buscar(z, 1250.0, 1000.0);    // a mitad de A y B: sin barrio
    var sinPoblado = [Callejero.FORMATO, N, RA, [L[1]] as Array<Number>, [3] as Array<Number>] as Array;
    var e = Zonas.buscar(sinPoblado, 100.0, 100.0);
    var ok = "Oeste".equals(a[0]) && "Aldea".equals(a[1]) && a[2] == null && "Este".equals(b[0])
        && "Barrio A".equals(c[2]) && d[2] == null && "Monte".equals(e[1]);
    if (!ok) {
        logger.error("a " + a + " b " + b + " c " + c + " d " + d + " e " + e);
    }
    return ok;
}
