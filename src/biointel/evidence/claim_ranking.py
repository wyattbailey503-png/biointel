"""Bias-Weighted Multi-Source Scientific Claim Ranking Engine.

Ranks scientific claims according to:
1. Number of distinct, peer-reviewed sources confirming the claim.
2. Low systematic bias (unbiased academic / national lab sources weighted higher).
3. Independent replication (different institutions and author networks).
4. Penalization of contradictory evidence from rigorous studies.

Claims with more independent, unbiased sources rank strictly higher than claims
with single, conflicted, or contradictory sources.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from biointel.evidence.corroboration import ClaimCorroborationSummary, CorroboratingSourceRecord, MultiSourceCorroborator
from biointel.evidence.source_bias import FundingCategory, MeasurementMethod, SourceBiasEvaluation, SourceBiasEvaluator, SourceMetadata


@dataclass(frozen=True)
class RankedClaimRecord:
    rank: int
    claim_id: str
    technology_id: str
    claim_statement: str
    effective_unbiased_score: float
    evidence_tier: str  # 'TIER_1_GOLD_STANDARD', 'TIER_2_SILVER_CORROBORATED', 'TIER_3_BRONZE_PRELIMINARY', 'TIER_4_CONTESTED_OR_BIASED'
    supporting_sources_count: int
    independent_groups_count: int
    contradicting_sources_count: int
    mean_source_bias_score: float
    consensus_ratio_pct: float
    corroboration_summary: ClaimCorroborationSummary
    ranking_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "claim_id": self.claim_id,
            "technology_id": self.technology_id,
            "claim_statement": self.claim_statement,
            "effective_unbiased_score": self.effective_unbiased_score,
            "evidence_tier": self.evidence_tier,
            "supporting_sources_count": self.supporting_sources_count,
            "independent_groups_count": self.independent_groups_count,
            "contradicting_sources_count": self.contradicting_sources_count,
            "mean_source_bias_score": self.mean_source_bias_score,
            "consensus_ratio_pct": self.consensus_ratio_pct,
            "corroboration_summary": self.corroboration_summary.to_dict(),
            "ranking_rationale": self.ranking_rationale,
        }


class ClaimRankingEngine:
    """Ranks collections of scientific claims based on bias-weighted corroboration depth."""

    @classmethod
    def calculate_claim_score(
        cls,
        corroboration: ClaimCorroborationSummary,
    ) -> float:
        """
        Compute Effective Unbiased Corroboration Depth:
        S = sum_{sup} (1 - Bias_i) * Indep_i - 1.5 * sum_{contra} (1 - Bias_j)
        """
        support_score = 0.0
        for s in corroboration.supporting_sources:
            bias = s.bias_evaluation.composite_bias_score
            cred = max(0.0, 1.0 - bias)
            # Independence weighting
            indep_factor = 1.0 if s.bias_evaluation.circularity_bias_score <= 0.20 else 0.40
            support_score += cred * indep_factor

        contra_penalty = 0.0
        for c in corroboration.contradicting_sources:
            c_bias = c.bias_evaluation.composite_bias_score
            c_cred = max(0.0, 1.0 - c_bias)
            contra_penalty += 1.5 * c_cred

        net_score = round(max(-5.0, support_score - contra_penalty), 3)
        return net_score

    @classmethod
    def assign_evidence_tier(
        cls,
        score: float,
        independent_groups: int,
        contradicting_count: int,
    ) -> str:
        if score >= 2.0 and independent_groups >= 3 and contradicting_count == 0:
            return "TIER_1_GOLD_STANDARD"
        elif score >= 1.0 and independent_groups >= 2 and contradicting_count == 0:
            return "TIER_2_SILVER_CORROBORATED"
        elif score >= 0.35 and contradicting_count == 0:
            return "TIER_3_BRONZE_PRELIMINARY"
        else:
            return "TIER_4_CONTESTED_OR_BIASED"

    @classmethod
    def rank_claims(
        cls,
        claims: List[ClaimCorroborationSummary],
    ) -> List[RankedClaimRecord]:
        """Rank claims descending by effective unbiased corroboration score."""
        scored: List[tuple[float, ClaimCorroborationSummary]] = []
        for c in claims:
            s = cls.calculate_claim_score(c)
            scored.append((s, c))

        # Sort descending: higher unbiased score first; break ties with more independent groups
        scored.sort(key=lambda x: (x[0], x[1].independent_supporting_groups_count, -x[1].contradicting_sources_count), reverse=True)

        ranked: List[RankedClaimRecord] = []
        for idx, (score, c) in enumerate(scored, start=1):
            tier = cls.assign_evidence_tier(score, c.independent_supporting_groups_count, c.contradicting_sources_count)
            all_biases = [s.bias_evaluation.composite_bias_score for s in (c.supporting_sources + c.contradicting_sources)]
            mean_bias = round(sum(all_biases) / len(all_biases), 3) if all_biases else 0.0

            if tier == "TIER_1_GOLD_STANDARD":
                rationale = f"Gold standard: {c.supporting_sources_count} supporting sources across {c.independent_groups_count if hasattr(c, 'independent_groups_count') else c.independent_supporting_groups_count} independent groups with low bias (mean: {mean_bias}). Zero contradictions."
            elif tier == "TIER_2_SILVER_CORROBORATED":
                rationale = f"Silver corroborated: {c.supporting_sources_count} sources across {c.independent_supporting_groups_count} independent groups with good consensus."
            elif tier == "TIER_3_BRONZE_PRELIMINARY":
                rationale = "Preliminary: single group observation or modest source count without extensive cross-lab validation."
            else:
                rationale = f"Contested or biased: subject to commercial conflicts of interest, high risk of bias, or active contradictions ({c.contradicting_sources_count} refuting studies)."

            ranked.append(RankedClaimRecord(
                rank=idx,
                claim_id=c.claim_id,
                technology_id=c.technology_id,
                claim_statement=c.claim_statement,
                effective_unbiased_score=score,
                evidence_tier=tier,
                supporting_sources_count=c.supporting_sources_count,
                independent_groups_count=c.independent_supporting_groups_count,
                contradicting_sources_count=c.contradicting_sources_count,
                mean_source_bias_score=mean_bias,
                consensus_ratio_pct=round(c.consensus_ratio * 100.0, 1),
                corroboration_summary=c,
                ranking_rationale=rationale,
            ))

        return ranked
