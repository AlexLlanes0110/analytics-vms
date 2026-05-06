# Contrato CSV/JSON

## Propósito

Definir el contrato actual de entrada y salida para **VMS HealthCheck**.

Reglas base:

- **1 fila = 1 cámara / endpoint de video**.
- **OK real = `frames_ok == 1`**.
- `ffprobe` aporta metadata y diagnóstico, pero no declara una cámara OK.
- `black_detected` y `freeze_detected` son señales diagnósticas; no cambian el status final.

## Input CSV

El inventario de entrada mantiene una fila por cámara.

Columnas esperadas:

| Columna | Obligatoria | Descripción |
|---|---:|---|
| `project_code` | sí | Código del proyecto o despliegue. |
| `municipality` | sí | Municipio o ubicación administrativa. |
| `site_type` | sí | Tipo de sitio: `PMI` o `ARC`. |
| `site_code` | sí | Identificador corto del sitio. |
| `site_name` | sí | Nombre legible del sitio. |
| `traffic_direction` | no | Para `ARC`: `ENTRY` o `EXIT`; para `PMI`: vacío. |
| `camera_role` | sí | Rol lógico de la cámara. |
| `camera_name` | sí | Nombre legible de la cámara. |
| `brand` | sí | Marca o `unknown`. |
| `ip` | sí | IP o host del endpoint RTSP. |
| `rtsp_port` | sí | Puerto RTSP. |
| `rtsp_path` | sí para ejecución real | Path RTSP. |
| `transport` | sí | `tcp` o `udp`. |
| `credential_id` | recomendado | Referencia a credenciales externas al repo. |
| `username` | no | Solo para uso local/laboratorio. |
| `password` | no | Solo para uso local/laboratorio. |

Los archivos reales, IPs reales, credenciales reales y outputs reales no deben subirse al repo.

## Estados

| `status` | Significado |
|---|---|
| `OK` | `frames_ok == 1`; ffmpeg decodificó frames reales. |
| `PROBE_FAILED` | No se obtuvo metadata útil con ffprobe. |
| `NO_FRAMES` | ffprobe respondió, pero ffmpeg no decodificó frames reales. |
| `ERROR` | Fallo inesperado o error de construcción/ejecución. |

## CSV detallado por cámara

Campos:

| Columna | Tipo | Descripción |
|---|---|---|
| `camera_id` | string | Identificador estable usado por el resultado. |
| `camera_name` | string | Nombre de cámara desde el inventario, si está disponible. |
| `status` | string | `OK`, `PROBE_FAILED`, `NO_FRAMES` o `ERROR`. |
| `probe_ok` | int | `1` si ffprobe obtuvo metadata útil; `0` si no. |
| `frames_ok` | int | `1` si ffmpeg decodificó frames reales; `0` si no. |
| `black_detected` | int | `1` si blackdetect detectó señal; `0` si no. |
| `freeze_detected` | int | `1` si freezedetect detectó señal; `0` si no. |
| `error` | string | Mensaje sanitizado. |

Ejemplo:

```csv
camera_id,camera_name,status,probe_ok,frames_ok,black_detected,freeze_detected,error
DEMO-PMI-SITE001-PTZ,DEMO-PMI-SITE001-PTZ,OK,1,1,0,0,
DEMO-PMI-SITE002-PTZ,DEMO-PMI-SITE002-PTZ,PROBE_FAILED,0,0,0,0,probe failed on dummy endpoint
```

## CSV resumen global

Campos:

| Columna | Tipo |
|---|---|
| `total` | int |
| `ok` | int |
| `no_frames` | int |
| `probe_failed` | int |
| `error` | int |
| `black_detected` | int |
| `freeze_detected` | int |

Ejemplo:

```csv
total,ok,no_frames,probe_failed,error,black_detected,freeze_detected
5,2,1,1,1,1,0
```

## CSV resumen por sitio

El resumen por sitio se construye cruzando resultados con filas fuente por `camera_id`.

Campos:

| Columna | Tipo |
|---|---|
| `site_code` | string |
| `site_name` | string |
| `total` | int |
| `ok` | int |
| `no_frames` | int |
| `probe_failed` | int |
| `error` | int |
| `black_detected` | int |
| `freeze_detected` | int |

Ejemplo:

```csv
site_code,site_name,total,ok,no_frames,probe_failed,error,black_detected,freeze_detected
SITE001,DEMO-PMI-SITE001,2,2,0,0,0,1,0
SITE002,DEMO-PMI-SITE002,1,0,0,1,0,0,0
```

## JSON

El payload JSON mínimo contiene:

```json
{
  "summary": {},
  "summary_by_site": [],
  "details": []
}
```

Los campos internos son los mismos que los CSV correspondientes.
