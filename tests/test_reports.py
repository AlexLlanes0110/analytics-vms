"""Report helper tests."""

from __future__ import annotations

import json
from pathlib import Path

from analytics_vms import reports
from analytics_vms.batch_check import BatchCheckResult, BatchCheckSummary
from analytics_vms.camera_check import CameraCheckResult


def _results() -> tuple[CameraCheckResult, ...]:
    return (
        CameraCheckResult(
            camera_id="CAM-OK",
            rtsp_url_masked="rtsp://user:***@192.0.2.10/stream",
            probe_ok=1,
            frames_ok=1,
            black_detected=1,
            status="OK",
        ),
        CameraCheckResult(
            camera_id="CAM-NO-FRAMES",
            rtsp_url_masked="rtsp://user:***@192.0.2.11/stream",
            probe_ok=1,
            frames_ok=0,
            status="NO_FRAMES",
            error="no frames decoded",
        ),
        CameraCheckResult(
            camera_id="CAM-PROBE",
            rtsp_url_masked="rtsp://user:***@192.0.2.12/stream",
            status="PROBE_FAILED",
            error="probe failed",
        ),
        CameraCheckResult(
            camera_id="CAM-ERROR",
            freeze_detected=1,
            status="ERROR",
            error="unexpected dummy error",
        ),
    )


def _batch_result() -> BatchCheckResult:
    return BatchCheckResult(
        results=_results(),
        summary=BatchCheckSummary(
            total=4,
            ok=1,
            no_frames=1,
            probe_failed=1,
            error=1,
            black_detected=1,
            freeze_detected=1,
        ),
    )


def _source_rows() -> list[dict[str, str]]:
    return [
        {
            "camera_id": "CAM-ERROR",
            "camera_name": "Dummy Error",
            "site_code": "SITE-C",
            "site_name": "Dummy Site C",
        },
        {
            "camera_id": "CAM-PROBE",
            "camera_name": "Dummy Probe",
            "site_code": "SITE-B",
            "site_name": "Dummy Site B",
        },
        {
            "camera_id": "CAM-NO-FRAMES",
            "camera_name": "Dummy No Frames",
            "site_code": "SITE-A",
            "site_name": "Dummy Site A",
        },
        {
            "camera_id": "CAM-OK",
            "camera_name": "Dummy OK",
            "site_code": "SITE-A",
            "site_name": "Dummy Site A",
        },
    ]


def test_build_detailed_rows_uses_source_rows_and_omits_rtsp_url() -> None:
    rows = reports.build_detailed_rows(_batch_result(), source_rows=_source_rows())

    assert list(rows[0]) == list(reports.DETAILED_FIELDNAMES)
    assert rows[0] == {
        "camera_id": "CAM-OK",
        "camera_name": "Dummy OK",
        "status": "OK",
        "probe_ok": 1,
        "frames_ok": 1,
        "black_detected": 1,
        "freeze_detected": 0,
        "error": "",
    }
    assert "rtsp_url_masked" not in rows[0]


def test_build_summary_rows_from_batch_result() -> None:
    assert reports.build_summary_rows(_batch_result()) == [
        {
            "total": 4,
            "ok": 1,
            "no_frames": 1,
            "probe_failed": 1,
            "error": 1,
            "black_detected": 1,
            "freeze_detected": 1,
        }
    ]


def test_build_summary_by_site_rows_matches_by_camera_id_not_order() -> None:
    rows = reports.build_summary_by_site_rows(
        _batch_result(),
        source_rows=_source_rows(),
    )

    assert rows == [
        {
            "site_code": "SITE-A",
            "site_name": "Dummy Site A",
            "total": 2,
            "ok": 1,
            "no_frames": 1,
            "probe_failed": 0,
            "error": 0,
            "black_detected": 1,
            "freeze_detected": 0,
        },
        {
            "site_code": "SITE-B",
            "site_name": "Dummy Site B",
            "total": 1,
            "ok": 0,
            "no_frames": 0,
            "probe_failed": 1,
            "error": 0,
            "black_detected": 0,
            "freeze_detected": 0,
        },
        {
            "site_code": "SITE-C",
            "site_name": "Dummy Site C",
            "total": 1,
            "ok": 0,
            "no_frames": 0,
            "probe_failed": 0,
            "error": 1,
            "black_detected": 0,
            "freeze_detected": 1,
        },
    ]


def test_build_summary_by_site_rows_supports_camera_name_as_source_id() -> None:
    rows = reports.build_summary_by_site_rows(
        [
            CameraCheckResult(
                camera_id="Dummy Camera",
                probe_ok=1,
                frames_ok=1,
                status="OK",
            )
        ],
        source_rows=[
            {
                "camera_name": "Dummy Camera",
                "site_code": "SITE-A",
                "site_name": "Dummy Site A",
            }
        ],
    )

    assert rows[0]["site_code"] == "SITE-A"
    assert rows[0]["ok"] == 1


def test_build_summary_by_site_rows_without_source_rows_returns_empty() -> None:
    assert reports.build_summary_by_site_rows(_batch_result()) == []


def test_write_csv_report(tmp_path: Path) -> None:
    rows = reports.build_detailed_rows(_batch_result(), source_rows=_source_rows())
    path = tmp_path / "detailed.csv"

    reports.write_csv_report(path, rows, fieldnames=reports.DETAILED_FIELDNAMES)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(reports.DETAILED_FIELDNAMES)
    assert "rtsp://" not in path.read_text(encoding="utf-8")


def test_build_report_payload_and_write_json_report(tmp_path: Path) -> None:
    payload = reports.build_report_payload(_batch_result(), source_rows=_source_rows())
    path = tmp_path / "report.json"

    reports.write_json_report(path, payload)

    assert payload["summary"]["total"] == 4
    assert payload["details"][0]["camera_name"] == "Dummy OK"
    assert json.loads(path.read_text(encoding="utf-8")) == payload


def test_build_report_payload_can_reuse_source_row_generator() -> None:
    payload = reports.build_report_payload(
        _batch_result(),
        source_rows=(row for row in _source_rows()),
    )

    assert payload["summary_by_site"][0]["site_code"] == "SITE-A"
    assert payload["details"][0]["camera_name"] == "Dummy OK"
