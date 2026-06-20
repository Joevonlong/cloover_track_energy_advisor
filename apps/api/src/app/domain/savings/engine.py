"""Recommendation engine — orchestrates the pure savings ladder.

Owner: Lukas (engine)
Feature ID: F05 (intake baseline) … F11 (financing)

Pure: takes a Household + PricingContext, returns a Recommendation.
No I/O — adapters/services supply the context.
"""

from __future__ import annotations

from app.domain.models import Household, PricingContext, Recommendation


def recommend(household: Household, ctx: PricingContext) -> Recommendation:
    """Compute the ranked recommendation. TODO F05-F11."""
    raise NotImplementedError("TODO F05-F11: engine.recommend")
