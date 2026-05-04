"""Probe stubs for stream metadata and frame checks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProbeResult:
    """Minimal probe result shape used by later MVPs."""

    frames_ok: int = 0
    codec: str | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None


def run_probe_stub() -> ProbeResult:
    """Return an empty probe result without external processes."""
    return ProbeResult()
