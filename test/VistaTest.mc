import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.Time;

// Pinta la vista en cada estado sobre un lienzo en memoria: no mira píxeles, pero
// cualquier excepción del dibujo (tipos, nulos, fuentes) hace fallar el test.
(:test)
function vistaTodosLosEstados(logger as Test.Logger) as Boolean {
    var dc = Lienzo.dc();
    var m = new Modelo();
    var v = new VistaCalle(m, new Localizador(m));
    v.onLayout(dc);
    v.onUpdate(dc);                                   // buscando
    m.estado = EST_FUERA;
    m.lat = 43.0d;
    m.lon = -8.5d;
    v.onUpdate(dc);
    m.estado = EST_LEJOS;
    v.onUpdate(dc);
    m.estado = EST_OK;
    m.calidad = 4;
    m.radio = 8;
    var largos = ["Rúa do Franco", "Rúa de Bernardo Barreiro de Vázquez-Varela",
        "Polígono Industrial do Tambre - A Ponte do Romaño (Variante de Aradas)", "AP-9"] as Array<String>;
    for (var i = 0; i < largos.size(); i++) {
        m.limpiar();
        m.calle1 = largos[i];
        m.num1 = i % 2 == 0 ? "12B" : null;
        v.onUpdate(dc);
        m.calle2 = "Rúa da Raíña";
        m.cruce = true;
        v.onUpdate(dc);
        m.cruce = false;
        m.num2 = "7";
        v.onUpdate(dc);
    }
    // v2: barrio encima, tramo debajo (dos lados, uno), esquina con barrio.
    for (var i = 0; i < largos.size(); i++) {
        m.limpiar();
        m.calle1 = largos[i];
        m.num1 = i % 2 == 0 ? "12B" : null;
        m.barrio = i % 2 == 0 ? "Casco Histórico" : null;
        m.tramoA = "Rúa da República de El Salvador";
        m.tramoB = i < 2 ? "Rúa de Bernardo Barreiro de Vázquez-Varela" : null;
        v.onUpdate(dc);
        m.calle2 = "Rúa da Raíña";
        m.cruce = true;
        v.onUpdate(dc);
    }
    // Madrid: barrio con distrito, número con letra; y el mismo con el dato viejo (su edad bajo la hora).
    m.limpiar();
    m.calle1 = "Calle de la Princesa";
    m.num1 = "25B";
    m.barrio = "Hispanoamérica, Castillejos y Nueva España · Chamartín";
    m.tramoA = "Calle de Alberto Aguilera";
    m.tramoB = "Calle de Marqués de Urquijo";
    v.onUpdate(dc);
    m.semilla = true;
    v.onUpdate(dc);
    m.calle2 = "Calle de Martín de los Heros";
    v.onUpdate(dc);
    m.semilla = false;
    m.limpiar();
    m.estado = EST_LEJOS;
    m.lat = 42.82d;
    m.lon = -8.60d;
    v.onUpdate(dc);                                   // sin calle, sin lugar ni parroquia
    m.parroquia = "Santa María de Marrozos";
    v.onUpdate(dc);
    m.lugar = "O Curruncho da Devesa de Arriba";
    v.onUpdate(dc);
    m.estado = EST_FUERA;
    v.onUpdate(dc);
    v.avisar("Anotado 23:41", Graphics.COLOR_GREEN);
    v.onUpdate(dc);
    v.avisar("Anotaciones llenas (300)", Graphics.COLOR_YELLOW);
    v.onUpdate(dc);
    v.onFinAviso();
    m.estado = EST_OK;
    m.calle1 = "Rúa do Franco";
    m.semilla = true;
    v.onUpdate(dc);
    v.cambiarPagina();
    v.onUpdate(dc);                                   // detalle
    var v38 = Fuentes.vectorial(38);
    if (v38 != null) {
        var c = Texto.colocar(dc, "Polígono Industrial do Tambre - A Ponte do Romaño (Variante de Aradas)",
            [v38] as Array, 3, 52, 192);
        logger.debug("VISTA nombre larguísimo a 38 px: " + (c == null ? "no cabe (cae a la siguiente fuente)" : "cabe"));
    }
    // Las fuentes de este reloj: la hora y las de sistema (para ajustar cotas en el fēnix 6X).
    logger.debug("VISTA alto de fuente: hora " + dc.getFontHeight(Fuentes.hora(dc)) + " px (vectorial: "
        + (Fuentes.vectorial(L.HORA_PX) != null) + "), XTINY " + dc.getFontHeight(Graphics.FONT_XTINY)
        + ", TINY " + dc.getFontHeight(Graphics.FONT_TINY) + ", SMALL " + dc.getFontHeight(Graphics.FONT_SMALL)
        + ", MEDIUM " + dc.getFontHeight(Graphics.FONT_MEDIUM) + ", LARGE " + dc.getFontHeight(Graphics.FONT_LARGE)
        + ", NUMBER_MILD " + dc.getFontHeight(Graphics.FONT_NUMBER_MILD) + "; ancho de 23:59 "
        + dc.getTextWidthInPixels("23:59", Fuentes.hora(dc)));
    return true;
}

(:test)
function abrevYPalabras(logger as Test.Logger) as Boolean {
    var p = Texto.palabras("  Rúa  do Franco ");
    return Abrev.corta("Rúa do Franco").equals("R. do Franco") && Abrev.corta("Avenida de Lugo").equals("Av. de Lugo")
        && Abrev.corta("AP-9").equals("AP-9") && Abrev.corta("Alameda").equals("Alameda")
        && Abrev.corta("Carrer de Colón").equals("C. de Colón") && Abrev.corta("Plaça Major").equals("Pl. Major")
        && Abrev.corta("Passatge del Crèdit").equals("Ptge. del Crèdit") && Abrev.corta("Travessera de Gràcia").equals("Trav. de Gràcia")
        && p.size() == 3 && p[0].equals("Rúa") && p[2].equals("Franco")
        && Fmt.edad(25).equals("hace 25 s") && Fmt.edad(185).equals("hace 3 min") && Fmt.hhmm(7, 5).equals("07:05")
        && Fmt.MESES.size() == 12 && Fmt.horaYFecha(0)[1].length() >= 5;
}

// Pantallas pequeñas: lo que cabe sale tal cual; lo que no, a trozos de palabras con «…» que caben en el ancho.
(:test)
function trozoCabe(logger as Test.Logger) as Boolean {
    var dc = Lienzo.dc();
    var f = Graphics.FONT_XTINY;
    var e = dc.getTextWidthInPixels("…", f);
    var w = dc.getTextWidthInPixels("Hospital Xeral", f) + 2 * e;
    var t = Texto.trozo(dc, "Hospital Xeral Ribera Juan Cardona", f, w);
    logger.debug("TROZO " + t);
    return Texto.trozo(dc, "Rúa do Franco", f, 280).equals("Rúa do Franco") && dc.getTextWidthInPixels(t, f) <= w
        && t.find("…") != null && Texto.trozo(dc, "Supercalifragilístico", f, e).equals("Supercalifragilístico");
}

// System.getTimer() negativo (reloj encendido más de ~24,8 días): el trozo sigue dentro de [0, n).
(:test)
function trozoTurnoNegativo(logger as Test.Logger) as Boolean {
    var ts = [0, 1999, 2000, 7999, -1, -2000, -2001, -7999, -2147483647, 2147483647] as Array<Number>;
    for (var i = 0; i < ts.size(); i++) {
        for (var n = 1; n <= 4; n++) {
            var p = Texto.turno(ts[i], n);
            if (p < 0 || p >= n) {
                logger.debug("turno(" + ts[i] + ", " + n + ") = " + p);
                return false;
            }
        }
    }
    return Texto.turno(4000, 3) == 2 && Texto.turno(-2000, 3) == 2;
}

// La caché de maquetación se rehace cuando el dato envejece con dos calles y barrio (Madrid): topDos() baja la
// primera calle para la edad, y antes la clave no lo veía («HACE 20 S» encima del nombre).
(:test)
function claveVeElDatoViejo(logger as Test.Logger) as Boolean {
    var m = new Modelo();
    var v = new VistaCalle(m, new Localizador(m));
    m.estado = EST_OK;
    m.calle1 = "Calle de la Princesa";
    m.calle2 = "Calle de Martín de los Heros";
    m.barrio = "Argüelles · Moncloa-Aravaca";
    m.tFix = Time.now().value() - 2;
    var fresca = v.clave();
    m.tFix = Time.now().value() - 20;
    var vieja = v.clave();
    if (fresca.equals(vieja)) {
        logger.error("la misma clave con el dato fresco y viejo: " + fresca);
    }
    return !fresca.equals(vieja);
}

// Un nombre que no cabe en una línea pero sí en dos (el recurso de pintarCaja cuando Texto.colocar no lo coloca)
// sale entero, sin trozos; solo lo que no cabe ni así va a trozos.
(:test)
function encajaEnDosLineas(logger as Test.Logger) as Boolean {
    var dc = Lienzo.dc();
    var f = Graphics.FONT_TINY;
    var a = dc.getTextWidthInPixels("Rúa da Raíña", f);
    var b = dc.getTextWidthInPixels("Vella de Abaixo", f);
    var w = (a > b ? a : b) + 6;
    var h = dc.getFontHeight(f) * 5 / 2;
    var s = Texto.encaja(dc, "Rúa da Raíña Vella de Abaixo", f, w, h);
    var largo = Texto.encaja(dc, "Rúa de Bernardo Barreiro de Vázquez-Varela e Pereira", f, w, h);
    logger.debug("ENCAJA «" + s + "» / «" + largo + "»");
    return s.find("…") == null && s.find("Rúa") != null && s.find("Abaixo") != null && largo.find("…") != null;
}
