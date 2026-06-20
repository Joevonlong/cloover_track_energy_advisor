"""Pure physics and policy constants used by the savings engine.

Monetary prices do not belong here. They are injected through PricingContext.
"""

from __future__ import annotations

AUTARKY_PV_ONLY: float = 0.30
AUTARKY_WITH_BATTERY: float = 0.60
BATTERY_CYCLES_PER_YEAR: int = 300
BATTERY_ROUND_TRIP_EFFICIENCY: float = 0.90

PETROL_CONSUMPTION_L_PER_100KM: float = 7.0
DIESEL_CONSUMPTION_L_PER_100KM: float = 6.0
EV_CONSUMPTION_KWH_PER_100KM: float = 18.0

DEFAULT_OLD_HEATPUMP_SCOP: float = 2.8
