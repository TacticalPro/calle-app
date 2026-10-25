import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

// Mide las fuentes de sistema de cada reloj en el simulador (./ciq.sh fuentes → tools/fonts/metricas.json):
// alto, ascenso, descenso y el ancho de cada carácter de CHARS. Los anchos suman exactos (sin kerning),
// así que tools/mockup.py reparte los nombres en líneas como el reloj. App vacía: solo vale para los tests.
class MApp extends Application.AppBase {
    function initialize() { AppBase.initialize(); }
    function getInitialView() as [WatchUi.Views] or [WatchUi.Views, WatchUi.InputDelegates] { return [new WatchUi.View()]; }
}

(:test)
module Med {
    const CHARS = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~áéíóúÁÉÍÓÚñÑüÜçÇºª·…—–àèòïÏ";
    function dc() as Graphics.Dc {
        if (Graphics has :createBufferedBitmap) {
            return (Graphics.createBufferedBitmap({:width => 20, :height => 20}).get() as Graphics.BufferedBitmap).getDc();
        }
        return new Graphics.BufferedBitmap({:width => 20, :height => 20}).getDc();
    }
    function fuente(logger as Test.Logger, nombre as String, f as Graphics.FontType) as Boolean {
        var d = dc();
        var s = "MED " + nombre + " h=" + d.getFontHeight(f) + " asc=" + Graphics.getFontAscent(f) + " desc=" + Graphics.getFontDescent(f) + " w=";
        var cs = CHARS.toCharArray();
        for (var i = 0; i < cs.size(); i++) {
            s += d.getTextWidthInPixels(cs[i].toString(), f) + ",";
        }
        logger.debug(s);
        logger.debug("MED " + nombre + " par=" + d.getTextWidthInPixels("Calle de la Princesa", f));
        return true;
    }
}
(:test) function m0(l as Test.Logger) as Boolean { return Med.fuente(l, "xtiny", Graphics.FONT_XTINY); }
(:test) function m1(l as Test.Logger) as Boolean { return Med.fuente(l, "tiny", Graphics.FONT_TINY); }
(:test) function m2(l as Test.Logger) as Boolean { return Med.fuente(l, "small", Graphics.FONT_SMALL); }
(:test) function m3(l as Test.Logger) as Boolean { return Med.fuente(l, "medium", Graphics.FONT_MEDIUM); }
(:test) function m4(l as Test.Logger) as Boolean { return Med.fuente(l, "large", Graphics.FONT_LARGE); }
(:test) function m5(l as Test.Logger) as Boolean { return Med.fuente(l, "numberMild", Graphics.FONT_NUMBER_MILD); }
(:test) function m6(l as Test.Logger) as Boolean {
    var d = Med.dc();
    var s = "MED vect";
    if (Graphics has :getVectorFont) {
        var tam = [20, 24, 26, 28, 30, 32, 34, 38, 44, 48, 52, 56, 64, 72] as Array<Number>;
        for (var i = 0; i < tam.size(); i++) {
            var f = Graphics.getVectorFont({:face => "RobotoCondensedBold", :size => tam[i]});
            s += " " + tam[i] + ":" + (f == null ? "null" : d.getFontHeight(f) + "/" + d.getTextWidthInPixels("Calle de la Princesa", f));
        }
    } else {
        s += " none";
    }
    l.debug(s);
    return true;
}
