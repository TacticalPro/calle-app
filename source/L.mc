import Toybox.Graphics;
import Toybox.Lang;

// Umbrales, colores y coordenadas: todo lo ajustable está aquí.
module L {
    // --- Localizador
    const MOVER_M = 5.0;         // recalcular si se ha movido al menos esto…
    const CADA_MS = 10000;       // …o si ha pasado esto
    const HISTERESIS_M = 3.0;    // la calle mostrada se queda mientras no la superen por más de esto
    // Dos calles son ambiguas si sus distancias difieren menos de max(AMBIG_MIN_M, radio·AMBIG_FACTOR).
    // Con 8 m el casco salía ambiguo más de la mitad del tiempo (tools/ref.py, 2026-10-23): es su trama.
    const AMBIG_MIN_M = 3.0;
    const AMBIG_FACTOR = 0.5;
    const CRUCE_M = 5.0;         // ambas a menos de esto: es una esquina, no una duda
    const PORTAL_APROX = 20.0;   // portal más lejos que esto: se marca con «~» (Fmt.numero)
    const SEMILLA_MAX_S = 600;   // al abrir, se ofrece la última posición si tiene menos de esto
    const VIEJA_S = 15;          // dato más viejo que esto: en gris y con su edad

    // --- Anotaciones
    const NOTAS_MAX = 300;
    const NOTA_VIEJA_S = 60;     // posición más vieja que esto: la anotación lo dice
    const AVISO_MS = 2000;       // «Anotado 23:41» en pantalla
    const VIBRA_MS = 50;

    // --- Pantalla. Las cotas son de la de 280×280 (fēnix 6X/7X) y se escalan con L.y() al alto real:
    // 218 (5S), 240 (5, 6S, 7S), 260 (6, 7), 416 y 454 (8 AMOLED). Las vistas llaman a L.escalar() en onLayout.
    // La hora arriba en grande; debajo, el barrio o la edad del dato.
    const HORA_Y = 34;           // centro vertical de la hora
    const HORA_PX = 44;          // tamaño de la hora con fuente vectorial (fēnix 7); sin ella, la numérica del reloj
    const HORA_MAX = 50;         // alto máximo de la fuente de sistema para la hora (sin vectoriales)
    const HORA_PUNTO = 18;       // hueco a la izquierda de la hora para el punto de calidad del GPS
    const SUB_Y = 63;            // línea pequeña bajo la hora: barrio, «sin calle a 50 m» o edad del dato
    const NOMBRE_Y = 58;         // arriba de la franja del nombre sin esa línea…
    const NOMBRE_Y_SUB = 76;     // …y con ella

    // --- Guía (VistaIr) con el anillo de brújula (source/Anillo.mc; pantallas de 280 px)
    const ANILLO_R = 133;        // radio del círculo fino del anillo
    const ANILLO_RI = 128;       // el texto de la guía va dentro de este radio

    var S as Float = 1.0;        // alto de la pantalla / 280

    function escalar(dc as Graphics.Dc) as Void {
        S = dc.getHeight() / 280.0;
    }

    // Una cota de la pantalla de 280 px, en la pantalla real (redondeo simétrico: la flecha tiene cotas negativas).
    function y(v as Numeric) as Number {
        var r = v * S;
        return (r < 0 ? r - 0.5 : r + 0.5).toNumber();
    }


    // Calidad del GPS (Position.QUALITY_*) → radio en metros. El reloj no da la precisión en metros.
    function radio(calidad as Number) as Number {
        if (calidad >= 4) {
            return 8;       // GOOD
        } else if (calidad == 3) {
            return 15;      // USABLE
        }
        return 30;          // POOR / LAST_KNOWN
    }
}
