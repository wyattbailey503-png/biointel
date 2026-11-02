"""Science-to-Commercialization Feasibility Framework.

Evaluates biological innovations across eight distinct, explainable dimensions:
Scientific Validity, Engineering Feasibility, Scale Feasibility, Product Feasibility,
Regulatory Feasibility, Economic Feasibility, Competitive Differentiation, and Defensibility.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class CommercializationDimension:
    dimension_name: str
    status: str  # Validated, De-risked, Emergent, Unproven, Bottleneck
    score: float  # 0.0 to 10.0
    evidence_summary: str
    key_risks: List[str]


@dataclass
class CommercializationAssessment:
    technology_id: str
    maturity_stage: str
    dimensions: Dict[str, CommercializationDimension]
    overall_commercial_readiness: str  # Commercial, Late Preclinical, Early Pipeline, Research Tool, Horizon
    major_bottlenecks: List[str]
    strategic_recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technology_id": self.technology_id,
            "maturity_stage": self.maturity_stage,
            "overall_commercial_readiness": self.overall_commercial_readiness,
            "dimensions": {k: asdict(v) for k, v in self.dimensions.items()},
            "major_bottlenecks": self.major_bottlenecks,
            "strategic_recommendation": self.strategic_recommendation,
        }


class CommercializationEvaluator:
    """Computes multidimensional feasibility profiles for biotechnology platforms."""

    @classmethod
    def evaluate_precision_fermentation(cls, tech_id: str = "precision_fermentation_hydrolase") -> CommercializationAssessment:
        dimensions = {
            "scientific_validity": CommercializationDimension(
                dimension_name="Scientific Validity",
                status="Validated",
                score=9.0,
                evidence_summary="Catalytic mechanism, active-site stereoselectivity, and substrate kinetics verified by crystal structure and in vitro enzyme assays.",
                key_risks=["Potential substrate inhibition at pilot fermentation concentrations."],
            ),
            "engineering_feasibility": CommercializationDimension(
                dimension_name="Engineering Feasibility",
                status="De-risked",
                score=8.5,
                evidence_summary="Successfully expressed in standard Pichia pastoris / Komagataella phaffii expression system with high secretion efficiency.",
                key_risks=["Host cell protease degradation during prolonged fed-batch culture."],
            ),
            "scale_feasibility": CommercializationDimension(
                dimension_name="Scale Feasibility",
                status="Emergent",
                score=6.5,
                evidence_summary="Demonstrated in 50 L pilot bioreactors; oxygen transfer and heat dissipation manageable up to 20,000 L.",
                key_risks=["Oxygen mass transfer limitation ($k_L a$) in commercial >100 m³ fermenters."],
            ),
            "product_feasibility": CommercializationDimension(
                dimension_name="Product Feasibility",
                status="Validated",
                score=8.0,
                evidence_summary="Meets industrial specifications for biocatalytic enantiomeric excess (>99% ee) in fine chemical synthesis.",
                key_risks=["Downstream formulated stability over 12-month ambient storage."],
            ),
            "regulatory_feasibility": CommercializationDimension(
                dimension_name="Regulatory Feasibility",
                status="De-risked",
                score=8.0,
                evidence_summary="Non-pathogenic microbial host with GRAS history for industrial enzymes; self-affirmed GRAS or TSCA pathway.",
                key_risks=["Residual host cell protein (HCP) threshold compliance in food/pharma grades."],
            ),
            "economic_feasibility": CommercializationDimension(
                dimension_name="Economic Feasibility",
                status="De-risked",
                score=7.5,
                evidence_summary="Achievable production cost of $14.20/kg at 45 g/L titer with 85% DSP recovery, yielding viable gross margins (>50%).",
                key_risks=["Sensitivity to carbon feedstock (glucose/dextrose) price spikes."],
            ),
            "competitive_differentiation": CommercializationDimension(
                dimension_name="Competitive Differentiation",
                status="Validated",
                score=8.5,
                evidence_summary="10x higher stereoselectivity and 3-fold higher catalytic rate ($k_{cat}/K_M$) than incumbent chemical catalysts.",
                key_risks=["Commoditization if competitor directed evolution produces equivalent isoforms."],
            ),
            "defensibility": CommercializationDimension(
                dimension_name="Defensibility",
                status="Emergent",
                score=7.0,
                evidence_summary="Composition of matter patents filed covering specific engineered active-pocket mutations and expression cassette.",
                key_risks=["Freedom to operate around legacy fungal expression vectors."],
            ),
        }

        bottlenecks = [
            "Downstream processing (DSP) purification cost and yield at >10,000 L batch scale.",
            "Aeration and cooling limits in high-density aerobic fermentation.",
        ]

        recommendation = (
            "Advance from 50 L pilot to 5,000 L demo scale. Focus R&D on strain engineering to reduce "
            "foaming and optimize carbon conversion yield ($Y_{p/s}$) to insulate unit economics against glucose volatility."
        )

        return CommercializationAssessment(
            technology_id=tech_id,
            maturity_stage="pilot_scale",
            dimensions=dimensions,
            overall_commercial_readiness="Late Preclinical / Pilot Scale",
            major_bottlenecks=bottlenecks,
            strategic_recommendation=recommendation,
        )
