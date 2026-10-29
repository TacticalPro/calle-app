# C5 · Plan 4: Calles A Coruña y Calles Pontevedra en los relojes de 128 KB

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Pasos con `- [ ]`.

**Decisión del autor (2026-10-27):** de momento, dos apps por provincia para los relojes de 128 KB (fēnix 5, 5S, 6
y 6S): **Calles A Coruña** y **Calles Pontevedra**. Datos en FORMATO 4 y `source/` sin tocar. Lugo y Ourense, más
adelante (el generador ya las admite: basta con añadirlas a `tools/regiones.json` y al catálogo).

**Goal:** generar y empaquetar las dos apps, cada una dentro de 128 KB de memoria y del tope de 250 recursos,
**sin cambiar ni un byte de `source/`**. El 7X Pro, el 6X Pro y la variante b siguen igual.

**Base:** los recuentos del plan 3, que quedó en borrador fuera del repositorio, y la memoria medida en la Task 5
del plan 2 (`docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md`, *Memoria*).

---

## Lo que cambia respecto de la app de siempre

| Pieza | Apps provinciales | De dónde sale |
|---|---|---|
| Lector de teselas | el común (`source/Tesela.mc`, `Buscador.mc`), con U y K de la variante b | sin cambios |
| Lector de zonas | **`source-c5/Zonas.mc`**: árbol cuaternario de 20 → 10 → 5 → 2,5 km | nuevo, solo en estas apps |
| Selección del lector | `sourcePath` por fichero: `source/*.mc` sin `Zonas.mc`, más `source-c5/Zonas.mc` | `tools/tienda.py` |
| Datos | variante `c5` de `tools/build_callejero.py` (`resources-gen-c5/<provincia>/`) | nuevo |

**Por qué hace falta un lector de zonas propio.** El común solo admite una rejilla de un nivel (`ZONA`, `ZIDX[i]`).
Con un solo nivel, las zonas de A Coruña no caben: con 10 km, 13 pasan del tope; con 5 km, son 435 recursos.
Con el árbol, cada zona se parte en cuatro mientras pase del tope, hasta 2,5 km, y ninguna hoja queda por encima.

## Reglas de volumen (variante `c5`)

Son las de la especificación c5 (`tools/medir_c5.py`, con los 15 municipios):
- **Zona urbana** = los 15 municipios con callejero completo (`ref:ine` de las parroquias).
- **Dentro de la zona urbana:** todo, como en la variante b (trozos, portales y sendas).
- **Fuera de la zona urbana:**
  - las vías lineales de una misma calle se encadenan por un nodo extremo común, sin trocear, y se simplifican con
    Douglas-Peucker a 8 m;
  - las áreas sí entran;
  - no entran sendas (clase 2), portales ni parajes (`tipo == 4`).
- **Provincia:** por celda de 1 km, según el `ref:ine` de las parroquias.
  - Calles: por el centro de su caja.
  - Parroquias: por el centro de su caja.
  - Portales y hospitales: por su posición.
  - Lugares: los de la provincia y los que están a menos de 1,5 km de ella.
- **Unidad por tesela:**
  - 1 m si la tesela, con su margen, **toca** la zona urbana (rejilla de 500 m; lado ≤ 7,9 km);
  - 4 m si no (lado ≤ 31,4 km);
  - K siempre.
  - Al principio se usaba la regla del centro de la tesela, pero una tesela del borde de la ciudad de Pontevedra iba
    en 4 m y la cuantización cambiaba el tramo de una calle con portales (1 discrepancia en la fuerza bruta).
- **Corte geométrico:** una caja que no cabe solo por el lado (31,4 km, o 7,9 km si toca la zona urbana) se parte
  por su mitad geométrica, no por la mediana del peso. Así no quedan tiras casi vacías: Galicia entera baja de 272 a
  245 teselas.
- **Proyección:** la de Galicia (`regiones.json → galicia.bbox`), la misma de los recuentos.

## Topes y recuentos

### Primer intento (topes de la Task 5 del plan 2): no vale

Tesela de 27,6 KB y zona de 13 KB, el 10 % por debajo de lo que cargó la puerta en modo app (30.712 + 14.328 B).
Recursos: A Coruña 234 y Pontevedra 173. **En la app real, las dos se caen con «Out Of Memory» al cargar la primera
tesela** (simulador del fēnix 5, modo app, `tools/medida_c5.py`). La puerta suponía que la app usa 66 KB con la
retención del primer recurso pagada. La app real arranca con **69,7-72,2 KB** sin haberla pagado: el código y los
datos fijos son 55-57,5 KB (`--build-stats`), y los índices de la región van como literales en `Region<Nombre>.datos()`
(~28 B de código por entrada).

### Memoria medida con la app real (fēnix 5, A Coruña)

| Prueba | Carga | No carga |
|---|---|---|
| Primera tesela, en frío | 26.400 B | 27.865 B (al cargar la tesela) |
| Zona con la tesela en memoria: tesela + 2 × zona | 46,2 KB | 49,5 KB (al cargar la zona) |

La carga de un recurso pide ~2 veces su tamaño. Topes con un 10 % de margen: **primera tesela ≤ 23,8 KB** y
**tesela + 2 × zona ≤ 41,6 KB**. Con el ~1 KB de código que puede añadir el arreglo de textos (otra rama, en
`source/`), la tesela baja a **22,8 KB**.

### Recuentos con esos topes (generador real)

| | Tesela / zona | Recursos |
|---|---|---|
| A Coruña, zona junto a la tesela | 20 / 10,8 · 22 / 9,8 · 23,8 / 8,9 | 308 · 322 · 340 ✗ |
| A Coruña, **zona con la tesela soltada** (palanca 1) | 23,8 / 16 · 23,8 / 20 · 23,8 / 23,8 | 237 · 222 · 210 ✓ |
| Pontevedra, zona junto a la tesela | **20 / 10,8** · 23,8 / 8,9 | **222** · 245 ✓ |

### Lo que se queda

- **Pontevedra:** teselas de 20 KB y zonas de 10,8 KB, con la arquitectura de siempre. 222 recursos.
  **Aceptada (2026-10-27):**
  - tests: 48/48 en fēnix 5, 5S, 6 y 6S;
  - modo app en el fēnix 5: los 3 peores pares y la tesela y la zona mayores, 3/3; arranque en frío en t46, 3/3;
  - una pasada en 5S, 6 y 6S, con ≥ 18,4 KB libres.
- **A Coruña:** teselas de 22,8 KB y zonas de 20 KB, con la **palanca 1**. 222 recursos.
  - Qué hace: `source-c5/Localizador.mc` consulta la zona con la tesela soltada, solo al moverse 100 m o al forzar,
    y luego vuelve a cargar la tesela. El pico es el mayor de 2 × tesela y 2 × zona.
  - Condiciones del coordinador:
    - (a) la calle y el tramo nunca se retrasan; parroquia y lugar, como mucho 100 m; sin pantalla en blanco ni parpadeo;
    - (b) cada consulta de zona tarda ≤ 1 s en el peor par, sin watchdog, 3/3;
    - (c) 10 min en coche por Santiago (un fix cada 10 s) sin OOM ni watchdog;
    - (d) un 10 % de margen con el ~1 KB de textos descontado.
  - **Resultado (simulador del fēnix 5, 2026-10-27, 10:16-10:29): cumple las cuatro.**
    - Peores pares (t23/t59/t32 con zonas de 20 KB) y tesela y zona mayores: 3/3, 8-10 ms por actualización con
      consulta de zona, ≥ 26,9 KB libres.
    - Arranque en frío en la tesela mayor (t18): 3/3, ≥ 29,5 KB libres.
    - En coche, 10 min por Santiago (60 fixes cada 10 s, con la zona consultada en casi todos): 60/60 sin OOM ni
      watchdog, máximo 20 ms, ≥ 19,3 KB libres.
    - Tests: 51/51 en fēnix 5, 5S, 6 y 6S.
    - El arreglo de textos añade +936 B en el fēnix 5, dentro del kilobyte descontado.
    - **Reserva:** los ms del simulador no son los del reloj. El tiempo de cada consulta de zona en el fēnix 5 se
      comprueba en la prueba de campo.
- **Palanca 2** (bajar el arranque): recortar la rejilla de zonas a la caja de la provincia ahorraría unas 70 entradas
  nulas (~2 KB de código). Queda en reserva.

---

## Convivencia

- Worktree `~/code/calle-c5p3` (rama `c5-plan3`). Commits con `git add <ruta>`. **Nunca push**: la revisión de
  privacidad y la subida las hace el coordinador. En los textos, «zona urbana».
- `tools/cache/` es una copia (clonada con `cp -c`) de la de `~/code/calle-fenix`. El original no se toca.
- Simulador: turno con el coordinador y el candado `/tmp/calles-sim.lock`. Antes de medir, una ejecución de prueba con
  la salida de error de `monkeydo` a la vista.
- `main`: turno con el coordinador y `--ff-only`.
- Tienda: solo con la confirmación del autor en la sesión.

---

### Task 1 · Variante `c5` del generador
Archivos: `tools/build_callejero.py`, `tools/regiones.json`.
- [ ] `--variante c5`; `regiones.json`: `coruna` y `pontevedra`. Cada una lleva su `provincia` y `datos_de: galicia`
      (lee el extracto y el Catastro de Galicia), la proyección de Galicia y `c5`, con estos campos: `zona` 20000,
      `zona_min` 2500, `tope_kb` 27.6, `tope_zona_kb` 13, `rcel` 100, `zu` 2, `rural_u` 4, `rural_dp` 8 y `urbana`
      (los 15 INE).
- [ ] `preparar_c5()`: las reglas de volumen de arriba. Se aplican sobre las vías, los portales, las parroquias, los
      lugares y los hospitales antes de trocear.
- [ ] `teselar_kd`: corte geométrico y lado máximo de 4 × 7.900 − 2·BUF. `empaquetar`: U por zona urbana y K.
      Todo detrás de `VARIANTE == "c5"`.
- [ ] Zonas en árbol: una raíz por celda de 20 km. Mientras la zona pase de `tope_zona_kb` y mida más de 2,5 km, se
      parte en cuatro. Cada hoja lleva su lado en `z[10]`. El índice `ZIDX` es una lista de raíces; cada entrada es un
      `ResourceId`, `null` o un `Array` de cuatro hijos en orden SO, SE, NO, NE.
- [ ] Topes duros: el generador falla si una tesela o una zona pasa de su tope, o si la región pasa de 250
      recursos. En la c5 el tope se comprueba **por región**, porque cada app lleva una sola.
- [ ] Las variantes `normal`, `c` y `b` no cambian: Santiago (normal) generado antes y después, `diff -r` vacío.

### Task 2 · `tools/ref.py` con el árbol
- [ ] `Ref._zona` baja por el árbol (el lado sale de la hoja). Meta: `z_mayor_xy`, el centro de la hoja más pesada.
- [ ] `--variante c5`. Fuerza bruta de 40.000 puntos sin discrepancias, zonas incluidas, en las dos provincias.
- [ ] Puntos de control propios de cada provincia (`puntos_control-<provincia>.json`), con un punto rural sin portal.
- [ ] `--gen-tests` → `test-gen-c5/<provincia>/`: una carpeta por app, porque cada app lleva sus propios vectores.
- [ ] `--par-mayor`: el par (tesela, zona) más pesado que conviven en un punto, con su lat/lon.

### Task 3 · `source-c5/Zonas.mc`
- [ ] El mismo módulo `Zonas` que el común (`soltar`, `consultar`, `buscar`, `par16`, `nombre`), con estos cambios:
  - `consultar` baja por el árbol de `Callejero.ZIDX`;
  - la zona cargada se identifica por la raíz y el camino;
  - `buscar` toma el lado de `z[10]` y, si no lo tiene (zonas sintéticas de los tests), `Callejero.ZONA`.
- [ ] Los tests comunes (`ZonasTest`, `Vectores`) pasan sin cambios.

### Task 4 · Empaquetado
- [ ] `tools/catalogo.json`: `coruna` («Calles A Coruña») y `pontevedra` («Calles Pontevedra»).
  - Id nuevo cada una.
  - Relojes: `fenix5`, `fenix5s`, `fenix6` y `fenix6s`.
  - `"variante"`: c5 en los cuatro.
- [ ] `tools/tienda.py`: variante `c5`.
  - `source` se expande a `source/*.mc` sin `Zonas.mc`, más `source-c5/Zonas.mc`; la lista se genera, para que
    un fichero nuevo del común no se quede fuera.
  - `test-gen-c5` → `test-gen-c5/<provincia>`.
- [ ] `ciq.sh`: `APP=<app> ./ciq.sh test` compila con el jungle de la app.
- [ ] `ciq.sh privacidad` también mira `source-c5`.

### Task 5 · Simulador (turno con el coordinador)
- [ ] Ejecución de prueba de cada app en el `fenix5`, con la salida de error de `monkeydo` a la vista.
- [ ] Tests de las dos apps en el `fenix5`, `fenix5s`, `fenix6` y `fenix6s`: todo en PASS, incluidas las cadenas
      (watchdog).
- [ ] Memoria con la app real en modo app (sin tests): jungle de medida con un `Gps.mc` falso (`medida/Gps.mc`), que
      reparte posiciones fijas y pone en el registro la memoria usada. Se lleva al punto del par más pesado
      (`ref.py --par-mayor`), con la tesela y luego la zona. **3 veces** por app. Si A Coruña falla una, tesela de
      26 KB y se recuenta.

### Task 6 · Cierre
- [ ] `.iq` de las dos apps (`APP=coruna ./ciq.sh tienda`, `APP=pontevedra …`), **sin subirlos**.
- [ ] Commits y pasar al coordinador la lista para la revisión de privacidad.
- [ ] Registro del autor.
