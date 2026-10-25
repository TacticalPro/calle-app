import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.Test;

// Ir a hospital o comisaría: distancias, rumbos, textos, y los más cercanos en orden y por tipo.
(:test)
function irCuentas(logger as Test.Logger) as Boolean {
    // Sol → Cibeles: unos 920 m al este (y un poco al norte).
    var d = Ir.distancia(40.4169d, -3.7035d, 40.4193d, -3.6931d);
    var r = Ir.rumbo(40.4169d, -3.7035d, 40.4193d, -3.6931d);
    var norte = Ir.rumbo(40.0d, -3.0d, 40.01d, -3.0d);
    var este = Ir.rumbo(40.0d, -3.0d, 40.0d, -2.99d);
    var oeste = Ir.rumbo(40.0d, -3.0d, 40.0d, -3.01d);
    var pi = Math.PI.toFloat();
    var ok = d > 900.0 && d < 940.0 && r > 1.2 && r < 1.4
        && norte.abs() < 0.001 && (este - pi / 2.0).abs() < 0.001 && (oeste - 3.0 * pi / 2.0).abs() < 0.001
        && Ir.texto(850.0).equals("850 m") && Ir.texto(994.0).equals("990 m") && Ir.texto(996.0).equals("1,0 km")
        && Ir.texto(1234.0).equals("1,2 km") && Ir.texto(12345.0).equals("12 km")
        && Ir.cardinal(0.0).equals("N") && Ir.cardinal(pi / 4.0).equals("NE") && Ir.cardinal(pi).equals("S")
        && Ir.cardinal(7.0 * pi / 4.0).equals("NO") && Ir.cardinal(2.0 * pi - 0.1).equals("N");
    if (!ok) {
        logger.error("d " + d + " r " + r + " norte " + norte + " este " + este + " oeste " + oeste
            + " textos " + Ir.texto(994.0) + "/" + Ir.texto(996.0) + "/" + Ir.texto(1234.0));
    }
    return ok;
}

(:test)
function irCercanos(logger as Test.Logger) as Boolean {
    Activa.poner(Regiones.IDS[0]);
    // Cinco puntos en metros de región: tres hospitales y dos comisarías, a distintas distancias de (1000, 1000).
    var d = [Callejero.FORMATO,
        ["H lejos", "C cerca", "H cerca", "H medio", "C lejos"],
        ["", "Calle A 1", "", "Calle B 2", ""],
        [5000, 1100, 1050, 2000, 9000],
        [1000, 1000, 1000, 1000, 1000],
        [Ir.HOSPITAL, Ir.CNP, Ir.URGENCIAS, Ir.HOSPITAL, Ir.CNP]] as Array;
    var lat = Callejero.LAT_MIN + 1000.0d / Callejero.KY;
    var lon = Callejero.LON_MIN + 1000.0d / Callejero.KX;
    var h = Ir.cercanos(d, lat, lon, Ir.HOSPITALES, 2);
    var c = Ir.cercanos(d, lat, lon, Ir.COMISARIAS, 8);
    var ok = h.size() == 2 && "H cerca".equals(h[0][0]) && "H medio".equals(h[1][0])
        && ((h[0][5] as Float) - 50.0).abs() < 1.0 && (h[0][4] as Number) == Ir.URGENCIAS
        && c.size() == 2 && "C cerca".equals(c[0][0]) && "Calle A 1".equals(c[0][1]) && "C lejos".equals(c[1][0])
        && Ir.cercanos(d, lat, lon, Ir.OTRAS_POLICIAS, 8).size() == 0;
    if (!ok) {
        logger.error("h " + h + " c " + c);
    }
    // El recurso real de la región carga y tiene el formato.
    var real = Ir.cargar();
    logger.debug("IR " + Callejero.ETIQUETA + ": " + (real == null ? "sin puntos" : (real[1] as Array).size() + " puntos"));
    return ok && real != null;
}

// La región se elige sola por la posición (automática) y se queda quieta con una zona fija.
(:test)
function activaPorPosicion(logger as Test.Logger) as Boolean {
    Ajustes.fijarZona(Ajustes.AUTO);
    var ok = true;
    var c = Regiones.CAJAS;
    for (var i = 0; i < Regiones.IDS.size(); i++) {
        var lat = (c[4 * i] + c[4 * i + 2]) / 2.0d;
        var lon = (c[4 * i + 1] + c[4 * i + 3]) / 2.0d;
        Activa.paraPosicion(lat, lon);
        ok = ok && Callejero.ID == Regiones.IDS[i] && Ajustes.ultima() == Regiones.IDS[i];
    }
    // Fuera de todas: se queda la última.
    var antes = Callejero.ID;
    var cambia = Activa.paraPosicion(0.0d, 0.0d);
    ok = ok && !cambia && Callejero.ID == antes;
    // Fija en la primera: aunque la posición caiga en otra, no se mueve.
    Ajustes.fijarZona(Regiones.IDS[0]);
    var n = Regiones.IDS.size() - 1;
    Activa.paraPosicion((c[4 * n] + c[4 * n + 2]) / 2.0d, (c[4 * n + 1] + c[4 * n + 3]) / 2.0d);
    ok = ok && Callejero.ID == Regiones.IDS[0] && Ajustes.zona() == Regiones.IDS[0];
    Ajustes.fijarZona(Ajustes.AUTO);
    ok = ok && Ajustes.zona() == Ajustes.AUTO;
    if (!ok) {
        logger.error("región " + Callejero.ID + " zona " + Ajustes.zona());
    }
    return ok;
}

// La guía se pinta con y sin posición, con un nombre largo y pasando al siguiente.
(:test)
function vistaIrPinta(logger as Test.Logger) as Boolean {
    Activa.poner(Regiones.IDS[0]);
    var dc = Lienzo.dc();
    var lista = [
        ["Complexo Hospitalario Universitario de Santiago de Compostela", "Rúa da Choupana", 42.87d, -8.56d, Ir.URGENCIAS, 1200.0],
        ["Comisaría", "Rúa do Vilar 44", 42.8785d, -8.5446d, Ir.CNP, 20.0]
    ] as Array<Array>;
    var v = new VistaIr(lista, 0, 42.88d, -8.545d);
    v.onLayout(dc);
    v.onUpdate(dc);
    v.mover(1);
    v.onUpdate(dc);                 // a 20 m: «HA LLEGADO»
    v.mover(1);
    var sin = new VistaIr(lista, 1, null, null);
    sin.onLayout(dc);
    sin.onUpdate(dc);               // sin posición
    // Hacia una anotación (rótulo con la hora, la UTM en lugar de la dirección), y a la siguiente.
    var notas = Ir.deNotas([[7, [1000, "Rúa do Vilar 44 / Rúa Nova ≈11", 42.8785539d, -8.5446323d]],
        [5, [900, "Rúa do Franco 33", 42.8781762d, -8.5453149d]]] as Array<Array>);
    var vn = new VistaIr(notas, 0, 42.88d, -8.545d);
    vn.onLayout(dc);
    vn.onUpdate(dc);
    vn.mover(1);
    vn.onUpdate(dc);
    // El pie que cabe en este reloj dentro del anillo (se acorta antes de perder el cardinal).
    var pw = Texto.anchoR(dc, 245 - 9, 245 + 9, L.ANILLO_RI, 4);
    logger.debug("ANILLO pie: ancho " + pw + " px; «línea recta · NO» " + dc.getTextWidthInPixels("línea recta · NO",
        Graphics.FONT_XTINY) + " px, «norte arriba · NO» " + dc.getTextWidthInPixels("norte arriba · NO", Graphics.FONT_XTINY)
        + " px; rótulo «ANOTACIÓN · 21:15» " + dc.getTextWidthInPixels("ANOTACIÓN · 21:15", Graphics.FONT_XTINY)
        + " de " + Texto.anchoR(dc, 52 - 9, 52 + 9, L.ANILLO_RI, 4) + " px");
    return true;
}

// El anillo se pinta con y sin brújula, con y sin destino, en varios giros (cualquier excepción falla).
(:test)
function anilloPinta(logger as Test.Logger) as Boolean {
    var dc = Lienzo.dc();
    var giros = [null, 0.0, 1.3, 3.14159, 5.9] as Array<Float or Null>;
    var destinos = [null, 0.0, 2.2, 6.2] as Array<Float or Null>;
    for (var i = 0; i < giros.size(); i++) {
        for (var j = 0; j < destinos.size(); j++) {
            for (var t = 0; t <= Ir.ANOTACION; t++) {
                Anillo.dibujar(dc, giros[i], destinos[j], Ir.color(t), Ir.colorOscuro(t));
            }
        }
    }
    return true;
}

// Anotaciones → lista de la guía: solo las que tienen posición, en el mismo orden, con «≈» ya como «~»,
// la UTM en lugar de la dirección, el rótulo con la hora y el seq para encontrarlas.
(:test)
function irDeNotas(logger as Test.Logger) as Boolean {
    var ns = [[9, [3000, "Rúa Nova ≈11", 42.8785539d, -8.5446323d]],
        [8, [2000, "sin posición", null, null]],
        [6, [1000, "Rúa do Franco 33", 42.8781762d, -8.5453149d]]] as Array<Array>;
    var l = Ir.deNotas(ns);
    var ok = l.size() == 2 && "Rúa Nova ~11".equals(l[0][0]) && (l[0][1] as String).find("29T ") == 0
        && (l[0][4] as Number) == Ir.ANOTACION && (l[0][6] as String).find("ANOTACIÓN · ") == 0
        && (l[0][7] as Number) == 9 && (l[1][7] as Number) == 6 && (l[1][2] as Double) == 42.8781762d
        && Ir.indiceNota(l, 6) == 1 && Ir.indiceNota(l, 8) == -1 && Ir.indiceNota(l, 9) == 0
        && Ir.deNotas([] as Array<Array>).size() == 0
        && Ir.color(Ir.ANOTACION) != Ir.color(Ir.CNP) && Ir.color(Ir.URGENCIAS) != Ir.color(Ir.CNP)
        && Ir.etiquetaTipo(Ir.ANOTACION).equals("ANOTACIÓN");
    if (!ok) {
        logger.error("deNotas " + l);
    }
    return ok;
}
