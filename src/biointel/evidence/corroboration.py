"""Multi-Source Evidence Corroboration Engine.

Aggregates independent scientific studies, measures cross-validation consensus,
and detects contradictions across disparate research groups and institutions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from biointel.evidence.source_bias import SourceBiasEvaluation, SourceBiasEvaluator, SourceMetadata


@dataclass(frozen=True)
class CorroboratingSourceRecord:
    source_id: str
    citation: str
    doi: Optional[str]
    pmid: Optional[str]
    bias_evaluation: SourceBiasEvaluation
    support_direction: str  # 'SUPPORTS', 'CONTRADICTS', 'QUALIFIED'
    measured_value: Optional[float] = None
    unit: Optional[str] = None
    operating_conditions: Optional[str] = None


@dataclass(frozen=True)
class ClaimCorroborationSummary:
    claim_id: str
    claim_statement: str
    technology_id: str
    total_sources_count: int
    supporting_sources_count: int
    independent_supporting_groups_count: int
    contradicting_sources_count: int
    weighted_support_mass: float
    weighted_contradiction_mass: float
    consensus_ratio: float  # [0.0, 1.0]
    is_multi_source_corroborated: bool
    corroboration_status: str  # 'ROBUST_CONSENSUS', 'MODERATE_CORROBORATION', 'SINGLE_SOURCE_UNCONFIRMED', 'CONTESTED_CONTRADICTED'
    supporting_sources: List[CorroboratingSourceRecord]
    contradicting_sources: List[CorroboratingSourceRecord]
    synthesis_narrative: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_statement": self.claim_statement,
            "technology_id": self.technology_id,
            "total_sources_count": self.total_sources_count,
            "supporting_sources_count": self.supporting_sources_count,
            "independent_supporting_groups_count": self.independent_supporting_groups_count,
            "contradicting_sources_count": self.contradicting_sources_count,
            "weighted_support_mass": self.weighted_support_mass,
            "weighted_contradiction_mass": self.weighted_contradiction_mass,
            "consensus_ratio": self.consensus_ratio,
            "is_multi_source_corroborated": self.is_multi_source_corroborated,
            "corroboration_status": self.corroboration_status,
            "supporting_sources": [asdict(s) for s in self.supporting_sources],
            "contradicting_sources": [asdict(s) for s in self.contradicting_sources],
            "synthesis_narrative": self.synthesis_narrative,
        }


class MultiSourceCorroborator:
    """Evaluates multi-source convergence and discordance across scientific claims."""

    @classmethod
    def evaluate_claim_corroboration(
        cls,
        claim_id: str,
        claim_statement: str,
        technology_id: str,
        sources: List[CorroboratingSourceRecord],
    ) -> ClaimCorroborationSummary:
        supporting: List[CorroboratingSourceRecord] = []
        contradicting: List[CorroboratingSourceRecord] = []

        weighted_support = 0.0
        weighted_contra = 0.0
        distinct_indep_supporting: set[str] = set()

        for s in sources:
            weight = s.bias_evaluation.unbiased_credibility_weight
            if s.support_direction == "SUPPORTS":
                supporting.append(s)
                weighted_support += weight
                if s.bias_evaluation.circularity_bias_score <= 0.20:
                    # Treat as independent group if circularity is low
                    distinct_indep_supporting.add(s.source_id)
            elif s.support_direction == "CONTRADICTS":
                contradicting.append(s)
                weighted_contra += weight

        total_mass = weighted_support + weighted_contra
        consensus_ratio = round(weighted_support / total_mass, 3) if total_mass > 0 else 0.0

        n_indep = len(distinct_indep_supporting)
        is_multi = n_indep >= 2 and consensus_ratio >= 0.70

        if n_indep >= 3 and consensus_ratio >= 0.85:
            status = "ROBUST_CONSENSUS"
            narrative = f"Strong multi-group consensus: {len(supporting)} peer-reviewed sources across {n_indep} independent groups confirm the claim with high credibility."
        elif n_indep >= 2 and consensus_ratio >= 0.70:
            status = "MODERATE_CORROBORATION"
            narrative = f"Moderately corroborated: {len(supporting)} sources confirm the claim across {n_indep} independent groups."
        elif len(contradicting) > 0 and consensus_ratio < 0.60:
            status = "CONTESTED_CONTRADICTED"
            narrative = f"Contested claim: {len(contradicting)} rigorous sources contradict or fail to replicate the reported findings."
        elif len(supporting) == 1:
            status = "SINGLE_SOURCE_UNCONFIRMED"
            narrative = "Single-source observation: lacks external independent corroboration."
        else:
            status = "UNVERIFIED_EVIDENCE"
            narrative = "Insufficient credible evidence to corroborate claim."

        return ClaimCorroborationSummary(
            claim_id=claim_id,
            claim_statement=claim_statement,
            technology_id=technology_id,
            total_sources_count=len(sources),
            supporting_sources_count=len(supporting),
            independent_supporting_groups_count=n_indep,
            contradicting_sources_count=len(contradicting),
            weighted_support_mass=round(weighted_support, 3),
            weighted_contradiction_mass=round(weighted_contra, 3),
            consensus_ratio=consensus_ratio,
            is_multi_source_corroborated=is_multi,
            corroboration_status=status,
            supporting_sources=supporting,
            contradicting_sources=contradicting,
            synthesis_narrative=narrative,
        )
