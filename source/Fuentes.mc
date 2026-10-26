import Toybox.Graphics;
import Toybox.Lang;

// Fuentes de la pantalla. Las vectoriales (API 4.2) existen en el fēnix 7 y el 8; los fēnix 5 y 6 usan las de
// sistema, que ya vienen a la medida de su pantalla.
// Interfaz de la v3.4 (P73, propuesta C): nombres en Noto Sans (grotesca, con tildes y ñ) y cifras en Bionic, la de
// las esferas de Garmin. Bionic solo trae « #%+-./0123456789:°»: lo demás (la letra de «12B») va en la de nombres.
// Si el reloj no tiene una cara, getVectorFont toma la siguiente de la lista: Roboto Condensed, la de la v3.
module Fuentes {
    const NOMBRES = ["NotoSansSCMedium", "RobotoCondensedBold"];
    const CIFRAS = ["BionicBold", "BionicSemiBold", "RobotoCondensedBold"];   // SemiBold: Enduro 3, fēnix 8 Solar
    const ROBOTO = ["RobotoCondensedBold"];
    const BIONIC = " #%+-./0123456789:°";

    // px es el tamaño en la pantalla de 280: se escala a la real (L.escalar antes).
    function cara(caras as Array, px as Number) as Graphics.FontType or Null {
        if (Graphics has :getVectorFont) {
            return Graphics.getVectorFont({:face => caras, :size => L.y(px)});
        }
        return null;
    }

    function vectorial(px as Number) as Graphics.FontType or Null {
        return cara(ROBOTO, px);
    }

    function nombre(px as Number) as Graphics.FontType or Null {
        return cara(NOMBRES, px);
    }

    // [cadena para una calle, cadena para dos calles y el lugar, fuente del número, fuente de su letra]
    function calle(dc as Graphics.Dc) as Array {
        var n32 = nombre(32);
        var n28 = nombre(28);
        var n25 = nombre(25);
        var n22 = nombre(22);
        var num = cara(CIFRAS, L.NUM_PX);
        var letra = nombre(24);
        if (n32 != null && n28 != null && n25 != null && n22 != null && num != null && letra != null) {
            return [[n32, n28, n25, n22, Graphics.FONT_SMALL] as Array,
                    [n28, n25, n22, Graphics.FONT_TINY] as Array, num, letra];
        }
        // Con TINY al final, un nombre muy largo aún cabe entero en tres líneas antes de recortarse en una.
        // El número: la NUMBER_MILD (también Bionic) si cabe en la pastilla; si no, la MEDIUM.
        var numS = dc.getFontHeight(Graphics.FONT_NUMBER_MILD) <= L.y(40) ? Graphics.FONT_NUMBER_MILD : Graphics.FONT_MEDIUM;
        return [[Graphics.FONT_LARGE, Graphics.FONT_MEDIUM, Graphics.FONT_SMALL, Graphics.FONT_TINY] as Array,
                [Graphics.FONT_MEDIUM, Graphics.FONT_SMALL, Graphics.FONT_TINY] as Array, numS, Graphics.FONT_SMALL];
    }

    // La hora: Bionic de L.HORA_PX; sin vectoriales, la más alta de sistema que no pase de HORA_MAX px.
    // En los fēnix 5 la NUMBER_MILD es más baja que la LARGE (26 y 37 px en el 5): por eso, la más alta.
    function hora(dc as Graphics.Dc) as Graphics.FontType {
        var v = cara(CIFRAS, L.HORA_PX);
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

    // Cuántos caracteres del principio de s caben en la fuente de cifras («12B» → 2).
    function cifras(s as String) as Number {
        var cs = s.toCharArray();
        for (var i = 0; i < cs.size(); i++) {
            if (BIONIC.find(cs[i].toString()) == null) {
                return i;
            }
        }
        return cs.size();
    }
}
