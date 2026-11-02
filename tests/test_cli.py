"""Tests for BioIntel CLI commands."""

from __future__ import annotations

import argparse
from pathlib import Path
from biointel.cli import (
    cmd_change_feed,
    cmd_compare,
    cmd_discover,
    cmd_export,
    cmd_memo,
    cmd_pathway,
    cmd_structure,
    cmd_teo_model,
)


def test_cli_discover_offline(tmp_path: Path) -> None:
    args = argparse.Namespace(live=False)
    cmd_discover(args)
    db_file = Path("biointel.db")
    assert db_file.exists()


def test_cli_structure() -> None:
    args = argparse.Namespace(pdb_id="7K38")
    cmd_structure(args)
    assert Path("outputs/figures/7k38_b_factors.svg").exists()
    assert Path("outputs/figures/7k38_contacts.svg").exists()


def test_cli_compare() -> None:
    args = argparse.Namespace(tech_a="crispr_cas9_nuclease", tech_b="prime_editing")
    cmd_compare(args)


def test_cli_memo() -> None:
    args = argparse.Namespace(technology="prime_editing")
    cmd_memo(args)
    assert Path("outputs/research/memo_prime_editing.md").exists()


def test_cli_teo_model() -> None:
    args = argparse.Namespace(
        titer=45.0, duration=120.0, volume=50000.0, recovery=0.85, feedstock_price=0.35, sensitivity=True
    )
    cmd_teo_model(args)
    assert Path("outputs/figures/fermentation_cost_sensitivity.svg").exists()


def test_cli_export() -> None:
    args = argparse.Namespace(version="test_v1")
    cmd_export(args)
    assert Path("data/exports/biointel_archive_test_v1.json").exists()
