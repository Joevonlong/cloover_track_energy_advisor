"""Physics / policy constants (placeholders).

Owner: Lukas (engine)
Feature ID: F03 (domain spec)

NOTE: NO product PRICES here. Product prices come from the price_catalog
via PricingContext (master plan §12). Only physics/policy constants live here.

TODO F03: replace placeholder values with spec-frozen numbers.
"""

from __future__ import annotations

# EUR paid per kWh fed back into the grid (feed-in tariff). TODO F03.
FEEDIN_EUR_PER_KWH: float = 0.0

# Share of demand covered by PV alone, no battery (0..1). TODO F03.
AUTARKY_PV_ONLY: float = 0.0
