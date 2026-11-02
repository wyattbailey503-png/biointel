"""Reproducible Research Study Package Runner & Verifier.

Discovers, verifies, and executes standardized study packages located
in research/studies/<study-id>/.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class StudyPackageRunner:
    """Manages execution and verification of reproducible study packages."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        if base_dir is None:
            # Auto-detect project root
            self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        else:
            self.base_dir = base_dir
        self.studies_dir = self.base_dir / "research" / "studies"

    def list_studies(self) -> List[str]:
        if not self.studies_dir.exists():
            return []
        return sorted([d.name for d in self.studies_dir.iterdir() if d.is_dir() and d.name.startswith("study_")])

    def verify_study(self, study_id: str) -> Dict[str, Any]:
        study_path = self.studies_dir / study_id
        if not study_path.exists():
            return {
                "study_id": study_id,
                "verified": False,
                "error": f"Study directory does not exist: {study_path}",
            }

        required_files = [
            "README.md",
            "question.md",
            "methods.md",
            "sources.json",
            "evidence.csv",
            "assumptions.yaml",
            "calculations.py",
            "limitations.md",
            "verification.json",
        ]

        missing_files = [f for f in required_files if not (study_path / f).exists()]
        if missing_files:
            return {
                "study_id": study_id,
                "verified": False,
                "error": f"Missing required study package files: {missing_files}",
                "missing_files": missing_files,
            }

        # 1. Validate sources.json
        try:
            with open(study_path / "sources.json", "r") as f:
                sources_data = json.load(f)
            num_sources = len(sources_data.get("primary_sources", []))
        except Exception as e:
            return {
                "study_id": study_id,
                "verified": False,
                "error": f"Failed to parse sources.json: {e}",
            }

        # 2. Execute calculations.py deterministically
        calc_script = study_path / "calculations.py"
        try:
            spec = importlib.util.spec_from_file_location(f"study_{study_id}_calc", calc_script)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load spec for {calc_script}")
            calc_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(calc_module)

            if not hasattr(calc_module, "run_study_calculations"):
                raise AttributeError(f"{calc_script} must define run_study_calculations(study_dir: Path)")

            calc_result = calc_module.run_study_calculations(study_path)
        except Exception as e:
            return {
                "study_id": study_id,
                "verified": False,
                "error": f"Execution of calculations.py failed: {e}",
            }

        # 3. Verify results and figures exist
        summary_file = study_path / "results" / "summary.json"
        if not summary_file.exists():
            return {
                "study_id": study_id,
                "verified": False,
                "error": "calculations.py did not produce results/summary.json",
            }

        figures = list((study_path / "figures").glob("*.svg"))

        # 4. Read verification.json
        with open(study_path / "verification.json", "r") as f:
            ver_meta = json.load(f)

        return {
            "study_id": study_id,
            "verified": True,
            "status": ver_meta.get("status", "CALCULATION_CHECKED"),
            "num_primary_sources": num_sources,
            "figures_generated": [fig.name for fig in figures],
            "calculations_summary": calc_result.get("strategic_recommendation") or calc_result.get("diligence_recommendation") or calc_result.get("scientific_and_diligence_verdict"),
            "verification_meta": ver_meta,
        }

    def run_study(self, study_id: str) -> Dict[str, Any]:
        return self.verify_study(study_id)
