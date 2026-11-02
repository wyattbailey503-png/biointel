"""Longitudinal Intelligence & Evidence Evolution Tests.

Verifies:
1. Strict as_of_date cutoff enforcement preventing hindsight leakage.
2. Immutability of earlier historical snapshots when new evidence is ingested.
3. Verification of independent replication vs same-lab extension.
4. Retention of well-designed negative studies as valuable scientific evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
from biointel.entities.models import ExperimentRecord, ResultRecord
from biointel.evidence.longitudinal import LongitudinalReplayEngine, PETaseHistoricalTrajectory
from biointel.evidence.quality import EvidenceQualityEvaluator
from biointel.storage.database import Database


def test_longitudinal_strict_date_cutoff_prevents_hindsight_leakage(temp_db: Database) -> None:
    """Verifies that earlier snapshots strictly exclude publications released after the cutoff date."""
    engine = LongitudinalReplayEngine(temp_db)
    engine.seed_historical_trajectory()

    # Query as of 2018-05-01 (should only contain Yoshida 2016 and Austin 2018)
    snap_2018 = engine.generate_snapshot("fast_petase_depolymerase", "2018-05-01", "Snapshot 2018")

    assert snap_2018.publications_count == 2
    pub_dois = [p["doi"] for p in snap_2018.publications]
    assert "10.1126/science.aad6359" in pub_dois  # Yoshida 2016
    assert "10.1073/pnas.1718804115" in pub_dois  # Austin 2018

    # Ensure 2020 (Tournier) and 2022 (Lu) do NOT leak in
    assert "10.1038/s41586-020-2149-4" not in pub_dois
    assert "10.1038/s41586-022-04599-z" not in pub_dois

    # Structures must only include 5XJH and 6EQE, not 6T54 or 7SH6
    assert "5XJH" in snap_2018.structures
    assert "6EQE" in snap_2018.structures
    assert "6T54" not in snap_2018.structures
    assert "7SH6" not in snap_2018.structures


def test_snapshot_immutability_and_hash_stability(temp_db: Database) -> None:
    """Verifies that an earlier snapshot hash remains identical before and after a newer snapshot is generated."""
    engine = LongitudinalReplayEngine(temp_db)
    engine.seed_historical_trajectory()

    # Generate Snapshot 1 (2016)
    snap_2016_before = engine.generate_snapshot("fast_petase_depolymerase", "2016-04-01", "Snapshot 2016")

    # Generate subsequent snapshots
    _ = engine.generate_snapshot("fast_petase_depolymerase", "2020-05-01", "Snapshot 2020")
    _ = engine.generate_snapshot("fast_petase_depolymerase", "2024-02-01", "Snapshot 2024")

    # Regenerate Snapshot 1
    snap_2016_after = engine.generate_snapshot("fast_petase_depolymerase", "2016-04-01", "Snapshot 2016")

    assert snap_2016_before.snapshot_hash == snap_2016_after.snapshot_hash
    assert snap_2016_before.publications_count == snap_2016_after.publications_count == 1
    assert snap_2016_before.commercial_feasibility["estimated_tpa_cost_usd_kg"] == 65.00


def test_new_evidence_shifts_commercial_assessment_without_rewriting_earlier(temp_db: Database) -> None:
    """Demonstrates that new publications change evidence and economic state without deleting earlier assessments."""
    engine = LongitudinalReplayEngine(temp_db)
    snapshots = engine.run_full_historical_replay("fast_petase_depolymerase")

    # Snapshot 1 (2016): Academic early stage, $65/kg TPA
    s1 = snapshots[0]
    assert s1.as_of_date == "2016-04-01"
    assert s1.commercial_feasibility["estimated_tpa_cost_usd_kg"] == 65.00
    assert "ECONOMICALLY UNVIABLE" in s1.commercial_feasibility["commercial_verdict"]

    # Snapshot 3 (2020): Tournier et al. thermostable cutinase breakthrough, drops cost to $1.65/kg
    s3 = snapshots[2]
    assert s3.as_of_date == "2020-05-01"
    assert s3.commercial_feasibility["estimated_tpa_cost_usd_kg"] == 1.65
    assert "CONDITIONAL PILOT VIABILITY" in s3.commercial_feasibility["commercial_verdict"]

    # Snapshot 5 (2024): Industrial reconciliation reveals non-biological amorphization floor
    s5 = snapshots[4]
    assert s5.as_of_date == "2024-02-01"
    assert s5.commercial_feasibility["estimated_tpa_cost_usd_kg"] == 1.60
    assert "NON-BIOLOGICAL UNIT OPERATIONS" in s5.commercial_feasibility["commercial_verdict"]

    # S1 was not altered by S3 or S5
    assert s1.commercial_feasibility["estimated_tpa_cost_usd_kg"] == 65.00


def test_replication_classification_distinguishes_same_lab_from_independent() -> None:
    """Verifies that evidence items differentiate independent replications, same-lab extensions, and cross-family homologs."""
    items = {ms["item_id"]: ms for ms in PETaseHistoricalTrajectory.MILESTONES}

    # Yoshida 2016: Initial Discovery
    assert items["PET-2016-YOSHIDA"]["reproducibility_class"] == "INITIAL_DISCOVERY"

    # Austin 2018: Independent replication & active-site engineering (Portsmouth/NREL vs Kyoto)
    assert items["PET-2018-AUSTIN"]["reproducibility_class"] == "INDEPENDENT_REPLICATION"
    assert items["PET-2018-AUSTIN"]["is_independent"] is True

    # Tournier 2020: Distinct thermophilic cutinase homolog (LCC)
    assert items["PET-2020-TOURNIER"]["reproducibility_class"] == "CROSS_FAMILY_HOMOLOG"

    # Lu 2022: Computational engineering extension
    assert items["PET-2022-LU"]["reproducibility_class"] == "SAME_LAB_EXTENSION"


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
        p_value=0.45,  # Non-significant / null effect
        standard_deviation=0.05,
        statistical_method="ANOVA with Tukey post-hoc",
    )

    assessment = EvidenceQualityEvaluator.evaluate(exp_negative, res_negative)

    # Methodological rigor remains solid (control present, biological replicates = 3, SD reported, method named)
    assert assessment.control_rigor_score >= 0.8
    assert assessment.replication_score >= 0.8
    assert assessment.statistical_reporting_score >= 0.7
    # Overall confidence should NOT be crushed to 'Exploratory' because controls & replicates are sound
    assert assessment.overall_confidence in ("High", "Moderate")
