import Toybox.Lang;
import Toybox.Test;

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
