import Toybox.Attention;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Position;
import Toybox.System;
import Toybox.Time;
import Toybox.Timer;
import Toybox.WatchUi;

enum Pagina {
    PAG_CALLE,
    PAG_DETALLE   // para la prueba de campo: coordenadas, UTM, distancias, tesela, tiempos
}

// Pantalla principal, con las cotas de la de 280×280 escaladas por L.y() (source/L.mc). El GPS se enciende al mostrarla y se apaga al ocultarla.
// La maquetación del nombre solo se recalcula cuando cambia lo que se pinta.
class VistaCalle extends WatchUi.View {
    private var _m as Modelo;
    private var _loc as Localizador;
    private var _timer as Timer.Timer or Null = null;
    private var _pag as Pagina = PAG_CALLE;

    private var _fGrande as Array = [] as Array;   // cadena de fuentes para una calle
    private var _fMedia as Array = [] as Array;    // para dos calles y para el lugar
    private var _fNum as Graphics.FontType = Graphics.FONT_MEDIUM;
    private var _fHora as Graphics.FontType = Graphics.FONT_NUMBER_MILD;
    // Lo que la XTINY del reloj pasa de la proporcional (19 px en 280): las fuentes de sistema no escalan con
    // la pantalla (26 px en el fēnix 5 de 240, 37 en el 8 de 454). Las pilas de líneas pequeñas se abren tanto.
    private var _ex as Number = 0;

    // Caché de maquetación: clave = lo que cambia la maquetación.
    private var _clave as String = "";
    private var _cajas as Array = [] as Array;     // por nombre: [fuente, líneas, top, alto de línea] o null

    // Aviso de 2 s («Anotado 23:41») encima de todo.
    private var _aviso as String or Null = null;
    private var _avisoColor as Number = Graphics.COLOR_GREEN;
    private var _avisoTimer as Timer.Timer or Null = null;

    function initialize(m as Modelo, loc as Localizador) {
        View.initialize();
        _m = m;
        _loc = loc;
    }

    function onLayout(dc as Graphics.Dc) as Void {
        L.escalar(dc);
        var f = Fuentes.calle(dc);
        _fGrande = f[0] as Array;
        _fMedia = f[1] as Array;
        _fNum = f[2] as Graphics.FontType;
        _fHora = Fuentes.hora(dc);
        var hx = dc.getFontHeight(Graphics.FONT_XTINY);
        _ex = hx > L.y(19) ? hx - L.y(19) : 0;
        _clave = "";
    }

    function onShow() as Void {
        if (_m.estado == EST_BUSCANDO) {
            _loc.sembrar();
        } else {
            _loc.forzar();   // al volver del menú: la zona puede haber cambiado
        }
        Gps.arrancar(method(:onPosition));
        var t = new Timer.Timer();
        t.start(method(:onTick), 1000, true);   // reloj y edad del dato aunque el GPS calle
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
        _loc.onPosition(info);
        WatchUi.requestUpdate();
    }

    function onTick() as Void {
        WatchUi.requestUpdate();
    }

    function forzar() as Void {
        _loc.forzar();
        WatchUi.requestUpdate();
    }

    // START: recalcula con la última posición y guarda lo que se ve. Vibra y avisa 2 s.
    function anotar() as Void {
        _loc.forzar();
        var m = _m;
        var hay = m.estado != EST_BUSCANDO;
        var r = Notas.anotar(Time.now().value(), Notas.texto(m), hay ? m.lat : null, hay ? m.lon : null);
        if (Attention has :vibrate) {
            Attention.vibrate([new Attention.VibeProfile(100, L.VIBRA_MS)] as Array<Attention.VibeProfile>);
        }
        if (r == NOTA_OK) {
            avisar("Anotado " + Fmt.reloj(), Graphics.COLOR_GREEN);
        } else if (r == NOTA_LLENAS) {
            avisar("Anotaciones llenas (" + L.NOTAS_MAX + ")", Graphics.COLOR_YELLOW);
        } else {
            avisar("No se ha podido guardar", Graphics.COLOR_RED);
        }
    }

    function avisar(txt as String, color as Number) as Void {
        _aviso = txt;
        _avisoColor = color;
        var t = _avisoTimer;
        if (t != null) {
            t.stop();
        }
        t = new Timer.Timer();
        t.start(method(:onFinAviso), L.AVISO_MS, false);
        _avisoTimer = t;
        WatchUi.requestUpdate();
    }

    function onFinAviso() as Void {
        _aviso = null;
        _avisoTimer = null;
        WatchUi.requestUpdate();
    }

    function cambiarPagina() as Void {
        _pag = _pag == PAG_CALLE ? PAG_DETALLE : PAG_CALLE;
        WatchUi.requestUpdate();
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
        dc.clear();
        dibujarEstado(dc);
        if (_pag == PAG_DETALLE) {
            dibujarDetalle(dc);
        } else {
            var m = _m;
            if (m.estado == EST_BUSCANDO) {
                aviso(dc, "BUSCANDO GPS", Graphics.COLOR_YELLOW, "Mejor con cielo despejado");
            } else if (m.estado == EST_FUERA) {
                aviso(dc, "FUERA DE ZONA", Graphics.COLOR_RED, "Callejero: " + Callejero.ETIQUETA
                    + (Ajustes.zona() == Ajustes.AUTO ? "" : " (fijo)"));
                pie(dc, Utm.texto(m.lat, m.lon), Graphics.COLOR_LT_GRAY, L.y(236));
            } else if (m.estado == EST_LEJOS) {
                dibujarLejos(dc);
            } else if (m.calle2 != null && !m.cruce) {
                dibujarDos(dc);
            } else {
                dibujarUna(dc);
            }
        }
        dibujarAviso(dc);
    }

    // Fila superior: la hora en grande (la app hace también de reloj) con el punto de
    // calidad del GPS a su izquierda. Si el dato es viejo, su edad va debajo, en amarillo, en lugar
    // del barrio.
    private function dibujarEstado(dc as Graphics.Dc) as Void {
        var m = _m;
        var cx = dc.getWidth() / 2;
        var txt = Fmt.reloj();
        var w = dc.getTextWidthInPixels(txt, _fHora);
        var punto = L.y(L.HORA_PUNTO);
        var x0 = cx - (w + punto) / 2;
        var hy = L.y(L.HORA_Y);
        dc.setColor(colorCalidad(m), Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(x0 + L.y(6), hy, L.y(6));
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x0 + punto, hy, _fHora, txt, Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER);
        if (viejo() && _pag == PAG_CALLE) {
            linea(dc, L.y(L.SUB_Y), Fmt.edad(m.edad()), Graphics.COLOR_YELLOW);
        }
    }

    private function viejo() as Boolean {
        return _m.estado != EST_BUSCANDO && (_m.semilla || _m.edad() > L.VIEJA_S);
    }

    // El barrio (o, sin calle, nada) va bajo la hora salvo que el dato sea viejo: entonces va su edad.
    private function hayBarrio() as Boolean {
        return _m.barrio != null && !viejo();
    }

    private function colorCalidad(m as Modelo) as Number {
        if (m.estado == EST_BUSCANDO || m.semilla) {
            return Graphics.COLOR_RED;
        } else if (m.calidad >= Position.QUALITY_GOOD) {
            return Graphics.COLOR_GREEN;
        } else if (m.calidad == Position.QUALITY_USABLE) {
            return Graphics.COLOR_YELLOW;
        }
        return Graphics.COLOR_ORANGE;
    }

    private function colorTexto() as Number {
        return _m.semilla || _m.edad() > L.VIEJA_S ? Graphics.COLOR_LT_GRAY : Graphics.COLOR_WHITE;
    }

    // Franjas del nombre: la hora y el barrio encima y el tramo debajo se las comen. Con tramo, el
    // número sube y el tramo va en la franja ancha (y 190-212): abajo, la pantalla redonda lo cortaba.
    private function franjaUna() as Array<Number> {
        return [topNombre(hayBarrio() || viejo()), _m.tramoA != null ? L.y(146) - _ex : L.y(192)] as Array<Number>;
    }

    // Arriba de la franja del nombre: con la línea pequeña bajo la hora, baja lo que esta crece.
    private function topNombre(conSub as Boolean) as Number {
        return conSub ? L.y(L.NOMBRE_Y_SUB) + _ex / 2 : L.y(L.NOMBRE_Y);
    }

    // Con dos calles no hay barrio; con el dato viejo, su edad baja la primera.
    private function topDos() as Number {
        return topNombre(viejo());
    }

    private function franjaCruce() as Array<Number> {
        return [topNombre(hayBarrio() || viejo()), L.y(168) - _ex] as Array<Number>;
    }

    private function maquetar(dc as Graphics.Dc) as Void {
        var m = _m;
        // Esquina y dos calles maquetan distinto; barrio y tramo cambian la franja; el lugar es otro título.
        var clave = m.estado + "|" + m.calle1 + "|" + m.calle2 + "|" + m.cruce + "|" + (hayBarrio() || viejo())
            + "|" + (m.tramoA != null) + "|" + m.lugar;
        if (clave.equals(_clave)) {
            return;
        }
        _clave = clave;
        if (m.estado == EST_LEJOS) {
            _cajas = [m.lugar != null ? Texto.colocar(dc, m.lugar as String, _fMedia, 2, L.y(86), L.y(146)) : null];
        } else if (m.calle2 == null) {
            var f = franjaUna();
            _cajas = [Texto.colocar(dc, m.calle1 as String, _fGrande, 3, f[0], f[1])];
        } else if (m.cruce) {
            var f = franjaCruce();
            _cajas = [Texto.colocar(dc, m.calle1 as String, _fGrande, 3, f[0], f[1])];
        } else {
            _cajas = [Texto.colocar(dc, m.calle1 as String, _fMedia, 2, topDos(), L.y(116)),
                      Texto.colocar(dc, m.calle2 as String, _fMedia, 2, L.y(152), L.y(214) - _ex)];
        }
    }

    // Pinta una caja de Texto.colocar; si no cupo, el nombre recortado en una línea.
    private function pintarCaja(dc as Graphics.Dc, caja as Array or Null, nombre as String, y0 as Number, y1 as Number) as Void {
        var cx = dc.getWidth() / 2;
        if (caja == null) {
            var w = Texto.ancho(dc, y0, y1, 12);
            var s = Graphics.fitTextToArea(Abrev.corta(nombre), Graphics.FONT_TINY, w, y1 - y0, true);
            dc.drawText(cx, (y0 + y1) / 2, Graphics.FONT_TINY, s, Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
            return;
        }
        var f = caja[0] as Graphics.FontType;
        var lineas = caja[1] as Array<String>;
        var top = caja[2] as Number;
        var lh = caja[3] as Number;
        for (var i = 0; i < lineas.size(); i++) {
            dc.drawText(cx, top + i * lh, f, lineas[i], Graphics.TEXT_JUSTIFY_CENTER);
        }
    }

    // Una línea pequeña recortada al ancho de la pantalla redonda en esa altura. La XTINY de los fēnix 5
    // es más alta que la cota (26 px en 240): la franja y el área crecen con ella, o fitTextToArea la vacía.
    private function linea(dc as Graphics.Dc, y as Number, txt as String, color as Number) as Void {
        var h = dc.getFontHeight(Graphics.FONT_XTINY);
        var med = L.y(11) > h / 2 ? L.y(11) : h / 2;
        var w = Texto.ancho(dc, y - med, y + med, 10);
        var alto = L.y(24) > h + 4 ? L.y(24) : h + 4;
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(dc.getWidth() / 2, y, Graphics.FONT_XTINY, Graphics.fitTextToArea(txt, Graphics.FONT_XTINY, w, alto, true),
            Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    // Una calle (con barrio encima y tramo debajo); en una esquina, "esq. <la otra>" debajo del número.
    private function dibujarUna(dc as Graphics.Dc) as Void {
        var m = _m;
        var cx = dc.getWidth() / 2;
        maquetar(dc);
        if (hayBarrio()) {
            linea(dc, L.y(L.SUB_Y), m.barrio as String, Graphics.COLOR_LT_GRAY);
        }
        dc.setColor(colorTexto(), Graphics.COLOR_TRANSPARENT);
        if (!m.cruce) {
            var f = franjaUna();
            pintarCaja(dc, _cajas[0], m.calle1 as String, f[0], f[1]);
            var tramo = m.tramoA != null;
            if (m.num1 != null) {
                dc.drawText(cx, f[1] + L.y(tramo ? 4 : 8), _fNum, Fmt.numero(m.num1 as String, m.aprox1),
                    Graphics.TEXT_JUSTIFY_CENTER);
            }
            if (tramo) {
                if (m.tramoB != null) {
                    linea(dc, L.y(212) - L.y(22) - _ex, "entre " + Abrev.corta(m.tramoA as String), Graphics.COLOR_LT_GRAY);
                    linea(dc, L.y(212), "y " + Abrev.corta(m.tramoB as String), Graphics.COLOR_LT_GRAY);
                } else {
                    linea(dc, L.y(212) - L.y(22) - _ex, "cerca de " + Abrev.corta(m.tramoA as String), Graphics.COLOR_LT_GRAY);
                }
            }
            return;
        }
        var f = franjaCruce();
        pintarCaja(dc, _cajas[0], m.calle1 as String, f[0], f[1]);
        if (m.num1 != null) {
            dc.drawText(cx, L.y(170) - _ex, _fNum, Fmt.numero(m.num1 as String, m.aprox1), Graphics.TEXT_JUSTIFY_CENTER);
        }
        linea(dc, L.y(221), "esq. " + Abrev.corta(m.calle2 as String), colorTexto());
        pie(dc, "CRUCE", Graphics.COLOR_YELLOW, L.y(252));
    }

    private function dibujarDos(dc as Graphics.Dc) as Void {
        var m = _m;
        var cx = dc.getWidth() / 2;
        maquetar(dc);
        dc.setColor(colorTexto(), Graphics.COLOR_TRANSPARENT);
        pintarCaja(dc, _cajas[0], m.calle1 as String, topDos(), L.y(116));
        if (m.num1 != null) {
            dc.drawText(cx, L.y(117), Graphics.FONT_XTINY, Fmt.numero(m.num1 as String, m.aprox1), Graphics.TEXT_JUSTIFY_CENTER);
        }
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawLine(cx - L.y(90), L.y(146), cx + L.y(90), L.y(146));
        dc.setColor(colorTexto(), Graphics.COLOR_TRANSPARENT);
        pintarCaja(dc, _cajas[1], m.calle2 as String, L.y(152), L.y(214) - _ex);
        if (m.num2 != null) {
            dc.drawText(cx, L.y(215) - _ex, Graphics.FONT_XTINY, Fmt.numero(m.num2 as String, m.aprox2), Graphics.TEXT_JUSTIFY_CENTER);
        }
        pie(dc, "DOS CALLES", Graphics.COLOR_YELLOW, L.y(252));
    }

    // Sin calle a MAXD: el lugar de título (o SIN CALLE), la parroquia (o el barrio, en Madrid)
    // debajo y la UTM al pie.
    private function dibujarLejos(dc as Graphics.Dc) as Void {
        var m = _m;
        var sub = m.parroquia != null ? "parroquia de " + m.parroquia
            : (m.barrio != null ? m.barrio as String : "a menos de " + Callejero.MAXD + " m");
        if (m.lugar == null) {
            aviso(dc, "SIN CALLE", Graphics.COLOR_WHITE, sub);
        } else {
            maquetar(dc);
            if (!viejo()) {
                linea(dc, L.y(L.SUB_Y), "sin calle a " + Callejero.MAXD + " m", Graphics.COLOR_YELLOW);
            }
            dc.setColor(colorTexto(), Graphics.COLOR_TRANSPARENT);
            pintarCaja(dc, _cajas[0], m.lugar as String, L.y(86), L.y(146));
            linea(dc, L.y(164), sub, Graphics.COLOR_LT_GRAY);
        }
        pie(dc, Utm.texto(m.lat, m.lon), Graphics.COLOR_LT_GRAY, L.y(236));
    }

    private function aviso(dc as Graphics.Dc, titulo as String, color as Number, sub as String) as Void {
        var cx = dc.getWidth() / 2;
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, L.y(112), _fMedia[0] as Graphics.FontType, titulo, Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        linea(dc, L.y(152), sub, Graphics.COLOR_LT_GRAY);
    }

    // Al pie, centrado en y; si ahí la pantalla redonda lo corta (la UTM en los relojes pequeños), sube hasta caber.
    private function pie(dc as Graphics.Dc, txt as String, color as Number, y as Number) as Void {
        var h = dc.getFontHeight(Graphics.FONT_XTINY);
        var w = dc.getTextWidthInPixels(txt, Graphics.FONT_XTINY);
        while (y > dc.getHeight() / 2 && Texto.ancho(dc, y - h / 2, y + h / 2, 4) < w) {
            y -= 2;
        }
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);

        dc.drawText(dc.getWidth() / 2, y, Graphics.FONT_XTINY, txt, Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    private function dibujarAviso(dc as Graphics.Dc) as Void {
        var txt = _aviso;
        if (txt == null) {
            return;
        }
        var w = dc.getWidth();
        var x = L.y(24);
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_TRANSPARENT);
        dc.fillRoundedRectangle(x, L.y(108), w - 2 * x, L.y(64), L.y(12));
        dc.setColor(_avisoColor, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(L.y(3));
        dc.drawRoundedRectangle(x, L.y(108), w - 2 * x, L.y(64), L.y(12));
        dc.setPenWidth(1);
        dc.drawText(w / 2, L.y(140), Graphics.FONT_SMALL,
            Graphics.fitTextToArea(txt as String, Graphics.FONT_SMALL, w - L.y(64), L.y(56), true),
            Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    private function dibujarDetalle(dc as Graphics.Dc) as Void {
        var m = _m;
        var cx = dc.getWidth() / 2;
        var st = System.getSystemStats();
        var nombres = ["—", "conocida", "mala", "usable", "buena"] as Array<String>;
        var sin = m.estado == EST_BUSCANDO;
        var lineas = [
            sin ? "sin posición" : Fmt.grados(m.lat, m.lon),
            sin ? "" : Utm.texto(m.lat, m.lon),
            "GPS " + (m.calidad < nombres.size() ? nombres[m.calidad] : "?") + " · ±" + m.radio + " m",
            "d1 " + m.d1.format("%.1f") + " m   d2 " + m.d2.format("%.1f") + " m",
            "tesela t" + m.tesela + "   " + m.ms + " ms",
            "memoria " + (st.usedMemory / 1024) + "/" + (st.totalMemory / 1024) + " KB",
            Callejero.ETIQUETA + (Ajustes.zona() == Ajustes.AUTO ? " (auto)" : " (fija)") + " · " + Callejero.DATOS
        ] as Array<String>;
        var paso = L.y(26) > dc.getFontHeight(Graphics.FONT_XTINY) ? L.y(26) : dc.getFontHeight(Graphics.FONT_XTINY);
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        for (var i = 0; i < lineas.size(); i++) {
            dc.drawText(cx, L.y(L.SUB_Y + 2) + i * paso,
 Graphics.FONT_XTINY, lineas[i], Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        }
    }
}
