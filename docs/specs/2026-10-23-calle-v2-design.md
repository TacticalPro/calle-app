# CALLE v2 — tramo, lugar/parroquia/barrio, UTM y anotaciones

Diseño aprobado el 2026-10-23. Parte de la v1 (fases 0–3 cerradas).

## Alcance

**Entra:**
1. **Tramo.** Las dos calles que cruzan a cada lado del punto: «entre R. de San Clemente y R. da República de El Salvador».
2. **Lugar y parroquia** cuando no hay calle a 50 m, y **barrio** en ciudad.
3. **Coordenadas UTM** (WGS84, huso 29T), calculadas en el reloj.
4. **Anotaciones.** El botón START guarda la hora y el lugar. Se guardan en el reloj hasta que el usuario las borre; tope de 300.

**Queda fuera** (descartado o aplazado):
- sentido de marcha;
- tipo de hecho en las anotaciones;
- reloj de detención;
- «ir a un sitio»;
- chuletas;
- exportar las anotaciones al Mac.

## 1. Datos (`tools/build_callejero.py`)

### 1.1 Tramos

**Intersección.** Un nodo OSM es intersección para una calle S si pertenece a una vía lineal de S y, además, a otra vía lineal de nombre distinto y clase calzada o peatonal. Las sendas y las áreas no cuentan como cruce. Necesita los ids `nodes` de cada vía, que `out geom` ya trae.

**Trozos y su tramo.** Cada vía de S se corta en sus intersecciones. Cada trozo guarda su tramo `(A, B)`, el nombre de la calle que cruza en cada extremo:
- **Si el extremo es una intersección:** el nombre de la calle que cruza. Si son varias, primero calzada y luego por orden alfabético.
- **Si no lo es** (la vía sigue en otra vía de S): se recorre el grafo de S, por nodos de grado 2, hasta la siguiente intersección. En una bifurcación o un fondo de saco no hay cruce (`ninguno`).

**Teselado.** Cada trozo se simplifica por separado, conservando sus extremos, y se tesela como en la v1. Las tiradas recortadas heredan el tramo de su trozo.

**FORMATO 2.**
- `R` pasa a 4 números por tirada: el 4.º es `(A+1) | (B+1) << 8`, donde 0 significa ninguno.
- `N` incluye los nombres de las calles que cruzan aunque no tengan tirada en la tesela. El tope de 255 se mantiene.

**Informe.** El porcentaje de tiradas con tramo completo, con un solo lado y con ninguno.

### 1.2 Zonas: lugar, parroquia y barrio

**Consulta.** Se amplía con:
- `relation[boundary=administrative][admin_level=9]` con `out geom`: 74 parroquias medidas;
- `node[place~hamlet|village|isolated_dwelling|locality|neighbourhood|suburb|quarter][name]`: 3.417 lugares y 164 barrios.

**Rejilla de zonas.** Celdas de 2.000 m sobre la misma región (12 × 9 = 108). Cada una es un recurso `z<idx>` con `[FORMATO, nombres, raster, lugares, idsNombre]`:
- **`raster`:** 40 × 40 celdas de 50 m. Cada celda guarda el índice de su parroquia (+1; 0 = ninguna), 4 celdas por número (8 bits), 400 números. La parroquia de una celda es la que contiene su centro (punto en polígono, con anillos exteriores e interiores).
- **`lugares`:** los nodos de la zona más un margen de 1.500 m, empaquetados como `x | y<<13 | tipo<<26`. Las coordenadas van desde el origen de la zona menos 1.500 m. El tipo es 0 para lugar (hamlet, village, isolated_dwelling, locality, neighbourhood) y 1 para barrio (suburb, quarter, neighbourhood). Un `neighbourhood` cuenta para las dos cosas.
- **`idsNombre`:** paralelo a `lugares`, indexa `nombres`.

**Índice.** `Callejero.ZIDX` (denso, 108 entradas) y `Callejero.ZONA = 2000`.

**Reglas:**
- **lugar:** el nodo de tipo 0 más cercano a menos de 1.500 m;
- **barrio:** el nodo de tipo 1 más cercano a menos de 800 m;
- **parroquia:** la de la celda del raster.

### 1.3 Presupuesto

Una zona ocupa unos 17 KB de memoria y convive con la tesela de calles, unos 70 KB en el peor caso. Lo comprueba `MemoriaTest`, que también carga la zona más pesada (`Z_MAYOR`).

## 2. Reloj

### 2.1 Tramo

- `Buscador.buscar` guarda, además de `mejor[]`, `mejorRun[]`: la tirada más cercana de cada calle.
- Tras elegir la calle principal (con histéresis), el `Localizador` lee su tramo. El `Modelo` gana `tramoA` y `tramoB`, de tipo `String` o `null`.
- **Pantalla:** solo en la vista de una calle sin esquina.
  - Debajo del número, en dos líneas XTINY grises: «entre {A}» / «y {B}», abreviadas con `Abrev.corta` y recortadas a lo ancho.
  - Si solo hay un lado: «cerca de {A}».
  - El «±8 m» del pie se traslada a la página de detalle.

### 2.2 Zonas

- Módulo `Zonas`: una zona cargada a la vez, independiente de la tesela de calles.
- Funciones: `parroquia(x, y)`, `lugar(x, y)` y `barrio(x, y)`, que devuelven `String` o `null`.
- El `Modelo` gana `barrio`, `lugar` y `parroquia`. Se recalculan con cada cálculo: el raster es O(1) y los lugares, una pasada lineal sobre unos 150.
- **Pantalla:**
  - **EST_OK:** el barrio en pequeño y gris, en y≈54, encima del nombre.
  - **EST_LEJOS:** el título es el lugar (o «SIN CALLE» si no hay ninguno), debajo «parroquia de X» (o «a menos de 50 m») y la UTM en el pie.
  - **EST_FUERA:** la UTM en el pie.

### 2.3 UTM

- `Utm.texto(lat, lon)` → `"29T 537212 4747321"`.
- Serie de Krüger sobre el elipsoide WGS84, calculada en Double. El huso sale de la longitud y la banda, de la latitud.
- Aparece en la página de detalle (en una línea propia, junto al «±m» de calidad), en «sin calle», en «fuera de zona» y en cada anotación.

### 2.4 Anotaciones

**Almacenamiento.**
- Módulo `Notas`, el único que puede usar `Application.Storage`, con la clave `"notas"`.
- Cada entrada es `[t (s de época), lugar (String completo), lat (Double o null), lon]`. Tope: 300.

**Gestos.** En `DelegadoCalle`:
- `onKey(KEY_ENTER)` (START) → `Notas.anotar`. Vibra 50 ms y muestra un aviso de 2 s: «Anotado 23:41», o «Anotaciones llenas (300)» sin guardar.
- `onTap` → recalcular.
- Las dos funciones devuelven `true` para que no salte `onSelect`. Hay que verificarlo en el simulador y en el reloj.

**El texto del lugar** es lo que se ve en pantalla, con los nombres completos:

| Estado | Texto guardado |
|---|---|
| Calle sin esquina | «R. do Franco 33» o «R. do Hórreo, entre X y Y» (el número manda; sin número, el tramo) |
| Esquina | «R. do Franco 54, esq. R. da Raíña» |
| Dos calles | «R. do Vilar 44 / Rúa Nova 11» |
| Sin calle | «Lugar de Mazas (parroquia de Marrozos)» o «sin calle» |
| Fuera de zona | «fuera de zona» |
| Buscando | «sin posición» |

**Menú (mantener ARRIBA).**
- «Anotaciones (N)» abre la lista, de la más nueva a la más vieja:
  - cada entrada: etiqueta «23:41 · {lugar abreviado}» y subetiqueta «23-oct · {UTM}»;
  - al seleccionar una: `Confirmation` «¿Borrar esta?»;
  - al final de la lista: «Borrar todas», también con confirmación.
- «Callejero» sigue como en la v1.

**Privacidad.**
- `./ciq.sh privacidad` permite `Application.Storage` solo en `source/Notas.mc`.
- Sigue prohibiendo red, grabación y servicio en segundo plano. El manifiesto sigue pidiendo solo `Positioning`.
- **Riesgo aceptado el 2026-10-23:** con el reloj perdido y conectado por USB, las anotaciones se pueden leer.

## 3. Pruebas

**`ref.py`:**
- **Tramo de s1:** los vectores lo incluyen, y una comprobación de coherencia compara el tramo de la tesela con el de los trozos globales en puntos al azar sobre calles.
- **Zonas:** vectores de parroquia, lugar y barrio, comparados con un punto en polígono sobre los límites reales; el raster falla como mucho cerca de un límite (< 50 m).
- **Fuerza bruta de calles:** sin cambios.

**Monkey C:**
- Vectores ampliados: tramo, barrio, lugar y parroquia.
- `Utm` frente a `Position.Location.toGeoString(GEO_MGRS)` en unos 10 puntos: el easting y el northing módulo 100 km deben coincidir a 1 m.
- `Notas`: alta, lectura, borrado, tope y texto del lugar en cada estado.
- `VistaTest` con los estados nuevos.
- `MemoriaTest` con la tesela y la zona más pesadas a la vez.

**Maquetas:** tramo, barrio, lugar y parroquia, aviso de anotado, lista y detalle con UTM.

**Muñeca:**
- Que START anote y el toque recalcule.
- Que el tramo coincida con la realidad en 10 puntos.
- Que la parroquia sea correcta en 3 puntos rurales.

## 4. Riesgos

- **Orden de `onKey` y `onTap` frente a `onSelect`** en el firmware real: se verifica en el simulador y en el reloj. Plan B: mantener START.
- **Tramo en bifurcaciones o con OSM cortado:** el informe da la tasa; sin cruce se muestra solo un lado o nada.
- **Barrio por punto más cercano:** puede fallar cerca de una frontera. Por eso va en pequeño y gris, y nunca en el título.
- **Anotaciones legibles por USB** si se pierde el reloj: aceptado.

## 5. Implementación (2026-10-23)

Hecha el mismo día en que se aprobó el diseño. Los 33 tests pasan en el simulador y la fuerza bruta sale sin discrepancias: 6.784 comparaciones de calle, 6.457 tramos y 1.407 portales; en 2.000 puntos de zonas, cero fallos y 23 parroquias distintas a menos de 50 m de un límite, como se admite. Falta la prueba en la muñeca.

**Cambios respecto a lo de arriba** (cada uno con su motivo):

- **Orden de START y del toque (§2.4, riesgo de §4).** La documentación del SDK dice lo contrario de lo supuesto: el reloj llama primero a la conducta (`onSelect`) y solo si devuelve `false` a la entrada (`onKey`, `onTap`). Por eso `onSelect` devuelve `false` y no hace nada; anota `onKey(KEY_ENTER)` y recalcula `onTap`, que devuelven `true`. Así funciona en los dos órdenes. El simulador no se dejó manejar desde fuera para comprobarlo (ni teclas ni capturas): queda para la muñeca.
- **Tramo en bifurcaciones (§1.1).** «Bifurcación = sin cruce» perdía el tramo en las calles con las calzadas desdobladas. Ahora se recorren todas las ramas: si todas llegan al mismo cruce, vale; si llegan a cruces distintos, ninguno. Tramo completo: del 42,3 al 48,8 % de las tiradas, y en el centro (a menos de 1,5 km de la catedral) 62 % completo, 28 % de un lado y 11 % ninguno. Lo que queda sin cruce son sobre todo rotondas y ramales sin nombre, que no se descargan.
- **Mismo nombre a los dos lados** (una calle en U): se muestra «cerca de A».
- **Lugar (§1.2).** `locality` mezcla aldeas con montes, cotos y agras («Monte de Corexo», «Pena de Castoira»). En la radio se da la aldea: manda el poblado más cercano (hamlet, village, isolated_dwelling, neighbourhood) a menos de 1.500 m, y un paraje (`locality`) solo si no hay ninguno. `tipo` pasa a máscara de 3 bits (lugar, barrio, paraje).
- **Barrio (§1.2).** OSM no tiene polígonos de barrio en Santiago ni nodo para la ciudad histórica: el Obradoiro salía «A Poza de Bar», a 463 m. Se añaden dos cosas:
  - `barrios_extra` en `overrides-santiago.json`, con «Casco Histórico»;
  - la regla de que el barrio solo se muestra si su nodo está a menos de 0,8 veces la distancia al segundo. En la frontera no se adivina: la Praza de Galicia y el Hórreo salen sin barrio.
- **Barrio en pantalla.** Va en la vista de una calle y en la de esquina; en «dos calles» no cabe.
- **Tramo en pantalla (§2.1).** Debajo del número, a 226 y 246 px, el círculo lo cortaba («entre Rla. de Paio o Ere…»). Ahora el número va pegado al nombre y el tramo a 190 y 212 px, donde la pantalla es más ancha.
- **Sin calle con lugar.** Encima del lugar, en amarillo, «sin calle a 50 m», para no confundir un topónimo con una dirección.
- **UTM (§2.3).** Se redondea al metro, como el MGRS del propio reloj (comprobado en 10 puntos, de Santiago a Barcelona). La serie de orden n³ coincide con una de orden n⁶ (Karney) en menos de 0,1 mm.
- **Anotaciones (§2.4).**
  - Una clave por anotación (`n<seq>`) y el índice en `"notas"`. Storage limita cada valor a 32 KB, y 300 anotaciones en una sola clave se acercarían a ese tope.
  - Texto: nombres completos y «≈» delante del número aproximado. Si la posición tiene más de 60 s, se añade «(posición de hace 3 min)».
  - Sin calle: «Mazas (parroquia de Marrozos)», sin el «Lugar de» del ejemplo.
  - Antes de guardar se recalcula con la última posición.
- **Memoria y tamaño (§1.3).**
  - Medido en el simulador: la tesela mayor ocupa 56 KB y la zona mayor 46,5 KB; las dos juntas, 102 KB de 768 KB. En la calle no coinciden: la tesela mayor es del centro y la zona mayor, del rural.
  - La media por zona es de unos 18 KB, como se estimó; el máximo, no.
  - El PRG pasa de 950 KB a 1,9 MB (el límite del reloj es de 64 MB), porque cada lugar se repite en unas seis zonas por el margen de 1,5 km.

## 6. Contraste con el Catastro (2026-10-24)

Se planteó usar las calles de Google Maps para la Zona Vella. No se puede: sus condiciones prohíben extraer datos para otro mapa, y la app va a la tienda. Se contrastó con la fuente oficial, el Catastro (WFS INSPIRE de direcciones, uso libre citando la fuente), que es de donde salen los portales de CartoCiudad.

- **Nombres.** En la caja de la Zona Vella (42,8745–42,8860 N, 8,5490–8,5365 O; 2.463 direcciones, 195 calles), ningún nombre de OSM estaba mal. Las seis calles del Catastro sin pareja son dos parques, un jardín, portales a más de 30 m de la calle y «Fuenterrabía», forma castellana de la «Fonterrabía» oficial. El Catastro abrevia, quita artículos y trunca («RU CASTRON DOURO», «RU SANTO DOMINGO DE LA CALZA»), así que no sirve para mostrar: los nombres siguen siendo los de OSM.
- **Números.** Al 14 % de los portales del Catastro les faltaba su número en OSM. `build_callejero.py` los añade si la región tiene caja `catastro` (`regiones.json`):
  - el portal se casa con una vía de OSM de su nombre a 30 m o menos, y el tipo de vía desempata (la Travesa do Franco no es la Rúa do Franco);
  - si a 150 m pasa una vía de su nombre y su tipo, el portal es de esa o de ninguna;
  - si OSM ya tiene ese número en esa calle, manda OSM;
  - si contradice la numeración de OSM de su misma acera a 25 m (salto de más de 12), no entra.
  Resultado: 379 portales añadidos, 1.832 que ya estaban, 4 que OSM tiene en otro sitio (se queda el de OSM). Fuerza bruta: 0 discrepancias, portales 1.439/1.439; 33/33 tests. La tesela mayor pasa de 56 a 58 KB.
- **Atribución.** El menú dice «OSM + Catastro» y la fecha. La ficha de la tienda debe citar «© colaboradores de OpenStreetMap» y «Fuente: Dirección General del Catastro».
