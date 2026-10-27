import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.System;

// Nombres largos en pantalla redonda: reparte palabras en líneas cuyo ancho depende
// de la altura (la cuerda del círculo), probando fuentes de mayor a menor.
module Texto {

    // Ancho útil de una franja horizontal [y0, y1] de la pantalla redonda, con margen (en px de la de 280).
    function ancho(dc as Graphics.Dc, y0 as Number, y1 as Number, margen as Number) as Number {
        return anchoR(dc, y0, y1, dc.getWidth() / 2, margen);
    }

    // Lo mismo dentro de un círculo de radio r centrado en la pantalla (la guía, dentro del anillo).
    function anchoR(dc as Graphics.Dc, y0 as Number, y1 as Number, r as Number, margen as Number) as Number {
        var c = dc.getHeight() / 2;
        var d0 = (y0 - c).abs();
        var d1 = (y1 - c).abs();
        var d = d0 > d1 ? d0 : d1;
        if (d >= r) {
            return 0;
        }
        return (2 * Math.sqrt(r * r - d * d)).toNumber() - 2 * L.y(margen);

    }

    function palabras(s as String) as Array<String> {
        var out = [] as Array<String>;
        var resto = s;
        var i = resto.find(" ");
        while (i != null) {
            if (i > 0) {
                out.add(resto.substring(0, i) as String);
            }
            resto = resto.substring(i + 1, resto.length()) as String;
            i = resto.find(" ");
        }
        if (resto.length() > 0) {
            out.add(resto);
        }
        return out;
    }

    // Reparte s en como mucho anchos.size() líneas, la i-ésima de ancho ≤ anchos[i]. null si no cabe.
    function partir(dc as Graphics.Dc, s as String, f as Graphics.FontType, anchos as Array<Number>) as Array<String> or Null {
        var ps = palabras(s);
        var lineas = [] as Array<String>;
        var actual = "";
        for (var i = 0; i < ps.size(); i++) {
            var prueba = actual.length() == 0 ? ps[i] : actual + " " + ps[i];
            if (dc.getTextWidthInPixels(prueba, f) <= anchos[lineas.size()]) {
                actual = prueba;
                continue;
            }
            if (actual.length() == 0) {
                return null;   // una palabra sola ya no cabe
            }
            lineas.add(actual);
            if (lineas.size() >= anchos.size() || dc.getTextWidthInPixels(ps[i], f) > anchos[lineas.size()]) {
                return null;
            }
            actual = ps[i];
        }
        if (actual.length() > 0) {
            lineas.add(actual);
        }
        return lineas;
    }

    // Pantallas pequeñas (fēnix 5 y 6): si txt no cabe en una línea de ancho w, lo parte por palabras en trozos que
    // caben y devuelve el que toca ahora (cambia cada 2 s), con «…» donde sigue. Si cabe, txt tal cual: lo que ya cabía
    // se pinta igual que antes. Con una palabra que no cabe sola, también tal cual (quien llama lo recorta).
    function trozo(dc as Graphics.Dc, txt as String, f as Graphics.FontType, w as Number) as String {
        if (dc.getTextWidthInPixels(txt, f) <= w) {
            return txt;
        }
        w -= 2 * dc.getTextWidthInPixels("…", f);
        var ls = partir(dc, txt, f, [w, w, w, w, w, w, w, w] as Array<Number>);
        if (ls == null) {
            return txt;
        }
        var n = ls.size();
        var p = turno(System.getTimer(), n);
        return (p > 0 ? "…" : "") + ls[p] + (p < n - 1 ? "…" : "");
    }

    // Qué trozo de n toca en el instante t (ms de System.getTimer()), cambiando cada 2 s. El contador da la vuelta a
    // negativo a los ~24,8 días de reloj encendido y el % de Monkey C conserva el signo: sin corregirlo, el índice sale
    // negativo (Array Out Of Bounds en el 7X Pro, 3.5.1, 2026-10-27; el simulador empieza en 0 y no lo ve).
    function turno(t as Number, n as Number) as Number {
        var p = (t / 2000) % n;
        return p < 0 ? p + n : p;
    }

    // Busca la primera combinación (fuente, forma del nombre, nº de líneas) que cabe en la
    // franja [y0, y1]. Devuelve [fuente, líneas, y de la primera línea, alto de línea] o null.
    function colocar(dc as Graphics.Dc, nombre as String, fuentes as Array, maxLineas as Number,
            y0 as Number, y1 as Number) as Array or Null {
        var corto = Abrev.corta(nombre);
        var formas = corto.equals(nombre) ? [nombre] : [nombre, corto];
        for (var fi = 0; fi < fuentes.size(); fi++) {
            var f = fuentes[fi] as Graphics.FontType;
            var alto = dc.getFontHeight(f);
            var lh = (alto * 0.92).toNumber();
            for (var k = 0; k < formas.size(); k++) {
                for (var n = 1; n <= maxLineas; n++) {
                    if (n * lh > y1 - y0) {
                        break;
                    }
                    var top = (y0 + y1 - n * lh) / 2;
                    var anchos = [] as Array<Number>;
                    for (var i = 0; i < n; i++) {
                        anchos.add(ancho(dc, top + i * lh, top + i * lh + alto, 10));
                    }
                    var lineas = partir(dc, formas[k] as String, f, anchos);
                    if (lineas != null) {
                        top = (y0 + y1 - lineas.size() * lh) / 2;
                        return [f, lineas, top, lh];
                    }
                }
            }
        }
        return null;
    }
}
