# CALLE v3 — hora grande, zonas (Santiago y Madrid), hospital y comisaría, fēnix 6X y beta

Diseño del 2026-10-24. Parte de la v2 (`2026-10-23-calle-v2-design.md`).

## Alcance

1. **Hora más grande**, para usar CALLE también como reloj sin perder la calle.
2. **Zona del callejero** elegible en el menú (y desde Garmin Connect en la versión de la tienda), con Madrid
   entero además de Santiago. Valorar «todo Madrid de golpe» frente a «por distritos».
3. **Ir al hospital o la comisaría más cercanos** (no estaba implementado: la v2 lo dejaba fuera).
4. **Compatible con el fēnix 6X Pro / Sapphire** (`fenix6xpro`).
5. **Beta** en la Connect IQ Store, como la de la esfera.

## 1. Hora

- Arriba, centrada en y = 34: Roboto Condensed Bold vectorial de 44 px en el fēnix 7 (86 px de ancho);
  en el 6X, que no tiene vectoriales, la mayor de sistema que no pase de 50 px (FONT_LARGE, 43 px).
- El punto de calidad del GPS, a su izquierda. Debajo (y = 63), la línea pequeña: el barrio o, si el dato es
  viejo, su edad en amarillo (antes iba junto a la hora).
- El nombre de la calle baja: franja desde y = 58 (sin línea) o y = 76 (con ella). Para que los nombres muy
  largos sigan cabiendo en tres líneas se añade la vectorial de 26 px a la cadena grande y se gana un poco
  abajo (el número va 4 px por debajo de la franja). Maquetas: `tools/out/mockups.png`.

## 2. Zonas: varias regiones en la app

**Generador.** `tools/regiones.json` describe cada región (id estable, prefijo de recursos, caja, zonas,
fuentes de portales). `./ciq.sh datos` (REGION=…) escribe cada una en `resources-gen/<región>/` con ids de
recurso prefijados (`st804`, `mt1234`…) y su módulo `source-gen/Region<Nombre>.mc`, y rehace lo común:
`Callejero.mc` (constantes del generador y la región activa) y `Regiones.mc` (ids, nombres y cajas).

**Reloj.** `Callejero` ya no es constante: `Callejero.activar()` toma los datos de una región. Los índices
(una entrada por tesela) se construyen al activarla y se sueltan al cambiar: solo la región activa ocupa
memoria. `Tesela` y `Zonas` comparan `Callejero.ID` con el de lo que tienen cargado.

**Ajuste «Zona»** (`source/Ajustes.mc`, propiedad `zona`):
- **Automática** (por defecto): la región cuya caja contiene la posición; si ninguna, la última usada.
- **Fija** (Santiago, Madrid…): siempre esa; fuera de ella, FUERA DE ZONA «(fijo)».
- Se cambia en el menú del reloj y, en la versión de la tienda, desde Garmin Connect. Junto a `Notas.mc`,
  `Ajustes.mc` es el único módulo que guarda algo (la zona y la última región); `./ciq.sh privacidad` lo vigila.

**¿Todo Madrid o por distritos?**
- **fēnix 7X Pro: todo Madrid.** El reloj nunca carga la ciudad entera: solo la tesela de 500 m en la que
  está (y su zona de 2 km). Elegir distrito no ahorraría memoria y obligaría a cambiarlo al cruzar una
  frontera de distrito. Lo que crece es el fichero de la app.
- **fēnix 6X: por partes.** Su máquina virtual no admite más de 254 recursos de datos por app (el
  compilador lo dijo con Santiago: 1.216). Ahí van teselas y zonas mayores y, de Madrid, los distritos
  que se elijan (§4).

**Madrid.**
- Caja: el término municipal (relación OSM 5326784) más ~500 m.
- Calles de OSM, bajadas por partes (Overpass corta las respuestas grandes; una parte que falla se parte
  en cuatro).
- **Portales del callejero oficial del Ayuntamiento** (datos.madrid.es, conjunto 213605, CC BY 4.0;
  214.676 direcciones frente a unas 97.000 en OSM). Como con el Catastro en Santiago: el número viene de
  ahí y el nombre lo pone siempre la vía de OSM; casan por la misma clave normalizada que `addr:street`.
- **Barrio y distrito por polígono** (OSM admin_level 10 y 9): «Sol · Centro». En Santiago el polígono es
  la parroquia y el barrio sale de los nodos; en Madrid el polígono es el barrio (`Callejero.ZBARRIO`).

## 3. Ir al hospital o la comisaría

- Datos por región (`<prefijo>poi`): nombre, dirección, posición y tipo. Hospitales: con urgencias
  (`emergency=yes` o «Urgencias…») o que se llamen hospital; fuera centros de salud y clínicas. Policía:
  comisaría CNP, otra dependencia del CNP (DNI, divisiones, unidades), municipal/local, Guardia Civil u
  otra; fuera las oficinas de la DGT. Correcciones en `overrides-<región>.json` → `poi` (p. ej. un hospital con la dirección mal puesta en OSM).
- Menú: «Hospital más cercano» y «Comisaría más cercana» (CNP; al final, «Otras policías»). Lista de los
  8 más cercanos a la última posición, con distancia y rumbo cardinal.
- Guía (`VistaIr`): flecha hacia el sitio, relativa a la brújula del reloj (`Activity.Info.currentHeading`,
  sin pedir el permiso `Sensor`); sin brújula, norte arriba. Distancia **en línea recta**, dirección,
  «HA LLEGADO» a menos de 30 m. ARRIBA/ABAJO pasan al anterior o siguiente.
- **No hay ruta por calles:** el reloj no lleva la red viaria ni la API deja usar la navegación del reloj
  sin red. Se dice en pantalla («línea recta»).

## 4. fēnix 6X

- `fenix6xpro` en el manifiesto; `minApiLevel` 3.4.0. Sin vectoriales (`Fuentes.mc` cae a las de sistema),
  sin `createBufferedBitmap` (solo en tests) y sin pantalla táctil (el toque no recalcula; recalcula solo).
- **Datos compactos** (`VARIANTE=6x ./ciq.sh datos` → `resources-gen-6x/`, `source-gen-6x/`;
  `monkey.jungle` los elige para el 6X): teselas y zonas mayores según `compacta` de cada región, y Madrid
  solo por `distritos`. El generador corta si se pasa de 250 recursos.
- **FORMATO 3** de tesela (para todas): 1.023 calles por tesela (antes 255) y coordenadas de 12 bits
  (teselas de hasta 3,9 km). La calle del portal pasa a `H`.
- La beta solo la puede instalar el desarrollador: para instalarla por cable en un fēnix 6X, `./ciq.sh prg6x` →
  `bin/calle-fenix6x.prg`, que se copia a `GARMIN/APPS`.

## 5. Beta

- Id propio (`BETA_ID` en `ciq.sh`), distinto del de las instalaciones por cable: la beta y la instalada a
  mano son dos apps distintas en el reloj, y las anotaciones de la instalada se quedan en ella.
- `./ciq.sh beta` → `bin/calle-beta.iq` (fēnix 7X Pro, 7X Pro sin Wi-Fi y 6X). Ficha: `./ciq.sh` no la
  genera; `tools/mockup.py --ficha` → `docs/tienda/`. Atribución obligatoria en la descripción:
  «© colaboradores de OpenStreetMap», «Fuente: Dirección General del Catastro», «Fuente: Ayuntamiento de
  Madrid (datos.madrid.es)».
  Textos de la ficha, en español y en inglés: `docs/tienda/descripcion.md`.

## 6. Verificación y cambios (2026-10-24, noche)

- **Memoria real en el simulador** (app de release, traza GPX reproducida en *Simulation › Activity Data*,
  *File › View Memory*):
  - fēnix 7X Pro, tesela más pesada de Madrid (t2343, ya en Majadahonda): 358,6 de 763,6 KB, pico 394,1 KB;
    en Sol, 345,5 KB y pico 370,3 KB. El pico incluye el cambio de Santiago a Madrid;
  - fēnix 6X, Sol con los datos compactos: 143,2 de 1.275,4 KB, pico 207,6 KB.
- **«≈» → «~».** Las fuentes de sistema (CDPG, página de códigos latina) no traen «≈» y lo pintaban como
  «�»: en DOS CALLES (`FONT_XTINY`), en todo el 6X y en el menú de anotaciones. `Fmt.numero` y
  `Notas` usan «~»; `Fmt.legible` convierte las anotaciones antiguas al mostrarlas. Ningún nombre de calle
  de los datos tiene caracteres fuera de esa página.
- **Variantes del nombre** (`unificar_variantes` en el generador). OSM etiqueta trozos de una misma calle
  con y sin partículas («Calle de Alcalá» / «Calle Alcalá»): en Madrid, 368 pares que se tocan. Sin
  unificar, el cambio de nombre parecía un cruce (tramo falso) y podía dar DOS CALLES con la misma calle.
  - Se juntan las vías de la misma `clave_unir()` a ≤ 20 m, en cadena; las homónimas lejanas (otro pueblo)
    no se tocan. `clave_unir` conserva las partículas de una letra: «Rúa "E"» y «Rúa "D"» son calles
    distintas.
  - El nombre es el de más metros pesados por tipo (`PESO_NOMBRE`: calzada 1, peatonal 0,5, senda 0,1,
    área 0,05). Sin el peso, el perímetro del área peatonal «Calle Arenal» le ganaba en Sol a «Calle del
    Arenal».
  - Lista de cambios en `tools/out/variantes-<región>.txt`: 6 en Santiago y 374 en Madrid.
  - Fuerza bruta: 0 discrepancias en las cuatro combinaciones; 51/51 tests en el 7X Pro y en el 6X.
- **fēnix 6X solo con Madrid** (2026-10-24): una parte de la ciudad.
  - Santiago sale de la variante 6x: ocupaba ~209 de los 250 recursos. Su `compacta` queda como
    `compacta_retirada` en `tools/regiones.json`.
  - Madrid compacta lleva cuatro distritos. Desde la 3.2.0 el 6X va con la variante c (Madrid entero) y la
    `compacta` de Madrid se retira de `tools/regiones.json`.
  - 128 de 250 recursos; fuerza bruta con 0 discrepancias; 37/37 tests en el 6X (los 14 de Santiago ya no
    van).
  - En el simulador, en la tesela más pesada (t85): 148 de 1.275 KB,
    con un pico de 221 KB.

## 7. v3.1: anillo de brújula e «Ir a una anotación» (2026-10-24)

Referencia de diseño: Pin Point — Location and Share (Connect IQ Store). De ella se toma solo la interfaz:
Pin Point saca la calle por geocodificación en línea a través del teléfono, y CALLE sigue sin red.

- **Anillo** (`source/Anillo.mc`), en la franja exterior de la guía (`VistaIr`):
  - círculo fino de radio `L.ANILLO_R` (133 px) en el tono oscuro del destino (`Ir.colorOscuro`);
  - marcas cada 10°, más largas y claras cada 30°;
  - triángulos hacia dentro en los cardinales: el norte, **rojo** y mayor; el este, el sur y el oeste, grises;
  - el destino, como una bola de su color con borde blanco, en su rumbo relativo. No aparece sin posición ni
    tras «HA LLEGADO».
  - Gira con `Ir.orientacion()` (la brújula, por `Activity`, sin el permiso `Sensor`), al mismo ritmo de 500 ms
    que la flecha. Sin brújula queda con el norte arriba, y el pie dice «norte arriba · SE».
- **Recolocación:** todo el texto de la guía va dentro de `L.ANILLO_RI` (128 px), con `Texto.anchoR`.
  - Hora en y = 30, rótulo en 52, nombre centrado en 86, flecha en 154, distancia en 200, dirección en 226 y pie
    en 245.
  - El pie se acorta antes de perder el cardinal: «línea recta · NO» → «recta · NO» → «NO». En los dos relojes
    cabe entero: 100 de 108 px (log `ANILLO` de `vistaIrPinta`).
- **Ir a una anotación:**
  - En «Anotaciones», al elegir una con posición se abre un menú con «Ir aquí» (flecha y distancia) y «Borrar»
    (pide confirmación). Sin posición, se pregunta directamente si se borra, como antes.
  - «Ir aquí» abre la guía con todas las anotaciones con posición (`Ir.deNotas`) en el orden del menú, la más
    nueva primero, y empieza por la elegida. ARRIBA y ABAJO pasan de una a otra.
  - Va en verde, con el rótulo «ANOTACIÓN · 21:15» y la UTM en lugar de la dirección.
  - «Borrar» quita su menú antes de preguntar, para volver después a la lista.
- **Pruebas:** 53/53 en el 7X Pro y 39/39 en el 6X.
  - Nuevas: `anilloPinta` (giros, destinos y tipos), `irDeNotas` y `vistaIrPinta` con anotaciones.
  - El recorrido por los menús no se puede automatizar en el simulador: queda para la muñeca.
- **Maquetas:** `tools/mockup.py --brujula` → `tools/out/mockups-brujula.png`. Las imágenes de la ficha de la
  tienda ya muestran la guía con el anillo.
