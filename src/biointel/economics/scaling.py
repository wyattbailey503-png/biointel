"""Continuous Scale-Elasticity & Unit-Operation Power Law Engine.

Implements chemical engineering economies of scale (the 'six-tenths' rule):
    CapEx(S) = CapEx_ref * (S / S_ref)^alpha
    C_unit(S) = C_variable + C_fixed_ref * (S_ref / S)^(1 - alpha)

Eliminates the 'Point-Scale Bias' by generating continuous cost-scaling functions
from small-scale pilot facilities to world-scale commercial gigafactories.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ScaleCurvePoint:
    scale_value: float
    scale_unit: str
    unit_cost_usd: float
    capex_contribution_usd: float
    variable_cost_usd: float
    scale_label: str  # 'PILOT', 'DEMONSTRATION', 'COMMERCIAL', 'WORLD_SCALE'


@dataclass(frozen=True)
class ScaleElasticityProfile:
    technology_id: str
    scale_unit: str
    reference_scale: float
    scaling_exponent_alpha: float
    variable_cost_floor_usd: float
    fixed_capex_cost_ref_usd: float
    curve_points: List[ScaleCurvePoint]

    def evaluate_cost_at_scale(self, scale: float) -> float:
        """Evaluate unit cost at arbitrary capacity scale."""
        if scale <= 0:
            raise ValueError("Scale must be strictly positive.")
        # Variable costs remain constant per unit; fixed/capital amortization decays with scale^(alpha - 1)
        fixed_unit = self.fixed_capex_cost_ref_usd * ((self.reference_scale / scale) ** (1.0 - self.scaling_exponent_alpha))
        return round(self.variable_cost_floor_usd + fixed_unit, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technology_id": self.technology_id,
            "scale_unit": self.scale_unit,
            "reference_scale": self.reference_scale,
            "scaling_exponent_alpha": self.scaling_exponent_alpha,
            "variable_cost_floor_usd": self.variable_cost_floor_usd,
            "fixed_capex_cost_ref_usd": self.fixed_capex_cost_ref_usd,
            "curve_points": [asdict(p) for p in self.curve_points],
        }


class ScaleElasticityEngine:
    """Computes continuous capital and operating cost elasticity across production scales."""

    # Standard chemical & biochemical engineering unit-operation scaling exponents (alpha)
    UNIT_OP_EXPONENTS = {
        "twin_screw_extrusion": 0.65,    # Thermal amorphization extruder lines
        "electrodialysis_bmed": 0.85,    # Modular electrochemical cell pair membrane stacks
        "stirred_bioreactor": 0.60,      # Vessel geometry (surface-to-volume ratio bound)
        "tangential_flow_filtration": 0.78, # Membrane cassette holders and skids
        "microfluidic_formulation": 0.82,  # Parallelized microchannel cartridges
        "sterile_fill_finish": 0.55,     # Automated vial isolator and robotic packaging line
    }

    @classmethod
    def build_scale_profile(
        cls,
        technology_id: str,
        scale_unit: str,
        reference_scale: float,
        unit_cost_ref: float,
        fixed_cost_fraction: float = 0.55,
        scaling_exponent_alpha: float = 0.65,
        scale_multipliers: Optional[List[float]] = None,
    ) -> ScaleElasticityProfile:
        """
        Constructs a complete scale-elasticity profile across 4 capacity tiers.
        """
        if scale_multipliers is None:
            # 0.05x (Pilot), 0.20x (Demo), 1.0x (Commercial Ref), 3.0x (World-Scale)
            scale_multipliers = [0.05, 0.20, 1.0, 3.0]

        fixed_ref = unit_cost_ref * fixed_cost_fraction
        var_ref = unit_cost_ref * (1.0 - fixed_cost_fraction)

        points: List[ScaleCurvePoint] = []
        tier_labels = {
            0: "PILOT",
            1: "DEMONSTRATION",
            2: "COMMERCIAL_REFERENCE",
            3: "WORLD_SCALE",
        }

        for idx, mult in enumerate(scale_multipliers):
            scale_val = reference_scale * mult
            # Scale-dependent fixed amortization
            fixed_unit = fixed_ref * ((reference_scale / scale_val) ** (1.0 - scaling_exponent_alpha))
            total_unit = var_ref + fixed_unit
            label = tier_labels.get(idx, f"SCALE_{mult}X")

            points.append(ScaleCurvePoint(
                scale_value=round(scale_val, 2),
                scale_unit=scale_unit,
                unit_cost_usd=round(total_unit, 4),
                capex_contribution_usd=round(fixed_unit, 4),
                variable_cost_usd=round(var_ref, 4),
                scale_label=label,
            ))

        return ScaleElasticityProfile(
            technology_id=technology_id,
            scale_unit=scale_unit,
            reference_scale=reference_scale,
            scaling_exponent_alpha=scaling_exponent_alpha,
            variable_cost_floor_usd=round(var_ref, 4),
            fixed_capex_cost_ref_usd=round(fixed_ref, 4),
            curve_points=points,
        )
