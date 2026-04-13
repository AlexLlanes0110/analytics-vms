# MVP-1 Spec — VMS HealthCheck (CLI)

## Objetivo

Implementar un CLI batch que reciba un CSV de cámaras y genere resultados de health check por cámara y por sitio.

El objetivo del MVP-1 es validar **video consumible** vía RTSP.  
El criterio central de éxito es:

- **OK real = frames decodificados exitosamente**
- No basta solo con conectividad o con que `ffprobe` responda

---

## Alcance del MVP-1

### Incluye

- Lectura de inventario desde CSV
- Procesamiento batch por cámara
- Soporte para sitios de tipo:
  - `PMI`
  - `ARC`
- Salida detallada por cámara
- Salida resumen por sitio
- Concurrencia controlada
- Ventanas y timeouts configurables
- Detección básica de:
  - black frames
  - freeze frames

### No incluye

- UI
- dashboard
- histórico en base de datos
- integración directa con VMS/BMS
- auto-discovery de RTSP por marca
- administración de credenciales dentro del repo

---

## Modelo de datos operativo

### Regla base

- **1 fila de input = 1 cámara**
- Un sitio puede contener múltiples cámaras
- Un sitio puede ser:
  - `PMI`
  - `ARC`

### Para `PMI`

Roles esperados:

- `PTZ`
- `FJ1`
- `FJ2`
- `FJ3`
- `LPR`

### Para `ARC`

Roles esperados:

- `FIXED_1`
- `FIXED_2`
- `LPR_1`
- `LPR_2`
- `LPR_3`
- `LPR_4`

y pueden repetirse por dirección operativa:

- `ENTRY`
- `EXIT`

---

## Entradas y salidas

### Entrada

CSV de inventario de cámaras según `docs/csv-contract.md`.

### Salidas

1. **Output detallado por cámara**
2. **Output resumen por sitio**

El output detallado sirve para operación y debugging.  
El resumen sirve para lectura rápida y para futura integración con dashboard.

---

## Estados normalizados (`output.status`)

| Estado | Significado |
|---|---|
| `OK` | Se lograron decodificar frames. |
| `DOWN` | No hubo conectividad real / timeout total / servicio inaccesible. |
| `NO_RTSP` | El endpoint es alcanzable pero falla negociación RTSP, auth o path. |
| `NO_FRAMES` | `ffprobe` respondió pero no se pudieron decodificar frames. |
| `ERROR` | Fallo inesperado no clasificado. |

### Regla principal

`status = OK` depende de `frames_ok = 1`.

---

## Pipeline por cámara (alto nivel)

1. **Preparación de contexto**
   - Leer fila de inventario
   - Resolver datos necesarios de ejecución
   - Preparar URL/parametrización RTSP

2. **(Opcional) Validación de conectividad**
   - Reachability básica
   - Puerto RTSP
   - Timeouts tempranos

3. **`ffprobe`**
   - Obtener metadata:
     - codec
     - width
     - height
     - fps

4. **`ffmpeg` — extracción de frames**
   - Intentar decodificar una ventana corta de video
   - Determinar `frames_ok`

5. **`ffmpeg` — detectores**
   - `blackdetect`
   - `freezedetect`

6. **Consolidación**
   - Calcular `status`
   - Calcular `failure_stage`
   - Escribir output detallado
   - Agregar resultado al resumen por sitio

---

## Interpretación de resultados

### Éxito real

Una cámara se considera operativamente **OK** cuando:

- se logra decodificar video
- `frames_ok = 1`

### Señales adicionales

Una cámara puede quedar en `OK` y aun así tener:

- `black_events > 0`
- `freeze_events > 0`

Eso significa que hay señal de video consumible, pero puede existir una alerta de calidad visual.  
En MVP-1 estas señales se reportan como métricas; no cambian automáticamente el estado central.

---

## Output detallado esperado

Debe incluir al menos:

- identidad del sitio
- identidad de la cámara
- IP
- `is_ok`
- `status`
- `failure_stage`
- metadata de `ffprobe`
- `frames_ok`
- eventos de black/freeze
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

## Configuración del CLI

Parámetros mínimos esperados:

- `workers`
  - default: `15`
  - máximo de cámaras procesadas en paralelo

- `batch-size`
  - default: `15`
  - procesa en bloques y permite escritura incremental

- timeouts
  - configurables

- ventanas de análisis
  - configurables

---

## Performance y red

Este proceso abre streams RTSP y genera tráfico.  
Por eso el MVP debe ejecutar con throttling controlado.

Recomendaciones iniciales:

- empezar con `workers=15`
- empezar con `batch-size=15`
- usar ventanas cortas de análisis
- evitar saturar red, cámaras o enlaces
- correr por ventanas horarias si aplica

---

## Evidencia

La evidencia puede incluir:

- logs locales
- frames temporales
- resultados intermedios

Reglas:

- es **local y temporal**
- no se versiona en GitHub
- no debe contener secretos en texto claro
- cualquier log debe redactar credenciales

---

## Seguridad operativa

- `examples/` solo contiene dummy
- archivos reales viven localmente, idealmente en `.local/`
- no se suben IPs reales
- no se suben credenciales
- no se suben outputs reales
- no se sube evidencia

---

## Criterios de aceptación del MVP-1

Se considera aceptable cuando:

1. lee un CSV válido de inventario
2. procesa filas como cámaras individuales
3. genera output detallado por cámara
4. genera output resumen por sitio
5. clasifica correctamente:
   - `OK`
   - `DOWN`
   - `NO_RTSP`
   - `NO_FRAMES`
   - `ERROR`
6. usa concurrencia controlada
7. no requiere UI
8. no escribe secretos ni evidencia al repo

---

## Limitaciones conocidas del MVP-1

- depende de que el inventario tenga datos RTSP válidos
- no resuelve automáticamente RTSP por marca
- no implementa dashboard
- no guarda histórico
- no integra base de datos
- no reemplaza monitoreo de red ni inventario completo de infraestructura
