"""Advisor routes — FROZEN CONTRACT (F02).

Signatures and response_model are locked to the contract so FastAPI renders
the correct OpenAPI schema.  Bodies raise 501 until the pipeline is wired (F17).

Owner: Zhou (backend)
Feature ID: F02 (contract signatures) — F17 wires the engine — F24 adds fixture support.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.domain.models import (
    Household,
    Recommendation,
    SiteCheckRequest,
    SiteCheckResponse,
)

router = APIRouter(prefix="/api/v1/advisor", tags=["advisor"])

_FIXTURES_DIR = Path(__file__).parent.parent.parent.parent.parent / "fixtures"


def _load_fixture(name: str, model_cls: type) -> object:
    """Load a fixture JSON file and return it as the given Pydantic model."""
    if not re.fullmatch(r"[a-z0-9_-]+", name):
        raise HTTPException(status_code=400, detail="Invalid fixture name")
    path = _FIXTURES_DIR / f"{name}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Fixture '{name}' not found")
    data = json.loads(path.read_text())
    data.pop("_note", None)
    return model_cls(**data)


@router.post("/recommend", response_model=Recommendation)
def recommend(
    body: Household,
    fixture: str | None = None,
) -> Recommendation:
    """Run the savings ladder and return ranked upgrade paths.

    alternatives[] is the four-rung cumulative ladder (☀️→🔋→♨️→🚗).
    Use ?fixture=demo-detached to return the golden demo payload (F24).
    TODO F17: delegate to services.recommendation.RecommendationService.
    """
    if fixture:
        return _load_fixture(fixture, Recommendation)  # type: ignore[return-value]
    raise HTTPException(status_code=501, detail="Not implemented — F17")


@router.post("/site-check", response_model=SiteCheckResponse)
def site_check(
    body: SiteCheckRequest,
    fixture: str | None = None,
) -> SiteCheckResponse:
    """Validate an address / roof for feasibility and return energy context.

    Called before /recommend to display the green/amber feasibility panel (§4, §14.2).
    Use ?fixture=<id> to return a canned payload.

    TODO F17: delegate to adapters.site_check.SiteCheck (F15).
    TODO F24: load fixture from apps/backend/fixtures/<fixture>-site-check.json when ?fixture is set.
    """
    raise HTTPException(status_code=501, detail="Not implemented — F17")
