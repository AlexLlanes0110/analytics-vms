# VMS HealthCheck

Sistema batch/CLI para validar **visualización real** de cámaras vía RTSP.

El objetivo de este proyecto es leer un inventario de cámaras desde CSV, ejecutar validaciones técnicas sobre cada endpoint de video y generar resultados estructurados que permitan saber:

- qué cámaras están funcionando realmente
- en qué etapa falla una cámara cuando no entrega video
- cuántas cámaras están OK o con falla por sitio

---

## Qué hace

### Entrada
- CSV de inventario de cámaras

### Proceso
- RTSP
- `ffprobe` para metadata
- `ffmpeg` para extracción de frames
- detectores `blackdetect` / `freezedetect`
- consolidación de resultado

### Salida
- CSV detallado por cámara
- CSV resumen por sitio

---

## Criterio clave

**“OK real” significa que se pudieron decodificar frames (`frames_ok = 1`)**, no solo que exista conectividad o que el endpoint responda parcialmente.

Esto es importante porque una cámara puede:

- responder a nivel red
- devolver metadata
- pero aun así no entregar video consumible

---

## Alcance actual

### MVP-1
CLI batch en Python:

- CSV in → CSV out
- concurrencia controlada
- validación por cámara
- resumen por sitio
- sin UI
- sin dashboard
- sin base de datos histórica

### MVP-2
Frontend básico para:

- cargar CSV
- ejecutar proceso
- visualizar resultados en tabla

### MVP-3
Dashboard / histórico:

- tendencias
- KPIs
- comparativos
- histórico por sitio / cámara

---

## Modelo operativo

La regla principal del inventario es:

- **1 fila = 1 cámara**

El sistema soporta sitios de tipo:

- `PMI`
- `ARC`

### Ejemplos de roles

#### PMI
- `PTZ`
- `FJ1`
- `FJ2`
- `FJ3`
- `LPR`

#### ARC
- `FIXED_1`
- `FIXED_2`
- `LPR_1`
- `LPR_2`
- `LPR_3`
- `LPR_4`

Para `ARC`, además puede usarse:

- `ENTRY`
- `EXIT`

en la columna `traffic_direction`.

---

## Estructura esperada del repo

```text
analytics-vms/
├─ README.md
├─ .gitignore
├─ docs/
│  ├─ mvps.md
│  ├─ mvp-1-spec.md
│  ├─ csv-contract.md
│  ├─ performance-and-network.md
│  └─ security.md
├─ examples/
│  ├─ cameras.input.example.csv
│  ├─ results.detailed.example.csv
│  └─ results.summary.example.csv
├─ .local/
│  ├─ cameras.input.real.csv
│  ├─ results.detailed.real.csv
│  └─ results.summary.real.csv
└─ src/
```

---

## Documentación clave

### Contrato CSV
Ver:

```text
docs/csv-contract.md
```

Ahí se define:

- qué columnas lleva el input
- qué columnas lleva el output detallado
- qué columnas lleva el output resumen
- reglas de validación
- ejemplos dummy

### Especificación funcional del MVP-1
Ver:

```text
docs/mvp-1-spec.md
```

Ahí se define:

- alcance
- estados normalizados
- pipeline por cámara
- configuración
- criterios de aceptación

### Seguridad
Ver:

```text
docs/security.md
```

Ahí se define:

- qué sí se sube al repo
- qué no se sube al repo
- uso de `examples/`
- uso de `.local/`
- manejo de credenciales y outputs

### Performance y red
Ver:

```text
docs/performance-and-network.md
```

---

## Quickstart (MVP-1)

1. Revisar el contrato de CSV en `docs/csv-contract.md`
2. Revisar la especificación funcional en `docs/mvp-1-spec.md`
3. Revisar restricciones de seguridad en `docs/security.md`
4. Usar un archivo dummy de `examples/` como referencia
5. Colocar inventario real solo en `.local/`
6. Ejecutar el CLI sobre el CSV real
7. Revisar:
   - output detallado por cámara
   - output resumen por sitio

---

## Archivos dummy vs archivos reales

### Archivos dummy
Se usan para:

- documentación
- ejemplos
- pruebas de formato
- repositorio público

Viven en:

```text
examples/
```

### Archivos reales
Se usan para:

- inventario operativo real
- pruebas locales
- ejecución del batch
- resultados reales

Viven localmente en:

```text
.local/
```

---

## Seguridad

> Este repo **NO** debe contener IPs reales, credenciales reales, CSV reales ni evidencia operativa.

Reglas base:

- `examples/` solo contiene dummy
- `.local/` solo contiene archivos reales/locales
- outputs reales no se suben
- credenciales no se suben
- evidencia no se sube
- logs sensibles no se suben

---

## `.gitignore`

El repositorio ya debe ignorar al menos:

- `.local/`
- `data/`
- `.evidence/`
- `.env`
- `*.local.csv`

Y puede reforzarse con:

- `*.real.csv`
- `*_real*.csv`

---

## Diseño del output

### Output detallado
Permite ver, por cámara:

- identidad del sitio
- identidad de la cámara
- IP
- `status`
- `failure_stage`
- metadata
- `frames_ok`
- eventos de black/freeze
- error resumido

### Output resumen
Permite ver, por sitio:

- total de cámaras
- cuántas están OK
- cuántas fallaron
- conteo por tipo de falla

Esto deja listo el camino para un dashboard futuro.

---

## Estados normalizados

Los estados esperados son:

- `OK`
- `DOWN`
- `NO_RTSP`
- `NO_FRAMES`
- `ERROR`

Resumen conceptual:

- `OK` → sí hubo frames decodificados
- `DOWN` → no hubo conectividad real o hubo timeout total
- `NO_RTSP` → falló negociación/auth/path RTSP
- `NO_FRAMES` → hubo metadata, pero no video consumible
- `ERROR` → fallo inesperado

---

## Performance y control de carga

Este proceso abre streams RTSP y genera tráfico.  
Para evitar saturar red, cámaras o enlaces, el MVP trabaja con concurrencia controlada.

Defaults acordados:

- `workers = 15`
- `batch-size = 15`

La recomendación es empezar con esos valores y ajustar según comportamiento real del entorno.

---

## Estado del proyecto

En esta etapa, el foco es:

1. cerrar contrato CSV
2. documentar bien el MVP-1
3. separar dummy vs real
4. crear scaffold del CLI
5. implementar pipeline por módulos

---

## Principios del proyecto

- primero contrato y documentación
- luego scaffold
- luego smoke test
- después implementación incremental
- seguridad desde el inicio
- nada real en GitHub

---

## Nota final

Este repositorio está pensado para construir el sistema por etapas, empezando por un flujo simple y verificable:

**CSV → health check RTSP → resultados estructurados**

El objetivo inmediato no es una UI, sino un backend/CLI confiable que sirva como base para automatización, reporting y dashboard futuro.
