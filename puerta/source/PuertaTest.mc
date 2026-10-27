import Toybox.Lang;
import Toybox.StringUtil;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

// Puerta del plan c5 (docs/plans/2026-10-26-c5-plan1-puerta.md): la tesela más pesada de Galicia en FORMATO 5,
// leída en el fēnix 5. Lo esperado lo calcula tools/puerta_c5.py con la referencia Python del FORMATO 4.
(:test)
function puertaVectores(logger as Test.Logger) as Boolean {
    var t = Puerta.tesela();
    var P = PuertaDatos.PUNTOS;
    var ok = true;
    for (var i = 0; i < P.size(); i++) {
        var c = P[i];
        var x = c[0] as Float;
        var y = c[1] as Float;
        var s = Buscador.buscar(t, x, y);
        var a = s[0];
        var b = s[1];
        var calle = a >= 0 && t.mejor[a] <= Callejero.MAXD ? t.nombre(a) : "";
        var d1 = calle.equals("") ? -1.0 : t.mejor[a];
        var num = "";
        if (!calle.equals("")) {
            var p = Buscador.portal(t, a, x, y);
            num = p == null ? "" : p[0] as String;
        }
        var calle2 = b >= 0 && t.mejor[b] <= Callejero.MAXD ? t.nombre(b) : "";
        var bien = calle.equals(c[2]) && (d1 - (c[3] as Float)).abs() < 0.1 && num.equals(c[4]) && calle2.equals(c[5]);
        if (!bien) {
            logger.error("punto " + i + ": esperaba " + c[2] + " " + c[3] + " nº" + c[4] + " / " + c[5] + "; dice "
                + calle + " " + d1 + " nº" + num + " / " + calle2);
            ok = false;
        }
    }
    logger.debug("PUERTA " + PuertaDatos.ETIQUETA + ": " + P.size() + " puntos");
    return ok;
}

(:test)
function puertaMemoria(logger as Test.Logger) as Boolean {
    var l0 = Puerta.libre();
    var s = WatchUi.loadResource(Rez.JsonData.TeselaPuerta) as String;
    var l1 = Puerta.libre();
    var b = StringUtil.convertEncodedString(s, {
        :fromRepresentation => StringUtil.REPRESENTATION_STRING_BASE64,
        :toRepresentation => StringUtil.REPRESENTATION_BYTE_ARRAY
    }) as ByteArray;
    var l2 = Puerta.libre();
    s = null;
    var t = new Tesela(0, b, PuertaDatos.CAJA);
    b = null;
    var l3 = Puerta.libre();
    var pico = l0 - l2;
    logger.debug("PUERTA memoria: base64 " + (l0 - l1) + " B, ByteArray " + (l1 - l2) + " B, pico " + pico
        + " B; tesela lista " + (l0 - l3) + " B (" + t.nc + " calles)");
    // La app sin tesela deja ~62 KB libres en los de 128 KB (especificación del FORMATO 4): el pico, por debajo de 58 KB.
    return pico < 58 * 1024;
}

(:test)
function puertaWatchdog1(logger as Test.Logger) as Boolean {
    var t0 = System.getTimer();
    var n = Puerta.cadena(1);
    logger.debug("PUERTA cadena ×1: " + (System.getTimer() - t0) + " ms");
    return n == 1;
}

(:test)
function puertaWatchdog2(logger as Test.Logger) as Boolean {
    var t0 = System.getTimer();
    var n = Puerta.cadena(2);
    logger.debug("PUERTA cadena ×2: " + (System.getTimer() - t0) + " ms");
    return n == 2;
}

// Plan 2: de qué se compone la tesela ya cargada (la puerta midió 40.192 B y se esperaban ~32.500). Mide, paso a paso, lo mismo
// que hace Tesela.initialize, y luego la tesela de verdad y una búsqueda. Solo mide: no falla.
(:test)
function puertaPartes(logger as Test.Logger) as Boolean {
    var l0 = Puerta.libre();
    var b = Teselas.bytes(Rez.JsonData.TeselaPuerta);
    var l1 = Puerta.libre();
    var ls = Teselas.palabra(b, 8);
    var nc = Teselas.palabra(b, 4);
    var p = 4 * Teselas.CABECERA;
    var trozo = b.slice(p, p + ls);
    var l2 = Puerta.libre();
    var S = StringUtil.convertEncodedString(trozo, {
        :fromRepresentation => StringUtil.REPRESENTATION_BYTE_ARRAY,
        :toRepresentation => StringUtil.REPRESENTATION_STRING_PLAIN_TEXT
    }) as String;
    var l3 = Puerta.libre();
    trozo = null;
    var l4 = Puerta.libre();
    var m1 = new Array<Float>[nc];
    var m2 = new Array<Number>[nc];
    var l5 = Puerta.libre();
    for (var i = 0; i < nc; i++) {
        m1[i] = Buscador.LEJOS;
        m2[i] = -1;
    }
    var l6 = Puerta.libre();
    logger.debug("PARTES ByteArray " + (l0 - l1) + " B; trozo de S " + (l4 - l3) + " B; S " + (l2 - l3) + " B ("
        + S.length() + " letras, " + ls + " bytes); mejor+mejorRun vacías " + (l4 - l5) + " B, llenas " + (l4 - l6)
        + " B (" + nc + " calles)");
    S = null;
    m1 = null;
    m2 = null;
    var l7 = Puerta.libre();
    var t = new Tesela(0, b, PuertaDatos.CAJA);
    b = null;
    var l8 = Puerta.libre();
    Buscador.buscar(t, PuertaDatos.CENTRO[0], PuertaDatos.CENTRO[1]);
    var l9 = Puerta.libre();
    logger.debug("PARTES Tesela sobre el ByteArray " + (l7 - l8) + " B (tablas + objeto); tras buscar +"
        + (l8 - l9) + " B; total desde el principio " + (l0 - l9) + " B");
    // ¿El resto de ~7 KB de new Tesela se paga una vez o con cada tesela? Una segunda sobre el mismo B.
    var t2 = new Tesela(1, t.B, PuertaDatos.CAJA);
    var l10 = Puerta.libre();
    logger.debug("PARTES segunda Tesela sobre el mismo B " + (l9 - l10) + " B (" + t2.nc + " calles)");
    t2 = null;
    return true;
}

// Plan 2: sin S en memoria, indiceDe busca por bisección comparando bytes. Cada calle muestreada se encuentra en su
// sitio; un nombre que no está (o vacío) da -1. Muestreo de ~20 calles más la última, para no rozar el watchdog.
(:test)
function puertaIndiceDe(logger as Test.Logger) as Boolean {
    var t = Puerta.tesela();
    var paso = t.nc / 20 + 1;
    var ok = true;
    for (var k = 0; k < t.nc; k += paso) {
        var n = t.nombre(k);
        var i = t.indiceDe(n);
        if (i != k) {
            logger.error("indiceDe(" + n + ") = " + i + ", esperaba " + k);
            ok = false;
        }
    }
    var ultima = t.nombre(t.nc - 1);
    if (t.indiceDe(ultima) != t.nc - 1) {
        logger.error("indiceDe(" + ultima + ") no da la última");
        ok = false;
    }
    if (t.indiceDe("Rúa que non existe") != -1 || t.indiceDe("") != -1) {
        logger.error("indiceDe encuentra un nombre que no está");
        ok = false;
    }
    // Bordes de comparar: un prefijo propio de un nombre, ese nombre con algo detrás y uno con bytes ≥ 0x80 mayor que todos.
    var n0 = t.nombre(t.nc / 2);
    var corto = n0.substring(0, n0.length() - 1) as String;
    if (t.indiceDe(corto) != -1 || t.indiceDe(n0 + "x") != -1 || t.indiceDe("ÿÿÿ") != -1) {
        logger.error("indiceDe: un borde da otra calle (" + n0 + ": " + t.indiceDe(corto) + ", "
            + t.indiceDe(n0 + "x") + ", " + t.indiceDe("ÿÿÿ") + ")");
        ok = false;
    }
    return ok;
}
