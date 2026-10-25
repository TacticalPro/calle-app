import Toybox.Application;
import Toybox.Lang;
import Toybox.Position;
import Toybox.WatchUi;

// Menú (mantener ARRIBA): ir al hospital o la comisaría más cercanos, las anotaciones (y volver a
// una de ellas), la zona del callejero y sus datos. Aquí se engancharán las funciones futuras.
module MenuCalle {
    function abrir() as Void {
        var menu = new WatchUi.Menu2({:title => "CALLE"});
        menu.addItem(new WatchUi.MenuItem("Hospital más cercano", "flecha y distancia", :hospital, null));
        menu.addItem(new WatchUi.MenuItem("Comisaría más cercana", "CNP; al final, otras policías", :comisaria, null));
        menu.addItem(new WatchUi.MenuItem(etiquetaNotas(), "START anota en la pantalla de calle", :notas, null));
        menu.addItem(new WatchUi.MenuItem("Zona: " + etiquetaZona(), "dónde se usa el callejero", :zona, null));
        menu.addItem(new WatchUi.MenuItem("Callejero: " + Callejero.ETIQUETA,
            Callejero.FUENTES + " " + Callejero.DATOS + " · " + Callejero.NTESELAS + " teselas", :datos, null));
        WatchUi.pushView(menu, new DelegadoMenu(menu), WatchUi.SLIDE_UP);
    }

    function etiquetaZona() as String {
        var z = Ajustes.zona();
        return z == Ajustes.AUTO ? "Automática (" + Callejero.ETIQUETA + ")" : Ajustes.etiqueta(z);
    }

    // Automática: la región que contiene la posición (si no hay ninguna, la última usada). Fija: siempre
    // esa; fuera de ella, FUERA DE ZONA.
    function abrirZona(principal as WatchUi.Menu2) as Void {
        var menu = new WatchUi.Menu2({:title => "Zona"});
        var z = Ajustes.zona();
        menu.addItem(new WatchUi.MenuItem("Automática", z == Ajustes.AUTO ? "elegida · según la posición" : "según la posición",
            Ajustes.AUTO, null));
        for (var i = 0; i < Regiones.IDS.size(); i++) {
            var id = Regiones.IDS[i];
            menu.addItem(new WatchUi.MenuItem(Regiones.ETIQUETAS[i], id == z ? "elegida · fija" : "fija", id, null));
        }
        WatchUi.pushView(menu, new DelegadoZona(principal), WatchUi.SLIDE_LEFT);
    }

    // Lista de los más cercanos a la última posición. Sin posición, lo dice; la guía la busca sola.
    function abrirIr(tipos as Array<Number>, titulo as String, otras as Boolean) as Void {
        var d = Ir.cargar();
        var pos = posicion();
        var hay = pos != null;
        var lat = pos != null ? pos[0] : 0.0d;
        var lon = pos != null ? pos[1] : 0.0d;
        var menu = new WatchUi.Menu2({:title => titulo});
        var lista = [] as Array<Array>;
        if (d != null) {
            // Sin ninguna posición, desde el centro del callejero: el orden es orientativo y la guía
            // calcula de verdad en cuanto llega el GPS.
            lista = hay ? Ir.cercanos(d, lat, lon, tipos, Ir.CUANTOS)
                : Ir.cercanos(d, Callejero.LAT_MIN + Callejero.FILAS * Callejero.TESELA / 2 / Callejero.KY,
                    Callejero.LON_MIN + Callejero.COLS * Callejero.TESELA / 2 / Callejero.KX, tipos, Ir.CUANTOS);
        }
        for (var i = 0; i < lista.size(); i++) {
            var e = lista[i];
            var t = e[4] as Number;
            var sub = hay ? Ir.texto(e[5] as Float) + " " + Ir.cardinal(Ir.rumbo(lat, lon, e[2] as Double, e[3] as Double))
                : "sin posición aún";
            if (t == Ir.URGENCIAS) {
                sub += " · urgencias";
            } else if (t != Ir.HOSPITAL && t != Ir.CNP) {
                sub += " · " + Ir.cuerpo(t);
            }
            menu.addItem(new WatchUi.MenuItem(Abrev.corta(e[0] as String), sub, i, null));
        }
        if (lista.size() == 0) {
            menu.addItem(new WatchUi.MenuItem("No hay ninguno", "en el callejero de " + Callejero.ETIQUETA, :nada, null));
        }
        if (otras) {
            menu.addItem(new WatchUi.MenuItem("Otras policías", "CNP no comisaría, municipal, G. Civil", :otras, null));
        }
        WatchUi.pushView(menu, new DelegadoIrLista(lista, hay ? lat : null, hay ? lon : null), WatchUi.SLIDE_LEFT);
    }

    // La posición de la app si tiene fix; si no, la última que conozca el reloj. [lat, lon] o null.
    function posicion() as Array<Double> or Null {
        var m = (Application.getApp() as CalleApp).modelo;
        var lat = m.lat;
        var lon = m.lon;
        if (m.estado != EST_BUSCANDO && lat != null && lon != null) {
            return [lat, lon] as Array<Double>;
        }
        var p = Position.getInfo().position;
        if (p != null) {
            var g = p.toDegrees();
            return [g[0].toDouble(), g[1].toDouble()] as Array<Double>;
        }
        return null;
    }

    function etiquetaNotas() as String {
        return "Anotaciones (" + Notas.cuantas() + ")";
    }

    // Lista de la más nueva a la más vieja: «23:41 · R. do Franco 33» / «23-oct · 29T 537212 4747321».
    function abrirNotas(principal as WatchUi.Menu2) as Void {
        var menu = new WatchUi.Menu2({:title => "Anotaciones"});
        var ns = Notas.lista();
        for (var i = 0; i < ns.size(); i++) {
            var e = ns[i][1] as Array;
            var hf = Fmt.horaYFecha(e[0] as Number);
            var lat = e[2];
            var sub = hf[1] + " · " + (lat != null ? Utm.texto(lat as Double, e[3] as Double) : "sin posición");
            menu.addItem(new WatchUi.MenuItem(hf[0] + " · " + Abrev.corta(Fmt.legible(e[1] as String)), sub, ns[i][0], null));
        }
        if (ns.size() > 0) {
            menu.addItem(new WatchUi.MenuItem("Borrar todas", null, :todas, null));
        } else {
            menu.addItem(new WatchUi.MenuItem("No hay anotaciones", "START anota en la pantalla de calle", :nada, null));
        }
        WatchUi.pushView(menu, new DelegadoNotas(menu, principal), WatchUi.SLIDE_LEFT);
    }

    // Tras borrar: el contador del menú principal.
    function refrescar(principal as WatchUi.Menu2) as Void {
        var i = principal.findItemById(:notas);
        var it = i >= 0 ? principal.getItem(i) : null;
        if (it != null) {
            it.setLabel(etiquetaNotas());
            principal.updateItem(it, i);
        }
    }
}

class DelegadoMenu extends WatchUi.Menu2InputDelegate {
    private var _menu as WatchUi.Menu2;

    function initialize(menu as WatchUi.Menu2) {
        Menu2InputDelegate.initialize();
        _menu = menu;
    }

    function onSelect(item as WatchUi.MenuItem) as Void {
        var id = item.getId();
        if (id == :notas) {
            MenuCalle.abrirNotas(_menu);
        } else if (id == :hospital) {
            MenuCalle.abrirIr(Ir.HOSPITALES, "Hospitales", false);
        } else if (id == :comisaria) {
            MenuCalle.abrirIr(Ir.COMISARIAS, "Comisarías CNP", true);
        } else if (id == :zona) {
            MenuCalle.abrirZona(_menu);
        } else {
            WatchUi.popView(WatchUi.SLIDE_DOWN);
        }
    }
}

class DelegadoZona extends WatchUi.Menu2InputDelegate {
    private var _principal as WatchUi.Menu2;

    function initialize(principal as WatchUi.Menu2) {
        Menu2InputDelegate.initialize();
        _principal = principal;
    }

    function onSelect(item as WatchUi.MenuItem) as Void {
        Ajustes.fijarZona(item.getId() as Number);
        Activa.aplicarAjuste();
        var i = _principal.findItemById(:zona);
        var it = i >= 0 ? _principal.getItem(i) : null;
        if (it != null) {
            it.setLabel("Zona: " + MenuCalle.etiquetaZona());
            _principal.updateItem(it, i);
        }
        i = _principal.findItemById(:datos);
        it = i >= 0 ? _principal.getItem(i) : null;
        if (it != null) {
            it.setLabel("Callejero: " + Callejero.ETIQUETA);
            it.setSubLabel(Callejero.FUENTES + " " + Callejero.DATOS + " · " + Callejero.NTESELAS + " teselas");
            _principal.updateItem(it, i);
        }
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
    }
}

class DelegadoIrLista extends WatchUi.Menu2InputDelegate {
    private var _lista as Array<Array>;
    private var _lat as Double or Null;
    private var _lon as Double or Null;

    function initialize(lista as Array<Array>, lat as Double or Null, lon as Double or Null) {
        Menu2InputDelegate.initialize();
        _lista = lista;
        _lat = lat;
        _lon = lon;
    }

    function onSelect(item as WatchUi.MenuItem) as Void {
        var id = item.getId();
        if (id == :otras) {
            MenuCalle.abrirIr(Ir.OTRAS_POLICIAS, "Otras policías", false);
        } else if (id instanceof Number) {
            var v = new VistaIr(_lista, id, _lat, _lon);
            WatchUi.pushView(v, new DelegadoIr(v), WatchUi.SLIDE_LEFT);
        }
    }
}

class DelegadoNotas extends WatchUi.Menu2InputDelegate {
    private var _menu as WatchUi.Menu2;
    private var _principal as WatchUi.Menu2;

    function initialize(menu as WatchUi.Menu2, principal as WatchUi.Menu2) {
        Menu2InputDelegate.initialize();
        _menu = menu;
        _principal = principal;
    }

    function onSelect(item as WatchUi.MenuItem) as Void {
        var id = item.getId();
        if (id == :todas) {
            WatchUi.pushView(new WatchUi.Confirmation("¿Borrar todas?"),
                new ConfirmaBorrar(_menu, _principal, null), WatchUi.SLIDE_IMMEDIATE);
        } else if (id instanceof Number) {
            // Con posición: «Ir aquí» o «Borrar». Sin ella no hay adónde ir, y se pregunta directamente.
            var lista = Ir.deNotas(Notas.lista());
            var i = Ir.indiceNota(lista, id);
            if (i < 0) {
                WatchUi.pushView(new WatchUi.Confirmation("¿Borrar esta?"),
                    new ConfirmaBorrar(_menu, _principal, id), WatchUi.SLIDE_IMMEDIATE);
                return;
            }
            var acc = new WatchUi.Menu2({:title => item.getLabel()});
            acc.addItem(new WatchUi.MenuItem("Ir aquí", "flecha y distancia", :ir, null));
            acc.addItem(new WatchUi.MenuItem("Borrar", "pide confirmación", :borrar, null));
            WatchUi.pushView(acc, new DelegadoNota(_menu, _principal, id, lista, i), WatchUi.SLIDE_LEFT);
        }
    }
}

// Una anotación: «Ir aquí» abre la guía con todas las anotaciones con posición (ARRIBA/ABAJO pasan de
// una a otra) y empieza por esta; «Borrar» quita este menú y pregunta, para volver después a la lista.
class DelegadoNota extends WatchUi.Menu2InputDelegate {
    private var _menu as WatchUi.Menu2;
    private var _principal as WatchUi.Menu2;
    private var _seq as Number;
    private var _lista as Array<Array>;
    private var _i as Number;

    function initialize(menu as WatchUi.Menu2, principal as WatchUi.Menu2, seq as Number, lista as Array<Array>,
            i as Number) {
        Menu2InputDelegate.initialize();
        _menu = menu;
        _principal = principal;
        _seq = seq;
        _lista = lista;
        _i = i;
    }

    function onSelect(item as WatchUi.MenuItem) as Void {
        var id = item.getId();
        if (id == :ir) {
            var pos = MenuCalle.posicion();
            var v = new VistaIr(_lista, _i, pos != null ? pos[0] : null, pos != null ? pos[1] : null);
            WatchUi.pushView(v, new DelegadoIr(v), WatchUi.SLIDE_LEFT);
        } else if (id == :borrar) {
            WatchUi.popView(WatchUi.SLIDE_IMMEDIATE);
            WatchUi.pushView(new WatchUi.Confirmation("¿Borrar esta?"),
                new ConfirmaBorrar(_menu, _principal, _seq), WatchUi.SLIDE_IMMEDIATE);
        }
    }
}

// La confirmación se cierra sola tras onResponse: aquí no se hace popView, se retoca la lista.
class ConfirmaBorrar extends WatchUi.ConfirmationDelegate {
    private var _menu as WatchUi.Menu2;
    private var _principal as WatchUi.Menu2;
    private var _seq as Number or Null;   // null = todas

    function initialize(menu as WatchUi.Menu2, principal as WatchUi.Menu2, seq as Number or Null) {
        ConfirmationDelegate.initialize();
        _menu = menu;
        _principal = principal;
        _seq = seq;
    }

    function onResponse(r as WatchUi.Confirm) as Boolean {
        if (r != WatchUi.CONFIRM_YES) {
            return true;
        }
        var seq = _seq;
        if (seq != null) {
            Notas.borrar(seq);
            var i = _menu.findItemById(seq);
            if (i >= 0) {
                _menu.deleteItem(i);
            }
        }
        if (seq == null || Notas.cuantas() == 0) {
            if (seq == null) {
                Notas.borrarTodas();
            }
            while (_menu.getItem(0) != null) {
                _menu.deleteItem(0);
            }
            _menu.addItem(new WatchUi.MenuItem("No hay anotaciones", "START anota en la pantalla de calle", :nada, null));
        }
        MenuCalle.refrescar(_principal);
        WatchUi.requestUpdate();
        return true;
    }
}
