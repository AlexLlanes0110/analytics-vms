# DEV_NOTES.md

## Current state

- Current branch: `mvp-1i-reports`.
- `main` is closed through MVP-1H at `02bf63d`.
- MVP-1I is in progress: CSV/JSON reports from in-memory camera check results.
- MVP-1H.5 note: Manual real-camera smoke test completed locally with 20 cameras: 18 OK, 2 PROBE_FAILED confirmed inactive, 0 NO_FRAMES, 0 ERROR. No real data committed.
- Current MVP files: `src/analytics_vms/reports.py`, `tests/test_reports.py`, `tests/test_imports.py`, `examples/`, `docs/csv-contract.md`, `README.md`, `DEV_NOTES.md`.
- Last validation status: `pytest -q` 78 passed; `analytics-vms --help` OK; `analytics-vms check-inventory examples/vms_input_dummy_repo.csv` OK with 181 rows; `git diff --check` OK.
- Documentation cleanup: current docs use only `OK`, `NO_FRAMES`, `PROBE_FAILED`, and `ERROR` as current states.

## Core rules

- OK real means `frames_ok == 1`.
- `ffprobe` is metadata/diagnostic signal only; it does not declare a camera OK.
- Visual diagnostics (`black_detected`, `freeze_detected`) do not change final status.
- Do not include RTSP URLs, credentials, real IPs, real CSVs, real outputs, or evidence in committed reports.
- Never use `shell=True`.
- Unit tests must not use real RTSP endpoints, real credentials, ffprobe, or ffmpeg.
- Do not touch `.local/`, `.venv/`, Docker, systemd, firewall, production outputs, or paths outside this repository without explicit review.
- Do not commit, push, or merge unless explicitly requested.

## MVP-1I scope

- Build detailed CSV rows from `BatchCheckResult` / `CameraCheckResult`.
- Build global summary CSV rows from `BatchCheckSummary`.
- Build summary-by-site CSV rows by matching `camera_id -> source row`.
- Add minimal JSON helpers: `build_report_payload()` and `write_json_report()`.
- Keep reports simple and safe: no `rtsp_url_masked` in MVP-1I output.
- No new CLI, concurrency, retries, network access, real RTSP execution, or `.local/` usage.

## Validation commands

- `pytest -q`
- `analytics-vms --help`
- `analytics-vms check-inventory examples/vms_input_dummy_repo.csv`
- `git diff --check`

## Next step

- Review the MVP-1I diff.
- If approved, commit on `mvp-1i-reports`.
- Push/merge only when explicitly requested.
