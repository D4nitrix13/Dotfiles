#!/bin/sh

# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

userresources=$HOME/.Xresources
usermodmap=$HOME/.Xmodmap
sysresources=/etc/X11/xinit/.Xresources
sysmodmap=/etc/X11/xinit/.Xmodmap

# Path

# Linuxbrew
# Se coloca al final del PATH a proposito. Homebrew antepone sus binutils
# (nm, ld, ar, ranlib, strip, objcopy) a los del sistema, y eso rompe las
# compilaciones de autotools: el nm de Homebrew no entiende la opcion -B, la
# comprobacion de configure falla y libtool genera una orden con una etapa de
# tuberia vacia. El interprete de Python del sistema trae el mismo numpy y el
# mismo pip, de modo que no se pierde nada al moverlo.
export PATH="$PATH:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin"

# Composer Path
export PATH="$HOME/.config/composer/vendor/bin:$PATH"

# If you come from bash you might have to change your $PATH.
export PATH="$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH"

# Rustup
export PATH="$PATH:$HOME/.rustup/toolchains/stable-x86_64-unknown-linux-gnu/bin"

# Luaenv
export PATH="$HOME/.luaenv/bin:$HOME/.luaenv/shims:$PATH"

# Pyenv
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
[[ -d $PYENV_ROOT/shims ]] && export PATH="$PYENV_ROOT/shims:$PATH"

# Perl
export PATH="/usr/bin/core_perl:$PATH"
export PATH="/usr/bin/site_perl:$PATH"
export PATH="/usr/bin/vendor_perl:$PATH"

# Java Virtual Machine - Jvm
export PATH="/usr/lib/jvm/default/bin:$PATH"

# Sbin
export PATH="/usr/local/sbin:$PATH"

# Cargo Binary

# Ls Colors
export LS_COLORS="di=38;5;67:ow=48;5;60:ex=38;5;132:ln=38;5;144:*.tar=38;5;180:*.zip=38;5;180:*.jpg=38;5;175:*.png=38;5;175:*.mp3=38;5;175:*.wav=38;5;175:*.txt=38;5;223:*.sh=38;5;132"

# Qt
export QT_QPA_PLATFORMTHEME=qt6ct
export QT_STYLE_OVERRIDE=kvantum
# export QT_STYLE_OVERRIDE=kvantum

# Language
# export LANG=es_ES.UTF-8
# export LANGUAGE=es_ES.UTF-8

# Ruby Gem
export PATH="$HOME/.local/share/gem/ruby/3.4.0/bin:$PATH"

# Scripts
export PATH="$HOME/Scripts:$PATH"

# merge in defaults and keymaps

if [ -f $sysresources ]; then
  /bin/xrdb -merge $sysresources
fi

if [ -f $sysmodmap ]; then
  /bin/xmodmap $sysmodmap
fi

if [ -f "$userresources" ]; then
  /bin/xrdb -merge "$userresources"
fi

if [ -f "$usermodmap" ]; then
  /bin/xmodmap "$usermodmap"
fi

# start some nice programs

if [ -d /etc/X11/xinit/xinitrc.d ]; then
  for f in /etc/X11/xinit/xinitrc.d/?*.sh; do
    [ -x "$f" ] && . "$f"
  done
  unset f
fi

# Composer
if [[ $DESKTOP_SESSION == "bspwm" ]]; then
  /bin/picom --config ~/.config/picom/bspwm/picom.conf &
else
  /bin/picom &
fi

# Network
/bin/nm-applet &

# Notify
/bin/dunst &

# Keyboard Layout
# /bin/setxkbmap latam &

# Screens
/bin/xrandr --output DVI-D-0 --off --output HDMI-0 --primary --mode 1920x1080 --pos 0x0 --rotate normal --output DP-0 --off --output DP-1 --off --output HDMI-1 --off

# Automount Devices
/bin/udiskie -t &

# Background image
/bin/feh --bg-scale "$($HOME/Scripts/getRandomBackground.sh)"

# Audio
# /bin/pulseaudio --start

# Get Active Network Interface
/bin/ip -o -4 addr show | /bin/awk '{print $2}' | /bin/grep -E '^(enp|wlp|wlan).*' --color=none | /bin/tee ~/.config/qtile/interface.txt >/dev/null

# Launch xautolock to automatically lock the screen after 15 minutes of inactivity.
# It uses a custom script located at ~/Scripts/lock to perform the actual lock.
# The -detectsleep option prevents locking immediately after system sleep/resume.
/bin/xautolock -time 15 -locker "~/Scripts/lock" -detectsleep &
. "$HOME/.cargo/env"
