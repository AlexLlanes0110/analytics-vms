# MVP-1 Spec — VMS HealthCheck (CLI)

## Objetivo
Implementar un CLI batch que reciba un CSV de cámaras y genere un CSV de resultados.
El criterio central es validar **video consumible** (frames decodificados), no solo conectividad.

## No objetivos (MVP-1)
- No UI
- No dashboard
- No base de datos histórica
- No integración con VMS/BMS

## Entradas / Salidas
- Contrato de CSV: ver `csv-contract.md`

## Estados normalizados (output.status)
- OK: frames decodificados exitosamente
- DOWN: sin conectividad/servicio (o timeout total)
- NO_RTSP: alcanzable pero falla negociación/auth/path RTSP (ffprobe falla)
- NO_FRAMES: ffprobe OK pero no se logran decodificar frames en ventana
- ERROR: fallo inesperado

## Pipeline por cámara (alto nivel)
1) (Opcional) conectividad/puerto RTSP
2) ffprobe (metadata: codec/res/fps)
3) ffmpeg: extracción de N frames
4) ffmpeg: detectores blackdetect/freezedetect (banderas)
5) consolidación de resultado

## Configuración (CLI)
- workers (default 15): máximo de cámaras procesadas en paralelo
- batch-size (default 15): procesa en bloques y escribe resultados incrementalmente
- timeouts y ventanas: configurables

## Evidencia
- La evidencia (frames/logs) es local y temporal
- Nunca se versiona en GitHub
