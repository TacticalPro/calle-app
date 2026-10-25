import Toybox.Graphics;
import Toybox.Lang;

// Un Dc de 280×280 en memoria para los tests de dibujo. createBufferedBitmap es de la API 4.0;
// en el fēnix 6X (3.4) se construye el BufferedBitmap directamente.
(:test)
module Lienzo {
    function dc() as Graphics.Dc {
        if (Graphics has :createBufferedBitmap) {
            return (Graphics.createBufferedBitmap({:width => 280, :height => 280}).get() as Graphics.BufferedBitmap).getDc();
        }
        return new Graphics.BufferedBitmap({:width => 280, :height => 280}).getDc();
    }
}
