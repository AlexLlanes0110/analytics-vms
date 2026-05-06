"""In-memory single-camera health check orchestration."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, unquote

from analytics_vms.frames import FrameValidationResult, validate_rtsp_frames
from analytics_vms.inventory import InventoryRow, normalize_inventory_row
from analytics_vms.probes import ProbeResult, run_ffprobe
from analytics_vms.rtsp import build_rtsp_url, mask_rtsp_url
from analytics_vms.visual_diagnostics import (
    BLACK_DETECTOR,
    FREEZE_DETECTOR,
    VisualDiagnosticResult,
    detect_black_frames,
    detect_frozen_frames,
)


@dataclass(frozen=True)
class CameraCheckResult:
    """Structured in-memory result for one camera row."""

    camera_id: str
    rtsp_url_masked: str = ""
    probe_ok: int = 0
    frames_ok: int = 0
    black_detected: int = 0
    freeze_detected: int = 0
    status: str = "ERROR"
    error: str = ""
    probe: ProbeResult | None = None
    frames: FrameValidationResult | None = None
    black: VisualDiagnosticResult | None = None
    freeze: VisualDiagnosticResult | None = None


def check_single_camera(
    row: Mapping[str, Any],
    *,
    probe_timeout_seconds: float | int = 5,
    frame_timeout_seconds: float | int = 10,
    min_frames: int = 1,
    enable_visual_diagnostics: bool = True,
    visual_timeout_seconds: float | int = 10,
    visual_sample_seconds: float | int = 5,
) -> CameraCheckResult:
    """Run one in-memory camera check without CLI, batch, or report output."""
    camera_id = _camera_id(row)
    rtsp_url = ""
    rtsp_url_masked = ""

    try:
        inventory_row = _inventory_row_from_mapping(row)
        rtsp_url = build_rtsp_url(inventory_row)
        rtsp_url_masked = _safe_mask_rtsp_url(rtsp_url)
    except Exception as exc:
        return CameraCheckResult(
            camera_id=camera_id,
            rtsp_url_masked=rtsp_url_masked,
            status="ERROR",
            error=_sanitize_error(str(exc), row=row, rtsp_url=rtsp_url),
        )

    try:
        probe = run_ffprobe(rtsp_url, timeout_seconds=probe_timeout_seconds)
    except Exception as exc:
        return CameraCheckResult(
            camera_id=camera_id,
            rtsp_url_masked=rtsp_url_masked,
            status="ERROR",
            error=_sanitize_error(str(exc), row=row, rtsp_url=rtsp_url),
        )

    probe_ok = 1 if probe.ok else 0
    if probe_ok == 0:
        return CameraCheckResult(
            camera_id=camera_id,
            rtsp_url_masked=rtsp_url_masked,
            probe_ok=0,
            frames_ok=0,
            status="PROBE_FAILED",
            error=_sanitize_error(probe.error, row=row, rtsp_url=rtsp_url),
            probe=probe,
        )

    try:
        frames = validate_rtsp_frames(
            rtsp_url,
            timeout_seconds=frame_timeout_seconds,
            min_frames=min_frames,
        )
    except Exception as exc:
        return CameraCheckResult(
            camera_id=camera_id,
            rtsp_url_masked=rtsp_url_masked,
            probe_ok=probe_ok,
            status="ERROR",
            error=_sanitize_error(str(exc), row=row, rtsp_url=rtsp_url),
            probe=probe,
        )

    frames_ok = 1 if frames.frames_ok == 1 else 0
    status = "OK" if frames_ok == 1 else "NO_FRAMES"

    if frames_ok == 0 or not enable_visual_diagnostics:
        return CameraCheckResult(
            camera_id=camera_id,
            rtsp_url_masked=rtsp_url_masked,
            probe_ok=probe_ok,
            frames_ok=frames_ok,
            status=status,
            error=_sanitize_error(frames.error, row=row, rtsp_url=rtsp_url),
            probe=probe,
            frames=frames,
        )

    black = _run_visual_diagnostic(
        BLACK_DETECTOR,
        detect_black_frames,
        rtsp_url,
        row=row,
        timeout_seconds=visual_timeout_seconds,
        sample_seconds=visual_sample_seconds,
    )
    freeze = _run_visual_diagnostic(
        FREEZE_DETECTOR,
        detect_frozen_frames,
        rtsp_url,
        row=row,
        timeout_seconds=visual_timeout_seconds,
        sample_seconds=visual_sample_seconds,
    )

    return CameraCheckResult(
        camera_id=camera_id,
        rtsp_url_masked=rtsp_url_masked,
        probe_ok=probe_ok,
        frames_ok=frames_ok,
        black_detected=black.detected,
        freeze_detected=freeze.detected,
        status=status,
        error="",
        probe=probe,
        frames=frames,
        black=black,
        freeze=freeze,
    )


def _inventory_row_from_mapping(row: Mapping[str, Any]) -> InventoryRow:
    """Build the existing InventoryRow type from an in-memory mapping."""
    normalized = normalize_inventory_row(row)
    return InventoryRow(
        project_code=normalized.get("project_code", ""),
        municipality=normalized.get("municipality", ""),
        site_type=normalized.get("site_type", ""),
        site_code=normalized.get("site_code", ""),
        site_name=normalized.get("site_name", ""),
        traffic_direction=normalized.get("traffic_direction", ""),
        camera_role=normalized.get("camera_role", ""),
        camera_name=normalized.get("camera_name", ""),
        brand=normalized.get("brand", ""),
        ip=normalized.get("ip", ""),
        rtsp_port=int(normalized.get("rtsp_port", "")),
        rtsp_path=normalized.get("rtsp_path", ""),
        transport=normalized.get("transport", ""),
        credential_id=normalized.get("credential_id", ""),
        username=normalized.get("username", ""),
        password=normalized.get("password", ""),
        extra={
            key: value
            for key, value in normalized.items()
            if key
            not in {
                "project_code",
                "municipality",
                "site_type",
                "site_code",
                "site_name",
                "traffic_direction",
                "camera_role",
                "camera_name",
                "brand",
                "ip",
                "rtsp_port",
                "rtsp_path",
                "transport",
                "credential_id",
                "username",
                "password",
            }
        },
        row_number=_optional_int(normalized.get("row_number")),
    )


def _run_visual_diagnostic(
    detector: str,
    detector_func: Any,
    rtsp_url: str,
    *,
    row: Mapping[str, Any],
    timeout_seconds: float | int,
    sample_seconds: float | int,
) -> VisualDiagnosticResult:
    """Run a visual detector without allowing it to change camera status."""
    try:
        return detector_func(
            rtsp_url,
            timeout_seconds=timeout_seconds,
            sample_seconds=sample_seconds,
        )
    except Exception as exc:
        return VisualDiagnosticResult(
            detector=detector,
            process_ok=False,
            detected=0,
            events=(),
            returncode=None,
            error=_sanitize_error(str(exc), row=row, rtsp_url=rtsp_url),
        )


def _camera_id(row: Mapping[str, Any]) -> str:
    """Choose a stable display id for the in-memory camera result."""
    for key in ("camera_id", "camera_name", "site_code"):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _optional_int(value: Any) -> int | None:
    """Convert an optional numeric value to int."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_mask_rtsp_url(rtsp_url: str) -> str:
    """Mask an RTSP URL without allowing masking errors to escape."""
    if not rtsp_url:
        return ""
    try:
        return mask_rtsp_url(rtsp_url)
    except Exception:
        return re.sub(
            r"(rtsp://[^:\s/@]+):([^@\s]+)@([^\s'\"<>]+)",
            r"\1:***@\3",
            rtsp_url,
        )


def _sanitize_error(
    message: Any,
    *,
    row: Mapping[str, Any],
    rtsp_url: str = "",
) -> str:
    """Sanitize top-level single-camera errors."""
    text = "" if message is None else str(message)
    if not text:
        return ""

    if rtsp_url:
        text = text.replace(rtsp_url, _safe_mask_rtsp_url(rtsp_url))

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
