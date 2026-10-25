# Documentación personal

Esta carpeta guarda notas e informes de incidencias del equipo. No es documentación de proyecto; es bitácora técnica para referencia futura del propio operador.

## Índice

- [`auditoria-2026-10-24.md`](./auditoria-2026-10-24.md) — auditoría completa del sistema y del repositorio dotfiles: estado térmico y de almacenamiento, plan de particionado para la reinstalación, mapa de secciones con veredictos, redundancias, inventario de acoplamiento a Omarchy, clasificación de cada paquete en conservar / eliminar / opcional, y correcciones de configuración pendientes.

- [`incidencias/`](./incidencias/) — informes post-mortem de eventos del sistema.
  - [`2026-10-20-apagones-termicos.md`](./incidencias/2026-10-20-apagones-termicos.md) — apagados silenciosos por protección térmica del EC, causada por governor `performance` + disipador saturado. Mitigación vía `cpufreq-stabilize.service`.
