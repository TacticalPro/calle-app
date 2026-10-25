import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;

// Anillo de brújula de la guía (VistaIr), en la franja exterior de la pantalla. Tiene:
// - un círculo fino en el tono oscuro del destino;
// - marcas cada 10°, más largas cada 30°;
// - triángulos en los cardinales: el norte, rojo y mayor; el resto, gris;
// - el destino, como una bola de su color.
// Gira con el rumbo del reloj; sin brújula, queda con el norte arriba. El texto de la guía vive
// dentro de L.ANILLO_RI. La referencia de diseño es Pin Point (Connect IQ Store), 2026-10-24.
module Anillo {
    // giro: hacia dónde mira el reloj (radianes desde el norte) o null. destino: rumbo verdadero al
    // destino (radianes) o null, y entonces no se pinta la bola (sin posición, o ya ha llegado).
    function dibujar(dc as Graphics.Dc, giro as Float or Null, destino as Float or Null, color as Number,
            oscuro as Number) as Void {
        var cx = dc.getWidth() / 2;
        var cy = dc.getHeight() / 2;
        var g = giro != null ? giro : 0.0;
        var r = L.ANILLO_R;
        dc.setPenWidth(1);
        dc.setColor(oscuro, Graphics.COLOR_TRANSPARENT);
        dc.drawCircle(cx, cy, r);
        for (var k = 1; k < 36; k++) {
            if (k % 9 == 0) {
                continue;               // los cardinales llevan triángulo
            }
            var a = k * Math.PI / 18.0 - g;
            if (k % 3 == 0) {
                dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
                dc.setPenWidth(2);
                _radial(dc, cx, cy, a, r - 4, r + 5);
            } else {
                dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
                dc.setPenWidth(1);
                _radial(dc, cx, cy, a, r - 2, r + 2);
            }
        }
        dc.setPenWidth(1);
        for (var k = 3; k >= 0; k--) {          // el norte, el último, para que quede encima
            var a = k * Math.PI / 2.0 - g;
            if (k == 0) {
                _triangulo(dc, cx, cy, a, r - 10, r + 6, 8, Graphics.COLOR_RED);
            } else {
                _triangulo(dc, cx, cy, a, r - 5, r + 5, 5, Graphics.COLOR_LT_GRAY);
            }
        }
        if (destino != null) {
            var a = destino - g;
            var x = cx + r * Math.sin(a);
            var y = cy - r * Math.cos(a);
            dc.setColor(color, Graphics.COLOR_TRANSPARENT);
            dc.fillCircle(x, y, 7);
            dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
            dc.setPenWidth(2);
            dc.drawCircle(x, y, 7);
            dc.setPenWidth(1);
        }
    }

    // Raya radial entre r0 y r1 px del centro, en el ángulo a (0 = arriba, sentido horario).
    function _radial(dc as Graphics.Dc, cx as Number, cy as Number, a as Numeric, r0 as Number, r1 as Number) as Void {
        var s = Math.sin(a);
        var c = Math.cos(a);
        dc.drawLine(cx + r0 * s, cy - r0 * c, cx + r1 * s, cy - r1 * c);
    }

    // Triángulo con la punta hacia dentro, a «punta» px del centro, y la base a «base» px, de 2·medio de ancho.
    function _triangulo(dc as Graphics.Dc, cx as Number, cy as Number, a as Numeric, punta as Number, base as Number,
            medio as Number, color as Number) as Void {
        var s = Math.sin(a);
        var c = Math.cos(a);
        var bx = cx + base * s;
        var by = cy - base * c;
        var pts = [] as Array<[Numeric, Numeric]>;
        pts.add([cx + punta * s, cy - punta * c]);
        pts.add([bx + medio * c, by + medio * s]);     // (c, s) es la tangente al anillo
        pts.add([bx - medio * c, by - medio * s]);
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon(pts);
    }
}
