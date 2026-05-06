"""ffmpeg frame validation for RTSP streams."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlsplit

from analytics_vms.rtsp import mask_rtsp_url


FFMPEG_COMMAND = "ffmpeg"


@dataclass(frozen=True)
class FrameValidationResult:
    """Structured ffmpeg frame validation result.

    Here, ok means ffmpeg decoded at least min_frames frames. It is equivalent
    to frames_ok == 1 inside this isolated validation piece.
    """

    frames_ok: int = 0
    ok: bool = False
    timed_out: bool = False
    returncode: int | None = None
    error: str = ""
    raw_stdout: str = ""
    raw_stderr: str = ""
    decoded_frames: int | None = None


def validate_rtsp_frames(
    rtsp_url: str,
    timeout_seconds: float | int,
    min_frames: int = 1,
) -> FrameValidationResult:
    """Use ffmpeg to validate that real frames can be decoded."""
    if min_frames < 1:
        return FrameValidationResult(
            frames_ok=0,
            ok=False,
            returncode=None,
            error="min_frames debe ser mayor o igual a 1.",
            decoded_frames=None,
        )

    command = [
        FFMPEG_COMMAND,
        "-v",
        "error",
        "-rtsp_transport",
        "tcp",
        "-i",
        rtsp_url,
        "-map",
        "0:v:0",
        "-an",
        "-frames:v",
        str(min_frames),
        "-f",
        "null",
        "-",
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
        return FrameValidationResult(
            frames_ok=0,
            ok=False,
            timed_out=True,
            returncode=None,
            error=f"ffmpeg timed out after {timeout_seconds} seconds.",
            raw_stdout=_sanitize_text(exc.stdout, rtsp_url),
            raw_stderr=_sanitize_text(exc.stderr, rtsp_url),
            decoded_frames=0,
        )
    except FileNotFoundError:
        return FrameValidationResult(
            frames_ok=0,
            ok=False,
            returncode=None,
            error="ffmpeg executable not found.",
            decoded_frames=None,
        )
    except OSError as exc:
        return FrameValidationResult(
            frames_ok=0,
            ok=False,
            returncode=None,
            error=f"ffmpeg execution error: {_sanitize_text(str(exc), rtsp_url)}",
            decoded_frames=None,
        )

    stdout = _sanitize_text(completed.stdout, rtsp_url)
    stderr = _sanitize_text(completed.stderr, rtsp_url)

    if completed.returncode != 0:
        return FrameValidationResult(
            frames_ok=0,
            ok=False,
            returncode=completed.returncode,
            error=_build_process_error(completed.returncode, stderr),
            raw_stdout=stdout,
            raw_stderr=stderr,
            decoded_frames=0,
        )

    return FrameValidationResult(
        frames_ok=1,
        ok=True,
        returncode=completed.returncode,
        raw_stdout=stdout,
        raw_stderr=stderr,
        decoded_frames=min_frames,
    )


def _build_process_error(returncode: int, stderr: str) -> str:
    """Build a concise sanitized ffmpeg error."""
    if stderr:
        return f"ffmpeg failed with return code {returncode}: {stderr}"
    return f"ffmpeg failed with return code {returncode}."


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
