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
mvp-1f-visual-diagnostics-detectors

Repo status:
MVP-1E closed and merged to main. MVP-1F visual diagnostics detectors in progress.

Next task:
MVP-1F - visual diagnostics detectors.

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

### MVP-1D - ffprobe timeout wrapper

Done:
- ProbeResult structured result for ffprobe metadata.
- run_ffprobe()
- Timeout handling.
- JSON parsing for ffprobe stream metadata.
- FPS parsing from avg_frame_rate with r_frame_rate fallback.
- Safe handling for nonzero return code, invalid JSON, missing ffprobe, timeout, and missing video stream.
- Credential masking in error/raw_stdout/raw_stderr.
- Unit tests with mocked subprocess.run; ffprobe is not required for tests.

Known commit:
- aa3771d feat: add ffprobe timeout wrapper

### MVP-1E - ffmpeg frame validation

Done:
- FrameValidationResult structured result for frame validation.
- validate_rtsp_frames()
- Timeout handling.
- frames_ok signal based on ffmpeg decoding min_frames frames.
- Explicit ffmpeg video stream selection with `-map 0:v:0`.
- Audio ignored with `-an` so audio-only inputs cannot pass frame validation.
- Safe handling for nonzero return code, missing ffmpeg, timeout, and invalid min_frames.
- Credential masking in error/raw_stdout/raw_stderr.
- Unit tests with mocked subprocess.run; ffmpeg is not required for tests.

Known commit:
- de2bac4 feat: add ffmpeg frame validation
- 94ab480 fix: require video stream for frame validation
- 5c13c10 merge: complete mvp-1e ffmpeg frame validation

## Next task

### MVP-1F - visual diagnostics detectors

Goal:
Implement optional isolated black/freeze diagnostic wrappers with ffmpeg filters.

Expected files:
- src/analytics_vms/visual_diagnostics.py
- tests/test_visual_diagnostics.py

Allowed scope:
- Add VisualDiagnosticEvent and VisualDiagnosticResult dataclasses.
- Add detect_black_frames() wrapper for ffmpeg blackdetect.
- Add detect_frozen_frames() wrapper for ffmpeg freezedetect.
- Parse detector events from sanitized ffmpeg stderr.
- Unit tests must mock subprocess.run and must not require ffmpeg installed.

Forbidden scope:
- Do not implement final camera classification.
- Do not implement CSV reports.
- Do not implement batch execution.
- Do not implement new CLI commands.
- Do not integrate with inventory.
- Do not use real RTSP endpoints.
- Do not use real credentials.
- Do not require ffmpeg installed for unit tests.

## Technical decisions

- Use Typer for CLI.
- Use pytest.
- Use subprocess with argument lists.
- Never use shell=True.
- Keep real/local data in .local/.
- Do not commit secrets, real IPs, real camera names, real CSVs, or production evidence.
- ffprobe success means metadata/connection signal only.
- Final camera OK depends only on frames_ok == 1 in a later MVP.

## MVP branch methodology

Each MVP must be developed on its own branch.

Required workflow:

1. Start from clean, updated `main`.
2. Create a branch specific to the MVP.
3. Implement only that MVP's scope.
4. Run validations.
5. Update `DEV_NOTES.md`.
6. Commit on the MVP branch.
7. Push the MVP branch.
8. Merge the MVP branch into `main`.
9. Push `main`.
10. Create the next branch from updated `main`.

Rules:
- Do not mix the next MVP into the previous MVP branch.
- Do not create a new branch from an unclosed MVP branch unless explicitly instructed.
- Do not implement future scope in the current MVP.
- Keep the historical MVP list under `Closed MVPs`.
- Move each completed MVP to `Closed MVPs`.
- Keep the next MVP under `Next task`.

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
MVP-1E - ffmpeg frame validation, merged to main

Next task:
MVP-1F - visual diagnostics detectors in progress.

Known risks:
- Do not treat ffprobe success as camera OK.
- Do not leak RTSP credentials in errors.
- Do not execute real ffprobe or ffmpeg during unit tests.
- Keep MVP-1F isolated from classification, inventory integration, batch execution, CLI, and reports.

## Handoff for next Codex session

Current branch:
mvp-1f-visual-diagnostics-detectors

Current working tree status expected:
- M DEV_NOTES.md
- M tests/test_imports.py
- ?? src/analytics_vms/visual_diagnostics.py
- ?? tests/test_visual_diagnostics.py

MVP currently in progress:
MVP-1F - visual diagnostics detectors

Implementation status:
MVP-1E is closed and merged to main at 5c13c10. MVP-1F adds isolated optional visual diagnostic wrappers only. There is no new CLI, no inventory integration, no batch execution, no CSV reporting, and no final camera classification.

Files changed:
- DEV_NOTES.md
- src/analytics_vms/visual_diagnostics.py
- tests/test_visual_diagnostics.py
- tests/test_imports.py

Validations already run:
- pytest -q: 57 passed
- analytics-vms --help: OK
- analytics-vms check-inventory examples/vms_input_dummy_repo.csv: OK, 181 rows

Commands that the next session should run first:
- git status --short --untracked-files=all
- git branch --show-current
- git log --oneline --decorate -10
- pytest -q
- analytics-vms --help
- analytics-vms check-inventory examples/vms_input_dummy_repo.csv

What to review before commit:
- Confirm src/analytics_vms/visual_diagnostics.py only implements isolated blackdetect/freezedetect wrappers.
- Confirm ffmpeg commands use argument lists, `-map 0:v:0`, `-an`, `-t`, `-vf`, and never `shell=True`.
- Confirm tests/test_visual_diagnostics.py uses mocks and does not require ffmpeg, real cameras, real RTSP endpoints, or real credentials.
- Confirm DEV_NOTES.md accurately describes one-branch-per-MVP methodology and the current MVP-1F handoff.
- Confirm no .local/, .venv/, real outputs, real IPs, real users, or real passwords were touched.

Exact commit command suggested:
git add DEV_NOTES.md src/analytics_vms/visual_diagnostics.py tests/test_visual_diagnostics.py tests/test_imports.py
git commit -m "feat: add visual diagnostic detectors"

Exact merge-to-main flow after review:
git push origin mvp-1f-visual-diagnostics-detectors
git checkout main
git pull origin main
git merge --no-ff mvp-1f-visual-diagnostics-detectors -m "merge: complete mvp-1f visual diagnostics detectors"
pytest -q
analytics-vms --help
analytics-vms check-inventory examples/vms_input_dummy_repo.csv
git push origin main

Next MVP suggested:
To be defined after MVP-1F is reviewed and merged to main.

## Update log

### 2026-05-06

MVP-1C merged into main.
AGENTS.md and DEV_NOTES.md created in main.
Next action: create branch mvp-1d-ffprobe-timeout and implement MVP-1D.

### 2026-05-06

MVP-1D implemented on branch mvp-1d-ffprobe-timeout.

Files created/modified:
- src/analytics_vms/probes.py
- tests/test_probes.py
- tests/test_imports.py
- DEV_NOTES.md

Classes/functions added:
- ProbeResult
- run_ffprobe()
- run_probe_stub()

Tests added:
- success with valid ffprobe JSON and video stream
- FPS parsing for 25/1
- FPS parsing for 30000/1001
- FPS None for 0/0
- FPS None for N/A
- no video stream
- nonzero return code
- timeout handling
- FileNotFoundError handling
- invalid JSON
- credential masking in error/raw_stdout/raw_stderr
- sanitizer fallback for malformed RTSP-like URLs
- masking URL-encoded and decoded password tokens

Commands executed:
- git status --short --untracked-files=all
- git branch --show-current
- git log --oneline --decorate -10
- pytest -q
- analytics-vms --help
- analytics-vms check-inventory examples/vms_input_dummy_repo.csv
- git diff --stat

Test result:
- pytest -q: 34 passed
- analytics-vms --help: OK
- analytics-vms check-inventory examples/vms_input_dummy_repo.csv: OK, 181 rows

Risks/pending:
- ffprobe ok is only a metadata/connection signal, not camera OK.
- ffmpeg frame validation and frames_ok remain unimplemented.
- Unit tests mock subprocess.run and do not require ffprobe installed.
- Suggested next task: define MVP-1E for ffmpeg frame validation wrapper.

Adjustment before closing MVP-1D:
- Added fixed MVP branch methodology to AGENTS.md and DEV_NOTES.md.
- Hardened ffprobe output sanitization so masking failures cannot break run_ffprobe().
- Protected password token extraction from malformed RTSP-like input.

### 2026-05-06

MVP-1E implemented on branch mvp-1e-ffmpeg-frame-validation.

Files created/modified:
- src/analytics_vms/frames.py
- tests/test_frames.py
- tests/test_imports.py
- DEV_NOTES.md

Classes/functions added:
- FrameValidationResult
- validate_rtsp_frames()

Tests added:
- success returncode 0 sets frames_ok=1 and ok=True
- nonzero returncode sets frames_ok=0 and ok=False
- timeout sets timed_out=True, frames_ok=0, and ok=False
- FileNotFoundError handling
- password masking in error/raw_stdout/raw_stderr
- URL-encoded and decoded password token masking
- subprocess.run called with a list of arguments
- shell=True is not used
- min_frames is passed to the ffmpeg command
- invalid min_frames returns a clear structured error

Commands executed:
- git status --short --untracked-files=all
- git branch --show-current
- git log --oneline --decorate -10
- pytest -q
- analytics-vms --help
- analytics-vms check-inventory examples/vms_input_dummy_repo.csv

Test result:
- pytest -q: 45 passed
- analytics-vms --help: OK
- analytics-vms check-inventory examples/vms_input_dummy_repo.csv: OK, 181 rows

Risks/pending:
- validate_rtsp_frames() does not classify cameras or write reports.
- frames_ok=1 only means ffmpeg decoded at least min_frames frames in this isolated piece.
- Hardening pending: require explicit video mapping with `-map 0:v:0` and ignore audio with `-an`.
- blackdetect and freezedetect remain unimplemented.
- CSV reports, batch execution, and final camera classification remain unimplemented.
- Unit tests mock subprocess.run and do not require ffmpeg installed.
- Suggested next task: define MVP-1F scope after review.

### 2026-05-06

MVP-1E hardening prepared on branch mvp-1e-ffmpeg-frame-validation after de2bac4 was already pushed.

Files modified:
- src/analytics_vms/frames.py
- tests/test_frames.py
- DEV_NOTES.md

Adjustment:
- ffmpeg now forces explicit video stream selection with `-map 0:v:0`.
- ffmpeg ignores audio with `-an`.
- `frames_ok=1` requires ffmpeg to process the first video stream.
- This avoids false positives with audio-only sources or sources without video.
- Because de2bac4 was already pushed, close this as a second fix commit on the same MVP branch; do not amend or rewrite history.

Tests adjusted:
- Frame validation command expectations include `-map 0:v:0` and `-an`.
- Added explicit coverage that video mapping appears after `-i <rtsp_url>` and before `-frames:v <min_frames>`.
- Kept coverage that subprocess.run receives a list and does not receive `shell=True`.

Commands executed:
- git branch --show-current
- git status --short --untracked-files=all
- git log --oneline --decorate -8
- pytest -q
- analytics-vms --help
- analytics-vms check-inventory examples/vms_input_dummy_repo.csv

Test result:
- pytest -q: 46 passed
- analytics-vms --help: OK
- analytics-vms check-inventory examples/vms_input_dummy_repo.csv: OK, 181 rows

### 2026-05-06

MVP-1E merged to main.

Known commit:
- 5c13c10 merge: complete mvp-1e ffmpeg frame validation

MVP-1F started on branch mvp-1f-visual-diagnostics-detectors.

Goal:
- Add isolated optional visual diagnostics wrappers for blackdetect and freezedetect.
- Keep `OK = frames_ok == 1`; visual diagnostics do not classify cameras as OK.
- Do not add CLI, batch execution, reports, inventory integration, or final classification.

Files planned/modified:
- src/analytics_vms/visual_diagnostics.py
- tests/test_visual_diagnostics.py
- tests/test_imports.py
- DEV_NOTES.md

Implementation:
- Added VisualDiagnosticEvent and VisualDiagnosticResult.
- Added detect_black_frames() using ffmpeg blackdetect.
- Added detect_frozen_frames() using ffmpeg freezedetect.
- Both wrappers require explicit video mapping with `-map 0:v:0`, ignore audio with `-an`, bound runtime with `-t`, and keep subprocess arguments as lists without `shell=True`.
- Output/error sanitization masks RTSP URLs and encoded/decoded password tokens.
- Invalid sample/duration parameters return structured errors without running subprocess.

Tests added:
- blackdetect and freezedetect command construction.
- video mapping order after `-i <rtsp_url>`.
- `-t <sample_seconds>` preservation.
- subprocess.run list args, capture_output=True, text=True, timeout, check=False, and no `shell`.
- black_start/black_end/black_duration parsing.
- freeze_start/freeze_end/freeze_duration parsing.
- no-event, nonzero returncode, timeout, FileNotFoundError, credential sanitization, and invalid-parameter cases.

Validation status:
- pytest -q: 57 passed.
- analytics-vms --help: OK.
- analytics-vms check-inventory examples/vms_input_dummy_repo.csv: OK, 181 rows.
