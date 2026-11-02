"""Phase 4 Regression and Adversarial Verification Suite.

Validates:
- HardQualityGateEngine and ClaimProvenance governance
- MultiFactorAssayBoundaryEngine condition compatibility checks
- StudyPackageRunner deterministic execution across all 3 study packages
- Benchmark dataset structural integrity and domain coverage
"""

import json
from pathlib import Path
import unittest

from biointel.comparison.matrix import BoundaryCondition, MultiFactorAssayBoundaryEngine
from biointel.evidence.quality import ClaimProvenance, HardQualityGateEngine, ReviewStatus
from biointel.reports.study_runner import StudyPackageRunner


class TestPhase4Rigor(unittest.TestCase):
    """Rigorous adversarial tests for Phase 4 capabilities."""

    def test_governance_guard_prevents_ai_self_assigning_human_review(self) -> None:
        """Ensures automated agents CANNOT self-promote reports to HUMAN_REVIEWED."""
        claim = ClaimProvenance(
            claim_id="CLM-01",
            doi="10.1038/s41586-022-04599-z",
            source_title="FAST-PETase",
            figure_or_table="Fig 2b",
            quoted_passage="FAST-PETase exhibited superior depolymerization capability, converting 52.3 ± 2.8%.",
            is_verified=True,
        )

        # Automated transition attempt (is_human_actor=False)
        res = HardQualityGateEngine.validate_gate_transition(
            current_status=ReviewStatus.CALCULATION_CHECKED,
            target_status=ReviewStatus.HUMAN_REVIEWED,
            provenance_claims=[claim],
            calculations_verified=True,
            diligence_questions_answered=8,
            is_human_actor=False,
        )
        self.assertFalse(res["allowed"])
        self.assertIn("GOVERNANCE_VIOLATION", res["violations"][0])
        self.assertEqual(res["resulting_status"], ReviewStatus.REJECTED.value)

        # Human reviewer action (is_human_actor=True)
        res_human = HardQualityGateEngine.validate_gate_transition(
            current_status=ReviewStatus.CALCULATION_CHECKED,
            target_status=ReviewStatus.HUMAN_REVIEWED,
            provenance_claims=[claim],
            calculations_verified=True,
            diligence_questions_answered=8,
            is_human_actor=True,
        )
        self.assertTrue(res_human["allowed"])
        self.assertEqual(res_human["resulting_status"], ReviewStatus.HUMAN_REVIEWED.value)

    def test_gate_engine_rejects_unverified_claims(self) -> None:
        """Ensures promotion to SOURCE_CHECKED is rejected if unverified claims exist."""
        unverified_claim = ClaimProvenance(
            claim_id="CLM-UNVERIFIED",
            doi="10.1038/nature12345",
            source_title="Phantom Paper",
            figure_or_table="Fig 1",
            quoted_passage="Short",
            is_verified=False,
        )

        res = HardQualityGateEngine.validate_gate_transition(
            current_status=ReviewStatus.DRAFT,
            target_status=ReviewStatus.SOURCE_CHECKED,
            provenance_claims=[unverified_claim],
            calculations_verified=False,
            diligence_questions_answered=0,
            is_human_actor=False,
        )
        self.assertFalse(res["allowed"])
        self.assertTrue(any("UNVERIFIED_CLAIMS_PRESENT" in v for v in res["violations"]))

    def test_multi_factor_boundary_catches_crystallinity_and_temp(self) -> None:
        """Validates that MultiFactorAssayBoundaryEngine catches polymer and thermal regime mismatches."""
        cond_fast_petase = BoundaryCondition(
            assay_type="HPLC quantification of TPA in aqueous buffer",
            substrate_or_target="Amorphous PET film (Xc = 3.5%)",
            temperature_c=50.0,
            cell_model_or_host="In vitro enzyme slurry",
        )
        cond_lcc_cutinase = BoundaryCondition(
            assay_type="HPLC quantification of TPA in aqueous buffer",
            substrate_or_target="Crystalline post-consumer bottle flake (Xc = 34%)",
            temperature_c=72.0,
            cell_model_or_host="In vitro enzyme slurry",
        )

        verdict = MultiFactorAssayBoundaryEngine.evaluate_boundary(cond_fast_petase, cond_lcc_cutinase)
        self.assertFalse(verdict.is_comparable)
        self.assertTrue(any("SUBSTRATE_CRYSTALLINITY_MISMATCH" in m for m in verdict.mismatch_types))
        self.assertTrue(any("TEMPERATURE_REGIME_MISMATCH" in m for m in verdict.mismatch_types))
        self.assertLess(verdict.compatibility_score, 0.5)

    def test_multi_factor_boundary_catches_cell_and_assay_resolution(self) -> None:
        """Validates that comparing T7E1 in HEK293T to HTS in primary cells triggers warnings."""
        cond_t7e1_hek = BoundaryCondition(
            assay_type="T7E1 Enzymatic Mismatch Cleavage",
            substrate_or_target="EMX1 locus",
            cell_model_or_host="HEK293T immortalized cell line",
            delivery_system="Plasmid Lipofection",
        )
        cond_hts_primary = BoundaryCondition(
            assay_type="Targeted NGS Amplicon Deep Sequencing",
            substrate_or_target="EMX1 locus",
            cell_model_or_host="Primary human CD34+ HSPCs",
            delivery_system="RNP Electroporation",
        )

        verdict = MultiFactorAssayBoundaryEngine.evaluate_boundary(cond_t7e1_hek, cond_hts_primary)
        self.assertFalse(verdict.is_comparable)
        self.assertTrue(any("ASSAY_RESOLUTION_MISMATCH" in m for m in verdict.mismatch_types))
        self.assertTrue(any("HOST_PHYSIOLOGY_MISMATCH" in m for m in verdict.mismatch_types))
        self.assertTrue(any("DELIVERY_MODALITY_MISMATCH" in m for m in verdict.mismatch_types))

    def test_study_package_runner_verifies_all_three_studies(self) -> None:
        """Verifies that all three reproducible research study packages execute deterministically."""
        runner = StudyPackageRunner()
        studies = runner.list_studies()
        self.assertIn("study_01_petase_plastics_bioprocess", studies)
        self.assertIn("study_02_prime_vs_base_editing_diligence", studies)
        self.assertIn("study_03_lactoferrin_fermentation_scaleup", studies)

        for s_id in studies:
            report = runner.verify_study(s_id)
            self.assertTrue(report["verified"], f"Study {s_id} failed verification: {report.get('error')}")
            self.assertGreaterEqual(report["num_primary_sources"], 3)
            self.assertGreaterEqual(len(report["figures_generated"]), 2)
            self.assertEqual(report["status"], "CALCULATION_CHECKED")

    def test_benchmark_dataset_integrity(self) -> None:
        """Ensures the 20 ground-truth benchmark observations are complete and grounded."""
        bench_path = Path(__file__).resolve().parent.parent / "data" / "benchmarks" / "ground_truth_evals.json"
        self.assertTrue(bench_path.exists())

        with open(bench_path, "r") as f:
            data = json.load(f)

        observations = data.get("observations", [])
        self.assertEqual(len(observations), 20)

        domains = set(o["domain"] for o in observations)
        self.assertEqual(len(domains), 4)

        for obs in observations:
            self.assertTrue(obs["id"].startswith("OBS-"))
            self.assertIn("doi", obs["publication"])
            self.assertGreater(len(obs["provenance_quote"]), 15)
            self.assertIsNotNone(obs["reported_value"])
            self.assertTrue("unit" in obs or "reported_unit" in obs)


if __name__ == "__main__":
    unittest.main()
