# Roadmap de MVPs — VMS HealthCheck

## MVP-1 — CLI batch funcional

### Objetivo

Construir un CLI en Python que valide visualización real de cámaras vía RTSP y genere reportes CSV.

### Incluye

- lectura de inventario desde CSV
- validación por fila/cámara
- soporte para `PMI` y `ARC`
- `ffprobe` para metadata
- `ffmpeg` para extracción de frames
- detectores `blackdetect` / `freezedetect`
- output detallado por cámara
- output resumen por sitio
- evidencia local por corrida
- throttling operativo:
  - `batch_size = 15`
  - `max_workers = 3`
- limpieza local de `evidence/` y `output/` antes de una corrida nueva

### No incluye

- UI
- dashboard
- histórico
- base de datos
- integración directa con VMS/BMS

---

## MVP-2 — Ejecución asistida / viewer básico

### Objetivo

Agregar una capa mínima de uso más cómoda sin cambiar el motor del CLI.

### Posibles entregables

- frontend básico o viewer local
- carga de CSV desde interfaz
- botón o acción para ejecutar el proceso
- tabla simple de resultados
- filtros básicos por sitio / estado

### No incluye todavía

- analítica histórica completa
- correlaciones complejas
- reporting avanzado

---

## MVP-3 — Dashboard e histórico

### Objetivo

Convertir los resultados operativos en una capa de observabilidad y reporting.

### Posibles entregables

- histórico por cámara
- histórico por sitio
- KPIs y tendencias
- comparativos por corrida
- dashboard
- visualización de degradación recurrente
- exportación adicional de reportes

---

## Principio del roadmap

El orden correcto del proyecto es:

1. contrato
2. documentación
3. motor CLI confiable
4. ejecución operativa controlada
5. visualización
6. histórico
