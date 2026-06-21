"""Machine-checkable reference vectors for the F03 mathematical contract."""

from __future__ import annotations

import json
from math import isclose
from pathlib import Path
from typing import Any

import pytest

VECTOR_PATH = (
    Path(__file__).parents[5] / "specs/domain/fixtures/savings-engine-vectors.json"
)


@pytest.fixture(scope="module")
def vectors() -> dict[str, Any]:
    return json.loads(VECTOR_PATH.read_text(encoding="utf-8"))


def _annuity(principal: float, annual_rate: float, term_months: int) -> float:
    if principal == 0:
        return 0.0
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return principal / term_months
    growth = (1 + monthly_rate) ** term_months
    return principal * monthly_rate * growth / (growth - 1)


def test_worked_base_vector(vectors: dict[str, Any]) -> None:
    pricing = vectors["pricing_context"]
    physics = vectors["physics"]
    vector = vectors["V_WORKED_BASE"]
    inputs = vector["input"]
    expected = vector["expected"]

    assert (
        inputs["electricity_eur_month"]
        + inputs["heating_eur_month"]
        + inputs["mobility_eur_month"]
        == expected["current_monthly_spend_eur"]
    )
    assert isclose(
        inputs["electricity_eur_month"] * 12 / pricing["retail_price_eur_kwh"],
        expected["annual_consumption_kwh"],
    )
    heat_demand = (
        inputs["heating_eur_month"]
        * 12
        / pricing["oil_per_litre_eur"]
        * physics["oil_kwh_per_litre"]
        * physics["oil_boiler_efficiency"]
    )
    assert isclose(heat_demand, expected["heat_demand_kwh"])
    assert isclose(
        heat_demand / physics["new_heatpump_scop"],
        expected["heatpump_electricity_kwh"],
    )
    assert inputs["km_year"] * physics["ev_kwh_per_100km"] / 100 == expected[
        "ev_kwh_year"
    ]
    assert inputs["pv_kwp"] * physics["specific_yield_kwh_per_kwp"] == expected[
        "pv_yield_kwh"
    ]


def test_battery_sub_derivation(vectors: dict[str, Any]) -> None:
    pricing = vectors["pricing_context"]
    physics = vectors["physics"]
    vector = vectors["V_BATTERY_8KWH"]
    inputs = vector["input"]
    expected = vector["expected"]

    extra_kwh = (
        physics["autarky_with_battery"] - physics["autarky_pv_only"]
    ) * inputs["base_load_kwh_year"]
    extra_value = extra_kwh * pricing["retail_price_eur_kwh"]
    lost_feedin = extra_kwh * pricing["feedin_price_eur_kwh"]
    arbitrage = (
        inputs["battery_kwh"]
        * physics["battery_cycles_year"]
        * physics["battery_round_trip"]
        * pricing["dynamic_spread_eur_kwh"]
    )
    gross_year = extra_value - lost_feedin + arbitrage
    installment = _annuity(
        inputs["capex_after_subsidy_eur"],
        pricing["financing_apr"],
        pricing["financing_term_months"],
    )

    assert isclose(extra_kwh, expected["extra_self_consumption_kwh"])
    assert extra_value == pytest.approx(expected["extra_self_value_eur_year"], abs=0.001)
    assert lost_feedin == pytest.approx(expected["lost_feedin_eur_year"], abs=0.001)
    assert arbitrage == pytest.approx(expected["arbitrage_eur_year"], abs=0.001)
    assert gross_year == pytest.approx(expected["gross_eur_year"], abs=0.001)
    assert gross_year / 12 == pytest.approx(expected["gross_eur_month"], abs=0.001)
    assert abs(gross_year / 12 - installment) <= expected["net_tolerance_eur_month"]


def test_financing_vector(vectors: dict[str, Any]) -> None:
    pricing = vectors["pricing_context"]

    for case in vectors["V_FINANCING_180M_5PCT"]:
        installment = _annuity(
            case["principal_eur"],
            pricing["financing_apr"],
            pricing["financing_term_months"],
        )
        assert installment == pytest.approx(
            case["expected_installment_eur_month"], abs=1.0
        )


def test_ladder_structure_and_exact_marginal_sum(vectors: dict[str, Any]) -> None:
    vector = vectors["V_WORKED_LADDER"]
    steps = vector["steps"]
    deltas = [step["target_delta_net_eur_month"] for step in steps]

    assert deltas[0] < 0
    assert abs(deltas[1]) <= 1
    assert deltas[2] > 0
    assert deltas[3] == max(deltas)
    assert sum(deltas) == vector["target_monthly_saving_eur"]
    assert steps[-1]["target_cumulative_net_eur_month"] == sum(deltas)
    assert (
        steps[-1]["target_after_payoff_eur_month"]
        > steps[-1]["target_cumulative_net_eur_month"]
    )


def test_owned_equipment_uses_only_incremental_delta(vectors: dict[str, Any]) -> None:
    vector = vectors["V_OWNED_EQUIPMENT"]
    inputs = vector["input"]
    expected = vector["expected"]

    added_pv = max(0.0, inputs["recommended_pv_kwp"] - inputs["existing_pv_kwp"])
    added_battery = max(
        0.0,
        inputs["recommended_battery_kwh"] - inputs["existing_battery_kwh"],
    )

    assert added_pv == expected["added_pv_kwp"]
    assert inputs["existing_pv_kwp"] + added_pv == expected["total_pv_kwp"]
    assert added_battery == expected["added_battery_kwh"]
    assert (
        inputs["existing_battery_kwh"] + added_battery
        == expected["total_battery_kwh"]
    )
