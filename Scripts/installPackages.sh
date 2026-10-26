#!/usr/bin/env bash
#
# installPackages.sh — restaura todos los paquetes declarados en packages/.
#
# Los manifiestos de packages/ se capturaron de la instalacion anterior de
# CachyOS. Este script instala lo que falte y omite lo que ya este presente,
# de modo que se puede ejecutar tantas veces como haga falta sin producir
# efectos secundarios.
#
# ESTRUCTURA DE LOS MANIFIESTOS
#
#   packages/<gestor>/<categoria>.txt   Paquetes instalables de esa categoria.
#   packages/<gestor>/excluidos/*.txt   Paquetes que NO se instalan. La
#                                       cabecera del archivo explica el
#                                       motivo de la exclusion.
#
# Las lineas que empiezan por '#' se ignoran, de modo que cada archivo puede
# llevar su propia documentacion.
#
# USO
#
#   Scripts/installPackages.sh --dry-run          Muestra el plan, no cambia nada.
#   Scripts/installPackages.sh                     Instala todo (pide sudo).
#   Scripts/installPackages.sh --only <gestor>    Instala un solo gestor.
#   Scripts/installPackages.sh --list              Lista el plan y termina.
#
# GESTORES
#
#   pacman   Paquetes de los repositorios oficiales de Arch y CachyOS.
#   yay      Paquetes del AUR declarados de forma explicita.
#   npm      Paquetes globales de npm.
#   cargo    Binarios instalados con cargo install.
#   pipx     Aplicaciones de Python instaladas con pipx.
#   flatpak  Aplicaciones de Flathub.
#
# REQUISITOS
#
#   - sudo disponible en el PATH (lo necesitan pacman y yay).
#   - base-devel y git, para poder compilar los paquetes del AUR.
#
# ESPOJOS
#
# El script antepone el CDN oficial de CachyOS (cdn.cachyos.org) a los
# mirrorlist si no lo tienen y refresca la base de sincronizacion antes de
# instalar. Sin las dos cosas, los repositorios de CachyOS devuelven 404 para
# las versiones recien publicadas: los espejos de terceros van con retraso y
# la base antigua sigue apuntando a los servidores muertos.
#
# CONFLICTOS
#
# rustup y rust no pueden coexistir, porque el paquete rust aporta tambien
# cargo y rustfmt. Como el manifiesto declara rustup, el script retira rust
# antes de instalarlo y deja constancia en el resumen.
#
# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13

# Se omite `set -e` de forma deliberada: un paquete del AUR que falle al
# compilar no debe abortar el resto de la restauracion. Cada paso comprueba
# su propio codigo de salida.
set -uo pipefail

readonly SCRIPT_NAME="${0##*/}"
readonly PKG_DIR="${PKG_DIR:-${HOME}/packages}"
readonly NPM_GLOBAL_ROOT="${NPM_GLOBAL_ROOT:-${HOME}/.local/lib/node_modules}"
readonly PIPX_VENVS="${PIPX_VENVS:-${HOME}/.local/share/pipx/venvs}"

readonly GESTORES=(pacman yay npm cargo pipx flatpak)

# Paquetes renombrados aguas arriba: nombre antiguo -> nombre actual.
declare -A RENOMBRADOS=(
  ["hyprland-preview-share-picker"]="hyprland-preview-share-picker-git"
)

# No figuran en los manifiestos, pero hacen falta para reparar herramientas
# que ahora mismo estan rotas. python-filelock: pipx 1.18.4 aborta con
# ModuleNotFoundError si falta su dependencia.
declare -a REPARACIONES=(python-filelock)

# Paquetes que chocan con otros ya instalados y que el manifiesto declara
# igualmente. La instalacion se resuelve retirando el incompatible.
# rustup y rust no pueden coexistir: el paquete rust aporta tambien cargo y
# rustfmt, de modo que rustup obliga a fuera el paquete rust completo.
declare -A CONFLICTOS=(
  ["rustup"]="rust"
)

# El CDN oficial de CachyOS es el unico espejo que va sincronizado con el
# repositorio. Los espejos de terceros van con retraso y devuelven 404 para
# las versiones recien publicadas, lo que aborta la transaccion entera con un
# "no se pudo obtener el archivo" y deja la base de sincronizacion inservible.
readonly CDN_CACHYOS="cdn.cachyos.org"

SECO=false
SOLO_LISTAR=false
SOLO_GESTOR="todos"
ACTUALIZAR_TODO=false

ESPOJOS_ARREGLADOS=false
BASE_REFRESCADA=false

# Control de ciclos al retirar paquetes y sus dependientes.
declare -a VISITADOS=()

# Paquetes retirados en esta ejecucion, para poder reinstalar los que
# formaban parte del manifiesto.
declare -a RETIRADOS_AHORA=()

declare -a RESULTADOS_INSTALADOS=()
declare -a RESULTADOS_PRESENTES=()
declare -a RESULTADOS_EXCLUIDOS=()
declare -a RESULTADOS_FALLIDOS=()
declare -a RESULTADOS_RETIRADOS=()

declare -a PAQUETES_REPO=()
declare -a PAQUETES_AUR=()
declare -a PAQUETES_YAY=()
declare -a BINARIOS_CARGO=()

# Conjuntos de consulta construidos una sola vez. Preguntar a pacman paquete
# por paquete cuesta medio segundo cada vez, lo que suma varios minutos sobre
# un manifiesto de este tamano.
declare -A CONJUNTO_REPO=()
declare -A CONJUNTO_INSTALADOS=()

REPARACION_RESUELTA=false

registrar() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "${*}"; }
avisar() { printf '[%s] AVISO: %s\n' "$(date '+%H:%M:%S')" "${*}" >&2; }
fallar() { printf '[%s] ERROR: %s\n' "$(date '+%H:%M:%S')" "${*}" >&2; }

uso() {
  cat <<EOF
Uso: ${SCRIPT_NAME} [opciones]

Restaura los paquetes declarados en ${PKG_DIR}/ a partir de la instalacion
anterior de CachyOS. Los paquetes que ya estan presentes se omiten.

Opciones:
  --dry-run          Muestra lo que se instalaria sin cambiar nada.
  --only <gestor>    Limita la ejecucion a un solo gestor.
  --list             Muestra el plan y termina.
  --refresh          Actualiza el sistema completo antes de instalar.
  -h, --help         Muestra esta ayuda.

Gestores: ${GESTORES[*]}
EOF
}

# Indica si un gestor forma parte de la ejecucion actual.
en_alcance() {
  [[ "${SOLO_GESTOR}" == "todos" || "${SOLO_GESTOR}" == "${1}" ]]
}

# Indica si un paquete existe en los repositorios oficiales.
esta_en_repo() { [[ -n "${CONJUNTO_REPO["${1}"]:-}" ]]; }

# Indica si un paquete ya esta instalado.
esta_instalado() { [[ -n "${CONJUNTO_INSTALADOS["${1}"]:-}" ]]; }

# Indica si el primer argumento coincide con alguno de los restantes.
contiene() {
  local buscado="${1}"
  shift
  local elemento
  for elemento in "${@}"; do
    [[ "${elemento}" == "${buscado}" ]] && return 0
  done
  return 1
}

# Devuelve el nombre que hay que usar, respetando la tabla de renombrados.
nombre_efectivo() {
  local nombre="${1}"
  printf '%s' "${RENOMBRADOS[${nombre}]:-${nombre}}"
}

# Lee los manifiestos de categoria de un gestor. Solo toma los archivos de la
# raiz del directorio: la subcarpeta 'excluidos' queda fuera a proposito, y
# tambien el manifiesto agregado, que es una copia de todo lo anterior.
leer_manifiestos() {
  local gestor="${1}"
  local archivo
  for archivo in "${PKG_DIR}/${gestor}"/*.txt; do
    [[ -f "${archivo}" ]] || continue
    [[ "${archivo}" == "${PKG_DIR}/${gestor}/installed.txt" ]] && continue
    grep -vE '^[[:space:]]*(#|$)' "${archivo}"
  done
}

# Muestra los paquetes excluidos y el motivo recorded en la cabecera.
reportar_excluidos() {
  local gestor archivo paquete motivo
  for gestor in "${GESTORES[@]}"; do
    for archivo in "${PKG_DIR}/${gestor}/excluidos"/*.txt; do
      [[ -f "${archivo}" ]] || continue
      motivo="$(sed -n '2s/^#[[:space:]]*//p' "${archivo}")"
      while read -r paquete; do
        [[ -z "${paquete}" ]] && continue
        RESULTADOS_EXCLUIDOS+=("${gestor}:${paquete}")
        registrar "excluido ${gestor}:${paquete} — ${motivo}"
      done < <(grep -vE '^[[:space:]]*(#|$)' "${archivo}")
    done
  done
}

# Lee el estado de paquetes de la maquina con dos llamadas en lugar de cientos.
cargar_estado() {
  local paquete
  while read -r paquete; do
    [[ -z "${paquete}" ]] && continue
    CONJUNTO_REPO["${paquete}"]=1
  done < <(pacman -Slq 2>/dev/null)

  while read -r paquete; do
    [[ -z "${paquete}" ]] && continue
    CONJUNTO_INSTALADOS["${paquete}"]=1
  done < <(pacman -Qq 2>/dev/null)

  registrar "pacman: ${#CONJUNTO_INSTALADOS[@]} paquetes instalados, ${#CONJUNTO_REPO[@]} en los repositorios"
}

# Se asegura de que node este accesible. En esta maquina node llega por mise
# y no forma parte del PATH de una shell que no sea de login, lo que rompe npm.
asegurar_node() {
  command -v node >/dev/null 2>&1 && return 0

  local shims="${HOME}/.local/share/mise/shims"
  if [[ -d "${shims}" ]]; then
    PATH="${shims}:${PATH}"
    export PATH
  fi

  local candidato
  for candidato in "${HOME}"/.local/share/mise/installs/node/*/bin; do
    [[ -x "${candidato}/node" ]] || continue
    PATH="${candidato}:${PATH}"
    export PATH
  done

  if command -v node >/dev/null 2>&1; then
    registrar "node: resuelto en $(command -v node)"
    return 0
  fi

  avisar "node no aparece en el PATH; no se pueden instalar paquetes de npm"
  return 1
}

# Se asegura de que un mirrorlist de CachyOS incluye el CDN oficial como
# servidor. Si no lo tiene, lo antepone: el CDN es el unico que responde con
# las versiones recien publicadas.
asegurar_espejo() {
  local lista="${1}"
  local ruta="${2}"

  [[ -f "${lista}" ]] || return 0
  if grep -qF "${CDN_CACHYOS}" "${lista}"; then
    return 0
  fi

  if [[ "${SECO}" == "true" || "${SOLO_LISTAR}" == "true" ]]; then
    printf '  pacman: antepondria %s a %s\n' "${CDN_CACHYOS}" "${lista}"
    return 0
  fi

  registrar "pacman: ${lista} no incluye el CDN oficial; se antepone"
  local temporal
  temporal="$(mktemp)"
  printf 'Server = https://%s%s\n' "${CDN_CACHYOS}" "${ruta}" > "${temporal}"
  cat "${lista}" >> "${temporal}"
  sudo install -m 644 "${temporal}" "${lista}"
  rm -f "${temporal}"
  ESPOJOS_ARREGLADOS=true
}

# Refresca la base de datos de sincronizacion. Es imprescindible: pacman
# descarga los paquetes desde los servidores guardados dentro de la base, de
# modo que si la base es antigua, sigue apuntando a espejos muertos y todos
# los paquetes dan 404 aunque el mirrorlist ya este corregido.
refrescar_base() {
  if [[ "${SECO}" == "true" || "${SOLO_LISTAR}" == "true" ]]; then
    printf '  pacman: refrescaria la base de sincronizacion\n'
    return 0
  fi

  registrar "pacman: refrescando la base de sincronizacion"
  sudo pacman -Sy --noconfirm || {
    fallar "No se pudo refrescar la base de sincronizacion"
    return 1
  }
  BASE_REFRESCADA=true
  if [[ "${ACTUALIZAR_TODO}" == "true" ]]; then
    registrar "pacman: actualizando el sistema completo"
    sudo pacman -Syu --noconfirm
  fi
}

# Devuelve los paquetes instalados que dependen del indicado.
# La consulta va con LC_ALL=C porque los nombres de los campos de pacman
# cambian con el idioma: en el del sistema el campo es "Requerido por" y la
# busqueda en ingles no encontraria nada.
paquetes_que_dependen_de() {
  local paquete="${1}"
  LC_ALL=C pacman -Qi "${paquete}" 2>/dev/null \
    | sed -n 's/^Required By *: *//p' \
    | tr ' ' '\n' \
    | grep -vE '^$|^None$'
}

# Retira un paquete y, antes, los que dependen de el. Sin esto pacman se
# niega a quitar rust porque rust-src lo necesita, y la transaccion aborta.
retirar_con_dependientes() {
  local paquete="${1}"
  local dependiente

  contiene "${paquete}" "${VISITADOS[@]}" && return 0
  VISITADOS+=("${paquete}")

  while read -r dependiente; do
    [[ -z "${dependiente}" ]] && continue
    retirar_con_dependientes "${dependiente}"
  done < <(paquetes_que_dependen_de "${paquete}")

  if [[ "${SECO}" == "true" || "${SOLO_LISTAR}" == "true" ]]; then
    printf '  pacman: retiraria %s\n' "${paquete}"
    return 0
  fi

  registrar "pacman: retirando ${paquete}"
  if ! sudo pacman -R --noconfirm "${paquete}"; then
    fallar "No se pudo retirar ${paquete}"
    return 1
  fi
  RESULTADOS_RETIRADOS+=("pacman:${paquete}")
  RETIRADOS_AHORA+=("${paquete}")
  return 0
}

# Quita una entrada de la lista de paquetes ya presentes.
quitar_de_presentes() {
  local objetivo="${1}"
  local -a restantes=()
  local elemento
  for elemento in "${RESULTADOS_PRESENTES[@]}"; do
    [[ "${elemento}" == "${objetivo}" ]] && continue
    restantes+=("${elemento}")
  done
  RESULTADOS_PRESENTES=("${restantes[@]}")
}

# Retira los paquetes que chocan con los que pide el manifiesto. Sin esto,
# pacman aborta la transaccion cuando un paquete declarado es incompatible
# con otro ya instalado, como rustup frente a rust.
resolver_conflictos() {
  local -a paquetes=("${@}")
  local -a a_retirar=()
  local paquete conflicto
  local -a conflictos=()

  for paquete in "${paquetes[@]}"; do
    [[ -n "${CONFLICTOS[${paquete}]:-}" ]] || continue
    read -ra conflictos <<< "${CONFLICTOS[${paquete}]}"
    for conflicto in "${conflictos[@]}"; do
      if esta_instalado "${conflicto}"; then
        a_retirar+=("${conflicto}")
      fi
    done
  done

  (( ${#a_retirar[@]} == 0 )) && return 0

  if [[ "${SECO}" == "true" || "${SOLO_LISTAR}" == "true" ]]; then
    printf '  pacman: retiraria %s y sus dependientes\n' "${a_retirar[*]}"
    return 0
  fi

  registrar "pacman: retirando ${a_retirar[*]}, incompatible con el manifiesto"
  local elemento
  for elemento in "${a_retirar[@]}"; do
    retirar_con_dependientes "${elemento}" || return 1
  done
  return 0
}

# Instala paquetes de los repositorios oficiales. Primero intenta una sola
# transaccion; si se aborta por un paquete problematico, repite uno a uno
# para que el resto llegue a instalarse.
instalar_repos() {
  local -a paquetes=("${@}")
  (( ${#paquetes[@]} == 0 )) && return 0

  local paquete
  for paquete in "${paquetes[@]}"; do
    if contiene "${paquete}" "${REPARACIONES[@]}"; then
      REPARACION_RESUELTA=true
    fi
  done

  resolver_conflictos "${paquetes[@]}"

  # Un paquete retirado en cascada puede formar parte del manifiesto, como
  # rust-analyzer cuando se retira rust. El plan ya estaba calculado cuando se
  # produjo la retirada, asi que hay que volver a anadirlo a la transaccion o
  # se quedaria fuera hasta la siguiente ejecucion.
  local retirado entrada
  for retirado in "${RETIRADOS_AHORA[@]}"; do
    entrada="pacman:${retirado}"
    if ! contiene "${entrada}" "${RESULTADOS_PRESENTES[@]}"; then
      continue
    fi
    avisar "pacman: ${retirado} se reinstala tras la retirada en cascada"
    quitar_de_presentes "${entrada}"
    paquetes+=("${retirado}")
  done

  if [[ "${BASE_REFRESCADA}" == "false" ]]; then
    refrescar_base
  fi

  if [[ "${SECO}" == "true" || "${SOLO_LISTAR}" == "true" ]]; then
    printf '  pacman: instalaria %s\n' "${paquetes[*]}"
    return 0
  fi

  registrar "pacman: instalando ${#paquetes[@]} paquetes en una transaccion"
  if sudo pacman -S --needed --noconfirm "${paquetes[@]}"; then
    for paquete in "${paquetes[@]}"; do
      RESULTADOS_INSTALADOS+=("pacman:${paquete}")
    done
    return 0
  fi

  avisar "La transaccion se aborto; se reintenta paquete por paquete"
  for paquete in "${paquetes[@]}"; do
    if sudo pacman -S --needed --noconfirm "${paquete}"; then
      RESULTADOS_INSTALADOS+=("pacman:${paquete}")
    else
      RESULTADOS_FALLIDOS+=("pacman:${paquete}")
      avisar "No se pudo instalar ${paquete}"
    fi
  done
}

# Compila paquetes del AUR de uno en uno. Un fallo de compilacion no debe
# detener el resto de la cola.
instalar_aur() {
  local gestor="${1}"
  shift
  local -a paquetes=("${@}")
  (( ${#paquetes[@]} == 0 )) && return 0

  local ayudante=""
  if command -v paru >/dev/null 2>&1; then
    ayudante="paru"
  elif command -v yay >/dev/null 2>&1; then
    ayudante="yay"
  else
    fallar "No hay ningun ayudante del AUR; instala paru o yay primero"
    return 1
  fi

  # Las compilaciones se hacen con las herramientas del sistema y no con las
  # de Homebrew. Homebrew pone sus binutils (nm, ld, ar, ranlib, strip) y su
  # libtool antes que las del sistema en el PATH, y eso rompe las
  # compilaciones de autotools: el nm de Homebrew no entiende la opcion -B,
  # la comprobacion de configure falla y libtool genera una orden con una
  # etapa de tuberia vacia.
  local path_compilacion="/usr/bin:/bin:${PATH}"

  registrar "aur: compilando ${#paquetes[@]} paquetes con ${ayudante}"
  local paquete
  for paquete in "${paquetes[@]}"; do
    if [[ "${SECO}" == "true" || "${SOLO_LISTAR}" == "true" ]]; then
      printf '  aur: compilaria %s\n' "${paquete}"
      continue
    fi
    if PATH="${path_compilacion}" \
      "${ayudante}" -S --needed --noconfirm "${paquete}"; then
      RESULTADOS_INSTALADOS+=("${gestor}:${paquete}")
    else
      RESULTADOS_FALLIDOS+=("${gestor}:${paquete}")
      avisar "No se pudo compilar ${paquete}"
    fi
  done
}

# Instala paquetes de usuario que todavia no estan presentes.
#
# Argumentos:
#   $1      - nombre del gestor, tal como aparece en el resumen
#   $2      - funcion que responde si un paquete ya esta presente
#   $3..    - comando que instala un paquete; el nombre se anade al final
instalar_paquetes_usuario() {
  local gestor="${1}"
  local esta_presente="${2}"
  shift 2
  local -a comando=("${@}")

  local -a pedidos=()
  mapfile -t pedidos < <(leer_manifiestos "${gestor}")
  (( ${#pedidos[@]} == 0 )) && return 0

  local paquete
  for paquete in "${pedidos[@]}"; do
    [[ -z "${paquete}" ]] && continue
    if "${esta_presente}" "${paquete}"; then
      RESULTADOS_PRESENTES+=("${gestor}:${paquete}")
      continue
    fi
    if [[ "${SECO}" == "true" || "${SOLO_LISTAR}" == "true" ]]; then
      printf '  %s: instalaria %s\n' "${gestor}" "${paquete}"
      continue
    fi
    registrar "${gestor}: instalando ${paquete}"
    if "${comando[@]}" "${paquete}"; then
      RESULTADOS_INSTALADOS+=("${gestor}:${paquete}")
    else
      RESULTADOS_FALLIDOS+=("${gestor}:${paquete}")
      avisar "No se pudo instalar ${paquete} con ${gestor}"
    fi
  done
}

# Separa los paquetes de pacman entre los que estan en los repositorios
# oficiales y los que hay que compilar desde el AUR.
calcular_destinos_pacman() {
  local -a pedidos=()
  mapfile -t pedidos < <(leer_manifiestos pacman)

  PAQUETES_REPO=()
  PAQUETES_AUR=()

  local paquete efectivo
  for paquete in "${pedidos[@]}"; do
    [[ -z "${paquete}" ]] && continue

    efectivo="$(nombre_efectivo "${paquete}")"
    if [[ "${efectivo}" != "${paquete}" ]]; then
      registrar "pacman: ${paquete} ahora se llama ${efectivo}"
    fi

    if esta_instalado "${efectivo}"; then
      RESULTADOS_PRESENTES+=("pacman:${efectivo}")
      continue
    fi

    if esta_en_repo "${efectivo}"; then
      PAQUETES_REPO+=("${efectivo}")
    else
      PAQUETES_AUR+=("${efectivo}")
    fi
  done
}

# Los paquetes declarados en packages/yay son del AUR por definicion.
calcular_destinos_yay() {
  local -a pedidos=()
  mapfile -t pedidos < <(leer_manifiestos yay)

  PAQUETES_YAY=()

  local paquete efectivo
  for paquete in "${pedidos[@]}"; do
    [[ -z "${paquete}" ]] && continue

    efectivo="$(nombre_efectivo "${paquete}")"
    if [[ "${efectivo}" != "${paquete}" ]]; then
      registrar "yay: ${paquete} ahora se llama ${efectivo}"
    fi

    if esta_instalado "${efectivo}"; then
      RESULTADOS_PRESENTES+=("yay:${efectivo}")
      continue
    fi

    PAQUETES_YAY+=("${efectivo}")
  done
}

instalar_pacman() {
  # El ayudante del AUR tiene que existir antes de compilar nada.
  if (( ${#PAQUETES_AUR[@]} > 0 || ${#PAQUETES_YAY[@]} > 0 )) \
    && ! command -v paru >/dev/null 2>&1 && ! command -v yay >/dev/null 2>&1; then
    PAQUETES_REPO+=("paru")
  fi
  instalar_repos "${PAQUETES_REPO[@]}"
}

instalar_yay() {
  if ! command -v paru >/dev/null 2>&1 && ! command -v yay >/dev/null 2>&1; then
    registrar "yay: no hay ayudante del AUR, se instala paru primero"
    instalar_repos "paru"
  fi
  instalar_aur yay "${PAQUETES_YAY[@]}"
}

npm_presente() { [[ -d "${NPM_GLOBAL_ROOT}/${1}" ]]; }
pipx_presente() { [[ -d "${PIPX_VENVS}/${1}" ]]; }
cargo_presente() { contiene "${1}" "${BINARIOS_CARGO[@]}"; }
flatpak_presente() { flatpak info "${1}" >/dev/null 2>&1; }

instalar_npm() {
  asegurar_node || return 0
  instalar_paquetes_usuario npm npm_presente npm install -g
}

instalar_cargo() {
  mapfile -t BINARIOS_CARGO < <(cargo install --list 2>/dev/null \
    | grep -E '^[A-Za-z0-9_-]+ v' | awk '{print $1}')
  instalar_paquetes_usuario cargo cargo_presente cargo install
}

instalar_pipx() {
  # pipx no funciona sin python-filelock, asi que el paquete de reparacion se
  # trae aqui incluso cuando este gestor va solo.
  local reparacion
  for reparacion in "${REPARACIONES[@]}"; do
    [[ "${REPARACION_RESUELTA}" == "true" ]] && break
    if ! esta_instalado "${reparacion}"; then
      instalar_repos "${reparacion}"
    fi
  done
  instalar_paquetes_usuario pipx pipx_presente pipx install
}

instalar_flatpak() {
  if ! flatpak remotes --columns=name 2>/dev/null | grep -qx "flathub"; then
    if [[ "${SECO}" == "true" || "${SOLO_LISTAR}" == "true" ]]; then
      printf '  flatpak: anadiria el remoto flathub\n'
    else
      registrar "flatpak: anadiendo el remoto flathub"
      flatpak remote-add --if-not-exists flathub \
        https://dl.flathub.org/repo/flathub.flatpakrepo
    fi
  fi
  instalar_paquetes_usuario flatpak flatpak_presente flatpak install -y flathub
}

mostrar_resumen() {
  printf '\n'
  registrar "Resumen"
  printf '  instalados: %s\n' "${#RESULTADOS_INSTALADOS[@]}"
  printf '  presentes:  %s\n' "${#RESULTADOS_PRESENTES[@]}"
  printf '  excluidos:  %s\n' "${#RESULTADOS_EXCLUIDOS[@]}"
  printf '  fallidos:   %s\n' "${#RESULTADOS_FALLIDOS[@]}"

  if [[ "${ESPOJOS_ARREGLADOS}" == "true" ]]; then
    printf '  Se antepuso el CDN oficial de CachyOS a los mirrorlist.\n'
  fi

  if (( ${#RESULTADOS_RETIRADOS[@]} > 0 )); then
    printf '\n  Paquetes retirados para resolver un conflicto:\n'
    printf '    %s\n' "${RESULTADOS_RETIRADOS[@]}"
  fi

  if (( ${#RESULTADOS_EXCLUIDOS[@]} > 0 )); then
    printf '\n  Paquetes excluidos:\n'
    printf '    %s\n' "${RESULTADOS_EXCLUIDOS[@]}"
  fi

  if (( ${#RESULTADOS_FALLIDOS[@]} > 0 )); then
    printf '\n  Paquetes que fallaron:\n'
    printf '    %s\n' "${RESULTADOS_FALLIDOS[@]}"
  fi
}

analizar_argumentos() {
  while (( $# > 0 )); do
    case "${1}" in
      --dry-run)
        SECO=true
        ;;
      --list)
        SOLO_LISTAR=true
        ;;
      --refresh)
        ACTUALIZAR_TODO=true
        ;;
      --only)
        shift
        (( $# > 0 )) || { fallar "--only necesita el nombre de un gestor"; exit 1; }
        SOLO_GESTOR="${1}"
        ;;
      -h|--help)
        uso
        exit 0
        ;;
      *)
        fallar "Opcion desconocida: ${1}"
        uso
        exit 1
        ;;
    esac
    shift
  done
}

principal() {
  analizar_argumentos "${@}"

  [[ -d "${PKG_DIR}" ]] || { fallar "No existe el directorio de paquetes: ${PKG_DIR}"; exit 1; }

  if [[ "${SOLO_GESTOR}" != "todos" ]]; then
    contiene "${SOLO_GESTOR}" "${GESTORES[@]}" \
      || { fallar "Gestor desconocido: ${SOLO_GESTOR}"; exit 1; }
  fi

  if [[ "${SECO}" == "false" && "${SOLO_LISTAR}" == "false" ]]; then
    if ! sudo -v; then
      fallar "La autenticacion de sudo ha fallado"
      exit 1
    fi
  fi

  registrar "Restaurando los paquetes de ${PKG_DIR}"

  # Los repos de CachyOS necesitan un espejo al dia. El CDN oficial se
  # antepone si el mirrorlist no lo tiene, porque los espejos de terceros van
  # con retraso y devuelven 404 para las versiones nuevas.
  asegurar_espejo /etc/pacman.d/cachyos-v3-mirrorlist "/repo/\$arch_v3/\$repo"
  asegurar_espejo /etc/pacman.d/cachyos-mirrorlist "/repo/\$arch/\$repo"

  cargar_estado
  calcular_destinos_pacman
  calcular_destinos_yay

  if en_alcance pacman; then
    instalar_pacman
  fi
  if en_alcance yay; then
    instalar_yay
  fi
  if en_alcance pacman && (( ${#PAQUETES_AUR[@]} > 0 )); then
    instalar_aur pacman "${PAQUETES_AUR[@]}"
  fi
  if en_alcance npm; then
    instalar_npm
  fi
  if en_alcance cargo; then
    instalar_cargo
  fi
  if en_alcance pipx; then
    instalar_pipx
  fi
  if en_alcance flatpak; then
    instalar_flatpak
  fi

  reportar_excluidos
  mostrar_resumen

  if (( ${#RESULTADOS_FALLIDOS[@]} > 0 )); then
    exit 1
  fi
}

principal "${@}"
