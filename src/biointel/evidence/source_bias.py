"""Multi-Dimensional Scientific Source Bias Evaluator.

Assesses systematic bias across 4 independent dimensions:
1. Commercial / Funding Conflict of Interest Bias
2. Methodological & Study Design Rigor (Cochrane RoB 2.0 principles)
3. Bibliometric Co-Authorship & Institutional Circularity Bias
4. Reporting Transparency & Publication / Selective Reporting Bias

Calculates a composite source bias score in [0.0, 1.0], where:
  0.0 = Rigorous, independent, peer-reviewed, well-controlled gold standard
  1.0 = Highly biased, commercially conflicted, unverified or self-serving claim
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class FundingCategory(str, Enum):
    GOVERNMENT_NATIONAL_LAB = "GOVERNMENT_NATIONAL_LAB"          # e.g., NREL, NIH, CNRS, Max Planck
    INDEPENDENT_ACADEMIC = "INDEPENDENT_ACADEMIC"                # Peer-reviewed university research
    INDUSTRY_COLLABORATIVE = "INDUSTRY_COLLABORATIVE"            # Academic lab with corporate sponsorship
    CORPORATE_INTERNAL = "CORPORATE_INTERNAL"                    # Corporate R&D disclosure / patent filing
    COMMERCIAL_PROMOTIONAL = "COMMERCIAL_PROMOTIONAL"            # Pitch deck, press release, non-peer-reviewed


class MeasurementMethod(str, Enum):
    QUANTITATIVE_CHROMATOGRAPHY_MS = "QUANTITATIVE_CHROMATOGRAPHY_MS"  # HPLC, GC-MS, LC-MS/MS, absolute quantification
    ATOMIC_STRUCTURE = "ATOMIC_STRUCTURE"                              # X-ray crystallography <=2.5A, Cryo-EM, NMR
    HIGH_THROUGHPUT_SEQUENCING = "HIGH_THROUGHPUT_SEQUENCING"          # Targeted NGS, deep RNA-seq
    SPECTROPHOTOMETRIC_PROXY = "SPECTROPHOTOMETRIC_PROXY"              # Turbidity, UV-Vis absorption, dye release
    UNVERIFIED_PROXY = "UNVERIFIED_PROXY"                              # Visual estimate, uncalibrated optical proxy


@dataclass(frozen=True)
class SourceMetadata:
    source_id: str
    title: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    year: int = 2020
    journal: Optional[str] = None
    funding_category: FundingCategory = FundingCategory.INDEPENDENT_ACADEMIC
    measurement_method: MeasurementMethod = MeasurementMethod.QUANTITATIVE_CHROMATOGRAPHY_MS
    is_peer_reviewed: bool = True
    has_negative_control: bool = True
    has_biological_replicates: bool = True
    replicates_count: int = 3
    is_external_replication: bool = True
    declares_conflict_of_interest: bool = False
    discloses_negative_findings: bool = True
    open_data_available: bool = True


@dataclass(frozen=True)
class SourceBiasEvaluation:
    source_id: str
    title: str
    commercial_bias_score: float      # [0.0, 1.0]
    methodology_bias_score: float     # [0.0, 1.0]
    circularity_bias_score: float     # [0.0, 1.0]
    reporting_bias_score: float       # [0.0, 1.0]
    composite_bias_score: float       # [0.0, 1.0]
    unbiased_credibility_weight: float # 1.0 - composite_bias_score in [0.0, 1.0]
    bias_category: str                # 'LOW_BIAS_GOLD_STANDARD', 'MODERATE_BIAS', 'HIGH_BIAS_CAUTION', 'CRITICAL_BIAS_UNRELIABLE'
    identified_bias_flags: List[str]
    audit_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SourceBiasEvaluator:
    """Evaluates multi-dimensional epistemic and operational source bias."""

    @classmethod
    def evaluate_source(cls, meta: SourceMetadata) -> SourceBiasEvaluation:
        flags: List[str] = []

        # 1. Commercial / Funding Conflict Bias
        if meta.funding_category == FundingCategory.GOVERNMENT_NATIONAL_LAB:
            comm_bias = 0.05
        elif meta.funding_category == FundingCategory.INDEPENDENT_ACADEMIC:
            comm_bias = 0.15 if not meta.declares_conflict_of_interest else 0.35
            if meta.declares_conflict_of_interest:
                flags.append("COMMERCIAL_CONFLICT: Academic authors hold commercial licensing or equity stakes.")
        elif meta.funding_category == FundingCategory.INDUSTRY_COLLABORATIVE:
            comm_bias = 0.45
            flags.append("INDUSTRY_FUNDING: Research supported by corporate industry sponsor.")
        elif meta.funding_category == FundingCategory.CORPORATE_INTERNAL:
            comm_bias = 0.75
            flags.append("CORPORATE_R_AND_D: Internal company disclosures without independent academic insulation.")
        else:
            comm_bias = 0.95
            flags.append("UNVERIFIED_COMMERCIAL: Marketing pitch or press release without external verification.")

        # 2. Methodological & Study Design Bias (Cochrane RoB 2.0 principles)
        method_bias = 0.0
        if meta.measurement_method == MeasurementMethod.QUANTITATIVE_CHROMATOGRAPHY_MS:
            method_bias += 0.05
        elif meta.measurement_method == MeasurementMethod.ATOMIC_STRUCTURE:
            method_bias += 0.05
        elif meta.measurement_method == MeasurementMethod.HIGH_THROUGHPUT_SEQUENCING:
            method_bias += 0.10
        elif meta.measurement_method == MeasurementMethod.SPECTROPHOTOMETRIC_PROXY:
            method_bias += 0.45
            flags.append("INDIRECT_ASSAY_BIAS: Dependent on spectrophotometric dye or turbidity proxy rather than mass balance.")
        else:
            method_bias += 0.70
            flags.append("UNVALIDATED_ASSAY: Dependent on uncalibrated or qualitative measurement.")

        if not meta.has_negative_control:
            method_bias += 0.20
            flags.append("MISSING_CONTROLS: Lacks validated negative or inactive mutant controls.")

        if not meta.has_biological_replicates or meta.replicates_count < 3:
            method_bias += 0.15
            flags.append(f"UNDERPOWERED_REPLICATES: Insufficient biological replicates (n={meta.replicates_count}).")

        method_bias = min(1.0, method_bias)

        # 3. Bibliometric Co-Authorship & Circularity Bias
        if meta.is_external_replication:
            circ_bias = 0.05
        else:
            circ_bias = 0.65
            flags.append("CIRCULAR_REPLICATION: Performed by original discovering laboratory or co-inventor network.")

        # 4. Reporting Transparency & Publication Bias
        rep_bias = 0.0
        if not meta.is_peer_reviewed:
            rep_bias += 0.40
            flags.append("UNREVIEWED_PREPRINT_OR_COMMERCIAL: Source lacks formal independent peer review.")
        if not meta.discloses_negative_findings:
            rep_bias += 0.30
            flags.append("SELECTIVE_REPORTING: Fails to report negative mutants, failure regimes, or boundary limits.")
        if not meta.open_data_available:
            rep_bias += 0.15
            flags.append("CLOSED_RAW_DATA: Raw chromatographic/sequencing data not deposited in public repository.")

        rep_bias = min(1.0, rep_bias)

        # Composite Weighted Bias Calculation
        composite = round(
            0.35 * comm_bias + 0.35 * method_bias + 0.15 * circ_bias + 0.15 * rep_bias,
            4
        )
        credibility_weight = round(max(0.0, 1.0 - composite), 4)

        if composite < 0.20:
            category = "LOW_BIAS_GOLD_STANDARD"
            verdict = "Rigorous, independent, peer-reviewed study with comprehensive controls and minimal bias."
        elif composite < 0.45:
            category = "MODERATE_BIAS"
            verdict = "Reliable scientific study with minor methodological limitations or single-institution authorship."
        elif composite < 0.70:
            category = "HIGH_BIAS_CAUTION"
            verdict = "Significant risk of bias due to corporate sponsorship, proxy assays, or circular validation."
        else:
            category = "CRITICAL_BIAS_UNRELIABLE"
            verdict = "High risk of systematic error; commercially conflicted or unverified without peer-reviewed data."

        return SourceBiasEvaluation(
            source_id=meta.source_id,
            title=meta.title,
            commercial_bias_score=round(comm_bias, 3),
            methodology_bias_score=round(method_bias, 3),
            circularity_bias_score=round(circ_bias, 3),
            reporting_bias_score=round(rep_bias, 3),
            composite_bias_score=composite,
            unbiased_credibility_weight=credibility_weight,
            bias_category=category,
            identified_bias_flags=flags,
            audit_rationale=verdict,
        )
