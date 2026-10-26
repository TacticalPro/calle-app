import Toybox.Application;
import Toybox.Lang;

enum ResultadoNota {
    NOTA_OK,
    NOTA_LLENAS,    // ya hay L.NOTAS_MAX: no se guarda
    NOTA_ERROR      // el reloj no la ha podido guardar
}

// Anotaciones: el único módulo que guarda algo en el reloj (./ciq.sh privacidad lo vigila).
// Se quedan en el reloj hasta que el usuario las borre; nada sale de él.
// Una clave por anotación, "n<seq>" → [t (s de época), lugar, lat (Double o null), lon], y un
// índice en "notas" con los seq de la más vieja a la más nueva: un valor de Storage no puede pasar
// de 32 KB, y 300 anotaciones en una sola clave se acercarían a ese tope.
module Notas {
    const CLAVE = "notas";

    function _indice() as Array<Number> {
        var v = Application.Storage.getValue(CLAVE);
        return v instanceof Array ? v as Array<Number> : [] as Array<Number>;
    }

    function cuantas() as Number {
        return _indice().size();
    }

    function anotar(t as Number, lugar as String, lat as Double or Null, lon as Double or Null) as ResultadoNota {
        var ix = _indice();
        if (ix.size() >= L.NOTAS_MAX) {
            return NOTA_LLENAS;
        }
        var seq = ix.size() > 0 ? ix[ix.size() - 1] + 1 : 0;
        try {
            // Primero la entrada y luego el índice: si algo corta en medio, solo queda una huérfana
            // que la siguiente anotación sobrescribe.
            Application.Storage.setValue("n" + seq, [t, lugar, lat, lon]);
            ix.add(seq);
            Application.Storage.setValue(CLAVE, ix);
        } catch (e) {
            return NOTA_ERROR;
        }
        return NOTA_OK;
    }

    // [[seq, [t, lugar, lat, lon]], …] de la más nueva a la más vieja.
    function lista() as Array<Array> {
        var ix = _indice();
        var out = [] as Array<Array>;
        for (var i = ix.size() - 1; i >= 0; i--) {
            var e = Application.Storage.getValue("n" + ix[i]);
            if (e instanceof Array) {
                out.add([ix[i], e]);
            }
        }
        return out;
    }

    function borrar(seq as Number) as Void {
        var ix = _indice();
        Application.Storage.deleteValue("n" + seq);
        ix.remove(seq);
        Application.Storage.setValue(CLAVE, ix);
    }

    function borrarTodas() as Void {
        var ix = _indice();
        for (var i = 0; i < ix.size(); i++) {
            Application.Storage.deleteValue("n" + ix[i]);
        }
        Application.Storage.deleteValue(CLAVE);
    }

    // Lo que se ve en pantalla, con los nombres completos.
    function texto(m as Modelo) as String {
        if (m.estado == EST_BUSCANDO) {
            return "sin posición";
        } else if (m.estado == EST_FUERA) {
            return "fuera de zona";
        }
        var s;
        if (m.estado == EST_LEJOS) {
            s = m.lugar != null ? m.lugar as String : "sin calle";
            if (m.parroquia != null) {
                s += " (" + Callejero.ZPREF + m.parroquia + ")";
            } else if (m.barrio != null) {
                s += " (" + m.barrio + ")";     // Madrid: barrio · distrito
            }
        } else if (m.calle2 != null && !m.cruce) {
            s = _conNumero(m.calle1 as String, m.num1, m.aprox1) + " / " + _conNumero(m.calle2 as String, m.num2, m.aprox2);
        } else if (m.cruce) {
            s = _conNumero(m.calle1 as String, m.num1, m.aprox1) + ", esq. " + m.calle2;
        } else if (m.num1 != null || m.tramoA == null) {
            s = _conNumero(m.calle1 as String, m.num1, m.aprox1);   // el número manda sobre el tramo
        } else if (m.tramoB != null) {
            s = m.calle1 + ", entre " + m.tramoA + " y " + m.tramoB;
        } else {
            s = m.calle1 + ", cerca de " + m.tramoA;
        }
        var e = m.edad();
        if (m.semilla || e > L.NOTA_VIEJA_S) {
            s += " (posición de " + Fmt.edad(e) + ")";
        }
        return s;
    }

    function _conNumero(calle as String, num as String or Null, aprox as Boolean) as String {
        return num == null ? calle : calle + " " + (aprox ? "~" : "") + num;
    }
}
