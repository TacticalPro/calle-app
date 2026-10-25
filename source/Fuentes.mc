import Toybox.Graphics;
import Toybox.Lang;

// Fuentes de la pantalla. Las vectoriales (Roboto Condensed Bold, API 4.2) existen en el fēnix 7 y el 8;
// los fēnix 5 y 6 usan las de sistema, que ya vienen a la medida de su pantalla.
module Fuentes {
    // px es el tamaño en la pantalla de 280: se escala a la real (L.escalar antes).
    function vectorial(px as Number) as Graphics.FontType or Null {
        if (Graphics has :getVectorFont) {
            return Graphics.getVectorFont({:face => "RobotoCondensedBold", :size => L.y(px)});
        }
        return null;
    }

    // [cadena para una calle, cadena para dos calles y el lugar, fuente del número]
    function calle(dc as Graphics.Dc) as Array {
        var v38 = vectorial(38);
        var v32 = vectorial(32);
        var v28 = vectorial(28);
        var v26 = vectorial(26);
        var v30 = vectorial(30);
        if (v38 != null && v32 != null && v28 != null && v26 != null && v30 != null) {
            return [[v38, v32, v28, v26, Graphics.FONT_SMALL] as Array,
                    [v30, v26, Graphics.FONT_SMALL, Graphics.FONT_TINY] as Array, v30];
        }
        // Con TINY al final, un nombre muy largo aún cabe entero en tres líneas antes de recortarse en una.
        return [[Graphics.FONT_LARGE, Graphics.FONT_MEDIUM, Graphics.FONT_SMALL, Graphics.FONT_TINY] as Array,

                [Graphics.FONT_MEDIUM, Graphics.FONT_SMALL, Graphics.FONT_TINY] as Array, Graphics.FONT_MEDIUM];
    }

    // La hora: vectorial de L.HORA_PX; sin vectoriales, la más alta de sistema que no pase de HORA_MAX px.
    // En los fēnix 5 la NUMBER_MILD es más baja que la LARGE (26 y 37 px en el 5): por eso, la más alta.
    function hora(dc as Graphics.Dc) as Graphics.FontType {
        var v = vectorial(L.HORA_PX);
        if (v != null) {
            return v;
        }
        var cands = [Graphics.FONT_NUMBER_MILD, Graphics.FONT_LARGE, Graphics.FONT_MEDIUM] as Array<Graphics.FontType>;
        var max = L.y(L.HORA_MAX);
        var mejor = Graphics.FONT_MEDIUM;
        var alto = 0;
        for (var i = 0; i < cands.size(); i++) {
            var h = dc.getFontHeight(cands[i]);
            if (h <= max && h > alto) {
                mejor = cands[i];
                alto = h;
            }
        }
        return mejor;
    }

}
