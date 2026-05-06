"""In-memory batch camera health check orchestration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, unquote

from analytics_vms.camera_check import CameraCheckResult, check_single_camera


@dataclass(frozen=True)
class BatchCheckSummary:
    """Basic in-memory summary for a camera batch."""

    total: int = 0
    ok: int = 0
    no_frames: int = 0
    probe_failed: int = 0
    error: int = 0
    black_detected: int = 0
    freeze_detected: int = 0


@dataclass(frozen=True)
class BatchCheckResult:
    """Structured in-memory result for multiple camera rows."""

    results: tuple[CameraCheckResult, ...]
    summary: BatchCheckSummary


def check_camera_batch(
    rows: Iterable[Mapping[str, Any]],
    *,
    probe_timeout_seconds: float | int = 5,
    frame_timeout_seconds: float | int = 10,
    min_frames: int = 1,
    enable_visual_diagnostics: bool = True,
    visual_timeout_seconds: float | int = 10,
    visual_sample_seconds: float | int = 5,
) -> BatchCheckResult:
    """Run single-camera checks for loaded rows without file or CLI output."""
    results: list[CameraCheckResult] = []

    for row in rows:
        try:
            result = check_single_camera(
                row,
                probe_timeout_seconds=probe_timeout_seconds,
                frame_timeout_seconds=frame_timeout_seconds,
                min_frames=min_frames,
                enable_visual_diagnostics=enable_visual_diagnostics,
                visual_timeout_seconds=visual_timeout_seconds,
                visual_sample_seconds=visual_sample_seconds,
            )
        except Exception as exc:
            result = CameraCheckResult(
                camera_id=_camera_id(row),
                status="ERROR",
                error=_sanitize_error(str(exc), row=row),
            )
        results.append(result)

    results_tuple = tuple(results)
    return BatchCheckResult(
        results=results_tuple,
        summary=_summarize_results(results_tuple),
    )


def _summarize_results(
    results: tuple[CameraCheckResult, ...],
) -> BatchCheckSummary:
    """Build status and visual diagnostic counts from camera results."""
    return BatchCheckSummary(
        total=len(results),
        ok=sum(1 for result in results if result.status == "OK"),
        no_frames=sum(1 for result in results if result.status == "NO_FRAMES"),
        probe_failed=sum(1 for result in results if result.status == "PROBE_FAILED"),
        error=sum(1 for result in results if result.status == "ERROR"),
        black_detected=sum(1 for result in results if result.black_detected == 1),
        freeze_detected=sum(1 for result in results if result.freeze_detected == 1),
    )


def _camera_id(row: Mapping[str, Any]) -> str:
    """Choose a stable display id when a row-level batch error occurs."""
    for key in ("camera_id", "camera_name", "ip", "host", "site_code"):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _sanitize_error(message: Any, *, row: Mapping[str, Any]) -> str:
    """Sanitize batch-level unexpected errors."""
    text = "" if message is None else str(message)
    if not text:
        return ""

    for secret in _row_secret_tokens(row):
        text = text.replace(secret, "***")

    return text


def _row_secret_tokens(row: Mapping[str, Any]) -> set[str]:
    """Return raw, URL-encoded, and decoded password tokens from a row."""
    password = row.get("password")
    if password is None:
        return set()

    text = str(password)
    tokens = {text, quote(text, safe=""), unquote(text)}
    return {token for token in tokens if token}
