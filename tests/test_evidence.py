"""Tests for Evidence Quality Scoring and Contradiction Detection."""

from __future__ import annotations

from biointel.entities.models import ExperimentRecord, ResultRecord
from biointel.evidence.contradiction import ContradictionDetector
from biointel.evidence.quality import EvidenceQualityEvaluator


def test_quality_evaluator_scoring() -> None:
    exp = ExperimentRecord(
        experiment_id="exp_001",
        publication_id="doi:10.1000/1",
        experimental_method="T7E1 assay",
        model_system="cell_line",
        treatment_intervention="CRISPR treatment",
        evidence_category="cell_based_experiment",
        control_group="Scrambled guide",
        biological_replicates=3,
        technical_replicates=3,
    )
    result = ResultRecord(
        result_id="res_001",
        experiment_id="exp_001",
        measured_endpoint="editing_efficiency",
        value=45.0,
        unit="percent",
        p_value=0.01,
        standard_deviation=2.5,
        statistical_method="t-test",
    )

    assessment = EvidenceQualityEvaluator.evaluate(exp, result)
    assert assessment.overall_confidence in ("High", "Moderate")
    assert assessment.control_rigor_score >= 0.8
    assert assessment.replication_score >= 0.9


def test_contradiction_detector_finds_discrepancy() -> None:
    exp_a = ExperimentRecord(
        experiment_id="exp_a",
        publication_id="doi:10.1000/a",
        experimental_method="Deep sequencing",
        model_system="cell_line",
        cell_line_or_tissue="HEK293T",
        treatment_intervention="Editor X",
        evidence_category="cell_based_experiment",
    )
    res_a = ResultRecord(
        result_id="res_a",
        experiment_id="exp_a",
        measured_endpoint="editing_efficiency",
        value=65.0,
        unit="percent",
        p_value=0.001,
    )

    exp_b = ExperimentRecord(
        experiment_id="exp_b",
        publication_id="doi:10.1000/b",
        experimental_method="Deep sequencing",
        model_system="primary_cells",
        cell_line_or_tissue="Primary Hepatocytes",
        treatment_intervention="Editor X",
        evidence_category="cell_based_experiment",
    )
    res_b = ResultRecord(
        result_id="res_b",
        experiment_id="exp_b",
        measured_endpoint="editing_efficiency",
        value=12.0,
        unit="percent",
        p_value=0.20,
    )

    report = ContradictionDetector.compare_experiments(exp_a, res_a, exp_b, res_b)
    assert report.has_conflict is True
    assert report.severity in ("high", "medium")
    assert any(d["factor"] == "statistical_significance" for d in report.divergent_aspects)
    assert any(d["factor"] == "model_system" for d in report.divergent_aspects)


def test_dynamic_commercialization_scoring_from_margin_and_evidence() -> None:
    """Verifies that CommercializationEvaluator dynamically updates scores based on unit economics."""
    from biointel.commercialization.framework import CommercializationEvaluator
    from biointel.economics.fermentation import FermentationInputs, TechnoEconomicFermentationModel

    # High-cost scenario: Low titer (10 g/L) -> high unit cost (> $40/kg)
    inputs_unfavorable = FermentationInputs(titer_g_per_l=10.0)
    outputs_unfavorable = TechnoEconomicFermentationModel.calculate(inputs_unfavorable)

    assessment_unfavorable = CommercializationEvaluator.evaluate_precision_fermentation(
        mass_balance=outputs_unfavorable
    )
    econ_dim_bad = assessment_unfavorable.dimensions["economic_feasibility"]
    assert econ_dim_bad.score <= 5.5
    assert econ_dim_bad.status in ("Emergent", "High Risk")

    # Favorable scenario: High titer (80 g/L) -> low unit cost (< $20/kg)
    inputs_favorable = FermentationInputs(titer_g_per_l=80.0)
    outputs_favorable = TechnoEconomicFermentationModel.calculate(inputs_favorable)

    assessment_favorable = CommercializationEvaluator.evaluate_precision_fermentation(
        mass_balance=outputs_favorable
    )
    econ_dim_good = assessment_favorable.dimensions["economic_feasibility"]
    assert econ_dim_good.score >= 7.5
    assert econ_dim_good.status == "De-risked"
