"""Report stubs for future CSV outputs."""

from collections.abc import Iterable, Mapping
from typing import Any


def build_detailed_rows(results: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return detailed report rows from already computed results."""
    return [dict(result) for result in results]


def write_csv_report(path: str, rows: Iterable[Mapping[str, Any]]) -> None:
    """Placeholder for future CSV report writing."""
    raise NotImplementedError("CSV report writing is not implemented in MVP-1A.")
