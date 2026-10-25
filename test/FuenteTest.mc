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

// P73: las caras de la v3.4 (Noto Sans en nombres, Bionic en cifras) existen en el reloj, y no han caído en la
// Roboto (si getVectorFont no tiene la cara, toma la siguiente: el ancho lo delata). Mayúsculas con tildes.
(:test)
function fuentesV34(logger as Test.Logger) as Boolean {
    var dc = Lienzo.dc();
    var ok = Fmt.mayus("Casco Histórico, A Raíña ü").equals("CASCO HISTÓRICO, A RAÍÑA Ü")
        && Fuentes.cifras("12B") == 2 && Fuentes.cifras("157") == 3 && Fuentes.cifras("s/n") == 0;
    var noto = Fuentes.nombre(28);
    var rob = Fuentes.vectorial(28);
    var bio = Fuentes.cara(Fuentes.CIFRAS, 32);
    var rob32 = Fuentes.vectorial(32);
    if (noto == null || rob == null || bio == null || rob32 == null) {
        logger.debug("FUENTES v3.4: sin vectoriales en este reloj (sistema)");
        return ok;
    }
    var s = "Rúa do Franco";
    var wn = dc.getTextWidthInPixels(s, noto);
    var wr = dc.getTextWidthInPixels(s, rob);
    var wb = dc.getTextWidthInPixels("1048", bio);
    var wr2 = dc.getTextWidthInPixels("1048", rob32);
    logger.debug("FUENTES v3.4: Noto " + wn + " px / Roboto " + wr + " px; Bionic 1048 " + wb + " / Roboto " + wr2
        + "; alto hora " + dc.getFontHeight(Fuentes.hora(dc)));
    return ok && wn != wr && wb != wr2;
}
