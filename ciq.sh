#!/bin/bash
# CALLE — compilar, probar, generar el callejero y empaquetar.
#
#   ./ciq.sh datos        genera el callejero (REGION=santiago|madrid; VARIANTE=6x para el fēnix 6X,
#                         VARIANTE=c para los de 128 KB: fēnix 5/5S y 6/6S;
#                         --refresh vuelve a Overpass; --comun solo rehace Callejero/Regiones/ajuste)
#   ./ciq.sh ref          autotest de la referencia Python y vectores para los tests de Monkey C
#   ./ciq.sh build        .prg de depuración        → bin/calle.prg
#   ./ciq.sh release      .prg optimizado (-r -O 2) → bin/calle-release.prg  (el que va al reloj)
#   ./ciq.sh test         compila con los tests y los ejecuta en el simulador
#   ./ciq.sh sim          abre el simulador con la app
#   ./ciq.sh package      .iq con el id de manifest.xml (publicación; no es la beta)
#   ./ciq.sh tienda       APP=<zona> .iq de una app del catálogo (tools/catalogo.json) → bin/calle-<zona>.iq
#   ./ciq.sh beta         .iq firmado con el id de la beta → bin/calle-beta.iq (se sube al portal; 7X Pro y 6X)
#                         APP=<zona>: la beta propia de esa app del catálogo ("beta_id", solo el 7X Pro)
#                         → bin/calle-<zona>-beta.iq
#   ./ciq.sh prg6x        .prg para un fēnix 6X → bin/calle-fenix6x.prg (se copia por cable a GARMIN/APPS)
#   ./ciq.sh instalar     release + copia a GARMIN/Apps/CALLE.PRG por MTP (reloj por USB directo
#                         al Mac, no al dock; Garmin Express cerrado; sustituye la versión anterior)
#   ./ciq.sh privacidad   falla si el código puede sacar datos del reloj o guardar fuera de Notas y Ajustes
#                         (va antes de release/instalar/package)
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
VARIANTE="${VARIANTE:-normal}"     # 6x: datos compactos del fēnix 6X (resources-gen-6x/, source-gen-6x/); c: Madrid
                                   # entero en teselas adaptativas para los de 128 KB (resources-gen-c/, source-gen-c/)
KEY="${KEY:-$HOME/.garmin/developer_key.der}"
# Beta privada de la Connect IQ Store: id propio, distinto del de manifest.xml (el de las instalaciones
# por USB, que guarda las anotaciones). Generado el 2026-10-24; no cambiarlo o la tienda la tratará como
# otra app. Con otro id, la beta y la instalada por cable son dos apps distintas en el reloj.
BETA_ID="19ddcb3e1e1a4286a60a87c0f2d907d0"
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

monkeyc() { "$BIN/monkeyc" -d "$DEV" -f monkey.jungle -y "$KEY" "$@"; }

simulador() {
    pgrep -f "ConnectIQ.app" >/dev/null || { open "$BIN/ConnectIQ.app"; sleep 4; }
}

# La app no debe poder sacar nada del reloj: sin red, sin grabar actividad, sin
# servicio en segundo plano. Sin el permiso Communications la plataforma no deja
# hacer peticiones; esto vigila que nadie lo añada sin darse cuenta. Lo único que
# se guarda en el reloj son las anotaciones (source/Notas.mc; riesgo aceptado el 2026-10-23:
# con el reloj perdido y por USB, se leen) y la zona elegida del callejero (source/Ajustes.mc).
privacidad() {
    local malo=0
    if grep -rnE 'Communications|makeWebRequest|ActivityRecording|FitContributor|setProperty|Toybox\.Background|registerForTemporalEvent' source source-gen; then
        echo "privacidad: el código usa una API que puede sacar o guardar datos (arriba)." >&2; malo=1
    fi
    if grep -rnE 'Storage|Properties' source source-gen | grep -vE '^source/(Notas|Ajustes)\.mc:'; then
        echo "privacidad: solo source/Notas.mc y source/Ajustes.mc pueden guardar en el reloj (arriba)." >&2; malo=1
    fi
    local perms; perms="$(grep -o 'uses-permission id="[^"]*"' manifest.xml | sed 's/.*id="//;s/"//' | sort -u | tr '\n' ' ')"
    if [ "$perms" != "Positioning " ]; then
        echo "privacidad: el manifiesto pide permisos de más: $perms" >&2; malo=1
    fi
    [ $malo -eq 0 ] && echo "privacidad: OK (solo Positioning; sin red, sin grabación; solo Notas y Ajustes guardan en el reloj)"
    return $malo
}

case "${1:-build}" in
    datos)   shift; $PY tools/build_callejero.py --region "$REGION" --variante "$VARIANTE" "$@" ;;
    ref)     shift; $PY tools/ref.py --region "$REGION" --variante "$VARIANTE" "$@" ;;
    build)   sdk; mkdir -p bin; monkeyc -o bin/calle.prg -w ;;
    release) privacidad; sdk; mkdir -p bin; monkeyc -o bin/calle-release.prg -r -O 2 -w --build-stats 0
             ls -la bin/calle-release.prg ;;
    test)    sdk; mkdir -p bin; monkeyc -o bin/test.prg -t -w; simulador
             "$BIN/monkeydo" bin/test.prg "$DEV" -t ;;
    sim)     sdk; mkdir -p bin; monkeyc -o bin/calle.prg -w; simulador
             "$BIN/monkeydo" bin/calle.prg "$DEV" ;;
    package) privacidad; sdk; mkdir -p bin
             "$BIN/monkeyc" -e -f monkey.jungle -y "$KEY" -o bin/calle.iq -r -O 2 -w ;;
    beta)    if [ -n "${APP:-}" ]; then   # beta propia de una app del catálogo (tools/tienda.py --beta)
                 privacidad; sdk
                 dir="$($PY tools/tienda.py "$APP" --beta)"
                 "$BIN/monkeyc" -e -f "$dir/monkey.jungle" -y "$KEY" -o "bin/calle-$APP-beta.iq" -r -O 2 -w 2>&1 \
                     | { grep -v "is large (> 8kb)" || true; }
                 ls -la "bin/calle-$APP-beta.iq"; exit 0
             fi
             privacidad; sdk; mkdir -p bin/beta
             # Sin el 7X Pro sin Wi-Fi: su .prg es idéntico al del 7X Pro (15 MB con Madrid) y con él el .iq pasa
             # de los 10 MB que sube el navegador automatizado (2026-10-24). La beta solo la instala el desarrollador (7X Pro).
             # Ni los de 128 KB (fēnix 5/5S y 6/6S): la beta es la del 7X Pro y el 6X.
             sed -E 's/(<iq:application id=")[0-9a-f]{32}/\1'"$BETA_ID"'/; /fenix7xpronowifi/d; /id="fenix(5|5s|6|6s)"/d' \
                 manifest.xml > bin/beta/manifest.xml
             grep -q "id=\"$BETA_ID\"" bin/beta/manifest.xml || { echo "No pude poner el id de beta" >&2; exit 1; }
             awk -F' = ' '/^#/ || NF < 2 || $1 == "project.manifest" { print; next }
                 { n = split($2, a, ";"); s = ""; for (i = 1; i <= n; i++) s = s (i > 1 ? ";" : "") "../../" a[i]
                   print $1 " = " s }' monkey.jungle > bin/beta/monkey.jungle
             "$BIN/monkeyc" -e -f bin/beta/monkey.jungle -y "$KEY" -o bin/calle-beta.iq -r -O 2 -w 2>&1 | grep -v "is large (> 8kb)"
             ls -la bin/calle-beta.iq ;;
    tienda)  # App de la tienda pública: una por zona, con el id, el nombre y los relojes de tools/catalogo.json.
             privacidad; sdk
             dir="$($PY tools/tienda.py "${APP:?APP=<zona de tools/catalogo.json>}")"
             "$BIN/monkeyc" -e -f "$dir/monkey.jungle" -y "$KEY" -o "bin/calle-$APP.iq" -r -O 2 -w 2>&1 \
                 | { grep -v "is large (> 8kb)" || true; }
             ls -la "bin/calle-$APP.iq" ;;
    prg6x)  # .prg firmado para un fēnix 6X, para copiarlo por cable a GARMIN/APPS (la beta solo la instala
             # el desarrollador). Con los datos compactos de resources-gen-6x/.
             privacidad; DEV=fenix6xpro; sdk; mkdir -p bin
             monkeyc -o bin/calle-fenix6x.prg -r -O 2 -w 2>&1 | grep -v "is large (> 8kb)"
             ls -la bin/calle-fenix6x.prg ;;
    instalar) privacidad; sdk; mkdir -p bin; monkeyc -o bin/calle-release.prg -r -O 2 -w
             [ tools/mtp_enviar -nt tools/mtp_enviar.c ] || clang -O2 -o tools/mtp_enviar tools/mtp_enviar.c \
                 -I/opt/homebrew/include -L/opt/homebrew/lib -lmtp
             tools/mtp_enviar bin/calle-release.prg CALLE.PRG 2>&1 | grep -v "association\|UNKNOWN\|report this" ;;
    privacidad) privacidad ;;
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
