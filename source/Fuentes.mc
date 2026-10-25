import Toybox.Graphics;
import Toybox.Lang;

// Fuentes de la pantalla. Las vectoriales (Roboto Condensed Bold, API 4.2) solo existen en el fēnix 7;
// el fēnix 6X (API 3.4) usa las de sistema, que en su pantalla de 280×280 tienen tamaños parecidos.
module Fuentes {
    function vectorial(px as Number) as Graphics.FontType or Null {
        if (Graphics has :getVectorFont) {
            return Graphics.getVectorFont({:face => "RobotoCondensedBold", :size => px});
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
        return [[Graphics.FONT_LARGE, Graphics.FONT_MEDIUM, Graphics.FONT_SMALL] as Array,
                [Graphics.FONT_MEDIUM, Graphics.FONT_SMALL, Graphics.FONT_TINY] as Array, Graphics.FONT_MEDIUM];
    }

    // La hora: vectorial de L.HORA_PX; sin vectoriales, la mayor de sistema que no pase de HORA_MAX px.
    function hora(dc as Graphics.Dc) as Graphics.FontType {
        var v = vectorial(L.HORA_PX);
        if (v != null) {
            return v;
        }
        var cands = [Graphics.FONT_NUMBER_MILD, Graphics.FONT_LARGE, Graphics.FONT_MEDIUM] as Array<Graphics.FontType>;
        for (var i = 0; i < cands.size(); i++) {
            if (dc.getFontHeight(cands[i]) <= L.HORA_MAX) {
                return cands[i];
            }
        }
        return Graphics.FONT_MEDIUM;
    }
}
