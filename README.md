# VMS HealthCheck

Herramientas Python para validar cámaras VMS/RTSP desde un inventario CSV y producir reportes operativos.

## Regla funcional central

> **OK real = `frames_ok == 1`**

Una cámara se considera OK solo cuando `ffmpeg` logra decodificar frames reales de video.

No basta con que:

- el host responda
- el puerto RTSP abra
- `ffprobe` devuelva metadata

`ffprobe` aporta señales diagnósticas, pero no declara una cámara OK.

## Flujo actual

Entrada:

- CSV de inventario, con **1 fila = 1 cámara**.

Proceso por cámara:

- validación y normalización de fila
- construcción de URL RTSP
- `ffprobe` para metadata
- `ffmpeg` para validación de frames reales
- detectores opcionales `blackdetect` y `freezedetect`
- resultado estructurado en memoria

Salida actual:

- CSV detallado por cámara
- CSV resumen global
- CSV resumen por sitio
- payload JSON mínimo

CLI operador:

```bash
python3 -m analytics_vms.cli check-cameras INVENTORY.csv --out-dir OUTPUT_DIR
```

## Estados actuales

| `status` | Significado |
|---|---|
| `OK` | `frames_ok == 1`; se decodificaron frames reales. |
| `PROBE_FAILED` | `ffprobe` no obtuvo metadata útil. |
| `NO_FRAMES` | `ffprobe` respondió, pero `ffmpeg` no decodificó frames reales. |
| `ERROR` | Fallo inesperado o error de construcción/ejecución. |

`black_detected` y `freeze_detected` son señales diagnósticas. No cambian el status final.

## Reporte detallado

Campos actuales:

```text
project_code
municipality
site_type
site_code
site_name
traffic_direction
camera_role
camera_name
brand
ip
rtsp_port
rtsp_path
transport
camera_id
status
probe_ok
frames_ok
black_detected
freeze_detected
error
```

No se incluyen `username`, `password`, `credential_id` ni URLs RTSP completas en
los reportes.

## Reporte resumen

Campos actuales:

```text
total
ok
no_frames
probe_failed
error
black_detected
freeze_detected
```

## Reporte resumen por sitio

Campos actuales:

```text
site_code
site_name
total
ok
no_frames
probe_failed
error
black_detected
freeze_detected
```

El resumen por sitio cruza resultados con filas fuente usando `camera_id`.

## Archivos dummy

```text
examples/
├─ vms_input_dummy_repo.csv
├─ vms_output_dummy_detailed_example.csv
├─ vms_output_dummy_summary_example.csv
└─ vms_output_dummy_summary_by_site_example.csv
```

## Seguridad

Todo lo real debe vivir fuera del repo, en `.local/`.

No se deben subir:

- IPs reales
- credenciales reales
- CSV reales
- outputs reales
- evidencia o logs sensibles

## Documentación clave

- `docs/csv-contract.md` - contrato actual de entrada y salida
