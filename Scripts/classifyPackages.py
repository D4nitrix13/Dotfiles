#!/usr/bin/env python3
"""Clasifica los manifiestos de paquetes por categoria y los escribe.

Lee un manifiesto plano por gestor, decide a que categoria pertenece cada
paquete segun las reglas declaradas en REGLAS, y escribe un archivo por
categoria dentro de packages/<gestor>/.

Uso:
    Scripts/classifyPackages.py --split <directorio>  Reparte un manifiesto plano
                                                      en archivos por categoria.
    Scripts/classifyPackages.py --sync               Regenera los manifiestos
                                                      agregados por gestor.
    Scripts/classifyPackages.py --verify              Comprueba que el agregado
                                                      coincide con las categorias.

Los archivos por categoria son la fuente de verdad. El manifiesto agregado de
cada gestor (packages/<gestor>/installed.txt) se deriva de ellos con --sync,
de modo que no puede desincronizarse: si alguien anade un paquete a una
categoria y ejecuta --sync, el agregado lo recoge.

El modo --split realiza el reparto inicial a partir de un manifiesto plano y
sirve para volver a clasificar en bloque cuando cambian las reglas.

Cuando un paquete no encaja en ninguna regla va a la categoria
'utilidades-varias', y el script avisa al final para que se revise a mano.

Los paquetes que no existen en ningun repositorio se apartan a
packages/pacman/excluidos/no-disponibles.txt.

Los tres paquetes de Omarchy (omarchy-keyring, omarchy-nvim y omarchy-walker)
no figuran en ningun manifiesto: su repositorio no esta configurado en CachyOS
simple y no existen ni en los repositorios oficiales ni en el AUR. La razon de
que no se instalen queda registrada en docs/auditoria-2026-10-24.md.

Autor: Daniel Benjamin Perez Morales
GitHub: https://github.com/D4nitrix13
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAQUETES_DIR = REPO / "packages"

GESTORES = ("pacman", "yay", "npm", "cargo", "pipx", "flatpak")

# Paquetes que se eliminaron de todos los repositorios y no se pueden instalar.
NO_DISPONIBLES = ("asdcontrol", "tobi-try")

# Paquetes renombrados aguas arriba: nombre antiguo -> nombre actual.
RENOMBRADOS = {
    "hyprland-preview-share-picker": "hyprland-preview-share-picker-git",
}

# El comando con el que se instala cada gestor, para la cabecera de los archivos.
COMANDOS = {
    "pacman": "sudo pacman -S --needed",
    "yay": "yay -S --needed",
    "npm": "npm install -g",
    "cargo": "cargo install",
    "pipx": "pipx install",
    "flatpak": "flatpak install -y flathub",
}

DESCRIPCIONES = {
    "kernels-firmware-y-arranque": "Kernels de CachyOS, firmware, initramfs y arranque del sistema.",
    "configuracion-cachyos": "Paquetes propios de CachyOS: ajustes, espejo, temas y herramientas de la distribucion.",
    "almacenamiento-y-sistemas-de-archivos": "Herramientas de discos, sistemas de archivos, cifrado, LVM y RAID.",
    "red-y-conectividad": "Conexion, DNS, Bluetooth, VPN, servidores y transferencia de archivos en red.",
    "seguridad-y-aislamiento": "Gestores de contrasenas, cortafuegos, aislamiento de procesos y control parental.",
    "escritorio-gnome": "GNOME, sus aplicaciones, portales de escritorio, temas e iconos.",
    "wayland-hyprland": "Hyprland, su ecosistema Wayland, barras, portales y utilidades del compositor.",
    "x11-y-qtile": "Servidor X11, Xorg y las herramientas de linea de comandos que usa Qtile.",
    "audio": "ALSA, PipeWire, WirePlumber, mezcladores y reproductores de audio.",
    "video-y-multimedia": "Reproduccion, edicion, imagen y streaming multimedia.",
    "edicion-y-lectura": "Oficina, visores de PDF, diccionarios, OCR y conversion de documentos.",
    "navegadores-y-comunicacion": "Navegadores web, correo y clientes de mensajeria.",
    "desarrollo-y-editores": "Editores, servidores de lenguaje, depuradores y herramientas de desarrollo.",
    "lenguajes-y-runtimes": "Interpreters, compiladores y gestores de versiones de los lenguajes usados.",
    "herramientas-de-construccion": "Compilacion, empaquetado y las herramientas base para construir software.",
    "contenedores-y-virtualizacion": "Contenedores, orquestadores, maquinas virtuales y emulacion.",
    "bases-de-datos": "Motores de base de datos y sus clientes.",
    "nube-y-devops": "Infraestructura como codigo, despliegue y operacion en la nube.",
    "terminal-y-cli": "Emuladores de terminal, paginadores y utilidades de linea de comandos.",
    "monitorizacion-y-diagnostico": "Medicion de recursos, hardware y diagnostico del sistema.",
    "fuentes": "Tipografias de sistema, de terminal y de interfaz grafica.",
    "impresion-y-dispositivos": "Impresoras, escaneres, Bluetooth, USB y dispositivos concretos.",
    "energia-y-hardware": "Gestion de energia, brillo y hardware grafico basico.",
    "juegos-y-graficos": "Controladores graficos, Vulkan, OpenCL, Wine y juegos.",
    "sistema-y-mantenimiento": "Mantenimiento base del sistema, utilidades core y actualizacion de paquetes.",
    "teclado-y-entradas": "Metodos de entrada, distribucion de teclado y peripherals.",
    "shell-zsh": "El interprete zsh con su gestor de plugins y los complementos que activan el resaltado, el autosuggest y la busqueda en el historial.",
    "mensajeria": "Clientes de mensajeria de escritorio.",
    "utilidades-varias": "Paquetes sin una categoria mas especifica; revisar y reubicar.",
    "editores-y-servidores-de-lenguaje": "Servidores de lenguaje y herramientas de edicion instaladas con npm.",
    "herramientas-y-servidores": "Utilidades de desarrollo instaladas con npm.",
    "terminal-y-multiplicadores": "Multiplicadores de terminal y editores de sesiones.",
    "calidad-de-codigo": "Analizadores estaticos y verificadores de tipos.",
    "entornos-y-gestores": "Entornos virtuales y gestores de dependencias de Python.",
    "terminal-interactivo": "Interpretadores interactivos de Python.",
    "criptografia": "Utilidades de cifrado y gestion de secretos.",
    "utilidades-de-red": "Aplicaciones de red instaladas como Flatpak.",
    "mensajeria": "Clientes de mensajeria de escritorio instalados como Flatpak.",
    "editores-y-escritorio": "Editores y componentes de escritorio del AUR.",
    "contrasenas-y-seguridad": "Gestores de contrasenas disponibles en el AUR.",
    "utilidades-y-terminal": "Utilidades graficas y de terminal disponibles en el AUR.",
    "red-y-devops": "Herramientas de red, observabilidad y desarrollo del AUR.",
    "impresion-y-otros": "Soporte de impresoras y paquetes sin uso claro.",
}

# Descripciones que solo se aplican a un gestor, cuando el mismo nombre de
# categoria significa otra cosa en otro gestor.
DESCRIPCIONES_POR_GESTOR = {
    "pipx": {},
}


def descripcion_de(categoria: str, gestor: str) -> str:
    """Devuelve la descripcion de una categoria, segun el gestor."""
    propia = DESCRIPCIONES_POR_GESTOR.get(gestor, {}).get(categoria)
    if propia:
        return propia
    return DESCRIPCIONES.get(categoria, "Paquetes agrupados por categoria.")


# Las reglas se evaluan en orden: gana la primera que coincide.
REGLAS: dict[str, list[tuple[str, list[str]]]] = {
    "pacman": [
        ("kernels-firmware-y-arranque", [
            r"^linux-cachyos", r"^linux-firmware", r"^mkinitcpio", r"^grub", r"^os-prober",
            r"^efibootmgr", r"^efitools", r"^kernel-modules-hook", r"^plymouth",
            r"^cachyos-plymouth", r"^cachyos-kernel-manager", r"^cachyos-keyring",
            r"^cachyos-hooks", r"^cachyos-grub-theme", r"^cachyos-mirrorlist",
            r"^cachyos-v3-mirrorlist", r"^cachyos-v4-mirrorlist", r"^cachyos-rate-mirrors",
            r"^amd-ucode", r"^fwupd", r"^sof-firmware",
        ]),
        ("configuracion-cachyos", [r"^cachyos-"]),
        ("almacenamiento-y-sistemas-de-archivos", [
            r"^btrfs-progs", r"^e2fsprogs", r"^f2fs-tools", r"^exfatprogs", r"^nilfs-utils",
            r"^dosfstools", r"^jfsutils", r"^mtools", r"^lvm2", r"^cryptsetup",
            r"^device-mapper", r"^mdadm", r"^dmraid", r"^hdparm", r"^smartmontools",
            r"^ntfs-3g", r"^lzip", r"^7zip", r"^unrar", r"^unshield", r"^file-roller",
            r"^fsarchiver", r"^xfsprogs", r"^libarchive", r"^squashfs-tools", r"^gptfdisk",
        ]),
        ("red-y-conectividad", [
            r"^bind", r"^bluez", r"^iwd", r"^wpa_supplicant", r"^openssh", r"^networkmanager",
            r"^nm-connection-editor", r"^netctl", r"^iperf3", r"^nmap", r"^arp-scan",
            r"^ethtool", r"^inetutils", r"^net-tools", r"^socat", r"^dnsmasq", r"^samba",
            r"^nfs-utils", r"^rsync", r"^wget", r"^whois", r"^xl2tpd", r"^nss-mdns",
            r"^modemmanager", r"^vsftpd", r"^caddy", r"^cloudflared", r"^localsend",
            r"^gping", r"^s-nail", r"^iputils", r"^avahi",
        ]),
        ("seguridad-y-aislamiento", [
            r"^1password", r"^keepassxc", r"^gnome-keyring", r"^ufw", r"^polkit",
            r"^sudo", r"^firejail", r"^malcontent", r"^orca", r"^seatd", r"^libpwquality",
            r"^pam", r"^ly$",
        ]),
        ("escritorio-gnome", [
            r"^gnome-", r"^gdm", r"^gvfs-", r"^xdg-desktop-portal-gnome", r"^nautilus",
            r"^dconf", r"^yelp", r"^gjs", r"^gtk3", r"^gtk4", r"^libadwaita", r"^mutter",
            r"^glib2", r"^pango", r"^cairo", r"^gdk-pixbuf", r"^gobject-introspection",
            r"^xdg-user-dirs", r"^xdg-utils", r"^baobab", r"^decibels", r"^loupe",
            r"^sushi", r"^thunar", r"^papers", r"^papirus-icon-theme", r"^yaru-icon-theme",
            r"^kvantum-qt5", r"^rofi", r"^nwg-look", r"^nwg-displays", r"^cbatticon",
            r"^mousetweaks", r"^sddm", r"^aether", r"^xournalpp", r"^xwayland",
        ]),
        ("wayland-hyprland", [
            r"^hyprland", r"^hypr", r"^waybar", r"^swaybg", r"^swayosd", r"^quickshell",
            r"^wl-clipboard", r"^wlr-randr", r"^wlroots", r"^xdg-terminal-exec",
            r"^wayland", r"^qt5-wayland", r"^mako", r"^grim", r"^slurp", r"^swappy",
            r"^uwsm", r"^impala", r"^xdg-desktop-portal-hyprland",
        ]),
        ("x11-y-qtile", [
            r"^xorg-", r"^xclip", r"^xset", r"^xterm", r"^xsel", r"^xprop", r"^xdpyinfo",
            r"^xrandr", r"^picom", r"^feh", r"^i3lock", r"^xhost", r"^xauth", r"^xinit",
            r"^xkbcomp", r"^scrot", r"^evtest", r"^xmodmap",
        ]),
        ("audio", [
            r"^alsa-", r"^pipewire", r"^wireplumber", r"^playerctl", r"^pavucontrol",
            r"^pulseaudio", r"^libpulse", r"^jack", r"^easyeffects", r"^pamixer",
            r"^mpv-mpris", r"^gst-", r"^gstreamer", r"^espeak-ng", r"^libao", r"^sndio",
            r"^sox", r"^wiremix",
        ]),
        ("video-y-multimedia", [
            r"^ffmpeg", r"^ffprobe", r"^mpv$", r"^vlc", r"^obs-studio", r"^kdenlive",
            r"^showtime", r"^pinta", r"^optiimage", r"^gifsicle", r"^jpegoptim",
            r"^pngquant", r"^optipng", r"^imv$", r"^imagemagick", r"^libraw",
            r"^libopenraw", r"^gpu-screen-recorder", r"^webcam", r"^libdvdcss",
            r"^libgsf", r"^grilo-", r"^rygel", r"^spotify", r"^cliamp",
            r"^flameshot", r"^satty",
        ]),
        ("edicion-y-lectura", [
            r"^libreoffice", r"^evince", r"^typora", r"^obsidian", r"^zathura",
            r"^okular", r"^pandoc", r"^hunspell", r"^hyphen-", r"^aspell", r"^poppler",
            r"^pdfgrep", r"^groff", r"^antiword", r"^catdoc", r"^tesseract", r"^ghostscript",
        ]),
        ("navegadores-y-comunicacion", [
            r"^firefox", r"^chromium", r"^epiphany", r"^signal-desktop", r"^thunderbird",
            r"^filezilla", r"^zoom", r"^telegram", r"^element",
        ]),
        ("desarrollo-y-editores", [
            r"^neovim", r"^vim$", r"^emacs", r"^visual-studio-code", r"^vscode-",
            r"^rust-analyzer", r"^marksman", r"^lua-language-server", r"^bash-language-server",
            r"^dockerfile-language-server", r"^eslint", r"^prettier", r"^shfmt",
            r"^shellcheck", r"^stylua", r"^taplo-cli", r"^yaml-language-server",
            r"^nano", r"^micro$", r"^meld", r"^lldb", r"^mypy", r"^pyright", r"^gum$",
            r"^github-cli", r"^claude-code", r"^ollama", r"^ty$", r"^tree-sitter-cli",
            r"^xmlstarlet", r"^xmllint", r"^shelly$", r"^paru$", r"^yay$",
        ]),
        ("lenguajes-y-runtimes", [
            r"^python", r"^pyenv", r"^ruby", r"^php", r"^perl", r"^lua$", r"^luarocks",
            r"^lua-lpeg", r"^lua-luv", r"^r$", r"^dotnet", r"^jdk", r"^jre", r"^npm$",
            r"^pnpm", r"^deno", r"^mise", r"^nodejs", r"^composer", r"^raku", r"^scala",
            r"^groovy", r"^haskell", r"^ghc", r"^cabal", r"^stack", r"^elixir",
            r"^rustup", r"^uv$",
        ]),
        ("herramientas-de-construccion", [
            r"^cmake", r"^gcc-fortran", r"^make$", r"^ninja", r"^meson", r"^autoconf",
            r"^automake", r"^libtool", r"^pkgconf", r"^m4", r"^bison", r"^flex",
            r"^gettext", r"^intltool", r"^patch", r"^git$", r"^base-devel",
        ]),
        ("contenedores-y-virtualizacion", [
            r"^docker", r"^podman", r"^buildah", r"^kubectl", r"^kind$", r"^minikube",
            r"^qemu", r"^kvm", r"^libvirt", r"^virt-manager", r"^cri-o", r"^runc",
            r"^skopeo", r"^umoci", r"^lxc", r"^containerd", r"^parsec-bin",
        ]),
        ("bases-de-datos", [
            r"^postgresql", r"^mariadb", r"^valkey", r"^redis", r"^sqlite", r"^mysql",
            r"^mongodb", r"^libpq", r"^unixodbc",
        ]),
        ("nube-y-devops", [
            r"^aws-", r"^terraform", r"^ansible", r"^helm", r"^vagrant", r"^packer",
            r"^consul", r"^vault", r"^nomad", r"^doctl", r"^k9s", r"^dagger",
        ]),
        ("terminal-y-cli", [
            r"^foot", r"^ghostty", r"^kitty", r"^alacritty", r"^wezterm", r"^tmux",
            r"^fzf", r"^bat", r"^eza", r"^lsd", r"^zoxide", r"^starship", r"^atuin",
            r"^ripgrep", r"^fd$", r"^jq", r"^yq", r"^httpie", r"^tree$", r"^tealdeer",
            r"^navi", r"^procs", r"^dust", r"^duf", r"^dua-cli", r"^btop", r"^fastfetch",
            r"^lazygit", r"^lazydocker", r"^nushell", r"^less$", r"^pv$", r"^bc$",
            r"^libqalculate", r"^plocate", r"^task$", r"^timew",
        ]),
        ("monitorizacion-y-diagnostico", [
            r"^htop", r"^glances", r"^stress-ng", r"^hwdetect", r"^hwinfo", r"^lshw",
            r"^iotop", r"^powertop", r"^nvtop", r"^bottom", r"^calcurse", r"^usage$",
            r"^cpupower", r"^dmidecode", r"^lsscsi", r"^sg3_utils", r"^chwd$",
            r"^smartmontools", r"^pkgfile", r"^sysfsutils", r"^snapshot",
        ]),
        ("fuentes", [
            r"^ttf-", r"^noto-fonts", r"^awesome-terminal-fonts", r"^cantarell-fonts",
            r"^gsfonts", r"^woff2-", r"^adobe-", r"^font-", r"^xfonts",
        ]),
        ("impresion-y-dispositivos", [
            r"^cups", r"^hplip", r"^foomatic", r"^system-config-printer", r"^bluez-utils",
            r"^blueman", r"^bluetui", r"^usbutils", r"^usb_modeswitch", r"^simple-scan",
            r"^sane", r"^hpijs", r"^libusb", r"^android-tools", r"^ipp-usb", r"^gutenprint",
            r"^bolt$", r"^avahi", r"^tecla",
        ]),
        ("energia-y-hardware", [
            r"^brightnessctl", r"^power-profiles-daemon", r"^upower", r"^acpid",
            r"^tlp$", r"^libinput", r"^mesa$", r"^xorg-server",
        ]),
        ("juegos-y-graficos", [
            r"^lib32-mesa", r"^vulkan", r"^lib32-vulkan", r"^opencl-mesa", r"^lib32-opencl",
            r"^mesa-utils", r"^wine", r"^winetricks", r"^gamemode", r"^mangohud",
            r"^dxvk", r"^vkd3d", r"^xf86-video-amdgpu", r"^x264", r"^x265",
        ]),
        ("sistema-y-mantenimiento", [
            r"^logrotate", r"^man-db", r"^man-pages", r"^pacman-contrib", r"^which$",
            r"^file$", r"^findutils", r"^gawk", r"^grep$", r"^sed$", r"^procps-ng",
            r"^psmisc", r"^util-linux", r"^coreutils", r"^diffutils", r"^tar$", r"^gzip",
            r"^bzip2", r"^xz$", r"^zstd", r"^ca-certificates", r"^systemd", r"^dbus",
            r"^accountsservice", r"^hwdata", r"^pciutils", r"^rebuild-detector",
            r"^reflector", r"^bash-completion", r"^lsb-release", r"^texinfo", r"^unzip",
            r"^tzupdate", r"^base$",
        ]),
        ("teclado-y-entradas", [
            r"^fcitx5", r"^xsel$", r"^ibus",
        ]),
        ("shell-zsh", [
            r"^zsh$", r"^zsh-", r"^oh-my-zsh-git$",
        ]),
        ("mensajeria", [
            r"^discord$",
        ]),
    ],
    "yay": [
        ("editores-y-escritorio", [
            r"^visual-studio-code-bin", r"^typora", r"^ttf-", r"^yaru-", r"^rstudio",
        ]),
        ("contrasenas-y-seguridad", [r"^1password"]),
        ("utilidades-y-terminal", [
            r"^aether$", r"^cliamp$", r"^python-terminaltexteffects", r"^ptpython$",
            r"^wlroots-asan-git", r"^monique$",
        ]),
        ("red-y-devops", [
            r"^k6$", r"^hadolint-bin", r"^mailpit-bin", r"^redisinsight-bin",
            r"^python-pyodbc", r"^mdbtools", r"^freelens-bin", r"^ryzenadj",
        ]),
        ("impresion-y-otros", [r"^epson-inkjet"]),
    ],
    "npm": [
        ("editores-y-servidores-de-lenguaje", [
            r"^@astrojs/language-server$", r"^@microsoft/compose-language-service$",
            r"^@vtsls/language-server$", r"^emmet-ls$", r"^intelephense$",
            r"^typescript-language-server$", r"^markdownlint-cli$",
        ]),
        ("herramientas-y-servidores", [
            r"^@colbymchenry/codegraph$", r"^@playwright/cli$", r"^prettier-plugin-astro$",
            r"^serve$", r"^typescript$",
        ]),
    ],
    "cargo": [
        ("terminal-y-multiplicadores", [r"^zellij$"]),
        ("utilidades", [r"^tokei$", r"^vtracer$"]),
    ],
    "pipx": [
        ("calidad-de-codigo", [r"^mypy$"]),
        ("entornos-y-gestores", [r"^pipenv$", r"^uv$"]),
        ("terminal-interactivo", [r"^ptpython$"]),
        ("criptografia", [r"^pycrypy$"]),
    ],
    "flatpak": [
        ("utilidades-de-red", [r"^es\.danirod\.Cartero$"]),
        ("mensajeria", [r"^com\.rtosta\.zapzap$"]),
    ],
}

CABECERA = """\
# {titulo}
# {descripcion}
#
# Categoria: {categoria}
# Paquetes: {total}
#
# Instalables con: {comando} {muestra}
"""

CABECERA_NO_DISPONIBLES = """\
# Paquetes no disponibles
# Se eliminaron de los repositorios oficiales y del AUR, por lo que no se pueden instalar.
#
# Se conservan aqui como registro de lo que habia en la instalacion anterior.
#
# Paquetes: 2
#
"""


def clasificar(paquete: str, gestor: str) -> str:
    """Devuelve la categoria de un paquete dentro de un gestor."""
    for categoria, patrones in REGLAS[gestor]:
        for patron in patrones:
            if re.match(patron, paquete):
                return categoria
    return "utilidades-varias"


def leer_manifiesto(ruta: Path) -> list[str]:
    """Lee un manifiesto plano ignorando comentarios y lineas vacias."""
    if not ruta.exists():
        return []
    lineas = []
    for linea in ruta.read_text().splitlines():
        limpia = linea.strip()
        if limpia and not limpia.startswith("#"):
            lineas.append(limpia)
    return lineas


def escribir_categoria(ruta: Path, categoria: str, paquetes: list[str], gestor: str) -> None:
    """Escribe un archivo de categoria con su cabecera."""
    muestra = " ".join(paquetes[:3]) + (" ..." if len(paquetes) > 3 else "")
    cabecera = CABECERA.format(
        titulo=categoria.replace("-", " ").capitalize(),
        descripcion=descripcion_de(categoria, gestor),
        categoria=categoria,
        total=len(paquetes),
        comando=COMANDOS[gestor],
        muestra=muestra,
    )
    ruta.write_text(cabecera + "\n".join(sorted(paquetes)) + "\n")


def clasificar_gestor(gestor: str, manifiesto: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    """Reparte los paquetes de un gestor en categorias."""
    categorias: dict[str, list[str]] = {}
    sin_resolver: list[str] = []
    for paquete in manifiesto:
        if paquete in NO_DISPONIBLES:
            continue
        categoria = clasificar(paquete, gestor)
        if categoria == "utilidades-varias" and not any(
            re.match(p, paquete) for _, patrones in REGLAS[gestor] for p in patrones
        ):
            sin_resolver.append(paquete)
        categorias.setdefault(categoria, []).append(paquete)
    return categorias, sin_resolver


def ejecutar_clasificacion(origen: Path) -> int:
    """Clasifica los manifiestos planos de un directorio y escribe el resultado."""
    fallos = 0
    for gestor in GESTORES:
        manifiesto = leer_manifiesto(origen / gestor / "installed.txt")
        if not manifiesto:
            print(f"  {gestor}: sin manifiesto en {origen / gestor / 'installed.txt'}")
            continue

        categorias, sin_resolver = clasificar_gestor(gestor, manifiesto)
        destino = PAQUETES_DIR / gestor
        destino.mkdir(parents=True, exist_ok=True)
        for viejo in destino.glob("*.txt"):
            viejo.unlink()
        for categoria, paquetes in categorias.items():
            escribir_categoria(destino / f"{categoria}.txt", categoria, paquetes, gestor)

        written = sorted(p for p in destino.glob("*.txt"))
        suma: list[str] = []
        for archivo in written:
            suma.extend(leer_manifiesto(archivo))
        esperado = [p for p in manifiesto if p not in NO_DISPONIBLES]
        ok = sorted(suma) == sorted(esperado)
        print(f"  {gestor:8} {len(manifiesto):4} paquetes -> {len(written)} categorias "
              f"[{'OK' if ok else 'DISCREPANCIA'}]")
        if not ok:
            fallos += 1
            print(f"    faltan: {sorted(set(esperado) - set(suma))}")
            print(f"    sobran:  {sorted(set(suma) - set(esperado))}")
        if sin_resolver:
            print(f"    sin regla, van a utilidades-varias: {sin_resolver}")

    excluidos = PAQUETES_DIR / "pacman" / "excluidos"
    excluidos.mkdir(parents=True, exist_ok=True)
    (excluidos / "no-disponibles.txt").write_text(
        CABECERA_NO_DISPONIBLES + "asdcontrol\ntobi-try\n"
    )
    return fallos


def paquetes_de_categorias(gestor: str) -> list[str]:
    """Devuelve la union de los paquetes de todas las categorias de un gestor."""
    suma: list[str] = []
    for archivo in sorted((PAQUETES_DIR / gestor).glob("*.txt")):
        if archivo.name == "installed.txt":
            continue
        suma.extend(leer_manifiesto(archivo))
    return suma


def reescribir_cabecera(gestor: str, ruta: Path, paquetes: list[str]) -> None:
    """Reescribe la cabecera de un archivo de categoria a partir de su cuerpo."""
    cabecera = CABECERA.format(
        titulo=ruta.stem.replace("-", " ").capitalize(),
        descripcion=descripcion_de(ruta.stem, gestor),
        categoria=ruta.stem,
        total=len(paquetes),
        comando=COMANDOS[gestor],
        muestra=" ".join(paquetes[:3]) + (" ..." if len(paquetes) > 3 else ""),
    )
    ruta.write_text(cabecera + "\n".join(sorted(paquetes)) + "\n")


def ejecutar_sincronizacion() -> int:
    """Regenera las cabeceras y el manifiesto agregado de cada gestor."""
    fallos = 0
    for gestor in GESTORES:
        for archivo in sorted((PAQUETES_DIR / gestor).glob("*.txt")):
            if archivo.name == "installed.txt":
                continue
            paquetes = leer_manifiesto(archivo)
            reescribir_cabecera(gestor, archivo, paquetes)
        paquetes = paquetes_de_categorias(gestor)
        if not paquetes:
            continue
        destino = PAQUETES_DIR / gestor / "installed.txt"
        cabecera = (
            f"# Manifiesto agregado de {gestor}\n"
            "#\n"
            "# Este archivo NO se edita a mano. Se genera desde los archivos por\n"
            "# categoria con: Scripts/classifyPackages.py --sync\n"
            "#\n"
            f"# Paquetes: {len(paquetes)}\n"
            "#\n"
        )
        destino.write_text(cabecera + "\n".join(sorted(paquetes)) + "\n")
        print(f"  {gestor:8} {len(paquetes):4} paquetes agregados")
    return fallos


def ejecutar_verificacion() -> int:
    """Comprueba que el agregado coincide con la union de las categorias."""
    fallos = 0
    for gestor in GESTORES:
        paquetes = paquetes_de_categorias(gestor)
        if not paquetes:
            continue
        agregado = leer_manifiesto(PAQUETES_DIR / gestor / "installed.txt")
        ok = sorted(agregado) == sorted(paquetes)
        print(f"  {gestor:8} {len(paquetes):4} paquetes en categorias, "
              f"{len(agregado):4} en el agregado [{'OK' if ok else 'DISCREPANCIA'}]")
        if not ok:
            fallos += 1
            print(f"    faltan: {sorted(set(paquetes) - set(agregado))}")
            print(f"    sobran:  {sorted(set(agregado) - set(paquetes))}")
    return fallos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--split", type=Path, metavar="DIR",
                       help="directorio con los manifiestos planos por gestor")
    grupo.add_argument("--verify", action="store_true",
                       help="comprueba que el agregado coincide con las categorias")
    grupo.add_argument("--sync", action="store_true",
                       help="regenera los manifiestos agregados por gestor")
    args = parser.parse_args()

    if args.verify:
        print("Verificando la cobertura de las categorias:")
        return 1 if ejecutar_verificacion() else 0

    if args.sync:
        print("Regenerando los manifiestos agregados:")
        return 1 if ejecutar_sincronizacion() else 0

    print(f"Clasificando los manifiestos de {args.split}:")
    fallos = ejecutar_clasificacion(args.split)
    if not fallos:
        print("Regenerando los manifiestos agregados:")
        fallos = ejecutar_sincronizacion()
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
