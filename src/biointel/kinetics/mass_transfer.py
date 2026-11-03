"""Non-Equilibrium Mass Transfer, Thiele Modulus & Reaction-Diffusion Boundaries.

Evaluates hydrodynamic external boundary layer film resistance (k_L, Sherwood correlation)
and intraparticle pore diffusion to compute Thiele modulus (Phi), Weisz-Prater criterion (Psi),
and internal/external effectiveness factors (eta_int, eta_ext).
Diagnoses whether reported laboratory or industrial depolymerization rates represent
intrinsic biocatalytic turnover or are confounded by mass transfer limitations.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class MassTransferDiagnostics:
    particle_diameter_microns: float
    reynolds_number_particle: float
    schmidt_number: float
    sherwood_number: float
    external_mass_transfer_coeff_m_s: float
    specific_interfacial_area_m2_m3: float
    kla_film_s_inv: float
    external_damkohler_number: float
    external_effectiveness_factor: float
    effective_diffusivity_m2_s: float
    thiele_modulus: float
    weisz_prater_criterion: float
    internal_effectiveness_factor: float
    overall_effectiveness_factor: float
    controlling_regime: str
    engineering_guidance: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MassTransferBoundaryEngine:
    """Rigorous chemical reaction engineering mass transfer diagnostics."""

    DIFFUSIVITY_WATER_M2_S = 7.5e-10   # Diffusivity of small solute (MHET/EG/TPA) in water at 50-65 °C
    DIFFUSIVITY_ENZYME_M2_S = 6.2e-11  # Diffusivity of ~30 kDa globular PETase enzyme
    RHO_WATER_KG_M3 = 1000.0
    MU_WATER_PA_S = 0.00055             # Viscosity of water at 50 °C (0.55 cP)

    @classmethod
    def evaluate_transport_limitations(
        cls,
        particle_diameter_microns: float = 250.0,
        solids_wt_percent: float = 15.0,
        specific_power_dissipation_w_m3: float = 250.0, # ~0.25 kW/m^3 typical industrial mixing
        observed_reaction_rate_mol_m3_s: float = 0.015, # Observed volumetric depolymerization rate
        bulk_solute_concentration_mol_m3: float = 5.0,  # Intermediate concentration in bulk
        particle_porosity: float = 0.25,                 # Void fraction of degrading porous polymer flake
        tortuosity_factor: float = 3.5,                 # Pore tortuosity
    ) -> MassTransferDiagnostics:
        """
        Computes non-equilibrium boundary layer film transfer and intraparticle Thiele modulus.
        """
        dp_m = particle_diameter_microns * 1e-6
        rp_m = dp_m / 2.0

        # Kinematic viscosity: nu = mu / rho
        nu_m2_s = cls.MU_WATER_PA_S / cls.RHO_WATER_KG_M3
        d_ab = cls.DIFFUSIVITY_WATER_M2_S

        # 1. Kolmogoroff Microscale Turbulent Slip Velocity:
        # u_slip = (epsilon * nu)^0.25
        epsilon_w_kg = specific_power_dissipation_w_m3 / cls.RHO_WATER_KG_M3
        u_kolmogoroff = (epsilon_w_kg * nu_m2_s) ** 0.25
        u_slip = max(0.01, u_kolmogoroff)  # m/s

        # Particle Reynolds number: Re_p = u_slip * d_p / nu
        re_p = (u_slip * dp_m) / nu_m2_s
        # Schmidt number: Sc = nu / D_AB
        sc = nu_m2_s / d_ab

        # Ranz-Marshall / Froessling Sherwood correlation:
        # Sh = 2.0 + 0.6 * Re_p^0.5 * Sc^0.333
        sh = 2.0 + 0.6 * (re_p ** 0.5) * (sc ** (1.0 / 3.0))

        # External film mass transfer coefficient: k_L = Sh * D_AB / d_p [m / s]
        k_l = (sh * d_ab) / dp_m

        # Specific interfacial external surface area per unit reactor volume:
        # a = 6 * phi_solids / d_p [m^2 / m^3 reactor]
        rho_pet = 1380.0
        # Volume fraction of solids from wt%
        w_s = solids_wt_percent / 100.0
        vol_fraction_solids = (w_s / rho_pet) / ((w_s / rho_pet) + ((1.0 - w_s) / cls.RHO_WATER_KG_M3))
        a_interfacial = (6.0 * vol_fraction_solids) / dp_m  # m^2 / m^3

        kla = k_l * a_interfacial  # s^-1

        # External Damköhler number: Da_ext = r_obs / (k_L * a * C_b)
        c_bulk = max(0.001, bulk_solute_concentration_mol_m3)
        max_external_flux = kla * c_bulk
        da_ext = observed_reaction_rate_mol_m3_s / max(1e-9, max_external_flux)

        # External film effectiveness factor: eta_ext = 1 / (1 + Da_ext)
        eta_ext = 1.0 / (1.0 + da_ext)

        # 2. Intraparticle Diffusion & Thiele Modulus:
        # Effective diffusivity: D_eff = D_AB * (porosity / tortuosity)
        d_eff = d_ab * (particle_porosity / tortuosity_factor)

        # Equivalent pseudo-first order rate constant: k_v = r_obs / C_b [s^-1]
        k_volumetric = observed_reaction_rate_mol_m3_s / c_bulk

        # Characteristic diffusion length for sphere: L_c = R_p / 3
        # Generalized Thiele Modulus: Phi = (R_p / 3) * sqrt(k_v / D_eff)
        # Note: Some conventions use Phi = R_p * sqrt(k_v / D_eff)
        thiele_phi = rp_m * math.sqrt(max(0.0, k_volumetric / d_eff))

        # Internal effectiveness factor for spherical particle:
        # eta_int = (3 / Phi) * [ (1 / tanh(Phi)) - (1 / Phi) ]
        if thiele_phi < 0.05:
            eta_int = 1.0 - (thiele_phi ** 2) / 15.0
        elif thiele_phi > 30.0:
            eta_int = 3.0 / thiele_phi
        else:
            eta_int = (3.0 / thiele_phi) * ((1.0 / math.tanh(thiele_phi)) - (1.0 / thiele_phi))
        eta_int = max(0.001, min(1.0, eta_int))

        # Weisz-Prater Criterion: Psi = r_obs * R_p^2 / (D_eff * C_surface)
        # C_surface = eta_ext * C_bulk
        c_surface = max(1e-6, eta_ext * c_bulk)
        weisz_prater_psi = (observed_reaction_rate_mol_m3_s * (rp_m ** 2)) / (d_eff * c_surface)

        # Overall effectiveness factor: eta_overall = eta_ext * eta_int
        eta_overall = eta_ext * eta_int

        # Diagnostic classification:
        if eta_overall > 0.90:
            regime = "REACTION_LIMITED (INTRINSIC KINETICS REGIME)"
            guidance = (
                "Observed depolymerization rate is >90% governed by intrinsic enzymatic catalysis. "
                "Reported turnover rates can be safely scaled to commercial reactors."
            )
        elif eta_int < 0.50 and eta_ext >= 0.80:
            regime = "INTERNAL_PORE_DIFFUSION_LIMITED"
            guidance = (
                f"Severe intraparticle pore diffusion resistance (eta_int = {eta_int:.2f}, Phi = {thiele_phi:.2f}). "
                "Adding more enzyme yields diminishing returns. Micronization to smaller particle diameter required."
            )
        elif eta_ext < 0.50:
            regime = "EXTERNAL_BOUNDARY_FILM_LIMITED"
            guidance = (
                f"External stagnant liquid film boundary layer limits transport (eta_ext = {eta_ext:.2f}, Da = {da_ext:.2f}). "
                "Increase agitator power dissipation or impeller tip speed to shrink boundary layer."
            )
        else:
            regime = "MIXED_TRANSPORT_REACTION_REGIME"
            guidance = (
                f"Mixed regime (eta_overall = {eta_overall:.2f}). "
                "Both boundary layer mass transfer and internal pore resistance attenuate intrinsic biocatalytic rate."
            )

        return MassTransferDiagnostics(
            particle_diameter_microns=particle_diameter_microns,
            reynolds_number_particle=round(re_p, 2),
            schmidt_number=round(sc, 1),
            sherwood_number=round(sh, 2),
            external_mass_transfer_coeff_m_s=round(k_l, 6),
            specific_interfacial_area_m2_m3=round(a_interfacial, 1),
            kla_film_s_inv=round(kla, 4),
            external_damkohler_number=round(da_ext, 4),
            external_effectiveness_factor=round(eta_ext, 3),
            effective_diffusivity_m2_s=d_eff,
            thiele_modulus=round(thiele_phi, 3),
            weisz_prater_criterion=round(weisz_prater_psi, 3),
            internal_effectiveness_factor=round(eta_int, 3),
            overall_effectiveness_factor=round(eta_overall, 3),
            controlling_regime=regime,
            engineering_guidance=guidance,
        )
