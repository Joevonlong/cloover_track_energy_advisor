"""solar_layer — Layer 1 Solar PV savings engine.

Physics source of truth: pipeline.py (ported from solar-pipeline/).
Public surface:          physics.py, economics.py, layer1.py (Phase 4).
Backtest data:           merged_input_output.csv (1,062 real DE installer projects).
"""

from app.domain.savings.solar_layer.physics import (
    ORIENTATION_FACTOR,
    PANEL_CATALOG,
    SPECIFIC_YIELD_DEFAULT,
    resolve_panel,
    sc_no_battery,
    self_consumption_rate,
    simulate_energy,
    simulate_economics,
)
from app.domain.savings.solar_layer.google_solar import (
    RoofData,
    GoogleSolarError,
    roof_from_address,
    geocode,
    parse_roof,
)
from app.domain.savings.solar_layer.economics import (
    DEFAULT_RETAIL_PRICE_EUR_KWH,
    FEED_IN_TARIFF_SMALL_EUR_KWH,
    FEED_IN_TARIFF_LARGE_EUR_KWH,
    blended_feed_in,
    pv_capex,
)

__all__ = [
    "RoofData",
    "GoogleSolarError",
    "roof_from_address",
    "geocode",
    "parse_roof",
    "ORIENTATION_FACTOR",
    "PANEL_CATALOG",
    "SPECIFIC_YIELD_DEFAULT",
    "resolve_panel",
    "sc_no_battery",
    "self_consumption_rate",
    "simulate_energy",
    "simulate_economics",
    "DEFAULT_RETAIL_PRICE_EUR_KWH",
    "FEED_IN_TARIFF_SMALL_EUR_KWH",
    "FEED_IN_TARIFF_LARGE_EUR_KWH",
    "blended_feed_in",
    "pv_capex",
]
