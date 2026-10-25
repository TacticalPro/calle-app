import Toybox.Activity;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.Position;
import Toybox.WatchUi;

// Hospitales y comisarías de la región activa (recurso <prefijo>poi, tools/build_callejero.py):
// [FORMATO, nombres, direcciones, x, y, tipo], con x, y en metros enteros de región. Se carga al
// abrir la lista y se suelta al cerrarla: no vive en memoria mientras se ve la calle.
// La guía es en línea recta (rumbo y distancia): el reloj no lleva la red de calles para calcular rutas.
module Ir {
    // Tipos, como POI_* del generador.
    const HOSPITAL = 0;
    const URGENCIAS = 1;
    const CNP = 2;
    const LOCAL = 3;
    const GC = 4;
    const POLICIA = 5;
    const CNP_OTRA = 6;          // dependencias del CNP que no son comisaría (DNI, divisiones, unidades)
    const ANOTACION = 7;         // no viene del generador: «Ir aquí» desde una anotación (deNotas)

    const HOSPITALES = [HOSPITAL, URGENCIAS] as Array<Number>;
    const COMISARIAS = [CNP] as Array<Number>;
    const OTRAS_POLICIAS = [CNP_OTRA, LOCAL, GC, POLICIA] as Array<Number>;
    const CUANTOS = 8;               // en la lista
    const LLEGADA_M = 30;            // más cerca que esto: «Ha llegado»

    function cargar() as Array or Null {
        var r = Callejero.POI;
        if (r == null) {
            return null;
        }
        var d = WatchUi.loadResource(r) as Array;
        return d[0] == Callejero.FORMATO ? d : null;
    }

    // Los n más cercanos a (lat, lon) de los tipos pedidos, del más cercano al más lejano:
    // [[nombre, dirección, lat, lon, tipo, metros], …].
    function cercanos(d as Array, lat as Double, lon as Double, tipos as Array<Number>, n as Number) as Array<Array> {
        var N = d[1] as Array<String>;
        var D = d[2] as Array<String>;
        var X = d[3] as Array<Number>;
        var Y = d[4] as Array<Number>;
        var T = d[5] as Array<Number>;
        var out = [] as Array<Array>;
        for (var i = 0; i < N.size(); i++) {
            if (tipos.indexOf(T[i]) < 0) {
                continue;
            }
            var la = Callejero.LAT_MIN + Y[i].toDouble() / Callejero.KY;
            var lo = Callejero.LON_MIN + X[i].toDouble() / Callejero.KX;
            var m = distancia(lat, lon, la, lo);
            // Inserción ordenada en una lista de como mucho n (no hay Array.sort en la API 3.4).
            var k = out.size();
            while (k > 0 && (out[k - 1][5] as Float) > m) {
                k--;
            }
            if (k < n) {
                var e = [N[i], D[i], la, lo, T[i], m];
                out.add(e);
                for (var j = out.size() - 1; j > k; j--) {
                    out[j] = out[j - 1];
                }
                out[k] = e;
                if (out.size() > n) {
                    out = out.slice(0, n);
                }
            }
        }
        return out;
    }

    // Metros de (lat1, lon1) a (lat2, lon2): equirectangular local, de sobra a escala de ciudad.
    function distancia(lat1 as Double, lon1 as Double, lat2 as Double, lon2 as Double) as Float {
        var d = _dxdy(lat1, lon1, lat2, lon2);
        return Math.sqrt(d[0] * d[0] + d[1] * d[1]).toFloat();
    }

    // Rumbo verdadero de 1 a 2, en radianes desde el norte, en sentido horario (0..2π).
    function rumbo(lat1 as Double, lon1 as Double, lat2 as Double, lon2 as Double) as Float {
        var d = _dxdy(lat1, lon1, lat2, lon2);
        var a = Math.atan2(d[0], d[1]).toFloat();
        return a < 0.0 ? a + (2.0 * Math.PI).toFloat() : a;
    }

    function _dxdy(lat1 as Double, lon1 as Double, lat2 as Double, lon2 as Double) as Array<Double> {
        var fi = (lat1 + lat2) / 2.0d * Math.PI / 180.0d;
        var dx = (lon2 - lon1) * 111320.0d * Math.cos(fi);
        var dy = (lat2 - lat1) * 110574.0d;
        return [dx.toDouble(), dy.toDouble()] as Array<Double>;
    }

    // Rumbo hacia el que mira el reloj (brújula) en radianes, o null si no lo da. La brújula llega por
    // Activity sin pedir el permiso Sensor; si no, el rumbo del GPS, que solo vale en marcha.
    function orientacion(info as Position.Info or Null) as Float or Null {
        var a = Activity.getActivityInfo();
        if (a != null && a.currentHeading != null) {
            return a.currentHeading as Float;
        }
        if (info != null && info.heading != null && info.speed != null && (info.speed as Float) > 1.0) {
            return info.heading as Float;
        }
        return null;
    }

    // «850 m», «1,2 km», «12 km».
    function texto(m as Float) as String {
        if (m < 995.0) {
            return (Math.round(m / 10.0) * 10).toNumber().toString() + " m";
        } else if (m < 9950.0) {
            var dec = Math.round(m / 100.0).toNumber();
            return (dec / 10).toString() + "," + (dec % 10).toString() + " km";
        }
        return Math.round(m / 1000.0).toNumber().toString() + " km";
    }

    // «NE», a partir del rumbo en radianes.
    function cardinal(r as Float) as String {
        var nombres = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"] as Array<String>;
        var k = Math.round(r / (Math.PI / 4.0)).toNumber() % 8;
        return nombres[k < 0 ? k + 8 : k];
    }

    // Para la lista: el cuerpo, en minúsculas.
    function cuerpo(t as Number) as String {
        return t == LOCAL ? "municipal/local" : (t == GC ? "Guardia Civil" : (t == CNP ? "CNP"
            : (t == CNP_OTRA ? "CNP, no comisaría" : "policía")));
    }

    function etiquetaTipo(t as Number) as String {
        if (t == URGENCIAS) {
            return "HOSPITAL · URGENCIAS";
        } else if (t == HOSPITAL) {
            return "HOSPITAL";
        } else if (t == CNP) {
            return "COMISARÍA CNP";
        } else if (t == CNP_OTRA) {
            return "CNP · DEPENDENCIA";
        } else if (t == LOCAL) {
            return "POLICÍA MUNICIPAL/LOCAL";
        } else if (t == GC) {
            return "GUARDIA CIVIL";
        } else if (t == ANOTACION) {
            return "ANOTACIÓN";
        }
        return "POLICÍA";
    }

    // Color del destino (flecha, rótulo y bola del anillo) y su tono oscuro (el círculo del anillo).
    function color(t as Number) as Number {
        if (t == HOSPITAL || t == URGENCIAS) {
            return Graphics.COLOR_RED;
        }
        return t == ANOTACION ? Graphics.COLOR_GREEN : Graphics.COLOR_BLUE;
    }

    function colorOscuro(t as Number) as Number {
        if (t == HOSPITAL || t == URGENCIAS) {
            return Graphics.COLOR_DK_RED;
        }
        return t == ANOTACION ? Graphics.COLOR_DK_GREEN : 0x0055AA;
    }

    // Las anotaciones con posición, como lista de la guía, en el orden de Notas.lista() (la más nueva
    // primero): [lugar, UTM, lat, lon, ANOTACION, 0, rótulo, seq]. El rótulo lleva la hora de la
    // anotación; la fecha ya se ve en la lista del menú.
    function deNotas(ns as Array<Array>) as Array<Array> {
        var out = [] as Array<Array>;
        for (var i = 0; i < ns.size(); i++) {
            var e = ns[i][1] as Array;
            var lat = e[2];
            if (lat == null) {
                continue;
            }
            var lon = e[3] as Double;
            out.add([Fmt.legible(e[1] as String), Utm.texto(lat as Double, lon), lat, lon, ANOTACION, 0.0,
                "ANOTACIÓN · " + Fmt.horaYFecha(e[0] as Number)[0], ns[i][0]]);
        }
        return out;
    }

    // Posición en la lista de deNotas() de la anotación seq, o -1.
    function indiceNota(lista as Array<Array>, seq as Number) as Number {
        for (var i = 0; i < lista.size(); i++) {
            if (lista[i].size() > 7 && lista[i][7] == seq) {
                return i;
            }
        }
        return -1;
    }
}
