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
    // Alturas de la guía, apiladas por el alto real de las fuentes (onLayout): [hora, rótulo, centro del
    // nombre, flecha, distancia, dirección, pie] y la escala de la flecha. En 280 con vectoriales son las
    // cotas de siempre (30, 52, 87, 156, 200, 226, 245).
    private var _y as Array<Number> = [30, 52, 87, 156, 200, 226, 245] as Array<Number>;
    private var _k as Float = 1.0;
    private var _lineas as Number = 2;      // del nombre

    function initialize(lista as Array<Array>, i as Number, lat as Double or Null, lon as Double or Null) {
        View.initialize();
        _lista = lista;
        _i = i;
        _lat = lat;
        _lon = lon;
    }

    function onLayout(dc as Graphics.Dc) as Void {
        L.escalar(dc);
        var v = Fuentes.vectorial(38);
        _fDist = v != null ? v : Graphics.FONT_LARGE;
        var n = Fuentes.nombre(25);   // Noto Sans, como el nombre de la calle (P73)
        _fNombre = n != null ? n : Graphics.FONT_SMALL;
        var hx = dc.getFontHeight(Graphics.FONT_XTINY);
        var nh = dc.getFontHeight(_fNombre);
        var dh = dc.getFontHeight(_fDist);
        var hora = L.y(30);
        var tipo = L.y(52) > hora + hx ? L.y(52) : hora + hx;
        var nombreTop = tipo + hx / 2;
        var pie = L.y(245);
        var dir = L.y(226) < pie - hx ? L.y(226) : pie - hx;
        var dist = dir - hx / 2 - dh / 2 + L.y(6);    // las cifras no bajan de la línea base: se puede montar
        dist = L.y(200) < dist ? L.y(200) : dist;
        // La flecha (de -40 a +22 en 280) entre el nombre y la distancia; si no cabe, se encoge. Antes de bajar
        // del 70 %, el nombre pasa a una línea (fēnix 5: su XTINY de 26 px se come la altura).
        var abajo = dist - dh / 2;
        _lineas = 2;
        var k = (abajo - nombreTop - 2 * nh - 4) / 62.0;
        if (k < 0.7 * L.S) {
            _lineas = 1;
            k = (abajo - nombreTop - nh - 4) / 62.0;
        }
        var arriba = nombreTop + _lineas * nh;
        _k = k < L.S ? k : L.S;
        _y = [hora, tipo, nombreTop + _lineas * nh / 2, (arriba + abajo) / 2 + (9 * _k).toNumber(), dist, dir, pie] as Array<Number>;
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
    // nombre, la flecha, la distancia, la dirección y el pie con el cardinal. Cotas de 280, escaladas con L.y().
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
        dc.drawText(cx, _y[0], Graphics.FONT_XTINY, Fmt.reloj() + "  " + (_i + 1) + "/" + _lista.size(),
            Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        // El rótulo: el tipo, o «ANOTACIÓN · 21:15» (Ir.deNotas).
        linea(dc, e.size() > 6 ? e[6] as String : Ir.etiquetaTipo(tipo), _y[1], color);
        // El nombre, en dos líneas si hace falta (los de los hospitales son largos).
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        var nh = dc.getFontHeight(_fNombre);
        var aw = Texto.anchoR(dc, _y[2] - _lineas * nh / 2, _y[2] + _lineas * nh / 2, L.y(L.ANILLO_RI), 4);
        var s = Abrev.corta(e[0] as String);
        var f = _fNombre;
        var t = Graphics.fitTextToArea(s, f, aw, _lineas * nh, true);
        // Si no cabe (fēnix 5 y 6: «Hospital Xeral…»), entero en la XTINY en esa misma altura; si tampoco, a trozos
        // que cambian cada 2 s: lo que dice qué hospital o qué comisaría tiene que leerse.
        if (t.find("…") != null) {
            var fx = Graphics.FONT_XTINY;
            var tx = Graphics.fitTextToArea(s, fx, aw, _lineas * nh, true);
            if (tx.find("…") == null) {
                f = fx;
                t = tx;
            } else {
                t = Graphics.fitTextToArea(Texto.trozo(dc, s, f, aw), f, aw, _lineas * nh, true);
            }
        }
        dc.drawText(cx, _y[2], f, t, Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);

        if (!hay) {
            dc.setColor(Graphics.COLOR_YELLOW, Graphics.COLOR_TRANSPARENT);
            dc.drawText(cx, _y[3], Graphics.FONT_SMALL, "BUSCANDO GPS", Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
            linea(dc, Abrev.corta(e[1] as String), _y[5], Graphics.COLOR_LT_GRAY);
            return;
        }
        if (m >= Ir.LLEGADA_M) {
            // Con brújula, la flecha es relativa a donde mira el reloj; sin ella, norte arriba.
            flecha(dc, cx, _y[3], o != null ? r - o : r, color);
        } else {
            dc.setColor(Graphics.COLOR_GREEN, Graphics.COLOR_TRANSPARENT);
            dc.drawText(cx, _y[3], Graphics.FONT_MEDIUM, "HA LLEGADO", Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        }
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, _y[4], _fDist, Ir.texto(m), Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        linea(dc, Abrev.corta(e[1] as String), _y[5], Graphics.COLOR_LT_GRAY);
        // Abajo el anillo deja poco ancho: si no cabe entero, se acorta antes de perder el cardinal.
        var card = Ir.cardinal(r);
        var pies = o == null ? ["norte arriba · " + card, card] : ["línea recta · " + card, "recta · " + card, card];
        var hx = dc.getFontHeight(Graphics.FONT_XTINY);
        var pw = Texto.anchoR(dc, _y[6] - hx / 2, _y[6] + hx / 2, L.y(L.ANILLO_RI), 4);
        var k = 0;
        while (k < pies.size() - 1 && dc.getTextWidthInPixels(pies[k] as String, Graphics.FONT_XTINY) > pw) {
            k++;
        }
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, _y[6], Graphics.FONT_XTINY, pies[k] as String, Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    // Una línea XTINY centrada en y, recortada al ancho que deja el anillo.
    private function linea(dc as Graphics.Dc, txt as String, y as Number, color as Number) as Void {
        if (txt.length() == 0) {
            return;
        }
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        var h = dc.getFontHeight(Graphics.FONT_XTINY);
        var med = L.y(9) > h / 2 ? L.y(9) : h / 2;
        var aw = Texto.anchoR(dc, y - med, y + med, L.y(L.ANILLO_RI), 4);
        var alto = L.y(24) > h + 4 ? L.y(24) : h + 4;
        dc.drawText(dc.getWidth() / 2, y, Graphics.FONT_XTINY,
            Graphics.fitTextToArea(Texto.trozo(dc, txt, Graphics.FONT_XTINY, aw), Graphics.FONT_XTINY, aw, alto, true),
            Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    // Flecha centrada en (cx, cy) que apunta al ángulo a (radianes, 0 = arriba, horario).
    private function flecha(dc as Graphics.Dc, cx as Number, cy as Number, a as Float, color as Number) as Void {
        var forma = [[0, -40], [27, 22], [0, 9], [-27, 22]] as Array<Array<Number>>;
        var c = Math.cos(a);
        var s = Math.sin(a);
        var pts = [] as Array<[Numeric, Numeric]>;
        for (var k = 0; k < forma.size(); k++) {
            var x = forma[k][0] * _k;
            var y = forma[k][1] * _k;

            pts.add([cx + x * c - y * s, cy + x * s + y * c]);
        }
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon(pts);
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(L.y(2));
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
