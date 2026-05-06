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
- Update `DEV_NOTES.md` at the end of each task.
- Run validations before closing a task.

## Core Functional Rule

`OK = frames_ok == 1`

- `ffprobe` does not declare a camera OK.
- `ffprobe` only provides metadata and diagnostic signals.
- Final OK depends on `ffmpeg` decoding real frames in a later phase.
