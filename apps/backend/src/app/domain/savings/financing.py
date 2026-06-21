"""Financing (annuity loan) + subsidy application.

Owner: Lukas (engine)
Feature ID: F11 (financing + confidence)
"""

from __future__ import annotations

from typing import Any


def annuity(principal: float, annual_rate: float, years: int) -> float:
    """Monthly annuity installment for a loan. TODO F11."""
    raise NotImplementedError("TODO F11: annuity")


def apply_subsidies(capex: float, ctx: Any) -> float:
    """Reduce capex by applicable subsidies. TODO F11."""
    raise NotImplementedError("TODO F11: apply_subsidies")
