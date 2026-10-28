# Calles Galicia — textos de la Connect IQ Store

App del catálogo por zonas (`tools/catalogo.json`): `APP=galicia ./ciq.sh tienda` → `bin/calle-galicia.iq`.
Subida nueva en el portal (no es una versión de la beta), con el id `50da24c1…`. **Subida el 2026-10-26** como
3.4.0: [ficha en la tienda](https://apps.garmin.com/apps/13c5de1f-6ebf-4264-8b3f-91a8b0bf33dd), aprobada el mismo
día. **3.5.0 subida el 2026-10-26** con *Upload New Version* (commit `fa70bc9`; 120 MB, 20 piezas, firma «Verified»
en el portal): añade los fēnix 6 Pro y 5X/5 Plus (abajo). Pendiente de aprobación; al aprobarse, comprobar en la ficha los
relojes nuevos. Subida por trozos con la extensión de Chrome (método en `calle-madrid.md`). La beta privada «Calles Galicia (offline) (beta)» (id `19ddcb3e…`) es solo del fēnix 7X Pro.

- **Título:** «Calles Galicia (offline)», en inglés y en español (el autor, 2026-10-26; antes «CALLE Galicia (offline)»).
  Que no usa red es su punto fuerte. La beta pasa a «Calles Galicia (offline) (beta)» con *Edit Details*.
- **Versión:** 3.5.1 (textos que no se salen del borde en las pantallas pequeñas; 3.5.0, los fēnix 6 Pro y 5X/5 Plus;
  3.4.0, la primera pública, con la interfaz nueva de P73).
- **Relojes:** la familia fēnix 7 (7, 7S, 7X, 7 Pro, 7S Pro, 7X Pro y los dos Pro sin Wi-Fi), con 108/108 tests
  en el 7S, el 7 y el 7X Pro. Desde la 3.5.0, además, los de 1,25 MB y tope de 254 recursos, con la variante `b`
  (Galicia entera en 216 recursos, `VARIANTE=b REGION=galicia ./ciq.sh datos`): fēnix 6 Pro, 6S Pro y 6X Pro, 5X, 5 Plus,
  5S Plus y 5X Plus, con 54/54 tests en los siete. Los de 128 KB (fēnix 5, 5S, 6 y 6S) aún no: P73. El `.iq` se sube a
  mano, porque el navegador automatizado no pasa de 10 MB.
- **Ficha:** categoría Navigation, sin migración automática a relojes nuevos, avisos de reseñas al correo de contacto.
- **Portada:** la carátula «el marcador en el cruce», sobre el callejero real del casco de Santiago, con «CALLES / GALICIA / LA
  CALLE Y EL PORTAL, SIN COBERTURA», todo en mayúsculas (elegida el 2026-10-25). Se genera con `tools/caratula.py --instalar`, que pone
  también el icono del lanzador.
- **Pantallas** en `docs/tienda/galicia/` (`tools/mockup.py --ficha galicia`, en el 7X Pro), por este orden: `ficha_1.png` a
  `ficha_4.png`. Cada escena es lo que dicen los datos reales en un sitio público (`tools/ref.py`):
  1. Santiago, Rúa do Franco 33, Casco Histórico, entre la Ruela de Paio o Eremita y la Rúa da Raíña;
  2. A Coruña, Rúa Real 26, A Pescaría, entre la Rúa Alcalde Canuto Berea y la Rúa Torreiro;
  3. la aldea de O Carrio (parroquia de Camposancos), sin calle a 50 m, con su UTM;
  4. desde la Rúa dos Campos (Pontevedra), el hospital con urgencias más cercano: el Montecelo, a 1,5 km hacia el SE.
- El portal puede avisar «Signature check failed» en la primera subida de una app nueva: es un fallo conocido suyo.
  La firma se comprueba en local con `openssl dgst -sha256 -verify dev_key.pub -keyform DER -signature manifest.sig2
  manifest.xml`.

Atribución obligatoria (OSM y Catastro): no se quita de ninguna versión.
Los datos de OSM vienen del extracto de Geofabrik; la fuente y la licencia siguen siendo OSM (ODbL).

**Source Code URL:** https://github.com/TacticalPro/calle-app

## Español

**Nombre:** Calles Galicia (offline)

**Sin conexión.** El callejero de Galicia entera viaja dentro de la app: la calle, el número de portal y las calles a
cada lado, sin teléfono, sin cobertura y sin datos móviles. Y fuera de la ciudad, la aldea y la parroquia.

**Por qué sin conexión:**
- Funciona donde el móvil no llega: sin cobertura, sin datos o con el teléfono en casa.
- No espera a ninguna red ni a ningún servidor: en cuanto el reloj tiene posición, tiene la dirección.
- Su posición es solo suya: la app no tiene acceso a internet, así que no puede enviarla a ningún sitio.

- En qué calle está, el portal más cercano y entre qué calles; en un cruce, la esquina.
- Parroquia, aldea o lugar más cercano, y barrio en las ciudades. Lejos de cualquier calle, dice dónde está igualmente.
- Hospital con urgencias más cercano, y comisaría o cuartel de la Guardia Civil más cercanos: flecha y anillo de
  brújula, y distancia en línea recta.
- Coordenadas UTM, redondeadas como las del propio reloj.
- Anotaciones con START: hora, lugar y coordenadas, guardadas en el reloj, y guía para volver a cada una.
- Hora grande, para usarla también como reloj.

Zona: Galicia entera, las cuatro provincias. Relojes: familia fēnix 7, fēnix 6 Pro, 6S Pro y 6X Pro, y fēnix 5X,
5 Plus, 5S Plus y 5X Plus. Se irán añadiendo más.

Los números de portal salen de OpenStreetMap y, en Santiago y su entorno, también del Catastro. En muchos pueblos y
aldeas el mapa aún no tiene números: ahí la app da la calle, la aldea y la parroquia, pero no el portal.

Permisos: solo la posición. Sin acceso a internet y sin grabar actividades.

Los fallos y las sugerencias, al correo de contacto.

Código y método de generación de los datos: https://github.com/TacticalPro/calle-app

Datos: © colaboradores de OpenStreetMap (ODbL). Fuente: Dirección General del Catastro.

**Novedades (3.5.2):** los nombres de calle largos ya no cierran la app cuando el reloj lleva más de unos 25 días encendido sin reiniciarse. **Subida el 2026-10-27 (tarde), en revisión:** corrige el cierre de `Texto.trozo` con `System.getTimer()` negativo (`a5fe21f`).

**Novedades (3.5.1):** los nombres largos ya no se cortan en las pantallas redondas pequeñas.

**Novedades (3.5.0):** ahora también en los fēnix 6 Pro, 6S Pro y 6X Pro, y en los fēnix 5X, 5 Plus, 5S Plus y 5X
Plus, con Galicia entera.

**Novedades (3.4.0):** primera versión pública. Galicia entera, con parroquias y aldeas, y números de portal del
Catastro en Santiago y su entorno.

## English

**Name:** Calles Galicia (offline)

**Fully offline.** The street map of all of Galicia ships inside the app: street name, door number and the streets
on each side, with no phone, no signal and no mobile data. Outside town, the village and the parish.

**Why offline:**
- It works where your phone doesn't: no signal, no data, or the phone left at home.
- It never waits for a network or a server: as soon as the watch has a position, you have the address.
- Your position stays yours: the app has no internet access, so it cannot send it anywhere.

- The street you are on, the nearest door number and the cross streets on each side; at a junction, the corner.
- Parish, nearest village or place, and neighbourhood in towns. Far from any street, it still tells you where you are.
- Nearest hospital with A&E, and nearest police station or Guardia Civil post: arrow, compass ring and
  straight-line distance.
- UTM coordinates, rounded like the watch's own.
- Notes with START: time, place and coordinates, kept on the watch, with guidance back to each one.
- Large clock, so it works as a watch too.

Area: all of Galicia, the four provinces. Watches: the fēnix 7 family, fēnix 6 Pro, 6S Pro and 6X Pro, and fēnix 5X,
5 Plus, 5S Plus and 5X Plus. More will follow. The interface is in Spanish.

Door numbers come from OpenStreetMap and, in Santiago de Compostela and its surroundings, also from the Spanish
Cadastre. Many villages still have no door numbers on the map: there the app gives the street, village and parish,
but no number.

Permissions: position only. No internet access and no activity recording.

Please send bugs and suggestions to the contact email.

Source code and how the data is built: https://github.com/TacticalPro/calle-app

Data: © OpenStreetMap contributors (ODbL). Source: Dirección General del Catastro.

**What's new (3.5.2):** Fixes a crash with long street names when the watch had been on for more than about 25 days without a restart.

**What's new (3.5.1):** long names no longer cut off on small round screens.

**What's new (3.5.0):** now also on the fēnix 6 Pro, 6S Pro and 6X Pro, and on the fēnix 5X, 5 Plus, 5S Plus and
5X Plus, with all of Galicia.

**What's new (3.4.0):** first public release. All of Galicia, with parishes and villages, and Cadastre door numbers
in Santiago de Compostela and its surroundings.
