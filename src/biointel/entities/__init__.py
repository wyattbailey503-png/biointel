"""Entities package for BioIntel."""
from biointel.entities.models import (
    ClaimRecord,
    CompetitorComparison,
    EvidenceLinkRecord,
    ExperimentRecord,
    PublicationRecord,
    ResultRecord,
    ScientificChangeCard,
    StructureRecord,
    TechnologyRecord,
)
from biointel.entities.resolver import EntityResolver

__all__ = [
    "EntityResolver",
    "PublicationRecord",
    "TechnologyRecord",
    "StructureRecord",
    "ExperimentRecord",
    "ResultRecord",
    "ClaimRecord",
    "EvidenceLinkRecord",
    "ScientificChangeCard",
    "CompetitorComparison",
]
