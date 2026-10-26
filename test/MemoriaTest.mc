import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

// En cada región, la tesela más pesada y la zona más pesada caben a la vez holgadamente, por debajo de
// Callejero.MEM_DOS (el fēnix 7X Pro da 768 KB a una watch-app; el 6X y el 6 Pro, 1,25 MB). En la calle nunca
// coinciden: la tesela mayor es del centro y la zona, del rural. Mide también lo que ocupan los índices de la región activa (Callejero.activar).
(:test)
function memoriaTeselaMayor(logger as Test.Logger) as Boolean {
    var ok = true;
    for (var k = 0; k < Regiones.IDS.size(); k++) {
        Callejero.soltar();
        var a0 = System.getSystemStats().usedMemory;
        Activa.poner(Regiones.IDS[k]);
        var indices = System.getSystemStats().usedMemory - a0;
        var s0 = System.getSystemStats().usedMemory;
        var t0 = System.getTimer();
        var t = new Tesela(0, WatchUi.loadResource(Callejero.T_MAYOR as ResourceId) as Array, Teselas.caja(0));
        var carga = System.getTimer() - t0;
        var s1 = System.getSystemStats().usedMemory;
        t0 = System.getTimer();
        for (var i = 0; i < 10; i++) {
            Buscador.buscar(t, t.ox + 325.0 + i, t.oy + 325.0);
        }
        var busca = (System.getTimer() - t0) / 10;
        t0 = System.getTimer();
        var z = WatchUi.loadResource(Callejero.Z_MAYOR as ResourceId) as Array;
        var cargaZ = System.getTimer() - t0;
        var s2 = System.getSystemStats().usedMemory;
        t0 = System.getTimer();
        for (var i = 0; i < 10; i++) {
            Zonas.buscar(z, 1000.0 + i, 1000.0);
        }
        var buscaZ = (System.getTimer() - t0) / 10;
        logger.debug("MEMORIA " + Callejero.ETIQUETA + ": índices " + indices + " B; tesela mayor " + (s1 - s0) + " B, carga "
            + carga + " ms, búsqueda " + busca + " ms (simulador), " + t.nc + " calles, " + t.R.size()
            + " números de tiradas, " + t.V.size() + " de vértices, " + t.P.size() + " portales, " + t.S.length() + " letras");
        logger.debug("MEMORIA " + Callejero.ETIQUETA + ": zona mayor " + (s2 - s1) + " B, carga " + cargaZ + " ms, búsqueda "
            + buscaZ + " ms, " + (z[5] as Array).size() + " lugares; las dos: " + (s2 - s0) + " B; en uso "
            + System.getSystemStats().usedMemory / 1024 + " de " + System.getSystemStats().totalMemory / 1024 + " KB");
        ok = ok && s2 - s0 < Callejero.MEM_DOS;
        t = null;
        z = null;
    }
    return ok;
}
