"""Inventory CSV loading, validation, and normalization."""

from __future__ import annotations

import csv
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = (
    "project_code",
    "municipality",
    "site_type",
    "site_code",
    "site_name",
    "camera_role",
    "camera_name",
    "brand",
    "ip",
    "rtsp_port",
    "rtsp_path",
    "transport",
)

OPTIONAL_COLUMNS = (
    "traffic_direction",
    "credential_id",
    "username",
    "password",
)

EXPECTED_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

VALID_SITE_TYPES = {"PMI", "ARC"}
VALID_TRANSPORTS = {"tcp", "udp"}
PMI_CAMERA_ROLES = {"PTZ", "FJ1", "FJ2", "FJ3", "LPR"}
ARC_CAMERA_ROLES = {"FIXED_1", "FIXED_2", "LPR_1", "LPR_2", "LPR_3", "LPR_4"}
ARC_TRAFFIC_DIRECTIONS = {"ENTRY", "EXIT"}


class InventoryValidationError(ValueError):
    """Raised when an inventory CSV does not match the expected contract."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


@dataclass(frozen=True)
class InventoryRow:
    """Normalized inventory row for one camera endpoint."""

    project_code: str
    municipality: str
    site_type: str
    site_code: str
    site_name: str
    traffic_direction: str
    camera_role: str
    camera_name: str
    brand: str
    ip: str
    rtsp_port: int
    rtsp_path: str
    transport: str
    credential_id: str = ""
    username: str = ""
    password: str = ""
    extra: dict[str, str] = field(default_factory=dict)
    row_number: int | None = None


def normalize_inventory_row(row: Mapping[str, Any]) -> dict[str, str]:
    """Trim column names and string values from a CSV row."""
    normalized: dict[str, str] = {}
    for key, value in row.items():
        column = "" if key is None else str(key).strip()
        normalized[column] = _normalize_value(value)
    return normalized


def load_inventory_csv(path: str | Path) -> list[InventoryRow]:
    """Load and validate an inventory CSV from disk."""
    csv_path = Path(path)
    errors: list[str] = []
    rows: list[InventoryRow] = []

    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.reader(csv_file)
            try:
                raw_header = next(reader)
            except StopIteration as exc:
                raise InventoryValidationError(["CSV de inventario vacio."]) from exc

            header = [_normalize_value(column) for column in raw_header]
            _validate_header(header, errors)

            if errors:
                raise InventoryValidationError(errors)

            for row_number, raw_values in enumerate(reader, start=2):
                if not raw_values or all(_normalize_value(value) == "" for value in raw_values):
                    continue

                if len(raw_values) > len(header):
                    errors.append(
                        f"Linea {row_number}: contiene mas valores que columnas declaradas."
                    )
                    continue

                padded_values = raw_values + [""] * (len(header) - len(raw_values))
                row = normalize_inventory_row(dict(zip(header, padded_values)))
                row_errors = _validate_row(row, row_number)
                if row_errors:
                    errors.extend(row_errors)
                    continue

                rows.append(_to_inventory_row(row, row_number))
    except OSError as exc:
        raise InventoryValidationError(
            [f"No se pudo leer el CSV de inventario: {exc.strerror or exc}."]
        ) from exc

    if errors:
        raise InventoryValidationError(errors)

    return rows


def _normalize_value(value: Any) -> str:
    """Convert empty CSV values to a consistent empty string."""
    if value is None:
        return ""
    return str(value).strip()


def _validate_header(header: list[str], errors: list[str]) -> None:
    """Validate required CSV header columns."""
    if not header:
        errors.append("CSV de inventario sin encabezado.")
        return

    blank_columns = [index + 1 for index, column in enumerate(header) if column == ""]
    if blank_columns:
        errors.append(f"Encabezado con columnas vacias en posiciones: {blank_columns}.")

    duplicate_columns = sorted(
        {column for column in header if column and header.count(column) > 1}
    )
    if duplicate_columns:
        errors.append(f"Columnas duplicadas: {', '.join(duplicate_columns)}.")

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in header]
    if missing_columns:
        errors.append(f"Faltan columnas obligatorias: {', '.join(missing_columns)}.")


def _validate_row(row: Mapping[str, str], row_number: int) -> list[str]:
    """Validate one normalized inventory row."""
    errors: list[str] = []

    missing_values = [column for column in REQUIRED_COLUMNS if row.get(column, "") == ""]
    if missing_values:
        errors.append(
            f"Linea {row_number}: campos obligatorios vacios: "
            f"{', '.join(missing_values)}."
        )

    site_type = row.get("site_type", "")
    camera_role = row.get("camera_role", "")
    traffic_direction = row.get("traffic_direction", "")
    transport = row.get("transport", "")
    rtsp_port = row.get("rtsp_port", "")

    if site_type and site_type not in VALID_SITE_TYPES:
        errors.append(
            f"Linea {row_number}: site_type debe ser PMI o ARC."
        )

    if site_type == "PMI":
        if camera_role and camera_role not in PMI_CAMERA_ROLES:
            errors.append(
                f"Linea {row_number}: camera_role no corresponde a site_type PMI."
            )
        if traffic_direction:
            errors.append(
                f"Linea {row_number}: traffic_direction debe estar vacio para PMI."
            )

    if site_type == "ARC":
        if camera_role and camera_role not in ARC_CAMERA_ROLES:
            errors.append(
                f"Linea {row_number}: camera_role no corresponde a site_type ARC."
            )
        if traffic_direction not in ARC_TRAFFIC_DIRECTIONS:
            errors.append(
                f"Linea {row_number}: traffic_direction debe ser ENTRY o EXIT para ARC."
            )

    if transport and transport not in VALID_TRANSPORTS:
        errors.append(f"Linea {row_number}: transport debe ser tcp o udp.")

    if rtsp_port:
        try:
            port = int(rtsp_port)
        except ValueError:
            errors.append(f"Linea {row_number}: rtsp_port debe ser un entero.")
        else:
            if port < 1 or port > 65535:
                errors.append(f"Linea {row_number}: rtsp_port fuera de rango.")

    return errors


def _to_inventory_row(row: Mapping[str, str], row_number: int) -> InventoryRow:
    """Build a typed inventory row from normalized strings."""
    extra = {
        column: value
        for column, value in row.items()
        if column not in EXPECTED_COLUMNS
    }
    return InventoryRow(
        project_code=row["project_code"],
        municipality=row["municipality"],
        site_type=row["site_type"],
        site_code=row["site_code"],
        site_name=row["site_name"],
        traffic_direction=row.get("traffic_direction", ""),
        camera_role=row["camera_role"],
        camera_name=row["camera_name"],
        brand=row["brand"],
        ip=row["ip"],
        rtsp_port=int(row["rtsp_port"]),
        rtsp_path=row["rtsp_path"],
        transport=row["transport"],
        credential_id=row.get("credential_id", ""),
        username=row.get("username", ""),
        password=row.get("password", ""),
        extra=extra,
        row_number=row_number,
    )
