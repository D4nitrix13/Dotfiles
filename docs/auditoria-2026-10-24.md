# Auditoría del sistema y del repositorio dotfiles

**Fecha:** 2026-10-24  
**Ámbito:** `/home/d4nitrix13` (raíz del repositorio y `$HOME`)  
**Propósito:** inventario, riesgos, redundancias y plan de preparación para una reinstalación limpia de CachyOS sin Omarchy.

> Este documento es una auditoría y un plan. No se eliminó, movió ni renombró ningún archivo existente. Los cambios realizados se limitan a remediación aditiva, manifiestos regenerados y las exclusiones solicitadas en `.gitignore`.

## Ruta rápida

1. **Rotar la credencial expuesta** de `.config/opencode/service.json` y el token de Fly.io en `Docs/notas/server.md`.
2. **Restaurar la mitigación térmica** desde `Utils/systemd/cpufreq-stabilize.sh` y `Utils/systemd/cpufreq-stabilize.service`.
3. **Conservar el reemplazo portable del brillo** en `Utils/scripts/display-brightness` antes de reinstalar Omarchy.
4. **Aplicar el nuevo particionado** y un swap en disco de 8 GiB conservando zram.
5. **Convertir Hyprland, Waybar y el lanzador** para que no dependan de los globales y scripts de Omarchy.

## 1. Resumen ejecutivo

### Estado general

El equipo funciona, pero se acumula una combinación de tres riesgos que no conviene arrastrar a una instalación nueva:

| Prioridad | Hallazgo | Impacto | Acción recomendada |
|---|---|---|---|
| P0 | La mitigación térmica del 2026-10-20 se perdió: no existe el script ni la unidad systemd, los 16 CPU están en `performance`, EPP `performance`, límite 4.55 GHz y `thermal_zone0` marca 81 °C en reposo. | El EC de Dell corta la energía al acercarse a 95 °C, sin dejar registro del kernel. | Instalar y activar el servicio versionado; limpiar el disipador y cambiar la pasta térmica. |
| P0 | `.config/opencode/service.json` contiene una contraseña en texto plano. No está versionado ni aparece en el historial, pero tampoco estaba ignorado. | Un `git add -A` podía publicarlo. | Rotar la contraseña, conservarla en un gestor de secretos y mantener el archivo ignorado. |
| P0 | Hyprland depende de `default.hypr.omarchy`, de los globales `hl`/`o` y de numerosos binarios `omarchy-*`. | Sin Omarchy, Hyprland no carga la configuración actual: no hay keybindings ni configuración de monitores. | Convertir la capa a `hyprland.conf` y enlaces Wayland portables antes de desinstalar Omarchy. |
| P1 | `/` está al 97 %: 54 GB usados y 2.1 GB libres; `/home` tiene 63 GB usados y 54 GB libres. | Las actualizaciones de kernel y paquetes pueden fallar por falta de espacio. | Reinstalar con `/` de 100 GiB, `/home` de 350 GiB y 18 GiB sin asignar. |
| P1 | La configuración portable de brillo todavía depende de un hook no versionado de Omarchy. | Al borrar Omarchy se pierde el workaround del DMUB. | Usar `Utils/scripts/display-brightness`; ya está incorporado en este repositorio. |

### Orden de ejecución recomendado

1. Rotar secretos y proteger el remoto.
2. Recuperar el control térmico y verificar la temperatura en reposo.
3. Instalar el script portable de brillo y probarlo antes de retirar Omarchy.
4. Tomar una copia de seguridad verificada de `/home` y de los documentos privados.
5. Reinstalar con el particionado de la sección 3.
6. Restaurar la configuración de usuario desde este repositorio, excluyendo los archivos Omarchy-only.
7. Portar Hyprland, Waybar, Walker, Mako, el bloqueo y `fastfetch`.
8. Eliminar progressively los restos de X11 y las dependencias de Omarchy.

### Conclusión

La base de Hyprland, Neovim, shell, herramientas y documentación es reutilizable. El componente que impide una reinstalación limpia no es el sistema base: es la **capa de automatización de Omarchy**, que ocupa varias capas superpuestas. El tema Tokyo Night es un activo independiente y portable; la mitigación térmica y el workaround de brillo también pueden conservarse sin Omarchy.

## 2. Estado del sistema

### Hardware y firmware

| Elemento | Estado | Observación |
|---|---|---|
| Equipo | Dell Inspiron 15 3535 | Portátil con APU AMD Barcelo, `gfx906`/Vega. |
| BIOS | `113-BARCELO-004`, 2022-02-23 | `fwupdmgr get-updates` no ofrece una versión más reciente para este equipo. |
| Kernel principal | `linux-cachyos 7.3.0-4` | Kernel de prueba activo. |
| Kernel alternativo | `linux-cachyos-lts 6.18.55-2` | Conservado como kernel de reserva. |
| Mesa | `26.2.5-1` | No se propone un downgrade. |
| Firmware | `linux-firmware 20261019` | Se mantiene durante la reinstalación. |

### Almacenamiento actual

| Punto de montaje | Dispositivo | Total | Usado | Libre | Uso | Lectura |
|---|---|---:|---:|---:|---:|---|
| `/` | `/dev/nvme0n1p8` | 59 GB | 54 GB | 2.1 GB | 97 % | Espacio insuficiente para kernels, caché y snapshots. |
| `/home` | `/dev/nvme0n1p7` | 129 GB | 69 GB | 54 GB | 57 % | Amplio; `$HOME` ocupa aproximadamente 63 GB. |
| `/var/cache/pacman/pkg` | En `/` | 2.5 GB | 2.5 GB | — | — | Caché recuperable, pero no sustituye un rediseño de particiones. |
| EFI | `/dev/nvme0n1p1` | 300 MiB | — | — | — | Debe conservarse una partición EFI propia. |

El dispositivo NVMe tiene 512,110,190,592 bytes, aproximadamente **477 GiB**. `lsblk` muestra además particiones de 8 GiB, 255 GiB, 19 GiB y otras sin sistema de archivos visible. No fue posible leer la tabla completa con `fdisk` o `parted` sin privilegios. Por tanto, el plan de la sección 3 es una propuesta de reinstalación de todo el disco, no una instrucción para redimensionar las particiones actuales.

### Swap

| Elemento | Estado | Veredicto |
|---|---|---|
| `zram0` | 15 GiB, activo, prioridad alta | Conservar. Es la primera línea de defensa para memoria comprimida. |
| `swap-swapfile.swap` | Falla en cada arranque; `/swap/swapfile` no existe | Corregir durante la reinstalación. |
| Swap en disco | Objetivo del propietario: 8 GB | Crear 8 GiB, con menor prioridad que zram. |

### Estado térmico

| Parámetro | Valor actual | Valor objetivo |
|---|---:|---:|
| Governor | `performance` en 16 CPU | `powersave` |
| EPP | `performance` | `balance_power` |
| `scaling_max_freq` | 4.55 GHz | 3.0 GHz |
| `thermal_zone0` en reposo | 81 °C | Por debajo de 60 °C tras aplicar la mitigación |

No hay `thermald`, `auto-cpufreq`, `tlp`, `powertop` ni `fancontrol`. `ryzenadj` está instalado, pero no se ejecuta y no puede controlar el SMU mientras Secure Boot está activo. `ananicy-cpp` y `lm_sensors` sí están presentes.

### Versiones de gestores de paquetes

| Gestor | Versión observada |
|---|---|
| pacman | 7.1.0 (`libalpm` 16.0.1) |
| yay | 13.0.1 (`libalpm` 16.0.1) |
| pipx | 1.18.4 |
| npm | 11.17.0 |
| cargo | 1.94.1 |
| flatpak | 1.18.4 |

Homebrew está instalado y `brew list` devuelve paquetes, pero el repositorio no contiene un manifiesto de Homebrew. No se generó uno porque no estaba entre los manifiestos existentes.

## 3. Plan de particionado para la reinstalación

### Distribución recomendada

| Partición | Tamaño | Tipo | Justificación |
|---|---:|---|---|
| EFI | 1 GiB | FAT32 | Margen suficiente para GRUB, kernels e initramfs; evita reutilizar una partición EFI de 300 MiB. |
| `/` | **100 GiB** | Btrfs | La instalación actual ocupa 54 GB, de los cuales 2.5 GB son caché recuperable. Cien GiB dejan margen para dos o más kernels, paquetes, journals y snapshots sin cerrar `/` al 97 %. |
| `/home` | **350 GiB** | Btrfs | `$HOME` usa 63 GB. Este tamaño deja aproximadamente 287 GiB de crecimiento sin repetir el problema de una partición raíz demasiado pequeña. |
| Swap en disco | **8 GiB** | swapfile o partición swap | Proporciona una reserva lenta para picos de memoria; zram conserva la prioridad para el uso cotidiano. |
| Sin asignar | **18 GiB** | — | Reserva para crecimiento, reorganización y herramientas del instalador. No es obligatorio asignarla desde el inicio. |

**Total asignado:** 459 GiB de aproximadamente 477 GiB.

### Recomendación definitiva de swap

**Usar 8 GiB de swap en disco y conservar los 15 GiB de zram.** Configurar el bloque de disco con prioridad inferior a `zram0`; por ejemplo, `zram0` con prioridad 100 y el swapfile con prioridad 10.

Esta combinación sí es coherente:

- 14 GiB de RAM y zram de 15 GiB cubren la mayor parte de la presión de memoria sin I/O físico.
- Los 8 GiB en disco aportan una segunda reserva si se agota zram o si una carga concreta necesita páginas no comprimibles.
- **8 GiB no permiten una hibernación fiable de 14 GiB de RAM.** Para hibernar el sistema completo se necesitaría al menos 16 GiB de swap en disco, además de espacio reservado.

Si se usa swapfile sobre Btrfs, debe seguir el procedimiento específico de Btrfs (`NOCOW` y creación del archivo con las propiedades correctas). Una partición swap dedicada es la opción con menosrans.

### Datos que justifican el cambio

- El problema no es la cantidad total de disco, sino la distribución: `/` está al 97 % y `/home` al 57 %.
- La caché de pacman ocupa 2.5 GB en `/` y se puede limpiar, pero limpiarla solo compra tiempo; no corrige la distribución.
- Mantener dos kernels y varios snapshots en una raíz de 60 GiB deja poco margen. Una raíz de 100 GiB ofrece una reserva mucho más sana.

## 4. Mapa de secciones del repositorio

El inventario base contiene **608 archivos versionados**. `docs/` en minúscula estaba sin versionar y es un directorio distinto de `Docs/`.

| Sección | Archivos base | Propósito | Acoplada a Omarchy | Veredicto |
|---|---:|---|---|---|
| `.config/` | 340 | Configuración de aplicaciones y del escritorio. | Parcial; Hyprland, Waybar, Walker, Mako, tema, `fastfetch` y servicios de usuario sí lo están. | **Conservar con cambios** |
| `Docs/` | 181 | Notas, tutoriales, archivos históricos y material personal. | No. | **Conservar con cambios** |
| `Utils/` | 28 | GRUB, LightDM, greeters, scripts y temas heredados. | No. | **Conservar con cambios** |
| `Scripts/` | 15 | Utilidades de shell, capturas, bloqueo y diagnóstico. | Parcial; el bloqueo usa `i3lock`. | **Conservar con cambios** |
| `packages/` | 6 | Manifiestos por gestor de paquetes. | Parcial; incluían tres paquetes `omarchy-*`. | **Conservar con cambios** |
| `.theme/` | 4 | Selector de temas para Qtile. | No, pero pertenece al X11 heredado. | **Eliminar** |
| `.local/` | 4 | Ejecutables personales versionados. | No. | **Conservar** |
| Archivos raíz | 30 | Dotfiles, `README.md`, `LICENSE` y archivos de shell/X11. | Parcial; `.profile` y `.xsession` son X11. | **Conservar con cambios** |
| `docs/` minúscula | 2 sin versionar | Bitácora técnica personal en español. | No. | **Conservar y convertir en canónico** si el propietario confirma. |

### Submapa de `.config/`

| Grupo | Rutas base | Hallazgo | Veredicto |
|---|---:|---|---|
| `nvim/` | 59 | Neovim/LazyVim; contiene integraciones de IA y CodeGraph. | Conservar; auditar por separado los plugins de IA. |
| `ghostty/` | 54 | Configuración extensa de un terminal que todavía no es el terminal de registro. | Conservar con cambios o mover a archivo privado. |
| `omarchy/` | 43 | Marca, extensiones, hooks y tema; el tema es portable, el resto no. | Dividir: conservar el tema, retirar el resto. |
| `qtile/` | 19 | WM X11 completo. | Eliminar o conservar únicamente como fixture de Xephyr. |
| `fish/` | 18 | Segundo shell con prompt y plugins propios. | Retirar si zsh queda como shell canónico. |
| `hypr/` | 12 | Configuración Hyprland acoplada a Lua y Omarchy. | Conservar con cambios; es la migración principal. |
| `polybar/` | 11 | Barra X11 sin bar backing activo. | Eliminar. |
| `kitty/` | 9 | Terminal Wayland viable. | Conservar como terminal de registro recomendado. |
| `elephant/` | 6 | Proveedores de Walker, sin paquete upstream. | Eliminar al reemplazar Walker. |
| `wezterm/` | 6 | Terminal adicional. | Opcional; retirar si se elige Kitty. |
| `bspwm/` | 5 | WM X11 heredado. | Eliminar. |
| `rofi/` | 8 | Lanzador X11 heredado. | Eliminar tras migrar. |
| `openbox/` | 4 | WM X11 heredado. | Eliminar. |
| `dunst/` | 4 | Notificador X11 heredado. | Eliminar; Mako cubre Wayland. |
| `spectrwm/` | 3 | WM X11 heredado. | Eliminar. |
| `waybar/` | 3 | Barra Wayland activa. | Conservar con cambios. |
| `xmobar/` | 3 | Barra X11 heredada. | Eliminar. |
| `picom/` | 2 | Compositor X11 heredado. | Eliminar. |
| `xmonad/` | 2 | WM X11 heredado. | Eliminar. |
| `sxhkd/` | 1 | Atajos X11 heredados. | Eliminar. |
| `tint2/` | 1 | Barra X11 heredada. | Eliminar. |
| `.config/haders` | 1 | Volcado de 335 líneas de ayuda de `less`. | Eliminar. |

La cifra agregada de 42 archivos X11 del inventario previo depende de si se cuentan subdirectorios completos; el desglose anterior refleja las rutas versionadas actuales. En cualquier caso, la conclusión es la misma: el conjunto no tiene el soporte de paquetes ni un flujo de sesión activo que lo justifique.

## 5. Redundancias

| Grupo | Evidencia | Superviviente recomendado | Decisión |
|---|---|---|---|
| Terminales | Alacritty (1), Foot (1), Ghostty (54), Kitty (9), WezTerm (6). | **Kitty**: soporte Wayland maduro, tabs, SSH y configuración ya presente. | Instalar solo Kitty; conservar las demás configs como archivo o retirarlas. |
| Shells | `fish/` (18), `cachyos-fish-config`, `nushell/` (2), `.zshrc`/`.zprofile`/`.zshenv`, `.p10k.zsh`. | **Zsh**: `/etc/passwd` ya lo declara como shell de inicio y la configuración Zsh está personalizada. | Retirar Fish y Nushell después de migrar cualquier variable necesaria. |
| Prompts | Powerlevel10k (`.p10k.zsh`, `.zshrc`), Starship (`.config/starship.toml`) y prompt Fish. | **Powerlevel10k** si Zsh es canónico. | Retirar Starship y el prompt Fish al cerrar la decisión de shell. |
| Barras | Waybar (3), Polybar (11), Tint2 (1), Xmobar (3). | **Waybar**. | Retirar las tres barras X11. |
| Gestores de ventanas | Hyprland (12) frente a BSPWM, Qtile, Openbox, Spectrwm y XMonad. | **Hyprland**. | Retirar los X11 salvo, como máximo, un fixture de pruebas con Xephyr. |
| LightDM | `Utils/lightdm.conf`, `Utils/lightdm-webkit2-greeter.conf`, `Utils/slick-greeter.conf` y copias en `Utils/configuration-lightdm/`. | **Ninguno**: GDM está instalado y es el display manager activo. | Retirar las copias; no mezclar dos greeters. |
| `.profile` / `.xsession` | Ambos inicializan X11, repiten `PATH`, XRDB, Picom, Dunst, `feh`, `xrandr`, `udiskie` y `xautolock`; sus salidas de `xrandr` se contradicen. | Un único archivo de entorno portable en `.config/environment.d/` o `.zprofile`. | Retirar ambos después de migrar las variables válidas. |
| GTK2 | `.gtkrc-2.0` incluye `.gtkrc-2.0.mine`; `gtkrc-2.0` no tiene punto inicial y GTK2 no lo lee. | `.gtkrc-2.0` + `.gtkrc-2.0.mine`. | Retirar `gtkrc-2.0`; no tocar `.gtkrc-2.0` porque GTK2 sí lo lee. |
| Capturas sin enlace | `Scripts/screenshots-wayland` y `Scripts/screenshots-x11` no aparecen en `bindings.lua`. | `Scripts/screenshot-full-clipboard` y `Scripts/screenshot-region-editor`, que sí están enlazados. | Retirar los dos scripts huérfanos. |
| Bloqueo heredado | `Scripts/lock` invoca `/bin/i3lock`; Hyprland usa `hyprlock`. | **`hyprlock`**. | Retirar `Scripts/lock` y `i3lock` después de verificar el bloqueo Wayland. |
| Helpers AUR | `paru` y `yay` están instalados. | **yay**, porque ya existe `packages/yay/installed.txt`. | Retirar `paru` y conservar un único helper. |
| Python/Cargo | `mypy` y `uv` aparecen en pacman y pipx; `ptpython` aparece en yay y pipx. | Versión de pacman para `mypy`/`uv`; pipx para `ptpython`. | Retirar los duplicados, no todo el software. |
| Omarchy | `omarchy-keyring`, `omarchy-nvim` y `omarchy-walker` bloquean la instalación en CachyOS simple. | Ninguno en la instalación base. | Conservarlos solo en `packages/pacman/omarchy-only.txt`. |
| Documentación | `Docs/` (181, versionado) y `docs/` (2, sin versionar) coexisten en un filesystem sensible a mayúsculas. | **`docs/` en minúscula** para la bitácora nueva. | Fusionar el material común en una sola convención; no mezclar ambos directorios. |

## 6. Inventario de acoplamiento a Omarchy

### 6.1 Configuración que no cargará sin Omarchy

| Archivo | Punto exacto de acoplamiento | Reemplazo portable |
|---|---|---|
| `.config/hypr/hyprland.lua:3-11` | Añade `$OMARCHY_PATH` a `package.path` y ejecuta `require("default.hypr.omarchy")`. | Convertir la entrada a `hyprland.conf`; conservar solo los módulos Lua propios si se reimplementan sus helpers. |
| `.config/hypr/{bindings,input,looknfeel,autostart,monitors}.lua` | Usan los globales `hl` y `o`, definidos por Omarchy en `default/hypr/helpers.lua`. | Reescribir con `bind`, `bindu`, `monitor`, `workspace` y `exec` de Hyprland. |
| `.config/hypr/bindings.lua:8-9,27-36` | `omarchy-reminder` y specs `{ omarchy = ... }` se expanden a binarios `omarchy-launch-*`. | Comandos directos (`kitty`, `firefox`, `nautilus`, etc.) o un lanzador portable. |
| `.config/hypr/hypridle.conf:2-4,11,17-18` | `omarchy-system-lock`, `omarchy-system-wake` y `omarchy-launch-screensaver`. | `hyprlock`, `systemctl suspend`/`hyprctl dispatch dpms on` o un script propio. |
| `.config/walker/config.toml:3-4,49` | Tema `omarchy-default`, ruta de temas de Omarchy y `omarchy-restart-walker`. | Sustituir Walker por un lanzador Wayland con tema local. |
| `.config/elephant/` | Sus seis archivos son proveedores para Walker; no hay paquete upstream autónomo. | Eliminar cuando Walker se sustituya. |
| `.config/omarchy/current/theme/hyprland.lua` | La capa de tema sigue la ruta Omarchy, aunque su paleta sea portable. | Copiar los valores a la configuración Hyprland nueva y retirar la ruta antigua. |

### 6.2 Comandos en runtime

| Archivo | Llamadas Omarchy | Reemplazo portable |
|---|---|---|
| `.config/waybar/config.jsonc` | Aproximadamente 20 puntos: menú, actualizaciones, Wi-Fi, Bluetooth, audio, batería, grabación, idle, silenciamiento, voxtype, terminal, navegador y selectores de zona horaria. | `nmcli`, `bluetoothctl`, `wpctl`, `upower`, `grim`/OBS, `wpctl` y scripts locales. |
| `.config/fastfetch/config.jsonc:5,69-81,117,148` | Branding y módulos `omarchy-version*`, `omarchy-theme-current`, `omarchy-version-pkgs`. | Logo propio, `fastfetch` nativo y versión de paquetes del sistema. |
| `.config/walker/config.toml:49` | `omarchy-restart-walker`. | No aplica tras sustituir el lanzador. |
| `.config/uwsm/env:4-5,11` | Exporta `OMARCHY_PATH`, lo antepone al `PATH` y ejecuta `omarchy-cmd-present mise`. | `PATH` propio y `command -v mise` o `mise activate`. |
| `.config/uwsm/default:4,7` | `TERMINAL=xdg-terminal-exec` y `BROWSER=omarchy-launch-browser`. | `TERMINAL=kitty` y `BROWSER=xdg-open` o script local. |
| `.config/chromium-flags.conf:4` | Carga una extensión ubicada en `~/.local/share/omarchy/...`. | Eliminar la bandera o apuntar a una extensión local versionada. |
| `.config/systemd/user/` | Servicios y timers de Omarchy, incluidos walker y monitor de batería. | Servicios Wayland propios; retirar los que solo replenish la distribución. |

### 6.3 Fuentes de tema

El tema activo es el activo más recuperable de toda la capa Omarchy. La paleta no depende de internals de Omarchy y puede trasladarse a `~/.config/theme/tokyo-night/`.

| Consumidor | Referencia actual | Nuevo origen |
|---|---|---|
| `.config/kitty/kitty.conf:1` | `include ~/.config/omarchy/current/theme/kitty.conf` | `~/.config/theme/tokyo-night/kitty.conf` |
| `.config/foot/foot.ini:2` | `include=~/.config/omarchy/current/theme/foot.ini` | `include=~/.config/theme/tokyo-night/foot.ini` |
| `.config/waybar/style.css:1` | `@import "../omarchy/current/theme/waybar.css";` | `@import "../theme/tokyo-night/waybar.css";` |
| `.config/swayosd/style.css:1` | `@import "../omarchy/current/theme/swayosd.css";` | `@import "../theme/tokyo-night/swayosd.css";` |
| `.config/hypr/hyprlock.conf:1` | `source = ~/.config/omarchy/current/theme/hyprlock.conf` | `source = ~/.config/theme/tokyo-night/hyprlock.conf` |
| `.config/mako/config:1` | `include=~/.local/share/omarchy/default/mako/core.ini` | `include=~/.config/theme/tokyo-night/mako.ini` |

`hyprlock.conf` tiene además dos dependencias adicionales: `background.path` apunta a `~/.config/omarchy/current/background` y la última línea carga `~/.local/state/omarchy/toggles/hyprlock.conf`. Ambas deben convertirse en rutas locales.

### 6.4 Archivos sin forma portable

| Archivo | Motivo |
|---|---|
| `.config/omarchy/extensions/menu.sh` | Parchea directamente `$OMARCHY_PATH/bin/omarchy-menu`; no existe sin Omarchy. |
| `.config/omarchy/hooks/**/*.sample` | Seis ejemplos de hooks cuyo contrato pertenece al gestor de hooks de Omarchy. |
| `.config/omarchy/themed/alacritty.toml.tpl.sample` | Plantilla del mecanismo de temas de Omarchy. |

No se eliminaron durante esta auditoría.

### 6.5 Archivos presentes en disco pero ignorados por Git

Estos archivos desaparecen silenciosamente en una reinstalación y el repositorio no puede restaurarlos:

| Archivo | Dependencia o contenido que se perdería |
|---|---|
| `.config/uwsm/env` | Define `OMARCHY_PATH` y el mecanismo que permite resolver los Lua de Hyprland. |
| `.config/uwsm/default` | Define terminal, navegador y editor de la sesión. |
| `.config/chromium-flags.conf` | Carga una extensión de Omarchy. |
| `.config/systemd/user/` | Servicios y timers que no están versionados. |
| `.config/environment.d/` | Variables de sesión fuera de Git. |

Antes de reinstalar deben copiarse a rutas versionadas y reescribirse sin comandos de Omarchy.

### 6.6 Acoplamiento de sistema fuera del repositorio

| Ruta del sistema | Acción manual del propietario |
|---|---|
| `/etc/pacman.d/hooks/walker-restart.hook` | Retirar al eliminar Walker/Omarchy. |
| `/etc/udev/rules.d/99-wifi-powersave.rules` | Revisar si sigue siendo necessária; no pertenece al repositorio. |
| `/etc/udev/rules.d/99-power-profile.rules` | Revisar si contradice el servicio térmico y el plan de energía. |

## 7. Clasificación de paquetes

### Criterio

- **Conservar**: se mantiene en la instalación base; tiene uso activo, es una dependencia relevante o forma parte del flujo principal.
- **Opcional**: instalar solo si el propietario confirma un flujo de trabajo concreto.
- **Eliminar**: no debe entrar en la instalación limpia; se retira después de la migración indicada.

En las tablas largas, una celda puede contener varios paquetes que comparten el mismo veredicto y el mismo motivo. **Cada entrada de todos los manifiestos aparece exactamente una vez**. Las tablas resumen **506 paquetes**: 355 para conservar, 20 para eliminar y 131 opcionales.

### 7.1 Resumen de manifiestos regenerados

| Gestor | Paquetes | Fuente de verdad | Observación |
|---|---:|---|---|
| pacman nativo | 466 | `pacman -Qqen` | Se excluyen los tres paquetes Omarchy. No se incluyen dependencias transitivas. |
| yay/AUR | 16 | `yay -Qqem` | Se excluye `omarchy-walker`; los duplicados de otras categorías se conservan aquí solo si no tienen otra copia. |
| pipx | 5 | `pipx list --short` | Se incluyen los cinco entornos vivos. |
| npm global de usuario | 12 | `npm ls -g --depth=0` | Se excluyen `npm`, `corepack`, `semver`, `node-gyp` y `nopt`. |
| cargo | 3 | `cargo install --list` | Se incluyen los tres paquetes instalados por Cargo. |
| flatpak | 1 | `flatpak list --app` | Solo aplicaciones; los runtimes no forman parte del manifiesto. |
| omarchy-only | 3 | Archivo explícito | No instalar en CachyOS simple. |

`pacman -Qq` devuelve el conjunto instalado completo, incluyendo dependencias transitivas; no es un manifiesto de reinstalación razonable. `pacman -Qqen` selecciona los paquetes nativos explícitamente instalados, que es la unidad correcta para este repositorio.

### 7.2 Comandos exactos de regeneración

```bash
# pacman: paquetes nativos explícitos, sin Omarchy
pacman -Qqen \
  | grep -v -E '^omarchy-(keyring|nvim|walker)$' \
  > packages/pacman/installed.txt

# yay: paquetes AUR explícitos, sin Omarchy
yay -Qqem \
  | grep -v -E '^omarchy-(keyring|nvim|walker)$' \
  > packages/yay/installed.txt

# pipx: una aplicación por entorno
pipx list --short \
  | cut -d ' ' -f 1 \
  > packages/pipx/installed.txt

# npm: prefijo global del usuario, sin paquetes bundled de Node.js
npm ls -g --depth=0 --json \
  | python3 -c 'import json,sys; data=json.load(sys.stdin); banned={"npm","corepack","semver","node-gyp","nopt"}; print("\n".join(sorted(name for name in data.get("dependencies",{}) if name not in banned)))' \
  > packages/npm/installed.txt

# cargo: nombres de los paquetes instalados, no sus binarios internos
cargo install --list \
  | sed -nE 's/^([^ ]+) v[^:]+:$/\1/p' \
  > packages/cargo/installed.txt

# flatpak: solo aplicaciones
flatpak list --app --columns=application \
  > packages/flatpak/installed.txt
```

El `.npmrc` fija `prefix=/home/d4nitrix13/.local`. Por eso `npm ls -g` describe el prefijo global del usuario. `/usr/lib/node_modules` contiene herramientas propiedad de paquetes del sistema y duplicados bundled; no se incorporate al manifiesto npm de usuario.

### 7.3 Separación de Omarchy

`packages/pacman/installed.txt` es el manifiestobase para CachyOS simple. `packages/pacman/omarchy-only.txt` conserva exactamente:

```text
omarchy-keyring
omarchy-nvim
omarchy-walker
```

Uso recomendado:

```bash
# CachyOS simple: no instalar omarchy-only.txt
sudo pacman -S --needed - < packages/pacman/installed.txt
yay -S --needed - < packages/yay/installed.txt

# Solo en una máquina que conserva Omarchy, y después de portar la configuración
yay -S --needed - < packages/pacman/omarchy-only.txt
```

### 7.4 Clasificación completa

#### pacman nativo — 466 paquetes

| Veredicto | Paquetes | Motivo |
|---|---|---|
| **Conservar — sistema, hardware y servicios (225)** | `1password-cli`; `accountsservice`; `alsa-firmware`; `alsa-plugins`; `alsa-utils`; `amd-ucode`; `base`; `bash-completion`; `bc`; `bluez`; `bluez-hid2hci`; `bluez-libs`; `bluez-obex`; `bluez-utils`; `bolt`; `brightnessctl`; `btop`; `btrfs-progs`; `cachyos-grub-theme`; `cachyos-hello`; `cachyos-hooks`; `cachyos-kernel-manager`; `cachyos-keyring`; `cachyos-mirrorlist`; `cachyos-packageinstaller`; `cachyos-plymouth-bootanimation`; `cachyos-plymouth-theme`; `cachyos-rate-mirrors`; `cachyos-settings`; `cachyos-v3-mirrorlist`; `cachyos-v4-mirrorlist`; `cachyos-zsh-config`; `caddy`; `calcurse`; `cbatticon`; `chwd`; `claude-code`; `cpupower`; `cryptsetup`; `cups`; `cups-browsed`; `cups-filters`; `cups-pdf`; `decibels`; `device-mapper`; `diffutils`; `dmidecode`; `dmraid`; `dosfstools`; `dua-cli`; `duf`; `e2fsprogs`; `efibootmgr`; `efitools`; `espeak-ng`; `ethtool`; `evince`; `evtest`; `exfatprogs`; `f2fs-tools`; `fastfetch`; `fcitx5`; `fcitx5-gtk`; `fcitx5-qt`; `ffmpegthumbnailer`; `firejail`; `foomatic-db`; `foomatic-db-engine`; `foomatic-db-gutenprint-ppds`; `foomatic-db-nonfree`; `foomatic-db-nonfree-ppds`; `foomatic-db-ppds`; `fsarchiver`; `fwupd`; `ghostscript`; `gifsicle`; `glances`; `gnome-keyring`; `gobject-introspection`; `gping`; `grilo-plugins`; `grub`; `grub-hook`; `gst-libav`; `gst-plugin-pipewire`; `gst-plugin-va`; `gst-plugins-bad`; `gst-plugins-ugly`; `gst-thumbnailers`; `gutenprint`; `gvfs-afc`; `gvfs-dnssd`; `gvfs-goa`; `gvfs-gphoto2`; `gvfs-mtp`; `gvfs-nfs`; `gvfs-onedrive`; `gvfs-smb`; `gvfs-wsdd`; `hdparm`; `hplip`; `htop`; `hunspell-es_any`; `hwdetect`; `hwinfo`; `hyphen-es`; `impala`; `imv`; `inetutils`; `iperf3`; `ipp-usb`; `iwd`; `jfsutils`; `jpegoptim`; `kernel-modules-hook`; `kvantum-qt5`; `lazydocker`; `lazygit`; `less`; `lib32-mesa`; `lib32-opencl-mesa`; `lib32-vulkan-radeon`; `libdvdcss`; `libgsf`; `libopenraw`; `libqalculate`; `libreoffice-fresh`; `libreoffice-fresh-es`; `linux-cachyos`; `linux-cachyos-headers`; `linux-cachyos-lts`; `linux-cachyos-lts-headers`; `linux-firmware`; `logrotate`; `lsb-release`; `lsd`; `lsscsi`; `lvm2`; `lzip`; `malcontent`; `man-db`; `man-pages`; `mdadm`; `meld`; `mesa`; `mesa-utils`; `mise`; `mkinitcpio`; `modemmanager`; `mousetweaks`; `mtools`; `nano`; `nano-syntax-highlighting`; `net-tools`; `netctl`; `networkmanager`; `networkmanager-openvpn`; `nfs-utils`; `nilfs-utils`; `nm-connection-editor`; `nmap`; `nss-mdns`; `ntfs-3g`; `opencl-mesa`; `openssh`; `optiimage`; `optipng`; `os-prober`; `pacman-contrib`; `pamixer`; `papirus-icon-theme`; `pipewire-alsa`; `pipewire-pulse`; `pkgfile`; `plocate`; `plymouth`; `pngquant`; `polkit-gnome`; `poppler-glib`; `power-profiles-daemon`; `pv`; `qt5-wayland`; `rebuild-detector`; `reflector`; `ripgrep`; `rsync`; `ruby`; `sg3_utils`; `shelly`; `smartmontools`; `snapshot`; `socat`; `sof-firmware`; `stress-ng`; `sudo`; `sysfsutils`; `system-config-printer`; `tecla`; `texinfo`; `tmux`; `tzupdate`; `ufw`; `ufw-docker`; `ufw-extras`; `upower`; `usb_modeswitch`; `usbutils`; `uwsm`; `vulkan-radeon`; `wget`; `which`; `whois`; `wiremix`; `wireplumber`; `wlr-randr`; `wpa_supplicant`; `xdg-user-dirs`; `xdg-utils`; `xf86-video-amdgpu`; `xfsprogs`; `xl2tpd`; `xmlstarlet`; `yaru-icon-theme`; `yay`; `zoxide` | Base del sistema, hardware, red, seguridad, impresión, audio y servicios con configuración activa. |
| **Conservar — desarrollo (67)** | `base-devel`; `bash-language-server`; `cmake`; `composer`; `docker`; `docker-buildx`; `docker-compose`; `dockerfile-language-server`; `eslint`; `eslint-language-server`; `gcc-fortran`; `git`; `github-cli`; `lldb`; `lua-language-server`; `lua-lpeg`; `lua-luv`; `luarocks`; `marksman`; `mypy`; `neovim`; `npm`; `perl`; `php`; `php-gd`; `php-pgsql`; `php-redis`; `php-sodium`; `pnpm`; `prettier`; `pyenv`; `pyright`; `python`; `python-dbus-fast`; `python-dbus-next`; `python-defusedxml`; `python-packaging`; `python-pip`; `python-pipenv`; `python-pipx`; `python-pulsectl`; `python-pulsectl-asyncio`; `python-pyclip`; `python-pydbus`; `python-pywayland`; `python-ruff`; `python-terminaltexteffects`; `python-virtualenv`; `rust-analyzer`; `rustup`; `shellcheck`; `shfmt`; `stylua`; `taplo-cli`; `task`; `tesseract`; `tesseract-data-eng`; `tree`; `tree-sitter-cli`; `ty`; `uv`; `vim`; `visual-studio-code-bin`; `vscode-css-languageserver`; `vscode-html-languageserver`; `vscode-json-languageserver`; `yaml-language-server` | Toolchain principal, editores, LSP y runtimes tiedos a configuraciones versionadas. |
| **Conservar — escritorio/Wayland (35)** | `chromium`; `flameshot`; `gdm`; `gpu-screen-recorder`; `grim`; `gum`; `hypridle`; `hyprland`; `hyprland-guiutils`; `hyprland-preview-share-picker`; `hyprlock`; `hyprpicker`; `hyprshot`; `hyprsunset`; `kitty`; `mako`; `mpv`; `mpv-mpris`; `nautilus`; `nautilus-python`; `obsidian`; `pavucontrol`; `playerctl`; `quickshell`; `signal-desktop`; `slurp`; `sushi`; `swappy`; `swaybg`; `swayosd`; `waybar`; `wl-clipboard`; `xdg-desktop-portal-gnome`; `xdg-desktop-portal-hyprland`; `xdg-terminal-exec` | Aplicaciones y plumbing del escritorio Wayland que se conservarán tras portar los comandos. |
| **Conservar — fuentes (17)** | `awesome-terminal-fonts`; `cantarell-fonts`; `gsfonts`; `noto-fonts`; `noto-fonts-cjk`; `noto-fonts-emoji`; `ttf-bitstream-vera`; `ttf-dejavu`; `ttf-fira-sans`; `ttf-ia-writer`; `ttf-jetbrains-mono-nerd`; `ttf-liberation`; `ttf-meslo-nerd`; `ttf-opensans`; `ttf-ubuntu-font-family`; `ttf-ubuntu-nerd`; `woff2-font-awesome` | Fuentes usadas por terminal, Neovim, Waybar y aplicaciones Qt/GTK. |
| **Opcional (110)** | `1password-beta`; `7zip`; `aether`; `alacritty`; `android-tools`; `antiword`; `arp-scan`; `asdcontrol`; `baobab`; `bind`; `blueman`; `bluetui`; `cachyos-fish-config`; `cachyos-micro-settings`; `cachyos-wallpapers`; `catdoc`; `cliamp`; `cloudflared`; `dnsmasq`; `dotnet-runtime-9.0`; `epiphany`; `file-roller`; `filezilla`; `firefox`; `foot`; `ghostty`; `gnome-backgrounds`; `gnome-calculator`; `gnome-calendar`; `gnome-characters`; `gnome-clocks`; `gnome-color-manager`; `gnome-connections`; `gnome-console`; `gnome-contacts`; `gnome-control-center`; `gnome-disk-utility`; `gnome-font-viewer`; `gnome-logs`; `gnome-maps`; `gnome-menus`; `gnome-music`; `gnome-remote-desktop`; `gnome-session`; `gnome-settings-daemon`; `gnome-shell`; `gnome-software`; `gnome-system-monitor`; `gnome-text-editor`; `gnome-themes-extra`; `gnome-tour`; `gnome-user-docs`; `gnome-user-share`; `gnome-weather`; `jdk-openjdk`; `jre21-openjdk`; `kdenlive`; `keepassxc`; `kind`; `kubectl`; `localsend`; `loupe`; `mariadb`; `mariadb-clients`; `mariadb-libs`; `micro`; `minikube`; `nushell`; `obs-studio`; `ollama`; `orca`; `pandoc-cli`; `papers`; `parsec-bin`; `pdfgrep`; `pinta`; `postgresql`; `postgresql-libs`; `python-poetry-core`; `python-pyqt5`; `python-reportlab`; `qemu-user-static-binfmt`; `r`; `rygel`; `s-nail`; `samba`; `satty`; `showtime`; `simple-scan`; `spotify`; `starship`; `thunar`; `timew`; `tobi-try`; `typora`; `unrar`; `unshield`; `unzip`; `usage`; `valkey`; `vlc-plugins-all`; `vsftpd`; `wine`; `wine-gecko`; `wine-mono`; `winetricks`; `xorg-server-xephyr`; `xorg-xdpyinfo`; `xournalpp`; `yelp` | Aplicaciones, runtimes o herramientas accesorias. Se instalan únicamente si el propietario confirma un uso real. Los matices por subconjunto están en la tabla siguiente. |
| **Eliminar (12)** | `feh`; `i3lock`; `nwg-displays`; `nwg-look`; `paru`; `rofi`; `scrot`; `sddm`; `xclip`; `xorg-xrandr`; `xorg-xset`; `xterm` | Todos exigen una migración previa o la eliminación de la configuración heredada indicada en la sección 8. |

Matices dentro de los 110 opcionales:

| Subconjunto | Paquetes | Razón |
|---|---|---|
| Terminales y shell | `alacritty`; `foot`; `ghostty`; `cachyos-fish-config`; `nushell`; `starship`; `micro` | Son Survivor alternatives a Kitty, Zsh y Powerlevel10k. |
| Navegadores | `epiphany`; `firefox` | Hay más de un navegador; conservar solo el de uso diario. |
| Aplicaciones GNOME | `gnome-backgrounds`; `gnome-calculator`; `gnome-calendar`; `gnome-characters`; `gnome-clocks`; `gnome-color-manager`; `gnome-connections`; `gnome-console`; `gnome-contacts`; `gnome-control-center`; `gnome-disk-utility`; `gnome-font-viewer`; `gnome-logs`; `gnome-maps`; `gnome-menus`; `gnome-music`; `gnome-remote-desktop`; `gnome-session`; `gnome-settings-daemon`; `gnome-shell`; `gnome-software`; `gnome-system-monitor`; `gnome-text-editor`; `gnome-themes-extra`; `gnome-tour`; `gnome-user-docs`; `gnome-user-share`; `gnome-weather` | Utilidades accesorias para un escritorio Wayland que no usa GNOME como shell. |
| Desarrollo y servidores | `dotnet-runtime-9.0`; `jdk-openjdk`; `jre21-openjdk`; `kind`; `kubectl`; `mariadb`; `mariadb-clients`; `mariadb-libs`; `minikube`; `pandoc-cli`; `postgresql`; `postgresql-libs`; `python-poetry-core`; `python-pyqt5`; `python-reportlab`; `qemu-user-static-binfmt`; `r` | Se/installar bajo demanda según los proyectos. |
| X11 de prueba | `xorg-server-xephyr`; `xorg-xdpyinfo` | Solo si se conserva una ruta de prueba Xephyr. |

#### yay/AUR — 16 paquetes

| Veredicto | Paquetes | Motivo |
|---|---|---|
| **Conservar (2)** | `ttf-ms-fonts`; `ttf-vista-fonts` | Fuentes del sistema que no están duplicadas en el conjunto conservado. |
| **Opcional — impresora (2)** | `epson-inkjet-printer-escpr`; `epson-inkjet-printer-escpr2` | Solo si se conserva la impresora Epson. |
| **Opcional — desarrollo (8)** | `freelens-bin`; `hadolint-bin`; `k6`; `mailpit-bin`; `mdbtools`; `python-pyodbc`; `redisinsight-bin`; `rstudio-desktop-bin` | Herramientas especializadas; instalar bajo demanda. |
| **Opcional (2)** | `monique`; `ryzenadj` | Uso no verificado. `ryzenadj` no funciona con Secure Boot y no está en ejecución. |
| **Eliminar (2)** | `ptpython`; `wlroots-asan-git` | `ptpython` se conserva en pipx; `wlroots-asan-git` es un build ASan de diagnóstico. |

#### pipx — 5 paquetes

| Veredicto | Paquetes | Motivo |
|---|---|---|
| **Conservar (1)** | `ptpython` | Survivor de la duplicación entre yay y pipx. |
| **Opcional (2)** | `pipenv`; `pycrypy` | Instalar solo si el flujo de trabajo los usa. |
| **Eliminar (2)** | `mypy`; `uv` | Duplican las versiones instaladas por pacman. |

#### npm — 12 paquetes

| Veredicto | Paquetes | Motivo |
|---|---|---|
| **Conservar (5)** | `@colbymchenry/codegraph`; `intelephense`; `markdownlint-cli`; `typescript`; `typescript-language-server` | Integran CodeGraph, PHP, Markdown y TypeScript con las configuraciones versionadas. |
| **Opcional (7)** | `@astrojs/language-server`; `@microsoft/compose-language-service`; `@playwright/cli`; `@vtsls/language-server`; `emmet-ls`; `prettier-plugin-astro`; `serve` | Extensiones o servicios npm bajo demanda. |

#### cargo — 3 paquetes

| Veredicto | Paquetes | Motivo |
|---|---|---|
| **Conservar (2)** | `tokei`; `zellij` | Multiplexer y herramienta de métricas con uso directo. |
| **Opcional (1)** | `vtracer` | Su uso en el repositorio no está verificado. |

#### flatpak — 1 paquete

| Veredicto | Paquetes | Motivo |
|---|---|---|
| **Eliminar (1)** | `es.danirod.Cartero` | Cartero fue discontinuado y fue sustituido por Graphpaper. |

#### omarchy-only — 3 paquetes

| Veredicto | Paquetes | Motivo |
|---|---|---|
| **Eliminar (3)** | `omarchy-keyring`; `omarchy-nvim`; `omarchy-walker` | Dependen de Omarchy y no existen en una instalación CachyOS simple. |

### 7.5 Paquetes a eliminar, con condición de seguridad

| Paquete | Gestor | Condición previa |
|---|---|---|
| `feh` | pacman | Retirar primero los arranque de X11 que lo invocan. |
| `i3lock` | pacman | Confirmar `hyprlock` y retirar `Scripts/lock`. |
| `nwg-displays` | pacman | Retirar el fallback X11 o decidir su conservación. |
| `nwg-look` | pacman | Retirar el fallback X11 o decidir su conservación. |
| `paru` | pacman | Seguro tras confirmar que `yay` sigue instalado. |
| `rofi` | pacman | Sustituir el lanzador X11. |
| `scrot` | pacman | Retirar `Scripts/screenshots-x11`. |
| `sddm` | pacman | Confirmar GDM como único display manager. |
| `xclip` | pacman | Retirar `Scripts/screenshots-x11` y el código X11 dependiente. |
| `xorg-xrandr` | pacman | Retirar `.profile`, `.xsession` y `.screenlayout/monitor.sh`. |
| `xorg-xset` | pacman | Retirar el código X11 dependiente. |
| `xterm` | pacman | Confirmar que no hay enlaces a un terminal X11. |
| `ptpython` | yay | Seguro; la versión pipx queda como sobreviviente. |
| `wlroots-asan-git` | yay | Seguro para una instalación normal. |
| `mypy` | pipx | Seguro después de validar el binario de pacman. |
| `uv` | pipx | Seguro después de validar el binario de pacman. |
| `es.danirod.Cartero` | flatpak | Migrar a Graphpaper y exportar lo necesario. |
| `omarchy-keyring` | omarchy-only | No instalar en CachyOS simple. |
| `omarchy-nvim` | omarchy-only | Portar la configuración de Neovim antes de retirar Omarchy. |
| `omarchy-walker` | omarchy-only | Sustituir Walker antes de retirar Omarchy. |

### 7.6 Paquetes que conviene añadir al manifiesto base

| Paquete | Motivo |
|---|---|
| `zram-generator` | Hacer explícita la dependencia de zram en una instalación limpia. |
| `bat` | `Scripts/extractPorts` lo usa como visor de fallback. |
| `aspell` | `.nanorc` invoca `aspell -x -c`. |
| `scrub` | `Scripts/rmk` depende de `/bin/scrub`. |
| `fuzzel` | Lanzador Wayland recomendado como replacement de Walker, si el propietario confirma la decisión. |
| Graphpaper (Flatpak) | Sustituto de Cartero. El identificador de aplicación exacto debe verificarse en el momento de instalar; no se.versionó un ID no confirmado. |

Si se conserva el estate X11 para Xephyr, también deben añadirse `picom`, `dunst`, `udiskie`, `networkmanager-applet`, `xautolock` y `xorg-xrandr`; no se incluyen en la instalación base porque hoy solo sostienen scripts muertos.

## 8. Correcciones de configuración

Las correcciones se ordenan por impacto. Este任务 no modificó `.config/omarchy/`, `.config/hypr/`, `.config/waybar/` ni los dotfiles raíz.

| Orden | Archivo | Corrección exacta |
|---:|---|---|
| 1 | `.config/opencode/service.json` | Ya se añadió a `.gitignore`. Rotar la contraseña y trasladarla a un almacén de secretos. |
| 2 | `.config/chromium-headless/` | Ya se añadió a `.gitignore`; no versionar perfiles de navegador efímeros. |
| 3 | `README.md:53,71` | Corregir el login: el shell efectivo es Zsh, no Fish. Indicar `hyprland`/UWSM de forma verificable, sin afirmar que `.xsession` inicia Hyprland. |
| 4 | `README.md:235` | Eliminar la afirmación de que `.xsession` ejecuta Hyprland vía UWSM. El archivo actual no contiene ni `hyprland` ni `uwsm`. |
| 5 | `README.md:255` | Actualizar el conteo de paquetes; usar las cifras de los manifiestos regenerados y separar pacman nativo, yay y omarchy-only. |
| 6 | `README.md:373-387` | Actualizar los comandos de regeneración y añadir cargo, flatpak, el filtro de Omarchy y el filtro de paquetes bundled de npm. |
| 7 | `.dmrc` | Cambiar `Session=qtile` por la sesión Hyprland válida; el valor actual contradice el escritorio vivo. |
| 8 | `.profile` y `.xsession` | Retirar ambos como scripts de sesión X11. Migrar solo las variables de entorno válidas a `.config/environment.d/` o `.zprofile`. |
| 9 | `.screenlayout/monitor.sh` | Retirar o regenerar: sus nombres de salida (`DVI-D-0`, `HDMI-0`, `DP-0`, `DP-1`, `HDMI-1`) no corresponden al uso actual de Hyprland. |
| 10 | `gnome.desktop`, `gtkrc-2.0` | Retirar el entrypoint GNOME y el archivo GTK2 sin punto inicial. |
| 11 | `.config/haders` | Retirar del repositorio: es una ayuda de `less` de 335 lines, no una configuración. |
| 12 | `.config/haders` y `gtkrc-2.0` | Una vez desversionados, añadir rutas exactas a `.gitignore` si se conservarán localmente. |
| 13 | `docs/` frente a `Docs/` | Elegir una sola convención y evitar que dos diferenciales de Git今后的신 detecten cambios de solo mayúscula. |
| 14 | `Utils/configuration-lightdm/` | Retirar copias de LightDM si GDM permanece; conservar una sola copia solo si se cambia de display manager. |
| 15 | `Scripts/screenshots-wayland` y `Scripts/screenshots-x11` | Retirar los dos scripts sin binding. |
| 16 | `Scripts/lock` | Retirar tras verificar `hyprlock` y sus hooks. |
| 17 | `.config/hypr/hyprlock.conf` | Retirar la fuente del toggle de Omarchy y apuntar el background a una ruta local. |
| 18 | `.config/mako/config` | Retirar los dos includes de Omarchy y usar el tema local. |
| 19 | `.config/fastfetch/config.jsonc` | Sustituir el logo y los módulos `omarchy-*` por información nativa. |
| 20 | `.config/waybar/config.jsonc` | Sustituir cada `omarchy-*` por un comando directo o script local; preservar el resto del layout. |
| 21 | `.config/walker/config.toml` y `.config/elephant/` | Sustituir el lanzador y retirar Elephant después de validar el replacement. |

## 9. Riesgos de seguridad y privacidad

| Riesgo | Estado | Acción obligatoria |
|---|---|---|
| Contraseña en `.config/opencode/service.json` | No versionada, nunca presente en el historial, pero antes de esta auditoría tampoco estaba ignorada. Ahora está en `.gitignore`. | Rotar la contraseña, comprobar si el servicio la reutiliza y guardar el nuevo valor fuera del repositorio. |
| Token de autenticación de Fly.io en `Docs/notas/server.md` | El archivo está versionado y contiene una URL de autorización con token. No se reproduce aquí. | Revocar y rotar el token; eliminar la URL del archivo y del historial cuando el propietario decida limpiar Git. |
| CV de un tercero: `Docs/documentos/CV-AndresFuentes_2024.pdf` | Archivo personal de otra persona dentro de un repositorio técnico. | Retirarlo del seguimiento y moverlo a almacenamiento privado con consentimiento del propietario del dato. |
| `Docs/musica/` | 13 archivos personales: compositions, catalysts, tutors e ideas. | Mover a un repositorio privado o bóveda cifrada; conservar en Git solo material que el propietario pueda publicar. |
| `Docs/documentos/` | 4 archivos, incluido el CV y notas personales. | Aplicar la misma separación; no versionar datos personales por defecto. |
| Visibilidad del remoto GitHub | **No verificada**: esta auditoría no consultó GitHub ni inspeccionó la visibilidad del remoto. | Confirmar si el repositorio es privado. Si es público, tratarlo como exposición y rotar todos los secretos encontrados. |
| Historial de Git | La contraseña de `service.json` no aparece en el historial. El token de Fly sí está en un archivo versionado; debe asumirse comprometido mientras el remoto sea público. | Planificar limpieza de historial solo después de confirmar visibilidad y hacer una copia de respaldo. |

No se imprimieron ni copiaron los valores de los secretos en este documento.

## 10. Mitigación térmica: cómo recuperarla

### Qué se perdió

La mitigación aplicada el 2026-10-20 no está en el sistema:

- `/usr/local/sbin/cpufreq-stabilize.sh` no existe.
- `/etc/systemd/system/cpufreq-stabilize.service` no existe.
- `systemctl is-enabled` devuelve `not-found`.
- Los 16 CPU volvieron a `performance`, EPP `performance` y límite 4.55 GHz.
- `thermal_zone0` marca 81 °C en reposo.

El archivo nunca estuvo versionado en este repositorio, por lo que no era recuperable desde Git.

### Fuente y archivos añadidos

La fuente completa está en `docs/incidencias/2026-10-20-apagones-termicos.md`, secciones **5.2** y **11**. Esta auditoría conserva sus tres decisiones de comportamiento:

```text
scaling_governor = powersave
scaling_max_freq = 3000000
energy_performance_preference = balance_power
```

Archivos aditivos:

| Archivo | Función |
|---|---|
| `Utils/systemd/cpufreq-stabilize.sh` | Aplica la política a las interfaces cpufreq disponibles. |
| `Utils/systemd/cpufreq-stabilize.service` | Unidad `oneshot` de sistema, ejecutada en `multi-user.target`. |

El script usa la ruta convencional `/usr/local/sbin/cpufreq-stabilize.sh`, y la unidad conserva `ConditionVirtualization=no`, `After=systemd-modules-load.service`, `RemainAfterExit=yes` y `WantedBy=multi-user.target`.

### Instalación que debe ejecutar el propietario

```bash
sudo install -Dm755 \
  Utils/systemd/cpufreq-stabilize.sh \
  /usr/local/sbin/cpufreq-stabilize.sh

sudo install -Dm644 \
  Utils/systemd/cpufreq-stabilize.service \
  /etc/systemd/system/cpufreq-stabilize.service

sudo systemctl daemon-reload
sudo systemctl enable --now cpufreq-stabilize.service
```

Verificación:

```bash
systemctl status cpufreq-stabilize.service
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference
sensors
```

Resultados esperados: unidad `active (exited)`, governor `powersave`, máximo `3000000`, EPP `balance_power` y temperatura en reposo inferior a 60 °C.

### Tensión con `amdgpu.runpm=0`

`amdgpu.runpm=0` se añadió el 2026-10-24 para evitar el cuelgue de la GPU. Mantiene la GPU permanentemente alimentada y, por tanto, **aumenta la carga térmica**. No debe quitarse sin sustituir antes el workaround del DMUB. La mitigación de frecuencia reduce el calor de la CPU, pero no elimina el calor generado por la GPU siempre activa.

La solución real es limpiar el ventilador y renovar la pasta térmica. El servicio es una medida paliativa para un disipador saturado, no una reparación.

## 11. Decisiones pendientes del propietario

| Decisión | Pregunta concreta | Default recomendado |
|---|---|---|
| Lanzador Wayland | ¿Qué reemplaza a Walker: `fuzzel`, `wofi` o `anyrun`? | **`fuzzel`**, con un wrapper de aplicaciones; es simple y no arrastra el ecosistema de proveedores de Walker. |
| Terminal de registro | ¿Cuál será el terminal único: Kitty, Foot, Ghostty o Alacritty? | **Kitty**. Ya está instalado, funciona en Wayland y ofrece una ruta clara para shells, tabs y SSH. |
| Shell de inicio | ¿Zsh o Fish? | **Zsh**, porque `/etc/passwd` ya lo define y `.zshrc` + `.p10k.zsh` están más completos. Corregir el README en consecuencia. |
| Motor de prompt | ¿Powerlevel10k o Starship? | **Powerlevel10k** con Zsh. Retirar Starship y el prompt Fish cuando se cierre la decisión de shell. |
| Estate X11 | ¿Se conserva algún WM como fallback de Xephyr/VM? | Conservar **solo Qtile como fixture de Xephyr** si la documentación de pruebas seguirá activa; retirar BSPWM, Openbox, Spectrwm, XMonad, Polybar, Tint2, Xmobar, Sxhkd, Picom, Rofi y Dunst. |
| Directorio canónico | ¿`docs/` o `Docs/`? | **`docs/` en minúscula**, por ser la bitácora reciente y el índice en español; migrar de forma controlada el contenido de `Docs/` que deba conservarse. |
| Documentos personales | ¿Qué material debe permanecer público? | **Ninguna** nota personal o CV de terceros en el remoto. Mover `Docs/musica/`, `Docs/documentos/` y equivalentes a un almacén privado. |
| Credenciales | ¿Se rotan ahora las dos credenciales expuestas? | **Sí**: contraseña de OpenCode y token de Fly.io. Ignorar archivos no sustituye la rotación. |
| Navegador | ¿Chromium o Firefox? | Mantener **Chromium** como navegador base y tratar Firefox como opcional si no se usa en bindings. |
| Display manager | ¿GDM o LightDM? | **GDM**, ya instalado; retirar todas las copias de LightDM y sus greeters. |
| AUR helper | ¿`yay` o `paru`? | **yay**, para mantener el manifiesto y los comandos existentes; retirar `paru`. |
| App Flatpak | ¿Cartero o Graphpaper? | **Graphpaper**; Cartero está discontinuado. |

## 12. Límites y elementos no verificados

- No se verificó la visibilidad del repositorio remoto en GitHub; no se consultó el servicio remoto.
- No se pudo leer la tabla completa del disco con `fdisk` o `parted` por falta de permisos. El plan usa el tamaño total y las particiones visibles de `lsblk`.
- No se instalaron, actualizaron ni desinstalaron paquetes. Todos los inventarios fueron consultas de solo lectura.
- No se modificaron `.config/omarchy/`, `.config/hypr/`, `.config/waybar/` ni los dotfiles raíz; las correcciones de esas rutas son recomendaciones.
- No se evaluó el identificador Flatpak exacto de Graphpaper; debe confirmarse antes de añadirlo al manifiesto.
- No se comprobó si los cuatro archivos de `Docs/documentos/` distintos del CV contienen secretos adicionales.
- La migración de Hyprland desde los helpers Lua de Omarchy es la parte más grande del trabajo y no fue implementada en esta auditoría.
