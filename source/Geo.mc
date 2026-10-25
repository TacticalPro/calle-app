import Toybox.Lang;
import Toybox.WatchUi;

// Proyección equirectangular en metros desde la esquina SO de la región.
// Es la misma fórmula que tools/build_callejero.py, con sus constantes generadas.
module Geo {

    // [x, y] en metros de región.
    function xy(lat as Double, lon as Double) as Array<Float> {
        return [((lon - Callejero.LON_MIN) * Callejero.KX).toFloat(),
                ((lat - Callejero.LAT_MIN) * Callejero.KY).toFloat()] as Array<Float>;
    }

    // Índice de tesela, o -1 fuera de la región. En la rejilla fija, fila·COLS + columna. Con teselas
    // adaptativas (Callejero.CAJAS, variante c), la caja que contiene el punto, o el número de cajas si
    // ninguna (zona sin calles: Callejero.IDX lleva ahí un null).
    function celda(x as Float, y as Float) as Number {
        if (x < 0.0 || y < 0.0) {
            return -1;
        }
        var c = (x / Callejero.TESELA).toNumber();
        var f = (y / Callejero.TESELA).toNumber();
        if (c >= Callejero.COLS || f >= Callejero.FILAS) {
            return -1;
        }
        var rc = Callejero.CAJAS;
        if (rc == null) {
            return f * Callejero.COLS + c;
        }
        // Las cajas se cargan solo para esto (se llama al cambiar de tesela) y se sueltan al salir.
        // En unidades de TESELA: los cortes caen en múltiplos de ella.
        var cajas = WatchUi.loadResource(rc) as Array<Number>;
        var n = cajas.size() / 2;
        for (var k = 0; k < n; k++) {
            var a = cajas[2 * k];
            var b = cajas[2 * k + 1];
            if (c >= (a & 0xFFFF) && f >= ((a >> 16) & 0xFFFF) && c < (b & 0xFFFF) && f < ((b >> 16) & 0xFFFF)) {
                return k;
            }
        }
        return n;
    }
}
