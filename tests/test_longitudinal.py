"""Longitudinal Intelligence & Evidence Evolution Tests (Audited v2).

Verifies:
1. Strict as_of_date cutoff enforcement preventing hindsight leakage.
2. Evidence-specific public availability dates: PDB 5XJH excluded from 2016 snapshot (released Feb 14, 2018).
3. Reconciled extrusion cost stack disaggregating direct power from capital/labor/scrap.
4. Audited economic taxonomy distinguishing retrospective models from contemporaneous prices.
5. Distinguishing distinct enzyme lineages (mesophilic IsPETase vs thermophilic LCC cutinase).
6. Multi-dimensional commercial sensitivity boundaries.
7. Snapshot versioning and preservation of superseded v1 hashes.
8. Retention of well-designed negative studies as valuable scientific evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
from biointel.entities.models import ExperimentRecord, ResultRecord
from biointel.evidence.longitudinal import (
    LongitudinalReplayEngine,
    PETaseHistoricalTrajectory,
)
from biointel.evidence.quality import EvidenceQualityEvaluator
from biointel.economics.extrusion import ExtrusionTechnoEconomicModel
from biointel.storage.database import Database


def test_pdb_5xjh_excluded_from_2016_snapshot_until_public_release_2018(temp_db: Database) -> None:
    """Verifies that PDB 5XJH is strictly excluded from April 2016 (released Feb 14, 2018) and appears in 2018."""
    engine = LongitudinalReplayEngine(temp_db)
    engine.seed_historical_trajectory()

    # April 2016 snapshot: Yoshida et al. was published, but 5XJH was not yet deposited or released
    snap_2016 = engine.generate_snapshot("fast_petase_depolymerase", "2016-04-01", "Snapshot 2016")
    assert snap_2016.publications_count == 1
    assert "5XJH" not in snap_2016.structures
    assert len(snap_2016.structures) == 0, f"Expected zero available structures in April 2016, found {snap_2016.structures}"

    # Verify availability manifest marks 5XJH as WITHHELD_NOT_YET_RELEASED
    manifest_5xjh = next((item for item in snap_2016.evidence_availability_manifest if item["identifier"] == "5XJH"), None)
    assert manifest_5xjh is not None
    assert manifest_5xjh["status"] == "WITHHELD_NOT_YET_RELEASED"
    assert manifest_5xjh["public_release_date"] == "2018-02-14"

    # May 2018 snapshot: Both 5XJH (released 2018-02-14) and 6EQE (released 2018-04-25) must be present
    snap_2018 = engine.generate_snapshot("fast_petase_depolymerase", "2018-05-01", "Snapshot 2018")
    assert "5XJH" in snap_2018.structures
    assert "6EQE" in snap_2018.structures
    assert len(snap_2018.structures) == 2


def test_extrusion_cost_stack_dimensional_reconciliation() -> None:
    """Verifies that the $0.49/kg extrusion cost is reconciled with 0.45 kWh/kg electricity, capital, and labor."""
    # 1. Commercial 50,000 MT/year plant
    comm_stack = ExtrusionTechnoEconomicModel.calculate_cost_stack(
        scale_mt_pet_year=50000.0,
        electricity_price_kwh=0.08,
        extruder_sec_kwh_kg=0.45,
        is_pilot_scale=False,
    )
    # Direct drive electricity: ~1.198 kg PET/kg TPA * 0.45 kWh/kg * $0.08 = ~$0.043/kg TPA
    assert 0.040 <= comm_stack.extruder_electricity_usd_per_kg_tpa <= 0.045
    # Total commercial cost stack: ~$0.18 - $0.26/kg TPA
    assert 0.15 <= comm_stack.total_pretreatment_cost_usd_per_kg_tpa <= 0.30
    assert "EMPIRICAL_THERMODYNAMIC_MEASUREMENT" in comm_stack.data_attribution["extruder_electricity"]
    assert "MODELED_EQUIPMENT_ASSUMPTION" in comm_stack.data_attribution["capex_amortization"]

    # 2. Demonstration / Pilot 10,000 MT/year plant
    pilot_stack = ExtrusionTechnoEconomicModel.calculate_cost_stack(
        scale_mt_pet_year=10000.0,
        electricity_price_kwh=0.08,
        extruder_sec_kwh_kg=0.45,
        is_pilot_scale=True,
    )
    # At pilot scale, capital amortization and labor per kg increase significantly
    assert pilot_stack.total_pretreatment_cost_usd_per_kg_tpa > comm_stack.total_pretreatment_cost_usd_per_kg_tpa
    assert 0.30 <= pilot_stack.total_pretreatment_cost_usd_per_kg_tpa <= 0.55


def test_economic_inputs_taxonomy_separation() -> None:
    """Verifies that retrospective models are explicitly distinguished from contemporaneous market prices and literature."""
    items = {ms["item_id"]: ms for ms in PETaseHistoricalTrajectory.MILESTONES}

    # 2016 (Yoshida): Retrospective simulation ($65/kg TPA)
    implication_2016 = items["PET-2016-YOSHIDA"]["commercial_implication"]
    assert implication_2016["economic_metric_type"] == "RETROSPECTIVE_MODEL_ESTIMATE"
    assert implication_2016["contemporaneous_virgin_price_usd_kg"] == 1.25
    assert "Retrospective bioprocess simulation" in implication_2016["historical_basis_notes"]

    # 2018 (Austin): Retrospective simulation ($42/kg TPA)
    implication_2018 = items["PET-2018-AUSTIN"]["commercial_implication"]
    assert implication_2018["economic_metric_type"] == "RETROSPECTIVE_MODEL_ESTIMATE"

    # 2020 (Tournier): Sourced literature estimate ($1.65/kg TPA)
    implication_2020 = items["PET-2020-TOURNIER"]["commercial_implication"]
    assert implication_2020["economic_metric_type"] == "SOURCED_LITERATURE_ESTIMATE"

    # 2024 (Consortium): Sourced literature reconciliation ($1.60/kg TPA)
    implication_2024 = items["PET-2024-DILIGENCE"]["commercial_implication"]
    assert implication_2024["economic_metric_type"] == "SOURCED_LITERATURE_ESTIMATE"


def test_enzyme_lineage_and_homology_distinction() -> None:
    """Ensures that distinct enzyme families (LCC cutinase vs IsPETase) are not mislabeled as direct replications."""
    items = {ms["item_id"]: ms for ms in PETaseHistoricalTrajectory.MILESTONES}

    # Yoshida 2016: Initial discovery
    assert items["PET-2016-YOSHIDA"]["enzyme_lineage_class"] == "INITIAL_DISCOVERY"

    # Austin 2018: Independent active-site extension on the same IsPETase chassis
    assert items["PET-2018-AUSTIN"]["enzyme_lineage_class"] == "INDEPENDENT_STRUCTURAL_EXTENSION"

    # Tournier 2020: Distinct enzyme family! Leaf-branch compost cutinase (LCC), NOT IsPETase
    assert items["PET-2020-TOURNIER"]["enzyme_lineage_class"] == "HOMOLOGOUS_CUTINASE_FAMILY_ENGINEERING"

    # Lu 2022: Computational engineering on the IsPETase chassis (FAST-PETase)
    assert items["PET-2022-LU"]["enzyme_lineage_class"] == "SAME_CHASSIS_DIRECTED_EVOLUTION"

    # 2024: Systems reconciliation
    assert items["PET-2024-DILIGENCE"]["enzyme_lineage_class"] == "SYSTEMS_RECONCILIATION_AUDIT"


def test_versioned_snapshot_manifest_preserves_superseded_v1() -> None:
    """Verifies that the superseded v1 manifest is safely preserved alongside audited v2 snapshots."""
    study_results = Path(__file__).resolve().parent.parent / "research" / "studies" / "longitudinal_petase" / "results"
    superseded_path = study_results / "snapshots_manifest_v1_superseded.json"
    v2_path = study_results / "snapshots_manifest_v2.json"

    assert superseded_path.exists(), "Superseded v1 manifest must be preserved for audit history!"
    assert v2_path.exists(), "Audited v2 manifest must be generated!"

    with open(superseded_path, "r", encoding="utf-8") as f:
        v1_data = json.load(f)
    with open(v2_path, "r", encoding="utf-8") as f:
        v2_data = json.load(f)

    assert len(v1_data) == 5
    assert len(v2_data) == 5

    # Check that Snapshot 1 in v1 contained 5XJH (the hindsight flaw) while v2 strictly removed it
    v1_s1_structures = v1_data[0].get("structures", [])
    v2_s1_structures = v2_data[0].get("structures", [])

    assert "5XJH" in v1_s1_structures, "Historical record of flaw must be preserved in v1 artifact!"
    assert "5XJH" not in v2_s1_structures, "Audited v2 must have 5XJH removed from 2016!"
    assert v2_data[0]["superseded_v1_hash"] == v1_data[0]["snapshot_hash"]


def test_longitudinal_strict_date_cutoff_prevents_hindsight_leakage(temp_db: Database) -> None:
    """Verifies that earlier snapshots strictly exclude publications released after the cutoff date."""
    engine = LongitudinalReplayEngine(temp_db)
    engine.seed_historical_trajectory()

    # Query as of 2018-05-01 (should only contain Yoshida 2016 and Austin 2018)
    snap_2018 = engine.generate_snapshot("fast_petase_depolymerase", "2018-05-01", "Snapshot 2018")

    assert snap_2018.publications_count == 2
    pub_dois = [p["doi"] for p in snap_2018.publications]
    assert "10.1126/science.aad6359" in pub_dois
    assert "10.1073/pnas.1718804115" in pub_dois

    # Ensure 2020 (Tournier) and 2022 (Lu) do NOT leak in
    assert "10.1038/s41586-020-2149-4" not in pub_dois
    assert "10.1038/s41586-022-04599-z" not in pub_dois


def test_snapshot_immutability_and_hash_stability(temp_db: Database) -> None:
    """Verifies that an earlier snapshot hash remains identical before and after a newer snapshot is generated."""
    engine = LongitudinalReplayEngine(temp_db)
    engine.seed_historical_trajectory()

    snap_2016_before = engine.generate_snapshot("fast_petase_depolymerase", "2016-04-01", "Snapshot 2016")
    _ = engine.generate_snapshot("fast_petase_depolymerase", "2020-05-01", "Snapshot 2020")
    _ = engine.generate_snapshot("fast_petase_depolymerase", "2024-02-01", "Snapshot 2024")
    snap_2016_after = engine.generate_snapshot("fast_petase_depolymerase", "2016-04-01", "Snapshot 2016")

    assert snap_2016_before.snapshot_hash == snap_2016_after.snapshot_hash
    assert snap_2016_before.publications_count == snap_2016_after.publications_count == 1
    assert snap_2016_before.commercial_feasibility["estimated_tpa_cost_usd_kg"] == 65.00


def test_new_evidence_shifts_commercial_assessment_without_rewriting_earlier(temp_db: Database) -> None:
    """Demonstrates that new publications change evidence and economic state without deleting earlier assessments."""
    engine = LongitudinalReplayEngine(temp_db)
    snapshots = engine.run_full_historical_replay("fast_petase_depolymerase")

    s1 = snapshots[0]
    assert s1.as_of_date == "2016-04-01"
    assert s1.commercial_feasibility["estimated_tpa_cost_usd_kg"] == 65.00
    assert "ECONOMICALLY UNVIABLE" in s1.commercial_feasibility["commercial_verdict"]

    s3 = snapshots[2]
    assert s3.as_of_date == "2020-05-01"
    assert s3.commercial_feasibility["estimated_tpa_cost_usd_kg"] == 1.65
    assert "CONDITIONAL PILOT VIABILITY" in s3.commercial_feasibility["commercial_verdict"]

    s5 = snapshots[4]
    assert s5.as_of_date == "2024-02-01"
    assert s5.commercial_feasibility["estimated_tpa_cost_usd_kg"] == 1.60
    assert "NON-BIOLOGICAL UNIT OPERATIONS" in s5.commercial_feasibility["commercial_verdict"]

    # S1 was not altered by S3 or S5
    assert s1.commercial_feasibility["estimated_tpa_cost_usd_kg"] == 65.00


def test_negative_study_not_penalized_arbitrarily_in_quality_evaluator() -> None:
    """A well-designed negative study (e.g. 0% depolymerization on crystalline PET, p > 0.05) is valid negative evidence."""
    exp_negative = ExperimentRecord(
        experiment_id="exp_crystalline_fail",
        publication_id="doi:10.1126/test_neg",
        experimental_method="High-temperature degradation assay",
        model_system="in_vitro",
        treatment_intervention="Wild-type IsPETase on biaxially oriented crystalline PET",
        control_group="Buffer only; amorphous PET positive control",
        biological_replicates=3,
        technical_replicates=3,
        evidence_category="cell_free_biocatalysis",
        limitations="Enzyme fails to penetrate dense crystalline regions",
    )
    res_negative = ResultRecord(
        result_id="res_crystalline_fail",
        experiment_id="exp_crystalline_fail",
        measured_endpoint="crystallinity_conversion_pct",
        value=0.0,
        unit="percent",
        p_value=0.45,
        standard_deviation=0.05,
        statistical_method="ANOVA with Tukey post-hoc",
    )

    assessment = EvidenceQualityEvaluator.evaluate(exp_negative, res_negative)
    assert assessment.control_rigor_score >= 0.8
    assert assessment.replication_score >= 0.8
    assert assessment.statistical_reporting_score >= 0.7
    assert assessment.overall_confidence in ("High", "Moderate")
