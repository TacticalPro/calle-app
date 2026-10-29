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

### T1 — Reparto reproducible del peso (`tools/peso_c5.py`) ✅ (2026-10-29)

- [x] Datos: `VARIANTE=c5 REGION=coruna ./ciq.sh datos` (≈ 1 min). En un worktree nuevo hacen falta `tools/cache`
      (enlace al del repositorio principal, 1,4 GB), `mkdir -p tools/out` y un `source-gen/` (enlace también):
      `ciq.sh` exige `source-gen/Callejero.mc` para compilar cualquier app, aunque la c5 no lo use.
- [x] `python3 -I tools/peso_c5.py coruna --prg bin/calle-release.prg` (la release: `APP=coruna DEV=fenix5
      ./ciq.sh release`, **2.537.148 B** desde `main` `84f402e`). Misma convención que la medición del 2026-10-28 y sus mismas cifras
      (R 27,6 % frente a 28; S 19,5 frente a 19; P 16,5 frente a 16; V 16,2 frente a 16).

| Bloque | KB | % |
|---|---|---|
| Teselas (135: 47 rurales de 4 m, 88 urbanas de 1 m) | 1.837 | 76,7 % |
| Zonas (100 hojas; 18.258 lugares, 17.948 nombres) | 550 | 23,0 % |
| `poi.json` + `cajas.json` | 8 | 0,3 % |
| **Total estimado** | **2.395** | |
| `.prg` real | 2.478 | +82 KB (3,3 %): el código (49 KB) y el empaquetado de 237 recursos (≈ 140 B cada uno). **La estimación de 5 B por número vale también para el fichero.** |

| Teselas, por sección | KB | % | rural | urbana |
|---|---|---|---|---|
| R, cabeceras de tirada | 506 | 27,6 | 152 | 355 |
| S, nombres | 358 | 19,5 | 150 | 208 |
| P, portales (+ E, escapes: 41) | 303 | 16,5 | 0 | 303 |
| V, vértices | 297 | 16,2 | 114 | 183 |
| C + CB + K (15 B por entrada de calle; 18.947 entradas) | 279 | 15,2 | 123 | 155 |
| O | 51 | 2,8 | 21 | 31 |
| **Total** | **1.837** | | **561** | **1.276** |

| Zonas, por sección | KB | % |
|---|---|---|
| S, nombres | 194 | 35 |
| RL, ráster de parroquias a 100 m | 140 | 25 |
| L + LN, lugares | 134 | 24 |
| O + F + FZ | 80 | 15 |

**Lo que dicen las cifras:**
- **Las tiradas son muchas y cortas, no largas y partidas:** 51.848 tiradas con 3,7 vértices de media; solo
  **1.634** llegan al tope de 240 m (749 rurales, 885 urbanas) y **ninguna** al de 63 vértices. **La palanca A
  (tiradas rurales más largas) queda descartada: cota de −16 KB.** El coste de R es una cabecera de 10 B por tramo
  entre cruces, y eso es el modelo de datos del lector común.
- **Nombres:** 130 KB de S se repiten entre teselas (salida 3); 874 entradas son calles que solo cruzan (30 KB entre
  S, C, CB y K); los sufijos de portal, 7 KB.
- **Portales:** 344 KB con los escapes, todos urbanos. La mitad, −170 KB.
- **Zonas:** dentro de una hoja los nombres ya no se repiten (0 KB); entre hojas, 70 KB (lugares homónimos en hojas
  distintas: no es duplicación). El ráster de 100 m pesa 140 KB.
- **Rural:** 561 KB de teselas (23 %) más la parte rural de las zonas (la mayoría de los 18.258 lugares).
- **Hace falta −637 KB y ninguna palanca sola llega.** Sin tocar el lector, en el mejor caso: ráster de 250 m (−115
  con sus recursos) + portales a la mitad (−170) + `track`/`service` (−80) + DP rural (por medir) ≈ −365 + DP. Con
  un `Tesela.mc` propio de la c5 (`c5_fuentes`): + salida 3 (−130) + calles que solo cruzan (−30) ≈ −525. **Lo que
  falte sale de la cobertura o de más precisión perdida.**

### T2 — Palancas que nadie ha medido (cada una: KB ahorrados · qué se pierde · qué toca · tiempo en el reloj)

Se miden **regenerando sobre una copia**, sin tocar la app, de mayor a menor ahorro esperado, y se para en cuanto
las que valgan alcancen el objetivo de T0. Ninguna se aplica sin el visto bueno del autor sobre lo que se pierde.

- [x] **A. Tiradas rurales más largas.** ~~Descartada en T1~~: solo 1.634 de 51.848 tiradas se parten por los
      240 m; cota de −16 KB. No merece tocar el lector.
- [ ] **F. Las ya medidas, combinadas (primero: solo generador, un commit):** salida 2 (`rcel` 250, −115 KB con
      sus recursos) + salida 4' (`track` y `service` rurales, −80 KB). Volver a medir juntas sobre la 3.5.3.
- [ ] **B. Portales (P + E = 344 KB, todos urbanos).** Medir: (a) uno de cada dos por calle (−170 KB; el «portal
      más cercano» puede errar un número); (b) solo las calles con ≥ N portales; (c) por rangos de tramo (pierde
      el punto exacto; exige lector). Decisión de producto del autor: precisión frente a tamaño.
- [ ] **C. Nombres (S = 358 KB en teselas).** Medir: (a) abreviar el tipo de vía al generar («Rúa», «Avenida»,
      «Camiño», «Estrada», «Lugar»: solo generador; pierde fidelidad en pantalla, aunque `Abrev` ya abrevia cuando
      no cabe); (b) la salida 3, nombres sin repetir entre teselas (−130 KB; `Tesela.mc` propio de la c5 vía
      `c5_fuentes`, y su coste en el pico de memoria); (c) las 874 calles que solo cruzan (−30 KB; comprobar qué
      hace el lector cuando el cruce A/B apunta a un nombre que ya no está).
- [ ] **D. Vértices (V = 297 KB; 114 rurales).** `rural_dp` 8 → 12 y 15 m, y DP urbano a 2 m. Límite: la fuerza
      bruta de `ref.py` tolera la unidad de la tesela; con 15 m la distancia a la calle puede variar más que el
      error del GPS en pistas sinuosas.
- [ ] **G. Teselas sin K (−84 KB).** K salta los vértices de las calles lejanas (watchdog) y lo añadió la variante
      b para sus teselas de 120 KB. **El lector común ya admite teselas sin K** (`source/Tesela.mc`: `K =
      datos.size() > 11 ? datos[11] : null`, como las de la variante normal): es solo generador (`"k": false`).
      Coste: tiempo de búsqueda en el fēnix 5; medir con los tests (watchdog) y en la muñeca.
- [x] **E. Coste fijo por recurso:** medido en T1, 33 KB en 237 recursos (≈ 140 B cada uno). Nada que rascar.

Para cada palanca que se mida: `ref.py` con 0 discrepancias, tests del fēnix 5 en verde y la fila en la tabla de
este documento. **Suma de lo medible sin tocar el lector (F + B + C.a + D): del orden de −400 a −450 KB; con
C.b y C.c, −550 a −600. El objetivo son −637.** Si al medir no se llega, T3.

**Decisión del autor (2026-10-29):** portales a la mitad, sí; abreviar los tipos de vía, sí; el rural se queda
(ni versión urbana ni menos lugares), solo menos detalle en pistas.

**Tanda 1 (2026-10-29, sobre `main` `84f402e`, con `C5_OPTS`; total estimado de `peso_c5.py`, base 2.395 KB):**

| Palanca (bandera del bloque c5) | Ahorro | Recursos | Qué cambia |
|---|---|---|---|
| Ráster de parroquias a 250 m (`rcel`) | −108 | 226 (−9 hojas) | frontera de parroquia a 250 m |
| Sin `track` ni `service` rurales (`rural_sin`) | −82 | 234 | 5.093 vías fuera |
| DP rural 12 m / 15 m (`rural_dp`) | −27 / −42 | 235 | pistas menos fieles |
| Unidad rural 8 m (`rural_u`) | falló | | `assert B_LADO_U * C5_RURAL_U < 1 << 15`: no se insiste |
| Portales uno de cada dos (`portales_mitad`) | −178 | 231 | 21.161 portales fuera |
| Tipo de vía abreviado (`abreviar`) | −51 | 235 | 26.686 nombres |
| **Las cinco aprobadas, DP rural 12** | **−441 → 1.954 KB** | 216 | `.prg` ≈ 2.036 KB: **faltan ≈ 180 KB para la cuota estricta y ≈ 240 para el objetivo** |

Reparto tras la combinación: teselas 1.504 KB (R 475 · S 287, de ellos 101 repetidos entre teselas · V 256, 173
urbanos · P + E 186 · C + CB + K 252) · zonas 442 (S 192 · L + LN 134 · RL 52).

**Tanda 2 (2026-10-29), sobre la combinación B (las cinco aprobadas, DP rural 12; 1.954 KB, 216 recursos):**

| Añadido a B | Ahorro | Recursos | Qué cambia |
|---|---|---|---|
| Teselas sin K (`"k": false`) | **−108** | 206 | sin K cabe más en cada tesela (125 → 115); la búsqueda lee las cabeceras R de las calles lejanas en vez de saltarlas: tiempo, por medir |
| DP urbano 2 m / 3 m (`urb_dp`; venía a 0,75) | −41 / −65 | 213 / 212 | geometría urbana a ≤ 2-3 m, por debajo del error del GPS |
| DP rural 15 en vez de 12 | −11 | 215 | |
| Ráster de parroquias a 500 m | −37 | 207 | frontera de parroquia a 500 m |
| Portales uno de cada tres (`portales_cada`) | −74 | 208 | el portal puede errar dos números |
| **C = B + DP rural 15 + sin K + DP urbano 2** | **−161 → 1.793 KB** | 204 | `.prg` ≈ 1.870 KB ≈ 1.915.000 B: **cabe en la cuota con las dos esferas (47 KB de sobra); 15 KB por encima del objetivo con margen** |
| C + ráster 500 | −199 → 1.755 | 195 | `.prg` ≈ 1.875.000 B: bajo el objetivo |
| C + portales uno de cada tres | −213 → 1.741 | 204 | `.prg` ≈ 1.862.000 B: bajo el objetivo |

Reparto de C: teselas 1.343 KB (R 462 · S 278 · V 213 · P + E 181 · C + CB 163) · zonas 442. Lo que queda grande es
estructural (R, una cabecera por tramo) o nombres.

**C compilada de verdad (2026-10-29): `.prg` del fēnix 5 = 1.915.788 B** (la estimación daba 1.915.000), 204
recursos. **Cabe en la cuota con las dos esferas: 1.915.788 + 135.104 = 2.050.892 < 2.097.152 (46 KB de sobra).**
`ref.py`: fuerza bruta de 10.000 puntos, 0 discrepancias (portales 1.338/1.338, tramos 4.783); zonas 0. Los puntos
de control se rederivan (`ref --derivar`): el fichero guardaba los nombres sin abreviar.

**Verificación de C en el simulador (2026-10-29, 19:00):** fēnix 5, `APP=coruna DEV=fenix5 ./ciq.sh test`: **55/55**.
Puntos de control **10/10** tras rederivarlos (cambian los nombres y ≤ 1 m de posición por el DP urbano; «franco»
admite «Pr. de Fonseca» como antes admitía «Praza de Fonseca»: la mitad del tramo cae dentro del polígono de la
plaza). `ref --gen-tests`: 62 vectores y una ruta de 37 fixes. **Pendiente, sobre los datos definitivos (T4):** 5S, 6
y 6S; `medida_c5.py --bordes` y `--punto … --lastre` (no cambia ningún byte de código: el margen debería seguir en
≈ 7,45 KB); la muñeca.

Trampas nuevas: `ref.py` corre con `python3 -I`, que no pone `tools/` en `sys.path`, así que un `import
build_callejero` suelto falla (se añade la carpeta antes de importar). Y un simulador abierto a mano desde el
binario dejó `monkeydo` sin conectar y el log vacío hasta el corte de 600 s: cerrarlo y que lo abra `ciq.sh`.

### T3 — Cobertura (solo si T2 no llega al objetivo; decide el autor)

- [ ] Medir qué pesaría **«Calles A Coruña (urbana)»**: solo los municipios de la zona urbana de la provincia
      (ref:ine 15030 A Coruña, 15036 Ferrol, 15054 Narón, 15073 Ribeira, 15078 Santiago), sin rural.
- [ ] Medir la partición en **dos apps** (norte: A Coruña-Ferrol; sur: Santiago-Ribeira), con el corte por
      municipios enteros.
- [ ] Presentar al autor las opciones con sus KB, y lo que pierde cada una. La tienda no admite elegir región
      dentro de una app: cada opción es una ficha nueva.

### T4 — Aplicar lo elegido, verificar e instalar

**Decisión del autor (2026-10-29): «C tal cual, sin más margen».**

- [x] C fijada en el bloque `c5` de `coruna` en `tools/regiones.json` (`rcel` 250, `rural_sin`, `rural_dp` 15,
      `portales_mitad`, `abreviar`, `urb_dp` 2, `k` false; la nota dice por qué). `source/` intacto. Regenerada sin
      `C5_OPTS`: el mismo `.prg`, **1.915.788 B**, 204 recursos (113 teselas + 91 hojas).
- [x] `ref.py` 0 discrepancias (10.000 puntos; portales 1.338/1.338; zonas 0); puntos de control 10/10 rederivados;
      `ref --gen-tests` 62 vectores. **Tests: fēnix 5, 5S, 6 y 6S, 55/55 cada uno.**
- [x] Memoria (`medida_c5.py`, fēnix 5, 2026-10-29 19:15-19:35, lastre retenido desde el arranque):
      - `--punto` en las dos teselas más pesadas (t71 y t25) **con 7 KB de lastre**: cargan, 20,5 KB libres
        después, ≤ 17 ms. El margen en el peor arranque en frío sigue ≥ 7 KB, como en la 3.5.3 (7,45 KB).
      - `--bordes` (18 puntos a 300 m de los bordes y esquinas de las tres hojas más pesadas, z1_6_11 de 12,5 KB
        con 532 lugares, z0_5_8 y z0_1_7; hasta 4 hojas seguidas): **sin lastre, todo carga**, ≥ 21,9 KB libres en
        reposo, ≤ 22 ms; **con 3 KB de lastre, todo carga** (≥ 18,9 KB); **con 5 KB, Out Of Memory** en el
        primer punto. El margen en el pico de la esquina está entre 3 y 5 KB. En la 3.5.3 los bordes se midieron sin lastre:
        para saber si C lo empeora, la misma prueba sobre los datos de la 3.5.3 en el mismo simulador:

        | `--bordes` (fēnix 5, mismo simulador, 19:15-19:45) | 3.5.3 publicada | **C** |
        |---|---|---|
        | sin lastre | carga todo; mínimo libre en reposo 19.992 B | carga todo; **21.904 B** |
        | lastre de 3 KB | **Out Of Memory** en el 2.º punto | carga todo; 18.872 B |
        | lastre de 5 KB | Out Of Memory | Out Of Memory |

        **C no empeora el margen de la esquina: lo mejora** (las teselas sin K dejan más sitio). Se acepta sin tocar
        `tope_zona_kb`. Hojas más pesadas: 3.5.3 z0_1_6 (12.075 B, 296 lugares); C z1_6_11 (12.519 B, 532 lugares).
- [x] Datos de C restaurados tras la comparación y release recompilada: **1.915.788 B**, SHA-256 `c77390ff…`.
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
