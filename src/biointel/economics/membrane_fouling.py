"""Dynamic Membrane Fouling & Ultrafiltration Flux Decay Kinetics.

Implements Hermia's classical membrane blocking mechanisms (cake filtration and pore constriction)
to model flux decay J(t) during biocatalytic enzyme recovery and TPA separation.
Driven by concentrations of insoluble mono-(2-hydroxyethyl) terephthalate (MHET) and oligomers.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class FoulingSimulationResult:
    foulant_concentration_g_l: float
    transmembrane_pressure_bar: float
    initial_flux_lmh: float
    terminal_flux_lmh: float
    time_to_terminal_flux_hours: float
    average_flux_lmh: float
    permeate_volume_filtered_l_m2: float
    fouling_mechanism: str
    cip_frequency_hours: float
    flux_trajectory: List[Dict[str, float]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MembraneFoulingModel:
    """Dynamic flux decay solver based on Hermia (1982) and Darcy's law."""

    @classmethod
    def simulate_flux_decay(
        cls,
        foulant_concentration_g_l: float = 1.2,  # MHET + BHET insoluble fraction
        tmp_bar: float = 2.5,                    # Transmembrane Pressure (TMP)
        membrane_resistance_m_inv: float = 1.5e12, # Clean membrane hydraulic resistance (R_m)
        specific_cake_resistance_m_kg: float = 2.8e14, # Specific cake resistance (alpha_c)
        fluid_viscosity_pa_s: float = 0.001,    # Permeate water viscosity at operating temp (1 cP)
        terminal_flux_cutoff_pct: float = 35.0, # Flux drops to 35% of initial -> CIP mandatory
        max_batch_time_hours: float = 24.0,
        time_step_hours: float = 0.25,
    ) -> FoulingSimulationResult:
        """
        Solves Darcy's law with progressive cake formation:
        J(t) = Delta P / [mu * (R_m + R_cake(t))]
        where R_cake(t) = specific_cake_resistance * mass_cake(t)
        mass_cake(t) = foulant_concentration * V_permeate(t)
        
        Analytical solution for constant pressure cake filtration (Hermia n=0):
        (t / V) = (mu * R_m / Delta P) + (mu * alpha_c * C_b / (2 * Delta P * A^2)) * V
        J(t) = J_0 / sqrt(1 + 2 * K_c * J_0^2 * t)
        """
        tmp_pa = tmp_bar * 1e5
        
        # Initial clean water flux: J0 [m/s] = Delta P / (mu * R_m)
        j0_m_s = tmp_pa / (fluid_viscosity_pa_s * membrane_resistance_m_inv)
        j0_lmh = j0_m_s * 3600.0 * 1000.0  # Convert m/s to L/(m^2 * h)

        terminal_j_lmh = j0_lmh * (terminal_flux_cutoff_pct / 100.0)

        # Cake filtration constant: K_c [s / m^2] = (mu * alpha_c * C_b) / Delta P
        # C_b in kg/m^3 (1 g/L = 1 kg/m^3)
        c_b_kg_m3 = foulant_concentration_g_l
        k_c_s_m2 = (fluid_viscosity_pa_s * specific_cake_resistance_m_kg * c_b_kg_m3) / tmp_pa

        trajectory: List[Dict[str, float]] = []
        t_hours = 0.0
        v_filtered_l_m2 = 0.0
        time_to_terminal = max_batch_time_hours

        while t_hours <= max_batch_time_hours:
            t_seconds = t_hours * 3600.0
            # J(t) in m/s = J0 / sqrt(1 + 2 * K_c * J0^2 * t)
            denominator = math.sqrt(1.0 + (2.0 * k_c_s_m2 * (j0_m_s ** 2) * t_seconds))
            j_t_m_s = j0_m_s / denominator
            j_t_lmh = j_t_m_s * 3.6e6

            # Integrated permeate volume: V(t) [m^3/m^2] = [sqrt(1 + 2*Kc*J0^2*t) - 1] / (Kc * J0)
            if k_c_s_m2 * j0_m_s > 0:
                v_t_m = (denominator - 1.0) / (k_c_s_m2 * j0_m_s)
                v_filtered_l_m2 = v_t_m * 1000.0
            else:
                v_filtered_l_m2 = j0_lmh * t_hours

            trajectory.append({
                "time_hours": round(t_hours, 2),
                "flux_lmh": round(j_t_lmh, 2),
                "permeate_volume_l_m2": round(v_filtered_l_m2, 2),
                "relative_flux_pct": round((j_t_lmh / j0_lmh) * 100.0, 1),
            })

            if j_t_lmh <= terminal_j_lmh and time_to_terminal == max_batch_time_hours:
                time_to_terminal = t_hours

            t_hours += time_step_hours

        avg_flux = v_filtered_l_m2 / max(0.1, max_batch_time_hours)

        return FoulingSimulationResult(
            foulant_concentration_g_l=foulant_concentration_g_l,
            transmembrane_pressure_bar=tmp_bar,
            initial_flux_lmh=round(j0_lmh, 2),
            terminal_flux_lmh=round(terminal_j_lmh, 2),
            time_to_terminal_flux_hours=round(time_to_terminal, 2),
            average_flux_lmh=round(avg_flux, 2),
            permeate_volume_filtered_l_m2=round(v_filtered_l_m2, 2),
            fouling_mechanism="Cake Filtration / Concentration Polarization (Hermia n=0)",
            cip_frequency_hours=round(time_to_terminal, 2),
            flux_trajectory=trajectory,
        )
