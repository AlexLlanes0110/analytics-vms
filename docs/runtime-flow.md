# Runtime Flow — VMS HealthCheck (MVP-1)

## Objetivo

Documentar el flujo operativo completo de una corrida real del CLI.

Este documento describe:

- qué entra
- qué valida el sistema
- qué hace cada herramienta
- cómo se genera evidencia
- cómo se clasifican los estados finales
- cómo se controla la carga de red y CPU

---

## Regla central

> **OK real = `frames_ok = 1`**

El runtime no busca únicamente saber si una cámara responde por red.

La validación real es:

1. si el endpoint RTSP negocia algo útil
2. si existe metadata de stream
3. si se pueden decodificar frames reales
4. si aparecen señales diagnósticas de negro o congelamiento

---

## Flujo end-to-end

### 1. Lectura del inventario

El CLI lee un CSV de inventario con **una fila por cámara**.

Cada fila contiene, al menos:

- identidad del sitio
- identidad de la cámara
- marca
- IP o host
- puerto RTSP
- path RTSP
- transporte
- credenciales o referencia a credenciales

---

### 2. Validación y normalización

Antes de abrir streams, el sistema valida:

- header del CSV
- valores permitidos para `site_type`
- coherencia entre `site_type` y `camera_role`
- regla de `traffic_direction`
- presencia de `rtsp_path`
- existencia de método de autenticación resoluble
- valores esperados para `transport`
- valores esperados para `rtsp_port`

También normaliza datos operativos cuando aplique:

- strings sin espacios accidentales
- marca en formato consistente
- vacíos uniformes
- campos derivados listos para construir la URL RTSP

---

### 3. Preparación de la corrida

Antes de ejecutar, el runtime prepara el entorno local.

#### Input real esperado

```text
.local/vms_input_real_local.csv
```

#### Directorios de salida

```text
.local/evidence/
.local/output/
```

#### Política de limpieza

Para laboratorio y operación local controlada, la corrida debe:

- conservar `.local/vms_input_real_local.csv`
- limpiar el contenido previo de `.local/evidence/`
- limpiar el contenido previo de `.local/output/`
- recrear estructura limpia para la nueva corrida

Esto evita acumular JPGs, logs y CSVs viejos.

---

### 4. División por bloques

El inventario completo no se procesa de una sola vez.

#### Decisión operativa cerrada

- `batch_size = 15`
- `max_workers = 3`

#### Interpretación

- 15 cámaras por lote lógico
- 3 cámaras en simultáneo dentro de ese lote

#### Objetivo

- reducir carga en CPU
- reducir tráfico RTSP simultáneo
- controlar uso de disco
- evitar saturar la red o el host local

---

### 5. Pipeline por cámara

Cada cámara sigue el mismo pipeline.

#### 5.1 Preparación de contexto

- tomar fila normalizada
- construir URL RTSP
- resolver autenticación
- preparar carpetas de evidencia

#### 5.2 `ffprobe`

Se ejecuta `ffprobe` para intentar obtener metadata del stream.

Se busca, cuando exista:

- codec
- width
- height
- fps

Resultado típico:

- `ffprobe_ok = 1` si hubo metadata utilizable
- `ffprobe_ok = 0` si no se logró abrir o leer el stream

Importante:

`ffprobe_ok = 1` **no implica** automáticamente que la cámara esté `OK`.

#### 5.3 `ffmpeg` para frames

Se ejecuta una ventana corta de prueba para intentar **decodificar frames reales**.

Resultado central:

- `frames_ok = 1` si hubo frames válidos
- `frames_ok = 0` si no se logró decodificar video útil

Este es el criterio principal para `OK`.

#### 5.4 `blackdetect`

Se analiza la ventana para detectar periodos de imagen negra.

Resultado:

- `black_events`

#### 5.5 `freezedetect`

Se analiza la ventana para detectar periodos de imagen congelada.

Resultado:

- `freeze_events`

#### 5.6 Consolidación

Se calculan:

- `status`
- `failure_stage`
- métricas técnicas
- error resumido
- evidencia local

---

### 6. Mapeo de estado final

#### `OK`

Cuando `frames_ok == 1`.

#### `PROBE_FAILED`

Cuando `ffprobe` no obtuvo metadata útil. Esto incluye cámaras o endpoints RTSP que no responden a la prueba de metadata.

#### `NO_FRAMES`

Cuando `ffprobe` respondió, pero `ffmpeg` no pudo decodificar frames reales.

#### `ERROR`

Cuando ocurre un fallo inesperado del software, construcción o excepción.

---

### 7. Interpretación de negro y congelamiento

En MVP-1:

- `black_events`
- `freeze_events`

son métricas diagnósticas.

No cambian automáticamente el estado central.

Ejemplo:

- una cámara puede quedar `OK`
- y además registrar `black_events > 0`
- o `freeze_events > 0`

Eso significa:

- sí hubo video consumible
- pero existe una alerta de calidad visual

---

### 8. Evidencia por corrida

La evidencia es local, temporal y no se versiona en GitHub.

#### Layout esperado

```text
.local/
├─ evidence/
│  └─ <run_id>/
│     └─ <camera_name>/
│        ├─ probe.txt
│        ├─ detect.txt
│        └─ frames/
│           ├─ frame_01.jpg
│           ├─ frame_02.jpg
│           └─ ...
└─ output/
   └─ <run_id>/
      ├─ vms_output_real_detailed.csv
      └─ vms_output_real_summary_by_site.csv
```

#### Reglas de evidencia

- no se versiona
- no debe contener secretos visibles
- credenciales deben redactarse en logs
- outputs reales no se suben al repo

---

### 9. Escritura de resultados

El sistema debe escribir:

1. output detallado por cámara
2. output resumen por sitio

La escritura puede ser incremental por lote para reducir riesgo de pérdida de resultados en corridas largas.

---

### 10. Resumen operativo

La corrida correcta del MVP-1 se interpreta así:

1. leer CSV
2. validar y normalizar
3. preparar `.local/`
4. dividir en bloques de 15
5. procesar con máximo 3 concurrentes
6. ejecutar pipeline por cámara
7. generar evidencia local
8. escribir outputs
9. conservar input real
10. limpiar evidencia y output antes de la siguiente corrida, si así se configura
