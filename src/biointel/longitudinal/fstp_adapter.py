"""FSTP Bottom-Up Integration Export Adapter.

Bridges BioIntel's first-principles biophysics, reaction kinetics, and unit-operation
techno-economic models into FSTP's macro S-curves, disruption engines, and prospective
prediction ledger.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from biointel.storage.database import Database
from biointel.economics.extrusion import ExtrusionTechnoEconomicModel
from biointel.economics.pinch_analysis import ThermalPinchAnalyzer
from biointel.economics.bmed import BipolarElectrodialysisModel
from biointel.kinetics.interfacial import InterfacialPolymerKineticsModel
from biointel.economics.mrna_lnp import MRNALNPTechnoEconomicModel


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "fstp_bottom_up_spec.v1.schema.json"


class FSTPBottomUpAdapter:
    """Exports standardized first-principles engineering models into FSTP's schema."""

    DEFAULT_FSTP_DIR = Path("/Users/wyattbailey/Desktop/Personal Projects/fstp-main/data/bottom_up_specs")

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or Database()

    def generate_petase_spec(
        self,
        scale_mt_pet_year: float = 50000.0,
        electricity_price_kwh: float = 0.08,
    ) -> Dict[str, Any]:
        """Generate bottom-up spec for enzymatic PET depolymerization."""
        # 1. Extrusion Pre-processing Stack
        ext_stack = ExtrusionTechnoEconomicModel.calculate_cost_stack(
            scale_mt_pet_year=scale_mt_pet_year,
            electricity_price_kwh=electricity_price_kwh,
            extruder_sec_kwh_kg=0.45,
            is_pilot_scale=False,
        )

        # 2. Electrochemical BMED Stack
        bmed = BipolarElectrodialysisModel.calculate_bmed_economics(
            scale_mt_tpa_year=scale_mt_pet_year * 0.865,
            electricity_price_kwh=electricity_price_kwh,
        )

        # 3. Thermal Pinch Utilities Target
        pinch = ThermalPinchAnalyzer.evaluate_plant_heat_integration(
            scale_mt_tpa_year=scale_mt_pet_year * 0.865,
            delta_t_min_k=10.0,
        )

        # 4. Heterogeneous Interfacial Kinetics & Boundary Layer
        kinetics = InterfacialPolymerKineticsModel.evaluate_interfacial_hydrolysis(
            particle_radius_microns=125.0,
            solids_concentration_g_l=50.0,
            enzyme_loading_um=2.5,
            crystallinity_pct=15.0,
            duration_hours=24.0,
        )

        # Cost stack decomposition ($/kg TPA)
        feedstock_cost = 0.35  # Sourced post-consumer baled PET scrap
        extrusion_cost = round(ext_stack.total_pretreatment_cost_usd_per_kg_tpa, 4)
        bmed_net_benefit = round(bmed.net_economic_benefit_usd_per_kg_tpa, 4)
        capex_deprec = 0.28
        labor_overhead = 0.16

        # Net unit production cost
        tpa_cost_floor = round(
            feedstock_cost + extrusion_cost + capex_deprec + labor_overhead - bmed_net_benefit, 2
        )

        return {
            "technology_id": "fast_petase_depolymerase",
            "domain": "industrial_biotechnology",
            "category": "enzymatic_plastics_recycling",
            "as_of_date": "2026-11-02",
            "scale_unit": "MT_per_year",
            "scale_value": float(scale_mt_pet_year),
            "thermodynamic_cost_floor_usd_per_unit": tpa_cost_floor,
            "cost_stack_usd_per_unit": {
                "feedstock_baled_pet": feedstock_cost,
                "extrusion_preprocessing": extrusion_cost,
                "bmed_salt_splitting_net": -bmed_net_benefit,
                "capex_depreciation": capex_deprec,
                "labor_and_plant_overhead": labor_overhead,
            },
            "physical_bottlenecks": {
                "limiting_regime": "INTRAPARTICLE_PORE_DIFFUSION",
                "thiele_modulus": 4.12,
                "effectiveness_factor": 0.38,
                "substance_crystallinity_limit_pct": 15.0,
                "aspect_ratio_shape_factor": 2.45,
                "final_conversion_pct": round(kinetics.conversion_trajectory[-1]["fractional_conversion_pct"], 2),
            },
            "utility_targets": {
                "minimum_hot_utility_steam_kw": round(pinch.minimum_hot_utility_kw, 2),
                "maximum_internal_heat_recovery_kw": round(pinch.maximum_internal_heat_recovery_kw, 2),
                "pinch_heat_recovery_fraction": round(pinch.energy_recovery_efficiency_pct / 100.0, 4),
                "pinch_temperature_hot_c": round(pinch.pinch_temperature_hot_c, 2),
                "pinch_temperature_cold_c": round(pinch.pinch_temperature_cold_c, 2),
            },
            "fstp_integration_metadata": {
                "confidence_tier": 2,
                "confidence_label": "Tier 2: Empirical / First-Principles Engineering Fit",
                "recommended_wrights_law_asymptote_usd": tpa_cost_floor,
                "incumbent_market_clearing_parity_ratio": round(tpa_cost_floor / 1.15, 2),
                "substitution_barrier": "Requires pre-extrusion amorphization when feedstock crystallinity > 15%",
            },
        }

    def generate_mrna_lnp_spec(
        self,
        annual_doses: float = 100_000_000.0,
        dose_mrna_ug: float = 100.0,
    ) -> Dict[str, Any]:
        """Generate bottom-up spec for therapeutic mRNA/LNP manufacturing."""
        lnp = MRNALNPTechnoEconomicModel.calculate_manufacturing_economics(
            annual_doses=annual_doses,
            dose_mrna_micrograms=dose_mrna_ug,
        )

        return {
            "technology_id": "mrna_lnp_platform",
            "domain": "genetic_medicine",
            "category": "nucleic_acid_therapeutics",
            "as_of_date": "2026-11-02",
            "scale_unit": "doses_per_year",
            "scale_value": float(annual_doses),
            "thermodynamic_cost_floor_usd_per_unit": lnp.total_cost_usd_per_dose,
            "cost_stack_usd_per_unit": {
                "enzymes_and_capping": lnp.enzymes_and_capping_usd_per_dose,
                "modified_nucleotides_m1psi": lnp.modified_nucleotides_usd_per_dose,
                "synthetic_lipids_sm102": lnp.synthetic_lipids_usd_per_dose,
                "single_use_consumables": lnp.single_use_consumables_usd_per_dose,
                "cleanroom_labor_overhead": lnp.cleanroom_labor_overhead_usd_per_dose,
                "capex_amortization": lnp.capex_amortization_usd_per_dose,
                "qc_release_testing": lnp.qc_release_testing_usd_per_dose,
            },
            "physical_bottlenecks": {
                "limiting_regime": lnp.limiting_regime,
                "damkohler_number": lnp.damkohler_number,
                "mixing_timescale_ms": lnp.microfluidic_mixing_time_ms,
                "encapsulation_efficiency_pct": lnp.encapsulation_efficiency_pct,
                "endosomal_escape_fraction_pct": lnp.endosomal_escape_fraction_pct,
                "polydispersity_index": lnp.polydispersity_index,
            },
            "utility_targets": {
                "storage_temperature_c": lnp.storage_temperature_c,
                "ethanol_residual_pct": lnp.ethanol_residual_pct,
                "cleanroom_air_exchanges_per_hour": 25.0,
            },
            "fstp_integration_metadata": {
                "confidence_tier": 2,
                "confidence_label": "Tier 2: Empirical / First-Principles Engineering Fit",
                "recommended_wrights_law_asymptote_usd": lnp.total_cost_usd_per_dose,
                "incumbent_market_clearing_parity_ratio": round(lnp.total_cost_usd_per_dose / 15.0, 3),
                "substitution_barrier": "Requires microfluidic Da < 1.0 to prevent uncontrolled lipid precipitation and cold-chain distribution",
            },
        }

    def validate_spec_schema(self, spec: Dict[str, Any]) -> bool:
        """Validate payload against canonical schema constraints."""
        required_keys = [
            "technology_id", "domain", "category", "as_of_date", "scale_unit",
            "scale_value", "thermodynamic_cost_floor_usd_per_unit", "cost_stack_usd_per_unit",
            "physical_bottlenecks", "utility_targets", "fstp_integration_metadata"
        ]
        for k in required_keys:
            if k not in spec:
                raise ValueError(f"Schema violation: missing required key '{k}'")

        if spec["thermodynamic_cost_floor_usd_per_unit"] < 0:
            raise ValueError("Schema violation: cost floor cannot be negative")

        if "limiting_regime" not in spec["physical_bottlenecks"]:
            raise ValueError("Schema violation: missing limiting_regime in physical_bottlenecks")

        return True

    def generate_bottom_up_spec(
        self,
        technology_id: str = "fast_petase_depolymerase",
        scale_mt_pet_year: float = 50000.0,
        electricity_price_kwh: float = 0.08,
    ) -> Dict[str, Any]:
        """Compute the fully reconciled bottom-up physical cost stack and bottleneck gates."""
        clean_tech = technology_id.strip().lower()

        if clean_tech in ("mrna_lnp_platform", "mrna_vaccines", "mrna"):
            spec_payload = self.generate_mrna_lnp_spec()
        else:
            spec_payload = self.generate_petase_spec(scale_mt_pet_year, electricity_price_kwh)

        # Backwards compatibility alias
        spec_payload["thermodynamic_cost_floor_usd_per_kg"] = spec_payload["thermodynamic_cost_floor_usd_per_unit"]
        spec_payload["cost_stack_usd_per_kg"] = spec_payload["cost_stack_usd_per_unit"]
        spec_payload["fstp_integration_metadata"]["recommended_wrights_law_asymptote_usd_kg"] = (
            spec_payload["fstp_integration_metadata"]["recommended_wrights_law_asymptote_usd"]
        )

        # Validate schema before sealing
        self.validate_spec_schema(spec_payload)

        # Deterministic provenance seal
        hash_seed = json.dumps(spec_payload, sort_keys=True)
        seal = f"SEAL_FSTP_{hashlib.sha256(hash_seed.encode('utf-8')).hexdigest()[:16].upper()}"
        spec_payload["model_provenance_seal"] = seal

        return spec_payload

    def export_fstp_spec(
        self,
        technology_id: str = "fast_petase_depolymerase",
        output_path: Optional[str | Path] = None,
        sync_to_fstp: bool = True,
    ) -> Path:
        """Export the FSTP bottom-up specification to a versioned JSON file and mirror to FSTP."""
        clean_tech = technology_id.strip().lower()
        spec = self.generate_bottom_up_spec(clean_tech)
        out_file = Path(output_path) if output_path else Path("outputs") / "exports" / f"fstp_bottom_up_{clean_tech}.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(spec, indent=2)
        out_file.write_text(content, encoding="utf-8")

        # File Bridge: If FSTP repository is detected, mirror specification & schema
        if sync_to_fstp and self.DEFAULT_FSTP_DIR.exists():
            fstp_target = self.DEFAULT_FSTP_DIR / f"fstp_bottom_up_{clean_tech}.json"
            schema_target = self.DEFAULT_FSTP_DIR / "schemas" / "fstp_bottom_up_spec.v1.schema.json"
            try:
                fstp_target.write_text(content, encoding="utf-8")
                if SCHEMA_PATH.exists():
                    schema_target.parent.mkdir(parents=True, exist_ok=True)
                    schema_target.write_text(SCHEMA_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass

        return out_file
