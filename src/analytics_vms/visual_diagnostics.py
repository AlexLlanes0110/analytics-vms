"""Optional ffmpeg visual diagnostic detectors for RTSP streams."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlsplit

from analytics_vms.rtsp import mask_rtsp_url


FFMPEG_COMMAND = "ffmpeg"
BLACK_DETECTOR = "blackdetect"
FREEZE_DETECTOR = "freezedetect"
_NUMBER_PATTERN = r"[-+]?\d+(?:\.\d+)?"


@dataclass(frozen=True)
class VisualDiagnosticEvent:
    """One visual diagnostic event detected by ffmpeg filters."""

    kind: str
    start_seconds: float | None = None
    end_seconds: float | None = None
    duration_seconds: float | None = None


@dataclass(frozen=True)
class VisualDiagnosticResult:
    """Structured result for an isolated visual diagnostic detector."""

    detector: str
    process_ok: bool = False
    detected: int = 0
    events: tuple[VisualDiagnosticEvent, ...] = ()
    timed_out: bool = False
    returncode: int | None = None
    error: str = ""
    raw_stdout: str = ""
    raw_stderr: str = ""


def detect_black_frames(
    rtsp_url: str,
    timeout_seconds: float | int,
    sample_seconds: float | int = 5,
    min_black_duration_seconds: float = 1.0,
    picture_black_threshold: float = 0.98,
    pixel_black_threshold: float = 0.10,
) -> VisualDiagnosticResult:
    """Run ffmpeg blackdetect over a bounded RTSP sample."""
    validation_error = _positive_number_error("sample_seconds", sample_seconds)
    if validation_error is None:
        validation_error = _positive_number_error(
            "min_black_duration_seconds",
            min_black_duration_seconds,
        )
    if validation_error is not None:
        return _validation_result(BLACK_DETECTOR, validation_error)

    video_filter = (
        f"blackdetect=d={min_black_duration_seconds}:"
        f"pix_th={pixel_black_threshold}:pic_th={picture_black_threshold}"
    )
    command = _build_detector_command(rtsp_url, sample_seconds, video_filter)
    return _run_detector(
        BLACK_DETECTOR,
        command,
        rtsp_url,
        timeout_seconds,
        _parse_black_events,
    )


def detect_frozen_frames(
    rtsp_url: str,
    timeout_seconds: float | int,
    sample_seconds: float | int = 5,
    min_freeze_duration_seconds: float = 2.0,
    noise_db: str = "-60dB",
) -> VisualDiagnosticResult:
    """Run ffmpeg freezedetect over a bounded RTSP sample."""
    validation_error = _positive_number_error("sample_seconds", sample_seconds)
    if validation_error is None:
        validation_error = _positive_number_error(
            "min_freeze_duration_seconds",
            min_freeze_duration_seconds,
        )
    if validation_error is not None:
        return _validation_result(FREEZE_DETECTOR, validation_error)

    video_filter = f"freezedetect=n={noise_db}:d={min_freeze_duration_seconds}"
    command = _build_detector_command(rtsp_url, sample_seconds, video_filter)
    return _run_detector(
        FREEZE_DETECTOR,
        command,
        rtsp_url,
        timeout_seconds,
        _parse_freeze_events,
    )


def _build_detector_command(
    rtsp_url: str,
    sample_seconds: float | int,
    video_filter: str,
) -> list[str]:
    """Build the shared ffmpeg command for visual detectors."""
    return [
        FFMPEG_COMMAND,
        "-v",
        "info",
        "-rtsp_transport",
        "tcp",
        "-i",
        rtsp_url,
        "-map",
        "0:v:0",
        "-an",
        "-t",
        str(sample_seconds),
        "-vf",
        video_filter,
        "-f",
        "null",
        "-",
    ]


def _run_detector(
    detector: str,
    command: list[str],
    rtsp_url: str,
    timeout_seconds: float | int,
    parse_events: Callable[[str], tuple[VisualDiagnosticEvent, ...]],
) -> VisualDiagnosticResult:
    """Run one ffmpeg detector and return sanitized structured output."""
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return VisualDiagnosticResult(
            detector=detector,
            process_ok=False,
            detected=0,
            events=(),
            timed_out=True,
            returncode=None,
            error=f"ffmpeg {detector} timed out after {timeout_seconds} seconds.",
            raw_stdout=_sanitize_text(exc.stdout, rtsp_url),
            raw_stderr=_sanitize_text(exc.stderr, rtsp_url),
        )
    except FileNotFoundError:
        return VisualDiagnosticResult(
            detector=detector,
            process_ok=False,
            detected=0,
            events=(),
            returncode=None,
            error="ffmpeg executable not found.",
        )
    except OSError as exc:
        return VisualDiagnosticResult(
            detector=detector,
            process_ok=False,
            detected=0,
            events=(),
            returncode=None,
            error=f"ffmpeg {detector} execution error: "
            f"{_sanitize_text(str(exc), rtsp_url)}",
        )

    stdout = _sanitize_text(completed.stdout, rtsp_url)
    stderr = _sanitize_text(completed.stderr, rtsp_url)

    if completed.returncode != 0:
        return VisualDiagnosticResult(
            detector=detector,
            process_ok=False,
            detected=0,
            events=(),
            returncode=completed.returncode,
            error=_build_process_error(detector, completed.returncode, stderr),
            raw_stdout=stdout,
            raw_stderr=stderr,
        )

    events = parse_events(stderr)
    return VisualDiagnosticResult(
        detector=detector,
        process_ok=True,
        detected=1 if events else 0,
        events=events,
        returncode=completed.returncode,
        raw_stdout=stdout,
        raw_stderr=stderr,
    )


def _parse_black_events(stderr: str) -> tuple[VisualDiagnosticEvent, ...]:
    """Parse blackdetect events from ffmpeg stderr."""
    events: list[VisualDiagnosticEvent] = []
    pending_start: float | None = None

    for line in stderr.splitlines():
        start = _metric_value(line, "black_start")
        end = _metric_value(line, "black_end")
        duration = _metric_value(line, "black_duration")

        if start is not None:
            pending_start = start

        if end is None and duration is None:
            continue

        events.append(
            VisualDiagnosticEvent(
                kind="black",
                start_seconds=pending_start,
                end_seconds=end,
                duration_seconds=duration,
            )
        )
        pending_start = None

    return tuple(events)


def _parse_freeze_events(stderr: str) -> tuple[VisualDiagnosticEvent, ...]:
    """Parse freezedetect events from ffmpeg stderr."""
    events: list[VisualDiagnosticEvent] = []
    pending_start: float | None = None
    pending_duration: float | None = None

    for line in stderr.splitlines():
        start = _metric_value(line, "freeze_start")
        duration = _metric_value(line, "freeze_duration")
        end = _metric_value(line, "freeze_end")

        if start is not None:
            pending_start = start
            pending_duration = None
        if duration is not None:
            pending_duration = duration
        if end is None:
            continue

        events.append(
            VisualDiagnosticEvent(
                kind="freeze",
                start_seconds=pending_start,
                end_seconds=end,
                duration_seconds=pending_duration,
            )
        )
        pending_start = None
        pending_duration = None

    return tuple(events)


def _metric_value(line: str, name: str) -> float | None:
    """Return one ffmpeg filter metric from a stderr line."""
    match = re.search(rf"{re.escape(name)}\s*:\s*({_NUMBER_PATTERN})", line)
    if match is None:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _positive_number_error(name: str, value: Any) -> str | None:
    """Return an error when a numeric parameter is not positive."""
    try:
        if float(value) > 0:
            return None
    except (TypeError, ValueError):
        pass
    return f"{name} debe ser mayor a 0."


def _validation_result(detector: str, error: str) -> VisualDiagnosticResult:
    """Return a structured result for validation errors."""
    return VisualDiagnosticResult(
        detector=detector,
        process_ok=False,
        detected=0,
        events=(),
        returncode=None,
        error=error,
    )


def _build_process_error(detector: str, returncode: int, stderr: str) -> str:
    """Build a concise sanitized ffmpeg detector error."""
    if stderr:
        return f"ffmpeg {detector} failed with return code {returncode}: {stderr}"
    return f"ffmpeg {detector} failed with return code {returncode}."


def _sanitize_text(value: Any, rtsp_url: str) -> str:
    """Mask RTSP passwords in captured process output."""
    text = _to_text(value)
    if not text:
        return ""

    masked_url = _safe_mask_rtsp_url(rtsp_url)
    text = text.replace(rtsp_url, masked_url)

    for match in re.findall(r"rtsp://[^\s'\"<>]+", text):
        text = text.replace(match, _safe_mask_rtsp_url(match))

    for secret in _password_tokens(rtsp_url):
        text = text.replace(secret, "***")

    return text


def _safe_mask_rtsp_url(value: str) -> str:
    """Mask an RTSP URL without allowing sanitizer failures to escape."""
    try:
        return mask_rtsp_url(value)
    except Exception:
        pass

    try:
        return re.sub(
            r"(rtsp://[^:\s/@]+):([^@\s]+)@([^\s'\"<>]+)",
            r"\1:***@\3",
            value,
        )
    except Exception:
        return value


def _password_tokens(rtsp_url: str) -> set[str]:
    """Return encoded and decoded password tokens from an RTSP URL."""
    try:
        parts = urlsplit(rtsp_url)
        if "@" not in parts.netloc:
            return set()

        userinfo, _hostinfo = parts.netloc.rsplit("@", 1)
        if ":" not in userinfo:
            return set()

        _username, password = userinfo.rsplit(":", 1)
        tokens = {password, unquote(password)}
        return {token for token in tokens if token}
    except Exception:
        return set()


def _to_text(value: Any) -> str:
    """Convert subprocess output to text."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)
