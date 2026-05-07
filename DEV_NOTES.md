# DEV_NOTES.md

## Current state

- Current branch: `mvp-1j-check-cameras-cli`.
- `main` and `origin/main` are at `0db69b3` (`merge: complete mvp-1i reports`).
- MVP-1J is implemented locally and pending review/commit.
- No commit, push, merge, Docker, systemd, firewall, `.local/`, `.venv/`, real camera data, real IPs, real users, real passwords, real production output, or paths outside this repository were touched.
- Last validation status on `srv-taiga`:
  - `git diff --check` -> OK.
  - `pytest -q` -> 81 passed.
  - `python -m analytics_vms.cli --help` -> OK.
  - `python -m analytics_vms.cli check-cameras --help` -> OK.
  - `python -m analytics_vms.cli check-inventory examples/vms_input_dummy_repo.csv` -> OK; 181 rows.

## Core rules

- OK real means `frames_ok == 1`.
- `ffprobe` is metadata/diagnostic signal only; it does not declare a camera OK.
- Visual diagnostics (`black_detected`, `freeze_detected`) do not change final status.
- Current normalized statuses: `OK`, `NO_FRAMES`, `PROBE_FAILED`, `ERROR`.
- Do not include RTSP URLs, credentials, real IPs, real CSVs, real outputs, or evidence in committed reports.
- Never use `shell=True`.
- Unit tests must not use real RTSP endpoints, real credentials, ffprobe, or ffmpeg.
- Do not touch `.local/`, `.venv/`, Docker, systemd, firewall, production outputs, or paths outside this repository without explicit review.
- Do not commit, push, or merge unless explicitly requested.

## Closed MVPs

- MVP-1I: report generation helpers for detailed CSV, summary CSV, summary-by-site CSV, and JSON payload were completed and merged at `0db69b3`.

## MVP-1J - check-cameras CLI

Status: implemented locally, pending review.

Implemented scope:

- Added operator command:
  - `python3 -m analytics_vms.cli check-cameras INVENTORY.csv --out-dir OUTPUT_DIR`
- CLI flow:
  - validates/loads inventory with `load_inventory_csv()`
  - converts loaded inventory rows into mappings for the existing batch runner
  - runs `check_camera_batch()`
  - creates `OUTPUT_DIR`
  - writes `detailed.csv`, `summary.csv`, `summary_by_site.csv`, and `report.json`
  - prints operational totals and generated file paths
  - exits 0 when the batch completes, even with camera-level `NO_FRAMES`, `PROBE_FAILED`, or `ERROR`
  - exits 1 for invalid inventory or fatal CLI/report errors
- Added CLI options:
  - `--probe-timeout-seconds` default 5
  - `--frame-timeout-seconds` default 10
  - `--min-frames` default 1
  - `--visual-diagnostics / --no-visual-diagnostics` default enabled
  - `--visual-timeout-seconds` default 10
  - `--visual-sample-seconds` default 5
  - `--print-details` default false
- Expanded detailed report and JSON detail rows with safe operational inventory fields:
  - `project_code`, `municipality`, `site_type`, `site_code`, `site_name`
  - `traffic_direction`, `camera_role`, `camera_name`, `brand`
  - `ip`, `rtsp_port`, `rtsp_path`, `transport`
  - `camera_id`, `status`, `probe_ok`, `frames_ok`
  - `black_detected`, `freeze_detected`, `error`
- Detailed reports omit `username`, `password`, `credential_id`, `rtsp_url_masked`, and full RTSP URLs.
- Report/terminal detail errors redact full RTSP URLs and source credential tokens.

Files modified:

- `src/analytics_vms/cli.py`
- `src/analytics_vms/reports.py`
- `tests/test_cli.py`
- `tests/test_reports.py`
- `README.md`
- `docs/csv-contract.md`
- `examples/vms_output_dummy_detailed_example.csv`
- `DEV_NOTES.md`

Validation commands run:

- `pytest tests/test_reports.py tests/test_cli.py -q` -> 16 passed.
- `pytest -q` -> 81 passed.
- `git diff --check` -> OK.
- `python -m analytics_vms.cli --help` -> OK; `check-cameras` listed.
- `python -m analytics_vms.cli check-cameras --help` -> OK; all MVP-1J options listed.
- `python -m analytics_vms.cli check-inventory examples/vms_input_dummy_repo.csv` -> OK; 181 rows.

## Next task

- Review/cierre de MVP-1J. Keep Next task empty for implementation; do not start MVP-2 until MVP-1J is reviewed, committed, and closed on request.
