"""Exhaustive PhD Defensibility Verification Suite.

Validates the 5 foundational scientific and software pillars:
1. Interfacial Heterogeneous Polymer Kinetics (interfacial.py)
2. Non-Equilibrium Mass Transfer & Thiele Modulus (mass_transfer.py)
3. Adaptive Stiff ODE Integrator with Invariant Conservation (integrator.py)
4. Non-Ideal Electrolyte Reactive Crystallization (precipitation.py)
5. Macromolecular Folding Thermodynamics & Delta-Delta-G (thermodynamics.py)
6. Systematic Review Cochrane RoB 2.0 & Meta-Analysis Heterogeneity (meta_analysis.py)
7. Bibliometric Replication Network & Pseudo-Replication Detection (replication_network.py)
8. Thermodynamic Thermal Pinch Integration (pinch_analysis.py)
9. Cryptographic Audit Trail & Reproducibility Certification (audit_trail.py)
"""

from __future__ import annotations

import math
from pathlib import Path

from biointel.biophysics.thermodynamics import EnzymeFoldingThermodynamicsModel
from biointel.crystallization.precipitation import ReactiveCrystallizationModel
from biointel.economics.pinch_analysis import ThermalPinchAnalyzer
from biointel.evidence.meta_analysis import MetaAnalysisEngine, StudyEffectRecord
from biointel.evidence.replication_network import (
    PublicationMetadataNode,
    ReplicationNetworkAnalyzer,
)
from biointel.kinetics.integrator import AdaptiveRK4Integrator
from biointel.kinetics.interfacial import InterfacialPolymerKineticsModel
from biointel.kinetics.mass_transfer import MassTransferBoundaryEngine
from biointel.provenance.audit_trail import ComputationalAuditTrail


def test_interfacial_polymer_kinetics_heterogeneous():
    """Verify 2D Langmuir adsorption and crystallinity steric restriction."""
    # Amorphous film (Xc = 5%)
    res_amorphous = InterfacialPolymerKineticsModel.evaluate_interfacial_hydrolysis(
        particle_radius_microns=100.0,
        crystallinity_pct=5.0,
        enzyme_loading_um=2.5,
    )
    assert res_amorphous.surface_coverage_theta > 0.0 and res_amorphous.surface_coverage_theta < 1.0
    assert res_amorphous.accessible_amorphous_fraction == 0.95
    assert res_amorphous.time_to_complete_dissolution_hours > 0.0

    # Bottle flake (Xc = 35%)
    res_crystalline = InterfacialPolymerKineticsModel.evaluate_interfacial_hydrolysis(
        particle_radius_microns=100.0,
        crystallinity_pct=35.0,
        enzyme_loading_um=2.5,
    )
    assert res_crystalline.accessible_amorphous_fraction == 0.65
    # High crystallinity must reduce volumetric cleavage rate significantly
    assert res_crystalline.volumetric_cleavage_rate_mm_per_hr < res_amorphous.volumetric_cleavage_rate_mm_per_hr
    # Time to complete dissolution must be longer for crystalline PET
    assert res_crystalline.time_to_complete_dissolution_hours > res_amorphous.time_to_complete_dissolution_hours

    # Monotonic particle radius decay in trajectory
    radii = [pt["particle_radius_microns"] for pt in res_amorphous.conversion_trajectory]
    for i in range(len(radii) - 1):
        assert radii[i] >= radii[i + 1]


def test_mass_transfer_and_thiele_modulus_regimes():
    """Verify Thiele modulus scaling and reaction vs diffusion regime diagnostics."""
    # 1. Micronized fine powder (30 microns): should be reaction limited
    res_fine = MassTransferBoundaryEngine.evaluate_transport_limitations(
        particle_diameter_microns=30.0,
        solids_wt_percent=15.0,
        observed_reaction_rate_mol_m3_s=0.005,
    )
    assert res_fine.thiele_modulus < 1.0
    assert res_fine.internal_effectiveness_factor > 0.90
    assert res_fine.overall_effectiveness_factor > 0.85
    assert "REACTION_LIMITED" in res_fine.controlling_regime

    # 2. Coarse unmicronized flake (1500 microns): severe internal pore diffusion limitation
    res_coarse = MassTransferBoundaryEngine.evaluate_transport_limitations(
        particle_diameter_microns=1500.0,
        solids_wt_percent=15.0,
        observed_reaction_rate_mol_m3_s=0.08,
    )
    assert res_coarse.thiele_modulus > 3.0
    assert res_coarse.internal_effectiveness_factor < 0.50
    assert res_coarse.overall_effectiveness_factor < 0.60
    assert "LIMITED" in res_coarse.controlling_regime


def test_adaptive_rk4_mass_conservation_invariants():
    """Verify adaptive RK4 integrator enforces exact carbon-mole conservation."""
    # A -> B -> C reaction network:
    # d[A]/dt = -k1 * [A]
    # d[B]/dt = k1 * [A] - k2 * [B]
    # d[C]/dt = k2 * [B]
    # Total mass / carbon [A] + [B] + [C] must be strictly invariant
    k1 = 1.2
    k2 = 0.8

    def derivatives(t: float, y: list[float]) -> list[float]:
        a, b, c = y[0], y[1], y[2]
        r1 = k1 * a
        r2 = k2 * b
        return [-r1, r1 - r2, r2]

    res = AdaptiveRK4Integrator.integrate(
        derivative_fn=derivatives,
        initial_state=[100.0, 0.0, 0.0],
        state_names=["A", "B", "C"],
        t_start=0.0,
        t_end=5.0,
        initial_step_size=0.05,
        tolerance=1e-5,
        stoichiometric_weights=[1.0, 1.0, 1.0],  # Conserved sum = 100.0
    )

    assert res.is_mass_conserved is True
    assert res.maximum_invariant_error < 1e-4
    # Final A should be mostly consumed, C accumulated
    final_a = res.state_trajectories["A"][-1]
    final_c = res.state_trajectories["C"][-1]
    assert final_a < 1.0
    assert final_c > 90.0
    assert abs((final_a + res.state_trajectories["B"][-1] + final_c) - 100.0) < 0.01


def test_reactive_crystallization_and_speciation():
    """Verify pH-dependent diprotic speciation, supersaturation, and cake resistance."""
    # Alkaline hydrolysate (pH 8.5): completely dissolved, zero precipitation
    res_alkaline = ReactiveCrystallizationModel.evaluate_acid_precipitation(
        initial_tpa_concentration_g_l=60.0,
        operating_ph=8.5,
        temperature_c=60.0,
    )
    assert res_alkaline.dianion_fraction_alpha2 > 0.99
    assert res_alkaline.neutral_tpa_fraction_alpha0 < 1e-4
    assert res_alkaline.precipitation_yield_pct == 0.0

    # Acidified to pH 2.2: >99% neutral H2TPA, high precipitation yield
    res_acidic = ReactiveCrystallizationModel.evaluate_acid_precipitation(
        initial_tpa_concentration_g_l=60.0,
        operating_ph=2.2,
        temperature_c=60.0,
    )
    assert res_acidic.neutral_tpa_fraction_alpha0 > 0.90
    assert res_acidic.precipitation_yield_pct > 95.0
    assert res_acidic.supersaturation_ratio > 10.0
    assert res_acidic.mean_crystal_diameter_microns > 5.0
    assert res_acidic.specific_cake_resistance_m_kg > 1e9
    assert 0.58 < res_acidic.h2so4_consumed_kg_per_kg_tpa < 0.65


def test_enzyme_folding_thermodynamics_and_ddg():
    """Verify Gibbs-Helmholtz thermal unfolding curve and mutation Delta-Delta-G."""
    # 1. Wild-type IsPETase at 65 °C (well above Tm 48.8 °C): severely unfolded
    wt_65c = EnzymeFoldingThermodynamicsModel.evaluate_variant_thermostability(
        variant_name="IsPETase-WT",
        operating_temperature_c=65.0,
    )
    assert wt_65c.fraction_native_folded < 0.05
    assert wt_65c.functional_half_life_hours < 1.0
    assert "UNSTABLE" in wt_65c.thermostability_verdict

    # 2. FAST-PETase at 50 °C (below Tm 68.2 °C): folded and stable
    fast_50c = EnzymeFoldingThermodynamicsModel.evaluate_variant_thermostability(
        variant_name="FAST-PETase",
        operating_temperature_c=50.0,
    )
    assert fast_50c.fraction_native_folded > 0.95
    assert fast_50c.functional_half_life_hours > 24.0
    assert fast_50c.delta_delta_g_vs_wt_kj_per_mol > 20.0
    assert "THERMOSTABLE" in fast_50c.thermostability_verdict

    # 3. LCC-ICCG at 72 °C (below Tm 94.5 °C): extreme stability
    lcc_72c = EnzymeFoldingThermodynamicsModel.evaluate_variant_thermostability(
        variant_name="LCC-ICCG",
        operating_temperature_c=72.0,
    )
    assert lcc_72c.fraction_native_folded > 0.95
    assert lcc_72c.delta_delta_g_vs_wt_kj_per_mol > 50.0


def test_meta_analysis_heterogeneity_and_publication_bias():
    """Verify DerSimonian-Laird pooling, Higgins I^2 heterogeneity, and Egger's test."""
    # Consistent concordant studies (low heterogeneity)
    consistent_studies = [
        StudyEffectRecord("S1", "10.1038/s1", 2022, "FAST-PETase", 12.4, 0.45, 4, "HPLC_QUANTITATIVE", True, 50.0, 10.0),
        StudyEffectRecord("S2", "10.1038/s2", 2023, "FAST-PETase", 11.8, 0.52, 3, "HPLC_QUANTITATIVE", True, 50.0, 10.0),
        StudyEffectRecord("S3", "10.1038/s3", 2023, "FAST-PETase", 13.1, 0.60, 4, "HPLC_QUANTITATIVE", True, 50.0, 10.0),
    ]
    meta_cons = MetaAnalysisEngine.run_meta_analysis(consistent_studies)
    assert meta_cons.higgins_i2_pct < 50.0
    assert meta_cons.is_statistically_poolable is True
    assert 11.5 < meta_cons.pooled_effect_random_effects < 13.0

    # Discordant studies with incompatible crystallinities / assays (extreme heterogeneity)
    discordant_studies = [
        StudyEffectRecord("S1", "10.1038/s1", 2022, "FAST-PETase", 12.4, 0.20, 4, "HPLC_QUANTITATIVE", True, 50.0, 5.0),
        StudyEffectRecord("S4", "10.1038/s4", 2023, "FAST-PETase", 1.1, 0.15, 3, "HPLC_QUANTITATIVE", True, 50.0, 35.0),
        StudyEffectRecord("S5", "10.1038/s5", 2024, "FAST-PETase", 24.5, 0.35, 3, "UV_VIS_SPECTROPHOTOMETRY", False, 65.0, 0.0),
    ]
    meta_disc = MetaAnalysisEngine.run_meta_analysis(discordant_studies)
    assert meta_disc.higgins_i2_pct > 75.0
    assert meta_disc.is_statistically_poolable is False
    assert "SUBSTANTIAL_HETEROGENEITY" in meta_disc.heterogeneity_classification


def test_replication_network_pseudo_replication_detection():
    """Verify co-authorship graph detects internal circular replication vs genuine external replication."""
    pub_yoshida = PublicationMetadataNode(
        doi="10.1126/science.aad6359",
        title="A bacterium that degrades and assimilates poly(ethylene terephthalate)",
        year=2016,
        authors=["Yoshida, S.", "Hiraga, K.", "Takehana, T.", "Taniguchi, I.", "Oda, K."],
        senior_author="Oda, K.",
        affiliations=["Kyoto Institute of Technology"],
        grant_numbers=["JSPS-12345"],
        patent_assignees=["KIT"],
    )

    # Same lab follow-up (shared senior author Oda, K.)
    pub_internal = PublicationMetadataNode(
        doi="10.1002/cbic.201700394",
        title="Further characterization of Ideonella sakaiensis PETase",
        year=2018,
        authors=["Hiraga, K.", "Taniguchi, I.", "Oda, K."],
        senior_author="Oda, K.",
        affiliations=["Kyoto Institute of Technology"],
        grant_numbers=["JSPS-12345"],
        patent_assignees=["KIT"],
    )

    # Genuine external replication (Austin et al., PNAS 2018 - Portsmouth / NREL)
    pub_external = PublicationMetadataNode(
        doi="10.1073/pnas.1718804115",
        title="Characterization and engineering of a plastic-degrading aromatic polyesterase",
        year=2018,
        authors=["Austin, H.P.", "Allen, M.D.", "Beckham, G.T.", "McGeehan, J.E."],
        senior_author="McGeehan, J.E.",
        affiliations=["University of Portsmouth", "NREL"],
        grant_numbers=["DOE-EERE-BETO"],
        patent_assignees=[],
    )

    # Audit pair 1: Internal follow-up
    audit_int = ReplicationNetworkAnalyzer.audit_replication_pair(pub_yoshida, pub_internal)
    assert audit_int.is_senior_author_shared is True
    assert audit_int.reproducibility_weight <= 0.30
    assert "INTERNAL" in audit_int.replication_classification

    # Audit pair 2: Genuine external
    audit_ext = ReplicationNetworkAnalyzer.audit_replication_pair(pub_yoshida, pub_external)
    assert audit_ext.is_senior_author_shared is False
    assert len(audit_ext.shared_authors) == 0
    assert audit_ext.reproducibility_weight == 1.00
    assert "GENUINE_EXTERNAL" in audit_ext.replication_classification

    # Full network
    net_summary = ReplicationNetworkAnalyzer.analyze_technology_network([pub_yoshida, pub_internal, pub_external])
    assert net_summary.total_publications == 3
    assert net_summary.genuine_external_replications_count >= 1
    assert net_summary.internal_followup_count >= 1


def test_thermal_pinch_heat_integration():
    """Verify thermal pinch calculation, hot/cold utility targets, and steam savings."""
    pinch = ThermalPinchAnalyzer.evaluate_plant_heat_integration(
        scale_mt_tpa_year=50000.0,
        delta_t_min_k=10.0,
    )
    # Minimum hot utility must be less than total cold duty due to heat recovery
    assert pinch.minimum_hot_utility_kw < pinch.total_cold_duty_required_kw
    assert pinch.maximum_internal_heat_recovery_kw > 1000.0  # >1 MW recovered
    assert pinch.energy_recovery_efficiency_pct > 40.0
    assert pinch.steam_cost_savings_usd_per_year > 100000.0  # >$100k/yr saved
    assert pinch.avoided_boiler_ghg_mt_co2e_per_year > 500.0
    assert "PINCH CONFIRMED" in pinch.pinch_verdict


def test_computational_audit_trail_provenance_seal():
    """Verify cryptographic SHA-256 computation seal and tamper detection."""
    inputs = {"scale_mt": 50000.0, "titer_g_l": 45.0, "solvent": "water"}
    outputs = {"cost_per_kg": 1.48, "yield_pct": 92.5}

    cert = ComputationalAuditTrail.generate_certificate(
        model_name="TEA_Enzymatic_Recycling",
        model_version="2.1.0",
        inputs=inputs,
        outputs=outputs,
        random_seed=42,
        notes="PhD defensibility benchmark",
    )

    assert cert.certificate_id.startswith("CERT-TEA_ENZY-")
    assert len(cert.computation_seal_sha256) == 64
    # Valid integrity check
    assert cert.verify_integrity(inputs, outputs) is True

    # Tampered inputs check
    tampered_inputs = dict(inputs)
    tampered_inputs["scale_mt"] = 60000.0
    assert cert.verify_integrity(tampered_inputs, outputs) is False

    # Tampered outputs check
    tampered_outputs = dict(outputs)
    tampered_outputs["cost_per_kg"] = 0.99
    assert cert.verify_integrity(inputs, tampered_outputs) is False
