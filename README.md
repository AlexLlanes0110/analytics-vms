# VMS HealthCheck

Sistema batch/CLI para validar **“visualización real”** de cámaras vía RTSP:
- Entrada: CSV de cámaras
- Proceso: RTSP -> ffprobe -> extracción de frames -> detectores black/freeze
- Salida: CSV con estados normalizados y métricas

## MVPs
- **MVP-1:** CLI (CSV in -> CSV out) con concurrencia controlada (default 15)
- **MVP-2:** UI simple para subir CSV y ver resultados en tabla
- **MVP-3:** Dashboard/histórico (tendencias, caídas, KPIs)

## Quickstart (MVP-1)
1) Ver contrato del CSV: `docs/csv-contract.md`
2) Especificación MVP-1: `docs/mvp-1-spec.md`
3) Performance/red: `docs/performance-and-network.md`

> Nota: este repo **NO** contiene IPs reales, credenciales, CSV reales ni evidencias.

## Seguridad
Ver `docs/security.md`.
