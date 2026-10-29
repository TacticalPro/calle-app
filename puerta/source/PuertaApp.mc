import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

// Solo existe para que los tests de la puerta tengan una app que los lleve.
class PuertaApp extends Application.AppBase {
    function initialize() {
        AppBase.initialize();
    }

    function getInitialView() as [WatchUi.Views] or [WatchUi.Views, WatchUi.InputDelegates] {
        return [vistaInicial()];
    }
}
