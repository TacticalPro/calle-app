import Toybox.Lang;
import Toybox.Position;

// GPS encendido solo mientras se ve la app. arrancar() y parar() se pueden
// llamar de más sin efecto: la vista lo enciende en onShow, lo apaga en onHide,
// y la app lo apaga otra vez en onStop por si acaso.
module Gps {
    var _activo as Boolean = false;

    // La mejor configuración que acepte el reloj. Multibanda (L1+L5) resiste
    // mejor los rebotes entre fachadas del casco viejo; el fēnix 6X no la tiene y cae a L1.
    function _configuracion() as Position.Configuration or Null {
        if (!(Position has :hasConfigurationSupport)) {
            return null;     // API < 3.3.6: la configuración por defecto del reloj
        }
        var prefs = [
            Position.CONFIGURATION_GPS_GLONASS_GALILEO_BEIDOU_L1_L5,
            Position.CONFIGURATION_GPS_GLONASS_GALILEO_BEIDOU_L1,
            Position.CONFIGURATION_GPS_GALILEO,
            Position.CONFIGURATION_GPS
        ] as Array<Position.Configuration>;
        for (var i = 0; i < prefs.size(); i++) {
            if (Position.hasConfigurationSupport(prefs[i])) {
                return prefs[i];
            }
        }
        return null;
    }

    function arrancar(cb as Method(info as Position.Info) as Void) as Void {
        if (_activo) {
            return;
        }
        var cfg = _configuracion();
        if (cfg != null) {
            Position.enableLocationEvents({
                :acquisitionType => Position.LOCATION_CONTINUOUS,
                :configuration => cfg
            }, cb);
        } else {
            Position.enableLocationEvents(Position.LOCATION_CONTINUOUS, cb);
        }
        _activo = true;
    }

    function parar() as Void {
        if (!_activo) {
            return;
        }
        Position.enableLocationEvents(Position.LOCATION_DISABLE, null);
        _activo = false;
    }

    function activo() as Boolean {
        return _activo;
    }
}
