# Performance y tráfico de red

Este proceso abre streams RTSP y genera tráfico. Se controla con throttling.

Defaults:
- workers: 15 (máximo de streams/cámaras simultáneas)
- batch-size: 15 (procesa en bloques y escribe incrementalmente)

Recomendaciones:
- Empezar con workers=15 y ajustar según red/cámaras
- Mantener ventanas cortas (frames y detectores) para reducir tráfico
- Ejecutar por ventanas/horarios si aplica
