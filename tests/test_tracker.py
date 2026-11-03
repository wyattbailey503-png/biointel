"""Unit tests for Generalized Longitudinal Technology Trajectory Tracker.

Verifies:
1. Registration and retrieval of arbitrary biotechnology platforms.
2. Chronological milestone logging and out-of-order insertion normalization.
3. Strict as_of_date cutoff enforcement preventing retroactive hindsight leakage.
4. Cryptographic provenance hashing and state immutability.
5. Differential snapshot auditing (compare_snapshots) across capabilities, boundaries, metrics, and structures.
6. CLI track subcommands integration.
"""

from __future__ import annotations

import argparse
from biointel.storage.database import Database
from biointel.longitudinal.tracker import (
    SnapshotDiff,
    TechnologyEntity,
    TechnologyTrajectoryTracker,
    TrajectoryMilestone,
    TrajectorySnapshot,
)
from biointel.cli import cmd_track


def test_technology_registration_and_listing(temp_db: Database) -> None:
    """Verifies that arbitrary biotechnology platforms can be registered, retrieved, and listed."""
    tracker = TechnologyTrajectoryTracker(temp_db)

    t1 = tracker.register_technology(
        tech_id="car_t_allogeneic",
        name="Allogeneic Off-The-Shelf CAR-T",
        domain="cell_and_gene_therapy",
        category="cell_therapy",
        maturity_stage="clinical_trial",
        description="Gene-edited allogeneic T cells with TCR alpha constant knockout to prevent GvHD.",
    )
    assert t1.tech_id == "car_t_allogeneic"
    assert t1.name == "Allogeneic Off-The-Shelf CAR-T"
    assert t1.maturity_stage == "clinical_trial"

    t2 = tracker.register_technology(
        tech_id="dac_sorbent_materials",
        name="Direct Air Capture Metal-Organic Sorbents",
        domain="climate_biotechnology",
        category="carbon_removal",
        maturity_stage="pilot_scale",
        description="Amine-functionalized MOF materials for ambient CO2 direct air capture.",
    )
    assert t2.tech_id == "dac_sorbent_materials"

    retrieved = tracker.get_technology("car_t_allogeneic")
    assert retrieved is not None
    assert retrieved.name == t1.name

    tech_list = tracker.list_technologies()
    tech_ids = [t.tech_id for t in tech_list]
    assert "car_t_allogeneic" in tech_ids
    assert "dac_sorbent_materials" in tech_ids


def test_milestone_chronological_ordering(temp_db: Database) -> None:
    """Verifies milestones are sorted strictly chronologically even if logged out of order."""
    tracker = TechnologyTrajectoryTracker(temp_db)

    # Insert later milestone first
    tracker.log_milestone(
        tech_id="base_editing",
        milestone_date="2020-06-01",
        title="CRISPR adenine base editors with expanded targeting scope",
        doi="10.1038/s41587-020-0456-9",
        milestone_type="ACTIVITY_ENHANCEMENT",
        previous_state="Early ABEs restricted to NGG PAM compatibility.",
        new_state="Engineered Cas9 variants expand ABE targeting to NG and non-G PAM sites.",
    )

    # Insert earlier milestone second
    tracker.log_milestone(
        tech_id="base_editing",
        milestone_date="2016-04-20",
        title="Programmable editing of a target base in genomic DNA without DSBs",
        doi="10.1038/nature17946",
        milestone_type="DISCOVERY",
        previous_state="Targeted single-base modification required double-strand breaks.",
        new_state="Cytidine deaminase fused to dCas9 converts C->T cleanly.",
    )

    # Insert intermediate milestone third
    tracker.log_milestone(
        tech_id="base_editing",
        milestone_date="2017-10-25",
        title="Programmable base editing of A*T to G*C in genomic DNA",
        doi="10.1038/nature24644",
        milestone_type="DISCOVERY",
        previous_state="Base editing restricted to cytidine deamination (C->T).",
        new_state="Engineered TadA deoxyadenosine deaminase enables A->G base editing.",
    )

    timeline = tracker.get_timeline("base_editing")
    assert len(timeline) == 3
    # Check strict chronological order
    assert timeline[0].milestone_date == "2016-04-20"
    assert timeline[1].milestone_date == "2017-10-25"
    assert timeline[2].milestone_date == "2020-06-01"


def test_strict_as_of_date_prevents_hindsight_leakage(temp_db: Database) -> None:
    """Verifies that snapshots strictly filter out future milestones, structures, and capabilities."""
    tracker = TechnologyTrajectoryTracker(temp_db)

    tracker.log_milestone(
        tech_id="test_platform",
        milestone_date="2018-01-15",
        title="Initial proof of concept",
        doi="10.1000/180115",
        milestone_type="DISCOVERY",
        new_state="Proof of concept achieved in vitro.",
        structures=["1AAA"],
        limitations=["In vitro only"],
        metrics={"potency_um": 50.0},
    )

    tracker.log_milestone(
        tech_id="test_platform",
        milestone_date="2021-06-30",
        title="High-potency lead molecule resolved",
        doi="10.1000/210630",
        milestone_type="STRUCTURAL_RESOLUTION",
        new_state="Co-crystal structure solved, revealing allosteric pocket.",
        structures=["2BBB"],
        limitations=["Low oral bioavailability"],
        metrics={"potency_um": 0.5, "bioavailability_pct": 5.0},
    )

    tracker.log_milestone(
        tech_id="test_platform",
        milestone_date="2024-03-10",
        title="Phase 1 clinical trial initiation",
        doi="10.1000/240310",
        milestone_type="CLINICAL_TRIAL",
        new_state="First human subjects dosed in ascending dose trial.",
        structures=[],
        limitations=["Maximum tolerated dose under evaluation"],
        metrics={"phase": 1, "patients_dosed": 12},
    )

    # Snapshot at 2019: only 2018 milestone knowable
    snap_2019 = tracker.generate_snapshot("test_platform", "2019-01-01")
    assert snap_2019.milestones_count == 1
    assert len(snap_2019.milestones) == 1
    assert snap_2019.milestones[0].milestone_date == "2018-01-15"
    assert snap_2019.eligible_structures == ["1AAA"]
    assert "2BBB" not in snap_2019.eligible_structures
    assert snap_2019.key_metrics == {"potency_um": 50.0}
    assert snap_2019.maturity_stage == "discovery"

    # Snapshot at 2022: 2018 and 2021 milestones knowable, 2024 is strictly excluded
    snap_2022 = tracker.generate_snapshot("test_platform", "2022-01-01")
    assert snap_2022.milestones_count == 2
    assert snap_2022.eligible_structures == ["1AAA", "2BBB"]
    assert snap_2022.key_metrics["potency_um"] == 0.5
    assert "patients_dosed" not in snap_2022.key_metrics

    # Snapshot at 2025: all 3 milestones knowable
    snap_2025 = tracker.generate_snapshot("test_platform", "2025-01-01")
    assert snap_2025.milestones_count == 3
    assert snap_2025.maturity_stage == "clinical_trial"
    assert snap_2025.key_metrics["patients_dosed"] == 12


def test_snapshot_hash_stability_and_provenance(temp_db: Database) -> None:
    """Verifies that snapshot hashing is deterministic and reproducible."""
    tracker = TechnologyTrajectoryTracker(temp_db)
    tracker.seed_default_trajectories()

    snap1 = tracker.generate_snapshot("fast_petase_depolymerase", "2018-05-01")
    snap2 = tracker.generate_snapshot("fast_petase_depolymerase", "2018-05-01")

    assert snap1.snapshot_hash == snap2.snapshot_hash
    assert snap1.provenance_seal == snap2.provenance_seal
    assert len(snap1.snapshot_hash) == 64
    assert snap1.provenance_seal.startswith("SEAL_V2_")


def test_differential_snapshot_audit(temp_db: Database) -> None:
    """Verifies compare_snapshots identifies additions, deltas, and progress between two cutoffs."""
    tracker = TechnologyTrajectoryTracker(temp_db)
    tracker.seed_default_trajectories()

    # Compare PETase 2016 vs 2022
    diff = tracker.compare_snapshots("fast_petase_depolymerase", "2016-04-01", "2022-06-01")

    assert diff.milestones_added_count == 3
    assert "5XJH" in diff.new_structures
    assert "7SH6" in diff.new_structures
    assert len(diff.new_physical_boundaries) >= 2
    assert diff.maturity_stage_a.lower() == "discovery"
    assert diff.maturity_stage_b.lower() in ("lead_optimization", "pilot_scale", "preclinical")
    assert "operating_temperature_c" in diff.metrics_deltas
    assert diff.metrics_deltas["operating_temperature_c"]["delta"] == 20.0
    assert len(diff.diff_hash) == 64
    assert "FAST-PETase" in diff.narrative_summary

    # Verifies swapping date order normalizes to chronological order
    diff_reverse = tracker.compare_snapshots("fast_petase_depolymerase", "2022-06-01", "2016-04-01")
    assert diff_reverse.date_a == "2016-04-01"
    assert diff_reverse.date_b == "2022-06-01"
    assert diff_reverse.diff_hash == diff.diff_hash


def test_cli_track_integration(temp_db: Database) -> None:
    """Verifies that CLI commands for track execute without exceptions."""
    import biointel.cli as cli_mod
    orig_get_db = cli_mod.get_db
    cli_mod.get_db = lambda: temp_db
    try:
        # 1. track add
        args_add = argparse.Namespace(
            command="track",
            track_action="add",
            id="synthetic_promoters",
            name="Synthetic Mammalian Promoters",
            domain="synthetic_biology",
            category="gene_regulation",
            stage="discovery",
            description="De novo designed synthetic promoters for cell-type specific expression.",
        )
        cmd_track(args_add)

        # 2. track milestone
        args_ms = argparse.Namespace(
            command="track",
            track_action="milestone",
            tech="synthetic_promoters",
            date="2023-01-15",
            title="Generative AI design of cell-type specific synthetic promoters",
            doi="10.1038/s41587-022-01615-x",
            type="DISCOVERY",
            prev="Endogenous promoters possess broad off-target expression.",
            new="Designed 100 bp synthetic enhancers with >50-fold hepatocyte selectivity.",
            significance="First computational GAN design of mammalian tissue-specific promoters.",
            implication="Reduces off-target toxicity in AAV and LNP gene therapies.",
            structures="8ABC",
            limits="Chromatin context in primary human cells remains variable",
        )
        cmd_track(args_ms)

        # 3. track timeline
        args_tl = argparse.Namespace(
            command="track",
            track_action="timeline",
            technology="synthetic_promoters",
        )
        cmd_track(args_tl)

        # 4. track snapshot
        args_snap = argparse.Namespace(
            command="track",
            track_action="snapshot",
            technology="synthetic_promoters",
            as_of="2023-06-01",
            label="Mid-2023 Evaluation",
        )
        cmd_track(args_snap)

        # 5. track diff
        args_diff = argparse.Namespace(
            command="track",
            track_action="diff",
            technology="synthetic_promoters",
            from_date="2022-01-01",
            to_date="2023-06-01",
        )
        cmd_track(args_diff)

        # 6. track list
        args_list = argparse.Namespace(
            command="track",
            track_action="list",
        )
        cmd_track(args_list)
    finally:
        cli_mod.get_db = orig_get_db


