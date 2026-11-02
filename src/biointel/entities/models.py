"""BioIntel Domain Models.

Strongly typed dataclasses representing biological, experimental,
structural, commercial, and provenance entities.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PublicationRecord:
    publication_id: str
    title: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    pub_year: Optional[int] = None
    pub_date: Optional[str] = None
    is_open_access: int = 0
    license: Optional[str] = None
    citation_count: int = 0
    abstract: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TechnologyRecord:
    tech_id: str
    name: str
    canonical_name: str
    domain: str
    category: str
    maturity_stage: str  # discovery, lead_optimization, preclinical, clinical_trial, pilot_scale, commercial
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructureRecord:
    structure_id: str
    pdb_id: str
    classification: str  # experimental, predicted
    source_url: str
    protein_id: Optional[str] = None
    experimental_method: Optional[str] = None
    resolution_angstrom: Optional[float] = None
    r_factor_free: Optional[float] = None
    organism: Optional[str] = None
    mutations: Optional[str] = None
    bound_ligands: Optional[str] = None
    coordinate_path: Optional[str] = None
    download_timestamp: Optional[str] = None
    version_revision: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentRecord:
    experiment_id: str
    publication_id: str
    experimental_method: str
    model_system: str  # in_vitro, cell_line, primary_cells, organoid, animal, human_clinical
    treatment_intervention: str
    evidence_category: str
    biological_question: Optional[str] = None
    hypothesis: Optional[str] = None
    species: Optional[str] = None
    cell_line_or_tissue: Optional[str] = None
    control_group: Optional[str] = None
    dose_concentration: Optional[str] = None
    exposure_duration: Optional[str] = None
    measurement_time: Optional[str] = None
    sample_size: Optional[int] = None
    biological_replicates: Optional[int] = None
    technical_replicates: Optional[int] = None
    evidence_location: Optional[str] = None
    limitations: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResultRecord:
    result_id: str
    experiment_id: str
    measured_endpoint: str
    value: Optional[float] = None
    unit: Optional[str] = None
    standard_deviation: Optional[float] = None
    confidence_interval: Optional[str] = None
    p_value: Optional[float] = None
    statistical_method: Optional[str] = None
    effect_size: Optional[float] = None
    raw_summary: Optional[str] = None
    assay_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClaimRecord:
    claim_id: str
    technology_id: str
    claim_statement: str
    claim_type: str  # efficacy, specificity, safety, yield, stability, scalability
    mechanistic_assertion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceLinkRecord:
    claim_id: str
    experiment_id: str
    support_direction: str  # supports, contradicts, inconclusive
    confidence_score: float = 1.0
    explanation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScientificChangeCard:
    change_id: str
    technology_id: str
    change_type: str  # replication, contradiction, new_evidence, scale_up, clinical_milestone
    title: str
    previous_state: str
    new_state: str
    primary_source_id: str
    scientific_significance: str
    commercial_implication: str
    diligence_questions: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompetitorComparison:
    comparison_id: str
    technology_a_id: str
    technology_b_id: str
    comparison_domain: str
    shared_target_or_objective: str
    comparison_matrix: Dict[str, Any]
    incompatibility_warnings: List[str]
    strategic_takeaway: str

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["comparison_matrix"] = res["comparison_matrix"]
        res["incompatibility_warnings"] = res["incompatibility_warnings"]
        return res
