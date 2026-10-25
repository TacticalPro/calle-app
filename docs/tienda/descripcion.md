# CALLE — textos de la Connect IQ Store

Imágenes: `portada_500.png` y `ficha_1..4.png`, en este orden (`tools/mockup.py --ficha`).
Atribución obligatoria (la de las tres fuentes de datos): no se quita de ninguna versión.

## Español

**Nombre:** CALLE (beta)

La calle, el número de portal y las calles a cada lado, sin teléfono ni cobertura.

- En qué calle está, el portal más cercano y entre qué calles; en un cruce, la esquina.
- Barrio y distrito en Madrid; barrio, lugar y parroquia en Santiago de Compostela.
- Hospital con urgencias y comisaría más cercanos: flecha y anillo de brújula, y distancia en línea recta.
- Coordenadas UTM, redondeadas como las del propio reloj.
- Anotaciones con START: hora, lugar y coordenadas, guardadas en el reloj, y guía para volver a cada una.
- Zona automática por la posición, o fija desde el menú o desde Garmin Connect.
- Hora grande, para usarla también como reloj.

Privacidad: solo pide el permiso de posición. No tiene red: la posición no sale nunca del reloj. No graba
actividades.

Zonas: Santiago de Compostela y alrededores, y el término municipal de Madrid. En el fēnix 6X, una parte
de Madrid: una parte de la ciudad.

Datos: © colaboradores de OpenStreetMap (ODbL). Fuente: Dirección General del Catastro. Fuente:
Ayuntamiento de Madrid (datos.madrid.es), CC BY 4.0.

## English

**Name:** CALLE (beta)

Street name, door number and the streets on each side, with no phone and no signal.

- The street you are on, the nearest door number and the cross streets on each side; at a junction, the
  corner.
- Neighbourhood and district in Madrid; neighbourhood, place and parish in Santiago de Compostela.
- Nearest hospital with A&E and nearest police station: arrow, compass ring and straight-line distance.
- UTM coordinates, rounded like the watch's own.
- Notes with START: time, place and coordinates, kept on the watch, with guidance back to each one.
- Area chosen automatically from your position, or fixed from the menu or Garmin Connect.
- Large clock, so it works as a watch too.

Privacy: the only permission is position. No network access: your position never leaves the watch. No
activity recording.

Areas: Santiago de Compostela and surroundings, and the municipality of Madrid. On the fēnix 6X, part
Madrid: part of the city.

Data: © OpenStreetMap contributors (ODbL). Source: Dirección General del Catastro. Source: Ayuntamiento de
Madrid (datos.madrid.es), CC BY 4.0.

La beta 3.0.0 (subida el 2026-10-24) lleva todavía en el 6X Santiago y Madrid Centro, y su ficha lo dice así.
Estos textos son los de la próxima subida (3.1.0: anillo de brújula e «Ir a una anotación»).

## Pendiente antes de hacerla pública

- **ODbL de OpenStreetMap.** El callejero que viaja en la app es una «base de datos derivada», y su uso
  público obliga a ofrecerla o a ofrecer el método para obtenerla (apartado 4.6). La beta privada no es uso
  público. La vía elegida es ofrecer el método:
  - `README.md` y `LICENSE` (MIT) ya están preparados;
  - repositorio publicado (https://github.com/TacticalPro/calle-app); falta poner su URL en el campo
    «Source Code URL» de la ficha;
  - en la descripción, una línea más: «Código y método de generación de los datos: https://github.com/TacticalPro/calle-app» y, en inglés,
    «Source code and how the data is built: https://github.com/TacticalPro/calle-app».
- **Subida nueva con el id de producción** (`./ciq.sh package`), no una versión nueva de la beta (el portal
  lo exige). Título «CALLE», sin «(beta)», y sin el párrafo de la beta.
- **Correo público de contacto** de la ficha: decidir si se mantiene.
