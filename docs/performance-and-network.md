# Performance and Network — VMS HealthCheck

## Objetivo

Definir reglas operativas para controlar carga de red, CPU, disco y memoria durante la ejecución del health check.

Este sistema abre múltiples streams RTSP, decodifica video y escribe evidencia local. Sin control, puede saturar recursos o volver inestable la ejecución.

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

1. tomar 15 cámaras
2. procesarlas con máximo 3 concurrentes
3. guardar evidencia y resultados
4. continuar con las siguientes 15

---

## Justificación

### Red

Cada stream RTSP consume ancho de banda real.

Abrir demasiados streams simultáneos puede:

- aumentar tráfico innecesariamente
- afectar enlaces hacia las cámaras
- presionar switches o segmentos intermedios
- provocar falsos negativos por saturación

### CPU

`ffprobe` y `ffmpeg` consumen CPU, especialmente durante:

- apertura de stream
- negociación
- decodificación
- aplicación de filtros

### Disco

Cada corrida puede generar:

- `probe.txt`
- `detect.txt`
- frames JPG
- CSVs de salida

Sin limpieza ni control, el crecimiento en disco puede ser rápido.

### Estabilidad operativa

La máquina de ejecución no se asume como un host sobrado de recursos.

El runtime debe ser conservador.

---

## Recomendaciones técnicas del MVP-1

### Transporte

Usar preferentemente:

- `transport = tcp`

Motivo:

- mayor estabilidad operativa en RTSP para redes reales

### Ventanas de análisis

Usar ventanas cortas y suficientes para:

- validar metadata
- intentar decodificar video
- detectar negro o congelamiento sin abrir streams demasiado tiempo

### Escritura

Preferir escritura incremental por lote cuando aplique.

### Limpieza

Antes de una nueva corrida:

- conservar `.local/vms_input_real_local.csv`
- limpiar `.local/evidence/`
- limpiar `.local/output/`

---

## Regla para cambiar la concurrencia

No subir `max_workers` por intuición.

Solo debe aumentarse después de medir:

- CPU
- memoria
- ancho de banda
- tiempos promedio por cámara
- estabilidad general del host y la red

---

## Señales de que la concurrencia está demasiado alta

- CPU sostenida innecesariamente alta
- timeouts masivos
- más `NO_RTSP` o `NO_FRAMES` de lo esperado
- caída fuerte del rendimiento global
- host local inestable
- crecimiento excesivo de evidencia en disco

---

## Resumen operativo

Para MVP-1, la configuración base recomendada y cerrada es:

- `batch_size = 15`
- `max_workers = 3`

Eso mantiene el proceso suficientemente conservador para laboratorio y primeras corridas reales.