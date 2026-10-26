import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
import Toybox.Time.Gregorian;

module Fmt {
    const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"] as Array<String>;

    function hhmm(h as Number, m as Number) as String {
        return h.format("%02d") + ":" + m.format("%02d");
    }

    function reloj() as String {
        var c = System.getClockTime();
        return hhmm(c.hour, c.min);
    }

    // Edad de la posición: "hace 25 s", "hace 3 min", "hace 2 h".
    function edad(s as Number) as String {
        if (s < 60) {
            return "hace " + s + " s";
        } else if (s < 3600) {
            return "hace " + (s / 60) + " min";
        }
        return "hace " + (s / 3600) + " h";
    }

    // Rótulos en mayúsculas (barrio, edad, «ENTRE»). toUpper() solo sube el ASCII: las tildes, la ñ y la ü, a mano.
    const MINUS = "áéíóúñüàèòçï";
    const MAYUS = "ÁÉÍÓÚÑÜÀÈÒÇÏ";

    function mayus(s as String) as String {
        var cs = s.toUpper().toCharArray();
        var r = "";
        for (var i = 0; i < cs.size(); i++) {
            var c = cs[i].toString();
            var k = MINUS.find(c);
            r += k != null ? MAYUS.substring(k, k + 1) : c;
        }
        return r;
    }

    // «~», no «≈»: las fuentes de sistema del reloj (CDPG, página de códigos latina) no traen «≈» y lo
    // pintan como «�» (visto en DOS CALLES, que va en FONT_XTINY, y en el 6X, que no tiene vectoriales).
    function numero(num as String, aprox as Boolean) as String {
        return (aprox ? "~ nº " : "nº ") + num;
    }

    // Las anotaciones guardadas antes del 2026-10-24 llevan «≈»; el menú lo muestra como «~».
    function legible(s as String) as String {
        var i = s.find("≈");
        while (i != null) {
            s = s.substring(0, i) + "~" + s.substring(i + 1, s.length());
            i = s.find("≈");
        }
        return s;
    }

    function grados(lat as Double, lon as Double) as String {
        return lat.format("%.5f") + "  " + lon.format("%.5f");
    }

    // Hora y fecha locales de un instante (s de época): ["23:41", "23-oct"].
    function horaYFecha(t as Number) as Array<String> {
        var g = Gregorian.info(new Time.Moment(t), Time.FORMAT_SHORT);
        return [hhmm(g.hour, g.min), (g.day as Number).toString() + "-" + MESES[(g.month as Number) - 1]] as Array<String>;
    }
}
