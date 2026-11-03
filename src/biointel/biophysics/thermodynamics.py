"""Macromolecular Folding Thermodynamics, Eyring Kinetics & Point Mutation Delta-Delta-G.

Models thermal denaturation and conformational stability of engineered depolymerases:
1. Complete Gibbs-Helmholtz thermodynamic unfolding curve Delta G_unfold(T) with Delta C_p curvature.
2. Two-state equilibrium native fraction f_native(T) and melting temperature (T_m).
3. Eyring transition state theory for catalytic turnover k_cat(T).
4. Arrhenius irreversible thermal deactivation kinetics and half-life tau_1/2(T).
5. Point mutation stabilization energy Delta-Delta-G and predicted Delta T_m shifts.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FoldingThermodynamicsOutputs:
    variant_name: str
    melting_temperature_c: float
    operating_temperature_c: float
    gibbs_free_energy_folding_kj_per_mol: float
    fraction_native_folded: float
    unfolding_equilibrium_constant: float
    thermal_deactivation_rate_per_hour: float
    functional_half_life_hours: float
    catalytic_turnover_kcat_s_inv: float
    effective_reaction_rate_factor: float
    delta_delta_g_vs_wt_kj_per_mol: float
    thermostability_verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EnzymeFoldingThermodynamicsModel:
    """Biophysical folding thermodynamics and thermal inactivation engine."""

    GAS_CONSTANT_R = 8.314462   # J / mol / K
    PLANCK_H = 6.62607e-34      # J * s
    BOLTZMANN_KB = 1.380649e-23 # J / K

    # Authoritative biophysical unfolding baselines from differential scanning calorimetry (DSC)
    KNOWN_VARIANTS = {
        "IsPETase-WT": {
            "tm_c": 48.8,
            "delta_h_m_kj_mol": 415.0,
            "delta_cp_kj_mol_k": 7.8,
            "ea_deactivation_kj_mol": 240.0,
            "a_preexp_s_inv": 1.2e35,
            "delta_h_act_kj_mol": 48.0,
            "delta_s_act_j_mol_k": -75.0,
        },
        "FAST-PETase": { # N233K/R224Q/S121E/D186H/R280A (Lu et al., Nature 2022)
            "tm_c": 68.2,
            "delta_h_m_kj_mol": 520.0,
            "delta_cp_kj_mol_k": 8.5,
            "ea_deactivation_kj_mol": 285.0,
            "a_preexp_s_inv": 4.5e39,
            "delta_h_act_kj_mol": 45.0,
            "delta_s_act_j_mol_k": -70.0,
        },
        "LCC-ICCG": { # F243I/S283C/A284C/G147C (Tournier et al., Nature 2020)
            "tm_c": 94.5,
            "delta_h_m_kj_mol": 680.0,
            "delta_cp_kj_mol_k": 9.2,
            "ea_deactivation_kj_mol": 340.0,
            "a_preexp_s_inv": 8.0e44,
            "delta_h_act_kj_mol": 42.0,
            "delta_s_act_j_mol_k": -65.0,
        },
    }

    @classmethod
    def evaluate_variant_thermostability(
        cls,
        variant_name: str = "FAST-PETase",
        operating_temperature_c: float = 50.0,
        custom_tm_c: Optional[float] = None,
        custom_delta_delta_g_kj_mol: Optional[float] = None,
    ) -> FoldingThermodynamicsOutputs:
        """
        Solves full Gibbs-Helmholtz unfolding and Eyring transition state kinetics.
        """
        baseline = cls.KNOWN_VARIANTS.get(variant_name, cls.KNOWN_VARIANTS["FAST-PETase"])
        tm_c = custom_tm_c if custom_tm_c is not None else baseline["tm_c"]

        t_op_k = operating_temperature_c + 273.15
        tm_k = tm_c + 273.15

        delta_h_m = baseline["delta_h_m_kj_mol"] * 1000.0  # J / mol
        delta_cp = baseline["delta_cp_kj_mol_k"] * 1000.0  # J / mol / K

        # 1. Complete Gibbs-Helmholtz Unfolding Free Energy:
        # Delta G_unfold(T) = Delta H_m * (1 - T / T_m) - Delta C_p * [ (T_m - T) + T * ln(T / T_m) ]
        delta_g_unfold = (
            delta_h_m * (1.0 - (t_op_k / tm_k))
            - delta_cp * ((tm_k - t_op_k) + t_op_k * math.log(t_op_k / tm_k))
        )  # J / mol

        # Unfolding equilibrium constant: K_unfold = exp( - Delta G_unfold / (R * T) )
        # Note: Delta G_unfold > 0 indicates folded state is stable
        exponent = -delta_g_unfold / (cls.GAS_CONSTANT_R * t_op_k)
        if exponent > 50.0:
            k_unfold = 1e20
            f_native = 0.0
        elif exponent < -50.0:
            k_unfold = 1e-20
            f_native = 1.0
        else:
            k_unfold = math.exp(exponent)
            # f_native = 1 / (1 + K_unfold)
            f_native = 1.0 / (1.0 + k_unfold)

        # 2. Eyring Transition State Theory for Catalytic Turnover k_cat:
        # k_cat = (k_B * T / h) * exp( Delta S_act / R ) * exp( - Delta H_act / (R * T) )
        delta_h_act = baseline["delta_h_act_kj_mol"] * 1000.0
        delta_s_act = baseline["delta_s_act_j_mol_k"]
        kcat_intrinsic = (
            (cls.BOLTZMANN_KB * t_op_k / cls.PLANCK_H)
            * math.exp(delta_s_act / cls.GAS_CONSTANT_R)
            * math.exp(-delta_h_act / (cls.GAS_CONSTANT_R * t_op_k))
        )

        # Effective observed kcat accounting for folded fraction:
        kcat_observed = kcat_intrinsic * f_native

        # 3. Arrhenius Irreversible Inactivation Kinetics:
        # k_d = A * exp( - E_a / (R * T) )
        ea_j_mol = baseline["ea_deactivation_kj_mol"] * 1000.0
        a_preexp = baseline["a_preexp_s_inv"]
        kd_s_inv = a_preexp * math.exp(-ea_j_mol / (cls.GAS_CONSTANT_R * t_op_k))
        kd_hr_inv = kd_s_inv * 3600.0

        if kd_hr_inv > 1e-12:
            half_life_hours = math.log(2.0) / kd_hr_inv
        else:
            half_life_hours = 999999.0

        # 4. Delta-Delta-G vs Wild-Type IsPETase:
        wt_baseline = cls.KNOWN_VARIANTS["IsPETase-WT"]
        wt_tm_k = wt_baseline["tm_c"] + 273.15
        delta_s_m = delta_h_m / tm_k  # J / mol / K
        if custom_delta_delta_g_kj_mol is not None:
            ddg_kj = custom_delta_delta_g_kj_mol
        else:
            # Shift in Tm gives Delta-Delta-G ~ Delta S_m * (Tm_mutant - Tm_WT)
            ddg_kj = (delta_s_m * (tm_k - wt_tm_k)) / 1000.0

        # Thermostability verdict:
        if f_native > 0.95 and half_life_hours >= 48.0:
            verdict = "HIGHLY_THERMOSTABLE (STABLE OPERATING WINDOW)"
        elif f_native > 0.70 and half_life_hours >= 12.0:
            verdict = "MODERATE_THERMOSTABILITY (ACCEPTABLE FOR BATCH PROCESS)"
        else:
            verdict = "THERMALLY_UNSTABLE (SEVERE CONFORMATIONAL DENATURATION)"

        return FoldingThermodynamicsOutputs(
            variant_name=variant_name,
            melting_temperature_c=round(tm_c, 2),
            operating_temperature_c=operating_temperature_c,
            gibbs_free_energy_folding_kj_per_mol=round(delta_g_unfold / 1000.0, 2),
            fraction_native_folded=round(f_native, 4),
            unfolding_equilibrium_constant=k_unfold,
            thermal_deactivation_rate_per_hour=round(kd_hr_inv, 5),
            functional_half_life_hours=round(min(999999.0, half_life_hours), 2),
            catalytic_turnover_kcat_s_inv=round(kcat_observed, 3),
            effective_reaction_rate_factor=round(f_native, 3),
            delta_delta_g_vs_wt_kj_per_mol=round(ddg_kj, 2),
            thermostability_verdict=verdict,
        )
