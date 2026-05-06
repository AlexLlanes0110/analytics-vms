"""Import checks for the Analytics VMS package."""

import analytics_vms
from analytics_vms import (
    batch_check,
    camera_check,
    classify,
    config,
    detection,
    frames,
    inventory,
    probes,
    reports,
    rtsp,
    visual_diagnostics,
)


def test_package_version() -> None:
    assert analytics_vms.__version__ == "0.1.0"


def test_modules_import() -> None:
    assert config.default_config().batch_size == 15
    assert inventory.normalize_inventory_row({"camera_name": "dummy"}) == {
        "camera_name": "dummy"
    }
    assert probes.run_probe_stub().ok is False
    assert frames.FrameValidationResult().frames_ok == 0
    assert visual_diagnostics.VisualDiagnosticResult(detector="blackdetect").detected == 0
    assert camera_check.CameraCheckResult(camera_id="dummy").status == "ERROR"
    assert batch_check.BatchCheckSummary().total == 0
    assert detection.run_detection_stub().black_events == 0
    assert reports.build_detailed_rows([{"status": "NO_FRAMES"}]) == [
        {"status": "NO_FRAMES"}
    ]
    assert hasattr(rtsp, "build_rtsp_url")


def test_ok_rule() -> None:
    assert classify.classify_frames(1) == "OK"
    assert classify.classify_frames(0) != "OK"
