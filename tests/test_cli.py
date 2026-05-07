"""CLI smoke tests."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from analytics_vms.batch_check import BatchCheckResult, BatchCheckSummary
from analytics_vms.camera_check import CameraCheckResult
from analytics_vms.cli import app
from analytics_vms.inventory import InventoryValidationError

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Analytics VMS" in result.output
    assert "check-cameras" in result.output


def test_cli_without_args_shows_help() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "analytics-vms 0.1.0" in result.output


def test_cli_check_inventory_with_dummy_csv() -> None:
    result = runner.invoke(
        app,
        ["check-inventory", str(REPO_ROOT / "examples" / "vms_input_dummy_repo.csv")],
    )

    assert result.exit_code == 0
    assert "Inventario valido: 181 filas." in result.output


def test_cli_check_inventory_fails_with_invalid_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "invalid_inventory.csv"
    csv_path.write_text(
        "project_code,municipality,site_type\n"
        "DEMO01,Sample Municipality,PMI\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check-inventory", str(csv_path)])

    assert result.exit_code == 1
    assert "Inventario invalido" in result.output
    assert "Faltan columnas obligatorias" in result.output


def test_cli_check_cameras_generates_reports_and_passes_options(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    inventory_path = tmp_path / "inventory.csv"
    out_dir = tmp_path / "reports"
    inventory_path.write_text("dummy\n", encoding="utf-8")
    source_rows = _source_rows()
    calls: dict[str, Any] = {}

    def fake_load_inventory_csv(path: Path) -> list[dict[str, Any]]:
        calls["inventory_path"] = path
        return source_rows

    def fake_check_camera_batch(
        rows: list[dict[str, Any]],
        **kwargs: Any,
    ) -> BatchCheckResult:
        calls["rows"] = rows
        calls["kwargs"] = kwargs
        return _batch_result_with_non_ok_statuses()

    monkeypatch.setattr(
        "analytics_vms.cli.load_inventory_csv",
        fake_load_inventory_csv,
    )
    monkeypatch.setattr(
        "analytics_vms.cli.check_camera_batch",
        fake_check_camera_batch,
    )

    result = runner.invoke(
        app,
        [
            "check-cameras",
            str(inventory_path),
            "--out-dir",
            str(out_dir),
            "--probe-timeout-seconds",
            "3",
            "--frame-timeout-seconds",
            "4",
            "--min-frames",
            "2",
            "--no-visual-diagnostics",
            "--visual-timeout-seconds",
            "5",
            "--visual-sample-seconds",
            "6",
            "--print-details",
        ],
    )

    assert result.exit_code == 0
    assert calls["inventory_path"] == inventory_path
    assert calls["rows"] == source_rows
    assert calls["kwargs"] == {
        "probe_timeout_seconds": 3.0,
        "frame_timeout_seconds": 4.0,
        "min_frames": 2,
        "enable_visual_diagnostics": False,
        "visual_timeout_seconds": 5.0,
        "visual_sample_seconds": 6.0,
    }
    assert "total: 4" in result.output
    assert "ok: 1" in result.output
    assert "no_frames: 1" in result.output
    assert "probe_failed: 1" in result.output
    assert "error: 1" in result.output
    assert "black_detected: 1" in result.output
    assert "freeze_detected: 1" in result.output

    expected_paths = {
        out_dir / "detailed.csv",
        out_dir / "summary.csv",
        out_dir / "summary_by_site.csv",
        out_dir / "report.json",
    }
    assert expected_paths == {path for path in out_dir.iterdir()}
    for path in expected_paths:
        assert str(path) in result.output

    detail_rows = list(
        csv.DictReader((out_dir / "detailed.csv").read_text(encoding="utf-8").splitlines())
    )
    assert detail_rows[0]["project_code"] == "DEMO01"
    assert detail_rows[0]["municipality"] == "Sample Municipality"
    assert detail_rows[0]["site_code"] == "SITE001"
    assert detail_rows[0]["site_name"] == "Dummy Site"
    assert detail_rows[0]["ip"] == "192.0.2.10"
    assert detail_rows[0]["rtsp_path"] == "/Streaming/Channels/101"
    assert "username" not in detail_rows[0]
    assert "password" not in detail_rows[0]

    report_text = (out_dir / "report.json").read_text(encoding="utf-8")
    payload = json.loads(report_text)
    assert payload["summary"]["total"] == 4
    assert payload["details"][0]["camera_role"] == "PTZ"
    assert "dummy-user" not in (out_dir / "detailed.csv").read_text(encoding="utf-8")
    assert "dummy-pass" not in report_text
    assert "dummy-user" not in result.output
    assert "dummy-pass" not in result.output
    assert "project_code" in result.output
    assert "SITE001" in result.output


def test_cli_check_cameras_invalid_inventory_exits_1(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    inventory_path = tmp_path / "inventory.csv"
    out_dir = tmp_path / "reports"
    inventory_path.write_text("dummy\n", encoding="utf-8")

    def fake_load_inventory_csv(_path: Path) -> list[dict[str, Any]]:
        raise InventoryValidationError(["CSV invalido de prueba."])

    monkeypatch.setattr(
        "analytics_vms.cli.load_inventory_csv",
        fake_load_inventory_csv,
    )

    result = runner.invoke(
        app,
        [
            "check-cameras",
            str(inventory_path),
            "--out-dir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 1
    assert "Inventario invalido" in result.output
    assert "CSV invalido de prueba." in result.output
    assert not out_dir.exists()


def _source_rows() -> list[dict[str, Any]]:
    return [
        {
            "project_code": "DEMO01",
            "municipality": "Sample Municipality",
            "site_type": "PMI",
            "site_code": "SITE001",
            "site_name": "Dummy Site",
            "traffic_direction": "",
            "camera_role": "PTZ",
            "camera_name": "CAM-OK",
            "brand": "unknown",
            "ip": "192.0.2.10",
            "rtsp_port": "554",
            "rtsp_path": "/Streaming/Channels/101",
            "transport": "tcp",
            "credential_id": "dummy-credential",
            "username": "dummy-user",
            "password": "dummy-pass",
        },
        {
            "project_code": "DEMO01",
            "municipality": "Sample Municipality",
            "site_type": "PMI",
            "site_code": "SITE001",
            "site_name": "Dummy Site",
            "traffic_direction": "",
            "camera_role": "FJ1",
            "camera_name": "CAM-NO-FRAMES",
            "brand": "unknown",
            "ip": "192.0.2.11",
            "rtsp_port": "554",
            "rtsp_path": "/Streaming/Channels/101",
            "transport": "tcp",
        },
        {
            "project_code": "DEMO01",
            "municipality": "Sample Municipality",
            "site_type": "PMI",
            "site_code": "SITE002",
            "site_name": "Dummy Site 2",
            "traffic_direction": "",
            "camera_role": "PTZ",
            "camera_name": "CAM-PROBE",
            "brand": "unknown",
            "ip": "192.0.2.12",
            "rtsp_port": "554",
            "rtsp_path": "/Streaming/Channels/101",
            "transport": "tcp",
        },
        {
            "project_code": "DEMO01",
            "municipality": "Sample Municipality",
            "site_type": "PMI",
            "site_code": "SITE003",
            "site_name": "Dummy Site 3",
            "traffic_direction": "",
            "camera_role": "PTZ",
            "camera_name": "CAM-ERROR",
            "brand": "unknown",
            "ip": "192.0.2.13",
            "rtsp_port": "554",
            "rtsp_path": "/Streaming/Channels/101",
            "transport": "tcp",
        },
    ]


def _batch_result_with_non_ok_statuses() -> BatchCheckResult:
    return BatchCheckResult(
        results=(
            CameraCheckResult(
                camera_id="CAM-OK",
                probe_ok=1,
                frames_ok=1,
                black_detected=1,
                status="OK",
            ),
            CameraCheckResult(
                camera_id="CAM-NO-FRAMES",
                probe_ok=1,
                frames_ok=0,
                status="NO_FRAMES",
                error="no frames decoded",
            ),
            CameraCheckResult(
                camera_id="CAM-PROBE",
                status="PROBE_FAILED",
                error="probe failed",
            ),
            CameraCheckResult(
                camera_id="CAM-ERROR",
                freeze_detected=1,
                status="ERROR",
                error=(
                    "failed rtsp://dummy-user:dummy-pass@192.0.2.13:554/stream "
                    "with dummy-credential"
                ),
            ),
        ),
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
