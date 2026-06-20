"""Dynamic tariff provider (price spread for battery arbitrage).

Owner: Zhou (backend)
Feature ID: F14 (dynamic tariff adapter)

SMARD / aWATTar live call TODO F14. Fallback: seeded €0.12/kWh spread.
"""

from __future__ import annotations

from typing import Any

# Deterministic offline fallback spread (EUR/kWh). TODO F14.
FALLBACK_SPREAD_EUR_PER_KWH: float = 0.12


class DynamicTariffProvider:
    """Peak/off-peak price spread for arbitrage modelling."""

    def spread(self, **kwargs: Any) -> float:
        """Daily price spread (EUR/kWh). Live call TODO F14.

        Falls back to FALLBACK_SPREAD_EUR_PER_KWH when offline.
        """
        raise NotImplementedError("TODO F14: DynamicTariffProvider.spread")
