import Toybox.Lang;
import Toybox.WatchUi;

// START: anotar. Toque: recalcular. ARRIBA/ABAJO: página de detalle. Mantener ARRIBA: menú.
// BACK sale. El deslizamiento a la derecha se anula: un roce de la manga no cierra la app.
//
// START y el toque llegan los dos como la conducta onSelect. Según la documentación del SDK, el
// reloj llama primero a la conducta y solo si devuelve false a la entrada (onKey, onTap); la
// especificación suponía lo contrario. onSelect devuelve false y no hace nada, así que funciona
// en los dos órdenes: quien actúa es onKey(KEY_ENTER) o onTap, y devuelve true.
class DelegadoCalle extends WatchUi.BehaviorDelegate {
    private var _vista as VistaCalle;

    function initialize(vista as VistaCalle, loc as Localizador) {
        BehaviorDelegate.initialize();
        _vista = vista;
    }

    function onSelect() as Boolean {
        return false;
    }

    function onKey(ev as WatchUi.KeyEvent) as Boolean {
        if (ev.getKey() == WatchUi.KEY_ENTER) {
            _vista.anotar();
            return true;
        }
        return false;
    }

    function onTap(ev as WatchUi.ClickEvent) as Boolean {
        _vista.forzar();
        return true;
    }

    function onNextPage() as Boolean {
        _vista.cambiarPagina();
        return true;
    }

    function onPreviousPage() as Boolean {
        _vista.cambiarPagina();
        return true;
    }

    function onMenu() as Boolean {
        MenuCalle.abrir();
        return true;
    }

    function onSwipe(ev as WatchUi.SwipeEvent) as Boolean {
        return ev.getDirection() == WatchUi.SWIPE_RIGHT;
    }
}
