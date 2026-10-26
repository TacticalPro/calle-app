import Toybox.Lang;
import Toybox.Math;
import Toybox.Position;
import Toybox.Test;

// La UTM calculada frente al MGRS del propio reloj (Position.Location.toGeoString): mismo huso
// y banda, y este y norte módulo 100 km iguales (los dos redondean; 1 m de margen por si un
// valor cae justo en el medio metro).
(:test)
function utmFrenteAMgrs(logger as Test.Logger) as Boolean {
    var puntos = [
        42.8806d, -8.5446d,      // catedral
        42.8785d, -8.5446d,      // Rúa do Vilar
        42.8650d, -8.5560d,      // Conxo
        42.8942d, -8.4243d,      // aeropuerto
        42.8100d, -8.6700d,      // esquina SO de la región
        42.9550d, -8.4050d,      // esquina NE
        43.3623d, -8.4115d,      // A Coruña
        42.2406d, -8.7207d,      // Vigo
        40.4168d, -3.7038d,      // Madrid (huso 30)
        41.3874d, 2.1686d        // Barcelona (huso 31)
    ] as Array<Double>;
    var ok = true;
    for (var i = 0; i < puntos.size(); i += 2) {
        var lat = puntos[i];
        var lon = puntos[i + 1];
        var u = Utm.calcular(lat, lon);
        var g = new Position.Location({:latitude => lat, :longitude => lon, :format => :degrees})
            .toGeoString(Position.GEO_MGRS);
        var s = UtmAux._sinEspacios(g);
        var n = s.length();
        var e5 = s.substring(n - 10, n - 5).toNumber();
        var n5 = s.substring(n - 5, n).toNumber();
        var cab = (u[0] as Number).toString() + (u[1] as String);
        var de = UtmAux._mod100k(Math.round(u[2] as Double).toNumber() - (e5 as Number));
        var dn = UtmAux._mod100k(Math.round(u[3] as Double).toNumber() - (n5 as Number));
        var bien = s.substring(0, cab.length()).equals(cab) && de <= 1 && dn <= 1;
        logger.debug("UTM " + Utm.texto(lat, lon) + "  MGRS " + g + (bien ? "" : "  ← NO"));
        ok = ok && bien;
    }
    return ok;
}

// Auxiliares del test: en un módulo (:test) para que no entren en el paquete publicado.
(:test)
module UtmAux {
    function _sinEspacios(s as String) as String {
        var out = "";
        var cs = s.toCharArray();
        for (var i = 0; i < cs.size(); i++) {
            if (cs[i] != ' ') {
                out += cs[i].toString();
            }
        }
        return out;
    }

    function _mod100k(d as Number) as Number {
        var r = d % 100000;
        r = r < 0 ? -r : r;
        return r > 50000 ? 100000 - r : r;
    }
}
