# CALLE — formato binario (FORMATO 4) y Madrid entero en los relojes de 128 KB

Diseño del 2026-10-25. Es el paso 3 del plan «fēnix 5 en adelante» (formato binario) y el grupo C del paso 4:
fēnix 5, 5S, 6 y 6S, que dan 128 KB a una watch-app y tienen API 3.1 (los 5) o 3.4 (los 6).

## Lo que se midió antes de diseñar (simulador del fēnix 6)

| Medida | Resultado |
|---|---|
| App sin tesela, con los datos 6x | 64 KB de 126,8 |
| Un número en un array de un recurso JSON | **5 B** |
| Una cadena | su longitud **+ ~34 B** de cabecera (300 nombres: 16,5 KB sueltos, 6,7 KB unidos) |
| Base64 → `ByteArray` | pico de 2,3 veces el tamaño; recorrer 20.000 bytes uno a uno dispara el watchdog |
| Cargar un recurso | pide **~2,2 veces** su tamaño final (con 45,9 KB libres carga uno de 20,3 KB y no uno de 21,3), partido o no en varios arrays |
| Watchdog | 120.000 instrucciones por evento en los fēnix 5 y 6 (240.000 en el 6X y el 7) |
| `ResourceId` | desplazamientos de bytes en el `.prg` (3750, 27879…): no se pueden calcular desde un índice |
| Un array literal en el código | ~20 B de código por elemento (el índice de cajas de Madrid eran ~9 KB de código) |

Conclusión: bits empaquetados en `Array<Number>` (no `ByteArray`), todos los nombres de una tesela en una sola
cadena, y nada grande escrito como literal en el código.

## FORMATO 4 (todas las variantes)

La cabecera de `tools/build_callejero.py` es la referencia. En resumen, una tesela es
`[FORMATO, NC, PB, S, O, C, CB, R, V, P, E]`:

- **Nombres:** `S` es una sola cadena, con las calles y después los sufijos de portal, separados por `\n`.
  `O` guarda dónde empieza cada uno: 2 por número, 16 bits cada uno.
- **Por calle:**
  - `C`: el offset de su primera tirada y de su primer portal.
  - `CB`: una caja gruesa (4 × 8 bits, en unidades de 32 m). Con ella la búsqueda salta de un golpe las calles
    lejanas, y es lo que la deja dentro del watchdog de 120.000 instrucciones.
- **Tiradas:** cada una lleva una cabecera de 2 números:
  - el primer vértice (13 + 13 bits), la extensión (5 bits, en unidades de 8 m) y si es área;
  - el ancho de los deltas, la clase, los dos cruces y el número de vértices.

  La calle de la tirada va implícita por el orden. Los vértices siguientes van como deltas en complemento a dos,
  en un flujo de bits `V`. Las tiradas lineales se parten a 63 vértices o 240 m.
- **Portal:** un número de 32 bits, sin pérdida a 1 m:
  - las coordenadas, en 12 bits cada una, o 13 si la tesela pasa de 4.095 m;
  - el salto de número desde el anterior de su calle, en 5 bits, o 3 con coordenadas de 13 bits;
  - el sufijo, en 3 bits: uno de los 6 más frecuentes de la tesela.

  Lo que no cabe va a la tabla de escapes `E`.
- **Zonas:** `[FORMATO, S, O, F, RL, L, LN]`, con el ráster por tramos (RLE) a la misma resolución de 50 m y los
  nombres en una cadena. Los lugares van en 14 + 14 bits, lo que permite zonas de hasta ~13 km.
- **Hospitales y comisarías:** `[FORMATO, SN, ON, SD, OD, XY, T]`. Los nombres y las direcciones van en cadenas, y
  la posición y el tipo empaquetados: pasan de ~30 KB en el reloj a ~15.

Efecto en lo que ya había:

| Variante | Tesela más pesada (FORMATO 4, real) | Zona más pesada (real) | `.prg` |
|---|---|---|---|
| Madrid normal (7X Pro) | 20,7 KB (el informe del FORMATO 3 estimaba 81,5) | 4,6 → 1,7 KB | ~15 → 9,1 MB (con Santiago) |
| Madrid 6x (6X) | 40,4 KB (estimada antes en 150; en el simulador la app pasaba de 143 KB en Sol) | 10,5 → 2,9 KB | 2,2 → 1,24 MB |
| Santiago | 17,3 KB | 44 → 20,4 KB | — |

La búsqueda tarda la mitad: en Madrid en el 7X, de 34 a 14 ms en el simulador.

## Variante c: Madrid entero en 128 KB

`VARIANTE=c ./ciq.sh datos` (con `REGION=madrid`) lee `tools/regiones.json` → `madrid.c` y escribe
`resources-gen-c/`, `source-gen-c/` y `test-gen-c/`. `monkey.jungle` las asigna a `fenix5`, `fenix5s`, `fenix6` y
`fenix6s`. El manifiesto baja `minApiLevel` a 3.1.0.

### Teselas adaptativas (`teselar_kd`)

- La región se parte por el eje largo, en proporción a cuántas teselas necesita cada lado. Una caja que pide 3
  teselas se corta en un tercio y dos tercios, no por la mitad.
- Con 2 o 3 teselas, el corte se busca por bisección con el coste real, para llenar la primera hasta el tope.
- Al final se funden las vecinas que juntas caben.
- **Tope:** 26 KB de heap estimado (`tope_kb`), con lado ≤ 7.800 m y cortes en múltiplos de 10 m.
- Resultado: **225 teselas** de 20,5 KB de media, la mayor de 26,0 KB.
- **El índice:**
  - Las cajas van en un recurso (`<prefijo>cajas`) que `Geo.celda` carga al cambiar de tesela y suelta.
  - La lista de teselas (`Callejero.IDX`) sigue siendo código, porque los `ResourceId` no se pueden calcular.
  - Un punto que no cae en ninguna caja da la entrada `null` del final, que se lee como «sin calle».

### Zonas y recursos

- Zonas de 10 km: 16, la mayor de 10 KB reales.
- **Recursos:** 225 teselas + 16 zonas + puntos + cajas = **243 de 254** (el compilador corta en 254).

### Memoria (app de release en el simulador del fēnix 6, y la misma en el fēnix 5)

- **Código y datos:** 42,5 + 8,8 KB. Era 47 + 8,7 antes de sacar las cajas del código.
- **Al cargar una tesela:** 65 KB en uso y ~61 KB libres. Antes de cargarla, el `Localizador` suelta la zona.
- **Con tesela, zona y pantalla:** ~100 KB de 126,8.
- **Teselas probadas:**
  - las 3 con más tiradas (hasta 1.277) y las 3 más pesadas;
  - Sol («Puerta del Sol 11»), Gran Vía («23»), Don Ramón de la Cruz («85») y Salamanca.

  Búsqueda: 10–19 ms en el 6 y 18–27 ms en el 5, sin watchdog.
- **«Hospital/Comisaría más cercana»:** con la tesela cargada no cabía (25 KB libres). Ahora `MenuCalle.abrirIr`
  suelta la tesela y la zona (`Localizador.soltar`), los puntos ocupan 15 KB y, al volver, `forzar()` recarga.

### Verificación

- `ref.py` lee el FORMATO 4 por su cuenta, sin importar nada del generador.
- **Fuerza bruta con 0 discrepancias en las cuatro variantes:**
  - Santiago: 10.000 puntos;
  - Madrid normal: 10.000;
  - Madrid 6x: 10.000;
  - Madrid c: **40.000**, con portales 12.604/12.604.

  Los puntos de control, todos OK.
- **Tests:** 53/53 en el 7X Pro, 39/39 en el 6X y 39/39 en el fēnix 6 con los datos c.
  - Nuevos: textos de portal con escapes, raster por tramos y cajas adaptativas.
  - `Sintetica` empaqueta teselas, zonas y puntos como el generador.

## Pendiente

- **Pantallas:** el grupo C tiene 218 (5S), 240 (5, 6S) y 260 px (6). `source/L.mc` está fijada a 280: es el
  tramo 1b (maquetas), que bloquea publicarlo.
- **Tienda:** añadir `fenix5`, `fenix5s`, `fenix6` y `fenix6s` a CALLE Madrid en `tools/catalogo.json` cuando estén
  las maquetas. `tools/tienda.py` ya les da los datos c por la jungle. Cada `.prg` pesa ~4,6 MB: falta saber si los
  fēnix 5 tienen tope de tamaño de app.
- **Grupo B** (5X, 5 Plus, 6 Pro: 1,25 MB y tope de recursos): pueden llevar la variante c tal cual, o una con
  teselas mayores.
- **En la muñeca:** los menús (anotaciones, guía) no se pueden recorrer en el simulador por script; la memoria de
  la guía con anillo en un fēnix 6 queda por medir a mano.
