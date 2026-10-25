import Toybox.Lang;

// Proyección equirectangular en metros desde la esquina SO de la región.
// Es la misma fórmula que tools/build_callejero.py, con sus constantes generadas.
module Geo {

    // [x, y] en metros de región.
    function xy(lat as Double, lon as Double) as Array<Float> {
        return [((lon - Callejero.LON_MIN) * Callejero.KX).toFloat(),
                ((lat - Callejero.LAT_MIN) * Callejero.KY).toFloat()] as Array<Float>;
    }

    // Índice de celda (fila·COLS + columna), o -1 fuera de la región.
    function celda(x as Float, y as Float) as Number {
        if (x < 0.0 || y < 0.0) {
            return -1;
        }
        var c = (x / Callejero.TESELA).toNumber();
        var f = (y / Callejero.TESELA).toNumber();
        if (c >= Callejero.COLS || f >= Callejero.FILAS) {
            return -1;
        }
        return f * Callejero.COLS + c;
    }
}
