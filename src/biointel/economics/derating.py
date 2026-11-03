"""Operational Commissioning Derating & Commercial Friction Engine.

Eliminates the 'Steady-State / Nameplate Capacity Bias' and 'FTO Royalty Blindspot':
1. Commissioning Ramp-Up: Real biotechnology facilities suffer high fixed-cost burdens in Year 1-2.
2. Batch Scrap & Contamination: Phage/bacterial contamination, filter plugging, and off-spec discards.
3. Freedom-to-Operate (FTO) & Patent Thickets: Commercial licensing royalty stacks (5-12%).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class OperationalDeratingSummary:
    year: int
    operational_stage: str
    effective_capacity_factor_pct: float
    steady_state_cost_usd: float
    fixed_overhead_inflation_multiplier: float
    batch_contamination_loss_pct: float
    fto_licensing_royalty_pct: float
    physical_cost_floor_usd: float
    commercial_clearing_cost_usd: float


class OperationalDeratingEngine:
    """Calculates realistic commissioning ramp-up and commercial IP royalty friction."""

    # Standard empirical capacity factor ramp for commercial biochemical/biopharmaceutical plants
    RAMP_PROFILE = {
        1: {"stage": "YEAR_1_COMMISSIONING", "capacity_factor_pct": 45.0, "scrap_pct": 8.0},
        2: {"stage": "YEAR_2_RAMP_UP",       "capacity_factor_pct": 75.0, "scrap_pct": 5.0},
        3: {"stage": "MATURE_STEADY_STATE",  "capacity_factor_pct": 92.0, "scrap_pct": 3.0},
    }

    @classmethod
    def evaluate_derated_costs(
        cls,
        steady_state_unit_cost_usd: float,
        fixed_cost_fraction: float = 0.50,
        fto_licensing_royalty_pct: float = 8.0,
        reference_year: int = 1,
    ) -> OperationalDeratingSummary:
        """
        Derates steady-state engineering costs to account for commissioning and IP drag.
        """
        profile = cls.RAMP_PROFILE.get(reference_year, cls.RAMP_PROFILE[3])
        cap_factor = profile["capacity_factor_pct"]
        scrap_rate = profile["scrap_pct"]
        stage = profile["stage"]

        # In year 1, running at 45% capacity inflates fixed CapEx/labor amortization:
        # fixed_unit_actual = fixed_unit_steady * (92% / cap_factor)
        mature_cap = 92.0
        fixed_multiplier = mature_cap / cap_factor if cap_factor > 0 else 2.0

        var_part = steady_state_unit_cost_usd * (1.0 - fixed_cost_fraction)
        fixed_part = steady_state_unit_cost_usd * fixed_cost_fraction * fixed_multiplier

        # Add batch contamination scrap loss
        unrecovered_loss_mult = 1.0 + (scrap_rate / 100.0)
        physical_derated_cost = (var_part + fixed_part) * unrecovered_loss_mult

        # Add Freedom-to-Operate (FTO) patent royalty drag
        # Commercial clearing cost includes IP licensing stacks (e.g. CleanCap, SM-102, mutant enzyme patents)
        commercial_cost = physical_derated_cost * (1.0 + (fto_licensing_royalty_pct / 100.0))

        return OperationalDeratingSummary(
            year=reference_year,
            operational_stage=stage,
            effective_capacity_factor_pct=cap_factor,
            steady_state_cost_usd=round(steady_state_unit_cost_usd, 4),
            fixed_overhead_inflation_multiplier=round(fixed_multiplier, 3),
            batch_contamination_loss_pct=scrap_rate,
            fto_licensing_royalty_pct=fto_licensing_royalty_pct,
            physical_cost_floor_usd=round(physical_derated_cost, 4),
            commercial_clearing_cost_usd=round(commercial_cost, 4),
        )
