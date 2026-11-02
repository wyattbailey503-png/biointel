"""Contradiction and Experimental Divergence Detector.

Identifies conflicting findings, condition mismatches, and replication failures
without arbitrarily suppressing unresolved scientific debates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from biointel.entities.models import ExperimentRecord, ResultRecord


@dataclass
class ContradictionReport:
    has_conflict: bool
    conflict_type: Optional[str] = None  # quantitative_discordance, model_system_incompatibility, direction_reversal
    severity: str = "none"  # low, medium, high
    summary: str = ""
    divergent_aspects: List[Dict[str, Any]] = None  # type: ignore

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_conflict": self.has_conflict,
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "summary": self.summary,
            "divergent_aspects": self.divergent_aspects or [],
        }


class ContradictionDetector:
    """Compares experimental results from different sources to detect divergence."""

    @classmethod
    def compare_experiments(
        cls,
        exp_a: ExperimentRecord,
        res_a: ResultRecord,
        exp_b: ExperimentRecord,
        res_b: ResultRecord,
    ) -> ContradictionReport:
        # Check if they measure the same endpoint
        if exp_a.experimental_method != exp_b.experimental_method and res_a.measured_endpoint != res_b.measured_endpoint:
            return ContradictionReport(
                has_conflict=False,
                summary="Assays measure different biological endpoints; cannot evaluate direct contradiction.",
            )

        divergences: List[Dict[str, Any]] = []

        # 1. Model system divergence
        if exp_a.model_system != exp_b.model_system or exp_a.cell_line_or_tissue != exp_b.cell_line_or_tissue:
            divergences.append({
                "factor": "model_system",
                "study_a": f"{exp_a.model_system} ({exp_a.cell_line_or_tissue})",
                "study_b": f"{exp_b.model_system} ({exp_b.cell_line_or_tissue})",
                "note": "Differences in chromatin state, delivery efficiency, or DNA repair pathways between cell lines may explain outcome variance.",
            })

        # 2. Quantitative outcome divergence
        if res_a.value is not None and res_b.value is not None:
            # If measuring efficiency or yield, compare relative discrepancy
            val_a, val_b = res_a.value, res_b.value
            max_v = max(abs(val_a), abs(val_b))
            diff = abs(val_a - val_b)

            if max_v > 0 and (diff / max_v) > 0.5:
                # Discrepancy > 50%
                divergences.append({
                    "factor": "quantitative_outcome",
                    "study_a_value": f"{val_a} {res_a.unit or ''}",
                    "study_b_value": f"{val_b} {res_b.unit or ''}",
                    "delta_percentage": f"{round((diff / max_v) * 100, 1)}%",
                    "note": f"Studies report divergent values for {res_a.measured_endpoint}.",
                })

        # 3. Direction reversal or significance conflict
        sig_a = res_a.p_value is not None and res_a.p_value <= 0.05
        sig_b = res_b.p_value is not None and res_b.p_value <= 0.05
        if res_a.p_value is not None and res_b.p_value is not None and sig_a != sig_b:
            divergences.append({
                "factor": "statistical_significance",
                "study_a_p": res_a.p_value,
                "study_b_p": res_b.p_value,
                "note": "One study reports statistically significant effect while the comparator does not.",
            })

        if not divergences:
            return ContradictionReport(
                has_conflict=False,
                summary="Findings are concordant within reported experimental uncertainty.",
            )

        is_reversal = any(d["factor"] == "statistical_significance" for d in divergences)
        is_large_diff = any(d["factor"] == "quantitative_outcome" for d in divergences)

        severity = "high" if is_reversal or (is_large_diff and len(divergences) > 1) else "medium"
        conflict_type = "direction_reversal" if is_reversal else "quantitative_discordance" if is_large_diff else "model_system_incompatibility"

        summary = (
            f"Detected {len(divergences)} experimental divergence factor(s) across studies "
            f"for {res_a.measured_endpoint} ({exp_a.treatment_intervention})."
        )

        return ContradictionReport(
            has_conflict=True,
            conflict_type=conflict_type,
            severity=severity,
            summary=summary,
            divergent_aspects=divergences,
        )
