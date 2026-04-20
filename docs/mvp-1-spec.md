# MVP-1 Spec — VMS HealthCheck

## Objetivo

Definir el comportamiento funcional del MVP-1 del sistema.

El MVP-1 consiste en un **CLI batch en Python** que lee un inventario de cámaras desde CSV, ejecuta validaciones RTSP por cámara y genera dos salidas:

1. output detallado por cámara
2. output resumen por sitio

---

## Criterio funcional central

> **OK real = `frames_ok = 1`**

El criterio de éxito operativo no es únicamente la conectividad ni la existencia de metadata, sino la capacidad de **decodificar frames reales**.

No basta con:

- reachability de red
- puerto RTSP abierto
- respuesta parcial del endpoint
- metadata disponible por `ffprobe`

---

## Alcance del MVP-1

### Incluye

- lectura de inventario desde CSV
- validación del contrato de entrada
- normalización de datos por fila
- soporte para sitios `PMI` y `ARC`
- construcción de URL RTSP por cámara
- `ffprobe` para metadata
- `ffmpeg` para extracción de frames
- `blackdetect`
- `freezedetect`
- clasificación de estado final
- output detallado por cámara
- output resumen por sitio
- evidencia local por corrida
- concurrencia controlada
- limpieza operativa opcional previa a una corrida

### No incluye

- UI
- dashboard
- histórico en base de datos
- integración directa con VMS/BMS
- auto-discovery RTSP por marca
- gestión de credenciales dentro del repo
- monitoreo continuo tipo daemon

---

## Modelo de datos operativo

### Regla base

> **1 fila de input = 1 cámara**

### Tipos de sitio soportados

- `PMI`
- `ARC`

### Roles esperados para `PMI`

- `PTZ`
- `FJ1`
- `FJ2`
- `FJ3`
- `LPR`

### Roles esperados para `ARC`

- `FIXED_1`
- `FIXED_2`
- `LPR_1`
- `LPR_2`
- `LPR_3`
- `LPR_4`

### Dirección operativa

- para `PMI`, `traffic_direction` debe ir vacío
- para `ARC`, `traffic_direction` puede ser `ENTRY` o `EXIT`

---

## Entradas y salidas

### Entrada

CSV de inventario conforme a `docs/csv-contract.md`.

### Salidas

1. **Output detallado por cámara**
2. **Output resumen por sitio**

El output detallado sirve para operación y debugging.

El output resumen sirve para lectura rápida y para una futura capa de visualización.

---

## Estados normalizados

- `OK`
- `DOWN`
- `NO_RTSP`
- `NO_FRAMES`
- `ERROR`

### Regla principal

`status = OK` depende exclusivamente de `frames_ok = 1`.

### Significado de estados

#### `OK`

Se lograron decodificar frames reales.

#### `DOWN`

No hubo conectividad útil o el servicio fue inaccesible.

#### `NO_RTSP`

El endpoint responde en algún nivel, pero falla la negociación RTSP, auth o path.

#### `NO_FRAMES`

Hubo metadata o negociación suficiente, pero no se lograron decodificar frames.

#### `ERROR`

Ocurrió un fallo inesperado no clasificado.

---

## Pipeline por cámara

Cada cámara debe seguir este flujo lógico:

1. leer fila del inventario
2. validar reglas mínimas
3. normalizar datos
4. preparar URL y parámetros RTSP
5. ejecutar `ffprobe`
6. ejecutar `ffmpeg` para frames
7. ejecutar `blackdetect` y `freezedetect`
8. consolidar métricas
9. mapear `status`
10. escribir resultado detallado
11. contribuir al resumen por sitio

---

## Interpretación de resultados

### Éxito real

Una cámara está operativamente **OK** cuando:

- se logró decodificar video
- `frames_ok = 1`

### Señales adicionales

Una cámara puede quedar en `OK` y además traer:

- `black_events > 0`
- `freeze_events > 0`

En MVP-1 estas señales **no cambian automáticamente** el estado central. Se reportan como métricas diagnósticas.

---

## Output detallado esperado

Debe incluir al menos:

- identidad del sitio
- identidad de la cámara
- IP
- `is_ok`
- `status`
- `failure_stage`
- metadata relevante de `ffprobe`
- `frames_ok`
- `black_events`
- `freeze_events`
- error resumido

---

## Output resumen esperado

Debe incluir por sitio:

- `total_cameras`
- `ok_cameras`
- `failed_cameras`
- `down_count`
- `no_rtsp_count`
- `no_frames_count`
- `error_count`

---

## Configuración mínima del CLI

Parámetros esperados:

- `batch_size`
- `max_workers`
- timeouts
- ventanas de análisis
- política de limpieza previa

### Defaults operativos cerrados para MVP-1

- `batch_size = 15`
- `max_workers = 3`

Interpretación:

- el inventario se divide en lotes de 15
- dentro de cada lote solo 3 cámaras se procesan en paralelo

---

## Evidencia y output real

### Evidencia local por corrida

Puede incluir:

- `probe.txt`
- `detect.txt`
- frames JPG
- logs intermedios redactados

### Layout esperado

```text
.local/
├─ vms_input_real_local.csv
├─ evidence/
│  └─ <run_id>/
│     └─ <camera_name>/
│        ├─ probe.txt
│        ├─ detect.txt
│        └─ frames/
└─ output/
   └─ <run_id>/
      ├─ vms_output_real_detailed.csv
      └─ vms_output_real_summary_by_site.csv
```

---

## Limpieza operativa

Antes de iniciar una corrida nueva, el runtime debe poder:

- conservar `.local/vms_input_real_local.csv`
- limpiar `.local/evidence/`
- limpiar `.local/output/`
- recrear estructura limpia

Objetivo:

- evitar crecimiento innecesario de disco
- evitar mezclar evidencia vieja con evidencia nueva

---

## Criterios de aceptación del MVP-1

Se considera aceptable cuando el sistema:

1. lee un CSV válido de inventario
2. procesa cada fila como una cámara individual
3. clasifica correctamente `OK`, `DOWN`, `NO_RTSP`, `NO_FRAMES` y `ERROR`
4. genera output detallado por cámara
5. genera output resumen por sitio
6. usa concurrencia controlada
7. genera evidencia local por corrida
8. respeta la política de limpieza configurada
9. no requiere UI
10. no escribe secretos ni evidencia al repo

---

## Limitaciones conocidas

- depende de que el inventario tenga datos RTSP válidos
- no resuelve RTSP automáticamente por marca
- no implementa dashboard
- no guarda histórico
- no integra base de datos
- no reemplaza monitoreo de red