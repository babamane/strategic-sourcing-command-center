"""Phase 1B true-up service stub."""

from __future__ import annotations

from typing import Optional


def compute_snapshot(
    vendor: Optional[str] = None,
    version: Optional[int] = None,
) -> list[dict]:
    """Phase 1C placeholder."""

    raise NotImplementedError("trueup_service.compute_snapshot is implemented in Phase 1C")


def get_latest_snapshot(vendor: Optional[str] = None) -> list[dict]:
    """Phase 1C placeholder."""

    raise NotImplementedError("trueup_service.get_latest_snapshot is implemented in Phase 1C")


def get_snapshot_history(vendor: Optional[str] = None) -> list[dict]:
    """Phase 1C placeholder."""

    raise NotImplementedError("trueup_service.get_snapshot_history is implemented in Phase 1C")

