# Roadmap de MVPs — VMS HealthCheck

## Principio del roadmap

El orden correcto del proyecto es:

1. contrato
2. documentación
3. motor CLI confiable
4. ejecución operativa controlada
5. visualización
6. histórico

---

## MVP-1 — Backend CLI

### Objetivo

Construir un CLI batch en Python que valide visualización real de cámaras vía RTSP y genere reportes CSV operativos.

### Incluye

- lectura de inventario desde CSV
- validación por fila y por cámara
- soporte para `PMI` y `ARC`
- `ffprobe` para metadata
- `ffmpeg` para extracción de frames
- `blackdetect`
- `freezedetect`
- output detallado por cámara
- output resumen por sitio
- evidencia local por corrida
- limpieza operativa local
- throttling operativo:
  - `batch_size = 15`
  - `max_workers = 3`

### No incluye

- UI
- dashboard
- histórico
- base de datos
- integración directa con VMS/BMS

---

## MVP-2 — Viewer básico / ejecución asistida

### Objetivo

Agregar una capa mínima de uso más cómoda sin cambiar el motor del CLI.

### Posibles entregables

- interfaz básica o viewer local
- carga de CSV desde interfaz
- acción para ejecutar el proceso
- tabla simple de resultados
- filtros básicos por sitio y estado

### No incluye todavía

- analítica histórica completa
- reporting avanzado
- correlaciones complejas

---

## MVP-3 — Dashboard e histórico

### Objetivo

Convertir el resultado operativo en una capa de observabilidad y reporting.

### Posibles entregables

- histórico por cámara
- histórico por sitio
- KPIs y tendencias
- comparativos por corrida
- dashboard
- visualización de degradación recurrente
- exportes adicionales