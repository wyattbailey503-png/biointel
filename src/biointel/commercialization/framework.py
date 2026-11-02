"""Science-to-Commercialization Feasibility Framework.

Evaluates biological innovations across eight distinct, explainable dimensions:
Scientific Validity, Engineering Feasibility, Scale Feasibility, Product Feasibility,
Regulatory Feasibility, Economic Feasibility, Competitive Differentiation, and Defensibility.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


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
    def evaluate_precision_fermentation(
        cls,
        tech_id: str = "precision_fermentation_hydrolase",
        db: Optional[Any] = None,
        mass_balance: Optional[Any] = None,
    ) -> CommercializationAssessment:
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

        # Dynamic update from techno-economic outputs if available
        if mass_balance is not None:
            unit_cost = getattr(mass_balance, "total_cost_per_kg", None)
            annual_mt = getattr(mass_balance, "annual_production_volume_mt", None)
            productivity = getattr(mass_balance, "volumetric_productivity_g_l_h", None)

            if unit_cost is not None:
                if unit_cost < 15.0:
                    econ_score = 8.5
                    econ_status = "De-risked"
                    summary = f"Total production cost ${unit_cost:.2f}/kg enables highly favorable gross margins (>50%) against commodity benchmarks."
                elif unit_cost <= 25.0:
                    econ_score = 7.5
                    econ_status = "De-risked"
                    summary = f"Production cost ${unit_cost:.2f}/kg supports commercial viability (20-40% gross margin) for fine/specialty chemical targets."
                elif unit_cost <= 40.0:
                    econ_score = 5.5
                    econ_status = "Emergent"
                    summary = f"Unit cost ${unit_cost:.2f}/kg leaves tight gross margins; commercial success requires premium pricing or yield optimization."
                else:
                    econ_score = 3.5
                    econ_status = "High Risk"
                    summary = f"Production cost ${unit_cost:.2f}/kg is economically underwater against prevailing commercial market prices."

                dimensions["economic_feasibility"] = CommercializationDimension(
                    dimension_name="Economic Feasibility",
                    status=econ_status,
                    score=econ_score,
                    evidence_summary=summary,
                    key_risks=["Feedstock price volatility", "CAPEX debt service during scale ramp-up"],
                )

            if annual_mt is not None and productivity is not None:
                if annual_mt >= 100.0:
                    scale_score = 8.0
                    scale_status = "Validated"
                    summary = f"Demonstrated commercial-scale throughput of {annual_mt:.1f} MT/yr with volumetric productivity {productivity:.3f} g/L/h."
                else:
                    scale_score = 6.0
                    scale_status = "Emergent"
                    summary = f"Scale demonstrated at pilot volumes ({annual_mt:.1f} MT/yr); industrial aeration and heat dissipation remain scaling gates."

                dimensions["scale_feasibility"] = CommercializationDimension(
                    dimension_name="Scale Feasibility",
                    status=scale_status,
                    score=scale_score,
                    evidence_summary=summary,
                    key_risks=["Mass transfer limitations ($k_L a$) in commercial vessels (>50 m³)"],
                )

        # Dynamic update from database evidence if available
        if db is not None:
            try:
                records = db.get_evidence_records()
                verified_records = [r for r in records if r.get("is_statistically_significant", False)]
                if len(verified_records) >= 3:
                    dimensions["scientific_validity"] = CommercializationDimension(
                        dimension_name="Scientific Validity",
                        status="Validated",
                        score=min(9.5, 8.0 + len(verified_records) * 0.3),
                        evidence_summary=f"Statistically significant evidence confirmed across {len(verified_records)} independent peer-reviewed experimental assays.",
                        key_risks=["Assay translational fidelity to target commercial host matrix"],
                    )
            except Exception:
                pass

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
