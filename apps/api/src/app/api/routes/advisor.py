"""Advisor routes — FROZEN CONTRACT (F02).

Signatures and response_model are locked to the contract so FastAPI renders
the correct OpenAPI schema.  Bodies raise 501 until the pipeline is wired (F17).

Owner: Zhou (backend)
Feature ID: F02 (contract signatures) — F17 wires the engine — F24 adds fixture support.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.domain.models import (
    Household,
    Recommendation,
    SiteCheckRequest,
    SiteCheckResponse,
)

router = APIRouter(prefix="/api/v1/advisor", tags=["advisor"])


@router.post("/recommend", response_model=Recommendation)
def recommend(
    body: Household,
    fixture: str | None = None,
) -> Recommendation:
    """Run the savings ladder and return ranked upgrade paths.

    alternatives[] is the four-rung cumulative ladder (☀️→🔋→♨️→🚗).
    Per-layer "+€X/mo" = consecutive differences of alternatives[].monthly_saving_eur.
    Use ?fixture=<id> (e.g. "demo-detached") to return a frozen golden payload (F24).

    TODO F17: delegate to services.recommendation.RecommendationService.
    TODO F24: load fixture from apps/api/fixtures/<fixture>.json when ?fixture is set.
    """
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
    TODO F24: load fixture from apps/api/fixtures/<fixture>-site-check.json when ?fixture is set.
    """
    raise HTTPException(status_code=501, detail="Not implemented — F17")
