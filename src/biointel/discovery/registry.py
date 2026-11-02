"""BioIntel Source Registry Management.

Tracks data sources, health status, monitoring frequencies, and rate limits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from biointel.storage.database import Database


class SourceRegistry:
    """Manages external scientific data source configurations and telemetry."""

    def __init__(self, db: Database, config_path: Optional[str | Path] = None) -> None:
        self.db = db
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path(__file__).parent.parent.parent.parent / "config" / "sources.yaml"

    def load_and_sync_sources(self) -> List[Dict[str, Any]]:
        """Parse configuration and sync into the database source_registry table."""
        sources = self._parse_yaml_sources(self.config_path)
        for s in sources:
            source_dict = {
                "source_id": s["id"],
                "name": s["name"],
                "publisher": s["publisher"],
                "url": s["url"],
                "category": s["category"],
                "adapter_type": s.get("adapter_type", s["id"]),
                "api_version": s.get("api_version"),
                "rate_limit_per_min": s.get("rate_limit_per_min", 60),
                "licensing": s.get("licensing", "Open"),
                "priority": s.get("priority", 1),
                "monitoring_frequency_hours": s.get("monitoring_frequency_hours", 24),
                "retry_state": "ready",
            }
            self.db.upsert_source(source_dict)
        return self.db.get_sources()

    def record_attempt(self, source_id: str, success: bool, timestamp: str, message: Optional[str] = None) -> None:
        """Update telemetry for a source after an API call."""
        status = "healthy" if success else "degraded"
        with self.db.transaction() as cur:
            if success:
                cur.execute(
                    """
                    UPDATE source_registry
                    SET last_attempt = ?, last_successful_retrieval = ?, retry_state = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE source_id = ?
                    """,
                    (timestamp, timestamp, status, source_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE source_registry
                    SET last_attempt = ?, retry_state = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE source_id = ?
                    """,
                    (timestamp, status, source_id),
                )

    def _parse_yaml_sources(self, path: Path) -> List[Dict[str, Any]]:
        """Lightweight YAML parser for source configuration."""
        if not path.exists():
            return []

        text = path.read_text(encoding="utf-8")
        sources: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("- id:"):
                if current:
                    sources.append(current)
                current = {"id": line.split(":", 1)[1].strip().strip('"').strip("'")}
            elif current and ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().lstrip("- ")
                val = val.strip().strip('"').strip("'")
                if val.isdigit():
                    val = int(val)
                current[key] = val

        if current:
            sources.append(current)

        return sources
