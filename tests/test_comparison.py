"""Tests for Technology Comparison and Condition Incompatibility Warnings."""

from __future__ import annotations

from biointel.comparison.matrix import TechnologyComparator
from biointel.storage.database import Database


def test_technology_comparator_flags_incompatible_conditions(temp_db: Database) -> None:
    comparator = TechnologyComparator(temp_db)
    comp = comparator.generate_gene_editing_comparison()

    assert comp.technology_a_id == "crispr_cas9_nuclease"
    assert comp.technology_b_id == "prime_editing"
    assert len(comp.incompatibility_warnings) > 0
    assert any("INCOMPATIBLE COMPARISON" in w for w in comp.incompatibility_warnings)
    assert len(comp.comparison_matrix["dimensions"]) >= 6
