"""Health check route.

Owner: Zhou (backend)
Feature ID: F01 (monorepo scaffold)
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — proves the app booted."""
    return {"status": "ok", "service": "heimwende-api"}
