"""Configuration defaults for Analytics VMS."""

from dataclasses import dataclass


DEFAULT_BATCH_SIZE = 15
DEFAULT_MAX_WORKERS = 3


@dataclass(frozen=True)
class RuntimeConfig:
    """Runtime limits for a batch execution."""

    batch_size: int = DEFAULT_BATCH_SIZE
    max_workers: int = DEFAULT_MAX_WORKERS


def default_config() -> RuntimeConfig:
    """Return conservative defaults for MVP execution."""
    return RuntimeConfig()
