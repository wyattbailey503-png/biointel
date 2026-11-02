"""Tests for Precision Fermentation Techno-Economic Calculations."""

from __future__ import annotations

from biointel.economics.fermentation import (
    FermentationInputs,
    FermentationOutputs,
    TechnoEconomicFermentationModel,
)


def test_techno_economic_mass_balance_and_cost_stack() -> None:
    inputs = FermentationInputs(
        titer_g_per_l=45.0,
        duration_hours=120.0,
        turnaround_hours=16.0,
        working_volume_liters=50000.0,
        recovery_efficiency=0.85,
        feedstock_price_usd_per_kg=0.35,
        yield_product_per_substrate=0.38,
        utilities_cost_usd_per_batch=4500.0,
        dsp_consumables_usd_per_kg=2.80,
        annual_labor_overhead_usd=1200000.0,
        annual_capex_depreciation_usd=850000.0,
        operating_hours_per_year=7920.0,
    )

    outputs = TechnoEconomicFermentationModel.calculate(inputs)

    # 50,000 L * 45 g/L = 2,250 kg raw * 0.85 recovery = 1,912.5 kg recovered
    assert abs(outputs.product_mass_per_batch_kg - 1912.5) < 0.1
    # Cycle time = 120 + 16 = 136 h
    assert outputs.batch_cycle_time_hours == 136.0
    # Annual volume > 100,000 kg (> 100 MT)
    assert outputs.annual_production_volume_mt > 100.0

    # Total cost must equal sum of individual stack components
    computed_sum = (
        outputs.feedstock_cost_per_kg
        + outputs.utilities_cost_per_kg
        + outputs.dsp_cost_per_kg
        + outputs.labor_overhead_cost_per_kg
        + outputs.capex_depreciation_per_kg
    )
    assert abs(outputs.total_cost_per_kg - computed_sum) < 0.05
    assert outputs.break_even_price_20pct_margin > outputs.total_cost_per_kg


def test_sensitivity_analysis_dimensions() -> None:
    inputs = FermentationInputs()
    titers = [20.0, 40.0, 60.0]
    prices = [0.30, 0.50]
    sens = TechnoEconomicFermentationModel.sensitivity_analysis(inputs, titers=titers, feedstock_prices=prices)

    assert sens["titers_evaluated"] == titers
    assert sens["feedstock_prices_evaluated"] == prices
    assert len(sens["sensitivity_matrix"]) == 3

    # Cost at 60 g/L must be lower than at 20 g/L
    cost_20 = sens["sensitivity_matrix"][0]["cost_feedstock_0.30"]
    cost_60 = sens["sensitivity_matrix"][2]["cost_feedstock_0.30"]
    assert cost_60 < cost_20


def test_dynamic_utilities_scaling_with_cell_density_and_our() -> None:
    """Verifies that dynamic utility calculations scale with cell density and respiration heat."""
    # Low titer / low cell density
    inputs_low = FermentationInputs(
        titer_g_per_l=10.0,
        use_dynamic_utilities=True,
    )
    outputs_low = TechnoEconomicFermentationModel.calculate(inputs_low)

    # High titer / high cell density (demands higher OUR, more aeration, more cooling)
    inputs_high = FermentationInputs(
        titer_g_per_l=80.0,
        use_dynamic_utilities=True,
    )
    outputs_high = TechnoEconomicFermentationModel.calculate(inputs_high)

    # Total batch electricity/utilities should be higher for high titer run
    # (cost per kg might be lower due to mass dilution, but total batch utility cost is greater)
    total_batch_utilities_low = outputs_low.utilities_cost_per_kg * outputs_low.product_mass_per_batch_kg
    total_batch_utilities_high = outputs_high.utilities_cost_per_kg * outputs_high.product_mass_per_batch_kg

    assert total_batch_utilities_high > total_batch_utilities_low
    assert outputs_high.utilities_cost_per_kg > 0.0


def test_greenfield_vs_brownfield_capex_amortization() -> None:
    """Verifies that greenfield facility CAPEX properly reflects full installation depreciation."""
    inputs_brownfield = FermentationInputs(
        facility_type="brownfield",
        annual_capex_depreciation_usd=850000.0,
    )
    outputs_brownfield = TechnoEconomicFermentationModel.calculate(inputs_brownfield)

    inputs_greenfield = FermentationInputs(
        facility_type="greenfield",
        greenfield_capex_usd=35000000.0,
        greenfield_depreciation_years=15.0,  # ~$2.33M / yr
    )
    outputs_greenfield = TechnoEconomicFermentationModel.calculate(inputs_greenfield)

    assert outputs_greenfield.capex_depreciation_per_kg > outputs_brownfield.capex_depreciation_per_kg
    # Greenfield depreciation should be ~2.7x brownfield ($2.33M vs $0.85M)
    ratio = outputs_greenfield.capex_depreciation_per_kg / outputs_brownfield.capex_depreciation_per_kg
    assert 2.5 < ratio < 3.0
