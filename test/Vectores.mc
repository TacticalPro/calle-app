import Toybox.Lang;
import Toybox.Test;

// Comprueba los vectores de test-gen/Vectores<Región>Test.mc (generados por tools/ref.py) con las teselas reales.
(:test)
module Vectores {
    function comprobar(logger as Test.Logger, region as Number, casos as Array<Array>) as Boolean {
        Activa.poner(region);
        var ok = true;
        for (var i = 0; i < casos.size(); i++) {
            var c = casos[i];
            var calle = c[3] as String;
            var d1 = c[4] as Float;
            var num = c[5] as String;
            // Tramo (en bruto, como lo da el callejero), barrio, lugar y parroquia.
            var esperado = c[6] + "|" + c[7] + "|" + c[8] + "|" + c[9] + "|" + c[10];
            var p = Geo.xy(c[1] as Double, c[2] as Double);
            var cel = Geo.celda(p[0], p[1]);
            var bien = false;
            var dice = "FUERA";
            var resto = esperado;
            if (cel < 0) {
                bien = calle.equals("FUERA");
            } else {
                var t = Teselas.cargar(cel);
                var r = t == null ? null : Buscador.consultar(t, p[0], p[1]);
                var z = Zonas.consultar(p[0], p[1]);
                var zs = z == null ? "||" : _s(z[2]) + "|" + _s(z[1]) + "|" + _s(z[0]);
                if (r == null || r.estado == EST_LEJOS) {
                    resto = "||" + zs;
                    bien = calle.equals("");
                    dice = "LEJOS";
                } else {
                    resto = _s(r.tramoA) + "|" + _s(r.tramoB) + "|" + zs;
                    var n = r.num1 == null ? "" : r.num1 as String;
                    bien = calle.equals(r.calle1) && (r.d1 - d1).abs() < 0.05 && num.equals(n);
                    dice = r.calle1 + " " + r.d1.format("%.3f") + " nº" + n;
                }
                bien = bien && resto.equals(esperado);
            }
            if (!bien) {
                logger.error(c[0] + ": esperaba " + calle + " " + d1 + " nº" + num + " [" + esperado + "]; dice "
                    + dice + " [" + resto + "]");
                ok = false;
            }
        }
        return ok;
    }

    function _s(v as String or Null) as String {
        return v == null ? "" : v;
    }

    // Recorre la ruta (lat, lon, lat, lon…) por el Localizador con GPS bueno y cuenta
    // cuántas veces cambia la calle principal y cuántos fixes no dicen la esperada.
    function ruta(logger as Test.Logger, esperada as String, pts as Array<Double>) as Boolean {
        var m = new Modelo();
        var loc = new Localizador(m);
        var cambios = 0;
        var otras = 0;
        var amb = 0;
        var esq = 0;
        var antes = "";
        var n = pts.size() / 2;
        for (var i = 0; i < n; i++) {
            loc.actualizar(pts[2 * i], pts[2 * i + 1], 4, 0, true, false);
            var ahora = m.calle1 != null ? m.calle1 as String : "";
            if (i > 0 && !antes.equals(ahora)) {
                cambios++;
            }
            antes = ahora;
            if (!esperada.equals(m.calle1)) {
                otras++;
            }
            if (m.calle2 != null) {
                if (m.cruce) {
                    esq++;
                } else {
                    amb++;
                }
            }
        }
        logger.debug("RUTA " + esperada + ": " + n + " fixes, " + cambios + " cambios, " + otras
            + " con otra calle, " + esq + " en esquina, " + amb + " con dos calles");
        return cambios <= 4 && otras * 10 <= n && amb * 4 <= n;
    }
}
