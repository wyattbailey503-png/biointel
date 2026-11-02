"""Mechanism of Action Analysis and Typed Biological Relationships.

Models causal interactions, substrate binding, catalytic transitions,
and engineering lineage while distinguishing causation from correlation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


VALID_RELATION_TYPES = {
    "binds",
    "inhibits",
    "activates",
    "edits",
    "degrades",
    "expresses",
    "regulates",
    "cleaves",
    "transports",
    "phosphorylates",
    "correlates_with",
    "causes",
}


@dataclass
class MechanismStep:
    step_number: int
    source_entity: str
    relation_type: str
    target_entity: str
    cellular_compartment: Optional[str] = None
    is_causal: bool = True
    evidence_citation: Optional[str] = None

    def __post_init__(self) -> None:
        if self.relation_type not in VALID_RELATION_TYPES:
            raise ValueError(f"Invalid relation type: {self.relation_type}. Allowed: {VALID_RELATION_TYPES}")
        if self.relation_type == "causes" and not self.is_causal:
            raise ValueError("Relation 'causes' cannot be marked as non-causal.")


@dataclass
class MechanismOfActionProfile:
    technology_id: str
    biological_substrate: str
    target_or_pathway: str
    molecular_mechanism: str
    cell_or_organism_context: str
    intended_functional_outcome: str
    steps: List[MechanismStep] = field(default_factory=list)
    known_limitations: List[str] = field(default_factory=list)
    unanswered_questions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technology_id": self.technology_id,
            "biological_substrate": self.biological_substrate,
            "target_or_pathway": self.target_or_pathway,
            "molecular_mechanism": self.molecular_mechanism,
            "cell_or_organism_context": self.cell_or_organism_context,
            "intended_functional_outcome": self.intended_functional_outcome,
            "steps": [
                {
                    "step_number": s.step_number,
                    "source": s.source_entity,
                    "relation": s.relation_type,
                    "target": s.target_entity,
                    "compartment": s.cellular_compartment,
                    "is_causal": s.is_causal,
                    "evidence": s.evidence_citation,
                }
                for s in self.steps
            ],
            "known_limitations": self.known_limitations,
            "unanswered_questions": self.unanswered_questions,
        }
