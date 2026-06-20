"""FastAPI dependency providers.

Owner: Zhou (backend)
Feature ID: F17 (api endpoints)

Placeholder dependencies the routes inject. Fill in as features land.
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings

__all__ = ["get_settings", "get_pricing_context", "get_db"]


def get_pricing_context() -> Any:
    """Resolve the PricingContext for a request.

    TODO F12: build via adapters.resolver.Resolver from price_catalog.
    """
    raise NotImplementedError("TODO F12: pricing context dependency")


def get_db() -> Any:
    """Yield a Supabase client / db handle.

    TODO F04: back with adapters.supabase.get_supabase_client().
    """
    raise NotImplementedError("TODO F04: db dependency")
