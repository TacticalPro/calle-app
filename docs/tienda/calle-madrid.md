# Calles Madrid — textos de la Connect IQ Store

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

**3.4.0 (2026-10-25): la interfaz de Calles Galicia (P73).** Mismos relojes y mismos datos que la 3.2.0; cambian la
pantalla, la carátula (el marcador ámbar sobre el callejero de Sol, `tools/caratula.py --instalar`) y el icono.
Las cinco imágenes, regeneradas (`mockup.py --ficha`). El `.iq` (`bin/calle-madrid.iq`, 52,5 MB, firma verificada)
se subió el mismo día con *Upload New Version* mientras la 3.2.0 seguía en revisión: el portal la verificó
(firma, 11 dispositivos) y ya da «Latest app version: 3.4.0». Novedades, carátula y las cuatro pantallas, cambiadas en
el mismo envío. **Subida de un `.iq` de más de 10 MB con la extensión de Chrome:** trocear con `split -b 9000000`,
subir cada trozo a un `<input type=file>` auxiliar creado por JS, recomponer con `new Blob(trozos)`, comprobar el
SHA-256 en la página y asignarlo al campo real con `DataTransfer`. Servirlo desde localhost no vale: la CSP
(`connect-src`) del portal lo bloquea.

**Aprobada la 3.4.0 (2026-10-26).** Ese mismo día, con *Edit Details*: título «Calles Madrid (offline)», carátula
«CALLES / MADRID» y la descripción de abajo (la de la tienda era aún la de la 3.1.0). **3.4.1 subida el 2026-10-26**
(*Upload New Version*, mismos 9 relojes y 14 piezas, firma verificada por el portal): solo cambia el nombre en el
reloj. Antes hubo que rehacer `source-gen-c` (`REGION=madrid VARIANTE=c ./ciq.sh datos --comun`): estaba generado
antes de `ZPREF` y el 6X Pro no compilaba.

**Beta de prueba con 54 relojes (2026-10-30, P98).** «Calles Madrid (offline) (beta)», app aparte con su `beta_id`
(`98051658…`; `APP=madrid ./ciq.sh beta` → `bin/calle-madrid-beta.iq`), id de la página en el portal
`e8dc7afc-ea4b-43d2-8d77-1d298e1d46b7`. Versión 3.4.5 (interna 1), con los 54 relojes del catálogo y 66 piezas:
245.034.465 B, sha1 `ad87c084cc16c832faf1e718b620a4e1ba3b4f73`, subida en 28 trozos de 9 MB (método arriba). Es la
prueba de un paquete por encima de los 174 MB de Barcelona y entró: el portal la deja en PENDINGSCAN, con ~7,9 MB por
reloj en la variante normal y 4,6 MB en la c. **El primer «Continue» devolvió «trouble communicating with our servers» y
el segundo, con el mismo fichero, entró**, como con Barcelona: antes de reintentar, comprobar que la «Latest app
version» no ha cambiado, para no subirla dos veces.

**Título «Calles Madrid (offline)»** (el autor, 2026-10-26; antes «CALLE Madrid (offline)»: que no usa red es su
punto fuerte). Se cambia con *Edit Details*, junto con la carátula «CALLES / MADRID», en cuanto Garmin apruebe la
versión en revisión: no se toca mientras tanto. En el reloj, «Calles Madrid» llega con la próxima versión.

Atribución obligatoria (OSM y Ayuntamiento de Madrid): no se quita de ninguna versión. El Catastro no
aparece, porque solo se usa en Santiago.

**Source Code URL:** https://github.com/TacticalPro/calle-app

## Español

**Nombre:** Calles Madrid (offline)

**Sin conexión.** El callejero de Madrid entero viaja dentro de la app: la calle, el número de portal y las calles a
cada lado, sin teléfono, sin cobertura y sin datos móviles.

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

Zona: el término municipal de Madrid entero, en el fēnix 6X y en toda la familia fēnix 7. Se irán añadiendo
relojes.

Permisos: solo la posición. Sin acceso a internet y sin grabar actividades.

Primera versión: los fallos y las sugerencias, al correo de contacto.

Código y método de generación de los datos: https://github.com/TacticalPro/calle-app

Datos: © colaboradores de OpenStreetMap (ODbL). Fuente: Ayuntamiento de Madrid (datos.madrid.es), CC BY 4.0.

**Novedades (3.4.4):** Sin GPS, la guía al hospital o a la comisaría ya no parte de una posición de hace horas: si el dato tiene más de 15 s, la distancia sale en gris y con su edad. En el monte gasta menos batería, y la distancia norte-sur es exacta a la latitud. **Subida el 2026-10-28** con *Upload New Version* (52,6 MB, 14 piezas, SHA-256 `14319aa9…`; API: 3.4.4, interna 7): `fa6a24f`. Entró con las novedades de la 3.4.3; corregidas el mismo día con *Edit Details* (API: ES/EN nuevas, sigue la interna 7).

**Novedades (3.4.3):** los nombres de calle largos ya no cierran la app cuando el reloj lleva más de unos 25 días encendido sin reiniciarse. **Subida el 2026-10-27 (tarde), en revisión:** corrige el cierre de `Texto.trozo` con `System.getTimer()` negativo (`a5fe21f`).

**Novedades (3.4.2):** los nombres largos ya no se cortan en las pantallas redondas pequeñas.

**Novedades (3.4.1):** la app pasa a llamarse «Calles Madrid» también en el reloj.

**Novedades (3.4.0):** pantalla nueva: hora grande, calidad del GPS en un arco, número de portal en una pastilla
ámbar y rótulos en mayúsculas, más legibles con un vistazo. Icono nuevo.

**Novedades (3.2.0):** Madrid entero, también en el fēnix 6X, y llega la familia fēnix 7 (7, 7S, 7X y Pro).
Datos más compactos.

## English

**Name:** Calles Madrid (offline)

**Fully offline.** The street map of all of Madrid ships inside the app: street name, door number and the streets
on each side, with no phone, no signal and no mobile data.

**Why offline:**
- It works where your phone doesn't: no signal, no data, or the phone left at home.
- It never waits for a network or a server: as soon as the watch has a position, you have the address.
- Your position stays yours: the app has no internet access, so it cannot send it anywhere.

- The street you are on, the nearest door number and the cross streets on each side; at a junction, the
  corner.
- Neighbourhood and district.
- Nearest hospital with A&E and nearest police station: arrow, compass ring and straight-line distance.
- UTM coordinates, rounded like the watch's own.
- Notes with START: time, place and coordinates, kept on the watch, with guidance back to each one.
- Large clock, so it works as a watch too.

Area: the whole municipality of Madrid, on the fēnix 6X and the whole fēnix 7 family. More watches will
follow. The interface is in Spanish.

Permissions: position only. No internet access and no activity recording.

First release: please send bugs and suggestions to the contact email.

Source code and how the data is built: https://github.com/TacticalPro/calle-app

Data: © OpenStreetMap contributors (ODbL). Source: Ayuntamiento de Madrid (datos.madrid.es), CC BY 4.0.

**What's new (3.4.4):** Without GPS, guidance to the hospital or police station no longer starts from a position hours old: if the fix is more than 15 s old, the distance turns grey and shows its age. Less battery use in open country, and exact north-south distances.

**What's new (3.4.3):** Fixes a crash with long street names when the watch had been on for more than about 25 days without a restart.

**What's new (3.4.2):** long names no longer cut off on small round screens.

**What's new (3.4.1):** the app is now called «Calles Madrid» on the watch too.

**What's new (3.4.0):** new screen: large clock, GPS quality as an arc, the door number on an amber badge and
upper-case labels, easier to read at a glance. New icon.

**What's new (3.2.0):** all of Madrid, now on the fēnix 6X too, and the fēnix 7 family (7, 7S, 7X and Pro).
Smaller data.

