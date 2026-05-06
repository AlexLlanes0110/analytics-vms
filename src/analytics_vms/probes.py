"""ffprobe wrapper for RTSP stream metadata."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlsplit

from analytics_vms.rtsp import mask_rtsp_url


FFPROBE_COMMAND = "ffprobe"


@dataclass(frozen=True)
class ProbeResult:
    """Structured ffprobe result without final camera classification."""

    ok: bool = False
    timed_out: bool = False
    returncode: int | None = None
    error: str = ""
    raw_stdout: str = ""
    raw_stderr: str = ""
    has_video: bool = False
    video_codec: str | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None


def run_ffprobe(rtsp_url: str, timeout_seconds: float | int) -> ProbeResult:
    """Run ffprobe with timeout and return sanitized metadata signals."""
    command = [
        FFPROBE_COMMAND,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height,avg_frame_rate,r_frame_rate",
        "-of",
        "json",
        rtsp_url,
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return ProbeResult(
            ok=False,
            timed_out=True,
            returncode=None,
            error=f"ffprobe timed out after {timeout_seconds} seconds.",
            raw_stdout=_sanitize_text(exc.stdout, rtsp_url),
            raw_stderr=_sanitize_text(exc.stderr, rtsp_url),
        )
    except FileNotFoundError:
        return ProbeResult(
            ok=False,
            returncode=None,
            error="ffprobe executable not found.",
        )
    except OSError as exc:
        return ProbeResult(
            ok=False,
            returncode=None,
            error=f"ffprobe execution error: {_sanitize_text(str(exc), rtsp_url)}",
        )

    stdout = _sanitize_text(completed.stdout, rtsp_url)
    stderr = _sanitize_text(completed.stderr, rtsp_url)

    if completed.returncode != 0:
        return ProbeResult(
            ok=False,
            returncode=completed.returncode,
            error=_build_process_error(completed.returncode, stderr),
            raw_stdout=stdout,
            raw_stderr=stderr,
        )

    try:
        payload = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return ProbeResult(
            ok=False,
            returncode=completed.returncode,
            error="ffprobe returned invalid JSON.",
            raw_stdout=stdout,
            raw_stderr=stderr,
        )

    stream = _first_video_stream(payload)
    if stream is None:
        return ProbeResult(
            ok=False,
            returncode=completed.returncode,
            error="ffprobe did not return a video stream.",
            raw_stdout=stdout,
            raw_stderr=stderr,
            has_video=False,
        )

    return ProbeResult(
        ok=True,
        returncode=completed.returncode,
        raw_stdout=stdout,
        raw_stderr=stderr,
        has_video=True,
        video_codec=_optional_string(stream.get("codec_name")),
        width=_optional_int(stream.get("width")),
        height=_optional_int(stream.get("height")),
        fps=_parse_fps(
            stream.get("avg_frame_rate"),
            fallback=stream.get("r_frame_rate"),
        ),
    )


def run_probe_stub() -> ProbeResult:
    """Return an empty probe result without external processes."""
    return ProbeResult()


def _first_video_stream(payload: Any) -> dict[str, Any] | None:
    """Return the first stream object from ffprobe JSON."""
    if not isinstance(payload, dict):
        return None

    streams = payload.get("streams")
    if not isinstance(streams, list):
        return None

    for stream in streams:
        if isinstance(stream, dict):
            return stream
    return None


def _parse_fps(value: Any, *, fallback: Any = None) -> float | None:
    """Parse ffprobe frame-rate strings such as 30000/1001."""
    parsed = _parse_single_fps(value)
    if parsed is not None:
        return parsed
    return _parse_single_fps(fallback)


def _parse_single_fps(value: Any) -> float | None:
    """Parse one ffprobe frame-rate value."""
    if value is None:
        return None

    text = str(value).strip()
    if not text or text == "N/A":
        return None

    if "/" in text:
        numerator_text, denominator_text = text.split("/", 1)
        try:
            numerator = float(numerator_text)
            denominator = float(denominator_text)
        except ValueError:
            return None
        if denominator == 0 or numerator == 0:
            return None
        return numerator / denominator

    try:
        fps = float(text)
    except ValueError:
        return None
    if fps == 0:
        return None
    return fps


def _optional_int(value: Any) -> int | None:
    """Convert a ffprobe numeric field to int when possible."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_string(value: Any) -> str | None:
    """Convert a ffprobe string field to a normalized optional string."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text == "N/A":
        return None
    return text


def _build_process_error(returncode: int, stderr: str) -> str:
    """Build a concise sanitized ffprobe error."""
    if stderr:
        return f"ffprobe failed with return code {returncode}: {stderr}"
    return f"ffprobe failed with return code {returncode}."


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
