"""PVGIS irradiance provider.

Owner: Zhou (backend)
Feature ID: F13 (PVGIS adapter)

Live call TODO F13. Fallback: constant 980 kWh/kWp/yr when offline.
"""

from __future__ import annotations

from typing import Any

# Deterministic offline fallback (kWh per kWp per year). TODO F13.
FALLBACK_YIELD_KWH_PER_KWP: float = 980.0


class PVGISProvider:
    """Annual specific PV yield from PVGIS."""

    def annual_yield(self, lat: float, lon: float, **kwargs: Any) -> float:
        """Specific yield (kWh/kWp/yr). Live call TODO F13.

        Falls back to FALLBACK_YIELD_KWH_PER_KWP when the API is unavailable.
        """
        raise NotImplementedError("TODO F13: PVGISProvider.annual_yield")
