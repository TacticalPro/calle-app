import Toybox.Lang;

// Qué región del callejero está activa (Callejero.activar). Solo una a la vez: sus índices se
// construyen al activarla y los de la anterior se sueltan. Tesela y Zonas comparan Callejero.ID
// con el de lo que tienen cargado y lo sueltan si ha cambiado.
module Activa {
    // Al abrir: la del ajuste o, en automática, la última usada (la posición aún no ha llegado).
    function inicial() as Void {
        var z = Ajustes.zona();
        poner(z != Ajustes.AUTO ? z : Ajustes.ultima());
    }

    // Tras cambiar el ajuste (menú o teléfono): la fijada ya; la automática espera a la posición.
    function aplicarAjuste() as Void {
        var z = Ajustes.zona();
        if (z != Ajustes.AUTO && z != Callejero.ID) {
            poner(z);
        }
    }

    // Con cada posición. Con zona fija no se mueve: fuera de ella se ve FUERA DE ZONA. En automática,
    // si la posición sale de la región activa y cae en otra, pasa a esa. Devuelve si ha cambiado.
    function paraPosicion(lat as Double, lon as Double) as Boolean {
        var z = Ajustes.zona();
        if (z != Ajustes.AUTO) {
            if (z == Callejero.ID) {
                return false;
            }
            poner(z);
            return true;
        }
        if (Callejero.ID != 0 && contiene(Callejero.ID, lat, lon)) {
            return false;
        }
        var ids = Regiones.IDS;
        for (var i = 0; i < ids.size(); i++) {
            if (ids[i] != Callejero.ID && contiene(ids[i], lat, lon)) {
                poner(ids[i]);
                Ajustes.fijarUltima(ids[i]);
                return true;
            }
        }
        return false;
    }

    function contiene(id as Number, lat as Double, lon as Double) as Boolean {
        var i = Regiones.IDS.indexOf(id);
        if (i < 0) {
            return false;
        }
        var c = Regiones.CAJAS;
        var k = 4 * i;
        return lat >= c[k] && lon >= c[k + 1] && lat <= c[k + 2] && lon <= c[k + 3];
    }

    function poner(id as Number) as Void {
        var d = Regiones.datos(id);
        if (d != null) {
            Callejero.activar(id, d);
        }
    }
}
