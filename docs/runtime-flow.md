# Runtime Flow — VMS HealthCheck (MVP-1)

## Objetivo

Documentar el flujo operativo completo del sistema durante una corrida real del CLI.

Este documento describe:

- qué entra
- qué valida el sistema
- qué hace cada herramienta (`ffprobe`, `ffmpeg`, `blackdetect`, `freezedetect`)
- cómo se genera evidencia
- cómo se clasifican los estados finales
- cómo se controla la carga de red y CPU

---

## Resumen ejecutivo

El sistema **no** busca únicamente saber si una cámara responde por red.

El objetivo real es validar si la cámara:

1. es alcanzable por RTSP
2. entrega metadata de stream
3. permite decodificar frames reales
4. no presenta señales visuales relevantes de negro o congelamiento dentro de una ventana corta de prueba

La regla central es:

> **OK real = `frames_ok = 1`**

---

## Flujo end-to-end

### 1. Lectura del inventario

El CLI lee un CSV de inventario con una fila por cámara.

Cada fila contiene al menos:

- identidad del sitio
- identidad de la cámara
- marca
- IP
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
- existencia de `rtsp_path`
- existencia de método de autenticación resoluble
- valores esperados de `transport` y `rtsp_port`

También normaliza datos operativos cuando aplique, por ejemplo:

- marca en minúsculas
- vacíos consistentes
- strings sin espacios accidentales

---

### 3. Preparación de la corrida

Antes de iniciar la ejecución, el runtime prepara el entorno local.

### Entrada real

```text
.local/vms_input_real_local.csv
```

### Directorios de salida local

```text
.local/evidence/
.local/output/
```

### Política de limpieza

Para laboratorio y operación local controlada, la corrida debe:

- conservar `.local/vms_input_real_local.csv`
- limpiar el contenido previo de `.local/evidence/`
- limpiar el contenido previo de `.local/output/`
- recrear la estructura de salida para la nueva corrida

Esto evita acumulación innecesaria de JPGs, logs y CSVs antiguos.

---

### 4. División por bloques

El inventario completo no se procesa de una sola vez.

Se divide en bloques de:

- `batch_size = 15`

Dentro de cada bloque, la concurrencia real es:

- `max_workers = 3`

Interpretación:

- 15 cámaras por lote lógico
- 3 cámaras en simultáneo dentro de ese lote

Esto permite:

- reducir carga en CPU
- reducir tráfico RTSP simultáneo
- controlar uso de disco
- evitar saturar la red o el host local

---

## Pipeline por cámara

Cada cámara sigue el mismo pipeline.

---

### Etapa A — Construcción de URL RTSP

Con la información del CSV se forma el endpoint RTSP final usando:

- `username`
- `password`
- `ip`
- `rtsp_port`
- `rtsp_path`
- `transport`

Ejemplo conceptual:

```text
rtsp://<username>:<password>@<ip>:<rtsp_port><rtsp_path>
```

> En logs públicos o compartidos, la URL nunca debe exponerse con credenciales en texto claro.

---

### Etapa B — `ffprobe`

## ¿Para qué sirve?

`ffprobe` se usa para intentar abrir el stream y extraer metadata de video.

## ¿Qué extrae?

Normalmente:

- `codec`
- `width`
- `height`
- `fps`

## ¿Qué demuestra?

Demuestra que:

- el endpoint RTSP respondió suficientemente
- hubo negociación útil del stream
- existe metadata legible del video

## ¿Qué NO demuestra?

No demuestra por sí solo que la cámara esté realmente OK.

Puede ocurrir que:

- el host responda
- el RTSP negocie
- exista metadata
- pero no se logren decodificar frames reales

Por eso `ffprobe_ok = 1` **no es suficiente** para clasificar una cámara como `OK`.

---

### Etapa C — `ffmpeg` para extracción de frames

## ¿Para qué sirve?

Intentar decodificar frames reales de video dentro de una ventana corta.

## ¿Qué genera?

- varios JPG de evidencia
- un indicador operativo:
  - `frames_ok = 1` si la extracción fue exitosa
  - `frames_ok = 0` si no hubo decodificación útil

## ¿Qué demuestra?

Esta es la prueba fuerte de visualización real.

Si el sistema logra extraer frames válidos, entonces existe video consumible.

Por eso la regla central del MVP-1 es:

> **`frames_ok = 1` define el OK real**

---

### Etapa D — `blackdetect`

## ¿Para qué sirve?

Detectar periodos donde la imagen está negra durante una duración mínima.

## ¿Qué produce?

- un conteo de eventos:
  - `black_events`

## ¿Qué interpreta el sistema?

Si `black_events > 0`, existe señal de imagen negra dentro de la ventana analizada.

## Importante

`black_events` no cambia por sí solo el estado central en MVP-1.

Se reporta como señal diagnóstica adicional de calidad visual.

---

### Etapa E — `freezedetect`

## ¿Para qué sirve?

Detectar periodos donde la imagen está congelada, es decir, el stream sigue “vivo” pero los frames no cambian como deberían.

## ¿Qué produce?

- un conteo de eventos:
  - `freeze_events`

## ¿Qué interpreta el sistema?

Si `freeze_events > 0`, existe señal de congelamiento dentro de la ventana analizada.

## Importante

`freeze_events` tampoco cambia por sí solo el estado central en MVP-1.

Se reporta como señal diagnóstica adicional de calidad visual.

---

### Etapa F — Consolidación

Con la información anterior se calculan:

- `is_ok`
- `status`
- `failure_stage`
- `error_type`
- `error_msg_short`

Y se escribe el resultado detallado por cámara.

Después, los resultados se agregan para generar el resumen por sitio.

---

## Estados finales

### `OK`

Usar cuando:

- se lograron decodificar frames reales
- `frames_ok = 1`

Notas:

- puede coexistir con `black_events > 0` o `freeze_events > 0`
- en MVP-1 esas señales no degradan automáticamente el estado central

---

### `DOWN`

Usar cuando:

- hubo timeout total
- el servicio no fue alcanzable
- no hubo conectividad útil hacia el stream
- hubo falla temprana de acceso al endpoint

Etapa típica:

- `CONNECT`

---

### `NO_RTSP`

Usar cuando:

- el host puede existir o responder
- pero falla auth/path/negociación RTSP
- `ffprobe` no logra obtener metadata útil

Ejemplos típicos:

- credenciales inválidas
- path RTSP inválido
- negociación RTSP fallida

Etapa típica:

- `FFPROBE`

---

### `NO_FRAMES`

Usar cuando:

- hubo metadata o negociación útil
- pero `ffmpeg` no logró decodificar frames válidos
- `frames_ok = 0`

Etapa típica:

- `FRAMES`

---

### `ERROR`

Usar cuando:

- ocurrió una excepción inesperada
- hubo fallo no clasificable
- falló alguna etapa de forma no normalizada

Etapas típicas:

- `DETECT`
- `UNEXPECTED`

---

## Interpretación correcta

La lógica operativa correcta es esta:

- conectividad **no equivale** a visualización real
- metadata **no equivale** a visualización real
- visualización real = frames decodificados
- negro y congelamiento son señales diagnósticas de calidad visual

En consecuencia:

- `ffprobe_ok = 1` no basta para `OK`
- `frames_ok = 1` sí define `OK`
- `black_events` y `freeze_events` enriquecen el análisis, pero no redefinen el estado central en MVP-1

---

## Artefactos locales de una corrida

Ejemplo de layout esperado:

```text
.local/
├─ vms_input_real_local.csv
├─ evidence/
│  └─ 2026-04-17_230000/
│     ├─ CAM_001/
│     │  ├─ probe.txt
│     │  ├─ detect.txt
│     │  └─ frames/
│     │     ├─ frame_01.jpg
│     │     ├─ frame_02.jpg
│     │     ├─ frame_03.jpg
│     │     ├─ frame_04.jpg
│     │     └─ frame_05.jpg
│     └─ CAM_002/
└─ output/
   └─ 2026-04-17_230000/
      ├─ vms_output_real_detailed.csv
      └─ vms_output_real_summary_by_site.csv
```

---

## Escritura incremental

La corrida debe ir escribiendo resultados conforme avanza.

Ventajas:

- mejor trazabilidad
- menor riesgo de perder todo si hay una falla a mitad de ejecución
- menos presión sobre memoria
- más claridad operativa por lote

---

## Parámetros operativos iniciales recomendados

Valores de arranque para MVP-1:

- `batch_size = 15`
- `max_workers = 3`
- `transport = tcp`
- ventanas cortas de análisis
- timeouts externos consistentes

La intención es priorizar estabilidad y control de carga sobre velocidad máxima.

---

## Reglas de seguridad durante la ejecución

- no guardar credenciales reales en el repo
- no exponer URLs con auth en logs compartidos
- no versionar evidencia ni outputs reales
- no subir JPGs, `probe.txt`, `detect.txt` ni CSVs reales
- mantener todo lo real dentro de `.local/`

---

## Cierre

El flujo correcto del sistema es:

```text
CSV → validación → RTSP → ffprobe → frames → black/freeze → status → detailed CSV → summary CSV
```

y la regla central sigue siendo:

> **una cámara solo está realmente OK si hay frames decodificables**