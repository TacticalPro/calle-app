# CALLE Madrid — textos de la Connect IQ Store

Primera app del catálogo por zonas (`tools/catalogo.json`): `APP=madrid ./ciq.sh tienda` → `bin/calle-madrid.iq`.
Subida nueva en el portal (no es una versión de la beta), con el id `cc8abcb6…`.
**Subida el 2026-10-25** como 3.1.0: [ficha en la tienda](https://apps.garmin.com/apps/f37fdd3d-8c12-435a-b5fd-9a0e967434ca),
pendiente de aprobación (el portal da hasta 3 días). Categoría Navigation, sin migración automática a relojes nuevos.
El portal avisa «Signature check failed» en la primera subida de una app nueva: es un fallo conocido suyo; la firma se
comprueba en local con `openssl dgst -sha256 -verify dev_key.pub -keyform DER -signature manifest.sig2 manifest.xml`.

**Primera versión (3.1.0): solo el fēnix 6X**, con una parte de Madrid. Imágenes: `portada_500.png`,
`ficha_1.png`, `ficha_3.png` y `ficha_4.png`.

**3.2.0 (2026-10-25): el 6X y la familia fēnix 7, todos con Madrid entero.** Es *Upload New Version* sobre la
misma app. El `.iq` pesa 52,5 MB: lo sube el autor a mano, porque el navegador automatizado no pasa de 10 MB.
La `ficha_2.png` (Argüelles) entra ahora en las imágenes: las cinco, en orden.

**3.4.0 (2026-10-25): la interfaz de CALLE Galicia (P73).** Mismos relojes y mismos datos que la 3.2.0; cambian la
pantalla, la carátula (el marcador ámbar sobre el callejero de Sol, `tools/caratula.py --instalar`) y el icono.
Las cinco imágenes, regeneradas (`mockup.py --ficha`). El `.iq` (`bin/calle-madrid.iq`, 52,5 MB, firma verificada)
lo sube el autor a mano con *Upload New Version*, cuando la 3.2.0 salga de revisión.

**Título «CALLE Madrid (offline)»** (decisión del autor, 2026-10-25: que no usa red es su punto fuerte). Se cambia
con *Edit Details* en cuanto Garmin apruebe la 3.2.0: no se toca mientras esté en revisión.

Atribución obligatoria (OSM y Ayuntamiento de Madrid): no se quita de ninguna versión. El Catastro no
aparece, porque solo se usa en Santiago.

**Source Code URL:** https://github.com/TacticalPro/calle-app

## Español

**Nombre:** CALLE Madrid

La calle, el número de portal y las calles a cada lado, sin teléfono ni cobertura.

- En qué calle está, el portal más cercano y entre qué calles; en un cruce, la esquina.
- Barrio y distrito.
- Hospital con urgencias y comisaría más cercanos: flecha y anillo de brújula, y distancia en línea recta.
- Coordenadas UTM, redondeadas como las del propio reloj.
- Anotaciones con START: hora, lugar y coordenadas, guardadas en el reloj, y guía para volver a cada una.
- Hora grande, para usarla también como reloj.

Zona: el término municipal de Madrid entero, en el fēnix 6X y en toda la familia fēnix 7. Se irán añadiendo
relojes.

Privacidad: solo pide el permiso de posición. No tiene red: la posición no sale nunca del reloj. No graba
actividades.

Primera versión: los fallos y las sugerencias, al correo de contacto.

Código y método de generación de los datos: https://github.com/TacticalPro/calle-app

Datos: © colaboradores de OpenStreetMap (ODbL). Fuente: Ayuntamiento de Madrid (datos.madrid.es), CC BY 4.0.

**Novedades (3.4.0):** pantalla nueva: hora grande, calidad del GPS en un arco, número de portal en una pastilla
ámbar y rótulos en mayúsculas, más legibles con un vistazo. Icono nuevo.

**Novedades (3.2.0):** Madrid entero, también en el fēnix 6X, y llega la familia fēnix 7 (7, 7S, 7X y Pro).
Datos más compactos.

## English

**Name:** CALLE Madrid

Street name, door number and the streets on each side, with no phone and no signal.

- The street you are on, the nearest door number and the cross streets on each side; at a junction, the
  corner.
- Neighbourhood and district.
- Nearest hospital with A&E and nearest police station: arrow, compass ring and straight-line distance.
- UTM coordinates, rounded like the watch's own.
- Notes with START: time, place and coordinates, kept on the watch, with guidance back to each one.
- Large clock, so it works as a watch too.

Area: the whole municipality of Madrid, on the fēnix 6X and the whole fēnix 7 family. More watches will
follow. The interface is in Spanish.

Privacy: the only permission is position. No network access: your position never leaves the watch. No
activity recording.

First release: please send bugs and suggestions to the contact email.

Source code and how the data is built: https://github.com/TacticalPro/calle-app

Data: © OpenStreetMap contributors (ODbL). Source: Ayuntamiento de Madrid (datos.madrid.es), CC BY 4.0.

**What's new (3.4.0):** new screen: large clock, GPS quality as an arc, the door number on an amber badge and
upper-case labels, easier to read at a glance. New icon.

**What's new (3.2.0):** all of Madrid, now on the fēnix 6X too, and the fēnix 7 family (7, 7S, 7X and Pro).
Smaller data.

