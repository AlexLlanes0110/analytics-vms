"""Inventory CSV loading and validation tests."""

from pathlib import Path

import pytest

from analytics_vms.inventory import (
    InventoryValidationError,
    load_inventory_csv,
    normalize_inventory_row,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_INVENTORY = REPO_ROOT / "examples" / "vms_input_dummy_repo.csv"

VALID_HEADER = (
    "project_code,municipality,site_type,site_code,site_name,traffic_direction,"
    "camera_role,camera_name,brand,ip,rtsp_port,rtsp_path,transport,"
    "credential_id,username,password\n"
)
VALID_ROW = (
    "DEMO01,Sample Municipality,PMI,SITE001,DEMO-PMI-SITE001,,PTZ,"
    "DEMO-PMI-SITE001-PTZ,unknown,192.0.2.10,554,/Streaming/Channels/101,"
    "tcp,cred_demo_site001,,\n"
)


def test_loads_dummy_inventory() -> None:
    rows = load_inventory_csv(EXAMPLE_INVENTORY)

    assert len(rows) == 181
    assert rows[0].project_code == "DEMO01"
    assert rows[0].rtsp_port == 554
    assert rows[0].row_number == 2


def test_loads_inventory_with_utf8_bom_header(tmp_path: Path) -> None:
    csv_path = tmp_path / "inventory_with_bom.csv"
    csv_path.write_text(VALID_HEADER + VALID_ROW, encoding="utf-8-sig")

    rows = load_inventory_csv(csv_path)

    assert len(rows) == 1
    assert rows[0].project_code == "DEMO01"


def test_normalizes_row_with_spaces() -> None:
    row = normalize_inventory_row(
        {
            " camera_name ": " DEMO-PMI-SITE001-PTZ ",
            " traffic_direction ": "   ",
            "rtsp_port": 554,
        }
    )

    assert row == {
        "camera_name": "DEMO-PMI-SITE001-PTZ",
        "traffic_direction": "",
        "rtsp_port": "554",
    }


def test_allows_extra_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "inventory_extra.csv"
    csv_path.write_text(
        VALID_HEADER.rstrip("\n") + ",notes\n" + VALID_ROW.rstrip("\n") + ",demo\n",
        encoding="utf-8",
    )

    rows = load_inventory_csv(csv_path)

    assert rows[0].extra == {"notes": "demo"}


def test_fails_when_required_column_is_missing(tmp_path: Path) -> None:
    csv_path = tmp_path / "missing_column.csv"
    csv_path.write_text(
        VALID_HEADER.replace("rtsp_port,", "") + VALID_ROW.replace("554,", ""),
        encoding="utf-8",
    )

    with pytest.raises(InventoryValidationError) as exc_info:
        load_inventory_csv(csv_path)

    assert "Faltan columnas obligatorias" in str(exc_info.value)
    assert "rtsp_port" in str(exc_info.value)


def test_fails_when_required_field_is_empty(tmp_path: Path) -> None:
    csv_path = tmp_path / "empty_required_field.csv"
    invalid_row = VALID_ROW.replace("PTZ,", ",", 1)
    csv_path.write_text(VALID_HEADER + invalid_row, encoding="utf-8")

    with pytest.raises(InventoryValidationError) as exc_info:
        load_inventory_csv(csv_path)

    message = str(exc_info.value)
    assert "Linea 2" in message
    assert "camera_role" in message
