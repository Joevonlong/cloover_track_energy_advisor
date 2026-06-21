"""Solar physics — re-exports from pipeline.py (HTW Berlin model).

pipeline.py is the authoritative source. This module exposes a clean,
typed public surface for layer1.py to import from.
"""

from __future__ import annotations

from app.domain.savings.solar_layer.pipeline import (
    ORIENTATION_FACTOR,
    _SC_TABLE as SC_TABLE,
    _sc_no_battery as _sc_raw,
    self_consumption_rate,
    simulate_energy,
    simulate_economics,
    build_context,
    DEFAULTS,
)


def sc_no_battery(R: float) -> float:
    """Self-consumption rate without battery for production/demand ratio R.

    HTW Berlin calibrated lookup table. Physics-locked.
    """
    return _sc_raw(R)


def resolve_panel(panel_id: str = "auto") -> dict:
    """Pick a panel from the catalog. 'auto' = cheapest €/Wp."""
    from app.domain.savings.solar_layer.pipeline import _resolve_panel, _resolve_config
    cfg = _resolve_config()
    if panel_id != "auto":
        cfg["selected_panel_id"] = panel_id
    return _resolve_panel(cfg)


PANEL_CATALOG: list[dict] = DEFAULTS["panel_catalog"]
SPECIFIC_YIELD_DEFAULT: float = DEFAULTS["specific_yield"]  # 950 kWh/kWp/yr

__all__ = [
    "ORIENTATION_FACTOR",
    "SC_TABLE",
    "PANEL_CATALOG",
    "SPECIFIC_YIELD_DEFAULT",
    "sc_no_battery",
    "resolve_panel",
    "self_consumption_rate",
    "simulate_energy",
    "simulate_economics",
    "build_context",
]
