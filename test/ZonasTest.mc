import Toybox.Lang;
import Toybox.Test;

// Zonas sintéticas: raster, poblado antes que paraje, y barrio solo si es claramente el más cercano.
(:test)
function zonasReglas(logger as Test.Logger) as Boolean {
    var M = Callejero.ZMARGEN;
    var rn = Callejero.RN;
    var N = ["Oeste", "Este", "Aldea", "Monte", "Barrio A", "Barrio B"] as Array<String>;
    // Ordenados por x, como los escribe build_callejero.py (Zonas.buscar busca la franja por bisección).
    var L = [
        (M + 120) | (M + 120) << 14 | 4 << 28,     // paraje, más cerca
        (M + 200) | (M + 200) << 14 | 1 << 28,     // poblado
        (M + 1000) | (M + 1000) << 14 | 2 << 28,   // barrio A
        (M + 1500) | (M + 1000) << 14 | 2 << 28    // barrio B, a 500 m de A
    ] as Array<Number>;
    var z = Sintetica.zona(N, L, [3, 2, 4, 5] as Array<Number>);
    var a = Zonas.buscar(z, 100.0, 100.0);      // oeste; el paraje está más cerca, pero manda el poblado
    var b = Zonas.buscar(z, (Callejero.ZONA - 10).toFloat(), 100.0);     // este
    var c = Zonas.buscar(z, 1050.0, 1000.0);    // claramente en A
    var d = Zonas.buscar(z, 1250.0, 1000.0);    // a mitad de A y B: sin barrio
    var e = Zonas.buscar(Sintetica.zona(N, [L[0]] as Array<Number>, [3] as Array<Number>), 100.0, 100.0);
    // Última columna de la mitad oeste y primera de la este (el tramo se elige por columna).
    var f = Zonas.buscar(z, ((rn / 2) * Callejero.RCEL - 1).toFloat(), (Callejero.ZONA - 1).toFloat());
    var g = Zonas.buscar(z, ((rn / 2) * Callejero.RCEL + 1).toFloat(), (Callejero.ZONA - 1).toFloat());
    var ok = "Oeste".equals(a[0]) && "Aldea".equals(a[1]) && a[2] == null && "Este".equals(b[0])
        && "Barrio A".equals(c[2]) && d[2] == null && "Monte".equals(e[1]) && "Oeste".equals(f[0]) && "Este".equals(g[0]);
    if (!ok) {
        logger.error("a " + a + " b " + b + " c " + c + " d " + d + " e " + e + " f " + f + " g " + g);
    }
    return ok;
}
