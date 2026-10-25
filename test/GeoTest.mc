import Toybox.Lang;
import Toybox.Test;

(:test)
function geoProyeccion(logger as Test.Logger) as Boolean {
    Activa.poner(Regiones.IDS[0]);
    var o = Geo.xy(Callejero.LAT_MIN, Callejero.LON_MIN);
    var p = Geo.xy(Callejero.LAT_MIN + 100.0d / Callejero.KY, Callejero.LON_MIN + 250.0d / Callejero.KX);
    var T = Callejero.TESELA;
    return Sintetica.cerca(o[0], 0.0) && Sintetica.cerca(o[1], 0.0) && Sintetica.cerca(p[0], 250.0) && Sintetica.cerca(p[1], 100.0)
        && Geo.celda(0.0, 0.0) == 0 && Geo.celda(-1.0, 5.0) == -1
        && Geo.celda((T * Callejero.COLS + 1).toFloat(), 0.0) == -1
        && Geo.celda((T + 1).toFloat(), (2 * T + 1).toFloat()) == 2 * Callejero.COLS + 1;
}

(:test)
function geoCubre(logger as Test.Logger) as Boolean {
    var t = Sintetica.tesela(["A"], [[0, 0, 0, [0, 0, 10, 0]]] as Array<Array>, [] as Array<Array>);
    var h = Callejero.BUF - Callejero.MAXD;
    // La tesela 0 cubre su celda (0..TESELA) más la holgura.
    return t.cubre(0.0, 0.0) && t.cubre((-h).toFloat(), 10.0) && !t.cubre((-h - 1).toFloat(), 10.0)
        && t.cubre((Callejero.TESELA + h).toFloat(), 10.0) && !t.cubre((Callejero.TESELA + h + 1).toFloat(), 10.0);
}
