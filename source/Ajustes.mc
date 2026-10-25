import Toybox.Application;
import Toybox.Lang;

// La zona del callejero: 0 = automática (la región que contiene la posición) o el id de una región
// (Regiones.IDS). Es la propiedad «zona», así que también se cambia desde Garmin Connect en la versión
// de la tienda. Junto a Notas, el único módulo que guarda algo en el reloj (./ciq.sh privacidad):
// la zona elegida y, en automática, la última región usada, para abrir con ella sin esperar al GPS.
module Ajustes {
    const AUTO = 0;

    function zona() as Number {
        var v = null;
        try {
            v = Application.Properties.getValue("zona");
        } catch (e) {
            v = null;
        }
        return v instanceof Number && (v == AUTO || Regiones.IDS.indexOf(v) >= 0) ? v : AUTO;
    }

    function fijarZona(id as Number) as Void {
        try {
            Application.Properties.setValue("zona", id);
        } catch (e) {
            // Sin propiedades (no debería pasar): la elección dura lo que la app abierta.
        }
    }

    function ultima() as Number {
        var v = Application.Storage.getValue("ultima");
        return v instanceof Number && Regiones.IDS.indexOf(v) >= 0 ? v : Regiones.IDS[0];
    }

    function fijarUltima(id as Number) as Void {
        if (id != ultima()) {
            Application.Storage.setValue("ultima", id);
        }
    }

    function etiqueta(id as Number) as String {
        var i = Regiones.IDS.indexOf(id);
        return i >= 0 ? Regiones.ETIQUETAS[i] : "Automática";
    }
}
