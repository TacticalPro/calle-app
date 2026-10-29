import Toybox.Lang;
import Toybox.StringUtil;
import Toybox.WatchUi;

// Una tesela del FORMATO 5 (tools/formato5.py): la del FORMATO 4 en bytes, para los relojes de 128 KB (variante
// c5). Mismo contenido y misma interfaz que source/Tesela.mc, pero las tablas se leen del ByteArray B: en
// reposo ocupa 4 B por número en lugar de 5, y al cargar se pasa por el texto base64 (pico ~2,3 veces B).
// Las coordenadas de la tesela van en unidades de u m (1 en ciudad, 4 en el rural); x, y, ox… en metros.
class Tesela {
    var idx as Number;
    var ox as Float;    // esquina SO de la tesela con su margen, en metros de región
    var oy as Float;
    var x1 as Float;    // esquina NE sin el margen
    var y1 as Float;
    var u as Number;    // metros por unidad
    var nc as Number;
    var pb as Number;
    var oS as Number;   // dónde empieza S en B: "\n" + cada nombre + "\n", en UTF-8 (O cuenta en bytes)
    var B as ByteArray;
    var oO as Number;   // dónde empieza cada tabla en B, en bytes
    var oC as Number;
    var oCB as Number;
    var oK as Number;
    var oR as Number;
    var oV as Number;
    var oP as Number;
    var oE as Number;
    var nE as Number;   // palabras de E (pares índice, valor)
    var mejor as Array<Float>;
    var mejorRun as Array<Number>;

    // caja: [x0, y0, x1, y1] de la tesela sin margen, en metros de región (Teselas.caja).
    function initialize(i as Number, b as ByteArray, caja as Array<Number>) {
        var h = Teselas.palabra(b, 0);
        if ((h & 0xFF) != Teselas.FORMATO) {
            throw new Lang.InvalidValueException("tesela con formato " + (h & 0xFF));
        }
        u = (h >> 8) & 0xFF;
        pb = (h >> 16) & 0xFF;
        nc = Teselas.palabra(b, 4);
        var ls = Teselas.palabra(b, 8);
        var p = 4 * Teselas.CABECERA;
        oS = p;
        p += (ls + 3) & ~3;
        oO = p;
        p += 4 * Teselas.palabra(b, 12);
        oC = p;
        p += 4 * Teselas.palabra(b, 16);
        oCB = p;
        p += 4 * Teselas.palabra(b, 20);
        oK = p;
        p += 4 * Teselas.palabra(b, 24);
        oR = p;
        p += 4 * Teselas.palabra(b, 28);
        oV = p;
        p += 4 * Teselas.palabra(b, 32);
        oP = p;
        p += 4 * Teselas.palabra(b, 36);
        oE = p;
        nE = Teselas.palabra(b, 40);
        B = b;
        idx = i;
        var m = Callejero.BUF * u;
        ox = (caja[0] - m).toFloat();
        oy = (caja[1] - m).toFloat();
        x1 = caja[2].toFloat();
        y1 = caja[3].toFloat();
        mejor = new Array<Float>[nc];
        mejorRun = new Array<Number>[nc];
    }

    // Dónde empieza en S el nombre k.
    function inicio(k as Number) as Number {
        var q = oO + 2 * k;
        return B[q] | (B[q + 1] << 8);
    }

    // El nombre k: una calle (k < nc) o un sufijo de portal. Se decodifica de B cada vez: guardar S como String
    // costaba ~5,3 KB más en reposo (plan 2), y se piden pocos nombres por búsqueda.
    function nombre(k as Number) as String {
        return StringUtil.convertEncodedString(B.slice(oS + inicio(k), oS + inicio(k + 1) - 1), {
            :fromRepresentation => StringUtil.REPRESENTATION_BYTE_ARRAY,
            :toRepresentation => StringUtil.REPRESENTATION_STRING_PLAIN_TEXT
        }) as String;
    }

    // [A, B]: las calles que cruzan en los extremos del trozo más cercano de la calle s en la última búsqueda.
    function tramo(s as Number) as Array<String or Null> {
        var r = mejorRun[s];
        if (r == null || r < 0) {
            return [null, null] as Array<String or Null>;
        }
        var h = Teselas.palabra(B, oR + 4 * (r + 1));
        var a = (h >> 6) & 0x3FF;
        var b = (h >> 16) & 0x3FF;
        return [a > 0 ? nombre(a - 1) : null, b > 0 ? nombre(b - 1) : null] as Array<String or Null>;
    }

    // Como en el FORMATO 4: vale mientras el punto no salga de la tesela más la holgura (BUF − MAXD).
    function cubre(x as Float, y as Float) as Boolean {
        var h = Callejero.BUF - Callejero.MAXD;
        var m = Callejero.BUF * u;
        var x0 = ox + m;
        var y0 = oy + m;
        return x >= x0 - h && x <= x1 + h && y >= y0 - h && y <= y1 + h;
    }

    // Índice de la calle con ese nombre, o -1. Las calles van en orden de bytes UTF-8 (el de sorted() del generador,
    // tools/formato5.py): bisección comparando bytes, sin pasar S a String.
    function indiceDe(n as String) as Number {
        var q = n.toUtf8Array();
        var lo = 0;
        var hi = nc - 1;
        while (lo <= hi) {
            var mid = (lo + hi) / 2;
            var c = comparar(q, mid);
            if (c == 0) {
                return mid;
            } else if (c > 0) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        return -1;
    }

    // Negativo, 0 o positivo: el nombre q (sus bytes UTF-8) frente al nombre k de la tesela, byte a byte.
    function comparar(q as Array<Number>, k as Number) as Number {
        var a = oS + inicio(k);
        var fin = oS + inicio(k + 1) - 1;
        var n = q.size();
        for (var i = 0; i < n; i++) {
            if (a + i >= fin) {
                return 1;       // el de la tesela es un prefijo de q: q va después
            }
            var d = q[i] - B[a + i];
            if (d != 0) {
                return d;
            }
        }
        return a + n < fin ? -1 : 0;
    }
}

module Teselas {
    const FORMATO = 5;
    const CABECERA = 11;    // palabras de la cabecera (tools/formato5.py)

    // La palabra de 32 bits little-endian que empieza en el byte k.
    function palabra(b as ByteArray, k as Number) as Number {
        return b[k] | (b[k + 1] << 8) | (b[k + 2] << 16) | (b[k + 3] << 24);
    }

    // El recurso (texto base64, en Rez.Strings o en un jsonData) como bytes. El texto se suelta al volver.
    function bytes(rid as ResourceId) as ByteArray {
        var s = WatchUi.loadResource(rid) as String;
        return StringUtil.convertEncodedString(s, {
            :fromRepresentation => StringUtil.REPRESENTATION_STRING_BASE64,
            :toRepresentation => StringUtil.REPRESENTATION_BYTE_ARRAY
        }) as ByteArray;
    }

    // null si la celda no tiene calles.
    function cargar(i as Number) as Tesela or Null {
        var rid = Callejero.IDX[i];
        if (rid == null) {
            return null;
        }
        return new Tesela(i, bytes(rid), caja(i));
    }

    // [x0, y0, x1, y1] de la tesela i sin margen, en metros de región (igual que en el FORMATO 4).
    function caja(i as Number) as Array<Number> {
        var T = Callejero.TESELA;
        var rc = Callejero.CAJAS;
        if (rc == null) {
            var c = (i % Callejero.COLS) * T;
            var f = (i / Callejero.COLS) * T;
            return [c, f, c + T, f + T] as Array<Number>;
        }
        var cajas = WatchUi.loadResource(rc) as Array<Number>;
        var a = cajas[2 * i];
        var b = cajas[2 * i + 1];
        return [(a & 0xFFFF) * T, ((a >> 16) & 0xFFFF) * T, (b & 0xFFFF) * T, ((b >> 16) & 0xFFFF) * T] as Array<Number>;
    }
}
