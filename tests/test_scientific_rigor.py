"""Permanent Scientific Quality and Rigor Regression Tests.

Ensures BioIntel maintains strict adherence to biological nomenclature,
experimental controls, condition-aware comparisons, chemical mass balance,
and molecular coordinate validation.
"""

from __future__ import annotations

from pathlib import Path

from biointel.comparison.matrix import TechnologyComparator
from biointel.economics.fermentation import FermentationInputs, TechnoEconomicFermentationModel
from biointel.entities.models import ExperimentRecord, ResultRecord
from biointel.entities.resolver import EntityResolver
from biointel.evidence.contradiction import ContradictionDetector
from biointel.evidence.quality import EvidenceQualityEvaluator
from biointel.storage.database import Database
from biointel.structures.parser import PDBParser


def test_entity_species_disambiguation() -> None:
    """Ensure genes, proteins, and orthologs across distinct species are not collapsed."""
    human_doi = "10.1093/nar/gkac506"
    plant_doi = "10.1038/s42003-022-03085-6"

    canon_h, doi_h, _, _ = EntityResolver.resolve_publication_ids(doi=human_doi)
    canon_p, doi_p, _, _ = EntityResolver.resolve_publication_ids(doi=plant_doi)

    assert canon_h != canon_p
    assert doi_h == "10.1093/nar/gkac506"
    assert doi_p == "10.1038/s42003-022-03085-6"

    # PDB IDs must remain distinct
    assert EntityResolver.normalize_pdb_id("7k38") == "7K38"
    assert EntityResolver.normalize_pdb_id("4oo8") == "4OO8"
    assert EntityResolver.normalize_pdb_id("1crn") == "1CRN"
    assert EntityResolver.normalize_pdb_id("invalid_id") is None


def test_misidentified_experimental_controls_flagged() -> None:
    """Studies lacking explicit vehicle or negative controls must receive a quality penalty and warning flag."""
    exp_no_control = ExperimentRecord(
        experiment_id="exp_bad_control",
        publication_id="doi:10.1000/test",
        experimental_method="Fluorescence assay",
        model_system="cell_line",
        treatment_intervention="Novel enzyme variant",
        evidence_category="cell_based_experiment",
        control_group="",  # Missing control
        biological_replicates=1,
    )
    res = ResultRecord(
        result_id="res_bad_control",
        experiment_id="exp_bad_control",
        measured_endpoint="enzyme_activity",
        value=120.0,
        unit="U/mg",
    )

    assessment = EvidenceQualityEvaluator.evaluate(exp_no_control, res)
    assert assessment.control_rigor_score <= 0.3
    assert any("MISSING_EXPLICIT_CONTROL" in f for f in assessment.flags)
    assert any("UNREPLICATED" in f for f in assessment.flags)
    assert assessment.overall_confidence == "Exploratory"


def test_incompatible_assay_comparison_rejected(temp_db: Database) -> None:
    """Direct numerical comparison between indel knockout and precise base editing must be flagged."""
    comparator = TechnologyComparator(temp_db)
    comp = comparator.generate_gene_editing_comparison("crispr_cas9_nuclease", "prime_editing")

    mismatch_found = False
    for dim in comp.comparison_matrix["dimensions"]:
        if "Editing Efficiency" in dim["metric"]:
            assert dim["compatible"] is False
            assert "INCOMPATIBLE COMPARISON" in dim["warning"]
            mismatch_found = True

    assert mismatch_found is True
    assert len(comp.incompatibility_warnings) >= 1


def test_fermentation_mass_balance_conservation() -> None:
    """
    Law of Conservation of Mass: Recovered protein mass can NEVER exceed
    the stoichiometric carbon input (Dextrose substrate mass * theoretical max yield).
    """
    inputs = FermentationInputs(
        titer_g_per_l=45.0,
        duration_hours=120.0,
        working_volume_liters=50000.0,
        recovery_efficiency=0.85,
        yield_product_per_substrate=0.38,
    )
    outputs = TechnoEconomicFermentationModel.calculate(inputs)

    # Total recovered mass
    recovered_kg = outputs.product_mass_per_batch_kg

    # Substrate required per batch:
    substrate_needed_kg = (inputs.working_volume_liters * inputs.titer_g_per_l / 1000.0) / inputs.yield_product_per_substrate

    # Theoretical maximum protein yield on glucose is <= 0.51 g/g based on elemental stoichiometry
    theoretical_max_mass_kg = substrate_needed_kg * 0.51

    # Recovered mass must strictly obey thermodynamics
    assert recovered_kg <= theoretical_max_mass_kg, "Thermodynamic violation: product mass exceeds stoichiometric ceiling!"

    # Test error handling on unphysical input
    try:
        invalid_inputs = FermentationInputs(recovery_efficiency=1.5)  # > 100% recovery impossible
        TechnoEconomicFermentationModel.calculate(invalid_inputs)
        assert False, "Should have raised ValueError on recovery > 1.0"
    except ValueError:
        pass


def test_multi_structure_molecular_coordinate_validity() -> None:
    """Verify coordinate parser integrity across 3 distinct macromolecular architectures."""
    base_dir = Path(__file__).parent.parent / "data" / "structures"

    # 1. 7K38 (Plant receptor hydrolase)
    p_7k38 = PDBParser(base_dir / "7k38.pdb")
    m_7k38 = p_7k38.get_summary_metrics()
    assert m_7k38["pdb_id"] == "7K38"
    assert m_7k38["resolution_angstrom"] == 2.0
    assert m_7k38["total_residues"] == 270
    assert 10.0 <= m_7k38["average_b_factor"] <= 40.0

    # 2. 1CRN (Crambin ultra-high resolution plant protein)
    p_1crn = PDBParser(base_dir / "1crn.pdb")
    m_1crn = p_1crn.get_summary_metrics()
    assert m_1crn["pdb_id"] == "1CRN"
    assert m_1crn["total_residues"] == 46
    assert m_1crn["average_b_factor"] < 10.0  # Exceptionally rigid crystal lattice

    # 3. 4OO8 (Cas9 RNP complex with guide RNA and target DNA)
    p_4oo8 = PDBParser(base_dir / "4oo8.pdb")
    m_4oo8 = p_4oo8.get_summary_metrics()
    assert m_4oo8["pdb_id"] == "4OO8"
    assert m_4oo8["resolution_angstrom"] == 2.50
    assert len(m_4oo8["chains"]) >= 4  # Protein, sgRNA, target DNA, non-target DNA
    assert m_4oo8["average_b_factor"] > 60.0  # Flexible nuclease lobes

    # Distance matrix validity (C-alpha distances must be non-negative and symmetric)
    res_nums, mat = p_1crn.get_ca_distance_matrix()
    for i in range(len(res_nums)):
        assert mat[i][i] == 0.0
        for j in range(i + 1, len(res_nums)):
            assert mat[i][j] == mat[j][i]
            assert mat[i][j] > 0.0
            # Bond distance between adjacent residues CA(i)-CA(i+1) is ~3.8 Angstroms
            if j == i + 1:
                assert 3.5 <= mat[i][j] <= 4.1, f"Unphysical adjacent Cα-Cα distance: {mat[i][j]:.2f} Å"


def test_statistical_uncertainty_and_contradiction() -> None:
    """Ensure contradiction detector distinguishes insignificant variations from true conflict."""
    exp1 = ExperimentRecord(
        experiment_id="e1",
        publication_id="doi:10.1",
        experimental_method="NGS",
        model_system="cell_line",
        treatment_intervention="Drug A",
        evidence_category="cell_based_experiment",
    )
    res1 = ResultRecord(
        result_id="r1",
        experiment_id="e1",
        measured_endpoint="viability",
        value=50.0,
        p_value=0.01,
    )

    # Concordant experiment
    exp2 = ExperimentRecord(
        experiment_id="e2",
        publication_id="doi:10.2",
        experimental_method="NGS",
        model_system="cell_line",
        treatment_intervention="Drug A",
        evidence_category="cell_based_experiment",
    )
    res2 = ResultRecord(
        result_id="r2",
        experiment_id="e2",
        measured_endpoint="viability",
        value=52.0,
        p_value=0.02,
    )

    report_concordant = ContradictionDetector.compare_experiments(exp1, res1, exp2, res2)
    assert report_concordant.has_conflict is False

    # Discordant experiment (p > 0.05 vs p <= 0.01)
    res3 = ResultRecord(
        result_id="r3",
        experiment_id="e2",
        measured_endpoint="viability",
        value=95.0,
        p_value=0.45,
    )
    report_discordant = ContradictionDetector.compare_experiments(exp1, res1, exp2, res3)
    assert report_discordant.has_conflict is True
    assert report_discordant.severity == "high"


def test_anti_structure_misidentification_regression() -> None:
    """REGRESSION TEST: Prevents misidentified structures from entering validated research outputs.

    Specifically guards against the conflation where PDB 7K38 (pea KAI2 hydrolase receptor)
    was erroneously claimed to be FAST-PETase (authoritative PDB is 7SH6).
    """
    # 7K38 is Pisum sativum KAI2; claiming it is FAST-PETase MUST be rejected
    valid_7k38_petase, msg_7k38_petase = EntityResolver.validate_structure_identity("7K38", "FAST-PETase")
    assert valid_7k38_petase is False
    assert "SCIENTIFIC IDENTITY MISMATCH" in msg_7k38_petase
    assert "Pisum sativum" in msg_7k38_petase
    assert "7SH6" in msg_7k38_petase

    # 7SH6 is authoritative FAST-PETase; must be accepted
    valid_7sh6_petase, msg_7sh6 = EntityResolver.validate_structure_identity("7SH6", "FAST-PETase")
    assert valid_7sh6_petase is True
    assert "Verified" in msg_7sh6 and "FAST-PETase" in msg_7sh6


    # 7K38 claiming KAI2 or karrikin receptor must be accepted
    valid_7k38_kai2, msg_kai2 = EntityResolver.validate_structure_identity("7K38", "KAI2")
    assert valid_7k38_kai2 is True

    # 4OO8 is Cas9; claiming FAST-PETase must be rejected
    valid_cas9_petase, msg_cas9 = EntityResolver.validate_structure_identity("4OO8", "FAST-PETase")
    assert valid_cas9_petase is False
    assert "Cas9" in msg_cas9 and "Streptococcus pyogenes" in msg_cas9


