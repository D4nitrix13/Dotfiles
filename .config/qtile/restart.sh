#!/bin/sh

# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

# Keyborad Latam
# El layout de teclado es una decision de sesion: restart.sh corre en cada
# arranque y en cada reinicio de qtile, autostart.sh solo por proceso.
layout=$(/bin/setxkbmap -query | /bin/tail -n 1 | /bin/xargs | /bin/awk '{print $2}')
if [ "$layout" != "latam" ]; then
  /bin/setxkbmap latam
fi

# Delete Files
# rm -f ~/.zcompdump-asus-*
