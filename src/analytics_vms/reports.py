"""CSV and JSON report helpers for camera check results."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from analytics_vms.batch_check import BatchCheckResult, BatchCheckSummary
from analytics_vms.camera_check import CameraCheckResult


DETAILED_FIELDNAMES = (
    "camera_id",
    "camera_name",
    "status",
    "probe_ok",
    "frames_ok",
    "black_detected",
    "freeze_detected",
    "error",
)

SUMMARY_FIELDNAMES = (
    "total",
    "ok",
    "no_frames",
    "probe_failed",
    "error",
    "black_detected",
    "freeze_detected",
)

SUMMARY_BY_SITE_FIELDNAMES = (
    "site_code",
    "site_name",
    "total",
    "ok",
    "no_frames",
    "probe_failed",
    "error",
    "black_detected",
    "freeze_detected",
)


def build_detailed_rows(
    results: BatchCheckResult | Iterable[CameraCheckResult | Mapping[str, Any]],
    *,
    source_rows: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build detailed per-camera report rows."""
    source_by_camera_id = _source_rows_by_camera_id(source_rows)
    rows: list[dict[str, Any]] = []

    for result in _iter_results(results):
        camera_id = str(_result_value(result, "camera_id", ""))
        source_row = source_by_camera_id.get(camera_id, {})
        camera_name = _mapping_text(source_row, "camera_name") or camera_id
        rows.append(
            {
                "camera_id": camera_id,
                "camera_name": camera_name,
                "status": str(_result_value(result, "status", "")),
                "probe_ok": _result_int(result, "probe_ok"),
                "frames_ok": _result_int(result, "frames_ok"),
                "black_detected": _result_int(result, "black_detected"),
                "freeze_detected": _result_int(result, "freeze_detected"),
                "error": str(_result_value(result, "error", "")),
            }
        )

    return rows


def build_summary_row(
    summary_source: (
        BatchCheckResult
        | BatchCheckSummary
        | Iterable[CameraCheckResult | Mapping[str, Any]]
    ),
) -> dict[str, int]:
    """Build one global summary row."""
    summary = _summary_from_source(summary_source)
    return {
        "total": summary.total,
        "ok": summary.ok,
        "no_frames": summary.no_frames,
        "probe_failed": summary.probe_failed,
        "error": summary.error,
        "black_detected": summary.black_detected,
        "freeze_detected": summary.freeze_detected,
    }


def build_summary_rows(
    summary_source: (
        BatchCheckResult
        | BatchCheckSummary
        | Iterable[CameraCheckResult | Mapping[str, Any]]
    ),
) -> list[dict[str, int]]:
    """Build a single-row CSV-friendly global summary."""
    return [build_summary_row(summary_source)]


def build_summary_by_site_rows(
    results: BatchCheckResult | Iterable[CameraCheckResult | Mapping[str, Any]],
    *,
    source_rows: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build site summaries by matching results to source rows by camera id."""
    source_by_camera_id = _source_rows_by_camera_id(source_rows)
    if not source_by_camera_id:
        return []

    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for result in _iter_results(results):
        camera_id = str(_result_value(result, "camera_id", ""))
        source_row = source_by_camera_id.get(camera_id)
        if source_row is None:
            continue

        site_code = _mapping_text(source_row, "site_code")
        site_name = _mapping_text(source_row, "site_name")
        key = (site_code, site_name)
        if key not in groups:
            groups[key] = {
                "site_code": site_code,
                "site_name": site_name,
                "total": 0,
                "ok": 0,
                "no_frames": 0,
                "probe_failed": 0,
                "error": 0,
                "black_detected": 0,
                "freeze_detected": 0,
            }

        _add_result_counts(groups[key], result)

    return sorted(
        groups.values(),
        key=lambda row: (row["site_code"], row["site_name"]),
    )


def build_report_payload(
    batch_result: BatchCheckResult,
    *,
    source_rows: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal JSON-serializable report payload."""
    source_rows_tuple = None if source_rows is None else tuple(source_rows)
    return {
        "summary": build_summary_row(batch_result),
        "summary_by_site": build_summary_by_site_rows(
            batch_result,
            source_rows=source_rows_tuple,
        ),
        "details": build_detailed_rows(batch_result, source_rows=source_rows_tuple),
    }


def write_csv_report(
    path: str | Path,
    rows: Iterable[Mapping[str, Any]],
    *,
    fieldnames: Sequence[str] | None = None,
) -> None:
    """Write report rows to CSV."""
    rows_list = [dict(row) for row in rows]
    if fieldnames is None:
        if not rows_list:
            raise ValueError("fieldnames are required for empty CSV reports")
        fieldnames = tuple(rows_list[0].keys())

    with Path(path).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows_list)


def write_json_report(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Write a minimal JSON report payload."""
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    Path(path).write_text(f"{text}\n", encoding="utf-8")


def _iter_results(
    results: BatchCheckResult | Iterable[CameraCheckResult | Mapping[str, Any]],
) -> tuple[CameraCheckResult | Mapping[str, Any], ...]:
    if isinstance(results, BatchCheckResult):
        return results.results
    return tuple(results)


def _summary_from_source(
    summary_source: (
        BatchCheckResult
        | BatchCheckSummary
        | Iterable[CameraCheckResult | Mapping[str, Any]]
    ),
) -> BatchCheckSummary:
    if isinstance(summary_source, BatchCheckResult):
        return summary_source.summary
    if isinstance(summary_source, BatchCheckSummary):
        return summary_source

    summary_row = _build_summary_by_status(_iter_results(summary_source))
    return BatchCheckSummary(**summary_row)


def _build_summary_by_status(
    results: Iterable[CameraCheckResult | Mapping[str, Any]],
) -> dict[str, int]:
    """Build summary counts from result rows or CameraCheckResult objects."""
    row = {
        "total": 0,
        "ok": 0,
        "no_frames": 0,
        "probe_failed": 0,
        "error": 0,
        "black_detected": 0,
        "freeze_detected": 0,
    }

    for result in results:
        _add_result_counts(row, result)

    return row


def _add_result_counts(
    row: dict[str, Any],
    result: CameraCheckResult | Mapping[str, Any],
) -> None:
    row["total"] += 1
    status = str(_result_value(result, "status", ""))
    if status == "OK":
        row["ok"] += 1
    elif status == "NO_FRAMES":
        row["no_frames"] += 1
    elif status == "PROBE_FAILED":
        row["probe_failed"] += 1
    elif status == "ERROR":
        row["error"] += 1

    if _result_int(result, "black_detected") == 1:
        row["black_detected"] += 1
    if _result_int(result, "freeze_detected") == 1:
        row["freeze_detected"] += 1


def _source_rows_by_camera_id(
    source_rows: Iterable[Mapping[str, Any]] | None,
) -> dict[str, Mapping[str, Any]]:
    if source_rows is None:
        return {}

    rows_by_camera_id: dict[str, Mapping[str, Any]] = {}
    for row in source_rows:
        camera_id = _camera_id(row)
        if camera_id and camera_id not in rows_by_camera_id:
            rows_by_camera_id[camera_id] = row
    return rows_by_camera_id


def _camera_id(row: Mapping[str, Any]) -> str:
    for key in ("camera_id", "camera_name", "ip", "host", "site_code"):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _mapping_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key, "")
    if value is None:
        return ""
    return str(value)


def _result_value(
    result: CameraCheckResult | Mapping[str, Any],
    key: str,
    default: Any,
) -> Any:
    if isinstance(result, Mapping):
        return result.get(key, default)
    return getattr(result, key, default)


def _result_int(result: CameraCheckResult | Mapping[str, Any], key: str) -> int:
    value = _result_value(result, key, 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
