"""Tests for BioIntel Chemical Engineering and Computational Advancements.

Validates:
1. BMED Electrochemical Salt Recovery (bmed.py)
2. Dynamic Membrane Fouling via Hermia's filtration laws (membrane_fouling.py)
3. Monte Carlo Technoeconomic Uncertainty Simulation (monte_carlo.py)
4. Non-Newtonian Slurry Rheology and Zwietering suspension (rheology.py)
5. Coupled Two-Enzyme Cascade Kinetics with MHET inhibition (cascade_kinetics.py)
6. Monoethylene Glycol Distillation and VLE Mass Balance (glycol_recovery.py)
7. Life Cycle Assessment (LCA) Scope 1-3 Carbon Footprint (lca.py)
8. Structural Superposition and Active Site RMSD (superposition.py)
9. Continuous Evidence Ingestion & Boundary Monitoring Daemon (monitor.py)
10. Database-driven snapshot generation (longitudinal.py)
11. Science visualization sidecar integration (visualizer.py)
"""

from __future__ import annotations

import math
import tempfile
from pathlib import Path

from biointel.discovery.monitor import ContinuousMonitoringDaemon
from biointel.economics.bmed import BipolarElectrodialysisModel
from biointel.economics.cascade_kinetics import CascadeKineticsModel
from biointel.economics.glycol_recovery import GlycolDistillationModel
from biointel.economics.lca import LifeCycleAssessmentModel
from biointel.economics.membrane_fouling import MembraneFoulingModel
from biointel.economics.monte_carlo import MonteCarloTEASimulator
from biointel.economics.rheology import SlurryRheologyModel
from biointel.evidence.longitudinal import (
    LongitudinalReplayEngine,
    PETaseHistoricalTrajectory,
)
from biointel.storage.database import Database
from biointel.structures.parser import PDBParser
from biointel.structures.superposition import StructureSuperposition
from biointel.structures.visualizer import StructureVisualizer


def test_bmed_electrochemical_salt_recovery():
    """Verify BMED mass balance, specific power, and chemical net economic recovery."""
    res = BipolarElectrodialysisModel.calculate_bmed_economics(
        scale_mt_tpa_year=50000.0,
        electricity_price_kwh=0.08,
    )

    # Stoichiometric sodium sulfate: 142.04 g/mol Na2SO4 / 166.13 g/mol TPA ~ 0.855 - 0.876 kg salt/kg TPA
    assert 0.85 <= res.sodium_sulfate_kg_per_kg_tpa <= 0.90
    # Specific energy should be ~0.9 - 2.0 kWh/kg salt
    assert 0.8 <= res.specific_energy_kwh_per_kg_salt <= 2.5
    # BMED power consumption per kg TPA: ~0.8 - 2.3 kWh/kg TPA
    assert 0.7 <= res.bmed_power_consumption_kwh_per_kg_tpa <= 2.6

    # NaOH and H2SO4 stoichiometric recovery
    assert res.recovered_naoh_kg_per_kg_tpa > 0.45
    assert res.recovered_h2so4_kg_per_kg_tpa > 0.55

    # Gross value should be ~$0.30-$0.35/kg TPA
    assert res.total_gross_savings_usd_per_kg_tpa > 0.30
    # Net economic benefit must be positive at $0.08/kWh electricity
    assert res.net_economic_benefit_usd_per_kg_tpa > 0.10
    assert res.is_economically_favorable is True
    assert res.breakeven_electricity_price_usd_per_kwh > 0.10

    # High electricity breakeven test
    expensive_res = BipolarElectrodialysisModel.calculate_bmed_economics(
        scale_mt_tpa_year=50000.0,
        electricity_price_kwh=0.50,
    )
    assert expensive_res.is_economically_favorable is False


def test_membrane_fouling_dynamic_decay():
    """Verify Hermia cake filtration law flux decay and CIP cleaning trigger."""
    res = MembraneFoulingModel.simulate_flux_decay(
        foulant_concentration_g_l=1.5,
        tmp_bar=3.0,
        terminal_flux_cutoff_pct=35.0,
        max_batch_time_hours=30.0,
    )

    # Initial flux should be reasonable for UF (50 - 1000 LMH)
    assert 50.0 < res.initial_flux_lmh < 1000.0
    # Monotonic decay
    assert res.terminal_flux_lmh < res.initial_flux_lmh
    assert res.average_flux_lmh < res.initial_flux_lmh
    assert res.permeate_volume_filtered_l_m2 > 0.0
    assert len(res.flux_trajectory) > 5

    # Check trajectory monotonic drop
    fluxes = [point["flux_lmh"] for point in res.flux_trajectory]
    for i in range(len(fluxes) - 1):
        assert fluxes[i] >= fluxes[i + 1]


def test_monte_carlo_tea_simulator():
    """Verify Monte Carlo simulation statistical consistency and quantile ordering."""
    res = MonteCarloTEASimulator.run_simulation(
        iterations=1000,
        random_seed=42,
        scale_mt_year=50000.0,
        enable_green_premium=True,
    )

    assert res.iterations == 1000
    assert res.p10_cost_usd_per_kg_tpa < res.p50_cost_usd_per_kg_tpa < res.p90_cost_usd_per_kg_tpa
    assert 1.0 < res.p50_cost_usd_per_kg_tpa < 2.5
    assert res.std_dev_usd_per_kg_tpa > 0.0
    # Parity probability should be between 0 and 100%
    assert 0.0 <= res.probability_commercial_parity_pct <= 100.0


def test_slurry_rheology_and_suspension():
    """Verify Zwietering off-bottom suspension speed and Herschel-Bulkley non-Newtonian viscosity."""
    res = SlurryRheologyModel.calculate_slurry_mixing(
        tank_volume_m3=40.0,
        solids_wt_pct=18.0,
        particle_diameter_mm=0.25,
    )

    # Off bottom suspension RPM
    assert 30.0 < res.zwietering_n_js_rpm < 120.0
    assert res.slurry_density_kg_m3 > 1000.0
    assert res.apparent_viscosity_pa_s > 0.001
    assert res.reynolds_number > 1000.0
    assert res.power_draw_kw > 1.0
    assert "SUSPENSION" in res.off_bottom_suspension_status


def test_coupled_cascade_kinetics():
    """Verify coupled PETase and MHETase ODE kinetics and competitive inhibition."""
    # Dual-enzyme cascade: PETase + MHETase
    dual_res = CascadeKineticsModel.simulate_cascade(
        initial_pet_mm=200.0,
        reaction_hours=24.0,
        petase_loading_um=2.0,
        mhetase_loading_um=2.0,
    )
    assert dual_res.final_conversion_pct > 70.0
    assert dual_res.final_tpa_produced_mm > 100.0
    assert dual_res.mhet_inhibition_factor < 15.0
    assert "EFFICIENT" in dual_res.kinetic_verdict

    # Single-enzyme: PETase alone (mhetase_loading_um = 0)
    single_res = CascadeKineticsModel.simulate_cascade(
        initial_pet_mm=200.0,
        reaction_hours=24.0,
        petase_loading_um=2.0,
        mhetase_loading_um=0.0,
    )
    # Without MHETase, MHET accumulates and severely inhibits PETase
    assert single_res.final_mhet_accumulated_mm > dual_res.final_mhet_accumulated_mm
    assert single_res.mhet_inhibition_factor > dual_res.mhet_inhibition_factor
    assert single_res.final_conversion_pct < dual_res.final_conversion_pct
    assert "INHIBITED" in single_res.kinetic_verdict or "STALLING" in single_res.kinetic_verdict


def test_glycol_distillation_and_vle():
    """Verify monoethylene glycol evaporation steam duty and solids loading breakeven."""
    res = GlycolDistillationModel.calculate_glycol_recovery(
        initial_solids_pct=16.0,
        steam_cost_per_kg=0.04,
        meg_market_price_kg=0.85,
    )

    assert abs(res.kg_eg_produced_per_kg_tpa - 0.3736) < 0.01
    assert res.water_evaporated_kg_per_kg_eg > 5.0
    assert res.evaporator_steam_duty_kg_per_kg_eg > 2.0
    assert res.total_steam_kg_per_kg_tpa > 1.0
    assert res.meg_market_value_usd_per_kg_tpa > 0.25
    assert res.solids_loading_breakeven_pct > 3.0 and res.solids_loading_breakeven_pct < 12.0
    assert res.is_glycol_recovery_profitable is True


def test_life_cycle_assessment_ghg():
    """Verify cradle-to-gate Scope 1-3 GHG footprint vs virgin PTA."""
    avg_grid = LifeCycleAssessmentModel.evaluate_carbon_footprint(
        grid_co2_kg_per_kwh=0.38,
        grid_region="US Average Grid",
    )
    assert avg_grid.virgin_petrochemical_pta_gwp_baseline == 1.95
    assert avg_grid.net_enzymatic_gwp_kg_co2e_per_kg_tpa < 1.95
    assert avg_grid.ghg_reduction_pct_vs_virgin > 20.0
    assert avg_grid.is_carbon_beneficial is True

    # Clean renewable grid
    clean_grid = LifeCycleAssessmentModel.evaluate_carbon_footprint(
        grid_co2_kg_per_kwh=0.04,
        grid_region="Hydro/Nuclear Renewable Grid",
    )
    assert clean_grid.net_enzymatic_gwp_kg_co2e_per_kg_tpa < avg_grid.net_enzymatic_gwp_kg_co2e_per_kg_tpa
    assert clean_grid.ghg_reduction_pct_vs_virgin > avg_grid.ghg_reduction_pct_vs_virgin


def test_structure_superposition_and_rmsd():
    """Verify structural superposition and catalytic triad displacement tracking."""
    # Use real pdb files in data/structures/
    p_7sh6 = PDBParser(Path("data/structures/7sh6.pdb"))
    p_7k38 = PDBParser(Path("data/structures/7k38.pdb"))

    # Self-comparison (RMSD must be 0)
    self_rep = StructureSuperposition.compare_structures(p_7sh6, p_7sh6)
    assert abs(self_rep.c_alpha_rmsd_angstrom) < 1e-4
    assert "ISOMORPHIC" in self_rep.structural_similarity_verdict

    # Divergent comparison (7SH6 vs 7K38 - different enzymes entirely)
    diverg_rep = StructureSuperposition.compare_structures(p_7sh6, p_7k38)
    assert "DISTINCT" in diverg_rep.structural_similarity_verdict or "HOMOLOGY" in diverg_rep.structural_similarity_verdict


def test_continuous_monitoring_daemon_boundary_check():
    """Verify monitoring daemon detects assay boundary violations and logs to SQLite."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tf:
        db = Database(tf.name)
        daemon = ContinuousMonitoringDaemon(db)

        # Ingest an assay test that violates boundary: 72 deg C on IsPETase (baseline 30 C, delta > 15 C)
        alert = daemon.evaluate_incoming_experiment(
            experiment_id="EXP-TEST-001",
            enzyme_variant="IsPETase-WT",
            assay_temp_c=72.0,
            assay_ph=7.5,
            substrate="crystallized_pet_pellets",
            source_doi="10.1038/s41586-test",
        )
        assert alert is not None
        assert alert["type"] == "INCOMPATIBLE_ASSAY_BOUNDARY"
        assert alert["severity"] in ("CRITICAL", "HIGH")

        # Check that it recorded in scientific_changes table
        changes = db.get_scientific_changes()
        assert len(changes) == 1
        assert "INCOMPATIBLE_ASSAY_BOUNDARY" in changes[0]["change_type"]

        # Compatible condition: 30 deg C on amorphous film
        alert_valid = daemon.evaluate_incoming_experiment(
            experiment_id="EXP-TEST-002",
            enzyme_variant="IsPETase-WT",
            assay_temp_c=30.0,
            assay_ph=7.5,
            substrate="amorphous_film",
            source_doi="10.1038/s41586-test2",
        )
        assert alert_valid is None


def test_generate_snapshot_from_db():
    """Verify longitudinal snapshot generation dynamically querying SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tf:
        db = Database(tf.name)
        engine = LongitudinalReplayEngine(db)
        engine.seed_historical_trajectory()
        snap = engine.generate_snapshot("fast_petase_depolymerase", "2022-06-01", "Snapshot 2022")
        assert snap.as_of_date == "2022-06-01"
        assert len(snap.structures) >= 3  # 5XJH, 6EQE, 7SH6 available in 2022


def test_science_sidecar_viewer_link():
    """Verify science visualization sidecar link adheres to user rule."""
    viz = StructureVisualizer()
    link = viz.get_sidecar_viewer_link("7SH6")
    assert link == "[Biomolecular Structure Viewer](sidecar://science/biomolecular_structure_viewer/ui.html)"
