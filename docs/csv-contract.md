# Contrato CSV

## Propósito

Definir el contrato de entrada y salida para **VMS HealthCheck (MVP-1)**.

Regla base del modelo:

- **1 fila = 1 cámara / endpoint de video**
- El sistema procesa cámaras individualmente
- Los resultados se pueden agrupar después por **sitio**
- Un sitio puede ser de tipo:
  - `PMI`
  - `ARC`

---

## Input CSV (MVP-1)

### Objetivo

Representar inventario operativo mínimo para ejecutar health checks RTSP.

### Columnas

| Columna | Tipo | Obligatoria | Valores / ejemplo | Descripción |
|---|---|---:|---|---|
| `project_code` | string | sí | `DEMO01` | Código del proyecto o despliegue. |
| `municipality` | string | sí | `Sample Municipality` | Municipio o ubicación administrativa. |
| `site_type` | string | sí | `PMI`, `ARC` | Tipo de sitio. |
| `site_code` | string | sí | `SITE001` | Identificador corto del sitio. |
| `site_name` | string | sí | `DEMO-PMI-SITE-001` | Nombre legible completo del sitio. |
| `traffic_direction` | string | no | `ENTRY`, `EXIT`, vacío | Dirección operativa. Para `ARC` se recomienda usar `ENTRY` o `EXIT`. Para `PMI` va vacío. |
| `camera_role` | string | sí | `PTZ`, `FJ1`, `FJ2`, `FJ3`, `LPR`, `FIXED_1`, `FIXED_2`, `LPR_1`, `LPR_2`, `LPR_3`, `LPR_4` | Rol lógico de la cámara dentro del sitio. |
| `camera_name` | string | sí | `DEMO-PMI-SITE-001-PTZ` | Nombre legible completo de la cámara. |
| `brand` | string | sí | `hikvision`, `dahua`, `huawei`, `axis`, `unknown` | Marca o `unknown` si aún no se conoce. |
| `ip` | string | sí | `192.0.2.10` | IP o host del endpoint RTSP. |
| `rtsp_port` | int | sí | `554` | Puerto RTSP. Default recomendado: `554`. |
| `rtsp_path` | string | sí para ejecución real | `/Streaming/Channels/101` | Path RTSP. En examples/dummy puede venir como ejemplo; en ejecución real debe existir. |
| `transport` | string | sí | `tcp`, `udp` | Transporte RTSP. Default recomendado: `tcp`. |
| `credential_id` | string | recomendado | `cred_demo_site001` | Referencia a credenciales resueltas fuera del repo. |
| `username` | string | no | `admin` | Solo para pruebas locales/laboratorio. Nunca se sube a GitHub. |
| `password` | string | no | `secret` | Solo para pruebas locales/laboratorio. Nunca se sube a GitHub. |

---

## Reglas de validación del input

1. `site_type` debe ser `PMI` o `ARC`.
2. `camera_role` debe ser coherente con `site_type`:
   - Para `PMI`:
     - `PTZ`
     - `FJ1`
     - `FJ2`
     - `FJ3`
     - `LPR`
   - Para `ARC`:
     - `FIXED_1`
     - `FIXED_2`
     - `LPR_1`
     - `LPR_2`
     - `LPR_3`
     - `LPR_4`
3. Para `ARC`, `traffic_direction` debería ser `ENTRY` o `EXIT`.
4. Para `PMI`, `traffic_direction` debería ir vacío.
5. `brand` puede ser `unknown` mientras se completa el inventario.
6. Para ejecución real, debe existir alguna forma de autenticación resoluble:
   - `credential_id`, o
   - `username` + `password`
7. Para ejecución real, `rtsp_path` no debe venir vacío.

---

## Ejemplo de input

```csv
project_code,municipality,site_type,site_code,site_name,traffic_direction,camera_role,camera_name,brand,ip,rtsp_port,rtsp_path,transport,credential_id,username,password
DEMO01,Sample Municipality,PMI,SITE001,DEMO-PMI-SITE-001,,PTZ,DEMO-PMI-SITE-001-PTZ,unknown,192.0.2.10,554,/Streaming/Channels/101,tcp,cred_demo_site001,,
DEMO01,Sample Municipality,ARC,SITE002,DEMO-ARC-SITE-002,ENTRY,LPR_1,DEMO-ARC-SITE-002-ENTRY-LPR_1,unknown,192.0.2.20,554,/Streaming/Channels/101,tcp,cred_demo_site002,,
```

---

## Output CSV detallado (MVP-1)

### Objetivo

Registrar el resultado por cámara, indicando si hubo video consumible y en qué etapa falló si no lo hubo.

### Columnas

| Columna | Tipo | Descripción |
|---|---|---|
| `project_code` | string | Copia desde input. |
| `municipality` | string | Copia desde input. |
| `site_type` | string | Copia desde input. |
| `site_code` | string | Copia desde input. |
| `site_name` | string | Copia desde input. |
| `traffic_direction` | string | Copia desde input. |
| `camera_role` | string | Copia desde input. |
| `camera_name` | string | Copia desde input. |
| `ip` | string | Copia desde input. |
| `is_ok` | int | `1` si la cámara entrega video consumible; `0` si no. |
| `status` | string | Estado normalizado: `OK`, `DOWN`, `NO_RTSP`, `NO_FRAMES`, `ERROR`. |
| `failure_stage` | string | Etapa donde falló: `CONNECT`, `FFPROBE`, `FRAMES`, `DETECT`, `UNEXPECTED`, o vacío si fue `OK`. |
| `ffprobe_ok` | int | `1` si ffprobe obtuvo metadata; `0` si no. |
| `codec` | string | Codec detectado, si aplica. |
| `width` | int | Ancho detectado, si aplica. |
| `height` | int | Alto detectado, si aplica. |
| `fps` | number | FPS detectados, si aplica. |
| `frames_ok` | int | `1` si se lograron decodificar frames; `0` si no. |
| `black_events` | int | Cantidad de eventos detectados por `blackdetect`. |
| `freeze_events` | int | Cantidad de eventos detectados por `freezedetect`. |
| `error_type` | string | Clasificación resumida del error. |
| `error_msg_short` | string | Mensaje corto del error. |

---

## Significado de `status`

| `status` | Significado |
|---|---|
| `OK` | Se decodificaron frames exitosamente. |
| `DOWN` | No hubo conectividad real o hubo timeout total. |
| `NO_RTSP` | Hubo problema de negociación RTSP, auth o path; `ffprobe` falló. |
| `NO_FRAMES` | `ffprobe` funcionó, pero no se lograron decodificar frames. |
| `ERROR` | Fallo inesperado no clasificado en las categorías anteriores. |

### Regla clave

**El criterio principal de OK es `frames_ok = 1`.**

Los detectores `black_events` y `freeze_events` son señales adicionales de calidad visual, pero no reemplazan el criterio central de video consumible.

---

## Ejemplo de output detallado

```csv
project_code,municipality,site_type,site_code,site_name,traffic_direction,camera_role,camera_name,ip,is_ok,status,failure_stage,ffprobe_ok,codec,width,height,fps,frames_ok,black_events,freeze_events,error_type,error_msg_short
DEMO01,Sample Municipality,PMI,SITE001,DEMO-PMI-SITE-001,,PTZ,DEMO-PMI-SITE-001-PTZ,192.0.2.10,1,OK,,1,h264,1920,1080,30,1,0,0,,
DEMO01,Sample Municipality,ARC,SITE002,DEMO-ARC-SITE-002,ENTRY,LPR_1,DEMO-ARC-SITE-002-ENTRY-LPR_1,192.0.2.20,0,NO_RTSP,FFPROBE,0,,,,,0,0,0,rtsp,rtsp auth/path negotiation failed
```

---

## Output CSV resumen por sitio (MVP-1)

### Objetivo

Facilitar lectura operativa y futura integración con dashboard.

### Columnas

| Columna | Tipo | Descripción |
|---|---|---|
| `project_code` | string | Código de proyecto. |
| `municipality` | string | Municipio. |
| `site_type` | string | `PMI` o `ARC`. |
| `site_code` | string | Código corto del sitio. |
| `site_name` | string | Nombre legible del sitio. |
| `total_cameras` | int | Total de cámaras procesadas para ese sitio. |
| `ok_cameras` | int | Total con `status = OK`. |
| `failed_cameras` | int | Total que no quedaron en `OK`. |
| `down_count` | int | Total `DOWN`. |
| `no_rtsp_count` | int | Total `NO_RTSP`. |
| `no_frames_count` | int | Total `NO_FRAMES`. |
| `error_count` | int | Total `ERROR`. |

### Regla

`failed_cameras = total_cameras - ok_cameras`

---

## Ejemplo de output resumen

```csv
project_code,municipality,site_type,site_code,site_name,total_cameras,ok_cameras,failed_cameras,down_count,no_rtsp_count,no_frames_count,error_count
DEMO01,Sample Municipality,PMI,SITE001,DEMO-PMI-SITE-001,5,4,1,0,1,0,0
DEMO01,Sample Municipality,ARC,SITE002,DEMO-ARC-SITE-002,12,9,3,1,1,1,0
```

---

## Notas de seguridad y operación

- Los archivos dummy para documentación viven en `examples/`.
- Los archivos reales viven localmente fuera del repo, idealmente en `.local/`.
- Nunca se suben IPs reales, credenciales reales, resultados reales ni evidencia a GitHub.