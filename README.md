# VMS HealthCheck

CLI batch en Python para validar **visualización real** de cámaras vía RTSP y generar reportes CSV operativos.

El objetivo del proyecto no es solo saber si una cámara responde por red, sino confirmar si **entrega video consumible de verdad**.

---

## Regla funcional central

> **OK real = `frames_ok = 1`**

Una cámara se considera realmente operativa solo cuando fue posible **decodificar frames reales**.

No basta con que:

- el host responda
- el puerto RTSP abra
- `ffprobe` devuelva metadata

---

## Qué hace el sistema

### Entrada

- CSV de inventario de cámaras

### Proceso por cámara

- validación y normalización de fila
- construcción de URL RTSP
- `ffprobe` para metadata del stream
- `ffmpeg` para extracción de frames
- `blackdetect` para detectar imagen negra
- `freezedetect` para detectar congelamiento
- consolidación de resultado

### Salida

- CSV detallado por cámara
- CSV resumen por sitio

---

## Qué significa cada validación

### `ffprobe`

Sirve para intentar abrir el stream y extraer metadata útil, por ejemplo:

- codec
- width
- height
- fps

Ayuda a saber que el endpoint negoció algo útil, pero **no prueba por sí solo** que la cámara esté OK.

### `ffmpeg` para frames

Es la validación fuerte.

Aquí se intenta abrir el stream y **decodificar video real** durante una ventana corta de prueba.

De aquí sale la señal principal:

- `frames_ok = 1` → sí hubo video útil
- `frames_ok = 0` → no se logró decodificar video útil

### `blackdetect`

Detecta periodos donde la imagen está negra.

Produce:

- `black_events`

### `freezedetect`

Detecta periodos donde la imagen está congelada.

Produce:

- `freeze_events`

### Importante

En **MVP-1**, `black_events` y `freeze_events` se reportan como señales diagnósticas de calidad visual, pero **no cambian por sí solos** el estado central.

Eso significa que una cámara puede quedar en `OK` y además traer alertas de negro o congelamiento.

---

## Estados normalizados

- `OK`
- `DOWN`
- `NO_RTSP`
- `NO_FRAMES`
- `ERROR`

### Regla de interpretación

- `OK` → hubo frames reales decodificados
- `DOWN` → no hubo conectividad útil / timeout duro / servicio inaccesible
- `NO_RTSP` → el host responde, pero falla auth / path / negociación RTSP
- `NO_FRAMES` → hubo negociación o metadata útil, pero no se pudieron decodificar frames
- `ERROR` → fallo inesperado no clasificado

---

## Alcance actual

### MVP-1

CLI batch en Python para:

- CSV in → CSV out
- validación por cámara
- resumen por sitio
- concurrencia controlada
- evidencia local por corrida
- sin UI
- sin dashboard
- sin histórico en base de datos

### MVP-2

Capa mínima de uso asistido para:

- cargar CSV
- ejecutar proceso
- visualizar resultados en tabla

### MVP-3

Dashboard e histórico para:

- tendencias
- KPIs
- comparativos
- histórico por sitio y por cámara

---

## Modelo operativo

La regla base del inventario es:

> **1 fila = 1 cámara**

Tipos de sitio soportados en MVP-1:

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

### `traffic_direction`

- para `PMI` se espera vacío
- para `ARC` se usa `ENTRY` o `EXIT`

---

## Decisión operativa de performance

Para MVP-1, la ejecución debe ser conservadora:

- `batch_size = 15`
- `max_workers = 3`

Interpretación:

- el inventario se divide en bloques de 15 cámaras
- dentro de cada bloque, solo 3 cámaras se procesan en simultáneo

Esto prioriza estabilidad sobre velocidad máxima.

---

## Layout operativo local

Todo lo real vive fuera del repo, en `.local/`.

```text
.local/
├─ vms_input_real_local.csv
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

### Política de limpieza

Antes de una corrida nueva, el runtime debe poder:

- conservar `.local/vms_input_real_local.csv`
- limpiar `.local/evidence/`
- limpiar `.local/output/`
- recrear estructura limpia para la nueva ejecución

No se debe borrar `.local/` completo salvo decisión explícita del operador.

---

## Archivos dummy vs archivos reales

### En el repo sí va

- código fuente
- documentación
- ejemplos dummy

### En el repo no va

- IPs reales
- credenciales reales
- CSV reales
- outputs reales
- evidencia
- logs sensibles

### Ejemplos públicos

```text
examples/
├─ vms_input_dummy_repo.csv
├─ vms_output_dummy_detailed_example.csv
└─ vms_output_dummy_summary_by_site_example.csv
```

---

## Documentación clave

- `docs/csv-contract.md` → contrato de entrada y salida CSV
- `docs/mvp-1-spec.md` → especificación funcional del MVP-1
- `docs/runtime-flow.md` → flujo operativo completo de una corrida
- `docs/performance-and-network.md` → control de carga y red
- `docs/security.md` → separación entre repo público y operación local
- `docs/mvps.md` → roadmap de evolución del proyecto

---

## Quickstart documental

1. Revisar `docs/csv-contract.md`
2. Revisar `docs/mvp-1-spec.md`
3. Revisar `docs/runtime-flow.md`
4. Revisar `docs/performance-and-network.md`
5. Revisar `docs/security.md`
6. Usar `examples/` solo como referencia dummy
7. Colocar inventario real solo en `.local/`
8. Ejecutar el CLI sobre el CSV real
9. Revisar output detallado y output resumen

---

## Estado actual del proyecto

El proyecto está orientado a construir primero un motor CLI confiable y documentado.

El orden correcto es:

1. contrato
2. documentación
3. implementación del CLI
4. ejecución controlada
5. visualización
6. histórico