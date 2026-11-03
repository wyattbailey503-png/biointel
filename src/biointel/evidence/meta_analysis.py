"""Systematic Review Cochrane Risk of Bias (RoB 2.0) & Quantitative Meta-Analysis Engine.

Implements gold-standard evidence synthesis methodology:
1. Cochrane Risk of Bias 2.0 assessment across 5 bias domains.
2. DerSimonian-Laird Random Effects meta-analysis for pooling heterogeneous experimental effects.
3. Cochran's Q test and Higgins I^2 inconsistency index to detect assay heterogeneity.
4. Egger's linear regression test for funnel plot asymmetry (detecting publication bias / file-drawer effect).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class StudyEffectRecord:
    study_id: str
    doi: str
    year: int
    enzyme_variant: str
    reported_rate_effect: float     # Measured effect size (e.g. log fold-change vs WT or mg TPA/L/hr)
    sample_variance: float          # Variance of measurement (SE^2)
    sample_size: int
    assay_method: str               # 'HPLC_QUANTITATIVE' vs 'UV_VIS_SPECTROPHOTOMETRY'
    is_external_replication: bool
    temperature_c: float
    crystallinity_pct: float


@dataclass
class MetaAnalysisSummary:
    number_of_studies: int
    pooled_effect_random_effects: float
    confidence_interval_95_lower: float
    confidence_interval_95_upper: float
    between_study_variance_tau2: float
    cochrans_q_statistic: float
    degrees_of_freedom: int
    higgins_i2_pct: float
    heterogeneity_classification: str
    eggers_intercept: float
    publication_bias_detected: bool
    is_statistically_poolable: bool
    methodological_guidance: str
    risk_of_bias_breakdown: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetaAnalysisEngine:
    """Formal statistical evidence synthesis and publication bias auditor."""

    @classmethod
    def evaluate_risk_of_bias(cls, study: StudyEffectRecord) -> Dict[str, Any]:
        """Evaluates Cochrane RoB 2.0 risk across 5 domains."""
        domains: Dict[str, str] = {}

        # D1: Confounding / Baseline condition selection
        if study.crystallinity_pct > 25.0:
            domains["D1_confounding"] = "LOW"
        else:
            # High risk of overestimating activity on amorphous film without testing bottle flake
            domains["D1_confounding"] = "SOME_CONCERNS"

        # D2: Measurement validity (HPLC vs UV-Vis)
        if "hplc" in study.assay_method.lower():
            domains["D2_measurement"] = "LOW"
        else:
            # UV-Vis at 240 nm suffers from soluble oligomer / turbidity interference
            domains["D2_measurement"] = "HIGH"

        # D3: Independent replication
        if study.is_external_replication:
            domains["D3_independence"] = "LOW"
        else:
            domains["D3_independence"] = "SOME_CONCERNS"

        # D4: Missing data / sample size
        if study.sample_size >= 3:
            domains["D4_sample_power"] = "LOW"
        else:
            domains["D4_sample_power"] = "HIGH"

        # D5: Selective reporting
        domains["D5_reporting"] = "LOW"

        # Overall RoB
        if any(v == "HIGH" for v in domains.values()):
            overall = "HIGH_RISK"
        elif sum(1 for v in domains.values() if v == "SOME_CONCERNS") >= 2:
            overall = "SOME_CONCERNS"
        else:
            overall = "LOW_RISK"

        return {
            "study_id": study.study_id,
            "doi": study.doi,
            "domain_scores": domains,
            "overall_risk_of_bias": overall,
        }

    @classmethod
    def run_meta_analysis(
        cls,
        studies: List[StudyEffectRecord],
    ) -> MetaAnalysisSummary:
        """
        Executes DerSimonian-Laird random effects meta-analysis and Egger's test.
        """
        k = len(studies)
        if k < 2:
            raise ValueError("Meta-analysis requires at least 2 independent studies.")

        # 1. Fixed effect weights: w_i = 1 / v_i
        y = [s.reported_rate_effect for s in studies]
        v = [max(1e-6, s.sample_variance) for s in studies]
        se = [math.sqrt(var) for var in v]
        w = [1.0 / var for var in v]

        sum_w = sum(w)
        sum_wy = sum(w_i * y_i for w_i, y_i in zip(w, y))
        y_fixed = sum_wy / sum_w

        # 2. Cochran's Q heterogeneity statistic:
        q = sum(w_i * ((y_i - y_fixed) ** 2) for w_i, y_i in zip(w, y))
        df = k - 1

        # 3. Between-study variance tau^2 (DerSimonian-Laird):
        # C = sum(w) - [ sum(w^2) / sum(w) ]
        sum_w_sq = sum(w_i ** 2 for w_i in w)
        c_denom = sum_w - (sum_w_sq / sum_w)
        if c_denom > 1e-9:
            tau_sq = max(0.0, (q - df) / c_denom)
        else:
            tau_sq = 0.0

        # 4. Higgins I^2 inconsistency index:
        # I^2 = max(0, (Q - df) / Q) * 100%
        if q > 1e-9:
            i_sq = max(0.0, ((q - df) / q) * 100.0)
        else:
            i_sq = 0.0

        # 5. Random effects weights: w_i* = 1 / (v_i + tau^2)
        w_star = [1.0 / (var + tau_sq) for var in v]
        sum_w_star = sum(w_star)
        y_random = sum(w_i * y_i for w_i, y_i in zip(w_star, y)) / sum_w_star
        se_random = 1.0 / math.sqrt(sum_w_star)

        ci_lower = y_random - 1.96 * se_random
        ci_upper = y_random + 1.96 * se_random

        # 6. Egger's linear regression test for funnel plot asymmetry:
        # z_i = y_i / SE_i regressed on precision x_i = 1 / SE_i
        # z_i = beta_0 + beta_1 * x_i
        precisions = [1.0 / s for s in se]
        z_scores = [y_i / s for y_i, s in zip(y, se)]

        n_pts = float(k)
        x_bar = sum(precisions) / n_pts
        z_bar = sum(z_scores) / n_pts

        s_xx = sum((x - x_bar) ** 2 for x in precisions)
        s_xz = sum((x - x_bar) * (z - z_bar) for x, z in zip(precisions, z_scores))

        if s_xx > 1e-9:
            beta_1 = s_xz / s_xx
            beta_0 = z_bar - beta_1 * x_bar
        else:
            beta_0 = 0.0

        # Asymmetry flag: |beta_0| > 1.5 indicates substantial funnel plot asymmetry
        pub_bias_detected = abs(beta_0) > 1.5

        # Heterogeneity verdict
        if i_sq < 25.0:
            het_class = "LOW_HETEROGENEITY (STUDIES HIGHLY CONCORDANT)"
            poolable = True
            guidance = "Quantitative pooling justified. Studies measure consistent biophysical phenomena."
        elif i_sq <= 75.0:
            het_class = "MODERATE_HETEROGENEITY (SYSTEMATIC INTER-ASSAY VARIATION)"
            poolable = True
            guidance = "Pooling acceptable under random-effects model with explicit caveat regarding varying assay parameters."
        else:
            het_class = "SUBSTANTIAL_HETEROGENEITY (INCOMPATIBLE EVIDENCE REGIMES)"
            poolable = False
            guidance = (
                f"Statistical pooling INVALID (I^2 = {i_sq:.1f}% > 75%, Q = {q:.1f}). "
                "Studies were conducted under contradictory substrate crystallinities, temperatures, or enzyme variants. "
                "Subgroup stratification mandatory."
            )

        rob_results = [cls.evaluate_risk_of_bias(s) for s in studies]

        return MetaAnalysisSummary(
            number_of_studies=k,
            pooled_effect_random_effects=round(y_random, 3),
            confidence_interval_95_lower=round(ci_lower, 3),
            confidence_interval_95_upper=round(ci_upper, 3),
            between_study_variance_tau2=round(tau_sq, 4),
            cochrans_q_statistic=round(q, 2),
            degrees_of_freedom=df,
            higgins_i2_pct=round(i_sq, 1),
            heterogeneity_classification=het_class,
            eggers_intercept=round(beta_0, 3),
            publication_bias_detected=pub_bias_detected,
            is_statistically_poolable=poolable,
            methodological_guidance=guidance,
            risk_of_bias_breakdown=rob_results,
        )
