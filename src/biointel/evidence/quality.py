"""Scientific Quality and Evidence Rigor Assessment.

Evaluates evidence across multiple explainable dimensions without
relying on arbitrary universal single-number 'truth scores'.
Enforces Hard Quality Gates and Claim Provenance tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from biointel.entities.models import ExperimentRecord, ResultRecord


class ReviewStatus(str, Enum):
    DRAFT = "DRAFT"
    SOURCE_CHECKED = "SOURCE_CHECKED"
    CALCULATION_CHECKED = "CALCULATION_CHECKED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    EXTERNALLY_REVIEWED = "EXTERNALLY_REVIEWED"
    REJECTED = "REJECTED"


@dataclass
class ClaimProvenance:
    claim_id: str
    doi: str
    source_title: str
    figure_or_table: str
    quoted_passage: str
    char_offset: Optional[int] = None
    is_verified: bool = False
    verification_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "doi": self.doi,
            "source_title": self.source_title,
            "figure_or_table": self.figure_or_table,
            "quoted_passage": self.quoted_passage,
            "char_offset": self.char_offset,
            "is_verified": self.is_verified,
            "verification_notes": self.verification_notes,
        }


@dataclass
class QualityAssessment:
    study_design_score: float  # 0.0 to 1.0
    control_rigor_score: float
    replication_score: float
    statistical_reporting_score: float
    biological_relevance_score: float
    overall_confidence: str  # High, Moderate, Low, Exploratory
    flags: List[str]
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "study_design_score": round(self.study_design_score, 2),
            "control_rigor_score": round(self.control_rigor_score, 2),
            "replication_score": round(self.replication_score, 2),
            "statistical_reporting_score": round(self.statistical_reporting_score, 2),
            "biological_relevance_score": round(self.biological_relevance_score, 2),
            "overall_confidence": self.overall_confidence,
            "flags": self.flags,
            "rationale": self.rationale,
        }


class EvidenceQualityEvaluator:
    """Evaluates the experimental rigor of biological studies."""

    @classmethod
    def evaluate(cls, exp: ExperimentRecord, result: ResultRecord) -> QualityAssessment:
        flags: List[str] = []

        # 1. Study Design & Model System
        design_scores = {
            "human_clinical": 1.0,
            "animal": 0.85,
            "organoid": 0.75,
            "primary_cells": 0.70,
            "cell_line": 0.55,
            "in_vitro": 0.50,
            "computational_prediction": 0.30,
        }
        design_score = design_scores.get(exp.model_system.lower(), 0.5)
        if exp.model_system.lower() == "computational_prediction":
            flags.append("UNVALIDATED_COMPUTATIONAL_PREDICTION: Findings require wet-lab experimental confirmation.")
        elif exp.model_system.lower() == "cell_line":
            flags.append("IMMORTALIZED_CELL_LINE: Immortalized model may not reflect primary human tissue biology.")

        # 2. Controls
        if exp.control_group and len(exp.control_group.strip()) > 2:
            control_score = 0.9
        else:
            control_score = 0.3
            flags.append("MISSING_EXPLICIT_CONTROL: Study did not report an explicit negative or vehicle control group.")

        # 3. Replication
        bio_rep = exp.biological_replicates or 0
        tech_rep = exp.technical_replicates or 0
        if bio_rep >= 3:
            rep_score = 0.95
        elif bio_rep >= 2:
            rep_score = 0.70
            flags.append("LIMITED_BIOLOGICAL_REPLICATES: n < 3 biological replicates reported.")
        elif tech_rep >= 3:
            rep_score = 0.50
            flags.append("TECHNICAL_REPLICATES_ONLY: Technical replicates reported without distinct biological replicates.")
        else:
            rep_score = 0.25
            flags.append("UNREPLICATED: Study reporting lacks independent replication numbers.")

        # 4. Statistical Reporting
        stat_points = 0.0
        if result.p_value is not None:
            stat_points += 0.35
            if result.p_value > 0.05:
                flags.append("STATISTICALLY_NON_SIGNIFICANT: Reported p-value exceeds standard 0.05 threshold.")
        if result.standard_deviation is not None or result.confidence_interval is not None:
            stat_points += 0.35
        if result.statistical_method:
            stat_points += 0.30
        stat_score = min(1.0, max(0.1, stat_points))
        if stat_score < 0.5:
            flags.append("INCOMPLETE_STATISTICAL_REPORTING: Missing error metrics (SD/CI) or named statistical test.")

        # 5. Biological Relevance
        relevance_score = design_score * (0.8 if exp.cell_line_or_tissue else 0.5)

        # Composite tier assignment
        avg_score = (design_score + control_score + rep_score + stat_score) / 4.0
        if avg_score >= 0.8 and not any("UNREPLICATED" in f for f in flags):
            confidence = "High"
        elif avg_score >= 0.6:
            confidence = "Moderate"
        elif avg_score >= 0.4:
            confidence = "Low"
        else:
            confidence = "Exploratory"

        rationale = (
            f"Assessed on {exp.model_system} system ({exp.species or 'unspecified species'}). "
            f"Biological replicates: {bio_rep}, Technical: {tech_rep}. "
            f"Reporting completeness: {'Complete' if stat_score >= 0.7 else 'Partial'}."
        )

        return QualityAssessment(
            study_design_score=design_score,
            control_rigor_score=control_score,
            replication_score=rep_score,
            statistical_reporting_score=stat_score,
            biological_relevance_score=relevance_score,
            overall_confidence=confidence,
            flags=flags,
            rationale=rationale,
        )


class HardQualityGateEngine:
    """Enforces non-negotiable review gate rules and provenance validation."""

    @classmethod
    def validate_gate_transition(
        cls,
        current_status: ReviewStatus,
        target_status: ReviewStatus,
        provenance_claims: List[ClaimProvenance],
        calculations_verified: bool = False,
        diligence_questions_answered: int = 0,
        is_human_actor: bool = False,
    ) -> Dict[str, Any]:
        violations: List[str] = []

        # Rule 1: Human review statuses can NEVER be set by software agents
        if target_status in [ReviewStatus.HUMAN_REVIEWED, ReviewStatus.EXTERNALLY_REVIEWED]:
            if not is_human_actor:
                violations.append(
                    f"GOVERNANCE_VIOLATION: Automated system cannot assign {target_status}. "
                    "Only documented human action by a verified reviewer may set this status."
                )

        # Rule 2: Promotion to SOURCE_CHECKED or higher requires 100% verified claims
        if target_status in [
            ReviewStatus.SOURCE_CHECKED,
            ReviewStatus.CALCULATION_CHECKED,
            ReviewStatus.READY_FOR_REVIEW,
            ReviewStatus.HUMAN_REVIEWED,
            ReviewStatus.EXTERNALLY_REVIEWED,
        ]:
            if not provenance_claims:
                violations.append("NO_CLAIMS_ATTACHED: Report contains zero provenance claims.")
            else:
                unverified = [c for c in provenance_claims if not c.is_verified]
                if unverified:
                    violations.append(
                        f"UNVERIFIED_CLAIMS_PRESENT: {len(unverified)} / {len(provenance_claims)} "
                        f"claims lack verified DOI quotations (e.g. {unverified[0].claim_id})."
                    )
                missing_quotes = [c for c in provenance_claims if not c.quoted_passage or len(c.quoted_passage.strip()) < 10]
                if missing_quotes:
                    violations.append(
                        f"MISSING_SOURCE_QUOTES: {len(missing_quotes)} claims lack verifiable quotation excerpts."
                    )

        # Rule 3: Promotion to CALCULATION_CHECKED requires deterministic math verification
        if target_status in [
            ReviewStatus.CALCULATION_CHECKED,
            ReviewStatus.READY_FOR_REVIEW,
            ReviewStatus.HUMAN_REVIEWED,
            ReviewStatus.EXTERNALLY_REVIEWED,
        ]:
            if not calculations_verified:
                violations.append(
                    "CALCULATION_VERIFICATION_MISSING: Quantitative mass balances or financial models "
                    "have not been verified deterministically."
                )

        # Rule 4: Promotion to READY_FOR_REVIEW requires all 8 diligence questions
        if target_status in [
            ReviewStatus.READY_FOR_REVIEW,
            ReviewStatus.HUMAN_REVIEWED,
            ReviewStatus.EXTERNALLY_REVIEWED,
        ]:
            if diligence_questions_answered < 8:
                violations.append(
                    f"INCOMPLETE_DILIGENCE_FRAMEWORK: Only {diligence_questions_answered}/8 core diligence "
                    "questions answered. Reports without all 8 questions remain DESCRIPTIVE, not ANALYTICAL."
                )

        allowed = len(violations) == 0
        new_status = target_status if allowed else ReviewStatus.REJECTED if target_status != ReviewStatus.DRAFT else current_status

        return {
            "allowed": allowed,
            "current_status": current_status.value,
            "target_status": target_status.value,
            "resulting_status": new_status.value,
            "violations": violations,
        }
