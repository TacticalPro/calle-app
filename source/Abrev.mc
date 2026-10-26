import Toybox.Lang;

// Forma corta del nombre, solo si el completo no cabe: abrevia el tipo de vía y deja el resto.
// "Rúa do Franco" → "R. do Franco", "Avenida de Lugo" → "Av. de Lugo", "Carrer de Colón" → "C. de Colón".
module Abrev {
    const TIPOS = [
        "Rúa", "R.", "Avenida", "Av.", "Praza", "Pr.", "Praciña", "Prc.", "Travesa", "Tr.", "Travesía", "Tr.",
        "Camiño", "Cm.", "Calle", "C/", "Plaza", "Pl.", "Paseo", "P.º", "Rolda", "Rd.", "Ronda", "Rd.",
        "Estrada", "Estr.", "Carretera", "Ctra.", "Corredoira", "Corr.", "Costa", "Cta.", "Glorieta", "Gl.",
        "Lugar", "Lg.", "Urbanización", "Urb.", "Polígono", "Pol.", "Pasaxe", "Psx.", "Ruela", "Rla.",
        "Carrer", "C.", "Avinguda", "Av.", "Plaça", "Pl.", "Passeig", "Pg.", "Camí", "Cm."
    ] as Array<String>;

    function corta(nombre as String) as String {
        var esp = nombre.find(" ");
        if (esp == null) {
            return nombre;
        }
        var tipo = nombre.substring(0, esp) as String;
        for (var i = 0; i < TIPOS.size(); i += 2) {
            if (TIPOS[i].equals(tipo)) {
                return TIPOS[i + 1] + nombre.substring(esp, nombre.length());
            }
        }
        return nombre;
    }
}
