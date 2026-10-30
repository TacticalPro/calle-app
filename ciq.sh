#!/bin/bash
# CALLE — compilar, probar, generar el callejero y empaquetar.
#
#   ./ciq.sh datos        genera el callejero (REGION=santiago|madrid;
#                         VARIANTE=c para los de 128 KB, fēnix 5/5S y 6/6S, y para el 6X Pro;
#                         VARIANTE=b para los de 1,25 MB y 254 recursos: fēnix 6 Pro/6S Pro y 5X/5 Plus (Galicia);
#                         --refresh vuelve a Overpass; --comun solo rehace Callejero/Regiones/ajuste)
#   ./ciq.sh ref          autotest de la referencia Python y vectores para los tests de Monkey C
#   ./ciq.sh build        .prg de depuración        → bin/calle.prg
#   ./ciq.sh release      .prg optimizado (-r -O 2) → bin/calle-release.prg  (el que va al reloj)
#   ./ciq.sh test         compila con los tests y los ejecuta en el simulador
#                         APP=<app>: con el jungle de esa app del catálogo (tools/tienda.py; las provincias de la c5:
#                         APP=coruna DEV=fenix5 ./ciq.sh test). También vale para build, release y sim
#   ./ciq.sh sim          abre el simulador con la app
#   ./ciq.sh package      .iq con el id de manifest.xml (publicación; no es la beta). ZONAS=<zona,zona…> (por
#                         defecto, REGION): las zonas que lleva; cada reloj, las que tenga generadas su variante
#   ./ciq.sh tienda       APP=<zona> .iq de una app del catálogo (tools/catalogo.json) → bin/calle-<zona>.iq
#   ./ciq.sh beta         APP=<zona>: la beta privada de esa app del catálogo ("beta_id" y "beta_relojes" en
#                         tools/catalogo.json) → bin/calle-<zona>-beta.iq (se sube al portal). Sin APP, falla
#   ./ciq.sh prg6x        .prg para un fēnix 6X Pro → bin/calle-fenix6x.prg (se copia por cable a GARMIN/APPS)
#   ./ciq.sh instalar     release + copia a GARMIN/Apps/CALLE.PRG por MTP (reloj por USB directo
#                         al Mac, no al dock; Garmin Express cerrado; sustituye la versión anterior)
#   ./ciq.sh privacidad   falla si el código puede sacar datos del reloj o guardar fuera de Notas y Ajustes
#                         (va antes de release/instalar/package)
#   release, package, beta, tienda, prg6x e instalar compilan desde una copia de HEAD en
#   /private/tmp/ciq-build/calle-<app>-<worktree>/ (ruta neutra: el debug.xml de cada .prg lleva la ruta de las
#   fuentes) y fallan si el producto lleva /Users/, /private/var/folders/ o el nombre del usuario dentro.
#   ./ciq.sh guarda-test  prueba la guarda de rutas en los dos sentidos: un .iq sucio, roto o ausente falla y uno
#                         limpio pasa; y la de privacidad, con y sin las carpetas generadas
#                         (y la beta sin APP, y tools/iq_solido.py, que necesita iq_limpio.py en IQ_LIMPIO o en el PATH)
#   ./ciq.sh icon         regenera el icono (Python + Pillow)
#   ./ciq.sh fuentes      mide las fuentes de sistema de cada reloj en el simulador → tools/fonts/metricas.json
#                         (las usa tools/mockup.py; rehacer al añadir un reloj al catálogo)
#
# DEV=fenix7xpronowifi ./ciq.sh build   para la variante sin wifi; DEV=fenix6xpro para el 6X; DEV=fenix6 (o
# fenix6s, fenix5, fenix5s) para los de 128 KB, con los datos de VARIANTE=c.
set -euo pipefail
cd "$(dirname "$0")"

DEV="${DEV:-fenix7xpro}"
REGION="${REGION:-santiago}"
VARIANTE="${VARIANTE:-normal}"     # c: Madrid entero en teselas adaptativas para los de 128 KB y el 6X Pro
                                   # (resources-gen-c/, source-gen-c/); b y c5: ver tools/build_callejero.py
KEY="${KEY:-$HOME/.garmin/developer_key.der}"
PY="${PY:-python3} -I"   # PY=/ruta/a/python3 para usar otro (Pillow, para ./ciq.sh icon)
CFG="$HOME/Library/Application Support/Garmin/ConnectIQ/current-sdk.cfg"

sdk() {
    [ -f "$CFG" ] || { echo "Falta el SDK: abra SdkManager.app, inicie sesión y descargue el SDK y el fēnix 7X Pro." >&2; exit 1; }
    local s; s="$(tr -d '\n' < "$CFG")"; s="${s%/}"
    [ -d "/opt/homebrew/opt/openjdk@21/bin" ] && export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"
    [ -d "$HOME/Library/Application Support/Garmin/ConnectIQ/Devices/$DEV" ] || {
        echo "Falta el dispositivo $DEV: descárguelo en SdkManager.app → Devices." >&2; exit 1; }
    [ -f source-gen/Callejero.mc ] || { echo "Falta el callejero: ./ciq.sh datos" >&2; exit 1; }
    BIN="$s/bin"
}

# Apps del catálogo con beta propia ("beta_id"), para el mensaje de ./ciq.sh beta sin APP.
betas() { $PY -c 'import json, sys; print(", ".join(k for k, v in json.load(open(sys.argv[1], encoding="utf-8")).items()
                                       if isinstance(v, dict) and v.get("beta_id")))' tools/catalogo.json; }

monkeyc() { "$BIN/monkeyc" -d "$DEV" -f "$(jungle)" -y "$KEY" "$@"; }
# El jungle: el del repositorio o, con APP, el de esa app del catálogo (tools/tienda.py lo escribe en bin/tienda/).
jungle() { if [ -n "${APP:-}" ]; then echo "$($PY tools/tienda.py "$APP")/monkey.jungle"; else echo monkey.jungle; fi; }

# Lo que sale del Mac (los .iq de la tienda y de la beta, los .prg para el reloj) se compila desde una copia en
# una ruta neutra, /private/tmp/ciq-build/calle-<app>-<worktree>/: el debug.xml de cada .prg lleva la ruta absoluta
# de cada fuente (filename="…/source/X.mc", miles de veces por paquete) y, compilado aquí, llevaría la carpeta del
# usuario (2026-10-29). Una copia por worktree, no por app: dos worktrees que compilaban la misma app compartían la
# copia y el rsync --delete de uno pisaba al del otro (2026-10-30). test, build y sim siguen compilando aquí.
# neutro: si no estamos ya en la copia (CIQ_NEUTRO), saca HEAD con git archive (se publica lo que hay en un commit,
# no lo que quede sin guardar), le añade lo generado, que no está en git (callejero y tests de ./ciq.sh datos y ref,
# y las metas de tools/out), vuelve a lanzar esta misma orden dentro y trae bin/; la copia se puede borrar.
NEUTRO=/private/tmp/ciq-build
neutro() {
    [ -n "${CIQ_NEUTRO:-}" ] && return 0
    local dest; dest="$NEUTRO/calle-${APP:-base}-$(basename "$(git rev-parse --show-toplevel)")"
    local sucio; sucio="$(git status --porcelain)"
    if [ -n "$sucio" ]; then
        echo "neutro: esto no está en HEAD y no entra en la copia (lo generado, que git ignora, sí):" >&2
        echo "$sucio" >&2
    fi
    rm -rf "$dest"; mkdir -p "$dest"
    git archive HEAD | tar -x -C "$dest"
    rm -rf "$dest/docs"
    # De tools/out solo van las metas: tienda.py rehace el común de la app con ellas (--comun --solo) en cuanto
    # source-gen-c5 tiene más de una provincia; sin ellas, Regiones.mc salía vacío.
    rsync -a --exclude __pycache__ --exclude .DS_Store --include '/*-gen*/***' --include /puerta/ \
        --include '/puerta/*-gen/***' --include /tools/ --include /tools/out/ --include '/tools/out/meta-*.json' \
        --exclude '*' ./ "$dest/"
    echo "compilo en $dest" >&2
    CIQ_NEUTRO=1 "$dest/ciq.sh" "$@"
    mkdir -p bin; rsync -a "$dest/bin/" bin/
    exit 0
}

# Guarda: ningún producto que salga del Mac lleva rutas del Mac: /Users/, /private/var/folders/ (el $TMPDIR) ni el
# nombre del usuario. Mira dentro del .iq (manifest, debug.xml y .prg de cada reloj) y en cada .prg suelto con su
# .debug.xml. Si las lleva, el fichero se retira a /tmp y se falla. Falla cerrada: sin ficheros que mirar, con uno
# que falta o está vacío, con un .iq que bsdtar no lee o con un recuento que no sale, es fallo, no OK. El contenido
# va a un fichero y se cuenta entero con grep -c: con grep -q en una tubería y pipefail, grep cierra al primer
# acierto, bsdtar muere de SIGPIPE y el sucio pasaba por limpio (2026-10-30).
rutas() {
    local f n malo=0 tmp
    [ $# -gt 0 ] || { echo "rutas: no hay ningún producto que mirar" >&2; return 1; }
    tmp="$(mktemp)"
    for f in "$@"; do
        if [ ! -s "$f" ]; then
            echo "rutas: $f no existe o está vacío" >&2; malo=1; continue
        fi
        case "$f" in
            *.iq) if ! bsdtar -xOf "$f" > "$tmp"; then echo "rutas: bsdtar no puede leer $f" >&2; malo=1; continue; fi ;;
            *)    cat "$f" > "$tmp"; if [ -f "$f.debug.xml" ]; then cat "$f.debug.xml" >> "$tmp"; fi ;;
        esac
        if [ ! -s "$tmp" ]; then
            echo "rutas: $f no tiene nada dentro" >&2; malo=1; continue
        fi
        n=$(grep -acF -e /Users/ -e /private/var/folders/ -e "${USER:-$(id -un)}" "$tmp" || true)
        case "$n" in
            ''|*[!0-9]*) echo "rutas: no pude contar las rutas de $f" >&2; malo=1 ;;
            0) echo "rutas: $f sin rutas del Mac" >&2 ;;
            *) mkdir -p /tmp/ciq-rechazado; mv "$f" /tmp/ciq-rechazado/
               if [ -f "$f.debug.xml" ]; then mv "$f.debug.xml" /tmp/ciq-rechazado/; fi
               echo "rutas: $f lleva rutas del Mac ($n líneas); retirado a /tmp/ciq-rechazado/" >&2; malo=1 ;;
        esac
    done
    rm -f "$tmp"
    return $malo
}

# El simulador es uno para todas las sesiones y proyectos (Tactical Grid, Esfera…): el candado
# /tmp/calles-sim.lock (un directorio con «quien» dentro) dice quién lo usa. Sin él, dos sesiones lo abren y
# cierran a la vez y los tests salen en blanco (2026-10-26). Se toma al usarlo y se suelta al salir; si lo
# tiene otro, se espera (SIM_ESPERA s, 1800 por defecto) y, si no lo suelta, se para.
# Con SIM_ESPERA=0 no se espera: si está ocupado, se para enseguida.
CANDADO=/tmp/calles-sim.lock
simulador() {
    local t=0
    # Turno dado de antemano (SIM_TURNO=<nombre>): si el candado ya es de ese nombre (primer campo de «quien»),
    # se usa sin esperar, sin reescribirlo y sin soltarlo al salir; lo suelta quien lo tomó.
    if [ -n "${SIM_TURNO:-}" ] && [ "$(cut -d' ' -f1 "$CANDADO/quien" 2>/dev/null)" = "$SIM_TURNO" ]; then
        pgrep -x simulator >/dev/null || { open "$BIN/ConnectIQ.app"; sleep 4; }
        return
    fi
    until mkdir "$CANDADO" 2>/dev/null; do
        [ -f "$CANDADO/quien" ] && grep -q "^calle-fenix $$ " "$CANDADO/quien" && break
        [ $t -eq 0 ] && echo "simulador ocupado por: $(cat "$CANDADO/quien" 2>/dev/null) — espero" >&2
        t=$((t + 10)); [ $t -gt "${SIM_ESPERA:-1800}" ] && { echo "simulador: sigue ocupado; paro" >&2; exit 1; }
        sleep 10
    done
    echo "calle-fenix $$ $(date +%H:%M)" > "$CANDADO/quien"
    trap 'grep -q "^calle-fenix $$ " "$CANDADO/quien" 2>/dev/null && rm -r "$CANDADO"' EXIT
    # Por el nombre del proceso, no con -f: la línea de órdenes de otras sesiones que esperan el candado contiene
    # «ConnectIQ.app» y daba el simulador por abierto sin estarlo («Unable to connect to simulator», 2026-10-26).
    pgrep -x simulator >/dev/null || { open "$BIN/ConnectIQ.app"; sleep 4; }
}

# La app no debe poder sacar nada del reloj: sin red, sin grabar actividad, sin
# servicio en segundo plano. Sin el permiso Communications la plataforma no deja
# hacer peticiones; esto vigila que nadie lo añada sin darse cuenta. Lo único que
# se guarda en el reloj son las anotaciones (source/Notas.mc; riesgo aceptado el 2026-10-23:
# con el reloj perdido y por USB, se leen) y la zona elegida del callejero (source/Ajustes.mc).
#   Falla cerrada (2026-10-30): con un glob sin coincidencias (un worktree sin test-gen*/ ni source-gen*/), grep y
# awk salían con 2 por la carpeta que faltaba y el «if» lo tomaba por limpio aunque hubiera una línea culpable. Ahora
# solo se pasan las carpetas que existen, y un 2 de grep o de awk es fallo.
privacidad() {
    local malo=0 rc out d dirs=() pruebas=() ng
    ng="$(shopt -p nullglob || true)"; shopt -s nullglob   # shopt -p sale con 1 si está apagada
    for d in source source-c5 source-gen* test test-gen*; do [ -d "$d" ] && dirs+=("$d"); done
    pruebas=(test/*.mc test-gen*/*.mc)
    $ng
    if [ ! -d source ] || [ ${#pruebas[@]} -eq 0 ]; then
        echo "privacidad: no encuentro source/ o test/*.mc; no puedo revisar nada" >&2; return 1
    fi
    out="$(grep -rnE 'Communications|makeWebRequest|ActivityRecording|FitContributor|setProperty|Toybox\.Background|registerForTemporalEvent' "${dirs[@]}")" && rc=0 || rc=$?
    case $rc in
        0) echo "$out"; echo "privacidad: el código usa una API que puede sacar o guardar datos (arriba)." >&2; malo=1 ;;
        1) ;;
        *) echo "privacidad: grep falló ($rc) al buscar APIs" >&2; malo=1 ;;
    esac
    out="$(grep -rnE 'Storage|Properties' "${dirs[@]}")" && rc=0 || rc=$?
    case $rc in
        0) out="$(grep -vE '^source/(Notas|Ajustes)\.mc:' <<< "$out" || true)"
           if [ -n "$out" ]; then
               echo "$out"; echo "privacidad: solo source/Notas.mc y source/Ajustes.mc pueden guardar en el reloj (arriba)." >&2; malo=1
           fi ;;
        1) ;;
        *) echo "privacidad: grep falló ($rc) al buscar Storage y Properties" >&2; malo=1 ;;
    esac
    # test/ y test-gen*/ están en el sourcePath de los builds publicados: solo quedan fuera si todo va con (:test).
    out="$(awk 'FNR == 1 { prev = "" } /^(class|module|function) / && prev !~ /\(:test\)/ { print FILENAME ":" FNR ": " $0; bad = 1 }
            NF { prev = $0 } END { exit !bad }' "${pruebas[@]}")" && rc=0 || rc=$?
    case $rc in
        0) echo "$out"; echo "privacidad: en test/ todo va con (:test), o entraría en el paquete publicado (arriba)." >&2; malo=1 ;;
        1) ;;
        *) echo "privacidad: awk falló ($rc) al revisar test/" >&2; malo=1 ;;
    esac
    local perms; perms="$(grep -o 'uses-permission id="[^"]*"' manifest.xml | sed 's/.*id="//;s/"//' | sort -u | tr '\n' ' ')"
    if [ "$perms" != "Positioning " ]; then
        echo "privacidad: el manifiesto pide permisos de más: $perms" >&2; malo=1
    fi
    [ $malo -eq 0 ] && echo "privacidad: OK (solo Positioning; sin red, sin grabación; solo Notas y Ajustes guardan en el reloj)"
    return $malo
}

# Prueba de las dos guardas en los dos sentidos, sin SDK (2026-10-30): una guarda que no se ha visto fallar no se
# sabe si falla. rutas: los .iq sucios (cada una de las tres rutas vetadas), rotos, vacíos o ausentes fallan y el
# limpio pasa; también con .prg sueltos. privacidad: sin carpetas generadas (el glob vacío que la dejaba pasar) y
# con ellas, el código limpio pasa y el que usa red, guarda fuera de Notas y Ajustes o deja un test sin (:test) falla.
guarda_test() {
    local t mal=0 v i=0
    t="$(mktemp -d)"
    # Cada caso corre en un bash aparte con set -euo pipefail, como en una orden de verdad: dentro de un «if» bash no
    # aplica set -e, y una línea que en uso real corta el script en silencio aquí pasaba (2026-10-30, shopt -p).
    espera() {   # espera <pasa|falla> <qué> <orden…>
        local quiero=$1 que=$2 r; shift 2
        if bash -c "set -euo pipefail; $(declare -f rutas privacidad); \"\$@\"" _ "$@"; then r=pasa; else r=falla; fi
        if [ "$r" = "$quiero" ]; then echo "guarda-test: OK   $que: $r"; else echo "guarda-test: MAL  $que: $r, y debía $quiero"; mal=1; fi
    }
    iq() { mkdir -p "$t/iq-$1"; printf '%s\n' "$2" > "$t/iq-$1/debug.xml"; (cd "$t/iq-$1" && bsdtar --format 7zip -cf "../$1.iq" debug.xml); }

    iq limpio 'filename="/private/tmp/ciq-build/calle/source/Calle.mc"'
    espera pasa ".iq limpio" rutas "$t/limpio.iq"
    for v in /Users/x/calle/source/Calle.mc /private/var/folders/x/T/Calle.mc "${USER:-$(id -un)}"; do
        i=$((i + 1)); iq "sucio$i" "filename=\"$v\""
        espera falla ".iq sucio con «${v%%/x*}»" rutas "$t/sucio$i.iq"
    done
    printf 'esto no es un 7z\n' > "$t/roto.iq"; : > "$t/vacio.iq"
    espera falla ".iq roto" rutas "$t/roto.iq"
    espera falla ".iq vacío" rutas "$t/vacio.iq"
    espera falla ".iq ausente" rutas "$t/ausente.iq"
    espera falla "sin ficheros (glob vacío)" rutas
    iq juntos "filename=\"/Users/x/calle/source/Calle.mc\""
    espera falla "limpio y sucio juntos" rutas "$t/limpio.iq" "$t/juntos.iq"
    printf 'PRG\n' > "$t/limpio.prg"; printf '<debug filename="/private/tmp/ciq-build/x.mc"/>\n' > "$t/limpio.prg.debug.xml"
    printf 'PRG\n' > "$t/sucio.prg"; printf '<debug filename="/Users/x/x.mc"/>\n' > "$t/sucio.prg.debug.xml"
    espera pasa ".prg limpio con su debug.xml" rutas "$t/limpio.prg"
    espera falla ".prg con debug.xml sucio" rutas "$t/sucio.prg"

    mkdir -p "$t/p/source" "$t/p/test"
    printf 'using Toybox.Position;\n' > "$t/p/source/Calle.mc"
    printf '(:test)\nfunction prueba(logger) { return true; }\n' > "$t/p/test/Prueba.mc"
    printf '<iq:uses-permission id="Positioning"/>\n' > "$t/p/manifest.xml"
    espera pasa "privacidad limpia sin carpetas generadas" eval "cd '$t/p'; privacidad"
    printf 'Communications.makeWebRequest(u, {}, {}, m);\n' > "$t/p/source/Red.mc"
    espera falla "privacidad con red, sin carpetas generadas" eval "cd '$t/p'; privacidad"
    mv "$t/p/source/Red.mc" "$t/Red.mc"
    mkdir -p "$t/p/source-gen" "$t/p/test-gen"; printf 'module Callejero {}\n' > "$t/p/source-gen/Callejero.mc"
    printf '(:test)\nmodule PruebaGen {}\n' > "$t/p/test-gen/PruebaGen.mc"
    espera pasa "privacidad limpia con carpetas generadas" eval "cd '$t/p'; privacidad"
    printf 'Application.Storage.setValue("x", 1);\n' > "$t/p/source-gen/Guarda.mc"
    espera falla "privacidad con Storage fuera de Notas y Ajustes" eval "cd '$t/p'; privacidad"
    mv "$t/p/source-gen/Guarda.mc" "$t/Guarda.mc"
    printf 'function suelta() {}\n' > "$t/p/test/Suelta.mc"
    espera falla "privacidad con un test sin (:test)" eval "cd '$t/p'; privacidad"

    # beta (2026-10-30): sin APP falla y dice cómo seguir; con APP, el id del manifiesto es el "beta_id" de la app en el
    # catálogo, no otro suelto en este script. Sin SDK ni datos: tienda.py en una copia mínima, con la región de mentira.
    local out d quiero sale
    out="$(env -u APP "$PWD/ciq.sh" beta 2>&1)" && v=pasa || v=falla
    if [ "$v" = falla ] && grep -qF 'APP=<app> ./ciq.sh beta' <<< "$out"; then
        echo "guarda-test: OK   beta sin APP: falla y dice cómo seguir"
    else echo "guarda-test: MAL  beta sin APP: $v, y debía fallar con el uso"; mal=1; fi
    mkdir -p "$t/b/tools" "$t/b/source-gen" "$t/b/source-gen-b"
    cp tools/tienda.py tools/catalogo.json "$t/b/tools/"; cp manifest.xml monkey.jungle "$t/b/"
    printf 'module RegionGalicia {}\n' > "$t/b/source-gen/RegionGalicia.mc"; cp "$t/b/source-gen/RegionGalicia.mc" "$t/b/source-gen-b/"
    quiero="$($PY -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["galicia"]["beta_id"])' \
        tools/catalogo.json)" || quiero=
    d="$($PY "$t/b/tools/tienda.py" galicia --beta 2>/dev/null)" || d=
    sale="$(grep -o '<iq:application id="[0-9a-f]*"' "${d:-/nada}/manifest.xml" 2>/dev/null | grep -o '[0-9a-f]\{32\}' || true)"
    if [ -n "$quiero" ] && [ "$sale" = "$quiero" ]; then
        echo "guarda-test: OK   beta APP=galicia: id ${sale}, el \"beta_id\" del catálogo"
    else echo "guarda-test: MAL  beta APP=galicia: id «${sale}», y el catálogo dice «${quiero}»"; mal=1; fi

    # tools/iq_solido.py (2026-10-30): un .iq de mentira, firmado con una clave de prueba como lo firma monkeyc
    # (manifest.sig2 = RSA-SHA256 de manifest.xml, dev_key.pub en DER). El bueno pasa y deja la salida; con la firma
    # rota, sin manifest.sig2, con una ruta del Mac, con la salida ya puesta o con un empaquetado que pierde o cambia
    # un fichero, falla y no deja salida. Necesita iq_limpio.py en IQ_LIMPIO o en el PATH, como la herramienta.
    local s="$t/s" caso
    mkdir -p "$s/iq/006-B0001-00" "$s/iq/006-B0002-00"
    openssl genrsa -out "$s/k.pem" 2048 2>/dev/null
    openssl rsa -in "$s/k.pem" -pubout -outform DER -out "$s/iq/dev_key.pub" 2>/dev/null
    printf '<iq:manifest><iq:product partNumber="006-B0001-00"/></iq:manifest>\n' > "$s/iq/manifest.xml"
    openssl dgst -sha256 -sign "$s/k.pem" -out "$s/iq/manifest.sig2" "$s/iq/manifest.xml"
    head -c 300000 /dev/urandom > "$s/iq/006-B0001-00/calle.prg"; cp "$s/iq/006-B0001-00/calle.prg" "$s/iq/006-B0002-00/"
    for caso in 006-B0001-00 006-B0002-00; do
        printf '<debug filename="/private/tmp/ciq-build/calle/source/Calle.mc"/>\n' > "$s/iq/$caso/debug.xml"
    done
    sopa() {   # sopa <nombre> <carpeta>: el .iq como lo deja monkeyc (7z, un fichero tras otro)
        (cd "$2" && bsdtar --format 7zip -cf "$s/$1.iq" ./*)
    }
    sopa bueno "$s/iq"
    sin_salida() {   # sin_salida <qué> <salida>: tras un fallo, ni la salida ni la .parcial
        if [ -e "$2" ] || [ -e "$2.parcial" ]; then echo "guarda-test: MAL  $1: dejó salida"; mal=1; fi
    }
    espera pasa "iq_solido: .iq bueno" $PY tools/iq_solido.py "$s/bueno.iq" "$s/bueno-solido.iq"
    [ -s "$s/bueno-solido.iq" ] || { echo "guarda-test: MAL  iq_solido: el bueno no dejó salida"; mal=1; }
    espera falla "iq_solido: la salida ya existe" $PY tools/iq_solido.py "$s/bueno.iq" "$s/bueno-solido.iq"
    cp -R "$s/iq" "$s/rota"; printf '<!-- otro -->\n' >> "$s/rota/manifest.xml"; sopa rota "$s/rota"
    espera falla "iq_solido: firma rota" $PY tools/iq_solido.py "$s/rota.iq" "$s/rota-solido.iq"
    sin_salida "iq_solido: firma rota" "$s/rota-solido.iq"
    cp -R "$s/iq" "$s/sinfirma"; mv "$s/sinfirma/manifest.sig2" "$s/sinfirma.sig2"; sopa sinfirma "$s/sinfirma"
    espera falla "iq_solido: sin manifest.sig2" $PY tools/iq_solido.py "$s/sinfirma.iq" "$s/sinfirma-solido.iq"
    sin_salida "iq_solido: sin manifest.sig2" "$s/sinfirma-solido.iq"
    cp -R "$s/iq" "$s/ruta"; printf '<debug filename="/Users/x/calle/source/Calle.mc"/>\n' > "$s/ruta/006-B0002-00/debug.xml"
    sopa ruta "$s/ruta"
    espera falla "iq_solido: ruta del Mac dentro" $PY tools/iq_solido.py "$s/ruta.iq" "$s/ruta-solido.iq"
    sin_salida "iq_solido: ruta del Mac dentro" "$s/ruta-solido.iq"
    for caso in pierde cambia; do   # el empaquetado se estropea a propósito: la comprobación de después lo tiene que ver
        espera falla "iq_solido: el empaquetado $caso un fichero" $PY -c '
import sys; sys.path.insert(0, "tools"); import iq_solido as m
bueno = m.empaquetar
def malo(d, ficheros, dst):
    if sys.argv[1] == "pierde":
        ficheros = ficheros[:-1]
    else:
        (d / "006-B0002-00" / "calle.prg").write_bytes(b"otro")
    bueno(d, ficheros, dst)
m.empaquetar = malo
sys.exit(m.main(sys.argv[2:]))' "$caso" "$s/bueno.iq" "$s/$caso-solido.iq"
        sin_salida "iq_solido: el empaquetado $caso un fichero" "$s/$caso-solido.iq"
    done

    rm -rf "$t"
    [ $mal -eq 0 ] && echo "guarda-test: todo como debía"
    return $mal
}

case "${1:-build}" in
    datos)   shift; $PY tools/build_callejero.py --region "$REGION" --variante "$VARIANTE" "$@" ;;
    ref)     shift; $PY tools/ref.py --region "$REGION" --variante "$VARIANTE" "$@" ;;
    build)   sdk; mkdir -p bin; monkeyc -o bin/calle.prg -w ;;
    release) neutro "$@"; privacidad; sdk; mkdir -p bin; monkeyc -o bin/calle-release.prg -r -O 2 -w --build-stats 0
             rutas bin/calle-release.prg; ls -la bin/calle-release.prg ;;
    test)    sdk; mkdir -p bin; monkeyc -o bin/test.prg -t -w; simulador
             # Con tope de tiempo (TEST_MAX s, 600 por defecto): un test colgado retenía el simulador y el candado
             # (fēnix 6S, 22 min, 2026-10-26). macOS no trae «timeout»: se vigila en segundo plano.
             # monkeydo -t sale con 1 aunque todo pase: manda la línea final del informe (bin/test.log). El
             # vigilante se mata pase lo que pase (antes, con set -e, un wait fallido lo dejaba huérfano 600 s).
             { "$BIN/monkeydo" bin/test.prg "$DEV" -t | tee bin/test.log; } & md=$!
             ( sleep "${TEST_MAX:-600}"; kill -0 $md 2>/dev/null && { echo "test: más de ${TEST_MAX:-600} s; lo corto" >&2; pkill -P $md; kill $md; } ) & vig=$!
             wait $md || true; pkill -P $vig 2>/dev/null || true; kill $vig 2>/dev/null || true
             grep -q '^PASSED' bin/test.log ;;
    sim)     sdk; mkdir -p bin; monkeyc -o bin/calle.prg -w; simulador
             "$BIN/monkeydo" bin/calle.prg "$DEV" ;;
    package) # Por tools/tienda.py --raiz, como tienda: con el jungle de la raíz, cada .prg llevaba todas las regiones
             # de resources-gen y Java se quedaba sin memoria en el primer reloj (P96, 2026-10-30).
             neutro "$@"; privacidad; sdk; mkdir -p bin
             dir="$($PY tools/tienda.py --raiz "${ZONAS:-$REGION}")"
             "$BIN/monkeyc" -e -f "$dir/monkey.jungle" -y "$KEY" -o bin/calle.iq -r -O 2 -w 2>&1 \
                 | { grep -v "is large (> 8kb)" || true; }
             rutas bin/calle.iq; ls -la bin/calle.iq ;;
    beta)    # Solo la beta de una app del catálogo, con su "beta_id" (tools/tienda.py --beta). La beta de la raíz, sin
             # APP, se retiró el 2026-10-30: llevaba su id suelto aquí, que era el de la beta de Galicia, y con otras
             # ZONAS subía otra región a esa app.
             [ -n "${APP:-}" ] || { echo "beta: falta APP. Uso: APP=<app> ./ciq.sh beta, con una app de tools/catalogo.json que tenga \"beta_id\": $(betas)" >&2; exit 1; }
             neutro "$@"; privacidad; sdk
             dir="$($PY tools/tienda.py "$APP" --beta)"
             "$BIN/monkeyc" -e -f "$dir/monkey.jungle" -y "$KEY" -o "bin/calle-$APP-beta.iq" -r -O 2 -w 2>&1 \
                 | { grep -v "is large (> 8kb)" || true; }
             rutas "bin/calle-$APP-beta.iq"; ls -la "bin/calle-$APP-beta.iq" ;;
    tienda)  # App de la tienda pública: una por zona, con el id, el nombre y los relojes de tools/catalogo.json.
             neutro "$@"; privacidad; sdk
             dir="$($PY tools/tienda.py "${APP:?APP=<zona de tools/catalogo.json>}")"
             "$BIN/monkeyc" -e -f "$dir/monkey.jungle" -y "$KEY" -o "bin/calle-$APP.iq" -r -O 2 -w 2>&1 \
                 | { grep -v "is large (> 8kb)" || true; }
             rutas "bin/calle-$APP.iq"; ls -la "bin/calle-$APP.iq" ;;
    prg6x)   # .prg firmado para un fēnix 6X Pro, para copiarlo por cable a GARMIN/APPS sin pasar por la tienda.
             # Con los datos de la variante c (resources-gen-c/, ver monkey.jungle).
             neutro "$@"; privacidad; DEV=fenix6xpro; sdk; mkdir -p bin
             monkeyc -o bin/calle-fenix6x.prg -r -O 2 -w 2>&1 | grep -v "is large (> 8kb)"
             rutas bin/calle-fenix6x.prg; ls -la bin/calle-fenix6x.prg ;;
    instalar) neutro "$@"; privacidad; sdk; mkdir -p bin; monkeyc -o bin/calle-release.prg -r -O 2 -w
             rutas bin/calle-release.prg
             [ tools/mtp_enviar -nt tools/mtp_enviar.c ] || clang -O2 -o tools/mtp_enviar tools/mtp_enviar.c \
                 -I/opt/homebrew/include -L/opt/homebrew/lib -lmtp
             tools/mtp_enviar bin/calle-release.prg CALLE.PRG 2>&1 | grep -v "association\|UNKNOWN\|report this" ;;
    privacidad) privacidad ;;
    guarda-test) guarda_test ;;
    icon)    $PY tools/gen_icon.py ;;
    fuentes) sdk; simulador; out="$(mktemp -d)"
             for d in $(grep -o 'product id="[^"]*"' tools/medir_fuentes/manifest.xml | sed 's/.*id="//;s/"//'); do
                 DEV=$d; sdk
                 "$BIN/monkeyc" -d "$d" -f tools/medir_fuentes/monkey.jungle -y "$KEY" -o "$out/$d.prg" -t -w >/dev/null
                 "$BIN/monkeydo" "$out/$d.prg" "$d" -t > "$out/out-$d.txt" 2>&1 || true
                 echo "$d: $(grep -c 'MED ' "$out/out-$d.txt") líneas"
             done
             $PY tools/medir_fuentes/recoger.py "$out"/out-*.txt tools/fonts/metricas.json ;;

    *)       awk 'NR == 1 { next } /^#/ { print; next } { exit }' "$0"; exit 1 ;;
esac
