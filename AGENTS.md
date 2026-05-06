# AGENTS.md

Permanent rules for Codex in this repository.

## Before Any Change

- Read `DEV_NOTES.md`.
- Run:
  - `git status --short --untracked-files=all`
  - `git branch --show-current`
  - `git log --oneline --decorate -10`
- Explain the current repository state before changing code.
- Confirm which MVP/task is being worked on.

## Safety Boundaries

Do not touch without explicit review:

- `.local/`
- `.venv/`
- Docker
- systemd
- firewall
- paths outside this repository
- real camera data
- real IPs
- real users
- real passwords
- real production outputs/evidence

## Engineering Rules

- Do not use `shell=True` in `subprocess`.
- Do not commit unless explicitly requested.
- Do not push unless explicitly requested.
- Update `DEV_NOTES.md` at the end of each task.
- Treat `DEV_NOTES.md` as the live handoff for current MVP state.
- Run validations before closing a task.
- Unit tests must not use real RTSP endpoints, ffprobe, or ffmpeg.

## MVP Branch Methodology

Each MVP must be developed on its own branch.

Required workflow:

1. Start from clean, updated `main`.
2. Create a branch specific to the MVP.
3. Implement only that MVP's scope.
4. Run validations.
5. Update `DEV_NOTES.md`.
6. Commit on the MVP branch when explicitly requested.
7. Push the MVP branch when explicitly requested.
8. Merge the MVP branch into `main`.
9. Push `main`.
10. Create the next branch from updated `main`.

Rules:

- Do not mix the next MVP into the previous MVP branch.
- Do not create a new branch from an unclosed MVP branch unless explicitly instructed.
- Do not implement future scope in the current MVP.
- Keep the MVP history in `DEV_NOTES.md`.
- Move each completed MVP to `Closed MVPs`.
- Keep the next MVP in `Next task`.

## Core Functional Rule

`OK = frames_ok == 1`

- `ffprobe` does not declare a camera OK.
- `ffprobe` only provides metadata and diagnostic signals.
- Final OK depends on `ffmpeg` decoding real frames.
- Visual diagnostics do not change final OK status.
