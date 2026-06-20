"""Resolver — maps a PLZ to context + PricingContext.

Owner: Zhou (backend)
Feature ID: F12 (resolver)

Reads the price_catalog (master plan §12) and assembles a PricingContext.
"""

from __future__ import annotations

from typing import Any

from app.domain.models import PricingContext


class Resolver:
    """Resolve location-specific pricing/context."""

    def resolve(self, plz: str) -> tuple[Any, PricingContext]:
        """Return (context, PricingContext) for a postcode. TODO F12."""
        raise NotImplementedError("TODO F12: Resolver.resolve")
