import Toybox.Lang;
import Toybox.Test;

// Geometría del Buscador sobre teselas sintéticas (coordenadas locales, ver Sintetica.mc).

(:test)
function geomSegmento(logger as Test.Logger) as Boolean {
    var t = Sintetica.tesela(["A", "B"], [
        [0, 0, 0, [100, 100, 300, 100]],
        [1, 0, 0, [100, 105]]              // tirada de un solo vértice: distancia a un punto
    ] as Array<Array>, [] as Array<Array>);
    Buscador.buscar(t, Sintetica.x(200), Sintetica.x(130));
    var interior = Sintetica.cerca(t.mejor[0], 30.0);
    Buscador.buscar(t, Sintetica.x(60), Sintetica.x(100));
    var extremo = Sintetica.cerca(t.mejor[0], 40.0);
    Buscador.buscar(t, Sintetica.x(103), Sintetica.x(109));
    var punto = Sintetica.cerca(t.mejor[1], 5.0);
    return interior && extremo && punto;
}

(:test)
function geomAreas(logger as Test.Logger) as Boolean {
    var t = Sintetica.tesela(["Cuadrada", "Ele"], [
        [0, 1, 1, [100, 100, 200, 100, 200, 200, 100, 200, 100, 100]],
        [1, 1, 1, [300, 300, 500, 300, 500, 350, 350, 350, 350, 500, 300, 500, 300, 300]]
    ] as Array<Array>, [] as Array<Array>);
    Buscador.buscar(t, Sintetica.x(150), Sintetica.x(150));
    var dentro = Sintetica.cerca(t.mejor[0], 0.0);
    Buscador.buscar(t, Sintetica.x(150), Sintetica.x(230));
    var fuera = Sintetica.cerca(t.mejor[0], 30.0);
    Buscador.buscar(t, Sintetica.x(400), Sintetica.x(400));   // en la muesca de la L: fuera
    var muesca = Sintetica.cerca(t.mejor[1], 50.0);
    Buscador.buscar(t, Sintetica.x(320), Sintetica.x(450));   // en el brazo de la L: dentro
    var brazo = Sintetica.cerca(t.mejor[1], 0.0);
    return dentro && fuera && muesca && brazo;
}

(:test)
function geomClaseYPoda(logger as Test.Logger) as Boolean {
    var t = Sintetica.tesela(["Calle", "Senda", "Lejana"], [
        [0, 0, 0, [0, 100, 600, 100]],
        [1, 2, 0, [0, 110, 600, 110]],
        [2, 0, 0, [0, 600, 600, 600]]
    ] as Array<Array>, [] as Array<Array>);
    var s = Buscador.buscar(t, Sintetica.x(300), Sintetica.x(106));
    // La senda está a 4 m pero penaliza 4: gana la calle, a 6 m.
    return s[0] == 0 && s[1] == 1 && Sintetica.cerca(t.mejor[0], 6.0) && Sintetica.cerca(t.mejor[1], 8.0)
        && t.mejor[2] == Buscador.LEJOS;
}

(:test)
function geomPortales(logger as Test.Logger) as Boolean {
    var t = Sintetica.tesela(["A", "B"], [
        [0, 0, 0, [0, 100, 600, 100]],
        [1, 0, 0, [300, 0, 300, 600]]
    ] as Array<Array>, [
        [200, 110, 0, 12, 0],
        [240, 110, 0, 14, 0],
        [310, 200, 1, 0, 0],
        [310, 260, 1, 7, 0]
    ] as Array<Array>);
    var p = Buscador.portal(t, 0, Sintetica.x(205), Sintetica.x(100));
    var a = p != null && (p[0] as String).equals("12");
    var q = Buscador.portal(t, 0, Sintetica.x(500), Sintetica.x(100));   // nada a 40 m
    var r = Buscador.portal(t, 1, Sintetica.x(300), Sintetica.x(250));   // el 7, no el de la calle A
    return a && q == null && r != null && (r[0] as String).equals("7");
}

// El tramo es el de la tirada más cercana de la calle, aunque otra de la misma calle esté cerca.
(:test)
function geomTramo(logger as Test.Logger) as Boolean {
    var t = Sintetica.tesela(["A", "B", "C", "D"], [
        [0, 0, 0, [0, 100, 300, 100], [1, 2]],     // A entre B y C
        [0, 0, 0, [300, 100, 600, 100], [2, -1]],  // A, pasado C, sin cruce al otro lado
        [3, 0, 0, [0, 300, 600, 300]]              // D sin tramo
    ] as Array<Array>, [] as Array<Array>);
    Buscador.buscar(t, Sintetica.x(150), Sintetica.x(104));
    var a = t.tramo(0);
    Buscador.buscar(t, Sintetica.x(450), Sintetica.x(104));
    var b = t.tramo(0);
    Buscador.buscar(t, Sintetica.x(150), Sintetica.x(296));
    var d = t.tramo(3);
    var r = Buscador.consultar(t, Sintetica.x(150), Sintetica.x(104));
    return "B".equals(a[0]) && "C".equals(a[1]) && "C".equals(b[0]) && b[1] == null && d[0] == null && d[1] == null
        && "B".equals(r.tramoA) && "C".equals(r.tramoB);
}

// El Localizador ordena el tramo: A primero, y el mismo nombre a los dos lados es un solo lado.
(:test)
function geomTramoModelo(logger as Test.Logger) as Boolean {
    var t = Sintetica.tesela(["A", "B", "C"], [
        [0, 0, 0, [0, 100, 300, 100], [-1, 1]],
        [0, 0, 0, [300, 300, 600, 300], [2, 2]]
    ] as Array<Array>, [] as Array<Array>);
    var m = new Modelo();
    m.radio = 8;
    var loc = new Localizador(m);
    loc.calcularEn(t, Sintetica.x(150), Sintetica.x(104));
    var uno = "B".equals(m.tramoA) && m.tramoB == null;
    m.limpiar();
    loc.calcularEn(t, Sintetica.x(450), Sintetica.x(304));
    var u = "C".equals(m.tramoA) && m.tramoB == null;
    return uno && u;
}

(:test)
function geomTextoNumero(logger as Test.Logger) as Boolean {
    Activa.poner(Regiones.IDS[0]);
    return Buscador.textoNumero(12).equals("12") && Buscador.textoNumero(0).equals(Callejero.SUF[0])
        && Buscador.textoNumero(3 | 1 << 12).equals("3" + Callejero.SUF[1]);
}
