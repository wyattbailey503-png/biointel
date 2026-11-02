"""Evidence package for BioIntel."""
from biointel.evidence.contradiction import ContradictionDetector, ContradictionReport
from biointel.evidence.engine import EvidenceEngine
from biointel.evidence.quality import EvidenceQualityEvaluator, QualityAssessment

__all__ = [
    "EvidenceEngine",
    "EvidenceQualityEvaluator",
    "QualityAssessment",
    "ContradictionDetector",
    "ContradictionReport",
]
