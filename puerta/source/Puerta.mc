import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;

// Puerta del plan c5 (docs/plans/2026-10-26-c5-plan1-puerta.md): la tesela más pesada de Galicia en FORMATO 5,
// leída en el fēnix 5. Lo esperado lo calcula tools/puerta_c5.py con la referencia Python del FORMATO 4.
module Puerta {
    function tesela() as Tesela {
        return new Tesela(0, Teselas.bytes(Rez.JsonData.TeselaPuerta), PuertaDatos.CAJA);
    }

    function libre() as Number {
        return System.getSystemStats().freeMemory;
    }

    // La parte de la cadena del Localizador que toca la tesela, n veces seguidas en un mismo evento:
    // cargar el base64, convertirlo, buscar y los dos portales.
    function cadena(n as Number) as Number {
        var x = PuertaDatos.CENTRO[0];
        var y = PuertaDatos.CENTRO[1];
        var hechas = 0;
        for (var k = 0; k < n; k++) {
            var t = tesela();
            var s = Buscador.buscar(t, x, y);
            if (s[0] >= 0) {
                Buscador.portal(t, s[0], x, y);
                hechas++;
            }
            if (s[1] >= 0) {
                Buscador.portal(t, s[1], x, y);
            }
            t = null;   // como en el Localizador: la tesela anterior se suelta antes de cargar otra
        }
        return hechas;
    }
}
