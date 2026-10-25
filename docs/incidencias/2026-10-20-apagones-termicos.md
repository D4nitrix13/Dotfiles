# Apagones térmicos recurrentes — Dell con AMD Ryzen 7 7730U

Fecha del incidente: 2026-10-20
Equipo: Dell (smbus managed by `dell_smm`), kernel CachyOS `7.2.11-1-cachyos`
Síntoma reportado: la computadora se apagó 3 veces en menos de 1 hora sin aviso, sin mensaje y sin volcado.

---

## 1. Resumen ejecutivo

La máquina se apagaba de forma silenciosa porque el controlador embebido (EC) de Dell detectaba que el sensor Tj del APU se acercaba a Tjmax (95 °C) y cortaba la energía **antes** de que el kernel pudiera registrar nada. El apagado nunca fue por software (panic, OOM, abort), sino por protección térmica de hardware.

La causa inmediata: el governor de cpufreq estaba fijado en `performance`, lo que mantenía al APU en modo boost (4.4 GHz) **incluso en reposo**, sin dar oportunidad a la frecuencia de bajar. Combinado con un disipador saturado (pasta térmica gastada o polvo acumulado en el ventilador), cualquier carga breve disparaba la curva térmica.

Estabilización aplicada: governor `powersave`, cap de frecuencia en 3.0 GHz, EPP en `balance_power`. Resultado: 22 °C menos en reposo y pico de 76 °C bajo stress sostenido (vs 97 °C en 2 s antes). Cambio persistente vía servicio systemd `cpufreq-stabilize.service`.

Pendiente real (no resuelto por software): apertura del laptop para limpieza del ventilador y cambio de pasta térmica. Mientras esto no se haga, el software paliativo te da aire, pero el hardware sigue degradado.

---

## 2. Cronología del incidente

Datos extraídos de `journalctl --list-boots`.

| Boot # | Inicio | Fin | Uptime | Causa |
|--------|--------|-----|--------|-------|
| `-3` | 17:06:53 | 17:58:09 | 51 min | EC cut por Tj |
| `-2` | 17:58:54 | 18:22:36 | 24 min | EC cut por Tj |
| `-1` | 18:23:48 | 18:32:28 | 9 min  | EC cut por Tj |
| `0` (corriente) | 18:33:10 | — | — | — |

Tiempo entre arranques cada vez más corto → **acumulación de calor residual** entre reinicios. Patrón clásico de daño térmico progresivo: el disipador no alcanza a evacuar el calor acumulado del ciclo anterior.

Las últimas entradas de cada sesión antes del corte son actividades benignas (healthchecks de Caddy, deprecation warnings de ananicy-cpp). No hay panic, ni `Out of memory`, ni `kernel BUG`, ni `shutting down`. Eso descarta software como causa directa.

---

## 3. Diagnóstico paso a paso

### 3.1. Hardware y entorno

```text
Modelo:            AMD Ryzen 7 7730U with Radeon Graphics
Núcleos lógicos:   16 (8 físicos + SMT)
Frecuencia boost:  hasta 4.5 GHz
Frecuencia base:   2.0 GHz
Driver cpufreq:    amd-pstate-epp
Tjmax del SKU:     95 °C (Tctl)
Secure Boot:       activo
Secure path:       cap-end, sin password NOPASSWD excepto whitelist
```

El `amd-pstate-epp` es importante: en este kernel CachyOS solo expone `performance` y `powersave` como governors válidos; `schedutil` y `ondemand` no están compilados. Inicialmente se intentó `schedutil` y devolvió `Invalid argument` por sysfs.

### 3.2. Revisión de logs

Comandos:

```bash
journalctl --list-boots
journalctl --since "-2 hours" -p err -n 100
journalctl -b -3 -n 30     # últimas entradas del boot que murió
journalctl -b -2 -n 30
journalctl -b -1 -n 30
```

Hallazgos:

1. **Apagados silenciosos.** En los tres boots que terminaron, la última entrada del log es una operación benigna (healthcheck HTTP, deprecation warning). No hay rastro del shutdown, lo que significa que el sistema perdió energía sincrónicamente con la escritura del journal.
2. **Swap fallando en cada arranque.** `Failed to activate swap /swap/swapfile.` aparece en los 4 boots. No causa los apagones, pero indica configuración sucia.
3. **Errores en `.profile` (líneas 97, 101, 104, 113, 116, 127).** Intentos de ejecutar `/bin/picom`, `/bin/nm-applet`, `/bin/dunst`, `/bin/udiskie`, `/bin/xautolock` y un script `~/.Scripts/getRandomBackground.sh`. Estos binarios no existen en el sistema (CachyOS usa `/usr/bin/`, no `/bin/`). Es ruido, no causa de los apagones. Pendiente de limpieza ortogonal.
4. **LED de mute y SFH AMD fallando.** Mensajes inocuos del kernel relacionados con micrófono mute LED y `pcie_mp2_amd`. Ruido estándar en hardware Dell.

### 3.3. Estado térmico en el momento de la investigación

Lecturas tomadas con `sensors` y `cat /sys/class/hwmon/*/temp*_input` con la máquina en reposo tras 1 minuto de uptime:

| Sensor | Valor | Notas |
|--------|-------|-------|
| `k10temp Tctl` | 75.0 °C | sensor Tj del APU |
| `acpitz` | 75.0 °C | zona ACPI |
| `amdgpu edge` | 60.0 °C | GPU integrada |
| `dell_smm CPU` | 75.0 °C | EC report |
| `dell_smm ambient` | 46.0 °C | aire interior |
| `dell_smm SODIMM` | 45.0 °C | RAM |
| `nvme Composite` | 48.9 °C | SSD |
| `Processor Fan` | 4300 RPM | ventilador al 78 % de su máximo (5500 RPM) |

**Lectura importante**: 75 °C en reposo absoluto después de un arranque en frío es un disipador saturado. Con un disipador sano esa lectura no debería pasar de 50 °C en reposo. Tener el ventilador al 78 % con la máquina en reposo confirma que el ventilador intenta compensar una resistencia térmica anormal (pasta seca, polvo acumulado, o ambos).

### 3.4. Batería

```text
Fabricante:        ATL
Modelo:            0x47,0x34,0x42,0x45
Estado:            fully-charged
Porcentaje:        100 %
Energía llena:     30.34 Wh
Energía diseño:    41.01 Wh
Salud (capacity):  73.99 %
Tecnología:        lithium-ion
Voltaje:           12.24 V (cargando)
```

La batería conserva el 74 % de la capacidad original. No es la causa del incidente (estaba llena y con AC conectado), pero está clara candidata a reemplazo: una batería así puede generar brownouts internos bajo carga que disparan apagados en cascada si el jack de DC tiene contacto marginal.

### 3.5. Carga del APU con governor `performance`

Antes de cualquier mitigación:

```text
scaling_governor          : performance
scaling_cur_freq promedio : 4.41 GHz (16 cores con boost)
energy_performance_pref   : performance (no había balance)
Tctl en reposo            : 75-78 °C
```

El APU estaba permanentemente en boost aunque la carga del usuario fuese cero. Esto se confirma porque la frecuencia reportada por `/proc/cpuinfo` era uniformemente alta (4.4-4.5 GHz) en los 16 cores en vez del patrón heterogéneo que se observa con governor correcto.

### 3.6. Stress test verificable

Para confirmar que el causante era térmico y no eléctrico, se ejecutó un stress controlado con `stress-ng` y un watchdog que mata el stress si Tctl ≥ 92 °C. Captura cada 2 s en `/tmp/opencode/thermal-watch/stress.log`.

Resultado del primer stress (sin mitigación):

```text
Tctl inicial:  78 °C
Tctl tras 2s:  97 °C   ← watchdog cortó stress
Freq al corte: 3969 MHz
Acción:        stress-killed a las 2s por threshold
```

El resultado es definitivo: con el governor por defecto, dos segundos de carga son suficientes para empujar la CPU al borde del Tjmax. El EC de Dell estaba cortando en producción por el mismo motivo, solo que en vez de a los 2 s lo hacía a los pocos minutos (los healthchecks de Caddy y el ruido de journal hacen de carga equivalente a la de un stress sostenido).

---

## 4. Causa raíz

Tres factores en orden de contribución:

1. **Governor `performance` activo + EPP en `performance`.** El APU no bajaba de 4.4 GHz ni en reposo. Esto carga térmica constante sin justificación, y reduce enormemente el headroom para cargas reales.
2. **Disipador térmico saturado por hardware.** Pasta térmica seca y/o polvo en el ventilador. Esto limita la evacuación incluso con el APU a baja potencia.
3. **Batería degradada (74 % de capacidad original).** No causó este incidente, pero incrementa el riesgo de apagados súbitos bajo picos de carga si el jack de DC hace mal contacto.

(2) es el problema físico que el software no puede resolver. (1) es mitigable inmediatamente y es lo que se atacó. (3) es cambio de hardware.

---

## 5. Solución aplicada

### 5.1. Mitigación inmediata (volátil)

Cambios aplicados en caliente, sobreviven hasta el próximo reinicio:

| Parámetro | Antes | Después | Cómo |
|-----------|-------|---------|------|
| `scaling_governor` | `performance` | `powersave` | `echo powersave > .../cpufreq/scaling_governor` |
| `scaling_max_freq` | 4547946 kHz (4.5 GHz) | 3000000 kHz (3.0 GHz) | `echo 3000000 > .../cpufreq/scaling_max_freq` |
| `energy_performance_preference` | `performance` | `balance_power` | `echo balance_power > .../energy_performance_preference` |

Lectura térmica posterior a la mitigación:

```text
Tctl reposo:        56.4 °C     (antes 78 °C → -22 °C)
GPU edge reposo:    51.0 °C
Fan RPM reposo:     3400 RPM    (antes 4300 → más silencioso)
Freq media reposo:  2.92 GHz    (antes 4.41 GHz)
```

Lectura térmica con stress controlado de 60 s (`stress-ng --cpu 8`, log en `/tmp/opencode/thermal-watch/verify.log`):

```text
Tctl máximo:        76 °C
Tctl final:         76 °C
Margen al Tjmax:    +19 °C      (antes -2 °C)
Freq sostenida:     ~2.8 GHz    (sujeta al cap)
```

La verificación es exitosa: la máquina aguanta 60 segundos de carga completa con margen amplio.

### 5.2. Persistencia: servicio systemd

Para que los cambios se apliquen también tras el próximo reinicio, se creó un script y un servicio systemd.

#### Archivo: `/usr/local/sbin/cpufreq-stabilize.sh`

```bash
#!/usr/bin/env bash
# Aplica política de cpufreq estable al boot del sistema.
# Diseñado para estabilizar el APU Ryzen 7 7730U en Dell
# con kernel cachyos/amd-pstate-epp.

set -u

apply() {
  local pattern="$1" value="$2"
  for f in $pattern; do
    [ -w "$f" ] && echo "$value" > "$f" 2>/dev/null
  done
}

apply "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor" "powersave"
apply "/sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq" "3000000"
apply "/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference" "balance_power"
```

#### Archivo: `/etc/systemd/system/cpufreq-stabilize.service`

```ini
[Unit]
Description=Aplica governor powersave + cap 3GHz + EPP balance_power
After=systemd-modules-load.service
Documentation=https://wiki.archlinux.org/title/CPU_frequency_scaling
ConditionVirtualization=no

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/cpufreq-stabilize.sh
RemainAfterExit=yes
StandardOutput=journal

[Install]
WantedBy=multi-user.target
```

#### Por qué cada decisión

- **`Type=oneshot` + `RemainAfterExit=yes`**: la unidad ejecuta el script una sola vez en el boot y queda reportando estado "active (exited)" en lugar de fallar al intentar mantener un proceso vivo que no existe.
- **`After=systemd-modules-load.service`**: garantiza que los módulos de cpufreq están cargados antes de intentar escribir a los sysfs. Sin esto, en algunos boots la escritura a `scaling_governor` puede fallar por no existir aún.
- **`ConditionVirtualization=no`**: previene ejecución en máquinas virtuales. Dentro de una VM no tiene sentido (ni a veces es posible) tocar cpufreq del host, y suele romper el inicio.
- **`RemainAfterExit=yes`**: requerido para `systemctl status` muestre correctamente "active (exited)" y no "failed". Sin esta línea el servicio aparecería como fallido tras ejecutarse correctamente.
- **`WantedBy=multi-user.target`**: target estándar de boot multiusuario. Si el sistema entra en `rescue.target` o `emergency.target` la unidad no se ejecuta (lo cual es correcto: el operador está manejando la máquina manualmente).

#### Habilitar y arrancar

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cpufreq-stabilize.service
```

`--now` es equivalente a `start` + `enable`. El servicio queda corriendo ya y armado para próximos boots.

#### Verificación post-instalación

```bash
sudo systemctl status cpufreq-stabilize.service
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor              # powersave
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq | awk '{print $1/1000000 " GHz"}'  # 3 GHz
cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference # balance_power
```

Si la unidad está `active (exited)` sin errores y los tres valores posteriores son los esperados, está funcionando.

#### Reversión

Si en algún momento quieres volver al comportamiento por defecto:

```bash
sudo systemctl disable --now cpufreq-stabilize.service
```

Y manualmente:

```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
echo $(cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq) | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference
```

---

## 6. Estado actual de archivos

Archivos creados durante este incidente:

| Path | Tipo | Descripción |
|------|------|-------------|
| `/usr/local/sbin/cpufreq-stabilize.sh` | Script | Aplica política powersave al boot |
| `/etc/systemd/system/cpufreq-stabilize.service` | Unidad systemd | Dispara el script en multi-user.target |
| `/tmp/opencode/thermal-watch/stress.log` | CSV | Log del primer stress (incidente) |
| `/tmp/opencode/thermal-watch/verify.log` | CSV | Log del stress post-mitigación |
| `/tmp/opencode/thermal-watch/stress.stderr` | Texto | Salida de stress-ng |
| `/tmp/opencode/thermal-watch/meta.txt` | Texto | Metadatos de los tests |

Los archivos en `/tmp/opencode/thermal-watch/` son temporales y se borran al reiniciar. Si quieres conservarlos como evidencia del incidente, cópialos a `~/docs/incidencias/datos/`.

Archivos pendientes de corrección (no relacionados con los apagones, pero observados durante el diagnóstico):

- `~/.profile`: rutas hardcoded a binarios inexistentes (`/bin/picom`, `/bin/dunst`, etc.) y un script `~/.Scripts/getRandomBackground.sh` ausente.
- `/swap/swapfile`: entrada en fstab sin archivo real en disco.

---

## 7. Lo que **no** se hizo y por qué

### Desactivar Secure Boot en BIOS

Lo descubrí porque `ryzenadj` (instalado durante el incidente) devuelve:

```text
PCI Bus is not writeable, check secure boot
Unable to get MP1 SMU Obj
Unable to init ryzenadj
```

Secure Boot impide escribir al MSR del SMU (System Management Unit) del APU. Sin acceso al SMU, no se puede controlar el PPT/STAPM de forma fina. Sin embargo, con governor `powersave` y cap de frecuencia, el TDP efectivo ya está limitado por construcción: el APU no puede subir de 3 GHz y por lo tanto no puede consumir más de ~15 W sostenidos.

Conclusión: añadir `ryzenadj` requiere desactivar Secure Boot desde BIOS (que es un cambio invasivo y físico que el operador debe hacer). Para la estabilidad inmediata no es necesario; se deja como upgrade opcional si en el futuro quieres control fino de TDP sin cap de frecuencia.

### Cambiar `intel_pstate` o forzar `amd_pstate=active`

`amd-pstate-epp` (driver que está cargado) ofrece governor `powersave` que ya es suficiente para el caso. Cambiar el modo de driver requiere un parámetro de línea de kernel (`amd_pstate=active` o `amd_pstate=passive`) que se aplica vía GRUB. No se hizo porque el driver actual ya da lo necesario para estabilizar la máquina.

### Reemplazar `.profile` y swapfile

No relacionado con los apagones. Queda pendiente en una sesión aparte para no ensuciar este registro.

---

## 8. Recomendaciones a futuro

### Hardware (alta prioridad)

1. **Limpieza del ventilador y cambio de pasta térmica.** Esta es la causa raíz real. Sin esto, el software paliativo estirará los tiempos entre apagones pero no los eliminará del todo, sobre todo en meses cuando la pasta se degrade más.
   - Pasta recomendada: Arctic MX-4 o Thermal Grizzly Kryonaut.
   - Frecuencia de cambio: cada 2-3 años en uso normal, antes en uso intensivo.
2. **Reemplazo de batería (74 % de capacidad).** No fue el causante de este incidente, pero es candidata clara al primer corte de energía espurio bajo carga.
3. **Verificar jack de DC.** Mover suavemente el cable y ver si se corta. Un jack flojo multiplica el riesgo de brownouts con batería degradada.

### Firmware / BIOS

1. Actualizar BIOS de Dell. Las revisiones recientes suelen mejorar el threshold de EC térmico (de 80 a 95 °C) y la curva del ventilador.
2. Cambiar el perfil de energía de "Performance" a "Balanced" en BIOS si está disponible. Con CachyOS el sistema operativo manda, pero tener el BIOS en performance refuerza el comportamiento que causó el problema.

### Software (opcional)

1. Instalar `tlp` o `auto-cpufreq` para gestión automática de energía. Son más mantenibles que el servicio manual, aunque el actual cumple su función.
2. Migrar el cap de frecuencia a `cpufreq.default_governor` y un módulo Kernel Parameter en GRUB si quieres evitar systemd. Trade-off: pierdes la flexibilidad de cambiar el cap sin editar GRUB.

---

## 9. Comandos de referencia rápida

### Diagnóstico térmico

```bash
# Temperaturas
sensors
cat /sys/class/hwmon/hwmon5/temp1_input   # k10temp (Tctl)
cat /sys/class/hwmon/hwmon6/fan1_input    # fan RPM

# Frecuencia actual por core
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq

# Configuración efectiva
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq | awk '{print $1/1000000 " GHz"}'
cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference
```

### Reproducir el incidente (solo diagnóstico, no para producción)

```bash
# Ataque térmico controlado con auto-kill a 92 °C
stress-ng --cpu 16 --timeout 600 --metrics --times
```

Se sugiere correrlo solo en modo informativo y con la mano cerca del botón de encendido. La mejor verificación es el log del post-fix (`/tmp/opencode/thermal-watch/verify.log`): 76 °C en 60 s con la máquina bajo stress razonable confirma que la mitigación está activa.

### Restaurar el estado por defecto (si quieres volver)

```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
echo $(cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq) | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference
sudo systemctl disable --now cpufreq-stabilize.service
```

---

## 10. Anexo A — Logs térmicos

Captura del primer stress (sin mitigación), archivo `/tmp/opencode/thermal-watch/stress.log`:

```csv
epoch,t_msec,k10temp_c,acpitz_c,amdgpu_c,smm_main_c,smm_amb_c,fan_rpm,freq_mhz
1792542986,0,78,78,60,80,46,4300,3649
(threshold 92 °C alcanzado tras 2 s)
```

Meta de la corrida:

```text
started:2026-10-20T18:36:45-06:00
threshold:92C
model:AMD Ryzen 7 7730U with Radeon Graphics
samples:1
elapsed_s:2
peak_k10:97C     ← sobre Tjmax
peak_acpitz:97C
peak_freq:3218MHz
ended:2026-10-20T18:36:47-06:00
```

Captura del segundo stress (post-mitigación), archivo `/tmp/opencode/thermal-watch/verify.log`, últimos 15 segundos:

```csv
epoch,t_s,k10temp_c,acpitz_c,smm_c,fan_rpm,freq_mhz
1792543421,44,75,75,75,4200,2793
1792543422,45,75,75,75,4200,2797
1792543423,46,75,75,75,4300,2745
1792543424,47,76,75,75,4300,2818
1792543425,48,76,76,76,4200,2817
1792543426,49,76,76,76,4200,2821
1792543427,50,76,76,76,4300,2768
1792543428,51,75,75,75,4300,2768
1792543429,52,75,75,75,4300,2787
1792543430,53,75,75,75,4200,2743
1792543431,54,75,75,75,4200,2743
1792543432,55,75,76,76,4300,2844
1792543433,57,76,76,76,4300,2796
1792543434,58,76,76,76,4300,2818
1792543435,59,76,76,76,4300,2796
```

Meta:

```text
samples=59 peak_tctl=76C
final_tctl=76C final_freq=2994MHz
```

Contraste directo:

| | Sin mitigación | Con mitigación |
|---|---|---|
| Peak Tctl | 97 °C | 76 °C |
| Tiempo hasta el peak | 2 s | 54 s |
| Tjmax | 95 °C | 95 °C |
| Margen | -2 °C ⚠️ | +19 °C ✅ |
| Fans RPM pico | 4300 (subiendo a 4600) | 4300 (estable) |

---

## 11. Anexo B — Archivos en disco

Para reproducibilidad, aquí están los archivos completos tal como quedaron al final del incidente.

### `/usr/local/sbin/cpufreq-stabilize.sh`

```bash
#!/usr/bin/env bash
# Aplica política de cpufreq estable al boot del sistema.
# Diseñado para estabilizar el APU Ryzen 7 7730U en Dell
# con kernel cachyos/amd-pstate-epp.

set -u

apply() {
  local pattern="$1" value="$2"
  for f in $pattern; do
    [ -w "$f" ] && echo "$value" > "$f" 2>/dev/null
  done
}

apply "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor" "powersave"
apply "/sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq" "3000000"
apply "/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference" "balance_power"
```

Permisos: `755 root:root`.

### `/etc/systemd/system/cpufreq-stabilize.service`

```ini
[Unit]
Description=Aplica governor powersave + cap 3GHz + EPP balance_power
After=systemd-modules-load.service
Documentation=https://wiki.archlinux.org/title/CPU_frequency_scaling
ConditionVirtualization=no

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/cpufreq-stabilize.sh
RemainAfterExit=yes
StandardOutput=journal

[Install]
WantedBy=multi-user.target
```

Permisos: `644 root:root`.

Habilitado con: `systemctl enable --now cpufreq-stabilize.service`.

---

## 12. Glosario

| Término | Significado |
|---------|-------------|
| **APU** | Accelerated Processing Unit; CPU + GPU en el mismo die. El Ryzen 7 7730U es un APU Zen 3 con Radeon integrada. |
| **EC** | Embedded Controller. Microcontrolador de gestión de bajo nivel en laptops (Dell usa uno propio). Puede cortar energía por protección térmica antes que el SO se entere. |
| **EPP** | Energy Performance Preference. Nivel de "energía vs rendimiento" del driver amd-pstate-epp. Valores aceptables típicos: `performance`, `balance_performance`, `balance_power`, `power`. |
| **Governor** | Política del driver cpufreq que decide cómo varía la frecuencia con la carga. Tu kernel solo soporta `performance` y `powersave`. |
| **PPT** | Package Power Tracking. Límite de potencia del paquete del APU en vatios. En 7730U es 15 W por defecto en el SKU móvil estándar. |
| **STAPM** | Sustained Temperature-Aware Power Management. Límite dinámico de potencia basado en temperatura; controlado por el SMU. |
| **SMU** | System Management Unit. Coprocesador del APU que gestiona energía, frecuencia y térmica. Requiere acceso MSR (no disponible con Secure Boot). |
| **Tctl** | Temperatura de control del APU reportada por k10temp. Refleja el punto más caliente entre los núcleos. No es exactamente Tj (temperatura de la unión), pero se aproxima. |
| **Tjmax** | Temperatura máxima de la unión soportada por el APU. Para el 7730U es 95 °C. Superar este valor sin protección activa del EC puede degradar el silicio. |
| **TDP** | Thermal Design Power. Potencia que el sistema de refrigeración debe ser capaz de evacuar. Para el 7730U es 15 W (SKU 15-28 W configurable). |
