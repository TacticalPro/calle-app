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
| Lugares en OSM | 102.949, de ellos 55.270 parajes (`locality`); sin parajes fuera de la demarcación: 49.888 |
| Zonas de 20 km sin parajes rurales | 102 · 1,75 MB, 17 de más de 26 KB |
| **Con la demarcación final (15 municipios)** | **teselas 302 · 6,0 MB · zonas 103 · 1,79 MB (20 de más de 26 KB)** |

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
- **Zona urbana:** municipios enteros por código INE (`regiones.json` → `galicia.c5.demarcacion`): las
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
  1. **Rural sin cortes:** fuera de la demarcación, las vías lineales no pasan por `trocear`. Se encadenan
     las de la misma calle que comparten nodo extremo y van con `tramo = (None, None)`. Douglas-Peucker a 8 m
     (dentro, 0,75 m como hoy). Sin sendas (`clase 2`) fuera.
  2. **Zonas sin parajes fuera:** los lugares `tipo == 4` (`locality`) fuera de la demarcación no entran.
- **Unidad por tesela:** 1 m si el centro de la tesela cae en la demarcación, 4 m si no. `KD_LADO_MAX` pasa a
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
2. **Puntos de control:** los 13 de Galicia, más Lalín (rural dentro de la demarcación: con portal) y una aldea
   fuera de ella (sin portal, con lugar y parroquia).
3. **Tests de Monkey C** en el simulador del `fenix5`. La tesela y la zona más pesadas, cargadas juntas.
4. **Memoria en modo app** (tope real de 128 KB): pico de la conversión de la tesela más pesada, más la vista,
   más «hospital más cercano».
5. **Watchdog**, por el método comparativo de la 3.3.2. Se mide la cadena completa en la tesela más densa
   (casco de Vigo o de A Coruña) y se compara con la cadena de la 3.3.0 que tumbó el 7X. Hace falta un margen de
   **×1,5** sobre el límite de 120.000.

En el terreno (fēnix 5 del autor):

6. Un `.prg` por cable. Antes hay que ver si el fēnix 5 monta como almacenamiento USB o por MTP: `./ciq.sh instalar`
   está hecho para MTP. Rutas: casco de Santiago, Lalín, una aldea fuera de la demarcación y un cruce de límite
   municipal.
7. Informes de cierre con `era` tras sincronizar.

Solo si el paso 6 sale limpio: el `fenix5` entra en `catalogo.json` → `galicia`, y se decide aparte si Madrid y el 6X
pasan a `c5`.

## Riesgos y salidas

| Riesgo | Señal | Salida |
|---|---|---|
| **Watchdog** con el `ByteArray` (riesgo heredado) | paso 5 por debajo de ×1,5, o cierre en el reloj | Las teselas de la demarcación vuelven a FORMATO 4 (JSON, lector de hoy) y solo las rurales siguen en bytes. Entonces `JsonData` no da para ~112 teselas de ciudad más ~163 zonas: o las zonas suben a 25 km (~71 + partidas), o las zonas rurales pasan también a bytes. Se mide antes de elegir |
| Pico de memoria al convertir | paso 4 | Tope de tesela a 22 KB (más teselas; hay sitio de sobra en los dos módulos) |
| La estimación de 4 m se queda corta | el generador da más de ~480 recursos | Unidad de 4 m también en las teselas mixtas, o DP rural a 12 m |
| Un municipio mal en la demarcación | el autor lo corrige | Es una línea de `regiones.json` |

## Fuera de este diseño

- Madrid y el 6X (hasta la prueba de campo).
- El fēnix 5S, el 6 y el 6S (después).
- Portales del Catastro en toda Galicia (P71). Con este formato hay sitio para ellos, pero es otra fuente y otra
  sesión.
- FORMATO 5 en la variante normal del fēnix 7.
