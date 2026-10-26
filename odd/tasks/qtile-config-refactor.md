# Task: Refactor de la configuración de Qtile

## Objective

Refactorizar la configuración de Qtile para que el texto de las barras se vea con el tamaño y la tipografía correctos, corregir los defectos de ejecución y de tipado encontrados en la auditoría, y alinear el código con la convención del repositorio dotfiles, sin alterar el comportamiento del usuario más allá de los atajos de teclado ya acordados.

## Problem

El texto de las barras se ve pequeño y skinny. La causa no es una sola, son tres que se multiplican:

1. **Ninguna de las dos cadenas de fuente existe en el sistema.** `settings/widgets.py` pide `"UbuntuMono Bold Italic"` y `"UbuntuMono Nerd Font"`, pero las familias instaladas son `Ubuntu Mono` y `Ubuntu Nerd Font`. Pango parsea `"UbuntuMono Bold Italic"` como la familia inexistente `UbuntuMono`, y fontconfig cae a `Noto Sans Mono Regular`: sin negrita, sin cursiva y con métricas que no corresponden a los glifos Nerd Font que el panel usa por todas partes.
2. **`widget_defaults` está muerto.** libqtile sí lo aplica, vía `_Widget.global_defaults` (`libqtile/core/manager.py:137`), y el orden de resolución es `_variable_defaults` → `global_defaults` → `_user_config` (`libqtile/configurable.py:32-34`). Pero cada widget del panel fija su propio `font=` y `fontsize=` en `kwargs`, que van al final de esa cadena y siempre ganan. El `fontsize: 16` declarado nunca llega a la pantalla: lo que se ve es 14.
3. **La barra no tiene altura para su contenido.** `Bar(size=24)` en `settings/screens.py`, contra un `GroupBox` que necesita 22 px de fuente + 16 de `padding_y` + 2 de borde + 6 de margen = 46 px, y un triángulo de powerline con `fontsize=37`. El indicador de workspaces y los separadores se recortan.

Aparte de eso, la auditoría encontró defectos de ejecución, de tipado y de consistencia que no aparecen en el log pero sí en el código.

## Why

El usuario reporta texto pequeño y pide revisar si hay algo raro. El diagnóstico superficial sería subir un número en `fontsize`; el diagnóstico real muestra que subir ese número no arregla nada, porque la fuente no existe y el valor ni siquiera se aplica. Arreglarlo sin entender la cadena de resolución produce un cambio que parece funcionar en el editor y no cambia nada en la pantalla.

El mismo razonamiento aplica al resto: `mypy` reporta verde en este repositorio y no lo está, porque el binario del `PATH` no alcanza el site-packages del sistema y por eso no ve `libqtile`.

## Scope

### In scope

- `.config/qtile/settings/metrics.py` (nuevo): fuente única de verdad para tipografía y métricas del panel.
- `.config/qtile/settings/widgets.py`: heredar tipografía de `widget_defaults` en vez de fijarla en cada widget; GroupBox y powerline coherentes con la altura de la barra; cerrar el file handle de `interface.txt`; autodetectar la interfaz de red.
- `.config/qtile/settings/screens.py`: altura de barra desde `metrics`; conteo de monitores robusto.
- `.config/qtile/settings/theme.py`: `colors` a nivel de módulo, sin guard de `__name__`.
- `.config/qtile/settings/keys.py`: tipado correcto de la tabla de atajos.
- `.config/qtile/settings/groups.py`: nombres de grupo sin padding literal; imports coherentes.
- `.config/qtile/settings/layouts.py`: `Max` con la misma configuración de borde y margen que el resto.
- `.config/qtile/settings/mouse.py`, `settings/path.py`: imports coherentes.
- `.config/qtile/config.py`: tipado de `dgroups_app_rules`; imports coherentes.
- `.config/qtile/autostart.sh`, `restart.sh`: una sola definición del layout de teclado; shell POSIX; wallpaper que exista de verdad; picom sin instancias duplicadas.
- `.config/qtile/.gitignore`: sacar `interface.txt` del control de versiones.

### Out of scope

- Cambios de comportamiento del usuario que no sean los atajos ya acordados.
- La configuración de picom, rofi, thunar, flameshot: son de otras aplicaciones.
- Instalar `dbus-fast`: es un paquete, no configuración, y `sudo` no está disponible para el orquestador.
- Commit, push y apertura de pull request: son decisiones del propietario bajo la política habitual del repositorio.

## Constraints

- `sudo` requiere contraseña y no está disponible. Ninguna tarea puede instalar paquetes.
- No existe ningún fondo de pantalla propio del usuario: `~/Pictures`, `~/Images` no tienen imágenes y `/usr/share/backgrounds/Wallpapers/` está vacío. El script debe **descubrir** un fondo válido, no hardcodear una ruta.
- `~/.fehbg` apunta a `/usr/share/backgrounds/Wallpapers/38.jpg`, que ya no existe.
- Qtile corre bajo X11 puro (`XDG_SESSION_TYPE=x11`, `WAYLAND_DISPLAY` vacío), así que el script de captura correcto es `screenshots-x11`, no `screenshots-wayland`.
- El bloque de wallpaper y picom sin commitear en `autostart.sh` es un cambio del propietario: se preserva y se corrige, no se revierte.
- `libqtile.init(self)` corre en `Manager.__init__` (`libqtile/core/manager.py:108`) **antes** de que se cargue la configuración. Por eso `from libqtile import qtile` sí funciona en ejecución, aunque mypy lo marque.

## Route per task

| Task | Route | Trigger evidence |
|------|-------|------------------|
| T1 Métricas y tipografía | delegated direct (1 escritor) | 4 archivos no triviales: `metrics.py` nuevo, `widgets.py`, `screens.py`, `theme.py` → writer trigger |
| T2 Atajos, grupos, layouts y config | delegated direct (1 escritor) | 6 archivos: `keys.py`, `groups.py`, `layouts.py`, `mouse.py`, `path.py`, `config.py` → writer trigger |
| T3 Scripts de shell | delegated direct (1 escritor) | 2 scripts y `.gitignore` → writer trigger |

Los tres son secuenciales sobre la misma rama: un solo hilo de escritura a la vez, sin worktrees paralelos.

TDD: no aplica. No hay suite de tests para una configuración de window manager y no tiene sentido inventarla. Los checks aplicables son `python -m mypy .`, un smoke test de carga de la configuración, la verificación de duplicados de atajos, `bash -n` y `shellcheck`.

## Checklist

- [x] T1 — Crear `settings/metrics.py` con la fuente única de verdad y migrar `widgets.py`, `screens.py` y `theme.py` a ella
- [x] T2 — Tipar la tabla de atajos y alinear `keys.py`, `groups.py`, `layouts.py`, `mouse.py`, `path.py` y `config.py` con la convención
- [x] T3 — Unificar `autostart.sh` y `restart.sh`, arreglar el wallpaper y sacar `interface.txt` del repo
- [x] T4 — Corregir la causa raíz de `interface.txt` vacío en `.profile`

## Acceptance criteria

- El texto de las barras se renderiza en `Ubuntu Nerd Font` Bold Italic, con el tamaño declarado en `metrics.py` y no con uno hardcodeado en cada widget.
- El `GroupBox` de workspaces y los triángulos de powerline caben completos dentro de la barra: nada se recorta.
- `python -m mypy .` desde `.config/qtile/` termina con cero errores.
- La configuración de Qtile carga sin excepciones y sin atajos duplicados.
- `bash -n` y `shellcheck` pasan sobre `autostart.sh` y `restart.sh` sin findings.
- El wallpaper se aplica desde una ruta que existe de verdad, o no se aplica en silencio sin error.
- `interface.txt` se genera en el arranque y ya no está versionado.
- Los atajos acordados siguen en su sitio: rofi en `mod+space`, thunar en `mod+shift+f`, `toggle_floating` en `mod+f`, `layout.next` en `mod+m`, captura en `mod+s`.

## Checks

- `cd .config/qtile && python -m mypy .`
- `cd .config/qtile && bash -n autostart.sh restart.sh`
- `cd .config/qtile && shellcheck autostart.sh restart.sh`
- Smoke test de carga de la configuración con conteo de atajos y detección de duplicados
- `git diff --stat` por work unit, para que cada commit sea revisable por separado

## Progress

### Completed

- Auditoría del repositorio de qtile y del log de ejecución.
- Reubicación de atajos acordada con el propietario: rofi `mod+m` → `mod+space`, thunar `mod+e` → `mod+shift+f`, `toggle_floating` `mod+shift+f` → `mod+f`, `layout.next` `mod+space` → `mod+m`.
- `mod+s` corregido: `~/Scripts/screenshots` no existe, el destino real es `~/Scripts/screenshots-x11` porque la sesión es X11.
- T1, T2 y T3 ejecutados y verificados. Cuatro commits de código más uno de documentación.

### Commits

| Commit | Work unit | Contenido |
|--------|-----------|-----------|
| `07c611e` | atajos | rofi a `mod+space`, explorador a `mod+shift+f`, `toggle_floating` a `mod+f`, `layout.next` a `mod+m`, captura a `screenshots-x11` |
| `294dc86` | T1 | `settings/metrics.py` nuevo, `widgets.py`, `screens.py`, `theme.py` |
| `26ff1e0` | T1 | altura de barra a 36 px para que quepan los workspaces a 25 px |
| `08f260d` | T2 | `keys.py`, `groups.py`, `layouts.py`, `mouse.py`, `path.py`, `config.py` |
| `183e4a4` | T3 | `autostart.sh`, `restart.sh`, `.gitignore`, `interface.txt` fuera del índice |
| `85f2e0a` | T4 | regex de la interfaz de red en `.profile` |

### Evidencia de verificación

- `python -m mypy .` desde `.config/qtile/`: **0 errores** en 11 archivos. Antes había 3.
- `qtile check` con el `mypy` del sistema: `stubtest` sin problemas en 12 módulos y **"Your config can be loaded by Qtile"**, código de salida 0.
- 55 bindings, 9 grupos, **cero atajos duplicados**. Los 37 bindings estáticos se compararon uno por uno contra el baseline: idénticos. Los 18 de workspace difieren solo por el relleno eliminado del nombre.
- Resolución de la fuente comprobada con Pango, que es el motor real de libqtile: `family "Ubuntu Nerd Font"`, `style ITALIC`, `weight 700`.
- Geometría del panel: `25 + 2*2 + 2*1 + 2*2 = 35 px` de contenido en una barra de `36 px`. Nada se recorta.
- `shellcheck autostart.sh restart.sh`: sin findings. `bash -n` y `bash --posix -n`: sin salida.
- Selección del fondo: `/usr/share/wallpapers/cachyos-wallpapers/Dracula.png`, que acompaña al tema activo.
- Detección de la interfaz: `wlan0`, por la ruta por defecto y por el fallback de `/sys/class/net`.

### Hallazgos aparecidos durante la implementación

- **El `mypy` del `PATH` es un verde falso, y también rompe `qtile check`.** El binario es el build compilado de pipx, que no alcanza el site-packages del sistema: no resuelve `libqtile` y, con `ignore_missing_imports = True`, lo convierte todo en `Any`. `qtile check` invoca `mypy` y `stubtest` por nombre desde el `PATH`, así que su paso de tipos también era verde falso. El check real es `python -m mypy .`, y para `qtile check` hace falta un shim que use el Python del sistema.
- **La causa raíz del `interface.txt` vacío no estaba en el panel.** `.profile:128` lo sobreescribía en cada login con `grep -iPw '^enp.*?$'`, que solo matchea interfaces `enp`. La interfaz real es `wlan0`, así que no matcheaba nada y `tee` dejaba el archivo vacío sin error visible. `.xsession:136` ya usaba el regex correcto con `enp|wlp|wlan`. Corregido en `85f2e0a`.
- **`numlockx` no está instalado** en esta máquina, así que la comprobación original imprimía `No such file or directory` en cada arranque. Ahora se comprueba con `[ -x /bin/numlockx ]`.
- **`.profile` y `.xsession` llaman a `~/Scripts/getRandomBackground.sh`, que no existe.** El script real se llama `getRandomBackground`, sin extensión. Queda fuera del alcance de este trabajo: la línea de `feh` termina con un argumento vacío, pero `autostart.sh` ya deja el fondo correcto.
- **El propietario ajustó a mano `GROUP_FONTSIZE` de 18 a 25 px** mientras|work unit T1 estaba en curso, para leer los workspaces de un vistazo. Se respetó el valor y se subió `BAR_SIZE` de 30 a 36 px, porque a 25 px el `GroupBox` necesita 35 px y se recortaba.
- **Otra sesión del propietario commiteó en la misma rama** (`306ecf8`, "purgar las herramientas duplicadas") y tocó `keys.py`, `layouts.py` y `widgets.py`: `mod+shift+f` pasa a lanzar `nautilus` en lugar de `thunar`, la regla de flotación pasa a `Nautilus` y el widget de memoria usa `btop`. Esos cambios se conservaron y no se revirtieron. El atajo que pidió el propietario sigue en `mod+shift+f`; lo que cambió es la aplicación de detrás.

### Hallazgos de la auditoría

- Las fuentes declaradas no existen. Pango parsea `"UbuntuMono Bold Italic"` como la familia `UbuntuMono`, que no está instalada; fontconfig cae a `Noto Sans Mono Regular`. `"Ubuntu Nerd Font Bold Italic"` sí resuelve a la familia correcta con negrita y cursiva.
- `widget_defaults` es código muerto: cada widget fija su propia tipografía y siempre gana sobre el default global.
- `Bar(size=24)` contra un GroupBox que necesita 46 px y un powerline de 37 px: el contenido se recorta.
- `settings/widgets.py:193` abre `interface.txt` sin `with`: el handle se filtra en tiempo de importación.
- `interface.txt` está versionado **vacío** (blob `e69de29`); en cualquier clone `widget.Net` recibe `interface=""` y el widget de red queda muerto. Nada lo escribe en el arranque.
- `settings/theme.py:68` solo define `colors` cuando el módulo se importa como `settings.theme`; ejecutado como script falla, y para un verificador de tipos `colors` queda condicionalmente definido.
- `settings/keys.py:38` declara `key: Tuple[...]` y la comprehension de la línea 46 vuelve a ligar ese nombre: la anotación describe algo que no existe.
- `settings/keys.py:44` usa `*key[2 : len(key) : 1]`, que no es un `LazyCall`: es un error de tipos real.
- `settings/screens.py:35` cuenta monitores con `xrandr | grep -w 'connected' | cut -d ' ' -f 2 | wc -l`: el `cut` selecciona la palabra literal `connected` y solo cuenta líneas. También cuenta salidas conectadas pero deshabilitadas, lo que genera una pantalla fantasma.
- `settings/layouts.py` deja `layout.Max()` fuera de `layout_conf`, así que el borde y el margen saltan al cambiar de layout.
- `settings/groups.py` rellena los nombres de grupo con espacios literales que duplican el `padding_x` del GroupBox y se filtran a `lazy.group[group.name]`.
- Los imports mezclan absolutos (`config.py`, `groups.py`, `keys.py`, `layouts.py`, `mouse.py`) y relativos (`theme.py`, `widgets.py`, `screens.py`); `screens.py` usa ambos en el mismo archivo.
- `autostart.sh` y `restart.sh` duplican el bloque del layout de teclado, y ambos hooks (`startup_once` y `startup`) se disparan en el primer arranque, así que ese bloque corre dos veces.
- `autostart.sh` y `restart.sh` declaran `#!/bin/sh` pero usan `[[ ]]`, que es de bash.
- Las tres rutas del wallpaper en `autostart.sh` no existen, y `/usr/share/backgrounds/Wallpapers/` está vacío.
- El `mypy` del `PATH` (`~/.local/bin/mypy`, build compilado de pipx) no alcanza el site-packages del sistema, no resuelve `libqtile` y, con `ignore_missing_imports = True`, convierte todo en `Any`: el "Success" es un verde falso. El check real es `python -m mypy .`, que encuentra 3 errores genuinos.

## Next step

Reiniciar qtile (`mod+ctrl+r`) para cargar la configuración nueva y comprobar en pantalla que el texto de las barras se ve con el tamaño y la tipografía correctos, que el indicador de workspaces ya no se recorta y que el fondo de pantalla se aplica. La entrega (commit, push, pull request) queda como decisión del propietario.

Pendiente de reportar, fuera del alcance de este trabajo: `~/Scripts/getRandomBackground.sh` no existe y tanto `.profile` como `.xsession` lo invocan con ese nombre.

## Forecast

Unas 380 líneas de cambio entre los tres work units, con la mayor parte concentrada en `settings/widgets.py` y `settings/keys.py`. Entra en un solo slice de entrega, dentro del presupuesto de 400 líneas.

## Delivery strategy

`ask-on-risk` (default). El forecast está por debajo del presupuesto, así que no hace falta dividir en PRs encadenados: un solo slice sobre la rama `refactor/qtile-config`.
