import Toybox.Lang;
import Toybox.Position;
import Toybox.Test;
import Toybox.Time;

// Localizador: histéresis, ambigüedad y cruce con dos calles paralelas a 10 m y una perpendicular.
(:test)
function histeresisYAmbiguedad(logger as Test.Logger) as Boolean {
    var t = Sintetica.tesela(["A", "B", "C"], [
        [0, 0, 0, [0, 100, 600, 100]],
        [1, 0, 0, [0, 110, 600, 110]],
        [2, 0, 0, [300, 0, 300, 600]]
    ] as Array<Array>, [] as Array<Array>);
    var m = new Modelo();
    m.radio = 8;   // GPS GOOD
    var loc = new Localizador(m);
    loc.calcularEn(t, Sintetica.x(100), Sintetica.x(102));       // A a 2, B a 8: margen 4 m, no es ambiguo
    var paso1 = "A".equals(m.calle1) && m.calle2 == null;
    loc.calcularEn(t, Sintetica.x(100), Sintetica.x(106));       // A a 6, B a 4: se queda A, pero ambiguo
    var paso2 = "A".equals(m.calle1) && "B".equals(m.calle2) && !m.cruce;
    loc.calcularEn(t, Sintetica.x(100), Sintetica.x(109.5));     // B a 0,5: cambia a B
    var paso3 = "B".equals(m.calle1) && m.calle2 == null;
    m.limpiar();
    loc.calcularEn(t, Sintetica.x(301), Sintetica.x(101));       // en el cruce de A con C
    var paso4 = m.cruce && m.calle2 != null;
    loc.calcularEn(t, Sintetica.x(100), Sintetica.x(400));       // nada a 50 m
    var paso5 = m.estado == EST_LEJOS && m.calle1 == null;
    if (!(paso1 && paso2 && paso3 && paso4 && paso5)) {
        logger.error("pasos " + [paso1, paso2, paso3, paso4, paso5]);
    }
    return paso1 && paso2 && paso3 && paso4 && paso5;
}

// La histéresis no conserva una calle que ya está a más de Callejero.MAXD: la nueva, dentro, la sustituye
// (antes, con la nueva a MAXD − 0,5 y la mostrada a MAXD + 1,5, seguía la mostrada).
(:test)
function histeresisNoPasaDeMaxd(logger as Test.Logger) as Boolean {
    var d = Callejero.MAXD;
    var yb = 100 + 2 * d + 1;
    var t = Sintetica.tesela(["A", "B"], [
        [0, 0, 0, [0, 100, 600, 100]],
        [1, 0, 0, [0, yb, 600, yb]]
    ] as Array<Array>, [] as Array<Array>);
    var m = new Modelo();
    m.radio = 8;
    var loc = new Localizador(m);
    loc.calcularEn(t, Sintetica.x(100), Sintetica.x(105));             // A a 5 m
    var paso1 = "A".equals(m.calle1);
    loc.calcularEn(t, Sintetica.x(100), Sintetica.x(100 + d + 1.5));   // A a MAXD + 1,5; B a MAXD − 0,5
    var paso2 = "B".equals(m.calle1) && m.d1 <= d;
    if (!(paso1 && paso2)) {
        logger.error("pasos " + [paso1, paso2] + ": " + m.calle1 + " a " + m.d1 + " m; MAXD " + d);
    }
    return paso1 && paso2;
}

// Una Position.Info inventada, como la del GPS falso de medida/Gps.mc. w: segundos de Time.now(), o null.
(:test)
module GpsPrueba {
    function info(lat as Double, lon as Double, calidad as Position.Quality, w as Number or Null) as Position.Info {
        var i = new Position.Info();
        i.position = new Position.Location({:latitude => lat, :longitude => lon, :format => :degrees});
        i.accuracy = calidad;
        i.when = w != null ? new Time.Moment(w) : null;
        return i;
    }
}

// START, toque o vuelta a la vista (forzar): la LAST_KNOWN del reloj puede ser de hace horas y de otra ciudad.
// No pisa un fix más nuevo; sin fix, solo vale si tiene menos de L.SEMILLA_MAX_S, y como semilla (como al abrir).
// Posiciones fuera de toda región: no se carga ninguna tesela.
(:test)
function forzarLastKnownVieja(logger as Test.Logger) as Boolean {
    Activa.poner(Regiones.IDS[0]);
    var ahora = Time.now().value();
    var m = new Modelo();
    var loc = new Localizador(m);
    loc.forzarCon(GpsPrueba.info(-30.0d, 100.0d, Position.QUALITY_GOOD, ahora - 2), ahora);
    var paso1 = m.estado != EST_BUSCANDO && m.tFix == ahora - 2 && !m.semilla;
    var lat1 = m.lat;   // la de Position.Location no vuelve exacta: se compara con ella, no con -30
    loc.forzarCon(GpsPrueba.info(-31.0d, 101.0d, Position.QUALITY_LAST_KNOWN, ahora - 5 * 3600), ahora);
    var paso2 = m.tFix == ahora - 2 && m.lat == lat1;             // la de hace 5 h no pisa la de hace 2 s
    loc.forzarCon(GpsPrueba.info(-31.0d, 101.0d, Position.QUALITY_LAST_KNOWN, ahora - 60), ahora);
    var paso3 = m.tFix == ahora - 2 && m.lat == lat1;             // ni una reciente pero más vieja que el fix
    var m2 = new Modelo();
    var loc2 = new Localizador(m2);
    loc2.forzarCon(GpsPrueba.info(-31.0d, 101.0d, Position.QUALITY_LAST_KNOWN, ahora - 5 * 3600), ahora);
    var paso4 = m2.estado == EST_BUSCANDO;                           // sin fix: la de hace 5 h, tampoco
    loc2.forzarCon(GpsPrueba.info(-31.0d, 101.0d, Position.QUALITY_LAST_KNOWN, ahora - 60), ahora);
    var paso5 = m2.estado != EST_BUSCANDO && m2.semilla && m2.tFix == ahora - 60;   // la de hace 1 min, como semilla
    var ok = paso1 && paso2 && paso3 && paso4 && paso5;
    if (!ok) {
        logger.error("pasos " + [paso1, paso2, paso3, paso4, paso5]);
    }
    return ok;
}
