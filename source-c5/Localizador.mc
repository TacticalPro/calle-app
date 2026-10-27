import Toybox.Lang;
import Toybox.Position;
import Toybox.System;
import Toybox.Time;

// De la posición al Modelo: decide cuándo recalcular, qué tesela tener cargada,
// y aplica la histéresis y la regla de ambigüedad sobre lo que da el Buscador.
//
// Versión de la c5 para Calles A Coruña (plan 4, palanca 1, 2026-10-27; tools/catalogo.json → "c5_fuentes"): la
// compila en lugar de source/Localizador.mc. Lo único distinto es la zona. En el fēnix 5 no caben a la vez la tesela
// y la carga de una zona (medido con la app real: tesela + 2 × zona ≤ 46 KB), y con zonas pequeñas A Coruña no cabe en
// 250 recursos. Aquí la zona se consulta con la tesela soltada (pico: el mayor de 2 × tesela y 2 × zona), y solo al
// moverse ZONA_PASO_M desde la consulta anterior, al cambiar de región o al forzar; entre medias se repite la última
// respuesta. La calle y el tramo salen siempre de la tesela, en cada posición; parroquia y lugar pueden ir hasta
// ZONA_PASO_M por detrás (la celda del raster es de 100 m). Todo pasa en el mismo evento: la vista no ve el hueco.
class Localizador {
    const ZONA_PASO_M = 100.0;
    var modelo as Modelo;
    private var _t as Tesela or Null = null;
    private var _reg as Number = 0;      // región de la tesela cargada (Callejero.ID)
    private var _x as Float = -1.0e6;
    private var _y as Float = -1.0e6;
    private var _ms as Number = 0;
    private var _zr as Array<String or Null> or Null = null;   // última respuesta de Zonas.consultar
    private var _zx as Float = -1.0e6;   // dónde se pidió
    private var _zy as Float = -1.0e6;
    private var _zreg as Number = 0;     // y en qué región

    function initialize(m as Modelo) {
        modelo = m;
    }

    function onPosition(info as Position.Info) as Void {
        procesar(info, false, false);
    }

    // Al abrir la app: la última posición conocida, si es reciente, mientras llega una nueva.
    function sembrar() as Void {
        var info = Position.getInfo();
        var w = info.when;
        if (info.position != null && w != null && Time.now().value() - w.value() <= L.SEMILLA_MAX_S) {
            procesar(info, true, true);
        }
    }

    // START o toque: recalcular ya, sin esperar al umbral de distancia o tiempo.
    function forzar() as Void {
        procesar(Position.getInfo(), true, false);
    }

    function procesar(info as Position.Info, forzado as Boolean, semilla as Boolean) as Void {
        var pos = info.position;
        if (pos == null || info.accuracy == Position.QUALITY_NOT_AVAILABLE) {
            return;
        }
        var deg = pos.toDegrees();
        var w = info.when;
        actualizar(deg[0].toDouble(), deg[1].toDouble(), info.accuracy as Number,
            w != null ? w.value() : Time.now().value(), forzado, semilla);
    }

    // Separado de Position para poder probarlo con posiciones inventadas.
    function actualizar(lat as Double, lon as Double, calidad as Number, tFix as Number,
            forzado as Boolean, semilla as Boolean) as Void {
        var m = modelo;
        // Región: en automática puede cambiar con la posición; la tesela cargada solo vale en la suya.
        var cambia = Activa.paraPosicion(lat, lon) || calidad != m.calidad || semilla != m.semilla;
        if (_t != null && _reg != Callejero.ID) {
            _t = null;
        }
        m.lat = lat;
        m.lon = lon;
        m.calidad = calidad;
        m.radio = L.radio(calidad);
        m.tFix = tFix;
        m.semilla = semilla;
        var p = Geo.xy(lat, lon);
        var x = p[0];
        var y = p[1];
        var ahora = System.getTimer();
        var dx = x - _x;
        var dy = y - _y;
        if (!forzado && !cambia && m.estado != EST_BUSCANDO
                && dx * dx + dy * dy < L.MOVER_M * L.MOVER_M && ahora - _ms < L.CADA_MS) {
            return;
        }
        _x = x;
        _y = y;
        _ms = ahora;
        var t0 = System.getTimer();
        var t = _t;
        if (t == null || !t.cubre(x, y)) {
            var i = Geo.celda(x, y);
            if (i < 0) {
                _t = null;
                m.limpiar();
                m.estado = EST_FUERA;
                m.tesela = -1;
                return;
            }
            if (t == null || t.idx != i) {
                _t = null;   // soltar la anterior antes de cargar: nunca dos en memoria
                t = null;
                Zonas.soltar();   // ni la zona: se vuelve a cargar después, y es pequeña
                t = Teselas.cargar(i);
                _t = t;
                _reg = Callejero.ID;
            }
            if (t == null) {
                m.limpiar();
                m.estado = EST_LEJOS;
                m.tesela = i;
            }
        }
        if (t != null) {
            calcularEn(t, x, y);
        }
        var zx = x - _zx;
        var zy = y - _zy;
        if (forzado || _zreg != Callejero.ID || zx * zx + zy * zy >= ZONA_PASO_M * ZONA_PASO_M) {
            // Se suelta la tesela, se consulta la zona sola, se suelta la zona y se vuelve a cargar la tesela.
            var ti = t != null ? t.idx : -1;
            _t = null;
            t = null;
            _zr = Zonas.consultar(x, y);
            Zonas.soltar();
            _zx = x;
            _zy = y;
            _zreg = Callejero.ID;
            if (ti >= 0) {
                _t = Teselas.cargar(ti);
            }
        }
        var z = _zr;
        if (z != null) {
            m.parroquia = z[0];
            m.lugar = z[1];
            m.barrio = z[2];
        }
        m.ms = System.getTimer() - t0;
    }

    // Suelta la tesela y la zona (la lista de hospitales y comisarías las necesita en los relojes de 128 KB).
    // La siguiente posición, o forzar() al volver a la vista, las vuelve a cargar.
    function soltar() as Void {
        _t = null;
        Zonas.soltar();
        _zreg = 0;   // al volver, la zona se consulta otra vez
    }

    // La búsqueda sobre una tesela ya elegida (los tests la llaman con teselas sintéticas).
    function calcularEn(t as Tesela, x as Float, y as Float) as Void {
        var m = modelo;
        var s = Buscador.buscar(t, x, y);
        var a = s[0];
        var b = s[1];
        if (a < 0 || t.mejor[a] > Callejero.MAXD) {
            m.limpiar();
            m.estado = EST_LEJOS;
            m.tesela = t.idx;
            return;
        }
        // Histéresis: la calle que ya se ve se queda si la nueva no la mejora en más de HISTERESIS_M.
        var mostrada = m.calle1;
        if (mostrada != null && !t.nombre(a).equals(mostrada)) {
            var k = t.indiceDe(mostrada);
            if (k >= 0 && t.mejor[k] <= t.mejor[a] + L.HISTERESIS_M) {
                b = a;
                a = k;
            }
        }
        var r = new Resultado();
        Buscador.rellenar(r, t, a, b, x, y);
        m.limpiar();
        m.estado = EST_OK;
        m.tesela = t.idx;
        m.calle1 = r.calle1;
        m.num1 = r.num1;
        m.aprox1 = r.num1 != null && r.dn1 > L.PORTAL_APROX;
        m.d1 = r.d1;
        // Tramo: A primero; un solo lado, o el mismo nombre a los dos (una calle en U), es «cerca de A».
        var ta = r.tramoA;
        var tb = r.tramoB;
        if (ta == null) {
            ta = tb;
            tb = null;
        }
        if (ta != null && tb != null && ta.equals(tb)) {
            tb = null;
        }
        m.tramoA = ta;
        m.tramoB = tb;
        if (r.calle2 != null) {
            m.d2 = r.d2;
            var margen = m.radio * L.AMBIG_FACTOR;
            if (margen < L.AMBIG_MIN_M) {
                margen = L.AMBIG_MIN_M;
            }
            var dif = r.d2 - r.d1;
            if (dif < 0.0) {
                dif = -dif;
            }
            if (dif < margen) {
                m.calle2 = r.calle2;
                m.num2 = r.num2;
                m.aprox2 = r.num2 != null && r.dn2 > L.PORTAL_APROX;
                m.cruce = r.d1 < L.CRUCE_M && r.d2 < L.CRUCE_M;
            }
        }
    }
}
