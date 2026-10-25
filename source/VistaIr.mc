import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.Position;
import Toybox.Timer;
import Toybox.WatchUi;

// Guía a un hospital, una comisaría o una anotación: flecha hacia el destino (con la brújula del
// reloj), anillo de brújula alrededor y distancia en línea recta. ARRIBA/ABAJO pasan al anterior o
// siguiente de la lista; BACK vuelve. El GPS se enciende al mostrarla y se apaga al ocultarla, como
// la vista de la calle.
class VistaIr extends WatchUi.View {
    private var _lista as Array<Array>;     // la de Ir.cercanos(): [nombre, dirección, lat, lon, tipo, m],
                                            // o la de Ir.deNotas(), con el rótulo y el seq detrás
    private var _i as Number;
    private var _lat as Double or Null = null;
    private var _lon as Double or Null = null;
    private var _info as Position.Info or Null = null;
    private var _timer as Timer.Timer or Null = null;
    private var _fDist as Graphics.FontType = Graphics.FONT_LARGE;
    private var _fNombre as Graphics.FontType = Graphics.FONT_SMALL;

    function initialize(lista as Array<Array>, i as Number, lat as Double or Null, lon as Double or Null) {
        View.initialize();
        _lista = lista;
        _i = i;
        _lat = lat;
        _lon = lon;
    }

    function onLayout(dc as Graphics.Dc) as Void {
        var v = Fuentes.vectorial(38);
        _fDist = v != null ? v : Graphics.FONT_LARGE;
        var n = Fuentes.vectorial(26);
        _fNombre = n != null ? n : Graphics.FONT_SMALL;
    }

    function onShow() as Void {
        Gps.arrancar(method(:onPosition));
        var t = new Timer.Timer();
        t.start(method(:onTick), 500, true);   // la brújula gira aunque el GPS no traiga nada nuevo
        _timer = t;
    }

    function onHide() as Void {
        Gps.parar();
        var t = _timer;
        if (t != null) {
            t.stop();
        }
        _timer = null;
    }

    function onPosition(info as Position.Info) as Void {
        var p = info.position;
        if (p != null && info.accuracy != Position.QUALITY_NOT_AVAILABLE) {
            var d = p.toDegrees();
            _lat = d[0].toDouble();
            _lon = d[1].toDouble();
        }
        _info = info;
        WatchUi.requestUpdate();
    }

    function onTick() as Void {
        WatchUi.requestUpdate();
    }

    function mover(paso as Number) as Void {
        var n = _lista.size();
        _i = ((_i + paso) % n + n) % n;
        WatchUi.requestUpdate();
    }

    // Con el anillo (source/Anillo.mc), todo el texto va dentro de L.ANILLO_RI: la hora, el rótulo, el
    // nombre, la flecha, la distancia, la dirección y el pie con el cardinal.
    function onUpdate(dc as Graphics.Dc) as Void {
        var cx = dc.getWidth() / 2;
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
        dc.clear();
        var e = _lista[_i];
        var tipo = e[4] as Number;
        var color = Ir.color(tipo);
        var lat = _lat;
        var lon = _lon;
        var o = Ir.orientacion(_info);
        var m = 0.0;
        var r = 0.0;
        var hay = lat != null && lon != null;
        if (lat != null && lon != null) {
            m = Ir.distancia(lat, lon, e[2] as Double, e[3] as Double);
            r = Ir.rumbo(lat, lon, e[2] as Double, e[3] as Double);
        }
        // El anillo, debajo de todo. La bola del destino, solo con posición y antes de llegar.
        Anillo.dibujar(dc, o, hay && m >= Ir.LLEGADA_M ? r : null, color, Ir.colorOscuro(tipo));

        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, 30, Graphics.FONT_XTINY, Fmt.reloj() + "  " + (_i + 1) + "/" + _lista.size(),
            Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        // El rótulo: el tipo, o «ANOTACIÓN · 21:15» (Ir.deNotas).
        linea(dc, e.size() > 6 ? e[6] as String : Ir.etiquetaTipo(tipo), 52, color);
        // El nombre, en dos líneas si hace falta (los de los hospitales son largos).
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        var aw = Texto.anchoR(dc, 60, 112, L.ANILLO_RI, 4);
        dc.drawText(cx, 86, _fNombre, Graphics.fitTextToArea(Abrev.corta(e[0] as String), _fNombre, aw,
            2 * dc.getFontHeight(_fNombre), true), Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);

        if (!hay) {
            dc.setColor(Graphics.COLOR_YELLOW, Graphics.COLOR_TRANSPARENT);
            dc.drawText(cx, 154, Graphics.FONT_SMALL, "BUSCANDO GPS", Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
            linea(dc, Abrev.corta(e[1] as String), 226, Graphics.COLOR_LT_GRAY);
            return;
        }
        if (m >= Ir.LLEGADA_M) {
            // Con brújula, la flecha es relativa a donde mira el reloj; sin ella, norte arriba.
            flecha(dc, cx, 154, o != null ? r - o : r, color);
        } else {
            dc.setColor(Graphics.COLOR_GREEN, Graphics.COLOR_TRANSPARENT);
            dc.drawText(cx, 154, Graphics.FONT_MEDIUM, "HA LLEGADO", Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        }
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, 200, _fDist, Ir.texto(m), Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        linea(dc, Abrev.corta(e[1] as String), 226, Graphics.COLOR_LT_GRAY);
        // Abajo el anillo deja poco ancho: si no cabe entero, se acorta antes de perder el cardinal.
        var card = Ir.cardinal(r);
        var pies = o == null ? ["norte arriba · " + card, card] : ["línea recta · " + card, "recta · " + card, card];
        var pw = Texto.anchoR(dc, 245 - 9, 245 + 9, L.ANILLO_RI, 4);
        var k = 0;
        while (k < pies.size() - 1 && dc.getTextWidthInPixels(pies[k] as String, Graphics.FONT_XTINY) > pw) {
            k++;
        }
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, 245, Graphics.FONT_XTINY, pies[k] as String, Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    // Una línea XTINY centrada en y, recortada al ancho que deja el anillo.
    private function linea(dc as Graphics.Dc, txt as String, y as Number, color as Number) as Void {
        if (txt.length() == 0) {
            return;
        }
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        var aw = Texto.anchoR(dc, y - 9, y + 9, L.ANILLO_RI, 4);
        dc.drawText(dc.getWidth() / 2, y, Graphics.FONT_XTINY,
            Graphics.fitTextToArea(txt, Graphics.FONT_XTINY, aw, 24, true),
            Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    // Flecha centrada en (cx, cy) que apunta al ángulo a (radianes, 0 = arriba, horario).
    private function flecha(dc as Graphics.Dc, cx as Number, cy as Number, a as Float, color as Number) as Void {
        var forma = [[0, -40], [27, 22], [0, 9], [-27, 22]] as Array<Array<Number>>;
        var c = Math.cos(a);
        var s = Math.sin(a);
        var pts = [] as Array<[Numeric, Numeric]>;
        for (var k = 0; k < forma.size(); k++) {
            var x = forma[k][0];
            var y = forma[k][1];
            pts.add([cx + x * c - y * s, cy + x * s + y * c]);
        }
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon(pts);
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(2);
        for (var k = 0; k < pts.size(); k++) {
            var p = pts[k];
            var q = pts[(k + 1) % pts.size()];
            dc.drawLine(p[0], p[1], q[0], q[1]);
        }
        dc.setPenWidth(1);
    }
}

class DelegadoIr extends WatchUi.BehaviorDelegate {
    private var _vista as VistaIr;

    function initialize(vista as VistaIr) {
        BehaviorDelegate.initialize();
        _vista = vista;
    }

    function onNextPage() as Boolean {
        _vista.mover(1);
        return true;
    }

    function onPreviousPage() as Boolean {
        _vista.mover(-1);
        return true;
    }
}
