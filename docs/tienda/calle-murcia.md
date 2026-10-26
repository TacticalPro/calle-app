# Calles Murcia — textos de la Connect IQ Store

App del catálogo por zonas (`tools/catalogo.json`): `APP=murcia ./ciq.sh tienda` → `bin/calle-murcia.iq`.
Subida nueva en el portal (no es una versión de ninguna beta), con el id `e6ac6e68…`. **Sin subir**: la sube el autor.

**Beta privada** (app propia, solo el fēnix 7X Pro): `APP=murcia ./ciq.sh beta` → `bin/calle-murcia-beta.iq` (2,3 MB), con el
id de beta `fe5c0e8f…` (`beta_id` en `tools/catalogo.json`; no se cambia nunca). **Subida el 2026-10-26 como 3.4.0**:
«Calles Murcia (offline) (beta)», [página en la tienda](https://apps.garmin.com/apps/9fc95931-e107-4bde-8b54-8cec1f923d2f),
estado «App pending»; el portal la dio por verificada (fēnix 7X Pro y sus ediciones Sapphire Solar y Dual Power) y avisó
«Signature check failed» al subirla, el fallo conocido: en *Edit Details* ya dice «Signature: Verified». Textos en inglés y
en español con una línea de beta al principio, Navigation, sin datos de usuario, sin migración, gratis, avisos de reseñas,
la carátula y las cuatro pantallas. Siguiente versión: *Upload New Version* sobre esta misma app.

- **Título:** «Calles Murcia (offline)», en inglés y en español (confirmado por el autor, 2026-10-26).
- **Versión:** 3.4.0 (la interfaz 3.4, propuesta); la decide el autor al subirla.
- **Relojes:** la familia fēnix 7 (7, 7S, 7X, 7 Pro, 7S Pro, 7X Pro y los dos Pro sin Wi-Fi), con los tests en verde
  en el 7S, el 7 y el 7X Pro. El `.iq` pasa de los 10 MB: se sube a mano o por trozos, como las demás apps del catálogo.
- **Ficha:** categoría Navigation, sin migración automática a relojes nuevos, avisos de reseñas al correo de contacto.
- **Portada:** la carátula «el marcador en el cruce» sobre el callejero real del centro de Murcia (la plaza del
  Cardenal Belluga), con «CALLES / MURCIA / LA CALLE Y EL PORTAL, SIN COBERTURA». Se genera con
  `tools/caratula.py --region murcia` → `docs/tienda/murcia/portada_500.png`.
- **Pantallas** en `docs/tienda/murcia/` (`tools/mockup.py --ficha murcia`, en el 7X Pro), por este orden: `ficha_1.png` a
  `ficha_4.png`. Cada escena es lo que dicen los datos reales en un sitio público (`tools/ref.py --region murcia`):
  1. Murcia, Calle Trapería 19, entre la Calle Andrés Baquero y la Calle Platería;
  2. Cartagena, Calle Mayor 14, Casco Antiguo, entre la Calle Medieras y la Calle Andino;
  3. la pedanía de El Moral (término de Caravaca de la Cruz), sin calle a 50 m, con su UTM;
  4. desde la Gran Vía de Murcia (nº 23), el hospital con urgencias más cercano: el Morales Meseguer, a 750 m hacia el N
     (en el reloj, «Hosp. Morales Meseguer»: los nombres largos van abreviados para caber enteros, `poi_abrev` en
     `tools/overrides-murcia.json`).
- El portal puede avisar «Signature check failed» en la primera subida de una app nueva: es un fallo conocido suyo.
  La firma se comprueba en local con `openssl dgst -sha256 -verify dev_key.pub -keyform DER -signature manifest.sig2
  manifest.xml`.

Atribución obligatoria (OSM): no se quita de ninguna versión.
Los datos de OSM vienen del extracto de Geofabrik, recortado al polígono de la Región; la fuente y la licencia siguen
siendo OSM (ODbL).

**Source Code URL:** https://github.com/TacticalPro/calle-app

## Español

**Nombre:** Calles Murcia (offline)

**Sin conexión.** El callejero de toda la Región de Murcia viaja dentro de la app: la calle, el número de portal y las
calles a cada lado, sin teléfono, sin cobertura y sin datos móviles. Y fuera de la ciudad, la pedanía o el paraje y el
término municipal.

**Por qué sin conexión:**
- Funciona donde el móvil no llega: sin cobertura, sin datos o con el teléfono en casa.
- No espera a ninguna red ni a ningún servidor: en cuanto el reloj tiene posición, tiene la dirección.
- Su posición es solo suya: la app no tiene acceso a internet, así que no puede enviarla a ningún sitio.

- En qué calle está, el portal más cercano y entre qué calles; en un cruce, la esquina.
- Término municipal, pedanía, caserío o paraje más cercano, y barrio en las ciudades. Lejos de cualquier calle, dice
  dónde está igualmente.
- Hospital con urgencias más cercano, y comisaría o cuartel de la Guardia Civil más cercanos: flecha y anillo de
  brújula, y distancia en línea recta.
- Coordenadas UTM, redondeadas como las del propio reloj.
- Anotaciones con START: hora, lugar y coordenadas, guardadas en el reloj, y guía para volver a cada una.
- Hora grande, para usarla también como reloj.

Zona: la Región de Murcia entera, sus 45 municipios, en toda la familia fēnix 7. Se irán añadiendo relojes.

Los números de portal salen de OpenStreetMap. En muchas calles el mapa aún no tiene números: ahí la app da la calle y
las calles a cada lado, pero no el portal.

Permisos: solo la posición. Sin acceso a internet y sin grabar actividades.

Primera versión: los fallos y las sugerencias, al correo de contacto.

Código y método de generación de los datos: https://github.com/TacticalPro/calle-app

Datos: © colaboradores de OpenStreetMap (ODbL).

**Novedades (3.4.0):** primera versión pública. La Región de Murcia entera, con términos municipales, pedanías y parajes.

## English

**Name:** Calles Murcia (offline)

**Fully offline.** The street map of the whole Region of Murcia ships inside the app: street name, door number and the
streets on each side, with no phone, no signal and no mobile data. Outside town, the hamlet or rural area and the
municipality.

**Why offline:**
- It works where your phone doesn't: no signal, no data, or the phone left at home.
- It never waits for a network or a server: as soon as the watch has a position, you have the address.
- Your position stays yours: the app has no internet access, so it cannot send it anywhere.

- The street you are on, the nearest door number and the cross streets on each side; at a junction, the corner.
- Municipality, nearest hamlet, village or rural place, and neighbourhood in towns. Far from any street, it still tells
  you where you are.
- Nearest hospital with A&E, and nearest police station or Guardia Civil post: arrow, compass ring and
  straight-line distance.
- UTM coordinates, rounded like the watch's own.
- Notes with START: time, place and coordinates, kept on the watch, with guidance back to each one.
- Large clock, so it works as a watch too.

Area: the whole Region of Murcia, all 45 municipalities, on the whole fēnix 7 family. More watches will follow. The
interface is in Spanish.

Door numbers come from OpenStreetMap. Many streets still have no door numbers on the map: there the app gives the
street and the cross streets, but no number.

Permissions: position only. No internet access and no activity recording.

First release: please send bugs and suggestions to the contact email.

Source code and how the data is built: https://github.com/TacticalPro/calle-app

Data: © OpenStreetMap contributors (ODbL).

**What's new (3.4.0):** first public release. The whole Region of Murcia, with municipalities, hamlets and rural places.
