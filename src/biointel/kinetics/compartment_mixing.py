"""Two-Zone Reactor Compartment Hydrodynamics & Non-Ideal Mixing Model.

Models spatial non-uniformities in large-scale commercial stirred-tank bioprocess reactors (e.g. 50 m^3):
1. Divides the vessel into two coupled hydrodynamic compartments:
   - Impeller swept zone (5-10% volume, high local energy dissipation rate, high shear, thin boundary film).
   - Bulk circulation zone (90-95% volume, low dissipation, thick boundary layer, potential mass transfer starvation).
2. Calculates impeller pumping capacity Q_pump = N_q * N * D^3 and circulation exchange time.
3. Computes local Sherwood numbers (Sh_imp, Sh_bulk) and film coefficients (k_L,imp, k_L,bulk).
4. Derives the Segregation Ratio and diagnoses non-ideal hydrodynamic bottlenecks.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class CompartmentHydrodynamicOutputs:
    vessel_volume_m3: float
    impeller_volume_m3: float
    bulk_volume_m3: float
    pumping_capacity_m3_s: float
    circulation_time_seconds: float
    total_power_kw: float
    mean_dissipation_w_m3: float
    impeller_dissipation_w_m3: float
    bulk_dissipation_w_m3: float
    particle_diameter_microns: float
    sherwood_impeller: float
    sherwood_bulk: float
    mass_transfer_coeff_impeller_m_s: float
    mass_transfer_coeff_bulk_m_s: float
    segregation_ratio: float
    bulk_starvation_risk: bool
    engineering_diagnosis: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TwoZoneReactorCompartmentModel:
    """Rigorous two-compartment hydrodynamic model for industrial stirred bioreactors."""

    DIFFUSIVITY_SOLUTE_M2_S = 7.5e-10  # m^2/s at 50 °C
    KINEMATIC_VISCOSITY_M2_S = 5.5e-7  # m^2/s (water at 50 °C)
    RHO_FLUID_KG_M3 = 1000.0           # kg/m^3

    @classmethod
    def evaluate_compartment_mixing(
        cls,
        vessel_volume_m3: float = 50.0,
        impeller_diameter_m: float = 1.35,      # D/T ~ 0.38 for vessel diameter T ~ 3.5m
        impeller_speed_rpm: float = 85.0,       # Commercial scale ~85 RPM
        pumping_number_nq: float = 0.78,        # Typical 4-blade pitched-blade turbine
        power_number_np: float = 1.30,          # PBT Power number
        impeller_volume_fraction: float = 0.08, # Impeller swept volume ~8%
        impeller_power_fraction: float = 0.70,  # 70% of energy dissipated in impeller zone
        particle_diameter_microns: float = 250.0,
    ) -> CompartmentHydrodynamicOutputs:
        """
        Calculates local dissipation rates, Sherwood numbers, and film transfer coefficients.
        """
        d_p_m = particle_diameter_microns * 1e-6
        n_rev_s = impeller_speed_rpm / 60.0

        # Pumping rate Q = Nq * N * D^3
        q_pump = pumping_number_nq * n_rev_s * (impeller_diameter_m ** 3)
        tau_circ = vessel_volume_m3 / max(1e-6, q_pump)

        # Power input P = Np * rho * N^3 * D^5
        power_watts = power_number_np * cls.RHO_FLUID_KG_M3 * (n_rev_s ** 3) * (impeller_diameter_m ** 5)
        power_kw = power_watts / 1000.0

        v_imp = vessel_volume_m3 * impeller_volume_fraction
        v_bulk = vessel_volume_m3 * (1.0 - impeller_volume_fraction)

        eps_mean = power_watts / vessel_volume_m3
        eps_imp = (power_watts * impeller_power_fraction) / max(1e-6, v_imp)
        eps_bulk = (power_watts * (1.0 - impeller_power_fraction)) / max(1e-6, v_bulk)

        # Schmidt number
        sc = cls.KINEMATIC_VISCOSITY_M2_S / cls.DIFFUSIVITY_SOLUTE_M2_S

        # Kolmogoroff micro-scale / Sherwood correlation:
        # Sh = 2.0 + 0.6 * (eps * d_p^4 / nu^3)^(1/6) * Sc^(1/3)
        re_turb_imp = (eps_imp * (d_p_m ** 4)) / (cls.KINEMATIC_VISCOSITY_M2_S ** 3)
        re_turb_bulk = (eps_bulk * (d_p_m ** 4)) / (cls.KINEMATIC_VISCOSITY_M2_S ** 3)

        sh_imp = 2.0 + 0.6 * (re_turb_imp ** (1.0 / 6.0)) * (sc ** (1.0 / 3.0))
        sh_bulk = 2.0 + 0.6 * (re_turb_bulk ** (1.0 / 6.0)) * (sc ** (1.0 / 3.0))

        kl_imp = (sh_imp * cls.DIFFUSIVITY_SOLUTE_M2_S) / d_p_m
        kl_bulk = (sh_bulk * cls.DIFFUSIVITY_SOLUTE_M2_S) / d_p_m

        segregation = kl_imp / max(1e-6, kl_bulk)
        starvation = segregation > 2.5 or kl_bulk < 1.0e-5

        if starvation:
            diag = (
                f"SEVERE HYDRODYNAMIC SEGREGATION (Segregation ratio = {segregation:.2f}). "
                f"Mass transfer in the bulk circulation zone ({v_bulk:.1f} m^3) is throttled by a thick boundary film. "
                f"Multi-impeller staging (dual/triple PBT) or higher agitation is required to prevent local substrate starvation."
            )
        else:
            diag = (
                f"ADEQUATE TWO-ZONE HYDRODYNAMICS (Segregation ratio = {segregation:.2f}). "
                f"Circulation time of {tau_circ:.1f}s maintains sufficient bulk liquid boundary exchange."
            )

        return CompartmentHydrodynamicOutputs(
            vessel_volume_m3=vessel_volume_m3,
            impeller_volume_m3=round(v_imp, 3),
            bulk_volume_m3=round(v_bulk, 3),
            pumping_capacity_m3_s=round(q_pump, 4),
            circulation_time_seconds=round(tau_circ, 2),
            total_power_kw=round(power_kw, 2),
            mean_dissipation_w_m3=round(eps_mean, 2),
            impeller_dissipation_w_m3=round(eps_imp, 2),
            bulk_dissipation_w_m3=round(eps_bulk, 2),
            particle_diameter_microns=particle_diameter_microns,
            sherwood_impeller=round(sh_imp, 2),
            sherwood_bulk=round(sh_bulk, 2),
            mass_transfer_coeff_impeller_m_s=round(kl_imp, 6),
            mass_transfer_coeff_bulk_m_s=round(kl_bulk, 6),
            segregation_ratio=round(segregation, 2),
            bulk_starvation_risk=starvation,
            engineering_diagnosis=diag,
        )
