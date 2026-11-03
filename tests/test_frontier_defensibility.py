"""Frontier Defensibility Test Suite.

Validates the 4 frontier pillars of advanced bioprocess and genetic intelligence:
1. Anisotropic Flake Morphology & Lamellar Degradation (morphology.py)
2. Two-Zone Reactor Compartment Hydrodynamics & Mixing (compartment_mixing.py)
3. Intracellular Delivery, Endosomal Escape & Nuclear PK/PD (endosomal_escape.py)
4. Automated Cryptographic CI Certificate Verification (ci_verifier.py)
"""

from __future__ import annotations

import unittest
from pathlib import Path

from biointel.delivery.endosomal_escape import IntracellularDeliveryPKPDModel
from biointel.kinetics.compartment_mixing import TwoZoneReactorCompartmentModel
from biointel.kinetics.interfacial import InterfacialPolymerKineticsModel
from biointel.kinetics.morphology import AnisotropicFlakeMorphologyModel
from biointel.provenance.ci_verifier import AutomatedCertificateVerifier


class TestFrontierDefensibility(unittest.TestCase):
    """Test suite for advanced biophysical, transport, and cryptographic verifications."""

    def test_anisotropic_flake_morphology_and_aspect_ratio(self) -> None:
        """Verifies platelet flake geometry, shape factor, and preferential lamellar erosion."""
        # Initial flake: 250 um length x 20 um thickness (Aspect Ratio 12.5)
        res = AnisotropicFlakeMorphologyModel.evaluate_flake_dissolution(
            initial_length_microns=250.0,
            initial_thickness_microns=20.0,
            crystallinity_pct=15.0,
            base_cleavage_velocity_um_per_hr=1.2,
            amorphous_edge_acceleration_factor=3.5,
            total_time_hours=24.0,
        )

        self.assertEqual(res.initial_aspect_ratio, 12.5)
        # Non-spherical flake must have shape factor > 1.0 (typical 2.0 - 5.0)
        self.assertGreater(res.initial_shape_factor_sf, 2.0)
        # Edge erosion velocity must exceed face erosion velocity due to accessible amorphous folds
        self.assertGreater(res.edge_erosion_velocity_um_per_hr, res.face_erosion_velocity_um_per_hr)
        # High aspect ratio platelet has higher initial surface area than volume-equivalent sphere
        self.assertGreater(res.surface_area_gain_vs_sphere_factor, 1.5)
        # Thickness decays monotonically
        trajectory = res.trajectory
        self.assertGreater(len(trajectory), 5)
        self.assertLess(trajectory[-1]["thickness_microns"], trajectory[0]["thickness_microns"])

    def test_interfacial_anisotropic_coupling(self) -> None:
        """Verifies that interfacial engine couples Langmuir coverage with flake morphology."""
        flake_res = InterfacialPolymerKineticsModel.evaluate_anisotropic_hydrolysis(
            length_microns=200.0,
            thickness_microns=15.0,
            crystallinity_pct=10.0,
            duration_hours=24.0,
        )
        self.assertGreater(flake_res.face_erosion_velocity_um_per_hr, 0.0)
        self.assertGreater(flake_res.edge_erosion_velocity_um_per_hr, flake_res.face_erosion_velocity_um_per_hr)
        self.assertTrue(len(flake_res.trajectory) > 0)

    def test_two_zone_reactor_compartment_mixing(self) -> None:
        """Verifies two-zone compartment model in commercial 50 m^3 stirred reactor."""
        mix = TwoZoneReactorCompartmentModel.evaluate_compartment_mixing(
            vessel_volume_m3=50.0,
            impeller_diameter_m=1.35,
            impeller_speed_rpm=85.0,
            particle_diameter_microns=250.0,
        )

        # Total volume balance
        self.assertAlmostEqual(mix.impeller_volume_m3 + mix.bulk_volume_m3, mix.vessel_volume_m3, places=2)
        # Impeller zone dissipation must be dramatically higher than bulk zone
        self.assertGreater(mix.impeller_dissipation_w_m3, mix.bulk_dissipation_w_m3 * 5.0)
        # Local Sherwood number in impeller zone must exceed bulk zone
        self.assertGreater(mix.sherwood_impeller, mix.sherwood_bulk)
        self.assertGreater(mix.mass_transfer_coeff_impeller_m_s, mix.mass_transfer_coeff_bulk_m_s)
        # Segregation ratio must be > 1.0
        self.assertGreater(mix.segregation_ratio, 1.0)
        # Circulation time must be physically realistic (10s - 60s for 50 m^3)
        self.assertTrue(5.0 < mix.circulation_time_seconds < 120.0)

    def test_intracellular_delivery_and_endosomal_escape_barrier(self) -> None:
        """Verifies PK/PD delivery barriers and 98-99% endosomal entrapment constraint."""
        # 1. Hepatic parenchymal delivery (favorable ApoE targeting)
        liver_del = IntracellularDeliveryPKPDModel.evaluate_delivery_barriers(
            administered_dose_mg_per_kg=0.50,
            target_tissue="LIVER_HEPATOCYTES",
            endosomal_escape_efficiency=0.015,  # 1.5% escape benchmark
        )
        # 98.5% trapped in lysosomes
        self.assertAlmostEqual(liver_del.lysosomal_degradation_fraction, 0.985, places=3)
        # Total nuclear payload fraction is < 1% of total administered dose
        self.assertLess(liver_del.effective_nuclear_payload_fraction, 0.01)
        self.assertGreater(liver_del.effective_nuclear_payload_fraction, 0.001)
        self.assertIn("FEASIBLE FOR MONOGENIC DISORDER", liver_del.diligence_verdict)

        # 2. Extrahepatic CNS delivery without BBB-crossing technology
        cns_del = IntracellularDeliveryPKPDModel.evaluate_delivery_barriers(
            administered_dose_mg_per_kg=0.50,
            target_tissue="EXTRAHEPATIC_CNS",
        )
        self.assertLess(cns_del.target_organ_biodistribution_fraction, 0.01)
        self.assertIn("DELIVERY INFEASIBLE", cns_del.diligence_verdict)

    def test_automated_ci_certificate_verification(self) -> None:
        """Verifies that all studies and memos pass automated cryptographic verification."""
        root = Path(__file__).resolve().parent.parent
        summary = AutomatedCertificateVerifier.verify_all_study_packages(root)

        self.assertGreaterEqual(summary.total_certificates_checked, 4)
        self.assertTrue(summary.all_valid, f"Verification failed for: {[d for d in summary.details if not d.is_valid]}")
        self.assertEqual(summary.failure_count, 0)
        self.assertEqual(summary.successful_count, summary.total_certificates_checked)


if __name__ == "__main__":
    unittest.main()
