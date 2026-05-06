"""Visual detection stubs for black and frozen video."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionResult:
    """Minimal visual detection result shape."""

    black_events: int = 0
    freeze_events: int = 0


def run_detection_stub() -> DetectionResult:
    """Return empty visual detection counts."""
    return DetectionResult()
