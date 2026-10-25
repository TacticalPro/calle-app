import Toybox.Lang;
import Toybox.Position;
import Toybox.Time;

// Lo que se ve. Lo escribe el Localizador; las vistas (las de hoy y las futuras) solo lo leen.
// Vive en memoria mientras la app está abierta; solo una anotación (Notas) guarda algo en el reloj.
class Modelo {
    var estado as Estado = EST_BUSCANDO;
    var calle1 as String or Null = null;
    var num1 as String or Null = null;
    var aprox1 as Boolean = false;      // portal a más de L.PORTAL_APROX m
    var calle2 as String or Null = null;  // solo si hay dos calles casi a la misma distancia
    var num2 as String or Null = null;
    var aprox2 as Boolean = false;
    var cruce as Boolean = false;       // las dos a menos de L.CRUCE m: estamos en el cruce
    var tramoA as String or Null = null;  // calles que cruzan a cada lado en calle1 (A antes que B;
    var tramoB as String or Null = null;  // B es null si solo hay un lado o si es la misma que A)
    var barrio as String or Null = null;
    var lugar as String or Null = null;   // el poblado (o paraje) más cercano: para «sin calle»
    var parroquia as String or Null = null;
    var calidad as Number = Position.QUALITY_NOT_AVAILABLE;
    var radio as Number = 0;            // metros que se atribuyen a esa calidad
    var lat as Double = 0.0d;
    var lon as Double = 0.0d;
    var tFix as Number = 0;             // segundos (Time.now().value()) de la posición
    var semilla as Boolean = false;     // la posición viene de antes de abrir la app

    // Para la página de detalle (prueba de campo).
    var d1 as Float = 0.0;
    var d2 as Float = 0.0;
    var tesela as Number = -1;
    var ms as Number = 0;

    function initialize() {
    }

    function edad() as Number {
        return tFix == 0 ? 0 : Time.now().value() - tFix;
    }

    function hayCalle() as Boolean {
        return calle1 != null;
    }

    function limpiar() as Void {
        calle1 = null;
        num1 = null;
        calle2 = null;
        num2 = null;
        aprox1 = false;
        aprox2 = false;
        cruce = false;
        tramoA = null;
        tramoB = null;
        barrio = null;
        lugar = null;
        parroquia = null;
        d1 = 0.0;
        d2 = 0.0;
    }
}
