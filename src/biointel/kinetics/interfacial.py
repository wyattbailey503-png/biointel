"""Interfacial Heterogeneous Enzymatic Polymer Hydrolysis Kinetics.

Models enzymatic depolymerization of solid, insoluble semi-crystalline PET:
1. Reversible Langmuir adsorption isotherm of soluble biocatalyst onto 2D polymer surface.
2. Steric exclusion of crystalline lamellae (amorphous accessibility factor 1 - Xc).
3. Productive vs non-productive enzyme binding partitioning.
4. Shrinking-core / eroding particle morphology tracking dynamic surface area S_A(t).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class InterfacialKineticsOutputs:
    initial_particle_radius_microns: float
    crystallinity_pct: float
    accessible_amorphous_fraction: float
    langmuir_k_ads_l_per_umol: float
    maximum_surface_adsorption_umol_m2: float
    free_enzyme_um: float
    adsorbed_enzyme_umol_m2: float
    surface_coverage_theta: float
    initial_specific_surface_area_m2_per_g: float
    surface_reaction_rate_umol_per_m2_s: float
    volumetric_cleavage_rate_mm_per_hr: float
    time_to_complete_dissolution_hours: float
    conversion_trajectory: List[Dict[str, float]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InterfacialPolymerKineticsModel:
    """Rigorous heterogeneous solid-liquid biocatalytic depolymerization model."""

    RHO_PET_G_CM3 = 1.38          # g / cm^3 (solid PET density)
    RHO_PET_KG_M3 = 1380.0        # kg / m^3
    MW_ESTER_UNIT = 192.17        # g / mol repeating PET monomer unit
    MOLAR_DENSITY_MOL_M3 = 1380000.0 / 192.17  # ~7181.1 mol ester bonds / m^3

    @classmethod
    def evaluate_interfacial_hydrolysis(
        cls,
        particle_radius_microns: float = 125.0,  # 250 um diameter flake/powder
        solids_concentration_g_l: float = 50.0,  # 50 g/L PET slurry
        enzyme_loading_um: float = 2.5,          # 2.5 uM enzyme in bulk liquid
        crystallinity_pct: float = 12.0,         # 12% crystalline (amorphous Xc < 5%, bottle flake 30-40%)
        langmuir_k_ads_l_per_umol: float = 0.85, # Langmuir affinity constant (L / umol)
        max_adsorption_umol_m2: float = 1.80,    # Max monolayer capacity (~1.8 umol enzyme / m^2)
        non_productive_fraction: float = 0.15,   # 15% non-productive binding to crystalline faces/dyes
        kcat_2d_surface_s_inv: float = 4.2,      # 2D turnover frequency (s^-1)
        duration_hours: float = 48.0,
        time_step_hours: float = 0.5,
    ) -> InterfacialKineticsOutputs:
        """
        Solves coupled Langmuir surface equilibrium and shrinking-core eroding geometry.
        """
        r0_m = particle_radius_microns * 1e-6
        xc = max(0.0, min(0.95, crystallinity_pct / 100.0))
        amorphous_factor = 1.0 - xc

        # Initial specific surface area for spherical/isometric particles:
        # A / m = (4*pi*R^2) / (4/3*pi*R^3 * rho) = 3 / (rho * R) [m^2 / kg] = 3 / (rho_g_cm3 * R_cm * 1e4)
        s_a_m2_per_g = 3.0 / (cls.RHO_PET_KG_M3 * r0_m) * 1e-3  # m^2 / g

        # Total available polymer surface area in reactor: A_total [m^2 / L] = solids_g_l * s_a_m2_per_g
        total_surface_m2_l = solids_concentration_g_l * s_a_m2_per_g
        amorphous_surface_m2_l = total_surface_m2_l * amorphous_factor

        # Langmuir Adsorption Isotherm:
        # Theta = K_ads * [E_free] / (1 + K_ads * [E_free])
        # Total enzyme balance: [E_total] = [E_free] + [E_ads]*A_total
        # Quadratic solution for [E_free]:
        # K_ads * [E_free]^2 + (1 + K_ads * A_tot * E_max - K_ads * [E_tot]) * [E_free] - [E_tot] = 0
        a_quad = langmuir_k_ads_l_per_umol
        b_quad = 1.0 + langmuir_k_ads_l_per_umol * (total_surface_m2_l * max_adsorption_umol_m2 - enzyme_loading_um)
        c_quad = -enzyme_loading_um

        discriminant = b_quad ** 2 - 4.0 * a_quad * c_quad
        e_free = max(0.0, (-b_quad + math.sqrt(max(0.0, discriminant))) / (2.0 * a_quad))
        theta = (langmuir_k_ads_l_per_umol * e_free) / (1.0 + langmuir_k_ads_l_per_umol * e_free)
        e_ads_total = theta * max_adsorption_umol_m2  # umol / m^2

        # Partition productive enzyme on amorphous accessible surface
        productive_theta = theta * (1.0 - non_productive_fraction) * amorphous_factor
        e_ads_prod = productive_theta * max_adsorption_umol_m2  # umol / m^2

        # 2D surface reaction rate: v_2D = kcat_2D * [E_ads_prod] [umol / m^2 / s]
        v_2d_umol_m2_s = kcat_2d_surface_s_inv * e_ads_prod
        v_2d_mol_m2_s = v_2d_umol_m2_s * 1e-6

        # Radial erosion rate: dR/dt = - v_2D / rho_molar [m / s]
        dr_dt_m_s = v_2d_mol_m2_s / cls.MOLAR_DENSITY_MOL_M3
        dr_dt_microns_hr = dr_dt_m_s * 1e6 * 3600.0

        # Estimated time to complete particle dissolution (tau = R0 / (dR/dt))
        tau_complete_hours = particle_radius_microns / dr_dt_microns_hr if dr_dt_microns_hr > 0 else 9999.0

        # Volumetric cleavage rate in bulk reactor [mM ester / hr]:
        # r_vol = v_2D [mol/m^2/s] * total_amorphous_area [m^2/L] * 3600 [s/hr] * 1000 [mM/(mol/L)]
        volumetric_rate_mm_hr = v_2d_mol_m2_s * amorphous_surface_m2_l * 3600.0 * 1000.0

        # Dynamic shrinking-core trajectory simulation
        current_r = particle_radius_microns
        trajectory: List[Dict[str, float]] = []
        n_steps = int(duration_hours / time_step_hours)

        for step in range(n_steps + 1):
            t_hr = step * time_step_hours
            if current_r > 0.0:
                # Shrinking core: R(t) = max(0, R0 - (dR/dt)*t)
                r_t = max(0.0, particle_radius_microns - dr_dt_microns_hr * t_hr)
                fractional_conversion = 1.0 - (r_t / particle_radius_microns) ** 3.0
                curr_surface_area = s_a_m2_per_g * (r_t / particle_radius_microns) ** 2.0
            else:
                r_t = 0.0
                fractional_conversion = 1.0
                curr_surface_area = 0.0

            trajectory.append({
                "time_hours": round(t_hr, 2),
                "particle_radius_microns": round(r_t, 3),
                "fractional_conversion_pct": round(fractional_conversion * 100.0, 2),
                "active_surface_area_m2_per_g": round(curr_surface_area, 4),
            })

            if r_t <= 0.0 and current_r > 0.0:
                current_r = 0.0

        return InterfacialKineticsOutputs(
            initial_particle_radius_microns=particle_radius_microns,
            crystallinity_pct=crystallinity_pct,
            accessible_amorphous_fraction=round(amorphous_factor, 3),
            langmuir_k_ads_l_per_umol=langmuir_k_ads_l_per_umol,
            maximum_surface_adsorption_umol_m2=max_adsorption_umol_m2,
            free_enzyme_um=round(e_free, 4),
            adsorbed_enzyme_umol_m2=round(e_ads_total, 4),
            surface_coverage_theta=round(theta, 4),
            initial_specific_surface_area_m2_per_g=round(s_a_m2_per_g, 4),
            surface_reaction_rate_umol_per_m2_s=round(v_2d_umol_m2_s, 6),
            volumetric_cleavage_rate_mm_per_hr=round(volumetric_rate_mm_hr, 4),
            time_to_complete_dissolution_hours=round(tau_complete_hours, 2),
            conversion_trajectory=trajectory,
        )

    @classmethod
    def evaluate_anisotropic_hydrolysis(
        cls,
        length_microns: float = 250.0,
        thickness_microns: float = 20.0,
        solids_concentration_g_l: float = 50.0,
        enzyme_loading_um: float = 2.5,
        crystallinity_pct: float = 12.0,
        duration_hours: float = 48.0,
    ):
        """Couples Langmuir 2D surface adsorption with 3D anisotropic flake morphology."""
        from biointel.kinetics.morphology import AnisotropicFlakeMorphologyModel

        # Baseline isotropic rate
        iso = cls.evaluate_interfacial_hydrolysis(
            particle_radius_microns=min(length_microns, thickness_microns * 5.0) / 2.0,
            solids_concentration_g_l=solids_concentration_g_l,
            enzyme_loading_um=enzyme_loading_um,
            crystallinity_pct=crystallinity_pct,
            duration_hours=duration_hours,
        )

        # Linear erosion velocity (um / hr)
        # 1 umol / m^2 / s = 1e-6 mol / m^2 / s
        # Mol density = 7181.1 mol / m^3 = 7.1811e-6 mol / (m^2 * um)
        v_um_hr = (iso.surface_reaction_rate_umol_per_m2_s / (cls.MOLAR_DENSITY_MOL_M3 * 1e-6)) * 3600.0

        return AnisotropicFlakeMorphologyModel.evaluate_flake_dissolution(
            initial_length_microns=length_microns,
            initial_thickness_microns=thickness_microns,
            crystallinity_pct=crystallinity_pct,
            base_cleavage_velocity_um_per_hr=v_um_hr,
            total_time_hours=duration_hours,
        )

