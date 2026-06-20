"""Recommendation engine — orchestrates the pure savings ladder.

Owner: Lukas (engine)
Feature ID: F06 (solar) … F11 (financing)

Pure: takes a Household + PricingContext, returns a Recommendation.
No I/O — adapters/services supply the context.

F05 normalisation is implemented in savings.intake and is the first step this
orchestrator will call once the remaining layer features land.
"""

from __future__ import annotations

from app.domain.models import Household, PricingContext, Recommendation


def recommend(household: Household, ctx: PricingContext) -> Recommendation:
    """Compute the ranked recommendation. TODO F06-F11."""
    raise NotImplementedError("TODO F06-F11: engine.recommend")
