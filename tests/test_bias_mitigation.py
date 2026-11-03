"""Unit tests for Epistemic and Operational Bias Mitigation Engines.

Tests:
1. ScaleElasticityEngine (Continuous power-law scaling, eliminates point-scale bias)
2. RegionalCostEngine (Multi-regional cost matrix, eliminates western baseline bias)
3. OperationalDeratingEngine (Commissioning ramp, batch scrap, FTO royalty drag)
4. PredictionLedger (Adversarial null counter-hypothesis auto-pairing)
5. FSTPBottomUpAdapter (Schema validation and serialization of hardened specifications)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from biointel.economics.scaling import ScaleElasticityEngine, ScaleElasticityProfile
from biointel.economics.regional import RegionalCostEngine, GeographicRegion
from biointel.economics.derating import OperationalDeratingEngine
from biointel.longitudinal.prediction_ledger import PredictionLedger
from biointel.longitudinal.fstp_adapter import FSTPBottomUpAdapter
from biointel.storage.database import Database


def test_scale_elasticity_power_law_dynamics():
    """Verify continuous power law scaling across pilot, demo, commercial, and world scale."""
    profile = ScaleElasticityEngine.build_scale_profile(
        technology_id="fast_petase_depolymerase",
        scale_unit="MT_per_year",
        reference_scale=50_000.0,
        unit_cost_ref=0.76,
        fixed_cost_fraction=0.55,
        scaling_exponent_alpha=0.65,
    )

    assert isinstance(profile, ScaleElasticityProfile)
    assert len(profile.curve_points) == 4

    pilot = profile.curve_points[0]
    demo = profile.curve_points[1]
    comm = profile.curve_points[2]
    world = profile.curve_points[3]

    assert pilot.scale_label == "PILOT"
    assert pilot.scale_value == 2500.0  # 0.05x
    assert comm.scale_label == "COMMERCIAL_REFERENCE"
    assert comm.scale_value == 50_000.0  # 1.0x
    assert world.scale_label == "WORLD_SCALE"
    assert world.scale_value == 150_000.0  # 3.0x

    # Monotonic unit cost decline with scale (economies of scale)
    assert pilot.unit_cost_usd > demo.unit_cost_usd > comm.unit_cost_usd > world.unit_cost_usd

    # CapEx contribution scales down while variable cost remains constant
    assert pilot.variable_cost_usd == comm.variable_cost_usd == world.variable_cost_usd
    assert pilot.capex_contribution_usd > comm.capex_contribution_usd > world.capex_contribution_usd

    # Arbitrary scale evaluation
    cost_at_10k = profile.evaluate_cost_at_scale(10_000.0)
    assert demo.unit_cost_usd <= cost_at_10k <= pilot.unit_cost_usd


def test_regional_cost_benchmark_matrix():
    """Verify multi-regional matrix differentiates US, Western Europe, and East Asia."""
    matrix = RegionalCostEngine.evaluate_regional_matrix(
        base_us_cost=0.76,
        power_intensity_kwh_per_unit=1.85,
        labor_hours_per_unit=0.002,
        feedstock_kg_per_unit=1.15,
        base_capex_per_unit=0.28,
    )

    assert "US_GULF_COAST" in matrix
    assert "WESTERN_EUROPE" in matrix
    assert "EAST_ASIA" in matrix

    us = matrix["US_GULF_COAST"]
    eu = matrix["WESTERN_EUROPE"]
    asia = matrix["EAST_ASIA"]

    # East Asia has lower labor, scrap, and CapEx installation costs
    assert asia.unit_cost_usd < us.unit_cost_usd
    assert asia.cost_delta_vs_us_pct < 0.0
    assert asia.commercial_viability_verdict == "HIGHLY_COMPETITIVE"

    # Western Europe has higher electricity tariffs and feedstocks
    assert eu.unit_cost_usd > us.unit_cost_usd
    assert eu.cost_delta_vs_us_pct > 0.0
    assert eu.commercial_viability_verdict == "COST_PREMIUM_BURDEN"


def test_operational_commissioning_and_fto_derating():
    """Verify commissioning ramp-up penalty, batch scrap, and FTO royalty drag."""
    # Year 1 (45% capacity, 8% scrap)
    y1 = OperationalDeratingEngine.evaluate_derated_costs(
        steady_state_unit_cost_usd=0.75,
        fixed_cost_fraction=0.50,
        fto_licensing_royalty_pct=8.0,
        reference_year=1,
    )

    # Year 3 (92% mature steady-state capacity, 3% scrap)
    y3 = OperationalDeratingEngine.evaluate_derated_costs(
        steady_state_unit_cost_usd=0.75,
        fixed_cost_fraction=0.50,
        fto_licensing_royalty_pct=8.0,
        reference_year=3,
    )

    assert y1.effective_capacity_factor_pct == 45.0
    assert y3.effective_capacity_factor_pct == 92.0

    # Fixed overhead multiplier is ~2.04x in Year 1 vs 1.0x at mature state
    assert y1.fixed_overhead_inflation_multiplier > 2.0
    assert y3.fixed_overhead_inflation_multiplier == 1.0

    # Year 1 commercial clearing cost is substantially higher than steady-state cost
    assert y1.commercial_clearing_cost_usd > y3.commercial_clearing_cost_usd
    assert y3.commercial_clearing_cost_usd > y3.steady_state_cost_usd

    # Commercial clearing cost includes FTO patent royalty (+8%)
    assert y3.commercial_clearing_cost_usd >= y3.physical_cost_floor_usd * 1.079


def test_prediction_ledger_auto_pairs_adversarial_null():
    """Verify prediction ledger auto-registers adversarial counter-hypothesis if omitted."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_biointel.db"
        db = Database(str(db_path))
        ledger = PredictionLedger(db)

        # Issue contract without providing comparator_hypothesis
        contract = ledger.issue_contract(
            technology_id="fast_petase_depolymerase",
            horizon_years=5,
            target_date="2031-11-01",
            target_metric="cost_usd_per_kg_tpa",
            p10=0.65,
            p50=0.76,
            p90=0.95,
            falsification_criteria="Unit production cost exceeds $1.15/kg at 50,000 MT/year.",
            unit="USD_per_kg",
            created_at_override="2026-11-02",
        )

        assert contract.comparator_hypothesis is not None
        assert "Adversarial Null" in contract.comparator_hypothesis
        assert "fails to breach commercial parity" in contract.comparator_hypothesis


def test_fstp_adapter_bias_hardened_spec_generation():
    """Verify FSTPBottomUpAdapter exports and validates specs with all 4 bias-mitigation fields."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_biointel.db"
        db = Database(str(db_path))
        adapter = FSTPBottomUpAdapter(db)

        # Test PETase specification
        pet_spec = adapter.generate_bottom_up_spec("fast_petase_depolymerase")
        assert "regional_cost_matrix_usd" in pet_spec
        assert "scale_elasticity" in pet_spec
        assert "operational_derating" in pet_spec
        assert "fto_royalty_drag_pct" in pet_spec
        assert pet_spec["fto_royalty_drag_pct"] == 5.0
        assert len(pet_spec["regional_cost_matrix_usd"]) == 3
        assert len(pet_spec["scale_elasticity"]["curve_points"]) == 4
        assert "year_1_commissioning" in pet_spec["operational_derating"]

        # Test mRNA/LNP specification
        mrna_spec = adapter.generate_bottom_up_spec("mrna_lnp_platform")
        assert "regional_cost_matrix_usd" in mrna_spec
        assert "scale_elasticity" in mrna_spec
        assert "operational_derating" in mrna_spec
        assert "fto_royalty_drag_pct" in mrna_spec
        assert mrna_spec["fto_royalty_drag_pct"] == 8.0
        assert len(mrna_spec["regional_cost_matrix_usd"]) == 3
        assert len(mrna_spec["scale_elasticity"]["curve_points"]) == 4
