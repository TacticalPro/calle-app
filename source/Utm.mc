import Toybox.Lang;
import Toybox.Math;

// Coordenadas UTM (WGS84) calculadas en el reloj: serie de Krüger de orden n³, con error por
// debajo del milímetro dentro del huso. Todo en Double: en Float el norte (~4,7 millones de
// metros) ya no distingue el metro. UtmTest lo compara con el MGRS del propio reloj.
module Utm {
    const A = 6378137.0d;                    // semieje mayor
    const F = 1.0d / 298.257223563d;         // aplanamiento
    const K0 = 0.9996d;
    const E_ = 2.718281828459045d;
    const PI_ = 3.141592653589793d;          // Math.PI puede ser Float
    const BANDAS = "CDEFGHJKLMNPQRSTUVWXX";  // de 8 en 8 grados desde 80° S

    function _exp(x as Double) as Double {
        return Math.pow(E_, x).toDouble();
    }

    function _sinh(x as Double) as Double {
        var e = _exp(x);
        return (e - 1.0d / e) / 2.0d;
    }

    function _cosh(x as Double) as Double {
        var e = _exp(x);
        return (e + 1.0d / e) / 2.0d;
    }

    function _atanh(x as Double) as Double {
        return 0.5d * Math.ln((1.0d + x) / (1.0d - x)).toDouble();
    }

    // [huso, banda, este, norte] con este y norte en metros (Double).
    function calcular(lat as Double, lon as Double) as Array {
        var huso = Math.floor((lon + 180.0d) / 6.0d).toNumber() + 1;
        huso = huso > 60 ? 60 : (huso < 1 ? 1 : huso);
        var b = Math.floor((lat + 80.0d) / 8.0d).toNumber();
        b = b > 20 ? 20 : (b < 0 ? 0 : b);
        var lon0 = (huso - 1) * 6.0d - 180.0d + 3.0d;

        var n = F / (2.0d - F);
        var n2 = n * n;
        var n3 = n2 * n;
        var aa = A / (1.0d + n) * (1.0d + n2 / 4.0d + n2 * n2 / 64.0d);
        var al = [n / 2.0d - 2.0d * n2 / 3.0d + 5.0d * n3 / 16.0d,
                  13.0d * n2 / 48.0d - 3.0d * n3 / 5.0d,
                  61.0d * n3 / 240.0d] as Array<Double>;

        var phi = lat * PI_ / 180.0d;
        var dl = (lon - lon0) * PI_ / 180.0d;
        var c = 2.0d * Math.sqrt(n).toDouble() / (1.0d + n);
        var s = Math.sin(phi).toDouble();
        var t = _sinh(_atanh(s) - c * _atanh(c * s));
        var xi = Math.atan(t / Math.cos(dl).toDouble()).toDouble();
        var eta = _atanh(Math.sin(dl).toDouble() / Math.sqrt(1.0d + t * t).toDouble());

        var e = eta;
        var nn = xi;
        for (var j = 1; j <= 3; j++) {
            var k = 2.0d * j;
            e += al[j - 1] * Math.cos(k * xi).toDouble() * _sinh(k * eta);
            nn += al[j - 1] * Math.sin(k * xi).toDouble() * _cosh(k * eta);
        }
        var este = 500000.0d + K0 * aa * e;
        var norte = K0 * aa * nn;
        if (lat < 0.0d) {
            norte += 10000000.0d;
        }
        return [huso, BANDAS.substring(b, b + 1), este, norte];
    }

    // "29T 537191 4747656": metros redondeados, como los da el propio reloj (su MGRS redondea;
    // comprobado en UtmTest, 2026-10-23).
    function texto(lat as Double, lon as Double) as String {
        var u = calcular(lat, lon);
        return (u[0] as Number).toString() + (u[1] as String) + " "
            + Math.round(u[2] as Double).toNumber().toString() + " " + Math.round(u[3] as Double).toNumber().toString();
    }
}
