"""Unit tests for Source Bias Evaluation, Multi-Source Corroboration, and Claim Ranking.

Verifies:
1. Multi-dimensional source bias assessment (Cochrane RoB, conflict of interest, circularity, reporting).
2. Multi-source evidence convergence and consensus calculations.
3. Ranking algorithm where claims with more independent, unbiased sources strictly outrank others.
4. Contested claims with commercial bias and peer-reviewed refutations receive severe penalties.
"""

from __future__ import annotations

import argparse
from biointel.evidence.benchmarks import (
    build_standard_corroborated_claims,
    get_contested_lactoferrin_sources,
    get_verified_fast_petase_sources,
    get_verified_mrna_pseudouridine_sources,
    get_verified_prime_editing_sources,
)
from biointel.evidence.claim_ranking import ClaimRankingEngine, RankedClaimRecord
from biointel.evidence.corroboration import MultiSourceCorroborator
from biointel.evidence.source_bias import (
    FundingCategory,
    MeasurementMethod,
    SourceBiasEvaluator,
    SourceMetadata,
)
from biointel.cli import cmd_claims, cmd_evidence


def test_source_bias_evaluation_dimensions():
    """Verify bias evaluation across national lab, academic, and commercial pitch sources."""
    # 1. National Lab Gold Standard
    meta_nrel = SourceMetadata(
        source_id="nrel_2021",
        title="NREL TEA Study",
        doi="10.1016/j.joule.2021.06.015",
        funding_category=FundingCategory.GOVERNMENT_NATIONAL_LAB,
        measurement_method=MeasurementMethod.QUANTITATIVE_CHROMATOGRAPHY_MS,
        is_peer_reviewed=True,
        has_negative_control=True,
        has_biological_replicates=True,
        replicates_count=5,
        is_external_replication=True,
        declares_conflict_of_interest=False,
    )
    eval_nrel = SourceBiasEvaluator.evaluate_source(meta_nrel)
    assert eval_nrel.composite_bias_score < 0.10
    assert eval_nrel.bias_category == "LOW_BIAS_GOLD_STANDARD"
    assert eval_nrel.unbiased_credibility_weight > 0.90
    assert len(eval_nrel.identified_bias_flags) == 0

    # 2. Commercial Pitch Deck (High Risk of Bias)
    meta_pitch = SourceMetadata(
        source_id="commercial_pitch",
        title="Series B Deck",
        funding_category=FundingCategory.COMMERCIAL_PROMOTIONAL,
        measurement_method=MeasurementMethod.UNVERIFIED_PROXY,
        is_peer_reviewed=False,
        has_negative_control=False,
        has_biological_replicates=False,
        replicates_count=1,
        is_external_replication=False,
        declares_conflict_of_interest=True,
        discloses_negative_findings=False,
        open_data_available=False,
    )
    eval_pitch = SourceBiasEvaluator.evaluate_source(meta_pitch)
    assert eval_pitch.composite_bias_score > 0.85
    assert eval_pitch.bias_category == "CRITICAL_BIAS_UNRELIABLE"
    assert eval_pitch.unbiased_credibility_weight < 0.15
    assert len(eval_pitch.identified_bias_flags) >= 5


def test_multi_source_corroboration_consensus():
    """Verify multi-source consensus calculation and contradiction detection."""
    # Robust consensus claim
    pet_sources = get_verified_fast_petase_sources()
    pet_summary = MultiSourceCorroborator.evaluate_claim_corroboration(
        claim_id="test_pet",
        claim_statement="FAST-PETase degrades PET",
        technology_id="fast_petase_depolymerase",
        sources=pet_sources,
    )
    assert pet_summary.supporting_sources_count == 4
    assert pet_summary.independent_supporting_groups_count == 4
    assert pet_summary.contradicting_sources_count == 0
    assert pet_summary.consensus_ratio == 1.0
    assert pet_summary.is_multi_source_corroborated is True
    assert pet_summary.corroboration_status == "ROBUST_CONSENSUS"

    # Contested claim with refutations
    lacto_sources = get_contested_lactoferrin_sources()
    lacto_summary = MultiSourceCorroborator.evaluate_claim_corroboration(
        claim_id="test_lacto",
        claim_statement="40 g/L commercial titer",
        technology_id="lactoferrin_fermentation",
        sources=lacto_sources,
    )
    assert lacto_summary.supporting_sources_count == 1
    assert lacto_summary.contradicting_sources_count == 2
    assert lacto_summary.consensus_ratio < 0.10
    assert lacto_summary.is_multi_source_corroborated is False
    assert lacto_summary.corroboration_status == "CONTESTED_CONTRADICTED"


def test_claim_ranking_hierarchy():
    """Verify that claims with more independent, unbiased sources strictly outrank others."""
    claims = build_standard_corroborated_claims()
    ranked = ClaimRankingEngine.rank_claims(claims)

    assert len(ranked) == 4

    # Rank 1 must be FAST-PETase (4 independent peer-reviewed sources, score ~3.55)
    r1 = ranked[0]
    assert r1.claim_id == "claim_petase_depolymerization_efficacy"
    assert r1.evidence_tier == "TIER_1_GOLD_STANDARD"
    assert r1.effective_unbiased_score >= 3.0
    assert r1.independent_groups_count == 4

    # Rank 2 must be mRNA pseudouridine (3 independent sources, score ~2.66)
    r2 = ranked[1]
    assert r2.claim_id == "claim_pseudouridine_mrna_evasion"
    assert r2.evidence_tier == "TIER_1_GOLD_STANDARD"
    assert r2.effective_unbiased_score >= 2.5

    # Rank 3 must be Prime Editing (3 sources across 2 independent groups)
    r3 = ranked[2]
    assert r3.claim_id == "claim_prime_editing_precision_and_efficiency"
    assert r3.evidence_tier == "TIER_2_SILVER_CORROBORATED"
    assert r3.effective_unbiased_score >= 2.0

    # Rank 4 must be the contested pitch deck claim (score < 0 due to contradiction penalties)
    r4 = ranked[3]
    assert r4.claim_id == "claim_lactoferrin_unverified_hyper_titer"
    assert r4.evidence_tier == "TIER_4_CONTESTED_OR_BIASED"
    assert r4.effective_unbiased_score < 0.0

    # Strict monotonicity of ranking scores
    assert r1.effective_unbiased_score > r2.effective_unbiased_score > r3.effective_unbiased_score > r4.effective_unbiased_score


def test_cli_claims_and_evidence_integration(capsys=None):
    """Verify CLI subcommands execute cleanly."""
    args_claims = argparse.Namespace(command="claims", claims_action="rank")
    cmd_claims(args_claims)

    args_ev = argparse.Namespace(command="evidence", evidence_action="audit-sources")
    cmd_evidence(args_ev)
