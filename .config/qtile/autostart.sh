#!/bin/sh

# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

# Directorio de fondos de pantalla del sistema
wallpapers_dir="/usr/share/wallpapers/cachyos-wallpapers"

# Icono de bateria en la bandeja del sistema
for bat in /sys/class/power_supply/BAT*; do
  [ -d "$bat" ] && /bin/cbatticon -i standard -u 15 -l 20 -r 10 -n &
  break
done

# Tecla NumLock del teclado
# numlockx no esta instalado en todas las maquinas, se comprueba antes de usarlo
if [ -x /bin/numlockx ] && /bin/xset q | /bin/grep -iq "Num Lock: *off"; then
  /bin/numlockx on
fi

# Fondo de pantalla
# Se prueban primero los fondos propios del usuario, despues el fondo del tema
# activo (dracula) y por ultimo el primer jpg o png que haya en el sistema.
# Si no hay ninguno, el script no hace nada y no imprime ningun error.
wallpaper=""
for candidate in \
  "$HOME/Imágenes/Wallpapers/default.jpg" \
  "$HOME/Pictures/wallpapers/default.jpg" \
  "$HOME/Images/wallpapers/default.jpg" \
  "$wallpapers_dir/Dracula.png"; do
  if [ -f "$candidate" ]; then
    wallpaper="$candidate"
    break
  fi
done

if [ -z "$wallpaper" ]; then
  for candidate in "$wallpapers_dir"/*; do
    [ -f "$candidate" ] || continue
    case "$candidate" in
      *.jpg | *.png)
        wallpaper="$candidate"
        break
        ;;
    esac
  done
fi

if [ -n "$wallpaper" ]; then
  /usr/bin/feh --bg-fill "$wallpaper" >/dev/null 2>&1 &
fi

# Compositor (transparencias, sombras, redondeos)
# Un reinicio de qtile es un execv, el compositor anterior sigue vivo: se
# termina antes de arrancar el nuevo para no acumular procesos.
if /usr/bin/pgrep -x picom >/dev/null 2>&1; then
  /usr/bin/pkill -x picom >/dev/null 2>&1
  /bin/sleep 1
fi
/bin/picom --config "$HOME/.config/picom/picom.conf" &

# Interfaz de red para el widget de la barra
# Se escribe en interface.txt como override explicito. Si no se puede detectar,
# no se escribe nada y no se rompe nada.
interface=$(/usr/bin/ip route get 1.1.1.1 2>/dev/null | /bin/awk '{for (i = 1; i < NF; i++) if ($i == "dev") {print $(i + 1); exit}}')

if [ -z "$interface" ]; then
  for candidate in /sys/class/net/*; do
    [ -e "$candidate" ] || continue
    name=${candidate##*/}
    if [ "$name" != "lo" ]; then
      interface="$name"
      break
    fi
  done
fi

if [ -n "$interface" ] && [ -d "$HOME/.config/qtile" ]; then
  printf '%s\n' "$interface" > "$HOME/.config/qtile/interface.txt" 2>/dev/null
fi

# Icono de volumen en la bandeja del sistema
# volumeicon &
