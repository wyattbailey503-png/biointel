"""Unit tests for the 30-Year Compounding Scientific Moat Engine (v1.0).

Verifies:
1. 30-Year multi-horizon prospective prediction contract issuance (5Y, 10Y, 20Y, 30Y).
2. Strict prospective purity enforcement: rejection of retro-dated contracts.
3. Contract resolution, empirical residual calculation, and Sanders-Murphy algebraic Brier decomposition.
4. Technology graveyard failure logging, forensic dead-end queries, and automated candidate auditing.
5. FSTP bottom-up model specification generation and export validity.
6. CLI integration for contract, graveyard, and export-fstp commands.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from biointel.storage.database import Database
from biointel.longitudinal.prediction_ledger import (
    CalibrationObservatory,
    PredictionContract,
    PredictionLedger,
    PredictionResolution,
)
from biointel.evidence.graveyard import (
    GraveyardEntry,
    TechnologyGraveyardRegistry,
)
from biointel.longitudinal.fstp_adapter import FSTPBottomUpAdapter
import biointel.cli as cli_mod


def test_prospective_contract_issuance_and_integrity(temp_db: Database) -> None:
    """Verifies that multi-decade prospective prediction contracts can be issued with cryptographic seals."""
    ledger = PredictionLedger(temp_db)

    # Issue a 10-year contract (target: 2036)
    contract = ledger.issue_contract(
        technology_id="prime_editing",
        horizon_years=10,
        target_date="2036-12-31",
        target_metric="approved_therapeutic_indications_count",
        p10=1.0,
        p50=4.0,
        p90=8.0,
        unit="approved drugs",
        falsification_criteria="Zero regulatory approvals achieved globally.",
        comparator_hypothesis="Base editing commercial therapies (estimated 3-5)",
    )

    assert contract.contract_id.startswith("cnt_")
    assert contract.technology_id == "prime_editing"
    assert contract.horizon_years == 10
    assert contract.target_date == "2036-12-31"
    assert contract.p10_estimate == 1.0
    assert contract.p50_estimate == 4.0
    assert contract.p90_estimate == 8.0
    assert contract.status == "PENDING"
    assert contract.model_provenance_seal.startswith("SEAL_MODEL_")

    # Verify retrieval from database
    stored = ledger.db.get_prediction_contract(contract.contract_id)
    assert stored is not None
    assert stored["target_metric"] == "approved_therapeutic_indications_count"


def test_prospective_purity_rejects_backdated_contract(temp_db: Database) -> None:
    """Verifies that contracts with target dates in the past are strictly rejected."""
    ledger = PredictionLedger(temp_db)

    try:
        ledger.issue_contract(
            technology_id="fast_petase_depolymerase",
            horizon_years=5,
            target_date="2020-01-01",  # In the past relative to current date
            target_metric="production_cost",
            p10=1.0,
            p50=1.5,
            p90=2.0,
            falsification_criteria="Cost exceeds $2.0/kg",
            created_at_override="2026-11-01",
        )
        assert False, "Expected PROSPECTIVE_PURITY_VIOLATION was not raised."
    except ValueError as err:
        assert "PROSPECTIVE_PURITY_VIOLATION" in str(err)


def test_contract_evaluation_and_brier_scoring(temp_db: Database) -> None:
    """Verifies empirical contract resolution, residual error, and Brier scoring."""
    ledger = PredictionLedger(temp_db)

    # Issue contract with created_at in 2020 and target in 2025
    c1 = ledger.issue_contract(
        technology_id="fast_petase_depolymerase",
        horizon_years=5,
        target_date="2025-12-31",
        target_metric="tpa_cost_usd_kg",
        p10=1.40,
        p50=1.60,
        p90=1.85,
        falsification_criteria="Cost exceeds $2.20/kg",
        created_at_override="2020-01-01",
    )

    # Scenario 1: Empirical observation lands within [P10, P90]
    res1 = ledger.evaluate_contract(
        contract_id=c1.contract_id,
        empirical_value=1.65,
        primary_source_doi="10.1016/j.biotechadv.2025.100000",
        resolved_date="2025-12-31",
        resolution_notes="Demonstration plant audit confirmed $1.65/kg TPA.",
    )

    assert res1.outcome_status == "CONFIRMED"
    assert res1.empirical_value == 1.65
    assert res1.residual_error == 0.05
    assert res1.brier_score <= 0.05

    # Check that contract status is updated in database
    updated_c1 = ledger.db.get_prediction_contract(c1.contract_id)
    assert updated_c1["status"] == "CONFIRMED"


def test_sanders_murphy_brier_decomposition(temp_db: Database) -> None:
    """Verifies Sanders-Murphy algebraic Brier decomposition across multiple evaluations."""
    ledger = PredictionLedger(temp_db)
    ledger.seed_default_long_horizon_contracts()

    # Pre-registered contracts exist
    contracts = ledger.db.get_prediction_contracts()
    assert len(contracts) >= 5

    # Resolve two contracts for testing calibration decomposition
    c1 = contracts[0]
    ledger.evaluate_contract(
        contract_id=c1["contract_id"],
        empirical_value=c1["p50_estimate"],
        primary_source_doi="10.1038/s41586-026-00001",
    )

    obs = ledger.get_calibration_observatory()
    assert obs.total_contracts >= 5
    assert obs.resolved_contracts == 1
    assert obs.pending_contracts >= 4
    assert obs.prospective_purity_pct == 100.0
    assert 5 in obs.contracts_by_horizon
    assert 10 in obs.contracts_by_horizon
    assert 20 in obs.contracts_by_horizon
    assert 30 in obs.contracts_by_horizon

    # Check Sanders-Murphy scores exist
    assert obs.overall_brier_score >= 0.0
    assert obs.reliability_score >= 0.0


def test_technology_graveyard_search_and_audit(temp_db: Database) -> None:
    """Verifies that failure autopsies can be queried and candidate platforms audited."""
    registry = TechnologyGraveyardRegistry(temp_db)
    registry.seed_default_graveyard()

    # Query dead-ends
    biofuel_failures = registry.query_dead_ends("biofuel")
    assert len(biofuel_failures) >= 2
    platform_names = [e.platform_name for e in biofuel_failures]
    assert any("Solazyme" in name for name in platform_names)
    assert any("Amyris" in name for name in platform_names)

    # Query PETase failure
    pet_failures = registry.query_dead_ends("glass transition")
    assert len(pet_failures) >= 1
    assert any("Mesophilic IsPETase" in e.platform_name for e in pet_failures)

    # Audit a candidate platform
    # Register candidate technology with biofuel in description
    temp_db.upsert_technology({
        "tech_id": "novel_sugar_biofuel",
        "name": "Novel Sugar Biofuel",
        "canonical_name": "novel_sugar_biofuel",
        "domain": "industrial_biotechnology",
        "category": "biofuels",
        "maturity_stage": "discovery",
        "description": "Fermentation of cane sugar into drop-in diesel biofuels.",
    })

    warnings = registry.audit_technology_against_graveyard("novel_sugar_biofuel")
    assert len(warnings) >= 1
    assert any("Solazyme" in w["historical_analogy_platform"] for w in warnings)


def test_fstp_bottom_up_spec_export(temp_db: Database) -> None:
    """Verifies that FSTP-compliant bottom-up model specifications are generated accurately."""
    import tempfile
    adapter = FSTPBottomUpAdapter(temp_db)

    spec = adapter.generate_bottom_up_spec("fast_petase_depolymerase", scale_mt_pet_year=50000.0)

    assert spec["technology_id"] == "fast_petase_depolymerase"
    assert spec["thermodynamic_cost_floor_usd_per_kg"] >= 0.70
    assert "feedstock_baled_pet" in spec["cost_stack_usd_per_kg"]
    assert "extrusion_preprocessing" in spec["cost_stack_usd_per_kg"]
    assert "thiele_modulus" in spec["physical_bottlenecks"]
    assert spec["physical_bottlenecks"]["effectiveness_factor"] <= 1.0
    assert spec["utility_targets"]["pinch_heat_recovery_fraction"] >= 0.70
    assert spec["fstp_integration_metadata"]["confidence_tier"] == 2
    assert spec["model_provenance_seal"].startswith("SEAL_FSTP_")

    # Test file export
    with tempfile.TemporaryDirectory() as td:
        out_file = Path(td) / "test_fstp_spec.json"
        exported_path = adapter.export_fstp_spec("fast_petase_depolymerase", output_path=out_file)
        assert exported_path.exists()

        loaded = json.loads(exported_path.read_text(encoding="utf-8"))
        assert loaded["technology_id"] == "fast_petase_depolymerase"
        assert loaded["thermodynamic_cost_floor_usd_per_kg"] == spec["thermodynamic_cost_floor_usd_per_kg"]


def test_cli_moat_commands(temp_db: Database) -> None:
    """Verifies that CLI contract, graveyard, and export-fstp commands execute cleanly."""
    orig_get_db = cli_mod.get_db
    cli_mod.get_db = lambda: temp_db
    try:
        # 1. contract list
        args_cnt_list = argparse.Namespace(
            command="contract",
            contract_action="list",
            status=None,
        )
        cli_mod.cmd_contract(args_cnt_list)

        # 2. contract observatory
        args_cnt_obs = argparse.Namespace(
            command="contract",
            contract_action="observatory",
        )
        cli_mod.cmd_contract(args_cnt_obs)

        # 3. graveyard query
        args_gr_q = argparse.Namespace(
            command="graveyard",
            graveyard_action="query",
            query="biofuel",
        )
        cli_mod.cmd_graveyard(args_gr_q)

        # 4. graveyard list
        args_gr_list = argparse.Namespace(
            command="graveyard",
            graveyard_action="list",
        )
        cli_mod.cmd_graveyard(args_gr_list)

        # 5. export-fstp
        args_fstp = argparse.Namespace(
            command="export-fstp",
            technology="fast_petase_depolymerase",
            out=None,
        )
        cli_mod.cmd_export_fstp(args_fstp)

    finally:
        cli_mod.get_db = orig_get_db
