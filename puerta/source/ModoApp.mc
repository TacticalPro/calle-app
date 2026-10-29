import Toybox.Graphics;
import Toybox.Lang;
import Toybox.StringUtil;
import Toybox.System;
import Toybox.Timer;
import Toybox.WatchUi;

// La puerta tiene dos modos (plan 2): tests (puerta/monkey.jungle, sin :modoapp) y app (puerta/app.jungle, sin
// :modotest). En modo app mide la memoria con el tope real de una watch-app del fēnix 5.

(:modotest)
function vistaInicial() as WatchUi.Views {
    return new WatchUi.View();
}

(:modoapp)
function vistaInicial() as WatchUi.Views {
    return new VistaPuerta();
}

(:modoapp)
class VistaPuerta extends WatchUi.View {
    var esc as Escenario or Null = null;

    function initialize() {
        View.initialize();
    }

    function onShow() as Void {
        if (esc == null) {
            esc = new Escenario();
            (esc as Escenario).empezar();
        }
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
        dc.clear();
    }
}

// Un paso por evento (temporizador), como la app real, que carga una tesela o una zona por evento.
(:modoapp)
class Escenario {
    // Lo que usa la app real al cargar una tesela: 65 KB medidos en el fēnix 6 con Madrid (especificación del
    // FORMATO 4, «Memoria»), más 1 KB por los índices más largos de Galicia (estimación).
    const USADA_APP = 66 * 1024;
    var lastre as Object or Null = null;    // un ByteArray, o con APP_FRAG un Array de ByteArray de 256 B
    var l0 as Number = 0;
    var l1 as Number = 0;
    var paso as Number = 0;
    var t as Tesela or Null = null;
    var otro as Object or Null = null;      // lo que se retiene aparte de t: la tesela F4 o los trozos
    var reloj as Timer.Timer = new Timer.Timer();

    function initialize() {
    }

    function usada() as Number {
        return System.getSystemStats().usedMemory;
    }

    function empezar() as Void {
        var u0 = usada();
        // La primera carga de un recurso retiene ~8,4 KB (medido en F4 y F5): la app real ya lo ha pagado al cargar
        // una tesela (fuentes, cadenas), así que forma parte de sus 65 KB. Se paga aquí, antes del lastre.
        var z = WatchUi.loadResource(PuertaDatos.zonas()[0]) as Array;
        z = null;
        var st = System.getSystemStats();
        System.println("APP total " + st.totalMemory + " B; usada " + u0 + " B al arrancar y " + st.usedMemory
            + " B tras el primer recurso; modo " + PuertaDatos.APP_MODO + (PuertaDatos.APP_FRAG ? " +frag" : ""));
        if (PuertaDatos.APP_MODO == 4) {
            // La primera conversión base64, pagada antes del lastre (como la retención del primer recurso).
            var u1 = usada();
            var b = convertir(PuertaDatos.B64_1K);
            var u2 = usada();
            b = null;
            System.println("APP b64 1 KB: " + (u2 - u1) + " B con el resultado; retenidos al soltarlo " + (usada() - u1) + " B");
        }
        var falta = USADA_APP - usada();
        if (!PuertaDatos.APP_FRAG) {
            lastre = falta > 0 ? new [falta]b : null;
        } else {
            var a = new [600];
            var n = 0;
            while (usada() < USADA_APP && n < 600) {
                a[n] = new [256]b;
                n++;
            }
            lastre = a;
            System.println("APP lastre en " + n + " trozos de 256 B");
        }
        l0 = Puerta.libre();
        System.println("APP lastre " + falta + " B; usada " + usada() + " B; libre " + l0 + " B (la app real: ~61 KB)");
        reloj.start(method(:siguiente), 400, true);
    }

    function convertir(s as String) as ByteArray {
        return StringUtil.convertEncodedString(s, {
            :fromRepresentation => StringUtil.REPRESENTATION_STRING_BASE64,
            :toRepresentation => StringUtil.REPRESENTATION_BYTE_ARRAY
        }) as ByteArray;
    }

    function cargar(k as Number) as Tesela {
        return new Tesela(k, Teselas.bytes(PuertaDatos.teselas()[k]), PuertaDatos.TESELAS_CAJA[k]);
    }

    // Modos (PuertaDatos.APP_MODO, lo fija tools/puerta_c5.py; el detalle, en su docstring).
    function siguiente() as Void {
        var m = PuertaDatos.APP_MODO;
        if (m == 0) {
            escalera();
        } else if (m == 3) {
            escaleraF4();
        } else if (m == 2 && paso == 0) {
            t = cargar(0);
            var c = PuertaDatos.TESELAS_CENTRO[0];
            Buscador.buscar(t as Tesela, c[0], c[1]);
            System.println("APP previa " + PuertaDatos.TESELAS_BYTES[0] + " B: OK, en reposo " + (l0 - Puerta.libre()) + " B");
            t = null;
            System.println("APP previa soltada: quedan " + (l0 - Puerta.libre()) + " B retenidos");
        } else if (m == 5) {
            hueco();
        } else if (m == 6) {
            modulos();
        } else if (m == 8 && paso == 0) {
            trozos();
        } else {
            teselaYZonas(m == 2 ? paso - 1 : paso);
        }
        paso++;
    }

    // Suelta la anterior y carga la siguiente, una por evento.
    function escalera() as Void {
        if (paso >= PuertaDatos.TESELAS_BYTES.size()) {
            fin();
            return;
        }
        t = null;
        System.println("APP tesela " + PuertaDatos.TESELAS_BYTES[paso] + " B: cargando (libre " + Puerta.libre() + " B)");
        t = cargar(paso);
        var c = PuertaDatos.TESELAS_CENTRO[paso];
        Buscador.buscar(t as Tesela, c[0], c[1]);
        var l = Puerta.libre();
        System.println("APP tesela " + PuertaDatos.TESELAS_BYTES[paso] + " B: OK, en reposo " + (l0 - l) + " B ("
            + (t as Tesela).nc + " calles), libre " + l + " B");
    }

    // Lo mismo que hace hoy la variante c: la tesela como array JSON, de menor a mayor heap estimado, una por evento.
    function escaleraF4() as Void {
        var rs = PuertaDatos.teselasF4();
        if (paso >= rs.size()) {
            fin();
            return;
        }
        System.println("APP f4 " + PuertaDatos.F4_EST[paso] + " B estimados: cargando (libre " + Puerta.libre() + " B)");
        var d = WatchUi.loadResource(rs[paso]) as Array;
        var l = Puerta.libre();
        System.println("APP f4 " + PuertaDatos.F4_EST[paso] + " B estimados: OK (" + d.size() + "), en reposo " + (l0 - l)
            + " B, libre " + l + " B");
        d = null;
    }

    // Paso 0, la tesela APP_TESELA (FORMATO 5; en f4z, la F4); después, las zonas de menor a mayor con ella cargada.
    function teselaYZonas(i as Number) as Void {
        var k = PuertaDatos.APP_TESELA;
        if (i == 0) {
            if (PuertaDatos.APP_MODO == 7) {
                System.println("APP f4 " + PuertaDatos.F4_EST[k] + " B estimados, primera: cargando (libre " + Puerta.libre() + " B)");
                otro = WatchUi.loadResource(PuertaDatos.teselasF4()[k]);
                l1 = Puerta.libre();
                System.println("APP f4 " + PuertaDatos.F4_EST[k] + " B estimados: en reposo " + (l0 - l1) + " B, libre " + l1 + " B");
                return;
            }
            System.println("APP tesela " + PuertaDatos.TESELAS_BYTES[k] + " B: cargando (libre " + Puerta.libre() + " B)");
            t = cargar(k);
            var c = PuertaDatos.TESELAS_CENTRO[k];
            Buscador.buscar(t as Tesela, c[0], c[1]);
            l1 = Puerta.libre();
            System.println("APP tesela " + PuertaDatos.TESELAS_BYTES[k] + " B: en reposo " + (l0 - l1) + " B, libre " + l1 + " B");
            return;
        }
        var zs = PuertaDatos.zonas();
        if (i - 1 >= zs.size()) {
            fin();
            return;
        }
        System.println("APP zona " + PuertaDatos.ZONAS_EST[i - 1] + " B: cargando");
        var z = WatchUi.loadResource(zs[i - 1]) as Array;
        var l3 = Puerta.libre();
        System.println("APP zona " + PuertaDatos.ZONAS_EST[i - 1] + " B: OK (" + z.size() + "), en reposo " + (l1 - l3)
            + " B, libre " + l3 + " B");
        z = null;
    }

    // El mayor ByteArray que se deja reservar: tras APP_TESELA teselas de la escalera (cargadas y soltadas), uno por
    // evento, de 16 KB en adelante de 1 KB en 1 KB. El primero que no cabe tumba la app: el mayor bloque es el anterior.
    function hueco() as Void {
        var j = PuertaDatos.APP_TESELA;
        if (paso < j) {
            t = cargar(paso);
            var c = PuertaDatos.TESELAS_CENTRO[paso];
            Buscador.buscar(t as Tesela, c[0], c[1]);
            t = null;
            System.println("APP hueco: tesela " + PuertaDatos.TESELAS_BYTES[paso] + " B cargada y soltada; libre " + Puerta.libre() + " B");
            return;
        }
        var n = 16384 + 1024 * (paso - j);
        var l = Puerta.libre();
        if (n > l) {
            System.println("APP hueco: " + n + " B pasa del libre (" + l + " B): todo el libre es contiguo");
            fin();
            return;
        }
        System.println("APP hueco " + n + " B: reservando (libre " + l + " B)");
        var b = new [n]b;
        System.println("APP hueco " + n + " B: OK");
        b = null;
    }

    // ¿La retención del primer recurso se paga por módulo? Ya se pagó con un jsonData (empezar); ahora un Rez.Strings
    // y otro jsonData distinto.
    function modulos() as Void {
        var u1 = usada();
        var s = WatchUi.loadResource(Rez.Strings.AppName);
        s = null;
        var u2 = usada();
        var z = WatchUi.loadResource(PuertaDatos.zonas()[1]);
        z = null;
        var u3 = usada();
        System.println("APP modulos: primer Rez.Strings retiene " + (u2 - u1) + " B; otro jsonData, " + (u3 - u2) + " B");
        fin();
    }

    // Salida C: t412 en 4 trozos. 1, convertidos y concatenados en un ByteArray (y la Tesela sobre él); 2, un
    // Array<ByteArray> (sin Tesela: el lector aún no indexa trozos); 3, los 4 en un solo jsonData, como en 1.
    function trozos() as Void {
        var v = PuertaDatos.APP_TESELA;
        var rs = PuertaDatos.trozos();
        var t0 = System.getTimer();
        System.println("APP trozos:" + v + ": cargando (libre " + Puerta.libre() + " B)");
        if (v == 2) {
            var a = [] as Array<ByteArray>;
            for (var k = 0; k < rs.size(); k++) {
                a.add(convertir(WatchUi.loadResource(rs[k]) as String));
            }
            otro = a;
        } else {
            var b = null as ByteArray or Null;
            var ss = v == 3 ? WatchUi.loadResource(Rez.JsonData.Trozos) as Array<String or Null> : null;
            for (var k = 0; k < rs.size(); k++) {
                var x;
                if (ss != null) {
                    x = convertir(ss[k] as String);
                    ss[k] = null;
                } else {
                    x = convertir(WatchUi.loadResource(rs[k]) as String);
                }
                if (b == null) {
                    b = x;
                } else {
                    b.addAll(x);
                }
                x = null;
            }
            ss = null;
            t = new Tesela(0, b as ByteArray, PuertaDatos.CAJA);
            Buscador.buscar(t as Tesela, PuertaDatos.CENTRO[0], PuertaDatos.CENTRO[1]);
        }
        l1 = Puerta.libre();
        System.println("APP trozos:" + v + ": OK en " + (System.getTimer() - t0) + " ms, en reposo " + (l0 - l1) + " B, libre " + l1 + " B");
    }

    function fin() as Void {
        reloj.stop();
        System.println("APP FIN");
        System.exit();
    }
}
