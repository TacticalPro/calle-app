# Calles A Coruña — textos de la Connect IQ Store

App del catálogo por zonas (`tools/catalogo.json`): `APP=coruna ./ciq.sh tienda` → `bin/calle-coruna.iq`.
Subida nueva en el portal (no es versión de otra app), con el id `d80e9f16…`. **Subida el 2026-10-27** como 3.5.1: [ficha en la tienda](https://apps.garmin.com/apps/197766ff-5403-4037-a139-7cde9867c1b8), pendiente de aprobación. El portal la dio por verificada (fēnix 5, 5S, 6 y 6S) y avisó «Signature check failed», el fallo conocido de la primera subida; en local, «Verified OK». Categoría Navigation, sin datos de usuario, sin migración, gratis, avisos de reseñas, la portada y las cuatro pantallas. Siguiente versión: *Upload New Version* sobre esta misma app.

- **Título:** «Calles A Coruña (offline)», en inglés y en español, como las demás apps Calles.
- **Versión:** 3.5.1 (la misma base que Calles Galicia 3.5.1, con los textos que no se salen del borde en las pantallas
  pequeñas); la decide el autor al subirla.
- **Relojes:** fēnix 5, 5S, 6 y 6S (128 KB de memoria por app), con los tests en verde en los cuatro. Es la provincia de
  A Coruña de la variante `c5` del generador (`tools/regiones.json` → `coruna`); Galicia entera no cabe en estos relojes.
  Los demás relojes llevan «Calles Galicia».
  En A Coruña, parroquia y lugar se consultan con la tesela soltada, cada 100 m (`source-c5/Localizador.mc`).
- **Ficha:** categoría Navigation, sin migración automática a relojes nuevos, avisos de reseñas al correo de contacto.
- **Portada:** la carátula «el marcador en el cruce» sobre el callejero real (la praza de María Pita, en A Coruña), con «CALLES /
  A CORUÑA / LA CALLE Y EL PORTAL, SIN COBERTURA». Se genera con `tools/caratula.py --region coruna` →
  `docs/tienda/coruna/portada_500.png`.
- **Pantallas** en `docs/tienda/coruna/`, `ficha_1.png` a `ficha_4.png`: capturas del simulador del fēnix 5 con la app real
  (`tools/medida_c5.py coruna --ficha`), en sitios públicos, por este orden:
  1. Santiago, Rúa do Franco 33, Casco Histórico, entre la Ruela de Paio o Eremita y la Rúa da Raíña;
  2. A Coruña, Rúa Real 26, A Pescaría, entre la Rúa Alcalde Canuto Berea y la Rúa Torreiro;
  3. la aldea de Sisto (parroquia de Brates), sin calle a 50 m, con su UTM;
  4. desde la Rúa Bon Xesús 13 (Ferrol), el hospital con urgencias más cercano: el Hospital Naval, a 1,5 km hacia el NO.
- El portal puede avisar «Signature check failed» en la primera subida de una app nueva: es un fallo conocido suyo.
  La firma se comprueba en local con `openssl dgst -sha256 -verify dev_key.pub -keyform DER -signature manifest.sig2
  manifest.xml`.

Atribución obligatoria (OSM y Catastro): no se quita de ninguna versión.
Los datos de OSM vienen del extracto de Geofabrik de Galicia; la fuente y la licencia siguen siendo OSM (ODbL).

**Source Code URL:** https://github.com/TacticalPro/calle-app

## Español

**Nombre:** Calles A Coruña (offline)

**Sin conexión.** El callejero de la provincia de A Coruña viaja dentro de la app: la calle, el número de portal y las
calles a cada lado, sin teléfono, sin cobertura y sin datos móviles. Y fuera de la ciudad, la aldea y la parroquia.
Hecha para los relojes de 128 KB: fēnix 5, 5S, 6 y 6S.

**Por qué sin conexión:**
- Funciona donde el móvil no llega: sin cobertura, sin datos o con el teléfono en casa.
- No espera a ninguna red ni a ningún servidor: en cuanto el reloj tiene posición, tiene la dirección.
- Su posición es solo suya: la app no tiene acceso a internet, así que no puede enviarla a ningún sitio.

- En qué calle está, el portal más cercano y entre qué calles; en un cruce, la esquina.
- Parroquia, aldea o lugar más cercano, y barrio en las ciudades. Lejos de cualquier calle, dice dónde está igualmente.
- Hospital con urgencias más cercano: flecha y anillo de brújula, y distancia en línea recta.
- Coordenadas UTM, redondeadas como las del propio reloj.
- Anotaciones con START: hora, lugar y coordenadas, guardadas en el reloj, y guía para volver a cada una.
- Hora grande, para usarla también como reloj.

Zona: la provincia de A Coruña. Portal y calles a cada lado en A Coruña, Santiago, Ferrol, Narón y Ribeira; en el resto de la provincia, la calle o la
carretera, la aldea y la parroquia. Para otras provincias, «Calles Galicia» en los relojes con más memoria.

Los números de portal salen de OpenStreetMap y, en Santiago y su entorno, también del Catastro. En muchos pueblos y aldeas el mapa aún no tiene números: ahí la
app da la calle, la aldea y la parroquia, pero no el portal.

Relojes: fēnix 5, 5S, 6 y 6S.

Permisos: solo la posición. Sin acceso a internet y sin grabar actividades.

Los fallos y las sugerencias, al correo de contacto.

Código y método de generación de los datos: https://github.com/TacticalPro/calle-app

Datos: © colaboradores de OpenStreetMap (ODbL). Fuente: Dirección General del Catastro.

**Novedades (3.5.1):** primera versión, para los fēnix 5, 5S, 6 y 6S.

## English

**Name:** Calles A Coruña (offline)

**Fully offline.** The street map of the province of A Coruña ships inside the app: street name, door number and the
streets on each side, with no phone, no signal and no mobile data. Outside town, the village and the parish. Made for
the 128 KB watches: fēnix 5, 5S, 6 and 6S.

**Why offline:**
- It works where your phone doesn't: no signal, no data, or the phone left at home.
- It never waits for a network or a server: as soon as the watch has a position, you have the address.
- Your position stays yours: the app has no internet access, so it cannot send it anywhere.

- The street you are on, the nearest door number and the cross streets on each side; at a junction, the corner.
- Parish, nearest village or place, and neighbourhood in towns. Far from any street, it still tells you where you are.
- Nearest hospital with A&E: arrow, compass ring and straight-line distance.
- UTM coordinates, rounded like the watch's own.
- Notes with START: time, place and coordinates, kept on the watch, with guidance back to each one.
- Large clock, so it works as a watch too.

Area: the province of A Coruña. Door numbers and cross streets in A Coruña, Santiago de Compostela, Ferrol, Narón and Ribeira; in the rest of the province, the street or
road, the village and the parish. For other provinces, «Calles Galicia» on watches with more memory. The interface is
in Spanish.

Door numbers come from OpenStreetMap and, in Santiago de Compostela and its surroundings, also from the Spanish Cadastre. Many villages still have no door numbers on the map: there the app gives
the street, village and parish, but no number.

Watches: fēnix 5, 5S, 6 and 6S.

Permissions: position only. No internet access and no activity recording.

Please send bugs and suggestions to the contact email.

Source code and how the data is built: https://github.com/TacticalPro/calle-app

Data: © OpenStreetMap contributors (ODbL). Source: Dirección General del Catastro.

**What's new (3.5.1):** first release, for the fēnix 5, 5S, 6 and 6S.
