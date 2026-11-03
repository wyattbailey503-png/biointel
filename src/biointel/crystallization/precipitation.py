"""Reactive Crystallization & Acid Precipitation Thermodynamics for Pure Terephthalic Acid (PTA).

Rigorous downstream chemical engineering model for recovery of TPA from alkaline hydrolysate:
Na2TPA + H2SO4 -> H2TPA (solid) v + Na2SO4
1. Continuous diprotic acid-base speciation (pKa1 = 3.54, pKa2 = 4.46).
2. Davies non-ideal electrolyte activity coefficient corrections in high ionic strength media.
3. Temperature-dependent intrinsic solubility C*(T) and unrecovered mother-liquor loss.
4. Supersaturation ratio S and primary nucleation vs secondary crystal growth competition.
5. Crystal size distribution (d50) and Carman-Kozeny filtration cake resistance (alpha_c).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class PrecipitationThermodynamicOutputs:
    precipitation_temperature_c: float
    target_ph: float
    ionic_strength_molar: float
    davies_activity_coeff: float
    neutral_tpa_fraction_alpha0: float
    monoanion_fraction_alpha1: float
    dianion_fraction_alpha2: float
    intrinsic_solubility_g_l: float
    total_effective_solubility_g_l: float
    initial_tpa_concentration_g_l: float
    supersaturation_ratio: float
    precipitation_yield_pct: float
    mother_liquor_loss_pct: float
    h2so4_consumed_kg_per_kg_tpa: float
    byproduct_na2so4_kg_per_kg_tpa: float
    mean_crystal_diameter_microns: float
    specific_cake_resistance_m_kg: float
    nucleation_regime: str
    filtration_feasibility: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ReactiveCrystallizationModel:
    """Non-ideal electrolyte and speciation solver for TPA reactive crystallization."""

    PKA1 = 3.54                     # First dissociation constant of terephthalic acid
    PKA2 = 4.46                     # Second dissociation constant
    MW_TPA = 166.13                 # g / mol (C8H6O4)
    MW_H2SO4 = 98.08                # g / mol
    MW_NA2SO4 = 142.04              # g / mol
    RHO_SOLID_TPA = 1522.0          # kg / m^3 (pure crystalline TPA density)
    DELTA_H_DISSOLUTION = 24500.0   # J / mol heat of solution of neutral H2TPA
    GAS_CONSTANT_R = 8.3145         # J / mol / K

    @classmethod
    def calculate_activity_coeff(cls, ionic_strength: float, charge_z: int = 1) -> float:
        """Davies equation for activity coefficient in ionic solutions (I < 0.5 M)."""
        if ionic_strength <= 0.0:
            return 1.0
        sqrt_i = math.sqrt(ionic_strength)
        # log10(gamma) = -0.509 * z^2 * [ sqrt(I)/(1 + sqrt(I)) - 0.3 * I ]
        log10_gamma = -0.509 * (charge_z ** 2) * ((sqrt_i / (1.0 + sqrt_i)) - 0.3 * ionic_strength)
        return max(0.1, min(1.0, 10.0 ** log10_gamma))

    @classmethod
    def evaluate_acid_precipitation(
        cls,
        initial_tpa_concentration_g_l: float = 65.0,  # ~65 g/L disodium terephthalate in digestate
        operating_ph: float = 2.2,                    # Standard industrial acidulation endpoint
        temperature_c: float = 60.0,                  # Crystallization temperature (typically 50-80 °C)
        cake_porosity: float = 0.42,                  # Void fraction of filtered cake
    ) -> PrecipitationThermodynamicOutputs:
        """
        Solves complete reactive precipitation mass balance and crystal mechanics.
        """
        t_kelvin = temperature_c + 273.15
        t_ref_kelvin = 298.15  # 25 °C reference

        # 1. Temperature-dependent intrinsic solubility of neutral H2TPA:
        # C*(T) = C*(298) * exp( - Delta H / R * (1/T - 1/298.15) )
        # At 25 °C, C*(298) ~ 0.019 g / L (0.000114 M)
        solubility_ref_g_l = 0.019
        intrinsic_sol_g_l = solubility_ref_g_l * math.exp(
            (-cls.DELTA_H_DISSOLUTION / cls.GAS_CONSTANT_R) * ((1.0 / t_kelvin) - (1.0 / t_ref_kelvin))
        )

        # 2. Acid Dissociation Equilibria & Speciation:
        # [H+] = 10^(-pH)
        h_plus = 10.0 ** (-operating_ph)
        ka1 = 10.0 ** (-cls.PKA1)
        ka2 = 10.0 ** (-cls.PKA2)

        # Estimate ionic strength from background Na2SO4 brine:
        # 1 mol TPA yields 1 mol Na2SO4 -> 2 Na+ (1 M), 1 SO4^2- (0.5 M)
        # I = 0.5 * [ (2*C)*1^2 + C*2^2 ] = 3 * C_salt
        c_salt_molar = (initial_tpa_concentration_g_l / cls.MW_TPA)
        ionic_strength = 3.0 * c_salt_molar
        gamma_1 = cls.calculate_activity_coeff(ionic_strength, charge_z=1)

        # Apparent equilibrium constants adjusted for ionic activity:
        # Ka1_app = Ka1 / gamma_1^2
        ka1_app = ka1 / (gamma_1 ** 2)
        ka2_app = ka2 / (gamma_1 ** 2)

        # Speciation polynomial: D = [H+]^2 + Ka1_app * [H+] + Ka1_app * Ka2_app
        denom = (h_plus ** 2) + (ka1_app * h_plus) + (ka1_app * ka2_app)
        alpha0 = (h_plus ** 2) / denom             # Neutral H2TPA fraction (crystallizable)
        alpha1 = (ka1_app * h_plus) / denom        # Mono-anion HTPA- fraction (soluble)
        alpha2 = (ka1_app * ka2_app) / denom       # Di-anion TPA2- fraction (soluble)

        # Total effective solubility in solution at this pH and T:
        # C_eff_sol = C*_intrinsic / alpha0
        total_effective_sol_g_l = intrinsic_sol_g_l / max(1e-6, alpha0)

        # 3. Supersaturation and Yield:
        # S = C_total / C_eff_sol
        supersaturation_s = initial_tpa_concentration_g_l / max(1e-6, total_effective_sol_g_l)

        if supersaturation_s > 1.0:
            precipitated_g_l = max(0.0, initial_tpa_concentration_g_l - total_effective_sol_g_l)
            yield_pct = (precipitated_g_l / initial_tpa_concentration_g_l) * 100.0
            mother_liquor_loss_pct = 100.0 - yield_pct
        else:
            yield_pct = 0.0
            mother_liquor_loss_pct = 100.0
            precipitated_g_l = 0.0

        # Stoichiometric sulfuric acid consumption & salt generation:
        # Na2TPA + H2SO4 -> H2TPA + Na2SO4
        # kg H2SO4 per kg TPA = 98.08 / 166.13 = 0.5904
        # Plus stoichiometric excess for pH suppression to target pH
        excess_acid_factor = 1.0 + (h_plus * cls.MW_H2SO4 / (2.0 * initial_tpa_concentration_g_l))
        h2so4_per_kg_tpa = (cls.MW_H2SO4 / cls.MW_TPA) * excess_acid_factor
        na2so4_per_kg_tpa = cls.MW_NA2SO4 / cls.MW_TPA

        # 4. Crystal Size Distribution and Cake Resistance (Carman-Kozeny):
        # High supersaturation (S >> 10) causes rapid homogeneous nucleation producing fine crystals
        # Controlled reactive crystallization (S ~ 2-5) produces larger 60-100 um needle crystals
        if supersaturation_s <= 1.0:
            d50_microns = 0.0
            regime = "NO_PRECIPITATION (UNDERSATURATED)"
            alpha_c = 0.0
            feasibility = "NOT_APPLICABLE"
        elif supersaturation_s > 25.0:
            regime = "HOMOGENEOUS_NUCLEATION_DOMINATED (CRITICAL BURST)"
            # Fine crystals ~8-15 um
            d50_microns = max(6.0, 75.0 * (supersaturation_s ** -0.45))
            feasibility = "HIGH_RESISTANCE (FINE PARTICLES / BLINDING RISK)"
        else:
            regime = "CONTROLLED_GROWTH_DOMINATED (SECONDARY NUCLEATION)"
            d50_microns = max(35.0, 110.0 * (supersaturation_s ** -0.30))
            feasibility = "FAVORABLE_RAPID_FILTRATION"

        # Carman-Kozeny specific cake resistance:
        # alpha_c = [ 180 * (1 - epsilon_c) ] / [ rho_s * d50^2 * epsilon_c^3 ]
        if d50_microns > 0.0:
            d50_m = d50_microns * 1e-6
            eps = cake_porosity
            alpha_c = (180.0 * (1.0 - eps)) / (cls.RHO_SOLID_TPA * (d50_m ** 2) * (eps ** 3))
        else:
            alpha_c = 0.0

        return PrecipitationThermodynamicOutputs(
            precipitation_temperature_c=temperature_c,
            target_ph=operating_ph,
            ionic_strength_molar=round(ionic_strength, 3),
            davies_activity_coeff=round(gamma_1, 3),
            neutral_tpa_fraction_alpha0=round(alpha0, 5),
            monoanion_fraction_alpha1=round(alpha1, 5),
            dianion_fraction_alpha2=round(alpha2, 5),
            intrinsic_solubility_g_l=round(intrinsic_sol_g_l, 4),
            total_effective_solubility_g_l=round(total_effective_sol_g_l, 4),
            initial_tpa_concentration_g_l=initial_tpa_concentration_g_l,
            supersaturation_ratio=round(supersaturation_s, 2),
            precipitation_yield_pct=round(yield_pct, 2),
            mother_liquor_loss_pct=round(mother_liquor_loss_pct, 2),
            h2so4_consumed_kg_per_kg_tpa=round(h2so4_per_kg_tpa, 4),
            byproduct_na2so4_kg_per_kg_tpa=round(na2so4_per_kg_tpa, 4),
            mean_crystal_diameter_microns=round(d50_microns, 2),
            specific_cake_resistance_m_kg=alpha_c,
            nucleation_regime=regime,
            filtration_feasibility=feasibility,
        )
