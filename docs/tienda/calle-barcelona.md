# Calles Barcelona — textos de la Connect IQ Store

App del catálogo por zonas (`tools/catalogo.json`): `APP=barcelona ./ciq.sh tienda` → `bin/calle-barcelona.iq`.
App nueva en el portal, con su propio id. **Borrador del 2026-10-26, sin subir.**

- **Título:** «Calles Barcelona (offline)», en inglés y en español.
- **Datos:** el término municipal de Barcelona, del extracto de Cataluña de Geofabrik (OSM del 2026-10-26),
  recortado a su caja. OSM tiene aquí casi todos los portales (137.415 casados con su calle), así que no hace
  falta otra fuente. Barrio y distrito por polígono, como en Madrid («el Gòtic · Ciutat Vella»).
- **Relojes:** los que quepan en el paquete. La lista amplia (familia fēnix 7 y 39 modelos más, 59 números de
  pieza) pesa unos 174 MB; la beta de prueba (`prueba` en el catálogo) mide cuánto acepta la tienda.
- **Ficha:** categoría Navigation, sin migración automática a relojes nuevos, sin datos de usuario, gratis,
  avisos de reseñas al correo de contacto.
- **Portada:** la carátula «el marcador en el cruce» sobre el callejero del Gòtic (`tools/caratula.py --instalar`).
- **Pantallas** en `docs/tienda/barcelona/` (`tools/mockup.py --ficha barcelona`, en el 7X Pro): lo que dicen los
  datos reales en sitios públicos:
  1. Carrer de Ferran 41, el Gòtic · Ciutat Vella, entre el Passatge del Crèdit y el Carrer d'Avinyó;
  2. La Rambla 61, el Raval · Ciutat Vella, cerca del Carrer de Sant Pau;
  3. Carrer de Verdi 32, la Vila de Gràcia · Gràcia, entre el Carrer de la Perla y el Carrer de l'Or;
  4. desde la plaça de Catalunya, el hospital con urgencias más cercano: el Clínic, a 1,5 km hacia el O.

Atribución obligatoria (OSM): no se quita de ninguna versión.

**Source Code URL:** https://github.com/TacticalPro/calle-app

## Español

**Nombre:** Calles Barcelona (offline)

**Sin conexión.** El callejero de Barcelona entero viaja dentro de la app: la calle, el número de portal y las
calles a cada lado, sin teléfono, sin cobertura y sin datos móviles.

**Por qué sin conexión:**
- Funciona donde el móvil no llega: sin cobertura, sin datos o con el teléfono en casa.
- No espera a ninguna red ni a ningún servidor: en cuanto el reloj tiene posición, tiene la dirección.
- Su posición es solo suya: la app no tiene acceso a internet, así que no puede enviarla a ningún sitio.

- En qué calle está, el portal más cercano y entre qué calles; en un cruce, la esquina.
- Barrio y distrito.
- Hospital con urgencias y comisaría más cercanos: flecha y anillo de brújula, y distancia en línea recta.
- Coordenadas UTM, redondeadas como las del propio reloj.
- Anotaciones con START: hora, lugar y coordenadas, guardadas en el reloj, y guía para volver a cada una.
- Hora grande, para usarla también como reloj.

Zona: el término municipal de Barcelona entero. Los nombres de las calles, como en el mapa (en catalán); la
interfaz, en español.

Permisos: solo la posición. Sin acceso a internet y sin grabar actividades.

Primera versión: los fallos y las sugerencias, al correo de contacto.

Código y método de generación de los datos: https://github.com/TacticalPro/calle-app

Datos: © colaboradores de OpenStreetMap (ODbL).

**Novedades (3.4.0):** primera versión pública. Barcelona entera, con barrio y distrito.

## English

**Name:** Calles Barcelona (offline)

**Fully offline.** The street map of all of Barcelona ships inside the app: street name, door number and the
streets on each side, with no phone, no signal and no mobile data.

**Why offline:**
- It works where your phone doesn't: no signal, no data, or the phone left at home.
- It never waits for a network or a server: as soon as the watch has a position, you have the address.
- Your position stays yours: the app has no internet access, so it cannot send it anywhere.

- The street you are on, the nearest door number and the cross streets on each side; at a junction, the corner.
- Neighbourhood and district.
- Nearest hospital with A&E and nearest police station: arrow, compass ring and straight-line distance.
- UTM coordinates, rounded like the watch's own.
- Notes with START: time, place and coordinates, kept on the watch, with guidance back to each one.
- Large clock, so it works as a watch too.

Area: the whole municipality of Barcelona. Street names as on the map (in Catalan); the interface is in Spanish.

Permissions: position only. No internet access and no activity recording.

First release: please send bugs and suggestions to the contact email.

Source code and how the data is built: https://github.com/TacticalPro/calle-app

Data: © OpenStreetMap contributors (ODbL).

**What's new (3.4.0):** first public release. All of Barcelona, with neighbourhood and district.
