# Calles A Coruña — textos de la Connect IQ Store

App del catálogo por zonas (`tools/catalogo.json`): `APP=coruna ./ciq.sh tienda` → `bin/calle-coruna.iq`.
Subida nueva en el portal (no es versión de otra app), con el id `d80e9f16…`. **Subida el 2026-10-27** como 3.5.1: [ficha en la tienda](https://apps.garmin.com/apps/197766ff-5403-4037-a139-7cde9867c1b8); la 3.5.1 no se llegó a publicar. **Aprobada como 3.5.2 el 2026-10-27** (API: `APPROVED`, interna 2). Descripción reescrita el 2026-10-27 (lo que hace primero; sin «128 KB»). El portal la dio por verificada (fēnix 5, 5S, 6 y 6S) y avisó «Signature check failed», el fallo conocido de la primera subida; en local, «Verified OK», y la API del portal la da por buena (`signatureCheckSuccessFul`, versión 3.5.1, en y es). Categoría Navigation, sin datos de usuario, sin migración, gratis, avisos de reseñas, la portada y las cuatro pantallas. Siguiente versión: *Upload New Version* sobre esta misma app.

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

**Sin conexión.** La calle y el portal en la muñeca, en toda la provincia de A Coruña, sin teléfono, sin cobertura y sin datos. El callejero entero va dentro de la app. Sirve para cuando hay que decir dónde está (una llamada al 112, alguien que le espera) y el móvil no ayuda.

Para fēnix 5, 5S, 6 y 6S. Los relojes con más memoria tienen «Calles Galicia», con toda Galicia.

**Lo que le dice de un vistazo:**
- La calle, el portal más cercano y entre qué dos calles está. En un cruce, la esquina.
- Fuera de la ciudad, la aldea o el lugar más cercano y la parroquia; en las ciudades, el barrio. Aunque no haya ninguna calle cerca, le dice dónde está.
- El hospital con urgencias más cercano, con flecha, anillo de brújula y distancia en línea recta.
- Sus coordenadas UTM, redondeadas como las del propio reloj.
- Anotaciones con START: hora, lugar y coordenadas, guardadas en el reloj, con guía para volver a cada una.
- La hora en grande, para usarla también como reloj.

**Por qué sin conexión:**
- Funciona donde el móvil no llega: en el monte, en una aldea sin cobertura o con el teléfono en casa.
- No espera a ninguna red: en cuanto el reloj tiene posición, tiene la dirección.
- Su posición no sale del reloj, porque la app no tiene acceso a internet.

**Dónde llega:** portal y calles a cada lado en A Coruña, Santiago, Ferrol, Narón y Ribeira. En el resto de la provincia, la calle o la carretera, la aldea y la parroquia. Los números de portal vienen de OpenStreetMap y, en Santiago y su entorno, también del Catastro. En muchas aldeas el mapa aún no tiene números: ahí da la calle, la aldea y la parroquia, pero no el portal.

**Permisos:** solo la posición. No usa internet ni graba actividades.

Fallos y sugerencias, al correo de contacto. El código y el método de generación de los datos: https://github.com/TacticalPro/calle-app

Datos: © colaboradores de OpenStreetMap (ODbL). Fuente: Dirección General del Catastro.

**Novedades (3.5.2):** los nombres de calle largos ya no cierran la app cuando el reloj lleva más de unos 25 días encendido sin reiniciarse. **Subida el 2026-10-27 (tarde) y aprobada ese día:** corrige el cierre de `Texto.trozo` con `System.getTimer()` negativo (`ead5c7b`).

**Novedades (3.5.1):** primera versión, para los fēnix 5, 5S, 6 y 6S.

## English

**Name:** Calles A Coruña (offline)

**Fully offline.** The street and the door number on your wrist, across the whole province of A Coruña, with no phone, no signal and no data. The whole street map ships inside the app. For when you have to say where you are (a 112 call, someone waiting for you) and your phone is no help.

For fēnix 5, 5S, 6 and 6S. Watches with more memory have «Calles Galicia», covering all of Galicia.

**What it tells you at a glance:**
- The street, the nearest door number and the two cross streets you are between. At a junction, the corner.
- Outside town, the nearest village or place and the parish; in towns, the neighbourhood. Even with no street nearby, it tells you where you are.
- The nearest hospital with A&E, with arrow, compass ring and straight-line distance.
- Your UTM coordinates, rounded like the watch's own.
- Notes with START: time, place and coordinates, kept on the watch, with guidance back to each one.
- A large clock, so it works as a watch too.

**Why offline:**
- It works where your phone doesn't: in the hills, in a village with no signal, or with the phone left at home.
- It never waits for a network: as soon as the watch has a position, you have the address.
- Your position never leaves the watch, because the app has no internet access.

**Coverage:** door numbers and cross streets in A Coruña, Santiago de Compostela, Ferrol, Narón and Ribeira. In the rest of the province, the street or road, the village and the parish. Door numbers come from OpenStreetMap and, in Santiago de Compostela and its surroundings, also from the Spanish Cadastre. Many villages still have no door numbers on the map: there it gives the street, village and parish, but no number. The interface is in Spanish.

**Permissions:** position only. No internet use and no activity recording.

Please send bugs and suggestions to the contact email. Source code and how the data is built: https://github.com/TacticalPro/calle-app

Data: © OpenStreetMap contributors (ODbL). Source: Dirección General del Catastro.

**What's new (3.5.2):** Fixes a crash with long street names when the watch had been on for more than about 25 days without a restart.

**What's new (3.5.1):** first release, for the fēnix 5, 5S, 6 and 6S.
