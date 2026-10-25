import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:test)
function geoProyeccion(logger as Test.Logger) as Boolean {
    Activa.poner(Regiones.IDS[0]);
    var o = Geo.xy(Callejero.LAT_MIN, Callejero.LON_MIN);
    var p = Geo.xy(Callejero.LAT_MIN + 100.0d / Callejero.KY, Callejero.LON_MIN + 250.0d / Callejero.KX);
    var T = Callejero.TESELA;
    var ok = Sintetica.cerca(o[0], 0.0) && Sintetica.cerca(o[1], 0.0) && Sintetica.cerca(p[0], 250.0)
        && Sintetica.cerca(p[1], 100.0) && Geo.celda(-1.0, 5.0) == -1 && Geo.celda((T * Callejero.COLS + 1).toFloat(), 0.0) == -1;
    var rc = Callejero.CAJAS;
    if (rc == null) {
        return ok && Geo.celda(0.0, 0.0) == 0 && Geo.celda((T + 1).toFloat(), (2 * T + 1).toFloat()) == 2 * Callejero.COLS + 1;
    }
    // Teselas adaptativas: el centro y la esquina SO de cada caja caen en ella.
    var n = (WatchUi.loadResource(rc) as Array).size() / 2;
    for (var k = 0; k < n; k++) {
        var c = Teselas.caja(k);
        if (Geo.celda(((c[0] + c[2]) / 2).toFloat(), ((c[1] + c[3]) / 2).toFloat()) != k
                || Geo.celda(c[0].toFloat(), c[1].toFloat()) != k) {
            logger.error("caja " + k + " " + c);
            ok = false;
        }
    }
    return ok;
}

(:test)
function geoCubre(logger as Test.Logger) as Boolean {
    var t = Sintetica.tesela(["A"], [[0, 0, 0, [0, 0, 10, 0]]] as Array<Array>, [] as Array<Array>);
    var h = Callejero.BUF - Callejero.MAXD;
    var L = Sintetica.LADO;
    // La tesela 0 cubre su celda (0..LADO) más la holgura.
    return t.cubre(0.0, 0.0) && t.cubre((-h).toFloat(), 10.0) && !t.cubre((-h - 1).toFloat(), 10.0)
        && t.cubre((L + h).toFloat(), 10.0) && !t.cubre((L + h + 1).toFloat(), 10.0);
}
