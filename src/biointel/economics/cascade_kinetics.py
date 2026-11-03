"""Two-Enzyme Cascade Kinetics & Product Inhibition Solver.

Solves the coupled Michaelis-Menten ODE system for enzymatic PET depolymerization:
1. PETase: Cleaves PET ester bonds -> MHET (subject to severe MHET competitive inhibition K_i)
2. MHETase: Cleaves MHET -> TPA + EG
Models reaction velocity, intermediate accumulation, and kinetic stalling.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class CascadeSimulationOutputs:
    initial_pet_mm: float
    reaction_duration_hours: float
    mhetase_ratio: float
    final_conversion_pct: float
    final_tpa_produced_mm: float
    final_mhet_accumulated_mm: float
    mhet_inhibition_factor: float
    kinetic_verdict: str
    time_course: List[Dict[str, float]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CascadeKineticsModel:
    """Coupled ODE solver for two-enzyme polyester depolymerization."""

    @classmethod
    def simulate_cascade(
        cls,
        initial_pet_mm: float = 250.0,       # ~48 g/L PET ester bonds
        reaction_hours: float = 24.0,
        petase_loading_um: float = 2.0,      # PETase concentration (uM)
        mhetase_loading_um: float = 2.0,     # MHETase concentration (uM) (0 = PETase alone)
        kcat_petase_s_inv: float = 8.5,      # s^-1
        km_petase_mm: float = 12.0,          # mM
        ki_mhet_mm: float = 0.22,            # mM (severe competitive inhibition constant)
        ki_tpa_mm: float = 35.0,             # mM (mild TPA product inhibition)
        kcat_mhetase_s_inv: float = 28.0,    # s^-1
        km_mhetase_mm: float = 0.35,         # mM
        dt_seconds: float = 10.0,
    ) -> CascadeSimulationOutputs:
        """
        Solves:
        d[PET]/dt = -r1
        d[MHET]/dt = r1 - r2
        d[TPA]/dt = r2
        where:
        r1 = (Vmax1 * [PET]) / [Km1 * (1 + [MHET]/Ki_mhet + [TPA]/Ki_tpa) + [PET]]
        r2 = (Vmax2 * [MHET]) / [Km2 + [MHET]]
        """
        # Vmax in mM / s = kcat [s^-1] * [E] [uM] * 1e-3 [mM/uM]
        vmax1 = kcat_petase_s_inv * (petase_loading_um * 1e-3)
        vmax2 = kcat_mhetase_s_inv * (mhetase_loading_um * 1e-3)

        pet = initial_pet_mm
        mhet = 0.0
        tpa = 0.0

        total_steps = int((reaction_hours * 3600.0) / dt_seconds)
        record_interval = max(1, total_steps // 48)  # Record 48 data points

        time_course: List[Dict[str, float]] = []

        for step in range(total_steps):
            t_hr = (step * dt_seconds) / 3600.0

            # PETase rate r1 with competitive MHET and TPA inhibition
            inhibition_term = 1.0 + (mhet / max(1e-6, ki_mhet_mm)) + (tpa / max(1e-6, ki_tpa_mm))
            apparent_km1 = km_petase_mm * inhibition_term
            r1 = (vmax1 * pet) / (apparent_km1 + pet) if pet > 0 else 0.0

            # MHETase rate r2
            r2 = (vmax2 * mhet) / (km_mhetase_mm + mhet) if mhet > 0 else 0.0

            # Numerical integration (Euler forward with stability clamping)
            d_pet = min(pet, r1 * dt_seconds)
            d_mhet_in = d_pet
            d_mhet_out = min(mhet + d_mhet_in, r2 * dt_seconds)

            pet -= d_pet
            mhet += (d_mhet_in - d_mhet_out)
            tpa += d_mhet_out

            if step % record_interval == 0 or step == total_steps - 1:
                conversion = ((initial_pet_mm - pet) / initial_pet_mm) * 100.0
                time_course.append({
                    "time_hours": round(t_hr, 2),
                    "pet_remaining_mm": round(pet, 2),
                    "mhet_intermediate_mm": round(mhet, 3),
                    "tpa_product_mm": round(tpa, 2),
                    "conversion_pct": round(conversion, 2),
                    "inhibition_multiplier": round(inhibition_term, 2),
                })

        final_conv = ((initial_pet_mm - pet) / initial_pet_mm) * 100.0
        final_inhib = 1.0 + (mhet / max(1e-6, ki_mhet_mm)) + (tpa / max(1e-6, ki_tpa_mm))

        if mhetase_loading_um == 0.0 or final_inhib > 20.0:
            verdict = "KINETIC STALLING: Severe MHET accumulation competitively inhibited PETase active site."
        else:
            verdict = "EFFICIENT CASCADE: MHET intermediate cleared rapidly; conversion reached target."

        return CascadeSimulationOutputs(
            initial_pet_mm=initial_pet_mm,
            reaction_duration_hours=reaction_hours,
            mhetase_ratio=round(mhetase_loading_um / max(1e-6, petase_loading_um), 2),
            final_conversion_pct=round(final_conv, 2),
            final_tpa_produced_mm=round(tpa, 2),
            final_mhet_accumulated_mm=round(mhet, 3),
            mhet_inhibition_factor=round(final_inhib, 2),
            kinetic_verdict=verdict,
            time_course=time_course,
        )
