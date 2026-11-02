"""Scientific Change Detection and Change Card Generation.

Tracks evolutions in evidence, replication milestones, delivery breakthroughs,
and clinical transitions without confusing database updates with scientific discoveries.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from biointel.entities.models import ScientificChangeCard
from biointel.storage.database import Database


class ChangeDetector:
    """Detects meaningful scientific and commercial transitions across technologies."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def create_change_card(
        self,
        change_id: str,
        technology_id: str,
        change_type: str,
        title: str,
        previous_state: str,
        new_state: str,
        primary_source_id: str,
        scientific_significance: str,
        commercial_implication: str,
        diligence_questions: Optional[List[str]] = None,
    ) -> ScientificChangeCard:
        """Construct and persist a validated Change Card."""
        q_json = json.dumps(diligence_questions or [])
        card = ScientificChangeCard(
            change_id=change_id,
            technology_id=technology_id,
            change_type=change_type,
            title=title,
            previous_state=previous_state,
            new_state=new_state,
            primary_source_id=primary_source_id,
            scientific_significance=scientific_significance,
            commercial_implication=commercial_implication,
            diligence_questions=q_json,
        )

        self.db.insert_scientific_change(card.to_dict())
        return card

    def get_timeline_for_technology(self, technology_id: str) -> List[Dict[str, Any]]:
        """Retrieve all recorded scientific and commercial changes in chronological order."""
        changes = self.db.get_scientific_changes(technology_id)
        for c in changes:
            if c.get("diligence_questions"):
                try:
                    c["diligence_questions"] = json.loads(c["diligence_questions"])
                except Exception:
                    pass
        return changes
