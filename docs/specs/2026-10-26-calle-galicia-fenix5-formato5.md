# CALLE — Galicia en el fēnix 5: variante c5 y FORMATO 5

Diseño del 2026-10-26, aprobado por el autor por partes en la misma sesión. Objetivo: Calles Galicia en los
relojes de 128 KB y tope de 254 recursos, empezando por el **fēnix 5**, que el autor tiene para probarla sobre el
terreno. Madrid y el 6X **no cambian**: siguen en la variante `c` con FORMATO 4. Pasarán a `c5` solo si la
prueba de campo sale bien (decisión del autor).

## Lo que se midió antes de diseñar

Mediciones en una copia del generador (`build_callejero.py` importado, sin tocar el repositorio), con los
datos de Galicia del 2026-10-24 (Geofabrik + Catastro de Santiago). El tope de memoria por tesela es el de la
variante `c`: 26 KB de heap estimado.

| Medida | Resultado |
|---|---|
| Galicia en la variante `c` tal cual (lado ≤ 7,8 km) | **1.780 teselas** (mediana 2,8 KB: las multiplica el lado máximo, no el peso) |
| Con unidades de 2 m / 4 m (lado ≤ 15,6 / 31,2 km), sin portales rurales | 581 · 7,2 MB / 363 · 7,7 MB |
| + trazado rural simplificado a 8 m | 319 · 6,45 MB (a 15 m: 6,28 MB; no compensa) |
| Desglose de lo rural | cabeceras de tirada 1,5 MB · índices por calle 1,0 MB · nombres 0,9 MB · vértices 0,76 MB |
| + vías rurales enteras (sin cortar en los cruces) y encadenadas | **279 · 5,5 MB** (tiradas rurales 104.000 → 41.000) |
| Lugares en OSM | 102.949, de ellos 55.270 parajes (`locality`); sin parajes fuera de la zona urbana: 49.888 |
| Zonas de 20 km sin parajes rurales | 102 · 1,75 MB, 17 de más de 26 KB |
| **Con la zona urbana final (15 municipios)** | **teselas 302 · 6,0 MB · zonas 103 · 1,79 MB (20 de más de 26 KB)** |

Pruebas en el compilador y el simulador del fēnix 5 (proyecto de prueba en un directorio temporal):

| Prueba | Resultado |
|---|---|
| 250 `jsonData` + 251 `string` | compila y carga |
| 311 `string` | `Found 311 members in module '$.Rez.Strings', exceeding the limit of 254` → **el tope es por módulo** |
| 20.000 B de datos en JSON | 25.024 B en memoria |
| Los mismos 20.000 B en base64 → `ByteArray` | texto 26.688 B + `ByteArray` 20.024 B durante la conversión; **20.024 B** al soltar el texto |
| Base64 dentro de un `jsonData` (una cadena JSON suelta) | idéntico al de `Rez.Strings`: el lector no distingue el módulo |
| Tamaño máximo de un `<string>` | **32.767 caracteres** (≈ 24.570 bytes de tesela en base64); un `jsonData` con una cadena de 60.000 compila |

Conclusión: con dos módulos caben ~500 recursos, y la tesela en bytes ocupa un 20 % menos en reposo.

**Riesgo heredado (especificación del FORMATO 4, 2026-10-25):** «recorrer 20.000 bytes uno a uno dispara el
watchdog» de 120.000 instrucciones del fēnix 5 y 6. Por eso el FORMATO 4 eligió `Array<Number>`. El FORMATO 5
solo es viable si la búsqueda **no recorre** la tesela, sino que salta a lo cercano (ver *Lector* y *Riesgos*).

## Alcance

- **Contenido por zona** (decisión del autor):
  - **Dentro de la zona urbana:** todo como hoy: calle, portal (OSM + Catastro donde lo haya), entre qué
    calles, lugar y parroquia.
  - **Fuera:** calle, lugar y parroquia. Sin portal ni entre qué calles; sin parajes (`locality`).
- **Zona urbana:** municipios enteros por código INE (`regiones.json` → `<provincia>.c5.urbana`): las
  ciudades y villas con trama urbana densa (2026-10-26):
  15030 A Coruña · 15036 Ferrol · 15054 Narón · 15073 Ribeira · 15078 Santiago de
  Compostela · 27028 Lugo · 27031 Monforte de Lemos · 27066 Viveiro · 32054 Ourense · 36024 Lalín · 36026 Marín ·
  36038 Pontevedra · 36045 Redondela · 36057 Vigo · 36060 Vilagarcía de Arousa.
  El polígono es la unión de las parroquias (admin_level 9) cuyo `ref:ine`
  empieza por esos códigos.
- **Relojes:** solo el `fenix5`. El 5S (218 px, fuente pequeña sin resolver), el 6 y el 6S después de la prueba
  de campo. Madrid y el 6X, fuera.
- **Descripción pública:** «detalle completo en las ciudades». La zona urbana es un criterio interno de
  densidad.

## Arquitectura

**Variante `c5`** de `build_callejero.py` (`--variante c5`) → `resources-gen-c5/` y `source-gen-c5/`:

- Teselas adaptativas como la `c` (`teselar_kd`), con las dos medidas de volumen:
  1. **Rural sin cortes:** fuera de la zona urbana, las vías lineales no pasan por `trocear`. Se encadenan
     las de la misma calle que comparten nodo extremo y van con `tramo = (None, None)`. Douglas-Peucker a 8 m
     (dentro, 0,75 m como hoy). Sin sendas (`clase 2`) fuera.
  2. **Zonas sin parajes fuera:** los lugares `tipo == 4` (`locality`) fuera de la zona urbana no entran.
- **Unidad por tesela:** 1 m si el centro de la tesela cae en la zona urbana, 4 m si no. `KD_LADO_MAX` pasa a
  depender de la unidad (7,8 km × U). Esto arregla también las ~9 teselas de ciudad que pasaban de 26 KB con 4 m.
- **Tope de la tesela:** 24.000 bytes en FORMATO 5. Lo fijan a la vez el límite de un `<string>` (32.767 caracteres de base64) y el pico de memoria (~2,33 × 24.000 ≈ 56 KB).
- **Reparto en módulos:** cada tesela es un base64; las primeras van como `<string>` (`Rez.Strings`) hasta
  llenar el módulo (dejando las cadenas de la app y 4 de margen) y el resto como `jsonData` con una cadena suelta. El
  índice de teselas mezcla los dos tipos de `ResourceId`. Zonas, cajas y puntos (hospitales y comisarías) siguen
  en JSON. El generador **falla** si un módulo pasa de 250.
- **Cómo entra solo en Galicia:** `tools/tienda.py` elige la variante por app (`catalogo.json` →
  `galicia.variante_128k: "c5"`); `monkey.jungle` del paquete apunta `fenix5` a `*-gen-c5`. Para el `.prg` por
  cable, `VARIANTE=c5 DEV=fenix5 ./ciq.sh release` usa un jungle derivado con esa misma redirección.
- **Lectores en paralelo:** el lector de bytes vive en funciones con la anotación `(:c5)`; las versiones FORMATO 4
  de las mismas funciones llevan `(:f4)`. Cada compilación excluye la otra (`excludeAnnotations`). La app de
  Madrid y la compilación del 7X no llevan ni un byte nuevo.

## FORMATO 5 (tesela en bytes)

Un `ByteArray`, big-endian. La cabecera de `build_callejero.py` es la referencia definitiva del orden de bits,
como en el FORMATO 4. Contenido:

- **Cabecera:** FORMATO (5), U (unidad en m: 1 o 4), NC (calles), PB (bits de portal) y los desplazamientos en
  bytes de cada sección.
- **S:** los nombres en UTF-8, separados por `\n`. Se convierten a `String` una sola vez al cargar
  (`convertEncodedString` de bytes a texto) y la tesela los guarda como hoy.
- **CB:** la caja gruesa de cada calle en **4 bytes sueltos** (no un número de 32 bits): la comparación lee
  bytes sin desplazar ni enmascarar.
- **C + K:** por calle, el offset de su primera tirada, el de su primer portal y el **bit de V donde empiezan sus
  vértices** (K, nuevo). Con K, una calle lejana se salta sin recorrer sus tiradas: es la defensa contra el
  watchdog.
- **R, V, P, E:** las tiradas, el flujo de vértices, los portales y sus escapes, con el mismo contenido que en
  el FORMATO 4. Las coordenadas van en unidades de U m. Las teselas rurales no llevan P ni E, y sus tiradas
  llevan los cruces a 0.

## Zonas (FORMATO 4 con dos cambios)

- **Rejilla de 20 km**, raster de parroquias a 100 m (RN = 200). En la frontera entre parroquias, error de
  hasta ~70 m.
- **Lugares en unidades de 2 m:** 20 km + 2 × 1,5 km de margen no caben en 14 bits de metros.
- **Dos niveles:** una zona de más de 26 KB se parte en cuatro de 10 km. El índice de zonas marca las partidas
  y un segundo índice lleva sus cuatro recursos. Estimación: ~163 recursos.

## Lector en el reloj (solo `c5`)

- `Teselas.cargar`: `loadResource` → `String` → `convertEncodedString` → `ByteArray`. El texto se suelta antes de
  seguir. Pico medido: 2,33 veces los datos (con FORMATO 4, 2,2 × 1,25 = 2,75).
- `Buscador.buscar`, versión `(:c5)`:
  - recorre CB por bytes;
  - salta las calles lejanas con K;
  - solo en las cercanas lee las tiradas (R) y los vértices (V) del `ByteArray`, con acceso por índice y
    desplazamientos (sin `decodeNumber`, que crea un diccionario de opciones en cada llamada).
- Tramos y portales: en las teselas rurales no hay, y la vista ya omite lo que llega a `null`.
- `Zonas`: el mismo lector, con la unidad de 2 m y el índice de dos niveles.

## Verificación

En el Mac:

1. **`tools/ref.py`** lee el FORMATO 5. **Fuerza bruta** sobre 40.000 puntos de Galicia: 0 discrepancias.
2. **Puntos de control:** los 13 de Galicia, más Lalín (rural dentro de la zona urbana: con portal) y una aldea
   fuera de ella (sin portal, con lugar y parroquia).
3. **Tests de Monkey C** en el simulador del `fenix5`. La tesela y la zona más pesadas, cargadas juntas.
4. **Memoria en modo app** (tope real de 128 KB): pico de la conversión de la tesela más pesada, más la vista,
   más «hospital más cercano».
5. **Watchdog**, por el método comparativo de la 3.3.2. Se mide la cadena completa en la tesela más densa
   (casco de Vigo o de A Coruña) y se compara con la cadena de la 3.3.0 que tumbó el 7X. Hace falta un margen de
   **×1,5** sobre el límite de 120.000.

En el terreno (fēnix 5 del autor):

6. Un `.prg` por cable. Antes hay que ver si el fēnix 5 monta como almacenamiento USB o por MTP: `./ciq.sh instalar`
   está hecho para MTP. Rutas: casco de Santiago, Lalín, una aldea fuera de la zona urbana y un cruce de límite
   municipal.
7. Informes de cierre con `era` tras sincronizar.

Solo si el paso 6 sale limpio: el `fenix5` entra en `catalogo.json` → `galicia`, y se decide aparte si Madrid y el 6X
pasan a `c5`.

## Riesgos y salidas

| Riesgo | Señal | Salida |
|---|---|---|
| **Watchdog** con el `ByteArray` (riesgo heredado) | paso 5 por debajo de ×1,5, o cierre en el reloj | Las teselas de la zona urbana vuelven a FORMATO 4 (JSON, lector de hoy) y solo las rurales siguen en bytes. Entonces `JsonData` no da para ~112 teselas de ciudad más ~163 zonas: o las zonas suben a 25 km (~71 + partidas), o las zonas rurales pasan también a bytes. Se mide antes de elegir |
| Pico de memoria al convertir | paso 4 | Tope de tesela a 22 KB (más teselas; hay sitio de sobra en los dos módulos) |
| La estimación de 4 m se queda corta | el generador da más de ~480 recursos | Unidad de 4 m también en las teselas mixtas, o DP rural a 12 m |
| Un municipio mal en la zona urbana | el autor lo corrige | Es una línea de `regiones.json` |

## Fuera de este diseño

- Madrid y el 6X (hasta la prueba de campo).
- El fēnix 5S, el 6 y el 6S (después).
- Portales del Catastro en toda Galicia (P71). Con este formato hay sitio para ellos, pero es otra fuente y otra
  sesión.
- FORMATO 5 en la variante normal del fēnix 7.

## Resultado de la puerta (plan 1, 2026-10-26)

Simulador del `fenix5` (SDK 9.3), proyecto `puerta/` de la rama `c5-galicia`, tesela galicia t412 (Vigo; la más
pesada de la variante normal): 24.632 bytes, 32.844 caracteres de base64, 262 calles.

| Medida | Resultado |
|---|---|
| Vectores | **40/40** iguales a la referencia del FORMATO 4 (`ref.Tes`) |
| Memoria al cargar | base64 33.080 B · `ByteArray` 24.656 B · **pico 57.736 B** (< 58 KB) |
| Tesela ya cargada | **40.192 B** (estimado: 32.549; el FORMATO 4 de la misma tesela, ~30.400) |
| Cadena ×1 / ×2 | 10 ms / 40 ms, **sin watchdog** (margen ≥ ×2) |

**Decisión:** la puerta pasa. Se sigue con el plan 2.

**Pendiente para el plan 2, por la memoria en reposo:** la tesela cargada ocupa más que en el FORMATO 4. Eso
importa porque la zona se carga con la tesela en memoria: con ~62 KB libres, una tesela de 40 KB deja ~22 KB para
el pico de la zona (2,2 veces su tamaño), o sea, zonas de ~10 KB.
- Los nombres van dos veces: dentro de `B` y como `String` (~5,3 KB). Leerlos de `B` cuando se piden ahorra eso.
- Quedan ~7,6 KB sin explicar entre lo estimado y lo medido; se miden por partes antes de fijar los topes.
- Fijar el tope de las zonas `c5` (y quizá bajar el de la tesela) con una medición en modo app: tesela + zona
  cargadas a la vez con el tope real de 128 KB.

## Memoria (plan 2, 2026-10-26 y 2026-10-27)

Simulador del `fenix5` (SDK 9.3), `puerta/` en modo app (`puerta/app.jungle`). Total del simulador, 126.784 B. Se
rellena con lastre hasta 66 KB en uso: los 65 KB de la app real del FORMATO 4, más 1 KB. Libre antes de la tesela:
~59.100 B. Logs en `bin/app4d-*.log` y `bin/app4e-*.log`, fuera de git. **Cada modo se ejecutó una vez** (salvo la
4d): cerca del tope los resultados varían de una ejecución a otra (ver *Ruido*).

### Por partes (tests, t412, 262 calles)

| Parte | Antes (puerta) | Sin S (plan 2) |
|---|---|---|
| ByteArray | 24.920 B | 24.920 B |
| S como String | 5.608 B (5.253 letras, 5.587 bytes) | — |
| mejor + mejorRun (vacías / llenas) | 2.672 / 2.672 B | 2.672 / 2.672 B |
| Tesela sobre el ByteArray | 15.272 B | 9.664 B |
| Tras una búsqueda | +232 B | +232 B |
| **Tesela lista** | **40.192 B** | **34.584 B** |

### Modo app

**Retención del primer recurso:** ~8,3 KB, una vez por app. Un `Rez.Strings` y otro `jsonData` cargados después
retienen 0 B (modo `modulos`). Matiz: `AppName` podría estar ya cargado por el sistema.

**FORMATO 5, una tesela por recurso:**

| Tesela (bytes) | Como primera | En la escalera / tras otra | En reposo |
|---|---|---|---|
| 12.004 | carga | carga | 13.800–13.856 B |
| 14.016 | carga (4d) | carga | 15.760 B |
| 16.104 | **no carga** (4d) | carga | 17.800 B |
| 18.044 | **no carga** (4d, `zonas:3`, `b64:3`) | carga (4d, `previa:3`, `+frag`); **no carga** en `hueco:4` | 20.432 B |
| 19.896 | **no carga** (4d, `b64:4`) | carga (4d, `previa:4`, `+frag`) | 21.928 B |
| 21.976 | — | no carga (4d, ×2); **carga** con `+frag` | 24.288 B |
| 23.924 · 24.632 (t412) | — | no carga | — |

**La primera tesela, sin explicar, con dos hipótesis descartadas:**
- *Coste de la primera conversión base64:* no. Una conversión de 1 KB antes del lastre retiene 80 B, y después la
  de 18.044 y la de 19.896 siguen sin cargar como primeras (`b64:K`).
- *Falta de memoria contigua:* no al arrancar. Todo el libre se deja reservar en un solo `ByteArray` (58.368 B con
  59.280 libres), también con el lastre en 115 trozos de 256 B (`hueco:0`, `hueco:0+frag`). En `hueco:4` la app cayó
  antes de llegar a medir (al cargar la de 18.044 tras otras tres).
- Queda la carga del recurso (lectura del `jsonData` y construcción del `String`), que la API no deja medir.

**FORMATO 4, la tesela como array JSON** (lo que hace hoy la variante `c`):

| Tesela (heap estimado) | Fichero | Como primera | En la escalera (`+frag`) | En reposo |
|---|---|---|---|---|
| 13.980 · 18.211 · 22.037 · 25.920 | t1600 · t583 · t294 · t379 | — | carga | 12.776 · 16.968 · 20.608 · 23.768 B |
| 28.036 | t1570 | sin log | carga | 26.192 B |
| 29.971 | t514 | — | carga | 26.824 B |
| **30.712** | **t412** (la mayor de Galicia) | **carga** | **carga** | **28.160–28.224 B** |
| 32.498 | sintética (t412 + otra) | **no carga** | **no carga** | — |

`f4` y `f4z:4` (bloque único) dejaron el log vacío: no se dan cifras de ellos. La escalera vale por `f4+frag`.

**Zonas con la tesela en memoria** (heap estimado de la mayor que carga / la primera que no):

| Tesela en memoria | En reposo | Zona mayor que carga | Primera que no |
|---|---|---|---|
| F5 12.004 o 14.016 (4d) | 13,8–15,8 KB | 20.480 (todas) | — |
| F5 16.104 (`previa:2`) | 17.800 B | 18.443 | 20.480 |
| F5 18.044 (`previa:3`) | 20.432 B | 18.443 | 20.480 |
| F5 19.896 (`previa:4`) | 21.928 B | 16.353 | 18.443 |
| F5 t412 en 4 trozos concatenados (`trozos:1`) | 27.848 B | 14.328 | 16.353 |
| **F4 t412 (`f4z:6`)** | **28.160 B** | **14.328** | **16.353** |

**Carga partida (salida C), t412 en FORMATO 5:**

| Montaje | Resultado |
|---|---|
| Un recurso (32.844 caracteres) | no carga |
| 4 recursos de 8.212 caracteres, convertidos y concatenados (`addAll`) | **carga**, 13 ms, en reposo 27.848 B |
| 4 recursos, `Array<ByteArray>` sin Tesela | carga, 1 ms, en reposo 24.680 B (sin las tablas de la Tesela) |
| Los 4 en un solo `jsonData` (array de cadenas) | **no carga** |

### Lo que dicen las cifras

- **La memoria no favorece al FORMATO 5.** t412 ocupa en reposo lo mismo en F4 (28.160 B) que en F5 partida
  (27.848 B). En F4 carga de un solo recurso; en F5 solo partida en cuatro. El diseño suponía un 20 % menos en
  reposo para el FORMATO 5, y no se cumple.
- **Todas las teselas F4 de Galicia** (la mayor, t412, 30.712 B estimados) **cargan en el fēnix 5 como primera
  tesela**. El tope F4 medido está entre 30.712 y 32.498 B estimados.
- **El FORMATO 5 en un solo recurso es fiable solo hasta 14.016 B.** De 16 a 22 KB carga unas veces sí y otras no.
- **La salida C cuesta recursos:** cuatro por tesela pesada, porque juntarlos en un solo `jsonData` no carga.

### Topes (redondeados hacia abajo; zona = la mayor que cargó, menos 2 KB para la vista y el «hospital más cercano»,
que no se midieron)

| Salida | Tesela | Zona `c5` |
|---|---|---|
| **A'** FORMATO 4 | **30 KB estimados** (todas las de Galicia caben) | **12 KB** (con t412 en memoria) |
| **B** FORMATO 5, un recurso | **14 KB** | 18 KB (con 14.016 en memoria cargan todas, hasta 20.480) |
| **C** FORMATO 5 en trozos | t412 entera, en trozos de ~6 KB | **12 KB** (con t412 en memoria) |

**Zonas:** con 12 KB de tope (A' y C), una parte de las zonas de 10 km no cabe (mediana de la variante normal:
13,8 KB). Hacen falta las salidas del plan 2 (Task 5, paso 2): (a) zona consultada con la tesela soltada, (b) zonas
en bytes o (c) zonas de 10 y 5 km.

**Ruido:** cerca del tope el resultado cambia de una ejecución a otra:
- la de 21.976 no cargó en la 4d (dos veces) y cargó con `+frag`;
- la de 18.044 cargó en tres ejecuciones y no en `hueco:4`.

Antes de fijar los topes del plan 3 conviene repetir tres veces los casos de frontera: `zonas:2`, `previa:3`,
`f4z:6`, `f4z:7` y `trozos:1`, unos 10 minutos.

**Recuento de recursos:** decide entre las salidas y lo calcula el plan 3.

**Decisión:** del autor.
