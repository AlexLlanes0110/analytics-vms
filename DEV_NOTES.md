# DEV_NOTES.md

## Project

Analytics VMS / VMS HealthCheck

Python CLI/batch tool to validate VMS cameras over RTSP and generate CSV reports.

Core rule:

OK = frames_ok == 1

A camera is only considered OK when ffmpeg decodes real frames.
ffprobe metadata is not enough to declare a camera OK.

## Current state

Current branch:
main

Repo status:
MVP-1C merged into main.

Next task:
MVP-1D - ffprobe timeout wrapper

## Closed MVPs

### MVP-1A - base CLI

Done:
- Python package with src/ layout.
- Typer CLI.
- pytest.
- VS Code type checking.

Known commits:
- 910834e chore: scaffold Python CLI package
- 8ac74ef chore: configure VS Code type checking

### MVP-1B - inventory CSV

Done:
- InventoryRow
- InventoryValidationError
- load_inventory_csv()
- normalize_inventory_row()
- analytics-vms check-inventory

Known commit:
- 539b401 feat: add inventory CSV validation

### MVP-1C - safe RTSP URL builder

Done:
- RtspUrlError
- build_rtsp_url()
- mask_rtsp_url()
- Escapes username/password.
- Does not expose real password in masked URL.

Known commit:
- b9ca587 feat: build and mask RTSP URLs

## Next task

### MVP-1D - ffprobe timeout wrapper

Goal:
Implement a safe ffprobe wrapper with timeout and structured result.

Expected files:
- src/analytics_vms/probes.py
- tests/test_probes.py

Allowed scope:
- ffprobe subprocess wrapper.
- timeout handling.
- structured result object.
- parsing useful metadata from ffprobe JSON.
- safe error handling.
- masking credentials in any error/message.
- unit tests with mocks.

Forbidden scope:
- Do not implement ffmpeg frame validation.
- Do not implement frames_ok.
- Do not implement blackdetect.
- Do not implement freezedetect.
- Do not implement final camera classification.
- Do not implement CSV reports.
- Do not implement batch execution.
- Do not use real RTSP endpoints.
- Do not use real credentials.
- Do not require ffprobe installed for unit tests.

## Technical decisions

- Use Typer for CLI.
- Use pytest.
- Use subprocess with argument lists.
- Never use shell=True.
- Keep real/local data in .local/.
- Do not commit secrets, real IPs, real camera names, real CSVs, or production evidence.
- ffprobe success means metadata/connection signal only.
- Final camera OK depends only on frames_ok == 1 in a later MVP.

## Validation commands

python -m pip install -e ".[dev]"
pytest -q
analytics-vms --help
analytics-vms check-inventory examples/vms_input_dummy_repo.csv

## Do not touch without explicit review

- .local/
- .venv/
- Docker
- systemd
- firewall
- server paths outside the repo
- real camera IPs
- real passwords
- real VMS outputs

## Last session summary

Last completed task:
MVP-1C - safe RTSP URL builder

Next task:
MVP-1D - ffprobe timeout wrapper

Known risks:
- Do not treat ffprobe success as camera OK.
- Do not leak RTSP credentials in errors.
- Do not execute real ffprobe during unit tests.
- Keep MVP-1D isolated.

## Update log

### 2026-05-06

MVP-1C merged into main.
AGENTS.md and DEV_NOTES.md created in main.
Next action: create branch mvp-1d-ffprobe-timeout and implement MVP-1D.
