# C18 · Calles A Coruña más ligera para el fēnix 5 — arranque del trabajo

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Pasos con `- [ ]`. Cada tarea termina
> con sus cifras escritas **en este documento**.

Documento de entrega, escrito el 2026-10-29 a partir de las mediciones anteriores de
tamaño, de memoria de la c5 y de los paquetes publicados. Aquí está todo lo que hay que saber para empezar.

## 0. Qué es esto y en qué punto está

- **El problema (muñeca, 2026-10-29):** en el fēnix 5 del autor, con las esferas Ironsight e Ironsight Grid
  instaladas, Connect IQ no instala **Calles A Coruña 3.5.3**: no queda sitio. Las esferas no son la palanca:
  sus `.prg` para el fēnix 5 pesan **59,7 KB y 61,0 KB**, el 5 % de la app entre las dos.
- **Lo que hay publicado** (API del portal, 2026-10-28, todo «APPROVED»):

  | App | `.prg` del fēnix 5 | Recursos (de 250) | Antes (3.5.2) |
  |---|---|---|---|
  | Calles A Coruña 3.5.3 | **2.537.644 B** | 237 | 2.733.628 B |
  | Calles Pontevedra 3.5.3 | 1.636.348 B | 189 | 1.874.300 B |

  El `.iq` pesa el doble (5,2 y 3,5 MB) porque lleva un `.prg` por modelo; al reloj solo va uno. Los recursos son
  el **97,7 %** del `.prg`; el código, 49 KB.
- **La memoria de ejecución está resuelta y al límite.** Margen en el pico del peor arranque en frío de A Coruña
  (t18 y dos zonas, `medida_c5.py --punto --lastre`): **≈ 7,45 KB** en `main` (la 3.5.2 tenía 9,9; la diferencia
  es código). Cualquier byte de código nuevo lo come. Topes vigentes en `tools/regiones.json` → `coruna.c5`:
  tesela ≤ 22,8 KB de heap estimado, zona ≤ 13 KB (con 20 KB, 3-4 zonas seguidas en una esquina daban *Out Of
  Memory*), `rcel` 100 m, `zu` 2 m, `rural_u` 4 m, `rural_dp` 8 m, `zona_sin_margen`.
- **El objetivo (medido en T0, 2026-10-29): el fēnix 5 tiene una cuota de 2 MB para todas las apps de Connect IQ
  juntas** (`AppSpace` 2.097.152 B en `GARMIN/GarminDevice.xml`), con 51 MB libres de disco que no sirven de nada.
  La 3.5.3 (2.537.644 B) no cabe ni sola. **Objetivo: `.prg` ≤ 1.900.000 B (−25,1 %).** Detalle en §2, T0.

### Dónde está el peso (medición del 2026-10-28, sobre la 3.5.1; estimación 5 B por número y cadena = bytes + 3)

| A Coruña | KB | % | Dentro |
|---|---|---|---|
| Teselas | 1.840 | 71 | cabeceras de tirada **R 28 %** · nombres S 19 % · portales P 16 % · vértices V 16 % · C/K/CB/O 18 % |
| Zonas (antes de la salida 1) | 750 | 29 | nombres S 39 % (293 KB; únicos 123) · lugares L 19 % · ráster RL 18 % |

- En las teselas, las **vías rurales sin tramo suman 400 KB** y los tramos urbanos 344 KB.
- Pontevedra, igual salvo los portales (26 KB: OSM tiene pocos). Nombres de zona 228 KB, únicos 75.
- **El territorio vacío no pesa**: las teselas son adaptativas; la mitad menos densa de la provincia es el 8 % de
  las teselas. Las 40 más densas se llevan el 43 %.
- **El formato ya está apretado** (26-27 bits útiles de 32 por número; vértices en flujo de bits con deltas). El
  FORMATO 5 (base64 en cadena) ocupa **más**. Recodificar no da: **el ahorro sale del contenido o de la
  duplicación.**
- El script que dio este reparto se hizo en una copia fuera del repositorio y **no se conservó**: T1 lo rehace
  dentro de `tools/`.

### Lo que ya se probó (cifras de A Coruña / Pontevedra)

| Salida | Estado | Ahorro | Coste |
|---|---|---|---|
| 1. Zonas sin margen duplicado (lugares y nombres solo en su hoja; vecinas de una en una) | **hecha**, 3.5.3 | −7,2 % / −12,7 % | +0,67 KB de código (`source-c5/Zonas.mc`) |
| 2. Ráster de parroquias de 100 → 250 m (`rcel`) | medida, sin aplicar | −4,8 % / −5,3 % y −9 / −12 recursos | precisión en la frontera entre parroquias (hasta ≈ 177 m) |
| 2'. Ráster de 125 m | medida | −1,3 % | el de 200 m no vale: la hoja de 2.500 m debe ser múltiplo de `rcel` |
| 3. Nombres de calle sin repetir entre teselas | estimada | −136 / −82 KB (−5 %) | exige un `Tesela.mc` propio de la c5 (bisección por nombre) |
| 4. Fuera los `track` rurales | medida | −2,8 % / −1,4 % | pistas con nombre fuera del callejero |
| 4'. Fuera `track` y `service` | medida | −3,2 % / −2,3 % | ídem |
| FORMATO 5 (base64 en cadena) | descartado | **+6,6 %** | — |

**Las tres que quedan (2, 3 y 4') suman ≈ −13 %.** Si el objetivo pide más, la medición del 2026-10-28 concluyó que la única
palanca conocida es la **cobertura**. Antes de aceptarlo, T2 mide las palancas que nadie ha medido todavía.

### Límites que siguen en pie

1. **`source/` no pierde funcionalidad por los modelos antiguos.** Lo que necesite un lector distinto va en
   `source-c5/` y entra por `c5_fuentes` en `tools/catalogo.json` (hoy A Coruña y Pontevedra llevan
   `Localizador.mc`; `tools/tienda.py` monta el `sourcePath` por fichero). Un cambio en `source/` que **no**
   degrade a nadie (un campo nuevo en la tesela, leído por el lector común) es posible, pero se presenta con
   la batería completa: 7X Pro (jungle del repositorio), 6X Pro `c`, 6 Pro `b` y los cuatro de 128 KB.
2. **Memoria de ejecución:** margen ≥ 7 KB en el pico (`medida_c5.py --punto … --lastre`), tesela ≤ 22,8 KB,
   zona ≤ 13 KB, y `--bordes` en verde.
3. **250 recursos** por app: A Coruña usa 237.
4. **La tienda entrega el mismo `.prg` a los cuatro modelos** (fēnix 5, 5S, 6 y 6S): lo que se recorte lo pierden
   todos los usuarios de la app, no solo este reloj.
5. **Tiempo de consulta en el fēnix 5:** el simulador no lo mide (reserva abierta). Toda palanca que haga
   recorrer más vértices o más hojas se prueba en la muñeca antes de publicar.

## 1. Qué leer antes de tocar nada (en este orden, ~25 min)

1. Este documento entero.
2. `tools/build_callejero.py`: la cabecera (FORMATO 4: qué hay en `S O C CB R V P E` y en las zonas), las constantes
   `RUN_EXT_U`, `RUN_EXT_MAX`, `RUN_NV_MAX`, `CB_U` (≈ línea 174), `encadenar_rural()` (≈ 1577),
   `partir_tirada()` (≈ 2021) y el bloque `VARIANTE == "c5"` (≈ 1622, 1865-1925, 2218-2345).
3. `tools/regiones.json`, bloque `coruna` → `c5` (y `pontevedra`).
4. El lector: `source/Tesela.mc`, `source/Buscador.mc` (comunes), `source-c5/Zonas.mc`, `source-c5/Localizador.mc`.
   `source-c5/Tesela.mc` y `Buscador.mc` son del FORMATO 5 (puerta del plan 2): **no se compilan** en las apps.
5. `tools/tienda.py` (cómo una app c5 elige sus fuentes), `tools/medida_c5.py` (memoria con la app real y GPS falso),
   `tools/ref.py` (fuerza bruta, vectores de test, `--par-mayor`).
6. `docs/plans/2026-10-27-c5-plan4-provincias.md` (reglas de volumen de la c5) y
   `docs/specs/2026-10-25-calle-formato4-relojes-128k.md`, §FORMATO 4.
7. La cabecera de `ciq.sh` (órdenes, candado del simulador, ruta neutra de compilación).

## 2. Plan por tareas (una tarea = un commit; cifras en este documento antes de pasar a la siguiente)

### T0 — Medir el reloj: el objetivo en KB ✅ (2026-10-29, 18:01, fēnix 5 por USB)

El fēnix 5 monta como disco (`/Volumes/GARMIN`, FAT16), no por MTP como el 7X Pro. Firmware 25.00, máquina virtual
de Connect IQ 3.1.9 (`GARMIN/GarminDevice.xml`).

| Qué | Medido |
|---|---|
| Volumen `GARMIN` | 57,0 MB en total · 5,7 MB usados · **51,1 MB libres** |
| `GARMIN/APPS/` | 160 KB: `GAQL4734.PRG` = Ironsight v4, **71.376 B**; `GAQL4811.PRG` = Ironsight Grid v2, **63.728 B**. Ningún `.PRG` de Calles (la hipótesis de la versión anterior, descartada) |
| Lo demás | `TEXT` 1,9 MB (idiomas), `REMOTESW` 1,3 MB, `EDM` 1,0 MB, `SUMMARY`/`EVNTLOGS`/`DEBUG` < 250 KB cada uno; `ACTIVITY` vacía |
| `APPS/LOGS/CIQ_LOG.YML` | no existe: ningún error de ejecución registrado |
| **`<IQAppExt>` de `GarminDevice.xml`** | **`MaxApps` 32 · `AppSpace` 2.097.152 B** |

**Conclusión: el disco no es el límite. Lo es la cuota de Connect IQ del fēnix 5: 2 MB (2.097.152 B) para todas
las apps juntas.** Con las dos esferas (135.104 B) quedan **1.962.048 B**. Calles A Coruña 3.5.3 (2.537.644 B)
**no cabe ni sola**: supera la cuota en 440.492 B; con las esferas faltan 575.596 B. Calles Pontevedra 3.5.3
(1.636.348 B) sí cabe con las dos esferas (sobran 325.700 B). Los `compiler.json` del SDK no declaran esta cuota
para ningún modelo de 128 KB (el 7X Pro declara `maxPrgFilespace` 64 MB): la de los fēnix 5S, 6 y 6S se lee en su
`GarminDevice.xml` cuando haya uno a mano. Mientras tanto, la del fēnix 5 es el objetivo.

**Objetivo: `.prg` del fēnix 5 ≤ 1.900.000 B** (cuota − esferas − 60 KB de margen para una esfera más o sus
actualizaciones): **−637.644 B, un −25,1 %** respecto de la 3.5.3. Sin esferas, ≤ 2.035.000 B (−19,8 %). Las tres
salidas ya medidas (≈ −13 %) **no llegan**: hacen falta las palancas de T2, o cobertura (T3).

- [x] Espacio, ocupación, `APPS/`, log y cuota, medidos.
- [ ] Comprobar si la cuota se aplica también por cable: copiar el `.prg` de la 3.5.3 a `GARMIN/APPS/` y ver si el
      reloj lo lista y lo abre (si por cable la ignora, el autor puede llevar su propia compilación mientras la de
      la tienda adelgaza). Solo con su permiso.

### T1 — Reparto reproducible del peso (`tools/peso_c5.py`)

- [ ] Datos: `VARIANTE=c5 REGION=coruna ./ciq.sh datos` (comprobar la orden exacta en la cabecera de `ciq.sh` y en
      `build_callejero.py`; en un worktree nuevo, antes `mkdir -p tools/out`). Las regiones se generan **en
      serie**: dos en paralelo en la misma copia hacen fallar la comprobación común de `Callejero.ZONA`.
- [ ] Script que lee `resources-gen-c5/coruna/jsonData/` y da, por tesela y en total: bytes estimados de
      `S O C CB R V P E` y de las zonas `S O F RL L LN H FZ`; número de tiradas, vértices, portales y nombres;
      teselas rurales (unidad 4 m) frente a urbanas (1 m); nombres repetidos entre teselas y entre hojas de zona.
      Misma convención que la medición del 2026-10-28 (5 B por número, cadena = bytes + 3) para poder comparar.
- [ ] Contraste con la realidad: `APP=coruna DEV=fenix5 ./ciq.sh release` y comparar la suma estimada con el
      `.prg`. La diferencia es el coste fijo por recurso más el código: anotarlo (237 recursos).
- [ ] Tabla en este documento. Las cifras de la medición del 2026-10-28 deben salir dentro de un ±5 % (la salida 1 ya está aplicada:
      las zonas pesan menos que en la tabla de §0).

### T2 — Palancas que nadie ha medido (cada una: KB ahorrados · qué se pierde · qué toca · tiempo en el reloj)

Se miden **regenerando sobre una copia**, sin tocar la app, de mayor a menor ahorro esperado, y se para en cuanto
las que valgan alcancen el objetivo de T0. Ninguna se aplica sin el visto bueno del autor sobre lo que se pierde.

- [ ] **A. Tiradas rurales más largas (R = 28 %).** Una tirada lineal se parte a 63 vértices o **240 m**
      (`RUN_EXT_MAX` 30 × `RUN_EXT_U` 8 m, 5 bits en la cabecera), también en las teselas rurales de 4 m donde
      las vías van encadenadas. Si la estimación de 5 B vale, 515 KB de R son **≈ 50.000 cabeceras** de 10 B.
      Medir: cuántas tiradas hay en teselas rurales y cuántas vendrían de partir por los 240 m; qué ahorro da
      (a) `ext` en unidades de 8 × U m en las teselas de 4 m (960 m por tirada) y (b) subir el tope de vértices.
      Toca: el generador y **el lector** (`EXT_U` es constante en `Callejero.mc`; haría falta leer U de la tesela,
      como ya hace la variante b con su unidad). Coste: la búsqueda recorre más vértices por tirada cerca del
      usuario → tiempo y watchdog en el fēnix 5; `ext` más grueso descarta menos tiradas lejanas.
- [ ] **B. Portales (P = 16 %, ≈ 295 KB; ya son solo urbanos).** Medir: (a) uno de cada dos por calle (el «portal
      más cercano» puede errar un número); (b) solo las calles con ≥ N portales; (c) por rangos de tramo (pierde
      el punto exacto; exige lector). Es una decisión de producto del autor: precisión frente a tamaño.
- [ ] **C. Nombres (S = 19 % en teselas).** Medir: (a) la salida 3 (sin repetir entre teselas, lector propio
      vía `c5_fuentes`); (b) cuánto pesan en `S` las calles que **solo cruzan** (NC las incluye aunque no tengan
      tirada en la tesela); (c) abreviar el tipo de vía al generar (pierde fidelidad en pantalla: hoy `Abrev`
      solo abrevia si el nombre no cabe). En las zonas, qué queda de los 293 KB de nombres tras la salida 1.
- [ ] **D. Vértices (V = 16 %).** `rural_dp` 8 → 12 y 15 m. Límite: la fuerza bruta de `ref.py` tolera la unidad de
      la tesela; con 15 m la distancia a la calle puede variar más que el error del GPS en pistas sinuosas.
- [ ] **E. Coste fijo por recurso** (de T1): si pesa, menos teselas más grandes no es opción (tope de 22,8 KB);
      sí lo es juntar zonas pequeñas que estén lejos del tope de 13 KB.
- [ ] **F. Las ya medidas, combinadas:** salida 2 (`rcel` 250) + salida 4' (−8 %, solo generador, un commit).

Para cada palanca que se mida: `ref.py` con 0 discrepancias, tests del fēnix 5 en verde y la fila en la tabla de
este documento.

### T3 — Cobertura (solo si T2 no llega al objetivo; decide el autor)

- [ ] Medir qué pesaría **«Calles A Coruña (urbana)»**: solo los municipios de la zona urbana de la provincia
      (ref:ine 15030 A Coruña, 15036 Ferrol, 15054 Narón, 15073 Ribeira, 15078 Santiago), sin rural.
- [ ] Medir la partición en **dos apps** (norte: A Coruña-Ferrol; sur: Santiago-Ribeira), con el corte por
      municipios enteros.
- [ ] Presentar al autor las opciones con sus KB, y lo que pierde cada una. La tienda no admite elegir región
      dentro de una app: cada opción es una ficha nueva.

### T4 — Aplicar lo elegido, verificar e instalar

- [ ] Lo elegido entra por banderas en el bloque `c5` de `tools/regiones.json` (como `zona_sin_margen`); nada
      en `source/` sin aprobación expresa del autor (límite 1).
- [ ] `ref.py` 0 discrepancias y puntos de control OK; `ref --gen-tests`; tests en fēnix 5, 5S, 6 y 6S
      (`APP=coruna DEV=<modelo> ./ciq.sh test`, salida a fichero, no por tubería).
- [ ] Memoria: `medida_c5.py coruna --bordes` y `--punto … --lastre` → margen ≥ 7 KB en el pico; si una palanca
      toca el lector, repetir también la escalera (`--escalera`).
- [ ] `APP=coruna DEV=fenix5 ./ciq.sh release`, copiar el `.prg` a `/Volumes/GARMIN/GARMIN/APPS/` **con las dos
      esferas puestas**: la prueba real es que instala y abre. Después, recorrido en la muñeca (Santiago, una
      aldea, coche) para el tiempo de consulta.
- [ ] Versión 3.5.4 a la tienda (*Upload New Version*; el botón lo pulsa el autor) con *What's New* ES/EN, y
      comprobarlo en la API del portal, no en la ficha pública.
- [ ] Pontevedra con el mismo método, si vale.

## 3. Trampas conocidas

- **Simulador compartido** entre proyectos: candado `/tmp/calles-sim.lock` de `ciq.sh`; lanzar siempre
  con `SIM_ESPERA=0`. Al acabar: *Kill App*, ningún `monkeydo` vivo, modelo neutro. Un `monkeyc` superviviente de
  un corte puede pisar `bin/test.prg`.
- `monkeydo` sale con rc=1 aunque todo pase (SDK 9.3): vale el «PASSED» del log. Con la salida de `ciq.sh test`
  por una tubería, el vigilante de 600 s la retiene hasta que vence: a fichero.
- Lo que sale del Mac (`release`, `tienda`, `instalar`) se compila desde `/private/tmp/ciq-build/` y la guarda
  `rutas` rechaza el producto si lleva `/Users/` dentro (2026-10-29).
- En un worktree nuevo, `mkdir -p tools/out` antes de `./ciq.sh datos`. Regiones en serie, nunca dos a la vez.
- `rcel` debe dividir a 2.500 m (la hoja menor): 100, 125, 250 valen; 200 no.
- Los absolutos de memoria del simulador cambian con su estado: para comparar dos versiones, las dos en el
  mismo simulador, seguidas (`--lastre` mide el margen, no el pico).
- Las zonas de A Coruña van a 13 KB, no a 20: con 20 cargan de una en una pero no 3-4 seguidas en una esquina.
- Con el jungle de una app de la tienda, los vectores de las zonas que no lleva salen FUERA: artefacto, no fallo.
- Nunca `--no-verify`.
- El código que se añada a la c5 se paga en el pico de memoria (la salida 1 costó +0,67 KB tras adelgazarla);
  medir antes de dar por buena cualquier palanca que toque el lector.

## 4. Verificación de punta a punta (antes de dar por hecha la tarea)

1. La tabla de T0 con el objetivo, y la de T1/T2 con lo que pesa cada palanca aplicada.
2. `ref.py` 0 discrepancias en A Coruña (y Pontevedra si se tocó); tests en verde en los cuatro modelos.
3. Margen de memoria ≥ 7 KB en el pico y `--bordes` en verde.
4. El `.prg` instala y abre en el fēnix 5 **con las dos esferas instaladas**, y el recorrido en la muñeca no
   nota la consulta más lenta.
5. Lo que cambia para el usuario (precisión de portales, pistas rurales, frontera entre parroquias) está escrito
   en el *What's New* y en la ficha de la tienda.
