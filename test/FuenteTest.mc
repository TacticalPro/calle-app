import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;

// Fase 0: la fuente vectorial existe (fēnix 7) y se puede medir texto con tildes en un Dc de prueba.
// En el fēnix 6X (API 3.4) no hay vectoriales: se comprueba que las de sistema miden lo mismo con tildes.
(:test)
function fuenteVectorial(logger as Test.Logger) as Boolean {
    var vf = Fuentes.vectorial(38);
    var dc = Lienzo.dc();
    var s = "Rúa do Franco ñ";
    var f = vf != null ? vf : Graphics.FONT_LARGE;
    var w = dc.getTextWidthInPixels(s, f);
    var h = dc.getFontHeight(f);
    logger.debug("FUENTE vf=" + (vf != null) + " ancho=" + w + " alto=" + h + " len=" + s.length()
        + " sub=" + s.substring(0, 3) + " small=" + dc.getTextWidthInPixels(s, Graphics.FONT_MEDIUM));
    return w > 0 && s.length() == 15 && s.substring(0, 3).equals("Rúa");
}
