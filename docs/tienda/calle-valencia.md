# Calles Comunitat Valenciana — textos de la Connect IQ Store

App del catálogo por zonas (`tools/catalogo.json`): `APP=valencia ./ciq.sh tienda` → `bin/calle-valencia.iq`.
Subida nueva en el portal (no es una versión de ninguna beta), con el id `f435ba19…`. **Sin subir**: la sube el autor.

- **Título (provisional, lo decide el autor):** «Calles Comunitat Valenciana (offline)», en inglés y en español. En el
  reloj, «Calles C. Valenciana» (`nombre` de la entrada `valencia` en `tools/catalogo.json`, el único sitio donde se
  cambia). En el menú del reloj y en el ajuste «Zona del callejero», la zona se llama «C. Valenciana» (`etiqueta` en
  `tools/regiones.json`).
- **Versión:** la de la base de Calles (interfaz 3.4).
- **Relojes:** la familia fēnix 7 (7, 7S, 7X, 7 Pro, 7S Pro, 7X Pro y los dos Pro sin Wi-Fi), probada en el
  simulador del 7S, el 7 y el 7X Pro. El `.iq` pesa unos 112 MB (un `.prg` de 15,9 MB por pieza): se sube a mano o
  por trozos con la extensión del navegador (método documentado en `docs/tienda/`).
- **Ficha:** categoría Navigation, sin migración automática a relojes nuevos, avisos de reseñas al correo de contacto.
- **Portada:** la carátula «el marcador en el cruce» sobre el callejero real de la Plaça de l'Ajuntament de València,
  con «CALLES / COMUNITAT VALENCIANA / LA CALLE Y EL PORTAL, SIN COBERTURA». Se genera con
  `tools/caratula.py --region valencia` → `docs/tienda/valencia/portada_500.png`.
- **Pantallas** en `docs/tienda/valencia/` (`tools/mockup.py --ficha valencia`, en el 7X Pro), por este orden:
  `ficha_1.png` a `ficha_4.png`. Cada escena es lo que dicen los datos reales en un sitio público (`tools/ref.py`):
  1. València, Carrer de Sant Vicent Màrtir 21, el Mercat, entre el Carrer dels Manyans y el Carrer de Sant Ferran;
  2. Alacant, Carrer de Canalejas 5, Raval de Sant Francesc, entre el Carrer de Rafael Terol y el Carrer de Sant Ferran;
  3. en la huerta de Alboraia, sin calle a 50 m: Camí de Vera, término de Alboraia / Alboraya, con su UTM;
  4. desde el centro de Manises, el hospital con urgencias más cercano: el Hospital de Manises, a 1,2 km hacia el SE.
- El portal puede avisar «Signature check failed» en la primera subida de una app nueva: es un fallo conocido suyo.
  La firma se comprueba en local con `openssl dgst -sha256 -verify dev_key.pub -keyform DER -signature manifest.sig2
  manifest.xml`.

Atribución obligatoria (OSM): no se quita de ninguna versión.
Los datos de OSM vienen del extracto de Geofabrik; la fuente y la licencia siguen siendo OSM (ODbL).

**Source Code URL:** https://github.com/TacticalPro/calle-app

## Español

**Nombre:** Calles Comunitat Valenciana (offline)

**Sin conexión.** El callejero de toda la Comunitat Valenciana viaja dentro de la app: la calle, el número de portal y
las calles a cada lado, sin teléfono, sin cobertura y sin datos móviles. Y fuera de la ciudad, el lugar más cercano y
el término municipal.

**Por qué sin conexión:**
- Funciona donde el móvil no llega: sin cobertura, sin datos o con el teléfono en casa.
- No espera a ninguna red ni a ningún servidor: en cuanto el reloj tiene posición, tiene la dirección.
- Su posición es solo suya: la app no tiene acceso a internet, así que no puede enviarla a ningún sitio.

- En qué calle está, el portal más cercano y entre qué calles; en un cruce, la esquina.
- Los nombres tal como están en el mapa, en valenciano o en castellano según el municipio.
- Término municipal, pueblo, partida o lugar más cercano, y barrio en las ciudades. Lejos de cualquier calle, dice
  dónde está igualmente.
- Hospital con urgencias más cercano, y comisaría o cuartel de la Guardia Civil más cercanos: flecha y anillo de
  brújula, y distancia en línea recta.
- Coordenadas UTM, redondeadas como las del propio reloj.
- Anotaciones con START: hora, lugar y coordenadas, guardadas en el reloj, y guía para volver a cada una.
- Hora grande, para usarla también como reloj.

Zona: toda la Comunitat Valenciana, las tres provincias (Castellón, Valencia y Alicante), en toda la familia
fēnix 7. Se irán añadiendo relojes.

Los números de portal salen de OpenStreetMap. En muchas calles, sobre todo fuera de los centros urbanos, el mapa aún
no tiene números: ahí la app da la calle, el lugar y el término, pero no el portal.

Permisos: solo la posición. Sin acceso a internet y sin grabar actividades.

Primera versión: los fallos y las sugerencias, al correo de contacto.

Código y método de generación de los datos: https://github.com/TacticalPro/calle-app

Datos: © colaboradores de OpenStreetMap (ODbL).

**Novedades:** primera versión pública. Toda la Comunitat Valenciana, con términos municipales, pueblos y partidas.

## English

**Name:** Calles Comunitat Valenciana (offline)

**Fully offline.** The street map of the whole Valencian Community ships inside the app: street name, door number and
the streets on each side, with no phone, no signal and no mobile data. Outside town, the nearest place and the
municipality.

**Why offline:**
- It works where your phone doesn't: no signal, no data, or the phone left at home.
- It never waits for a network or a server: as soon as the watch has a position, you have the address.
- Your position stays yours: the app has no internet access, so it cannot send it anywhere.

- The street you are on, the nearest door number and the cross streets on each side; at a junction, the corner.
- Street names as they are on the map, in Valencian or in Spanish depending on the town.
- Municipality, nearest village, rural district or place, and neighbourhood in towns. Far from any street, it still
  tells you where you are.
- Nearest hospital with A&E, and nearest police station or Guardia Civil post: arrow, compass ring and
  straight-line distance.
- UTM coordinates, rounded like the watch's own.
- Notes with START: time, place and coordinates, kept on the watch, with guidance back to each one.
- Large clock, so it works as a watch too.

Area: the whole Valencian Community, all three provinces (Castellón, Valencia and Alicante), on the whole fēnix 7
family. More watches will follow. The interface is in Spanish.

Door numbers come from OpenStreetMap. Many streets, especially outside town centres, still have no door numbers on
the map: there the app gives the street, place and municipality, but no number.

Permissions: position only. No internet access and no activity recording.

First release: please send bugs and suggestions to the contact email.

Source code and how the data is built: https://github.com/TacticalPro/calle-app

Data: © OpenStreetMap contributors (ODbL).

**What's new:** first public release. The whole Valencian Community, with municipalities, villages and rural
districts.
