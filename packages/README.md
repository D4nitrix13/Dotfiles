# Manifiestos de paquetes

Este directorio guarda el inventario de programas de la instalacion anterior de
CachyOS, agrupados por categoria y por gestor de paquetes. Son la fuente de
verdad de lo que debe tener esta maquina.

El instalador que consume estos archivos es
[`Scripts/installPackages.sh`](../Scripts/installPackages.sh).

## Estructura

```
packages/
  <gestor>/
    <categoria>.txt      Paquetes instalables de esa categoria.
    excluidos/
      <motivo>.txt       Paquetes que NO se instalan, con el motivo.
```

Hay un directorio por gestor: `pacman`, `yay`, `npm`, `cargo`, `pipx` y
`flatpak`.

Cada archivo de categoria lleva su propia cabecera en comentarios, con el
nombre de la categoria, su descripcion, cuantos paquetes contiene y el comando
exacto para instalarlos. Las lineas que empiezan por `#` se ignoran, de modo
que los archivos se leen igual de bien con un visor de texto que con un
script.

## Como se instala

```bash
# Ver el plan sin tocar nada
Scripts/installPackages.sh --dry-run

# Instalar todo
Scripts/installPackages.sh

# Instalar un solo gestor
Scripts/installPackages.sh --only pacman
```

El script es idempotente: lo que ya esta instalado se omite, de modo que se
puede ejecutar tantas veces como haga falta.

## Paquetes excluidos

La subcarpeta `excluidos/` no se instala nunca. Cada archivo ahi dentro
explica en su segunda linea por que se excluyen los paquetes que contiene.

| Archivo | Paquetes | Motivo |
|---------|----------|--------|
| `pacman/excluidos/no-disponibles.txt` | 2 | Se eliminaron de los repositorios oficiales y del AUR. |

Los tres paquetes de Omarchy (`omarchy-keyring`, `omarchy-nvim` y
`omarchy-walker`) no figuran en ningun manifiesto. Su repositorio no esta
configurado en CachyOS simple y no existen ni en los repositorios oficiales
ni en el AUR. La razon queda registrada en
[`docs/auditoria-2026-10-24.md`](../docs/auditoria-2026-10-24.md), seccion 7.3.

## Categorias por gestor

### pacman (464 paquetes, 25 categorias)

| Categoria | Paquetes | Que agrupa |
|-----------|----------|------------|
| `almacenamiento-y-sistemas-de-archivos` | 23 | Discos, sistemas de archivos, cifrado, LVM y RAID. |
| `audio` | 17 | ALSA, PipeWire, WirePlumber, mezcladores y reproductores. |
| `bases-de-datos` | 6 | Motores de base de datos y sus clientes. |
| `configuracion-cachyos` | 7 | Ajustes, espejos, temas y herramientas propias de CachyOS. |
| `contenedores-y-virtualizacion` | 8 | Contenedores, orquestadores, maquinas virtuales y emulacion. |
| `desarrollo-y-editores` | 36 | Editores, servidores de lenguaje, depuradores y herramientas. |
| `edicion-y-lectura` | 15 | Oficina, visores de PDF, diccionarios, OCR y conversion. |
| `energia-y-hardware` | 4 | Gestion de energia, brillo y hardware grafico basico. |
| `escritorio-gnome` | 62 | GNOME, sus aplicaciones, portales, temas e iconos. |
| `fuentes` | 17 | Tipografias de sistema, de terminal y de interfaz. |
| `herramientas-de-construccion` | 4 | Compilacion y las herramientas base para construir software. |
| `impresion-y-dispositivos` | 22 | Impresoras, escaneres, Bluetooth, USB y dispositivos. |
| `juegos-y-graficos` | 11 | Controladores graficos, Vulkan, OpenCL, Wine y juegos. |
| `kernels-firmware-y-arranque` | 26 | Kernels, firmware, initramfs y arranque del sistema. |
| `lenguajes-y-runtimes` | 40 | Interpreters, compiladores y gestores de versiones. |
| `monitorizacion-y-diagnostico` | 15 | Medicion de recursos, hardware y diagnostico. |
| `navegadores-y-comunicacion` | 5 | Navegadores web, correo y mensajeria. |
| `red-y-conectividad` | 35 | Conexion, DNS, Bluetooth, VPN, servidores y transferencia. |
| `seguridad-y-aislamiento` | 13 | Contrasenas, cortafuegos, aislamiento y control parental. |
| `sistema-y-mantenimiento` | 15 | Mantenimiento base, utilidades core y actualizacion. |
| `teclado-y-entradas` | 3 | Metodos de entrada, distribucion de teclado y peripherals. |
| `terminal-y-cli` | 24 | Emuladores de terminal, paginadores y utilidades de consola. |
| `video-y-multimedia` | 23 | Reproduccion, edicion, imagen y streaming multimedia. |
| `wayland-hyprland` | 23 | Hyprland, su ecosistema Wayland, barras y portales. |
| `x11-y-qtile` | 10 | Servidor X11, Xorg y las herramientas que usa Qtile. |

### yay (14 paquetes, 4 categorias)

| Categoria | Paquetes | Que agrupa |
|-----------|----------|------------|
| `editores-y-escritorio` | 3 | Editores y componentes de escritorio del AUR. |
| `impresion-y-otros` | 2 | Soporte de impresoras y paquetes sin uso claro. |
| `red-y-devops` | 8 | Herramientas de red, observabilidad y desarrollo. |
| `utilidades-y-terminal` | 1 | Utilidades graficas y de terminal del AUR. |

### npm (12 paquetes, 2 categorias)

| Categoria | Paquetes | Que agrupa |
|-----------|----------|------------|
| `editores-y-servidores-de-lenguaje` | 7 | Servidores de lenguaje y herramientas de edicion. |
| `herramientas-y-servidores` | 5 | Utilidades de desarrollo instaladas con npm. |

### cargo (3 paquetes, 2 categorias)

| Categoria | Paquetes | Que agrupa |
|-----------|----------|------------|
| `terminal-y-multiplicadores` | 1 | Multiplicadores de terminal y editores de sesiones. |
| `utilidades` | 2 | Utilidades de linea de comandos. |

### pipx (5 paquetes, 4 categorias)

| Categoria | Paquetes | Que agrupa |
|-----------|----------|------------|
| `calidad-de-codigo` | 1 | Analizadores estaticos y verificadores de tipos. |
| `criptografia` | 1 | Utilidades de cifrado y gestion de secretos. |
| `entornos-y-gestores` | 2 | Entornos virtuales y gestores de dependencias. |
| `terminal-interactivo` | 1 | Interpretadores interactivos de Python. |

### flatpak (1 paquete, 1 categoria)

| Categoria | Paquetes | Que agrupa |
|-----------|----------|------------|
| `utilidades-de-red` | 1 | Aplicaciones de red instaladas como Flatpak. |

## Que se quito del AUR y por que

Dos paquetes del AUR se retiraron del manifiesto el 26 de octubre de 2026:

| Paquete | Motivo |
|---------|--------|
| `ptpython` | Ya se instala con pipx, y la rueda de PyPI no necesita compilacion. |
| `wlroots-asan-git` | Es una build de depuracion desde git, que por definicion no puede ser precompilada. |

`python-pyodbc` se mantiene en el AUR a proposito: instala la libreria en el
site-packages del Python del sistema, donde cualquier `import pyodbc` la
encuentra. No puede ir por pipx porque pyodbc es una libreria y no una
aplicacion: pipx exige un punto de entrada ejecutable.

De los 14 que quedan, 5 son variantes `-bin` y 2 son fuentes de tipografias:
se descargan tal cual. Los 7 restantes se compilan, y ninguno tiene
alternativa en los repositorios oficiales.

## Nota sobre `pacman` frente a `yay`

Los dos gestores se complementan. El manifiesto de `pacman` incluye algunos
paquetes que no estan en los repositorios oficiales y que por tanto se
compilan desde el AUR; el manifiesto de `yay` recoge los que se instalaron
expresamente con un ayudante del AUR. El instalador procesa ambos y compila
todo lo que falte en una sola cola.

## Nota historica

Hasta el 26 de octubre de 2026 cada gestor tenia un unico archivo
`installed.txt` con todos sus paquetes. Se sustituyeron por los archivos por
categoria para que el inventario fuera legible y para que anadir un paquete
no obligara a reordenar una lista de 466 lineas. El historial de git conserva
los archivos originales.
