# DEV_NOTES.md

## Current state

- Current branch: `mvp-1h-batch-camera-checks`.
- `main` is closed through MVP-1G at `b35bc6e`.
- MVP-1H is in progress: in-memory batch camera checks.
- Current MVP files: `src/analytics_vms/batch_check.py`, `tests/test_batch_check.py`, `tests/test_imports.py`, `DEV_NOTES.md`.
- `AGENTS.md` was updated with permanent repo rules only.

## Core rules

- Real OK means `frames_ok == 1`.
- `ffprobe` is metadata/diagnostic signal only; it does not declare a camera OK.
- Final OK depends on `ffmpeg` decoding real frames.
- Visual diagnostics do not change final OK status.
- Never use `shell=True`.
- Unit tests must not use real RTSP endpoints, real credentials, ffprobe, or ffmpeg.
- Do not touch `.local/`, `.venv/`, Docker, systemd, firewall, production outputs, or paths outside this repository without explicit review.
- Do not commit, push, or merge unless explicitly requested.

## MVP-1H scope

- Add an in-memory batch runner for already-loaded camera row mappings.
- `check_camera_batch()` calls `check_single_camera()` once per row.
- Return `BatchCheckResult(results, summary)` in memory.
- Summary counts `OK`, `NO_FRAMES`, `PROBE_FAILED`, `ERROR`, `black_detected`, and `freeze_detected`.
- Per-row unexpected exceptions become `CameraCheckResult(status="ERROR")` and do not stop the batch.
- Preserve result order.
- No new CLI, CSV reading, CSV/JSON reports, file writes, concurrency, multiprocessing, async, retries, or real RTSP execution.

## Validation commands

- `git diff --check`
- `pytest -q`
- `analytics-vms --help`
- `analytics-vms check-inventory examples/vms_input_dummy_repo.csv`

## Next step

- Review the MVP-1H diff.
- If approved, commit on `mvp-1h-batch-camera-checks` with:
  `git commit -m "feat: add batch camera check runner"`
- Then push/merge only when explicitly requested.
