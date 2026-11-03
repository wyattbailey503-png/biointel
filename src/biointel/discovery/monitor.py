"""Continuous Discovery Monitoring Daemon with Live Assay Boundary Triggers.

Monitors incoming literature and experimental evidence, running candidate records through
the MultiFactorAssayBoundaryEngine to detect incompatibilities (e.g. assay resolution mismatches,
unrepresentative cell lines, or temperature/substrate discrepancies) and logging
CONTRADICTION_ALERT and INCOMPATIBLE_ASSAY_BOUNDARY records to SQLite.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from biointel.comparison.matrix import (
    BoundaryCondition,
    CompatibilityVerdict,
    MultiFactorAssayBoundaryEngine,
)
from biointel.storage.database import Database


@dataclass
class MonitoringTriggerEvent:
    event_id: str
    technology_id: str
    trigger_type: str  # 'INCOMPATIBLE_ASSAY_BOUNDARY', 'CONTRADICTION_ALERT', 'NEW_REPLICATION_DETECTED'
    source_doi: str
    mismatch_types: List[str]
    severity: str      # 'CRITICAL', 'HIGH', 'MODERATE', 'INFORMATIONAL'
    description: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["type"] = self.trigger_type
        return d


class ContinuousMonitoringDaemon:
    """Automated surveillance engine for continuous evidence boundary checking."""

    # Baseline operating boundaries for known enzymes
    ENZYME_BASELINES: Dict[str, BoundaryCondition] = {
        "IsPETase-WT": BoundaryCondition(
            assay_type="in_vitro_uv_vis",
            substrate_or_target="amorphous_film",
            temperature_c=30.0,
            cell_model_or_host="cell_free",
        ),
        "FAST-PETase": BoundaryCondition(
            assay_type="in_vitro_hplc",
            substrate_or_target="amorphous_film",
            temperature_c=50.0,
            cell_model_or_host="cell_free",
        ),
        "LCC-ICCG": BoundaryCondition(
            assay_type="in_vitro_hplc",
            substrate_or_target="post_consumer_pet_flake",
            temperature_c=72.0,
            cell_model_or_host="cell_free",
        ),
    }

    def __init__(self, db: Database) -> None:
        self.db = db

    def audit_candidate_evidence(
        self,
        technology_id: str,
        baseline_conditions: BoundaryCondition,
        candidate_conditions: BoundaryCondition,
        candidate_doi: str,
        reported_claim: str = "",
    ) -> Optional[MonitoringTriggerEvent]:
        """
        Evaluates a candidate wet-lab observation against an established technology baseline.
        If assay parameters are incompatible or contradictory, records an alert into SQLite.
        """
        verdict = MultiFactorAssayBoundaryEngine.evaluate_boundary(
            baseline_conditions,
            candidate_conditions,
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        if not verdict.is_comparable:
            event_id = f"alert_{technology_id}_{abs(hash(candidate_doi + str(verdict.mismatch_types))) % 1000000}"
            severity = "CRITICAL" if any("TEMPERATURE" in m or "CRYSTALLINITY" in m for m in verdict.mismatch_types) else "HIGH"
            event = MonitoringTriggerEvent(
                event_id=event_id,
                technology_id=technology_id,
                trigger_type="INCOMPATIBLE_ASSAY_BOUNDARY",
                source_doi=candidate_doi,
                mismatch_types=verdict.mismatch_types,
                severity=severity,
                description=(
                    f"Direct comparison blocked for {technology_id}: Incompatible experimental parameters detected: "
                    f"{verdict.audit_warning}"
                ),
                timestamp=now_iso,
            )

            # Ensure technology and document exist to satisfy relational foreign key constraints
            try:
                self.db.upsert_source({
                    "source_id": "monitoring_feed",
                    "name": "Continuous Monitoring Feed",
                    "publisher": "BioIntel",
                    "url": "https://biointel.local",
                    "category": "feed",
                    "adapter_type": "internal",
                    "api_version": "v1",
                    "rate_limit_per_min": 60,
                    "licensing": "open",
                    "priority": 1,
                    "monitoring_frequency_hours": 24,
                    "last_successful_retrieval": None,
                    "last_attempt": None,
                    "retry_state": None,
                })
                self.db.upsert_technology({
                    "tech_id": technology_id,
                    "name": technology_id,
                    "canonical_name": technology_id.lower().replace("-", "_"),
                    "domain": "industrial_biotechnology",
                    "category": "biocatalysis",
                    "maturity_stage": "preclinical",
                    "description": f"Automated monitoring entity for {technology_id}",
                })
                self.db.upsert_document({
                    "document_id": f"doi:{candidate_doi}",
                    "source_id": "monitoring_feed",
                    "external_id": candidate_doi,
                    "title": f"Candidate Publication: {candidate_doi}",
                    "url": f"https://doi.org/{candidate_doi}",
                    "content_hash": f"hash_{abs(hash(candidate_doi))}",
                    "format": "json",
                    "ingestion_status": "parsed",
                })
            except Exception:
                pass

            # Insert alert into scientific_changes table
            self.db.insert_scientific_change({
                "change_id": event_id,
                "technology_id": technology_id,
                "change_type": event.trigger_type,
                "title": f"Assay Boundary Mismatch Flagged: {candidate_doi}",
                "previous_state": f"Baseline Assay: {baseline_conditions.assay_type} at {baseline_conditions.temperature_c}°C on {baseline_conditions.substrate_or_target}",
                "new_state": f"Candidate Assay: {candidate_conditions.assay_type} at {candidate_conditions.temperature_c}°C on {candidate_conditions.substrate_or_target}",
                "primary_source_id": f"doi:{candidate_doi}",
                "scientific_significance": event.description,
                "commercial_implication": "Reported rates cannot be substituted directly into commercial TEA without adjustment.",
                "diligence_questions": json.dumps([
                    "Did the candidate study validate with gold-standard high-throughput assays?",
                    "What is the quantitative conversion factor between the mismatched detection regimes?",
                ]),
            })

            return event

        return None

    def evaluate_incoming_experiment(
        self,
        experiment_id: str,
        enzyme_variant: str,
        assay_temp_c: float,
        assay_ph: float,
        substrate: str,
        source_doi: str,
    ) -> Optional[Dict[str, Any]]:
        """High-level entry point to evaluate single incoming experimental assay against enzyme baseline."""
        baseline = self.ENZYME_BASELINES.get(
            enzyme_variant,
            BoundaryCondition(
                assay_type="in_vitro_uv_vis",
                substrate_or_target="amorphous_film",
                temperature_c=30.0,
            ),
        )

        candidate = BoundaryCondition(
            assay_type="in_vitro_uv_vis",
            substrate_or_target=substrate,
            temperature_c=assay_temp_c,
        )

        event = self.audit_candidate_evidence(
            technology_id=enzyme_variant,
            baseline_conditions=baseline,
            candidate_conditions=candidate,
            candidate_doi=source_doi,
        )

        if event:
            return event.to_dict()
        return None
