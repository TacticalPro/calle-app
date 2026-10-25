import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

// CALLE: dice en qué calle está, el portal más cercano y su tramo, sin conexión.
// No graba actividad ni usa la red; solo guarda las anotaciones que el usuario hace con START,
// en el reloj (ver ./ciq.sh privacidad).
class CalleApp extends Application.AppBase {
    var modelo as Modelo;
    var localizador as Localizador;

    function initialize() {
        AppBase.initialize();
        modelo = new Modelo();
        localizador = new Localizador(modelo);
    }

    // La región se activa aquí y no en initialize(): las propiedades (el ajuste «Zona») ya se pueden leer.
    function onStart(state as Dictionary?) as Void {
        Activa.inicial();
    }

    function onStop(state as Dictionary?) as Void {
        Gps.parar();
    }

    // Cambio de «Zona» desde Garmin Connect (versión de la tienda).
    function onSettingsChanged() as Void {
        Activa.aplicarAjuste();
        WatchUi.requestUpdate();
    }

    function getInitialView() as [WatchUi.Views] or [WatchUi.Views, WatchUi.InputDelegates] {
        var vista = new VistaCalle(modelo, localizador);
        return [vista, new DelegadoCalle(vista, localizador)];
    }
}
