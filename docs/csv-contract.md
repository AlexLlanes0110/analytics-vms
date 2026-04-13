# Contrato CSV

## Input CSV (mínimo viable)
Columnas propuestas:
- name: identificador lógico
- brand: hikvision|dahua|huawei|axis|unknown
- ip: IP/host (en producción vendrá de fuente segura, no del repo)
- rtsp_port: default 554
- rtsp_path: path RTSP (o template por marca)
- transport: tcp|udp (default tcp)
- credential_id: referencia a credenciales (recomendado)

### Campo temporal para laboratorio (NO recomendado para producción)
- username/password: solo para pruebas locales; nunca se suben a Git.

## Output CSV (MVP-1)
- name, brand, ip
- status: OK|DOWN|NO_RTSP|NO_FRAMES|ERROR
- ffprobe_ok (0/1), codec, width, height, fps
- frames_ok (0/1)
- black_events (int), freeze_events (int)
- evidence_dir (opcional)
- error_type, error_msg_short
