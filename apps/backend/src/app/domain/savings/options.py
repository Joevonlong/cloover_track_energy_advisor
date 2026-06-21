"""Configurator marginals (per-component deltas).

Owner: Lukas (engine)
Feature ID: F10 (optimiser / configurator)
"""

from __future__ import annotations

from typing import Any


def marginals(household: Any, ctx: Any) -> dict[str, Any]:
    """Marginal saving/cost of toggling each component. TODO F10."""
    raise NotImplementedError("TODO F10: configurator marginals")
