"""Tests for PDB coordinate parsing and metric extraction."""

from __future__ import annotations

from pathlib import Path
from biointel.structures.parser import PDBParser
from biointel.structures.visualizer import StructureVisualizer


def test_pdb_parser_on_7k38() -> None:
    pdb_path = Path(__file__).parent.parent / "data" / "structures" / "7k38.pdb"
    assert pdb_path.exists(), f"Structure file missing: {pdb_path}"

    parser = PDBParser(pdb_path)
    metrics = parser.get_summary_metrics()

    assert metrics["pdb_id"] == "7K38"
    assert metrics["resolution_angstrom"] == 2.0
    assert metrics["total_residues"] == 270
    assert metrics["total_atoms"] > 2000
    assert metrics["helix_residues"] > 100
    assert "VTY" in metrics["bound_ligands"]

    res_nums, matrix = parser.get_ca_distance_matrix()
    assert len(res_nums) == 270
    assert len(matrix) == 270
    assert matrix[0][0] == 0.0
    assert matrix[0][1] > 0.0


def test_structure_visualizer_generates_svg(tmp_path: Path) -> None:
    pdb_path = Path(__file__).parent.parent / "data" / "structures" / "7k38.pdb"
    parser = PDBParser(pdb_path)
    vis = StructureVisualizer(output_dir=tmp_path)

    b_figs = vis.render_b_factor_profile(parser, "test_b_factor")
    c_figs = vis.render_contact_map(parser, "test_contacts")

    assert b_figs["svg"].exists()
    assert b_figs["svg"].stat().st_size > 500
    assert c_figs["svg"].exists()
    assert c_figs["svg"].stat().st_size > 500
