"""Versioned JSON Research Exporter.

Packages all validated records, technologies, evidence links, comparisons,
and economic models into reproducible, Git-ready versioned JSON archives.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from biointel.storage.database import Database


class ResearchExporter:
    """Exports structured database state to versioned JSON packages."""

    def __init__(self, db: Database, export_dir: Optional[str | Path] = None) -> None:
        self.db = db
        if export_dir:
            self.export_dir = Path(export_dir)
        else:
            self.export_dir = Path(__file__).parent.parent.parent.parent / "data" / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_full_archive(self, version_tag: str = "v1.0.0") -> Path:
        """Export complete relational snapshot to structured JSON."""
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.db.get_connection() as conn:
            sources = [dict(r) for r in conn.execute("SELECT * FROM source_registry").fetchall()]
            publications = [dict(r) for r in conn.execute("SELECT * FROM publications").fetchall()]
            technologies = [dict(r) for r in conn.execute("SELECT * FROM technologies").fetchall()]
            structures = [dict(r) for r in conn.execute("SELECT * FROM structures").fetchall()]
            experiments = [dict(r) for r in conn.execute("SELECT * FROM experiments").fetchall()]
            results = [dict(r) for r in conn.execute("SELECT * FROM experimental_results").fetchall()]
            claims = [dict(r) for r in conn.execute("SELECT * FROM claims").fetchall()]
            evidence_links = [dict(r) for r in conn.execute("SELECT * FROM evidence_links").fetchall()]
            comparisons = [dict(r) for r in conn.execute("SELECT * FROM competitor_matches").fetchall()]
            changes = [dict(r) for r in conn.execute("SELECT * FROM scientific_changes").fetchall()]
            economic_scenarios = [dict(r) for r in conn.execute("SELECT * FROM economic_scenarios").fetchall()]

        payload: Dict[str, Any] = {
            "archive_version": version_tag,
            "export_timestamp": timestamp,
            "system": "BioIntel Autonomous Biotechnology Intelligence Engine",
            "telemetry": {
                "total_sources": len(sources),
                "total_publications": len(publications),
                "total_technologies": len(technologies),
                "total_structures": len(structures),
                "total_experiments": len(experiments),
                "total_claims": len(claims),
                "total_comparisons": len(comparisons),
                "total_changes": len(changes),
                "total_economic_models": len(economic_scenarios),
            },
            "data": {
                "sources": sources,
                "publications": publications,
                "technologies": technologies,
                "structures": structures,
                "experiments": experiments,
                "experimental_results": results,
                "claims": claims,
                "evidence_links": evidence_links,
                "competitor_matches": comparisons,
                "scientific_changes": changes,
                "economic_scenarios": economic_scenarios,
            },
        }

        export_file = self.export_dir / f"biointel_archive_{version_tag}.json"
        export_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return export_file
