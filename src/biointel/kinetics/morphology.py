"""Anisotropic Flake Morphology & Lamellar Polymer Dissolution.

Models enzymatic depolymerization of real-world post-consumer PET particles:
1. Replaces isotropic shrinking sphere assumptions with high-aspect-ratio platelet/flake geometry.
2. Tracks aspect ratio AR(t) = L(t) / H(t) and dynamic shape factor S_f(t).
3. Accounts for anisotropic degradation: fast erosion of accessible amorphous tie-chains
   at edge faces vs restricted erosion of crystalline basal planes.
4. Predicts surface area evolution S_A(t) and particle fragmentation thresholds.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FlakeMorphologyOutputs:
    initial_length_microns: float
    initial_thickness_microns: float
    initial_aspect_ratio: float
    initial_shape_factor_sf: float
    crystallinity_pct: float
    face_erosion_velocity_um_per_hr: float
    edge_erosion_velocity_um_per_hr: float
    dissolution_time_hours: float
    surface_area_gain_vs_sphere_factor: float
    fragmentation_predicted: bool
    trajectory: List[Dict[str, float]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnisotropicFlakeMorphologyModel:
    """Rigorous 2D/3D morphological evolution engine for non-spherical polymer particles."""

    RHO_PET_G_CM3 = 1.38          # g / cm^3
    MW_ESTER = 192.17             # g / mol

    @classmethod
    def calculate_shape_factor(cls, length_um: float, thickness_um: float) -> float:
        """
        Calculates sphericity shape factor S_f = A_flake / A_equivalent_sphere.
        S_f = 1.0 for a perfect sphere; S_f > 1.0 for non-spherical high-aspect flakes.
        """
        if length_um <= 0.0 or thickness_um <= 0.0:
            return 1.0
        v_flake = (length_um ** 2) * thickness_um
        a_flake = 2.0 * (length_um ** 2) + 4.0 * length_um * thickness_um
        # Equivalent sphere radius
        r_eq = (3.0 * v_flake / (4.0 * math.pi)) ** (1.0 / 3.0)
        a_sphere = 4.0 * math.pi * (r_eq ** 2)
        return a_flake / max(1e-9, a_sphere)

    @classmethod
    def evaluate_flake_dissolution(
        cls,
        initial_length_microns: float = 250.0,
        initial_thickness_microns: float = 20.0,
        crystallinity_pct: float = 12.0,
        base_cleavage_velocity_um_per_hr: float = 1.2,
        amorphous_edge_acceleration_factor: float = 3.5,
        total_time_hours: float = 48.0,
        time_step_hours: float = 0.5,
    ) -> FlakeMorphologyOutputs:
        """
        Simulates anisotropic morphological erosion of a flat rectangular polymer flake.
        """
        xc = max(0.0, min(1.0, crystallinity_pct / 100.0))
        # Face erosion is restricted by crystalline lamellar fraction
        v_face = base_cleavage_velocity_um_per_hr * (1.0 - xc)
        # Edge erosion exposes amorphous inter-lamellar folds and tie chains
        v_edge = base_cleavage_velocity_um_per_hr * amorphous_edge_acceleration_factor * (1.0 - 0.3 * xc)

        curr_l = float(initial_length_microns)
        curr_h = float(initial_thickness_microns)
        initial_vol = (curr_l ** 2) * curr_h

        # Initial shape factor
        init_sf = cls.calculate_shape_factor(curr_l, curr_h)
        init_ar = curr_l / max(1e-6, curr_h)

        time = 0.0
        trajectory: List[Dict[str, float]] = []
        fragmentation_flag = False
        dissolution_time = total_time_hours

        while time <= total_time_hours:
            v_curr = max(0.0, (curr_l ** 2) * curr_h)
            conversion = max(0.0, min(1.0, 1.0 - (v_curr / initial_vol)))
            ar = curr_l / max(1e-6, curr_h)
            sf = cls.calculate_shape_factor(curr_l, curr_h)

            trajectory.append({
                "time_hours": round(time, 2),
                "length_microns": round(curr_l, 3),
                "thickness_microns": round(curr_h, 3),
                "aspect_ratio": round(ar, 2),
                "shape_factor_sf": round(sf, 3),
                "volume_remaining_fraction": round(1.0 - conversion, 4),
                "conversion_fraction": round(conversion, 4),
            })

            if curr_h <= 0.5 or curr_l <= 2.0:
                dissolution_time = time
                break

            # Mechanical flake fragmentation occurs when thickness erodes below critical limit
            if curr_h < 2.0 and not fragmentation_flag:
                fragmentation_flag = True

            # Advance erosion
            curr_h = max(0.0, curr_h - 2.0 * v_face * time_step_hours)
            curr_l = max(0.0, curr_l - 2.0 * v_edge * time_step_hours)
            time += time_step_hours

        # Surface area gain vs equivalent sphere of same volume
        v0 = (initial_length_microns ** 2) * initial_thickness_microns
        r_eq0 = (3.0 * v0 / (4.0 * math.pi)) ** (1.0 / 3.0)
        a_sphere0 = 4.0 * math.pi * (r_eq0 ** 2)
        a_flake0 = 2.0 * (initial_length_microns ** 2) + 4.0 * initial_length_microns * initial_thickness_microns
        sa_gain_factor = round(a_flake0 / max(1e-6, a_sphere0), 3)

        return FlakeMorphologyOutputs(
            initial_length_microns=initial_length_microns,
            initial_thickness_microns=initial_thickness_microns,
            initial_aspect_ratio=round(init_ar, 2),
            initial_shape_factor_sf=round(init_sf, 3),
            crystallinity_pct=crystallinity_pct,
            face_erosion_velocity_um_per_hr=round(v_face, 4),
            edge_erosion_velocity_um_per_hr=round(v_edge, 4),
            dissolution_time_hours=round(dissolution_time, 2),
            surface_area_gain_vs_sphere_factor=sa_gain_factor,
            fragmentation_predicted=fragmentation_flag,
            trajectory=trajectory,
        )
