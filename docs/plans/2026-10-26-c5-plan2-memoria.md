# C5 · Plan 2: la memoria en el fēnix 5 (por partes, nombres desde B y modo app)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** fijar con medidas, no con estimaciones, cuánto ocupa una tesela del FORMATO 5 ya cargada y qué zona cabe con ella en memoria con el tope real de 128 KB. Hay que bajar lo que sobra (los nombres van dos veces) antes de fijar los topes de tesela y de zona que usará el generador (especificación `docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md`, «Pendiente para el plan 2»).

**Por qué va antes que el generador:** la puerta midió 40.192 B para la tesela t412 ya cargada, frente a ~30.400 B en el FORMATO 4. Con ~61 KB libres en la app real, eso deja ~21 KB para el pico de la zona (2,2 veces su tamaño): zonas de ~10 KB. Las zonas de 10 km de Galicia en la variante normal tienen una mediana de **13,8 KB** (272 de 374 pasan de 10 KB). Si el tope sale así de bajo, el diseño de zonas de 20 km en dos niveles no vale y hay que elegir otra salida **antes** de escribir el generador.

**Architecture:**
- **Medición por partes** (test nuevo en `puerta/`): el `ByteArray`, la cadena `S`, las tablas `mejor`/`mejorRun` vacías y llenas, el objeto `Tesela` y lo que añade una búsqueda.
- **Nombres desde B:** en el FORMATO 5, `O` pasa a dar dónde empieza cada nombre **en bytes** de S. La tesela ya no guarda `S` como `String`: `nombre(k)` lo decodifica de `B` cuando se pide, e `indiceDe` busca por bisección comparando bytes. Las calles van en orden de bytes UTF-8, que es el de `sorted()` del generador.
- **Modo app:** la misma `puerta/` se compila como app, sin tests (`puerta/app.jungle`). Rellena memoria con lastre hasta lo que usa la app real al cargar una tesela. Después carga la tesela más pesada, busca y carga, de menor a mayor, zonas reales de Galicia de 6 a 20 KB con la tesela en memoria. La última zona que carga marca el tope.

**Tech Stack:** Python 3 (biblioteca estándar), Monkey C (SDK 9.3, `fenix5`, API 3.1), `monkeyc`/`monkeydo`, `StringUtil.convertEncodedString`, `String.toUtf8Array`, anotaciones con `excludeAnnotations` en el jungle.

**Después de este plan (aparte, cada uno con su plan):**
- **Plan 3, generador y referencia** (solo Python, en el Mac):
  - variante `c5` en `build_callejero.py`: zona urbana por INE, rural sin cortes y encadenado con DP a 8 m, sin sendas fuera, unidad por tesela (1 m / 4 m), zonas con el tope que salga de aquí y reparto entre `Strings` y `JsonData`;
  - `ref.py` con FORMATO 5;
  - fuerza bruta sobre 40.000 puntos y los puntos de control.
- **Plan 4, integración y campo:**
  - `Resultado` y `Estado` fuera de `source/Buscador.mc`, y `rellenar`/`consultar` en `source-c5`;
  - anotaciones `(:f4)`/`(:c5)`, el lector de zonas `c5`, `monkey.jungle`, `ciq.sh` y `tools/tienda.py`;
  - el `.prg` por cable al fēnix 5.

  `tienda.py` y `catalogo.json` van encima de `main` cuando la coordinadora fusione la beta por app de Murcia (`88dd96d`; acordado con ella el 2026-10-26).

**Convivencia (obligatoria):** en `~/code/calle-fenix` trabajan otras sesiones, y otra sesión (la coordinadora de Murcia y Valencia) fusiona las ramas.
- Todo este plan se hace en el worktree `~/code/calle-c5` (rama `c5-galicia`). Los commits, siempre con `git add <ruta>` explícita, nunca `-a` ni `.`.
- Este plan **no toca** `tools/build_callejero.py`, `tools/tienda.py`, `tools/catalogo.json`, `ciq.sh` ni nada de `source/`.
- Simulador: candado `/tmp/calles-sim.lock`. Se coge con `until mkdir /tmp/calles-sim.lock 2>/dev/null; do sleep 20; done; echo "calle-c5 $$ $(date +%H:%M)" > /tmp/calles-sim.lock/quien` y se suelta con `mv /tmp/calles-sim.lock /tmp/calles-sim.lock-liberado-$(date +%s)`, también si algo falla. `rm` lo bloquea un hook.
- Los datos generados (`resources-gen/`, `tools/out/`) no están en git: se leen del árbol principal, `~/code/calle-fenix`.

---

## Mapa de ficheros

| Fichero | Qué cambia |
|---|---|
| `puerta/source/PuertaTest.mc` | test nuevo `puertaPartes` (Task 1) y `puertaIndiceDe` (Task 3); `puertaMemoria` deja de leer `t.S`; el módulo `Puerta` sale a su fichero (Task 4) |
| `puerta/source/Puerta.mc` (nuevo, Task 4) | el módulo `Puerta` (tesela, libre, cadena), que usan los tests y el modo app |
| `tools/formato5.py` | `O` en bytes de S; `decodificar` devuelve el `O` del FORMATO 4 (en caracteres) |
| `tools/test_formato5.py` | cada nombre se lee de los bytes con el `O` nuevo, y las calles van en orden de bytes |
| `source-c5/Tesela.mc` | sin `S`: `oS`, `nombre(k)` desde `B`, `indiceDe` por bisección de bytes, `comparar` |
| `tools/puerta_c5.py` | escalera de zonas reales (`zonas_escalera`) → `puerta/resources-gen/zonas.xml` + `zona*.json`, y `PuertaDatos.ZONAS_EST` / `PuertaDatos.zonas()` |
| `puerta/source/PuertaApp.mc` | la vista inicial sale de `vistaInicial()`: una por modo |
| `puerta/source/ModoApp.mc` (nuevo) | `vistaInicial()` de cada modo, `VistaPuerta` y `Escenario` (`:modoapp`) |
| `puerta/monkey.jungle` | `base.excludeAnnotations = modoapp` |
| `puerta/app.jungle` (nuevo) | la puerta como app: `base.excludeAnnotations = modotest` |
| `docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md` | resultado de la memoria, topes y, si hace falta, las salidas para que decida el autor |

## Comandos que se repiten

**Generar la puerta** (lee los datos del árbol principal):
```bash
cd ~/code/calle-c5 && python3 -I tools/puerta_c5.py ~/code/calle-fenix/resources-gen/galicia ~/code/calle-fenix/tools/out/meta-galicia.json
```

**Compilar los tests de la puerta:**
```bash
cd ~/code/calle-c5 && export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH" && SDK="$(tr -d '\n' < "$HOME/Library/Application Support/Garmin/ConnectIQ/current-sdk.cfg")" && mkdir -p bin && "$SDK/bin/monkeyc" -d fenix5 -f puerta/monkey.jungle -y ~/.garmin/developer_key.der -o bin/puerta.prg -t -w 2>&1 | tail -5
```

**Ejecutar los tests en el simulador** (con el candado):
```bash
cd ~/code/calle-c5 && until mkdir /tmp/calles-sim.lock 2>/dev/null; do sleep 20; done; echo "calle-c5 $$ $(date +%H:%M)" > /tmp/calles-sim.lock/quien
export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"; SDK="$(tr -d '\n' < "$HOME/Library/Application Support/Garmin/ConnectIQ/current-sdk.cfg")"
pgrep -x simulator >/dev/null || { open "$SDK/bin/ConnectIQ.app"; sleep 5; }
"$SDK/bin/monkeydo" bin/puerta.prg fenix5 -t 2>&1 | tee bin/puerta.log | grep -E "PUERTA|PARTES|ERROR|PASS|FAIL|Watchdog|Tripped"
mv /tmp/calles-sim.lock /tmp/calles-sim.lock-liberado-$(date +%s)
```

---

### Task 0: Punto de partida

**Files:** ninguno.

- [ ] **Step 1: Rama y árbol limpios**

```bash
cd ~/code/calle-c5 && git status -sb && git log --oneline -1
```
Esperado: `## c5-galicia`, sin cambios, y el último commit es el de este plan (o `eae2ccb` si el plan aún no está en commit).

- [ ] **Step 2: Datos de Galicia en el árbol principal**

```bash
ls ~/code/calle-fenix/resources-gen/galicia/t | wc -l; ls ~/code/calle-fenix/resources-gen/galicia/z | wc -l; python3 -c "import json;print(json.load(open('$HOME/code/calle-fenix/tools/out/meta-galicia.json'))['t_mayor'])"
```
Esperado: ~1.700 teselas, 374 zonas y `t412`. Si falta algo, se para y se avisa: no se regenera Galicia desde aquí (52 min y otro árbol).

---

### Task 1: Medición por partes (con el lector de la puerta tal cual)

**Files:**
- Modify: `puerta/source/PuertaTest.mc` (añadir al final)

Se mide **antes** de cambiar nada, para saber qué pesa cada parte con el lector que pasó la puerta.

- [ ] **Step 1: Añadir el test `puertaPartes`**

Al final de `puerta/source/PuertaTest.mc`:

```monkeyc
// Plan 2: de qué se compone la tesela ya cargada (la puerta midió 40.192 B y se esperaban ~32.500). Mide, paso a
// paso, lo mismo que hace Tesela.initialize, y luego la tesela de verdad y una búsqueda. Solo mide: no falla.
(:test)
function puertaPartes(logger as Test.Logger) as Boolean {
    var l0 = Puerta.libre();
    var b = Teselas.bytes(Rez.JsonData.TeselaPuerta);
    var l1 = Puerta.libre();
    var ls = Teselas.palabra(b, 8);
    var nc = Teselas.palabra(b, 4);
    var p = 4 * Teselas.CABECERA;
    var trozo = b.slice(p, p + ls);
    var l2 = Puerta.libre();
    var S = StringUtil.convertEncodedString(trozo, {
        :fromRepresentation => StringUtil.REPRESENTATION_BYTE_ARRAY,
        :toRepresentation => StringUtil.REPRESENTATION_STRING_PLAIN_TEXT
    }) as String;
    var l3 = Puerta.libre();
    trozo = null;
    var l4 = Puerta.libre();
    var m1 = new Array<Float>[nc];
    var m2 = new Array<Number>[nc];
    var l5 = Puerta.libre();
    for (var i = 0; i < nc; i++) {
        m1[i] = Buscador.LEJOS;
        m2[i] = -1;
    }
    var l6 = Puerta.libre();
    logger.debug("PARTES ByteArray " + (l0 - l1) + " B; trozo de S " + (l3 - l4) + " B; S " + (l2 - l3) + " B ("
        + S.length() + " letras, " + ls + " bytes); mejor+mejorRun vacías " + (l4 - l5) + " B, llenas " + (l4 - l6)
        + " B (" + nc + " calles)");
    S = null;
    m1 = null;
    m2 = null;
    var l7 = Puerta.libre();
    var t = new Tesela(0, b, PuertaDatos.CAJA);
    b = null;
    var l8 = Puerta.libre();
    Buscador.buscar(t, PuertaDatos.CENTRO[0], PuertaDatos.CENTRO[1]);
    var l9 = Puerta.libre();
    logger.debug("PARTES Tesela sobre el ByteArray " + (l7 - l8) + " B (S + tablas + objeto); tras buscar +"
        + (l8 - l9) + " B; total desde el principio " + (l0 - l9) + " B");
    return true;
}
```

- [ ] **Step 2: Generar la puerta y compilar**

Los dos comandos de «Comandos que se repiten»: generar y compilar. Esperado: compila sin errores (los avisos de `-w` no cuentan).

- [ ] **Step 3: Ejecutar en el simulador**

El comando de ejecución, con el candado. Esperado: las 4 pruebas de la puerta siguen en PASS, y salen dos líneas `PARTES`, más `puertaPartes` en PASS.

- [ ] **Step 4: Anotar las cifras**

```bash
cd ~/code/calle-c5 && grep -E "PARTES|PUERTA memoria" bin/puerta.log > bin/partes-antes.txt && cat bin/partes-antes.txt
```
Se guardan para la Task 5. Lo que importa:
- cuánto pesa `S`, comparado con sus bytes;
- cuánto pesan `mejor` y `mejorRun`, vacías y llenas (si llenas pesan más que vacías, los `Float` ocupan memoria aparte);
- si «Tesela sobre el ByteArray» ≈ S + tablas, o queda un resto. Ese resto son los ~7,6 KB sin explicar.

- [ ] **Step 5: Commit**

```bash
cd ~/code/calle-c5 && git add puerta/source/PuertaTest.mc && git commit -m "Puerta c5: medición por partes de la tesela cargada (plan 2)"
```

---

### Task 2: FORMATO 5 con `O` en bytes de S (Python)

**Files:**
- Modify: `tools/test_formato5.py`
- Modify: `tools/formato5.py`

En el FORMATO 4, `O` cuenta en **caracteres** (para `String.substring`). Para leer un nombre directamente de `B`, el FORMATO 5 lo necesita en **bytes** UTF-8. En Galicia no coinciden en cuanto un nombre lleva tilde («Rúa…»). `decodificar` devuelve el `O` del FORMATO 4, así que la ida y vuelta sigue dando la misma lista.

- [ ] **Step 1: El test que falla**

En `tools/test_formato5.py`, añadir `import struct` junto a los otros imports:

```python
import json
import struct
import sys
from pathlib import Path
```

y, dentro del bucle de `main()`, justo después de `assert K[nc] == acum, f"{f.name}: K final"`, añadir:

```python
        # O del FORMATO 5: dónde empieza cada nombre en BYTES de S (el reloj los lee de B sin pasar S a String),
        # y las calles en orden de bytes UTF-8 (Tesela.indiceDe busca por bisección comparando bytes).
        cab = struct.unpack_from(f"<{F5.CABECERA}I", b, 0)
        ls = cab[2]
        p = 4 * F5.CABECERA
        sb = b[p:p + ls]
        O5 = struct.unpack_from(f"<{cab[3]}I", b, p + ls + (-ls % 4))
        ini = [(O5[j // 2] >> (16 * (j % 2))) & 0xFFFF for j in range(2 * len(O5))]
        nombres = t[3][1:].split("\n")[:-1]
        for k, nom in enumerate(nombres):
            assert sb[ini[k]:ini[k + 1] - 1].decode("utf-8") == nom, f"{f.name}: nombre {k} ({nom}) mal en bytes"
        calles = [nom.encode("utf-8") for nom in nombres[:nc]]
        assert calles == sorted(calles) and len(set(calles)) == nc, f"{f.name}: calles fuera del orden de bytes"
```

- [ ] **Step 2: Ver que falla**

```bash
cd ~/code/calle-c5 && python3 -I tools/test_formato5.py ~/code/calle-fenix/resources-gen/galicia/t
```
Esperado: `AssertionError: t…: nombre … mal en bytes` en la primera tesela con una tilde antes del último nombre.

- [ ] **Step 3: `O` en bytes en `tools/formato5.py`**

Sustituir el docstring del módulo por:

```python
"""FORMATO 5: una tesela del FORMATO 4 (la lista de build_callejero.empaquetar) en bytes, para los relojes de
128 KB (variante c5). Especificación: docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md.

Palabras de 32 bits little-endian (los 4 bytes de cada CB quedan sueltos: x0, y0, x1, y1):
  cabecera (CABECERA palabras): FORMATO | U << 8 | PB << 16, NC, bytes de S, y cuántas palabras tienen
  O, C, CB, K, R, V, P y E; luego S (UTF-8, rellenada a múltiplo de 4) y esas tablas, en ese orden.
U: metros por unidad de las coordenadas de la tesela (1 en ciudad, 4 en el rural; el contenido ya viene en
esas unidades). K (nuevo): por calle, y una más al final, el bit de V donde empiezan los vértices de su
primera tirada: la búsqueda salta una calle lejana sin recorrer sus tiradas.
O: como en el FORMATO 4 (2 por número, 16 bits), pero en BYTES de S y no en caracteres: el reloj lee cada
nombre de los bytes cuando lo necesita, sin guardar S como String (plan 2). Las calles van en orden de bytes
UTF-8, que es el de sorted() en build_callejero.empaquetar: Tesela.indiceDe busca por bisección.
"""
```

Añadir, después de `_palabras`:

```python
def _int32(v):
    return v - (1 << 32) if v >= 1 << 31 else v


def inicios(S, en_bytes):
    """O de S ("\\n" + cada nombre + "\\n"): dónde empieza cada nombre y uno final, 2 por número. En caracteres
    (FORMATO 4, el de build_callejero.cadena_nombres) o en bytes UTF-8 (FORMATO 5)."""
    offs, pos = [], 1
    for e in S[1:].split("\n")[:-1]:
        offs.append(pos)
        pos += (len(e.encode("utf-8")) if en_bytes else len(e)) + 1
    offs.append(pos)
    assert pos < 1 << 16, pos
    if len(offs) % 2:
        offs.append(0)
    return [_int32(offs[j] | offs[j + 1] << 16) for j in range(0, len(offs), 2)]
```

En `codificar`, cambiar la línea de `tablas`:

```python
    assert O == inicios(S, False), "O no corresponde a S"
    tablas = [inicios(S, True), C, CB, indice_k(nc, C, R), R, V, P, E]
```

En `decodificar`, cambiar las dos últimas líneas:

```python
    O5, C, CB, K, R, V, P, E = tablas
    assert O5 == inicios(S, True), "O del FORMATO 5 no corresponde a S"
    return [4, nc, pb, S, inicios(S, False), C, CB, R, V, P, E], u, K
```

- [ ] **Step 4: Ver que pasa**

```bash
cd ~/code/calle-c5 && python3 -I tools/test_formato5.py ~/code/calle-fenix/resources-gen/galicia/t
```
Esperado: `FORMATO 5: … teselas ida y vuelta OK; la mayor, t412, 24632 bytes` (el tamaño no cambia: `O` tiene las mismas palabras).

- [ ] **Step 5: La puerta se sigue generando**

```bash
cd ~/code/calle-c5 && python3 -I tools/puerta_c5.py ~/code/calle-fenix/resources-gen/galicia ~/code/calle-fenix/tools/out/meta-galicia.json
```
Esperado: `puerta: t412, 24632 bytes (32844 en base64), 262 calles, 40 puntos, …`. **No se compila ni se ejecuta todavía:** el lector de `source-c5/Tesela.mc` aún usa `O` en caracteres, y lo cambia la Task 3.

- [ ] **Step 6: Commit**

```bash
cd ~/code/calle-c5 && git add tools/formato5.py tools/test_formato5.py && git commit -m "FORMATO 5: O en bytes de S, para leer los nombres de B sin guardar S como String"
```

---

### Task 3: La tesela sin `S` (nombres desde B)

**Files:**
- Modify: `source-c5/Tesela.mc`
- Modify: `puerta/source/PuertaTest.mc` (`puertaMemoria` y el test nuevo `puertaIndiceDe`)

- [ ] **Step 1: El test que falla**

En `puerta/source/PuertaTest.mc`, en `puertaMemoria`, cambiar la línea del `logger.debug` (ya no hay `t.S`):

```monkeyc
    logger.debug("PUERTA memoria: base64 " + (l0 - l1) + " B, ByteArray " + (l1 - l2) + " B, pico " + pico
        + " B; tesela lista " + (l0 - l3) + " B (" + t.nc + " calles)");
```

Y añadir al final del fichero:

```monkeyc
// Plan 2: sin S en memoria, indiceDe busca por bisección comparando bytes. Cada calle muestreada se encuentra en su
// sitio; un nombre que no está (o vacío) da -1. Muestreo de ~40 calles más la última, para no rozar el watchdog.
(:test)
function puertaIndiceDe(logger as Test.Logger) as Boolean {
    var t = Puerta.tesela();
    var paso = t.nc / 40 + 1;
    var ok = true;
    for (var k = 0; k < t.nc; k += paso) {
        var n = t.nombre(k);
        var i = t.indiceDe(n);
        if (i != k) {
            logger.error("indiceDe(" + n + ") = " + i + ", esperaba " + k);
            ok = false;
        }
    }
    var ultima = t.nombre(t.nc - 1);
    if (t.indiceDe(ultima) != t.nc - 1) {
        logger.error("indiceDe(" + ultima + ") no da la última");
        ok = false;
    }
    if (t.indiceDe("Rúa que non existe") != -1 || t.indiceDe("") != -1) {
        logger.error("indiceDe encuentra un nombre que no está");
        ok = false;
    }
    return ok;
}
```

- [ ] **Step 2: Compilar y ver que falla**

Primero se genera la puerta con el `formato5.py` de la Task 2; luego se compila y se ejecuta (los tres comandos de «Comandos que se repiten»). Compila, porque `nombre` e `indiceDe` ya existen. El fallo se ve al ejecutar: `puertaVectores` en FAIL, porque `O` ya va en bytes y `S.substring` cuenta caracteres, así que los nombres que van detrás de una tilde salen corridos. `puertaIndiceDe` también falla, por lo mismo.

- [ ] **Step 3: `source-c5/Tesela.mc` sin `S`**

En la clase `Tesela`:

1. Sustituir la declaración `var S as String;` por:

```monkeyc
    var oS as Number;   // dónde empieza S en B: "\n" + cada nombre + "\n", en UTF-8 (O cuenta en bytes)
```

2. En `initialize`, sustituir el bloque que va desde `var p = 4 * Teselas.CABECERA;` hasta `p += (ls + 3) & ~3;` (ambos incluidos) por:

```monkeyc
        var p = 4 * Teselas.CABECERA;
        oS = p;
        p += (ls + 3) & ~3;
```

3. Sustituir la función `nombre` por:

```monkeyc
    // El nombre k: una calle (k < nc) o un sufijo de portal. Se decodifica de B cada vez: guardar S como String
    // costaba ~5,3 KB más en reposo (plan 2), y se piden pocos nombres por búsqueda.
    function nombre(k as Number) as String {
        return StringUtil.convertEncodedString(B.slice(oS + inicio(k), oS + inicio(k + 1) - 1), {
            :fromRepresentation => StringUtil.REPRESENTATION_BYTE_ARRAY,
            :toRepresentation => StringUtil.REPRESENTATION_STRING_PLAIN_TEXT
        }) as String;
    }
```

4. Sustituir la función `indiceDe` por estas dos:

```monkeyc
    // Índice de la calle con ese nombre, o -1. Las calles van en orden de bytes UTF-8 (el de sorted() del generador,
    // tools/formato5.py): bisección comparando bytes, sin pasar S a String.
    function indiceDe(n as String) as Number {
        var q = n.toUtf8Array();
        var lo = 0;
        var hi = nc - 1;
        while (lo <= hi) {
            var mid = (lo + hi) / 2;
            var c = comparar(q, mid);
            if (c == 0) {
                return mid;
            } else if (c > 0) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        return -1;
    }

    // Negativo, 0 o positivo: el nombre q (sus bytes UTF-8) frente al nombre k de la tesela, byte a byte.
    function comparar(q as Array<Number>, k as Number) as Number {
        var a = oS + inicio(k);
        var fin = oS + inicio(k + 1) - 1;
        var n = q.size();
        for (var i = 0; i < n; i++) {
            if (a + i >= fin) {
                return 1;       // el de la tesela es un prefijo de q: q va después
            }
            var d = q[i] - B[a + i];
            if (d != 0) {
                return d;
            }
        }
        return a + n < fin ? -1 : 0;
    }
```

`import Toybox.StringUtil;` ya está al principio del fichero, y `Teselas.bytes` lo sigue usando.

- [ ] **Step 4: Comprobar que nadie más lee `t.S`**

```bash
cd ~/code/calle-c5 && grep -n "\.S\b" source-c5/*.mc puerta/source/*.mc
```
Esperado: sin resultados. (`source/` es el FORMATO 4 y no se toca.)

- [ ] **Step 5: Generar, compilar y ejecutar**

Los tres comandos de «Comandos que se repiten». Esperado: las 6 pruebas en PASS (`puertaVectores` 40/40, `puertaMemoria`, `puertaWatchdog1`, `puertaWatchdog2`, `puertaPartes` y `puertaIndiceDe`). La línea `PUERTA memoria` debe dar una «tesela lista» **más baja** que los 40.192 B de la puerta. Lo esperado es ~5 KB menos.

Si `puertaWatchdog2` pasa a FAIL o sale `Watchdog Tripped`, se para: el lector nuevo no puede costar más que el viejo en la búsqueda (solo cambia `nombre` e `indiceDe`).

- [ ] **Step 6: Anotar las cifras**

```bash
cd ~/code/calle-c5 && grep -E "PARTES|PUERTA" bin/puerta.log > bin/partes-despues.txt && cat bin/partes-despues.txt
```

- [ ] **Step 7: Commit**

```bash
cd ~/code/calle-c5 && git add source-c5/Tesela.mc puerta/source/PuertaTest.mc && git commit -m "Tesela c5: los nombres se leen de B (sin S en memoria) e indiceDe por bisección de bytes"
```

---

### Task 4: Modo app: tesela y zona con el tope real de 128 KB

**Files:**
- Create: `puerta/source/Puerta.mc`
- Modify: `puerta/source/PuertaTest.mc` (quitar el módulo `Puerta`)
- Create: `puerta/source/ModoApp.mc`
- Modify: `puerta/source/PuertaApp.mc`
- Modify: `puerta/monkey.jungle`
- Create: `puerta/app.jungle`
- Modify: `tools/puerta_c5.py`

**Qué se mide y por qué así:**
- En los tests, el simulador da más memoria que a una app. Las diferencias valen, pero el límite no.
- Aquí la puerta corre como app. Primero rellena con un `ByteArray` de lastre hasta lo que usa la app real al cargar una tesela: **65 KB**, medidos en el fēnix 6 con Madrid (especificación del FORMATO 4, «Memoria»), **más 1 KB** por los índices más largos de Galicia (~300 teselas y ~160 zonas; es una estimación).
- Luego carga la tesela más pesada, busca y carga zonas reales de Galicia de menor a mayor, con la tesela en memoria. La primera que no cabe tumba la app con *Out Of Memory*. La última que cargó es el tope medido.

- [ ] **Step 1: El módulo `Puerta`, a su fichero**

Crear `puerta/source/Puerta.mc` con el módulo `Puerta` **tal cual** está hoy en `puerta/source/PuertaTest.mc` (las funciones `tesela`, `libre` y `cadena`, con su comentario de cabecera), y sus imports:

```monkeyc
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;
```

y borrar ese bloque `module Puerta { … }` de `PuertaTest.mc`. Motivo: el modo app lo usa y no debe arrastrar un fichero de tests.

- [ ] **Step 2: La escalera de zonas en `tools/puerta_c5.py`**

Añadir `import shutil` a los imports, y después de `centro_denso`:

```python
ESCALERA_KB = (6, 8, 10, 12, 14, 16, 18, 20)


def zonas_escalera(rdir):
    """[(heap estimado, fichero)]: la zona real (FORMATO 4) más cercana a cada peso de ESCALERA_KB, con el heap
    estimado de build_callejero.empaquetar_zona. El modo app las carga de menor a mayor con la tesela en memoria."""
    hs = []
    for f in sorted((rdir / "z").glob("z*.json")):
        z = json.loads(f.read_text("utf-8"))
        nums = sum(len(x) if isinstance(x, list) else 1 for x in z[2:])
        hs.append((int(5 * (nums + 7) + len(z[1].encode()) + 20), f))
    out = []
    for kb in ESCALERA_KB:
        h, f = min(hs, key=lambda e: abs(e[0] - kb * 1024))
        if not out or out[-1][0] != h:
            out.append((h, f))
    return out
```

En `main()`, después de escribir `tesela.xml`, añadir:

```python
    zs = zonas_escalera(rdir)
    for k, (_h, f) in enumerate(zs):
        shutil.copyfile(f, PUERTA / "resources-gen" / f"zona{k}.json")
    (PUERTA / "resources-gen" / "zonas.xml").write_text(
        "<resources>\n" + "".join(f'    <jsonData id="ZonaPrueba{k}" filename="zona{k}.json"/>\n'
                                  for k in range(len(zs))) + "</resources>\n", "utf-8")
```

En la plantilla de `PuertaDatos.mc` (la f-string que escribe `puerta/source-gen/PuertaDatos.mc`), sustituir sus dos últimas líneas, `    ] as Array<Array>;` y `}}`, por:

```python
    ] as Array<Array>;
    // Escalera del modo app: zonas reales de {meta['region']} ({', '.join(f.stem for _h, f in zs)}), heap estimado.
    const ZONAS_EST = [{', '.join(str(h) for h, _f in zs)}] as Array<Number>;

    function zonas() as Array<ResourceId> {{
        return [{', '.join(f'Rez.JsonData.ZonaPrueba{k}' for k in range(len(zs)))}] as Array<ResourceId>;
    }}
}}
```

Y en el `print` final, añadir las zonas:

```python
    print(f"puerta: {nombre}, {len(b5)} bytes ({len(base64.b64encode(b5))} en base64), {t[1]} calles, "
          f"{len(ps)} puntos, centro denso con {n_cb} calles; zonas {[h for h, _f in zs]}")
```

- [ ] **Step 3: Generar y comprobar**

```bash
cd ~/code/calle-c5 && python3 -I tools/puerta_c5.py ~/code/calle-fenix/resources-gen/galicia ~/code/calle-fenix/tools/out/meta-galicia.json && cat puerta/resources-gen/zonas.xml && grep -A4 "ZONAS_EST" puerta/source-gen/PuertaDatos.mc
```
Esperado: 8 zonas (o menos si dos pesos caen en la misma), de ~6.100 a ~20.500 B, y `zonas()` con sus `Rez.JsonData.ZonaPrueba*`.

- [ ] **Step 4: Una vista por modo**

`puerta/source/PuertaApp.mc`, sustituir `getInitialView`:

```monkeyc
    function getInitialView() as [WatchUi.Views] or [WatchUi.Views, WatchUi.InputDelegates] {
        return [vistaInicial()];
    }
```

Crear `puerta/source/ModoApp.mc`:

```monkeyc
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;

// La puerta tiene dos modos (plan 2): tests (puerta/monkey.jungle, sin :modoapp) y app (puerta/app.jungle, sin
// :modotest). En modo app mide la memoria con el tope real de una watch-app del fēnix 5.

(:modotest)
function vistaInicial() as WatchUi.Views {
    return new WatchUi.View();
}

(:modoapp)
function vistaInicial() as WatchUi.Views {
    return new VistaPuerta();
}

(:modoapp)
class VistaPuerta extends WatchUi.View {
    var hecho as Boolean = false;

    function initialize() {
        View.initialize();
    }

    function onShow() as Void {
        if (!hecho) {
            hecho = true;
            Escenario.correr();
        }
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
        dc.clear();
    }
}

(:modoapp)
module Escenario {
    // Lo que usa la app real al cargar una tesela: 65 KB medidos en el fēnix 6 con Madrid (especificación del
    // FORMATO 4, «Memoria»), más 1 KB por los índices más largos de Galicia (estimación).
    const USADA_APP = 66 * 1024;

    function correr() as Void {
        var st = System.getSystemStats();
        System.println("APP total " + st.totalMemory + " B, usada " + st.usedMemory + " B al arrancar");
        var falta = USADA_APP - st.usedMemory;
        var lastre = falta > 0 ? new [falta]b : null;
        var l0 = Puerta.libre();
        System.println("APP lastre " + falta + " B; libre " + l0 + " B (la app real: ~61 KB)");
        var t = Puerta.tesela();
        var l1 = Puerta.libre();
        Buscador.buscar(t, PuertaDatos.CENTRO[0], PuertaDatos.CENTRO[1]);
        var l2 = Puerta.libre();
        System.println("APP tesela " + PuertaDatos.ETIQUETA + ": en reposo " + (l0 - l1) + " B, tras buscar "
            + (l0 - l2) + " B; libre " + l2 + " B");
        var zs = PuertaDatos.zonas();
        for (var i = 0; i < zs.size(); i++) {
            System.println("APP zona " + PuertaDatos.ZONAS_EST[i] + " B: cargando");
            var z = WatchUi.loadResource(zs[i]);
            var l3 = Puerta.libre();
            System.println("APP zona " + PuertaDatos.ZONAS_EST[i] + " B: OK, en reposo " + (l2 - l3) + " B, libre "
                + l3 + " B");
            z = null;
        }
        System.println("APP FIN (lastre " + (lastre != null ? lastre.size() : 0) + " B, tesela " + t.nc + " calles)");
        System.exit();
    }
}
```

- [ ] **Step 5: Los dos jungles**

`puerta/monkey.jungle`, añadir al final:

```
base.excludeAnnotations = modoapp
```

Crear `puerta/app.jungle`:

```
# Puerta del plan c5 en modo app (plan 2): mide la memoria con el tope real de una watch-app del fēnix 5.
# Los tests, en monkey.jungle.
project.manifest = manifest.xml
base.sourcePath = source;source-gen;../source-c5
base.resourcePath = ../resources;resources-gen
base.excludeAnnotations = modotest
```

- [ ] **Step 6: Los tests siguen igual**

Compilar y ejecutar los tests (comandos de «Comandos que se repiten»). Esperado: las 6 pruebas en PASS. Las zonas no las usa ningún test, pero sus recursos se compilan.

- [ ] **Step 7: Compilar el modo app**

```bash
cd ~/code/calle-c5 && export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH" && SDK="$(tr -d '\n' < "$HOME/Library/Application Support/Garmin/ConnectIQ/current-sdk.cfg")" && "$SDK/bin/monkeyc" -d fenix5 -f puerta/app.jungle -y ~/.garmin/developer_key.der -o bin/puerta-app.prg -r -O 2 -w 2>&1 | tail -5
```
Esperado: compila. Sin `-t` se quitan las funciones `(:test)`, pero `PuertaTest.mc` sigue importando `Toybox.Test`. Si el compilador se queja de eso, se mueve `PuertaTest.mc` a `puerta/test/PuertaTest.mc` y `monkey.jungle` pasa a `base.sourcePath = source;test;source-gen;../source-c5`. `app.jungle` no lleva `test`.

- [ ] **Step 8: Ejecutar el modo app**

```bash
cd ~/code/calle-c5 && until mkdir /tmp/calles-sim.lock 2>/dev/null; do sleep 20; done; echo "calle-c5 $$ $(date +%H:%M)" > /tmp/calles-sim.lock/quien
export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"; SDK="$(tr -d '\n' < "$HOME/Library/Application Support/Garmin/ConnectIQ/current-sdk.cfg")"
pgrep -x simulator >/dev/null || { open "$SDK/bin/ConnectIQ.app"; sleep 5; }
"$SDK/bin/monkeydo" bin/puerta-app.prg fenix5 > bin/puerta-app.log 2>&1 & md=$!
for i in $(seq 1 45); do grep -qE "APP FIN|Error|ERROR|Memory" bin/puerta-app.log && break; sleep 2; done
kill $md 2>/dev/null; mv /tmp/calles-sim.lock /tmp/calles-sim.lock-liberado-$(date +%s)
cat bin/puerta-app.log
```
Esperado:
- `APP total` entre 120.000 y 132.000 B. Si no, el simulador no está dando el tope de una watch-app: se para y se avisa, porque la medida no vale.
- `APP tesela … en reposo` parecida a la «tesela lista» de la Task 3.
- Varias líneas `APP zona … OK` y después:
  - o `APP FIN`: todas caben, y el tope es la mayor;
  - o un `cargando` seguido de un error de memoria (*Out Of Memory* / `Error`): esa zona **no** cabe.

Si el log sale vacío (monkeydo no pasó el `println`), se para y se avisa. No se dan cifras sin log.

- [ ] **Step 9: Repetir para descartar ruido**

Se repite el Step 8 una vez más y se comprueba que el corte cae en la misma zona. Si no coincide, se anotan las dos y vale la más baja.

- [ ] **Step 10: Commit**

```bash
cd ~/code/calle-c5 && git add puerta/source/Puerta.mc puerta/source/PuertaTest.mc puerta/source/ModoApp.mc puerta/source/PuertaApp.mc puerta/monkey.jungle puerta/app.jungle tools/puerta_c5.py && git commit -m "Puerta c5 en modo app: tesela y escalera de zonas reales con el tope de 128 KB (plan 2)"
```
(Si en el Step 7 hubo que mover `PuertaTest.mc` a `puerta/test/`, se añade esa ruta en lugar de `puerta/source/PuertaTest.mc`.)

---

### Task 5: Topes y decisión

**Files:**
- Modify: `docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md` (sección nueva al final)

- [ ] **Step 1: Calcular los topes**

Con `bin/partes-antes.txt`, `bin/partes-despues.txt` y `bin/puerta-app.log`:
- **Tope de la tesela:** si t412 (24.632 B) cargó con el lastre, se confirman los **24.000 B** de la especificación. Si no cargó, se baja a 22.000 B, la salida prevista en la especificación (*Riesgos*).
- **Tope de la zona `c5`:** el heap estimado de la mayor zona que cargó con la tesela en memoria, **menos 2 KB** para la pantalla y las notas. Se redondea hacia abajo al KB.

- [ ] **Step 2: ¿Vale el diseño de zonas?**

La especificación prevé zonas de 20 km y parte en cuatro de 10 km las que pasan del tope. Como referencia, las zonas de 10 km de la variante normal tienen una mediana de 13,8 KB; en `c5` serán algo más ligeras, porque no llevan parajes fuera de la zona urbana.
- **Tope ≥ 14 KB:** el diseño se mantiene con ese tope. Se anota y el plan 3 lo usa.
- **Tope < 14 KB:** una buena parte de las zonas de 10 km no cabría, y harían falta más niveles. **No se decide aquí.** Se anotan estas salidas en la especificación para que elija el autor:
  - **(a) Zona sin tesela:** la zona se consulta solo cada ~100 m recorridos, con la tesela soltada, y se guardan las cadenas del resultado. Cada consulta cuesta recargar la tesela, ~10 ms medidos en la puerta.
  - **(b) Zonas en bytes,** como las teselas: ~4 B por número en lugar de 5, y un pico de 2,33 veces en lugar de 2,2.
  - **(c) Zonas de 10 km y de 5 km:** más recursos, a contar con el generador.

- [ ] **Step 3: Escribir el resultado en la especificación**

Al final de la especificación, con las cifras reales (sin redondear las medidas, sí los topes):

```markdown
## Memoria (plan 2, AAAA-MM-DD)

Por partes (tests del fēnix 5, t412, 262 calles):

| Parte | Antes (puerta) | Sin S (plan 2) |
|---|---|---|
| ByteArray | N B | N B |
| S como String | N B (N letras, N bytes) | — |
| mejor + mejorRun (vacías / llenas) | N / N B | N / N B |
| Tesela sobre el ByteArray | N B | N B |
| Tras una búsqueda | +N B | +N B |
| **Tesela lista** | **40.192 B** | **N B** |

Modo app (lastre hasta 66 KB en uso; total del simulador N B):

| Medida | Resultado |
|---|---|
| Libre antes de la tesela | N B |
| Tesela en reposo / tras buscar | N B / N B |
| Zonas que cargan con la tesela (heap estimado) | N, N, … B |
| Primera que no carga | N B (o: todas) |

**Topes:** tesela **N B** · zona `c5` **N B** (la mayor que cargó, menos 2 KB).
**Zonas:** se mantiene el diseño de 20 km en dos niveles / salidas (a), (b) y (c) para que decida el autor.
```

- [ ] **Step 4: Commit**

```bash
cd ~/code/calle-c5 && git add docs/specs/2026-10-26-calle-galicia-fenix5-formato5.md && git commit -m "Especificación c5: memoria medida en el fēnix 5 y topes de tesela y zona (plan 2)"
```

- [ ] **Step 5: Avisar**

- **Al autor:** la tabla, los topes y, si el tope de zona sale por debajo de 14 KB, las salidas (a), (b) y (c) para que elija. El plan 3 no se escribe hasta tener esa decisión.
- **A la coordinadora** (otra sesión): los commits de `c5-galicia`. Este plan no toca nada fuera de `puerta/`, `source-c5/`, `tools/formato5.py`, `tools/test_formato5.py`, `tools/puerta_c5.py` ni la especificación.
