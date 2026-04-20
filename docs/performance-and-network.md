# Performance and Network — VMS HealthCheck

## Objetivo

Definir reglas operativas para controlar carga de red, CPU, disco y memoria durante la ejecución del health check.

Este sistema abre múltiples streams RTSP, decodifica video y escribe evidencia local. Si se ejecuta sin control, puede:

- saturar CPU
- generar demasiado tráfico simultáneo
- castigar disco por escritura de JPGs y logs
- afectar la estabilidad del host local
- presionar innecesariamente a las cámaras o a la red

---

## Principio general

El MVP-1 prioriza **estabilidad y control de carga** sobre velocidad máxima.

No se busca procesar todas las cámaras al mismo tiempo.

---

## Decisión operativa cerrada

### Lote lógico

- `batch_size = 15`

Interpretación:

- el inventario total se divide en bloques de 15 cámaras

### Concurrencia real

- `max_workers = 3`

Interpretación:

- dentro de cada lote, solo 3 cámaras se procesan en simultáneo

### Flujo real

- tomar 15 cámaras
- procesarlas con máximo 3 concurrentes
- guardar evidencia y resultados
- continuar con las siguientes 15

---

## Justificación de esta decisión

### 1. Red

Cada stream RTSP consume ancho de banda real.

Si se abren demasiados streams simultáneos:

- se incrementa el tráfico de red
- se puede afectar el enlace hacia las cámaras
- se puede presionar el switch, el host o segmentos intermedios

### 2. CPU

`ffmpeg` y `ffprobe` consumen CPU, especialmente durante:

- apertura de stream
- negociación
- decodificación de video
- filtros de detección

### 3. Disco

Cada corrida puede generar:

- `probe.txt`
- `detect.txt`
- varios JPG por cámara
- CSVs de salida

Sin limpieza o control, esto crece rápido.

### 4. Estabilidad operativa

La máquina local de ejecución no se asume como un servidor sobrado de recursos.

Por eso el runtime debe ser conservador.

---

## Recomendaciones técnicas del MVP-1

### Transporte

Usar preferentemente:

- `transport = tcp`

Motivo:

- mayor estabilidad operativa para RTSP en entornos reales de red

### Timeouts

Usar timeouts externos y consistentes.

Motivo:

- comportamiento más controlable y reproducible que depender solo de timeouts internos de herramientas

### Ventanas de análisis

Usar ventanas cortas.

Objetivo:

- validar visualización real sin abrir streams más tiempo del necesario
- reducir tráfico y CPU
- evitar pruebas excesivamente largas

---

## Valores iniciales recomendados

Estos valores son una base operativa inicial y pueden quedar configurables en el CLI.

### `ffprobe`

- timeout corto
- extraer únicamente:
  - `codec`
  - `width`
  - `height`
  - `fps`

### Extracción de frames

- extraer pocos frames de evidencia
- objetivo operativo inicial:
  - 5 frames
  - frecuencia baja de captura
  - ventana corta

### Detectores

Base inicial recomendada:

- `blackdetect=d=1.0:pix_th=0.10`
- `freezedetect=n=0.003:d=5`

Estas configuraciones deben permanecer configurables para futuros ajustes si cambian condiciones reales de escena.

---

## Escritura incremental

Los resultados no deben esperar hasta el final de todo el inventario.

Se recomienda:

- consolidar resultados por cámara
- ir acumulando el resumen por sitio
- escribir outputs conforme avanza la corrida

Ventajas:

- menos riesgo si el proceso se interrumpe
- mejor trazabilidad
- menos presión sobre memoria
- más facilidad de debugging

---

## Evidencia local

La evidencia debe almacenarse solo en local, bajo `.local/evidence/`.

Ejemplo:

```text
.local/evidence/<run_id>/<camera_name>/
```

Artefactos típicos:

- `probe.txt`
- `detect.txt`
- `frames/*.jpg`

---

## Output local

Los CSV reales deben almacenarse solo en local, bajo `.local/output/`.

Ejemplo:

```text
.local/output/<run_id>/
```

Archivos esperados:

- `vms_output_real_detailed.csv`
- `vms_output_real_summary_by_site.csv`

---

## Política de limpieza

Para evitar acumulación de artefactos antiguos, se define la siguiente política operativa de laboratorio:

### Antes de cada nueva corrida

- conservar `.local/vms_input_real_local.csv`
- limpiar `.local/evidence/`
- limpiar `.local/output/`

### Después

- recrear la estructura para la corrida nueva
- generar solo evidencia y outputs actuales

### Motivo

- evitar crecimiento innecesario en disco
- evitar mezclar resultados viejos con resultados actuales
- simplificar análisis operativo

---

## Qué no debe hacerse

- no correr todas las cámaras en paralelo
- no dejar evidencia histórica crecer indefinidamente
- no almacenar evidencia real en el repo
- no usar valores de concurrencia agresivos sin validar carga real
- no dejar ventanas de stream más largas de lo necesario

---

## Reglas de ajuste futuro

Si más adelante se quiere optimizar rendimiento, el orden correcto es:

1. medir consumo real
2. revisar CPU
3. revisar tráfico
4. revisar tiempos promedio por cámara
5. ajustar primero `max_workers`
6. ajustar después `batch_size`

No aumentar ambos parámetros a la vez sin medir impacto.

---

## Conclusión

La decisión operativa de MVP-1 es:

- `batch_size = 15`
- `max_workers = 3`

porque equilibra:

- control de tráfico
- estabilidad del host
- seguridad operativa
- evidencia suficiente
- ejecución reproducible
