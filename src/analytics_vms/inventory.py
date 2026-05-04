"""Inventory helpers for camera input rows."""

from collections.abc import Mapping
from typing import Any


def normalize_inventory_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return a shallow normalized copy of an inventory row."""
    return dict(row)


def load_inventory_csv(path: str) -> list[dict[str, Any]]:
    """Placeholder for future CSV inventory loading."""
    raise NotImplementedError("Inventory loading is not implemented in MVP-1A.")
