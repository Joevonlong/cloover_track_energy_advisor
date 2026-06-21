"""F05 intake normalisation and baseline acceptance tests."""

from __future__ import annotations

import pytest

from app.domain.models import (
    Address,
    Assumption,
    CarType,
    FuelType,
    HeatingInput,
    Household,
    MobilityInput,
    PricingContext,
)
from app.domain.savings.intake import NormalisedHousehold, normalise_household


@pytest.fixture
def pricing() -> PricingContext:
    return PricingContext(
        plz="10115",
        retail_price_eur_kwh=0.37,
        feedin_price_eur_kwh=0.0778,
        grid_fee_eur_kwh=0.0,
        dynamic_spread_eur_kwh=0.12,
        pv_per_kwp_eur=1450.0,
        battery_per_kwh_eur=700.0,
        heatpump_fixed_eur=22000.0,
        wallbox_fixed_eur=1200.0,
        oil_per_litre_eur=1.10,
        gas_per_kwh_eur=0.115,
        petrol_per_litre_eur=1.85,
        diesel_per_litre_eur=1.75,
        public_charge_per_kwh_eur=0.45,
        home_charge_price_eur_kwh=0.20,
        financing_apr=0.05,
        financing_term_months=180,
    )


def household(
    *,
    mobility: MobilityInput,
    existing_pv_kwp: float = 0,
    existing_heatpump_year: int | None = None,
    existing_heatpump_power_kw: float | None = None,
    existing_heatpump_scop: float | None = None,
) -> Household:
    return Household(
        address=Address(street="Invalidenstraße", house_no="116", city="Berlin"),
        plz="10115",
        floor_area_m2=140,
        building_year=1985,
        occupants=3,
        electricity_eur_month=95,
        heating=HeatingInput(fuel=FuelType.OIL, eur_month=180),
        mobility=mobility,
        existing_pv_kwp=existing_pv_kwp,
        existing_heatpump_year=existing_heatpump_year,
        existing_heatpump_power_kw=existing_heatpump_power_kw,
        existing_heatpump_scop=existing_heatpump_scop,
    )


def assumption_map(result: NormalisedHousehold) -> dict[str, Assumption]:
    return {assumption.field: assumption for assumption in result.assumptions}


def test_km_direct_is_canonical_and_price_independent(pricing: PricingContext) -> None:
    source = household(mobility=MobilityInput(kind=CarType.PETROL, km_month=1233))
    expensive_fuel = pricing.model_copy(
        update={"petrol_per_litre_eur": pricing.petrol_per_litre_eur * 2}
    )

    first = normalise_household(source, pricing)
    second = normalise_household(source, expensive_fuel)

    assert first.km_year == 14796
    assert second.km_year == 14796


def test_petrol_euro_to_km_and_worked_baseline(pricing: PricingContext) -> None:
    result = normalise_household(
        household(mobility=MobilityInput(kind=CarType.PETROL, eur_month=160)),
        pricing,
    )

    assert result.mobility_fuel_litres_year == pytest.approx(1037.84, rel=0.01)
    assert result.km_year == pytest.approx(14826.25, rel=0.01)
    assert result.annual_consumption_kwh == pytest.approx(3081.08, abs=1)
    assert result.current_monthly_spend_eur == 435.0


def test_ev_euro_to_km(pricing: PricingContext) -> None:
    result = normalise_household(
        household(mobility=MobilityInput(kind=CarType.EV, eur_month=100)),
        pricing,
    )

    assert result.mobility_electricity_kwh_year == pytest.approx(2666.67, rel=0.01)
    assert result.km_year == pytest.approx(14814.81, rel=0.01)


def test_diesel_euro_to_km(pricing: PricingContext) -> None:
    result = normalise_household(
        household(mobility=MobilityInput(kind=CarType.DIESEL, eur_month=140)),
        pricing,
    )

    assert result.mobility_fuel_litres_year == pytest.approx(960.0)
    assert result.km_year == pytest.approx(16000.0)


def test_direct_ev_mileage_reconstructs_current_charging_spend(
    pricing: PricingContext,
) -> None:
    source = household(mobility=MobilityInput(kind=CarType.EV, km_month=1000))
    result = normalise_household(source, pricing)

    assert result.km_year == 12000
    assert result.mobility_electricity_kwh_year == 2160
    assert result.mobility_eur_month == pytest.approx(81.0)


def test_existing_pv_is_folded_without_changing_base_load(
    pricing: PricingContext,
) -> None:
    without_pv = normalise_household(
        household(mobility=MobilityInput(kind=CarType.NONE)),
        pricing,
    )
    with_pv = normalise_household(
        household(
            mobility=MobilityInput(kind=CarType.NONE),
            existing_pv_kwp=5,
        ),
        pricing,
    )

    assert with_pv.existing.pv_kwp == 5
    assert with_pv.existing.pv_incremental_only is True
    assert with_pv.annual_consumption_kwh == without_pv.annual_consumption_kwh


def test_none_mobility_and_default_assumptions(pricing: PricingContext) -> None:
    result = normalise_household(
        household(mobility=MobilityInput(kind=CarType.NONE)),
        pricing,
    )
    assumptions = assumption_map(result)

    assert result.km_year == 0
    assert result.mobility_eur_month == 0
    assert result.current_monthly_spend_eur == 275
    assert {
        "retail_price_eur_kwh",
        "petrol_per_litre_eur",
        "diesel_per_litre_eur",
        "public_charge_per_kwh_eur",
        "petrol_consumption_l_per_100km",
        "diesel_consumption_l_per_100km",
        "ev_consumption_kwh_per_100km",
        "annual_consumption_kwh",
        "existing_heatpump_power_kw",
        "existing_heatpump_scop",
    }.issubset(assumptions)
    assert assumptions["existing_heatpump_scop"].source != "user"


def test_user_heatpump_specs_override_defaults(pricing: PricingContext) -> None:
    result = normalise_household(
        household(
            mobility=MobilityInput(kind=CarType.NONE),
            existing_heatpump_year=2010,
            existing_heatpump_power_kw=8.0,
            existing_heatpump_scop=2.5,
        ),
        pricing,
    )
    assumptions = assumption_map(result)

    assert result.existing.heatpump_power_kw == 8.0
    assert result.existing.heatpump_scop == 2.5
    assert result.existing.heatpump_incremental_only is True
    assert assumptions["existing_heatpump_power_kw"].source == "user"
    assert assumptions["existing_heatpump_scop"].source == "user"


def test_contract_payload_decodes_with_and_without_new_hp_fields() -> None:
    base = {
        "address": {
            "street": "Invalidenstraße",
            "house_no": "116",
            "city": "Berlin",
        },
        "plz": "10115",
        "floor_area_m2": 140,
        "building_year": 1985,
        "occupants": 3,
        "electricity_eur_month": 95,
        "heating": {"fuel": "OIL", "eur_month": 180},
        "mobility": {"kind": "NONE"},
    }

    without_specs = Household.model_validate(base)
    with_specs = Household.model_validate(
        {
            **base,
            "existing_heatpump_power_kw": 8.0,
            "existing_heatpump_scop": 2.5,
        }
    )

    assert without_specs.existing_heatpump_power_kw is None
    assert without_specs.existing_heatpump_scop is None
    assert with_specs.existing_heatpump_power_kw == 8.0
    assert with_specs.existing_heatpump_scop == 2.5


def test_normalisation_is_deterministic(pricing: PricingContext) -> None:
    source = household(mobility=MobilityInput(kind=CarType.PETROL, eur_month=160))

    assert normalise_household(source, pricing) == normalise_household(
        source,
        pricing,
    )


def test_invalid_zero_price_is_rejected(pricing: PricingContext) -> None:
    invalid = pricing.model_copy(update={"retail_price_eur_kwh": 0})

    with pytest.raises(ValueError, match="retail_price_eur_kwh"):
        normalise_household(
            household(mobility=MobilityInput(kind=CarType.NONE)),
            invalid,
        )
