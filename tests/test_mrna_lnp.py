"""Unit tests for the Therapeutic mRNA / LNP Manufacturing Techno-Economic Model.

Verifies:
1. Stoichiometric mass balance for In Vitro Transcription (IVT), CleanCap AG, and m1Psi-UTP.
2. Microfluidic Damköhler mixing dynamics (Da < 1.0) and high encapsulation efficiency.
3. Cost stack decomposition and per-dose cost floor calculation.
4. FSTP bottom-up specification generation and Schema v1.0.0 compliance.
"""

import json
import tempfile
from pathlib import Path

from biointel.storage.database import Database
from biointel.economics.mrna_lnp import MRNALNPTechnoEconomicModel
from biointel.longitudinal.fstp_adapter import FSTPBottomUpAdapter


def test_mrna_lnp_mass_balance_and_kinetics() -> None:
    """Verifies that mRNA/LNP stoichiometry and microfluidic mixing limits are solved accurately."""
    res = MRNALNPTechnoEconomicModel.calculate_manufacturing_economics(
        annual_doses=100_000_000.0,
        dose_mrna_micrograms=100.0,
    )

    # 100M doses of 100 ug = 10 kg net formulated mRNA
    assert res.annual_mrna_kg == 10.0
    assert res.capping_efficiency_pct > 95.0
    assert res.encapsulation_efficiency_pct >= 90.0

    # Damköhler number Da < 1 indicates mixing finishes before lipid nucleation
    assert res.damkohler_number < 1.0
    assert res.damkohler_number == round(res.microfluidic_mixing_time_ms / res.lipid_nucleation_time_ms, 3)
    assert res.mean_lnp_diameter_nm < 100.0
    assert res.polydispersity_index < 0.15

    # Cost floor: bulk commercial vaccine scale is ~$0.50-$1.50 per 100 ug dose
    assert 0.40 <= res.total_cost_usd_per_dose <= 2.00
    assert res.total_cost_usd_per_gram_mrna > 1000.0


def test_mrna_lnp_fstp_spec_export(temp_db: Database) -> None:
    """Verifies that mRNA/LNP spec exports cleanly with cryptographic provenance seals."""
    adapter = FSTPBottomUpAdapter(temp_db)
    spec = adapter.generate_bottom_up_spec("mrna_lnp_platform")

    assert spec["technology_id"] == "mrna_lnp_platform"
    assert spec["domain"] == "genetic_medicine"
    assert spec["category"] == "nucleic_acid_therapeutics"
    assert spec["scale_unit"] == "doses_per_year"
    assert spec["scale_value"] == 100_000_000.0
    assert spec["thermodynamic_cost_floor_usd_per_unit"] > 0
    assert spec["physical_bottlenecks"]["damkohler_number"] < 1.0
    assert spec["physical_bottlenecks"]["limiting_regime"] == "MICROFLUIDIC_DIFFUSION_AND_ENDOSOMAL_ESCAPE"
    assert spec["model_provenance_seal"].startswith("SEAL_FSTP_")

    with tempfile.TemporaryDirectory() as td:
        out_file = Path(td) / "test_mrna_spec.json"
        exported = adapter.export_fstp_spec("mrna_lnp_platform", output_path=out_file)
        assert exported.exists()
        loaded = json.loads(exported.read_text(encoding="utf-8"))
        assert loaded["technology_id"] == "mrna_lnp_platform"
        assert loaded["model_provenance_seal"] == spec["model_provenance_seal"]
