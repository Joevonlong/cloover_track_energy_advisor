"""Electricity savings (solar self-consumption + battery arbitrage).

Owner: Lukas (engine)
Feature ID: F06 (layer1 solar) / F07 (layer2 battery)
"""

from __future__ import annotations

from typing import Any


def layer1_solar(household: Any, ctx: Any) -> dict[str, Any]:
    """Savings from PV self-consumption. TODO F06."""
    raise NotImplementedError("TODO F06: layer1_solar")


def layer2_battery(household: Any, ctx: Any) -> dict[str, Any]:
    """Added savings from battery + tariff arbitrage. TODO F07."""
    raise NotImplementedError("TODO F07: layer2_battery")
