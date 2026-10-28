import Toybox.Application;
import Toybox.Lang;
import Toybox.Position;
import Toybox.System;
import Toybox.Time;
import Toybox.Timer;

// GPS falso para medir la memoria con la app real en modo app (plan 4 de la c5, 2026-10-27). Solo lo compila el
// jungle de medida (tools/medida_c5.py), en lugar de source/Gps.mc: la app es la de la tienda, sin tests, y recibe
// las posiciones de MedidaPuntos.PUNTOS, una cada MedidaPuntos.PASO_MS, como si fueran del GPS. Tras cada una escribe
// la memoria en uso. Si una tesela y su zona no caben juntas, la app se cae con «Out Of Memory» en la salida de
// monkeydo. Con MedidaPuntos.MENU, al final abre el menú (capturas de pantalla, tools/medida_c5.py --capturas).
module Gps {
    var _activo as Boolean = false;
    var _paseo as Paseo or Null = null;
    var _lastre as ByteArray or Null = null;   // MedidaPuntos.LASTRE B retenidos desde el arranque (medida_c5.py --lastre)

    function arrancar(cb as Method(info as Position.Info) as Void) as Void {
        if (_activo) {
            return;
        }
        _activo = true;
        if (_paseo == null) {
            if (MedidaPuntos.LASTRE > 0) {
                _lastre = new [MedidaPuntos.LASTRE]b;
            }
            var st = System.getSystemStats();
            System.println("MEDIDA inicio: usada " + st.usedMemory + " B de " + st.totalMemory);
            var p = new Paseo(cb);
            _paseo = p;
            p.empezar();
        }
    }

    function parar() as Void {
        _activo = false;
    }

    function activo() as Boolean {
        return _activo;
    }
}

class Paseo {
    var _cb as Method(info as Position.Info) as Void;
    var _k as Number = 0;
    var _timer as Timer.Timer = new Timer.Timer();

    function initialize(cb as Method(info as Position.Info) as Void) {
        _cb = cb;
    }

    function empezar() as Void {
        _timer.start(method(:paso), MedidaPuntos.PASO_MS, true);
    }

    function paso() as Void {
        var P = MedidaPuntos.PUNTOS;
        if (_k >= MedidaPuntos.NOMBRES.size()) {
            _timer.stop();
            if (MedidaPuntos.MENU) {
                MenuCalle.abrir();
                System.println("MEDIDA MENU");
            }
            System.println("MEDIDA FIN");
            return;
        }
        var info = new Position.Info();
        info.position = new Position.Location({
            :latitude => P[2 * _k], :longitude => P[2 * _k + 1], :format => :degrees
        });
        info.accuracy = Position.QUALITY_GOOD;
        info.when = Time.now();
        var u0 = System.getSystemStats().usedMemory;
        _cb.invoke(info);
        var st = System.getSystemStats();
        System.println("MEDIDA " + MedidaPuntos.NOMBRES[_k] + ": usada " + u0 + " → " + st.usedMemory + " B; libre "
            + st.freeMemory + " B de " + st.totalMemory + "; " + (Application.getApp() as CalleApp).modelo.ms + " ms");
        _k++;
    }
}
