# Usos de las Calles offline — borrador para la tienda (sin publicar)

Ejemplos de uso para las apps Calles publicadas (2026-10-31). **Borrador: no se ha pegado en
ninguna ficha.** Cuando se apruebe, se pega con *Edit Details* (no hace falta versión nueva) y se comprueba en la API.

**Base:** los textos vivos de la tienda, leídos hoy en la API pública (`/api/appsLibraryExternalServices/api/asw/apps/<id>`,
`appLocalizations[].description`). Las copias de `calle-*.md` van por detrás en la línea de relojes (Galicia y Madrid
ya dicen «54 en total» en la tienda); los recuentos de abajo son sobre el texto vivo.

**Lo que hacen de verdad (comprobado en código y datos, no en la ficha):**

- **Sin teléfono ni cobertura:** el callejero va dentro; sin permiso de red (`manifest.xml`: solo `Positioning`).
- **Carretera:** en autopista y autovía muestran la referencia de la vía (`tools/build_callejero.py`, `nombre_via`:
  `motorway`/`trunk` con `ref`); en los datos generados salen «AP-9» (Galicia) y «M-30» (Madrid). **No hay punto
  kilométrico:** el único «km» de la app es la distancia de la guía (`source/Ir.mc`). Ese dato lo da Calles España.
- **Portal:** el más cercano a la posición, no una búsqueda de direcciones. Madrid, del callejero del Ayuntamiento;
  Galicia, de OpenStreetMap y del Catastro en Santiago (muchas aldeas sin números); A Coruña y Pontevedra, solo en
  los municipios de la lista «Dónde llega» (variante `c5`, `tools/regiones.json`: fuera de ellos, sin portales).
- **Entre qué calles, barrio, parroquia y aldea:** como dicen ya las fichas; en el monte, la aldea, la parroquia y la
  UTM (Galicia, A Coruña, Pontevedra). Madrid: barrio y distrito.
- **Nada de «exacta»:** la dirección es la calle y el portal más cercanos; la posición es la UTM, con la precisión del GPS.

**Tronco común con Calles España** (acordado con su ficha): emergencia o accidente, turismo, reparto («ante qué portal
está»), y la frase del 112. Diferencias reales: las offline dicen «sin teléfono ni cobertura» y «en qué vía está,
aunque no el kilómetro»; España, el kilómetro y que necesita el teléfono.

«Sin validez jurídica» no está en las offline y no se añade (es una condición de CartoCiudad, que estas no usan).

**Betas** (Murcia, Barcelona, C. Valenciana): sin tocar. Son privadas y no tienen público al que explicarle los usos.

## Recuentos (caracteres, sin Markdown: actual → con usos → con usos y reciprocidad)

Tope de 4.000 por descripción, el que se ha fijado. Todas quedan por debajo.

| App | Fichero | ES | EN |
|---|---|---|---|
| Calles Galicia (offline) | `calle-galicia.md` | 1.813 → 2.339 → 2.494 | 1.800 → 2.345 → 2.509 |
| Calles Madrid (offline) | `calle-madrid.md` | 1.439 → 1.912 → 2.088 | 1.436 → 1.938 → 2.121 |
| Calles A Coruña (offline) | `calle-coruna.md` | 1.915 → 2.492 → 2.652 | 1.994 → 2.583 → 2.752 |
| Calles Pontevedra (offline) | `calle-pontevedra.md` | 1.848 → 2.425 → 2.585 | 1.879 → 2.468 → 2.637 |

## Calles Galicia (offline)

Va justo antes del párrafo que empieza por «Zona:» (ES) y «Area:» (EN). La reciprocidad, justo
después de ese párrafo.

**Español**

```text
Para qué sirve, también sin teléfono ni cobertura, en toda Galicia:
- Decir dónde está ante una emergencia o un accidente: la calle y el portal más cercano, y entre qué calles; en el monte, la aldea, la parroquia y sus coordenadas UTM.
- En una autovía o autopista, decir en qué vía está («AP-9»), aunque no el kilómetro.
- Orientarse haciendo turismo.
- Saber ante qué portal está en un reparto, donde el mapa tiene números.

Ante una emergencia, llame al 112: la app le ayuda a decir dónde está, no sustituye a la llamada.
```

**English**

```text
What it is for, with no phone and no signal too, across Galicia:
- Saying where you are in an emergency or after an accident: the street, the nearest door number and the cross streets; in the hills, the village, the parish and your UTM coordinates.
- On a motorway, saying which road you are on («AP-9»), though not the kilometre.
- Finding your way as a tourist.
- Knowing which door you are at on a delivery round, where the map has door numbers.

In an emergency, call 112: the app helps you say where you are; it does not replace the call.
```

**Reciprocidad (aplicar cuando Calles España esté aprobada):**

```text
Fuera de Galicia, o en otros relojes, «Calles España» da la calle, el portal y, en carretera, el punto kilométrico en toda España, a través del teléfono.
```

```text
Outside Galicia, or on other watches, «Calles España» gives the street, the door number and, on roads, the kilometre marker anywhere in Spain, through your phone.
```

## Calles Madrid (offline)

Va justo antes del párrafo que empieza por «Zona:» (ES) y «Area:» (EN). La reciprocidad, justo
después de ese párrafo.

**Español**

```text
Para qué sirve, también sin teléfono ni cobertura, en todo el término municipal:
- Decir dónde está ante una emergencia o un accidente: la calle, el portal más cercano y entre qué calles, y sus coordenadas UTM.
- En la M-30 o en una autovía, decir en qué vía está («M-30»), aunque no el kilómetro.
- Orientarse haciendo turismo.
- Saber ante qué portal está en un reparto.

Ante una emergencia, llame al 112: la app le ayuda a decir dónde está, no sustituye a la llamada.
```

**English**

```text
What it is for, with no phone and no signal too, across the whole municipality:
- Saying where you are in an emergency or after an accident: the street, the nearest door number and the cross streets, and your UTM coordinates.
- On the M-30 or a motorway, saying which road you are on («M-30»), though not the kilometre.
- Finding your way as a tourist.
- Knowing which door you are at on a delivery round.

In an emergency, call 112: the app helps you say where you are; it does not replace the call.
```

**Reciprocidad (aplicar cuando Calles España esté aprobada):**

```text
Fuera del término municipal de Madrid, o en otros relojes, «Calles España» da la calle, el portal y, en carretera, el punto kilométrico en toda España, a través del teléfono.
```

```text
Outside the municipality of Madrid, or on other watches, «Calles España» gives the street, the door number and, on roads, the kilometre marker anywhere in Spain, through your phone.
```

## Calles A Coruña (offline)

Va justo antes del párrafo que empieza por «Dónde llega:» (ES) y «Coverage:» (EN). La reciprocidad, justo
después de ese párrafo.

**Español**

```text
Para qué sirve, también sin teléfono ni cobertura, en toda la provincia:
- Decir dónde está ante una emergencia o un accidente: en las ciudades de abajo, la calle, el portal más cercano y entre qué calles; en el resto, la calle o la carretera, la aldea, la parroquia y sus coordenadas UTM.
- En una autovía o autopista, decir en qué vía está («AP-9»), aunque no el kilómetro.
- Orientarse haciendo turismo.
- Saber ante qué portal está en un reparto, en las ciudades de abajo.

Ante una emergencia, llame al 112: la app le ayuda a decir dónde está, no sustituye a la llamada.
```

**English**

```text
What it is for, with no phone and no signal too, across the province:
- Saying where you are in an emergency or after an accident: in the towns listed below, the street, the nearest door number and the cross streets; elsewhere, the street or road, the village, the parish and your UTM coordinates.
- On a motorway, saying which road you are on («AP-9»), though not the kilometre.
- Finding your way as a tourist.
- Knowing which door you are at on a delivery round, in the towns listed below.

In an emergency, call 112: the app helps you say where you are; it does not replace the call.
```

**Reciprocidad (aplicar cuando Calles España esté aprobada):**

```text
Fuera de la provincia, o en otros relojes, «Calles España» da la calle, el portal y, en carretera, el punto kilométrico en toda España, a través del teléfono.
```

```text
Outside the province, or on other watches, «Calles España» gives the street, the door number and, on roads, the kilometre marker anywhere in Spain, through your phone.
```

## Calles Pontevedra (offline)

Va justo antes del párrafo que empieza por «Dónde llega:» (ES) y «Coverage:» (EN). La reciprocidad, justo
después de ese párrafo.

**Español**

```text
Para qué sirve, también sin teléfono ni cobertura, en toda la provincia:
- Decir dónde está ante una emergencia o un accidente: en las ciudades de abajo, la calle, el portal más cercano y entre qué calles; en el resto, la calle o la carretera, la aldea, la parroquia y sus coordenadas UTM.
- En una autovía o autopista, decir en qué vía está («AP-9»), aunque no el kilómetro.
- Orientarse haciendo turismo.
- Saber ante qué portal está en un reparto, en las ciudades de abajo.

Ante una emergencia, llame al 112: la app le ayuda a decir dónde está, no sustituye a la llamada.
```

**English**

```text
What it is for, with no phone and no signal too, across the province:
- Saying where you are in an emergency or after an accident: in the towns listed below, the street, the nearest door number and the cross streets; elsewhere, the street or road, the village, the parish and your UTM coordinates.
- On a motorway, saying which road you are on («AP-9»), though not the kilometre.
- Finding your way as a tourist.
- Knowing which door you are at on a delivery round, in the towns listed below.

In an emergency, call 112: the app helps you say where you are; it does not replace the call.
```

**Reciprocidad (aplicar cuando Calles España esté aprobada):**

```text
Fuera de la provincia, o en otros relojes, «Calles España» da la calle, el portal y, en carretera, el punto kilométrico en toda España, a través del teléfono.
```

```text
Outside the province, or on other watches, «Calles España» gives the street, the door number and, on roads, the kilometre marker anywhere in Spain, through your phone.
```
