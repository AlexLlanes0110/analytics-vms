"""Batch camera in-memory check tests."""

from __future__ import annotations

from typing import Any

from analytics_vms.batch_check import (
    BatchCheckSummary,
    check_camera_batch,
)
from analytics_vms.camera_check import CameraCheckResult


def test_check_camera_batch_empty() -> None:
    result = check_camera_batch([])

    assert result.results == ()
    assert result.summary == BatchCheckSummary()


def test_check_camera_batch_calls_single_camera_for_each_row(
    monkeypatch: Any,
) -> None:
    rows = [
        {"camera_name": "CAM-01"},
        {"camera_name": "CAM-02"},
    ]
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_check_single_camera(
        row: dict[str, Any],
        *,
        probe_timeout_seconds: float | int,
        frame_timeout_seconds: float | int,
        min_frames: int,
        enable_visual_diagnostics: bool,
        visual_timeout_seconds: float | int,
        visual_sample_seconds: float | int,
    ) -> CameraCheckResult:
        calls.append(
            (
                row["camera_name"],
                {
                    "probe_timeout_seconds": probe_timeout_seconds,
                    "frame_timeout_seconds": frame_timeout_seconds,
                    "min_frames": min_frames,
                    "enable_visual_diagnostics": enable_visual_diagnostics,
                    "visual_timeout_seconds": visual_timeout_seconds,
                    "visual_sample_seconds": visual_sample_seconds,
                },
            )
        )
        return CameraCheckResult(
            camera_id=row["camera_name"],
            probe_ok=1,
            frames_ok=1,
            status="OK",
        )

    monkeypatch.setattr(
        "analytics_vms.batch_check.check_single_camera",
        fake_check_single_camera,
    )

    result = check_camera_batch(
        rows,
        probe_timeout_seconds=3,
        frame_timeout_seconds=4,
        min_frames=2,
        enable_visual_diagnostics=False,
        visual_timeout_seconds=5,
        visual_sample_seconds=6,
    )

    assert [camera_result.camera_id for camera_result in result.results] == [
        "CAM-01",
        "CAM-02",
    ]
    assert calls == [
        (
            "CAM-01",
            {
                "probe_timeout_seconds": 3,
                "frame_timeout_seconds": 4,
                "min_frames": 2,
                "enable_visual_diagnostics": False,
                "visual_timeout_seconds": 5,
                "visual_sample_seconds": 6,
            },
        ),
        (
            "CAM-02",
            {
                "probe_timeout_seconds": 3,
                "frame_timeout_seconds": 4,
                "min_frames": 2,
                "enable_visual_diagnostics": False,
                "visual_timeout_seconds": 5,
                "visual_sample_seconds": 6,
            },
        ),
    ]


def test_check_camera_batch_summary_counts_status_and_visuals(
    monkeypatch: Any,
) -> None:
    results_by_camera_id = {
        "CAM-OK": CameraCheckResult(
            camera_id="CAM-OK",
            probe_ok=1,
            frames_ok=1,
            status="OK",
            black_detected=1,
        ),
        "CAM-NO-FRAMES": CameraCheckResult(
            camera_id="CAM-NO-FRAMES",
            probe_ok=1,
            frames_ok=0,
            status="NO_FRAMES",
        ),
        "CAM-PROBE-FAILED": CameraCheckResult(
            camera_id="CAM-PROBE-FAILED",
            status="PROBE_FAILED",
        ),
        "CAM-ERROR": CameraCheckResult(
            camera_id="CAM-ERROR",
            status="ERROR",
            freeze_detected=1,
        ),
    }

    def fake_check_single_camera(row: dict[str, Any], **_kwargs: Any) -> CameraCheckResult:
        return results_by_camera_id[row["camera_id"]]

    monkeypatch.setattr(
        "analytics_vms.batch_check.check_single_camera",
        fake_check_single_camera,
    )

    result = check_camera_batch(
        [
            {"camera_id": "CAM-OK"},
            {"camera_id": "CAM-NO-FRAMES"},
            {"camera_id": "CAM-PROBE-FAILED"},
            {"camera_id": "CAM-ERROR"},
        ]
    )

    assert result.summary == BatchCheckSummary(
        total=4,
        ok=1,
        no_frames=1,
        probe_failed=1,
        error=1,
        black_detected=1,
        freeze_detected=1,
    )


def test_check_camera_batch_exception_does_not_stop_batch(
    monkeypatch: Any,
) -> None:
    rows = [
        {"camera_name": "CAM-OK"},
        {
            "camera_name": "CAM-BAD",
            "password": "demo-secret",
        },
        {"camera_name": "CAM-NO-FRAMES"},
    ]

    def fake_check_single_camera(row: dict[str, Any], **_kwargs: Any) -> CameraCheckResult:
        if row["camera_name"] == "CAM-BAD":
            raise RuntimeError(
                "failed rtsp://admin:demo-secret@192.0.2.10:554/stream"
            )
        if row["camera_name"] == "CAM-NO-FRAMES":
            return CameraCheckResult(
                camera_id="CAM-NO-FRAMES",
                probe_ok=1,
                frames_ok=0,
                status="NO_FRAMES",
            )
        return CameraCheckResult(
            camera_id="CAM-OK",
            probe_ok=1,
            frames_ok=1,
            status="OK",
        )

    monkeypatch.setattr(
        "analytics_vms.batch_check.check_single_camera",
        fake_check_single_camera,
    )

    result = check_camera_batch(rows)

    assert [camera_result.camera_id for camera_result in result.results] == [
        "CAM-OK",
        "CAM-BAD",
        "CAM-NO-FRAMES",
    ]
    assert [camera_result.status for camera_result in result.results] == [
        "OK",
        "ERROR",
        "NO_FRAMES",
    ]
    assert result.summary.total == 3
    assert result.summary.ok == 1
    assert result.summary.no_frames == 1
    assert result.summary.error == 1
    assert "demo-secret" not in result.results[1].error
    assert result.results[1].error == "failed rtsp://admin:***@192.0.2.10:554/stream"
