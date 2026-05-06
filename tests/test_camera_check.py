"""Single-camera in-memory check tests."""

from __future__ import annotations

from typing import Any

from analytics_vms.camera_check import CameraCheckResult, check_single_camera
from analytics_vms.frames import FrameValidationResult
from analytics_vms.probes import ProbeResult
from analytics_vms.visual_diagnostics import VisualDiagnosticResult


RTSP_URL = "rtsp://admin:demo-secret@192.0.2.10:554/Streaming/Channels/101"
MASKED_RTSP_URL = "rtsp://admin:***@192.0.2.10:554/Streaming/Channels/101"


def _row(password: str = "demo-secret") -> dict[str, Any]:
    return {
        "camera_name": "DEMO-CAM-01",
        "project_code": "DEMO01",
        "municipality": "Sample Municipality",
        "site_type": "PMI",
        "site_code": "SITE001",
        "site_name": "DEMO-SITE001",
        "camera_role": "PTZ",
        "brand": "unknown",
        "ip": "192.0.2.10",
        "rtsp_port": "554",
        "rtsp_path": "/Streaming/Channels/101",
        "transport": "tcp",
        "username": "admin",
        "password": password,
    }


def _patch_build_rtsp(monkeypatch: Any, rtsp_url: str = RTSP_URL) -> None:
    def fake_build_rtsp_url(_inventory_row: Any) -> str:
        return rtsp_url

    monkeypatch.setattr("analytics_vms.camera_check.build_rtsp_url", fake_build_rtsp_url)


def _patch_probe(monkeypatch: Any, probe: ProbeResult | None = None) -> None:
    probe_result = probe or ProbeResult(ok=True, has_video=True, returncode=0)

    def fake_run_ffprobe(
        rtsp_url: str,
        *,
        timeout_seconds: float | int,
    ) -> ProbeResult:
        assert rtsp_url == RTSP_URL
        assert timeout_seconds == 3
        return probe_result

    monkeypatch.setattr("analytics_vms.camera_check.run_ffprobe", fake_run_ffprobe)


def _patch_frames(
    monkeypatch: Any,
    frames: FrameValidationResult | None = None,
) -> None:
    frame_result = frames or FrameValidationResult(
        frames_ok=1,
        ok=True,
        returncode=0,
        decoded_frames=1,
    )

    def fake_validate_rtsp_frames(
        rtsp_url: str,
        *,
        timeout_seconds: float | int,
        min_frames: int,
    ) -> FrameValidationResult:
        assert rtsp_url == RTSP_URL
        assert timeout_seconds == 4
        assert min_frames == 1
        return frame_result

    monkeypatch.setattr(
        "analytics_vms.camera_check.validate_rtsp_frames",
        fake_validate_rtsp_frames,
    )


def _patch_visuals(
    monkeypatch: Any,
    calls: list[str],
    *,
    black: VisualDiagnosticResult | None = None,
    freeze: VisualDiagnosticResult | None = None,
) -> None:
    black_result = black or VisualDiagnosticResult(
        detector="blackdetect",
        process_ok=True,
        detected=0,
    )
    freeze_result = freeze or VisualDiagnosticResult(
        detector="freezedetect",
        process_ok=True,
        detected=0,
    )

    def fake_detect_black_frames(
        rtsp_url: str,
        *,
        timeout_seconds: float | int,
        sample_seconds: float | int,
    ) -> VisualDiagnosticResult:
        assert rtsp_url == RTSP_URL
        assert timeout_seconds == 5
        assert sample_seconds == 6
        calls.append("black")
        return black_result

    def fake_detect_frozen_frames(
        rtsp_url: str,
        *,
        timeout_seconds: float | int,
        sample_seconds: float | int,
    ) -> VisualDiagnosticResult:
        assert rtsp_url == RTSP_URL
        assert timeout_seconds == 5
        assert sample_seconds == 6
        calls.append("freeze")
        return freeze_result

    monkeypatch.setattr(
        "analytics_vms.camera_check.detect_black_frames",
        fake_detect_black_frames,
    )
    monkeypatch.setattr(
        "analytics_vms.camera_check.detect_frozen_frames",
        fake_detect_frozen_frames,
    )


def test_check_single_camera_ok(monkeypatch: Any) -> None:
    calls: list[str] = []
    _patch_build_rtsp(monkeypatch)
    _patch_probe(monkeypatch)
    _patch_frames(monkeypatch)
    _patch_visuals(monkeypatch, calls)

    result = check_single_camera(
        _row(),
        probe_timeout_seconds=3,
        frame_timeout_seconds=4,
        visual_timeout_seconds=5,
        visual_sample_seconds=6,
    )

    assert result == CameraCheckResult(
        camera_id="DEMO-CAM-01",
        rtsp_url_masked=MASKED_RTSP_URL,
        probe_ok=1,
        frames_ok=1,
        black_detected=0,
        freeze_detected=0,
        status="OK",
        error="",
        probe=result.probe,
        frames=result.frames,
        black=result.black,
        freeze=result.freeze,
    )
    assert calls == ["black", "freeze"]


def test_check_single_camera_runs_visual_diagnostics_when_frames_ok(
    monkeypatch: Any,
) -> None:
    calls: list[str] = []
    _patch_build_rtsp(monkeypatch)
    _patch_probe(monkeypatch)
    _patch_frames(monkeypatch)
    _patch_visuals(monkeypatch, calls)

    result = check_single_camera(
        _row(),
        probe_timeout_seconds=3,
        frame_timeout_seconds=4,
        visual_timeout_seconds=5,
        visual_sample_seconds=6,
    )

    assert result.frames_ok == 1
    assert calls == ["black", "freeze"]
    assert result.black is not None
    assert result.freeze is not None


def test_check_single_camera_no_frames_skips_visual_diagnostics(
    monkeypatch: Any,
) -> None:
    calls: list[str] = []
    _patch_build_rtsp(monkeypatch)
    _patch_probe(monkeypatch)
    _patch_frames(
        monkeypatch,
        FrameValidationResult(
            frames_ok=0,
            ok=False,
            returncode=1,
            error="no frames decoded",
            decoded_frames=0,
        ),
    )
    _patch_visuals(monkeypatch, calls)

    result = check_single_camera(
        _row(),
        probe_timeout_seconds=3,
        frame_timeout_seconds=4,
        visual_timeout_seconds=5,
        visual_sample_seconds=6,
    )

    assert result.status == "NO_FRAMES"
    assert result.probe_ok == 1
    assert result.frames_ok == 0
    assert result.error == "no frames decoded"
    assert result.black is None
    assert result.freeze is None
    assert calls == []


def test_check_single_camera_probe_failed_skips_frames_and_visuals(
    monkeypatch: Any,
) -> None:
    calls: list[str] = []
    frames_called = False
    _patch_build_rtsp(monkeypatch)
    _patch_probe(
        monkeypatch,
        ProbeResult(ok=False, returncode=1, error="probe failed"),
    )

    def fake_validate_rtsp_frames(*args: Any, **kwargs: Any) -> FrameValidationResult:
        nonlocal frames_called
        frames_called = True
        return FrameValidationResult()

    monkeypatch.setattr(
        "analytics_vms.camera_check.validate_rtsp_frames",
        fake_validate_rtsp_frames,
    )
    _patch_visuals(monkeypatch, calls)

    result = check_single_camera(
        _row(),
        probe_timeout_seconds=3,
        frame_timeout_seconds=4,
        visual_timeout_seconds=5,
        visual_sample_seconds=6,
    )

    assert result.status == "PROBE_FAILED"
    assert result.probe_ok == 0
    assert result.frames is None
    assert result.error == "probe failed"
    assert frames_called is False
    assert calls == []


def test_check_single_camera_visual_diagnostics_disabled(
    monkeypatch: Any,
) -> None:
    calls: list[str] = []
    _patch_build_rtsp(monkeypatch)
    _patch_probe(monkeypatch)
    _patch_frames(monkeypatch)
    _patch_visuals(monkeypatch, calls)

    result = check_single_camera(
        _row(),
        probe_timeout_seconds=3,
        frame_timeout_seconds=4,
        enable_visual_diagnostics=False,
        visual_timeout_seconds=5,
        visual_sample_seconds=6,
    )

    assert result.status == "OK"
    assert result.frames_ok == 1
    assert result.black is None
    assert result.freeze is None
    assert calls == []


def test_check_single_camera_build_rtsp_error_returns_error(
    monkeypatch: Any,
) -> None:
    def fake_build_rtsp_url(_inventory_row: Any) -> str:
        raise ValueError("bad credentials demo-secret")

    monkeypatch.setattr("analytics_vms.camera_check.build_rtsp_url", fake_build_rtsp_url)

    result = check_single_camera(_row())

    assert result.status == "ERROR"
    assert result.probe is None
    assert result.frames is None
    assert "demo-secret" not in result.error
    assert result.error == "bad credentials ***"


def test_check_single_camera_masks_rtsp_password(monkeypatch: Any) -> None:
    calls: list[str] = []
    _patch_build_rtsp(monkeypatch)
    _patch_probe(monkeypatch)
    _patch_frames(monkeypatch)
    _patch_visuals(monkeypatch, calls)

    result = check_single_camera(
        _row(),
        probe_timeout_seconds=3,
        frame_timeout_seconds=4,
        visual_timeout_seconds=5,
        visual_sample_seconds=6,
    )

    assert result.rtsp_url_masked == MASKED_RTSP_URL
    assert "demo-secret" not in result.rtsp_url_masked


def test_check_single_camera_status_ok_depends_only_on_frames_ok(
    monkeypatch: Any,
) -> None:
    calls: list[str] = []
    _patch_build_rtsp(monkeypatch)
    _patch_probe(monkeypatch)
    _patch_frames(monkeypatch)
    _patch_visuals(
        monkeypatch,
        calls,
        black=VisualDiagnosticResult(
            detector="blackdetect",
            process_ok=True,
            detected=1,
        ),
        freeze=VisualDiagnosticResult(
            detector="freezedetect",
            process_ok=True,
            detected=1,
        ),
    )

    result = check_single_camera(
        _row(),
        probe_timeout_seconds=3,
        frame_timeout_seconds=4,
        visual_timeout_seconds=5,
        visual_sample_seconds=6,
    )

    assert result.status == "OK"
    assert result.frames_ok == 1
    assert result.black_detected == 1
    assert result.freeze_detected == 1
    assert calls == ["black", "freeze"]


def test_check_single_camera_visual_failure_does_not_change_ok_status(
    monkeypatch: Any,
) -> None:
    calls: list[str] = []
    _patch_build_rtsp(monkeypatch)
    _patch_probe(monkeypatch)
    _patch_frames(monkeypatch)
    _patch_visuals(
        monkeypatch,
        calls,
        black=VisualDiagnosticResult(
            detector="blackdetect",
            process_ok=False,
            detected=0,
            error="blackdetect failed",
        ),
        freeze=VisualDiagnosticResult(
            detector="freezedetect",
            process_ok=False,
            detected=0,
            error="freezedetect failed",
        ),
    )

    result = check_single_camera(
        _row(),
        probe_timeout_seconds=3,
        frame_timeout_seconds=4,
        visual_timeout_seconds=5,
        visual_sample_seconds=6,
    )

    assert result.status == "OK"
    assert result.error == ""
    assert result.black is not None
    assert result.black.error == "blackdetect failed"
    assert result.freeze is not None
    assert result.freeze.error == "freezedetect failed"
