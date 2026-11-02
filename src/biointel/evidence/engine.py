"""Evidence Engine.

Coordinates experimental data ingestion, claim-evidence linkage,
rigor evaluation, and contradiction checks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from biointel.entities.models import (
    ClaimRecord,
    EvidenceLinkRecord,
    ExperimentRecord,
    ResultRecord,
)
from biointel.evidence.contradiction import ContradictionDetector, ContradictionReport
from biointel.evidence.quality import EvidenceQualityEvaluator, QualityAssessment
from biointel.storage.database import Database


class EvidenceEngine:
    """Manages biological evidence extraction, claims, and experimental rigor."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def record_experiment_with_result(
        self,
        exp: ExperimentRecord,
        result: ResultRecord,
        claim: Optional[ClaimRecord] = None,
        support_direction: str = "supports",
    ) -> QualityAssessment:
        """Atomically persist an experiment, result, and optional claim linkage."""
        # 1. Evaluate scientific rigor
        quality = EvidenceQualityEvaluator.evaluate(exp, result)

        # 2. Persist to SQLite
        self.db.insert_experiment(exp.to_dict())
        self.db.insert_experimental_result(result.to_dict())

        # 3. If a claim is provided, link it
        if claim:
            self.db.insert_claim(claim.to_dict())
            link = EvidenceLinkRecord(
                claim_id=claim.claim_id,
                experiment_id=exp.experiment_id,
                support_direction=support_direction,
                confidence_score=quality.study_design_score,
                explanation=quality.rationale,
            )
            self.db.link_evidence(link.to_dict())

        return quality

    def check_claim_evidence(self, claim_id: str) -> Dict[str, Any]:
        """Retrieve all experiments supporting or contradicting a given claim."""
        with self.db.get_connection() as conn:
            claim_row = conn.execute("SELECT * FROM claims WHERE claim_id = ?", (claim_id,)).fetchone()
            if not claim_row:
                raise ValueError(f"Claim not found: {claim_id}")

            links = conn.execute("""
                SELECT l.*, e.*, r.measured_endpoint, r.value, r.unit, r.p_value, r.standard_deviation
                FROM evidence_links l
                JOIN experiments e ON l.experiment_id = e.experiment_id
                LEFT JOIN experimental_results r ON e.experiment_id = r.experiment_id
                WHERE l.claim_id = ?
            """, (claim_id,)).fetchall()

            supporting = [dict(r) for r in links if r["support_direction"] == "supports"]
            contradicting = [dict(r) for r in links if r["support_direction"] == "contradicts"]

            return {
                "claim": dict(claim_row),
                "supporting_experiments_count": len(supporting),
                "contradicting_experiments_count": len(contradicting),
                "supporting_evidence": supporting,
                "contradicting_evidence": contradicting,
            }
