# CALLE Galicia — textos de la Connect IQ Store

App del catálogo por zonas (`tools/catalogo.json`): `APP=galicia ./ciq.sh tienda` → `bin/calle-galicia.iq`.
Subida nueva en el portal (no es una versión de la beta), con el id `50da24c1…`. **Borrador del 2026-10-25,
sin subir.** La beta privada «CALLE Galicia (beta)» (id `19ddcb3e…`) es solo del fēnix 7X Pro.

- **Versión:** 3.3.2, la misma que la beta probada en la muñeca.
- **Relojes:** la familia fēnix 7 (7, 7S, 7X, 7 Pro, 7S Pro, 7X Pro y los dos Pro sin Wi-Fi), con 108/108 tests
  en el 7S, el 7 y el 7X Pro. El `.iq` pesa 87 MB: se sube a mano, porque el navegador automatizado no pasa de 10 MB.
- **Ficha:** categoría Navigation, sin migración automática a relojes nuevos, avisos de reseñas al correo de contacto.
- **Imágenes** en `docs/tienda/galicia/` (`tools/mockup.py --ficha galicia`, en el 7X Pro), por este orden: `portada_500.png`
  y `ficha_1.png` a `ficha_4.png`. Cada escena es lo que dicen los datos reales en un sitio público (`tools/ref.py`):
  1. Santiago, Rúa do Franco 33, Casco Histórico, entre la Ruela de Paio o Eremita y la Rúa da Raíña (también en la portada);
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

**Nombre:** CALLE Galicia

La calle, el número de portal y las calles a cada lado, sin teléfono ni cobertura. Y fuera de la ciudad, la aldea
y la parroquia.

- En qué calle está, el portal más cercano y entre qué calles; en un cruce, la esquina.
- Parroquia, aldea o lugar más cercano, y barrio en las ciudades. Lejos de cualquier calle, dice dónde está igualmente.
- Hospital con urgencias más cercano, y comisaría o cuartel de la Guardia Civil más cercanos: flecha y anillo de
  brújula, y distancia en línea recta.
- Coordenadas UTM, redondeadas como las del propio reloj.
- Anotaciones con START: hora, lugar y coordenadas, guardadas en el reloj, y guía para volver a cada una.
- Hora grande, para usarla también como reloj.

Zona: Galicia entera, las cuatro provincias, en toda la familia fēnix 7. Se irán añadiendo relojes.

Los números de portal salen de OpenStreetMap y, en Santiago y su entorno, también del Catastro. En muchos pueblos y
aldeas el mapa aún no tiene números: ahí la app da la calle, la aldea y la parroquia, pero no el portal.

Privacidad: solo pide el permiso de posición. No tiene red: la posición no sale nunca del reloj. No graba
actividades.

Primera versión: los fallos y las sugerencias, al correo de contacto.

Código y método de generación de los datos: https://github.com/TacticalPro/calle-app

Datos: © colaboradores de OpenStreetMap (ODbL). Fuente: Dirección General del Catastro.

**Novedades (3.3.2):** primera versión pública. Galicia entera, con parroquias y aldeas, y números de portal del
Catastro en Santiago y su entorno.

## English

**Name:** CALLE Galicia

Street name, door number and the streets on each side, with no phone and no signal. Outside town, the village and
the parish.

- The street you are on, the nearest door number and the cross streets on each side; at a junction, the corner.
- Parish, nearest village or place, and neighbourhood in towns. Far from any street, it still tells you where you are.
- Nearest hospital with A&E, and nearest police station or Guardia Civil post: arrow, compass ring and
  straight-line distance.
- UTM coordinates, rounded like the watch's own.
- Notes with START: time, place and coordinates, kept on the watch, with guidance back to each one.
- Large clock, so it works as a watch too.

Area: all of Galicia, the four provinces, on the whole fēnix 7 family. More watches will follow. The interface is in
Spanish.

Door numbers come from OpenStreetMap and, in Santiago de Compostela and its surroundings, also from the Spanish
Cadastre. Many villages still have no door numbers on the map: there the app gives the street, village and parish,
but no number.

Privacy: the only permission is position. No network access: your position never leaves the watch. No activity
recording.

First release: please send bugs and suggestions to the contact email.

Source code and how the data is built: https://github.com/TacticalPro/calle-app

Data: © OpenStreetMap contributors (ODbL). Source: Dirección General del Catastro.

**What's new (3.3.2):** first public release. All of Galicia, with parishes and villages, and Cadastre door numbers
in Santiago de Compostela and its surroundings.
