import Toybox.Lang;
import Toybox.Test;

// Anotaciones: alta, lectura de la más nueva a la más vieja, borrado, tope y texto de cada estado.
// Usa el almacenamiento real del simulador y lo deja vacío al acabar.
(:test)
function notasAltaLecturaBorrado(logger as Test.Logger) as Boolean {
    Notas.borrarTodas();
    var r0 = Notas.anotar(1000, "Rúa do Franco 33", 42.8781762d, -8.5453149d) == NOTA_OK;
    Notas.anotar(2000, "sin posición", null, null);
    Notas.anotar(3000, "Rúa do Vilar 44", 42.8785539d, -8.5446323d);
    var l = Notas.lista();
    var orden = l.size() == 3 && ((l[0][1] as Array)[0] as Number) == 3000 && ((l[2][1] as Array)[1] as String).equals("Rúa do Franco 33")
        && (l[1][1] as Array)[2] == null && ((l[2][1] as Array)[2] as Double) == 42.8781762d;
    Notas.borrar(l[1][0] as Number);
    var l2 = Notas.lista();
    var borrada = l2.size() == 2 && ((l2[0][1] as Array)[0] as Number) == 3000 && ((l2[1][1] as Array)[0] as Number) == 1000;
    Notas.anotar(4000, "otra", null, null);
    var l3 = Notas.lista();
    var nueva = l3.size() == 3 && ((l3[0][1] as Array)[1] as String).equals("otra");
    Notas.borrarTodas();
    var vacia = Notas.cuantas() == 0 && Notas.lista().size() == 0;
    if (!(r0 && orden && borrada && nueva && vacia)) {
        logger.error("pasos " + [r0, orden, borrada, nueva, vacia]);
    }
    return r0 && orden && borrada && nueva && vacia;
}

(:test)
function notasTope(logger as Test.Logger) as Boolean {
    Notas.borrarTodas();
    var largo = "Rúa de Bernardo Barreiro de Vázquez-Varela 125B, esq. Rúa de San Pedro de Mezonzo (posición de hace 3 min)";
    var ok = true;
    for (var i = 0; i < L.NOTAS_MAX; i++) {
        ok = ok && Notas.anotar(i, largo, 42.8d, -8.5d) == NOTA_OK;
    }
    var llena = Notas.anotar(9999, "una más", null, null) == NOTA_LLENAS;
    var n = Notas.cuantas();
    Notas.borrarTodas();
    logger.debug("NOTAS " + L.NOTAS_MAX + " largas guardadas: " + ok + "; la siguiente, llena: " + llena);
    return ok && llena && n == L.NOTAS_MAX;
}

(:test)
function notasTexto(logger as Test.Logger) as Boolean {
    var m = new Modelo();
    var t = [] as Array<String>;
    var pref = Callejero.ZPREF;
    Callejero.ZPREF = "parroquia de ";   // el de Galicia; lo pone la región activa (Cataluña: «término de »)
    t.add(Notas.texto(m));                                    // buscando
    m.estado = EST_FUERA;
    t.add(Notas.texto(m));
    m.estado = EST_LEJOS;
    t.add(Notas.texto(m));
    m.lugar = "Mazas";
    m.parroquia = "Marrozos";
    t.add(Notas.texto(m));
    m.limpiar();
    m.estado = EST_OK;
    m.calle1 = "Rúa do Franco";
    m.num1 = "33";
    m.tramoA = "Rúa do Vilar";
    m.tramoB = "Rúa da Raíña";
    t.add(Notas.texto(m));                                    // el número manda
    m.num1 = null;
    t.add(Notas.texto(m));
    m.tramoB = null;
    t.add(Notas.texto(m));
    m.num1 = "54";
    m.calle2 = "Rúa da Raíña";
    m.cruce = true;
    t.add(Notas.texto(m));
    m.cruce = false;
    m.calle1 = "Rúa do Vilar";
    m.num1 = "44";
    m.calle2 = "Rúa Nova";
    m.num2 = "11";
    m.aprox2 = true;
    t.add(Notas.texto(m));
    m.semilla = true;
    m.tFix = 1;
    var viejo = Notas.texto(m);
    m.limpiar();
    m.semilla = false;
    m.estado = EST_LEJOS;
    m.lugar = "Mas Pujol";
    m.parroquia = "Vic";
    Callejero.ZPREF = "término de ";
    var terme = Notas.texto(m);
    Callejero.ZPREF = pref;
    var esperado = ["sin posición", "fuera de zona", "sin calle", "Mazas (parroquia de Marrozos)",
        "Rúa do Franco 33", "Rúa do Franco, entre Rúa do Vilar y Rúa da Raíña", "Rúa do Franco, cerca de Rúa do Vilar",
        "Rúa do Franco 54, esq. Rúa da Raíña", "Rúa do Vilar 44 / Rúa Nova ~11"] as Array<String>;
    var ok = viejo.find("(posición de hace ") != null;
    if (terme.find("Mas Pujol (término de Vic)") != 0) {
        logger.error("término: «" + terme + "»");
        ok = false;
    }
    if (!Fmt.legible("Rúa Nova ≈11 / ≈3").equals("Rúa Nova ~11 / ~3")) {
        logger.error("legible: «" + Fmt.legible("Rúa Nova ≈11 / ≈3") + "»");
        ok = false;
    }
    for (var i = 0; i < esperado.size(); i++) {
        if (!esperado[i].equals(t[i])) {
            logger.error("texto " + i + ": «" + t[i] + "» ≠ «" + esperado[i] + "»");
            ok = false;
        }
    }
    return ok;
}
