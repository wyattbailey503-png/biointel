"""Competitive Technology Analysis and Condition-Aware Comparison Matrices.

Enforces the Fundamental Comparison Rule: never compare figures measured
under incompatible conditions without explicit flags and experimental context.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from biointel.entities.models import CompetitorComparison
from biointel.storage.database import Database


@dataclass
class ComparisonDimension:
    dimension_name: str
    tech_a_value: str
    tech_b_value: str
    tech_a_context: str
    tech_b_context: str
    is_condition_compatible: bool
    warning_note: Optional[str] = None


class TechnologyComparator:
    """Produces structured, condition-grounded technology comparison matrices."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def generate_gene_editing_comparison(
        self,
        tech_a_id: str = "crispr_cas9_nuclease",
        tech_b_id: str = "prime_editing",
        comparator_data: Optional[Dict[str, Any]] = None,
    ) -> CompetitorComparison:
        """
        Builds a verified comparison between two gene editing platforms.
        Default: SpCas9 DSB Nuclease vs Prime Editing (PE2/PE3/bi-PE).
        """
        dimensions: List[ComparisonDimension] = [
            ComparisonDimension(
                dimension_name="Targeting Mechanism",
                tech_a_value="sgRNA: 20-nt spacer targeting 5'-NGG PAM on SpCas9",
                tech_b_value="pegRNA: Guide sequence + Primer Binding Site (PBS) + Reverse Transcriptase (RT) template",
                tech_a_context="Direct DNA sequence pairing",
                tech_b_context="Dual pairing: guide targeting + 3'-flap hybridisation",
                is_condition_compatible=True,
            ),
            ComparisonDimension(
                dimension_name="Editing Modality",
                tech_a_value="Double-Strand Break (DSB) inducing non-homologous end joining (NHEJ) or HDR",
                tech_b_value="Single-strand nick with search-and-replace reverse transcription (no DSB required)",
                tech_a_context="Endogenous error-prone repair pathways",
                tech_b_context="Engineered M-MLV RT template incorporation",
                is_condition_compatible=True,
            ),
            ComparisonDimension(
                dimension_name="Reported On-Target Editing Efficiency",
                tech_a_value="40% – 85% indel knockout efficiency",
                tech_b_value="15% – 55% precise installation (bi-PE improves to 40% – 60%)",
                tech_a_context="HEK293T plasmid transfection (standard gene disruption)",
                tech_b_context="HEK293T plasmid/RNP with engineered dual-prime guides (precise transversion/insertion)",
                is_condition_compatible=False,
                warning_note="INCOMPATIBLE COMPARISON: Cas9 measured for simple indel knockout; Prime Editing measured for precise nucleotide transversion and micro-insertion.",
            ),
            ComparisonDimension(
                dimension_name="Off-Target Cleavage & Indels",
                tech_a_value="Moderate to High (1% – 10% genome-wide off-target cleavage at homologous sites)",
                tech_b_value="Low (< 0.5% unintended indel rate; minimal off-target nicking)",
                tech_a_context="GUIDE-seq / CIRCLE-seq across mismatched genomic targets",
                tech_b_context="High-throughput sequencing at predicted Cas9 off-target loci",
                is_condition_compatible=True,
            ),
            ComparisonDimension(
                dimension_name="Cell-Type Compatibility",
                tech_a_value="High in dividing cells; HDR severely restricted in non-dividing / post-mitotic cells",
                tech_b_value="Broadly active in both dividing and post-mitotic cells (does not depend on G2/M phase HDR)",
                tech_a_context="Dependent on cell cycle machinery for precise editing",
                tech_b_context="Operates independently of donor template and HDR machinery",
                is_condition_compatible=True,
            ),
            ComparisonDimension(
                dimension_name="Delivery Packaging Constraints",
                tech_a_value="Single AAV packaging viable with compact Cas9 or split Cas9 (~4.2 kb payload)",
                tech_b_value="Requires dual AAV or Lipid Nanoparticle (LNP) mRNA (>6.0 kb total editor size)",
                tech_a_context="Cas9 (1,368 aa) fits standard AAV packaging ceiling (<4.7 kb)",
                tech_b_context="Cas9 nickase + M-MLV RT + pegRNA exceeds single AAV capsid capacity",
                is_condition_compatible=True,
            ),
            ComparisonDimension(
                dimension_name="Clinical / Commercial Stage",
                tech_a_value="Commercial / FDA Approved (Exa-cel / Casgevy for sickle cell disease)",
                tech_b_value="Phase 1 Clinical Development (Prime Medicine PM359 for chronic granulomatous disease)",
                tech_a_context="Approved ex vivo autologous HSPC therapy",
                tech_b_context="Ex vivo early clinical trial; in vivo preclinical pipeline",
                is_condition_compatible=True,
            ),
        ]

        warnings: List[str] = [
            d.warning_note for d in dimensions if not d.is_condition_compatible and d.warning_note
        ]

        matrix_dict = {
            "dimensions": [
                {
                    "metric": d.dimension_name,
                    "technology_a": d.tech_a_value,
                    "technology_b": d.tech_b_value,
                    "context_a": d.tech_a_context,
                    "context_b": d.tech_b_context,
                    "compatible": d.is_condition_compatible,
                    "warning": d.warning_note,
                }
                for d in dimensions
            ]
        }

        strategic_takeaway = (
            "SpCas9 remains the standard for gene disruption and ex vivo knockout where high indel rates are acceptable. "
            "Prime Editing significantly expands therapeutic scope by enabling all 12 base conversions, insertions up to 100 bp, "
            "and deletions without double-strand breaks or donor DNA, but faces in vivo delivery bottlenecks due to protein size (>6 kb)."
        )

        comparison_id = f"comp_{tech_a_id}_vs_{tech_b_id}"
        comp = CompetitorComparison(
            comparison_id=comparison_id,
            technology_a_id=tech_a_id,
            technology_b_id=tech_b_id,
            comparison_domain="molecular_and_cellular_engineering",
            shared_target_or_objective="Precision Genome Modification in Eukaryotic Cells",
            comparison_matrix=matrix_dict,
            incompatibility_warnings=warnings,
            strategic_takeaway=strategic_takeaway,
        )

        # Ensure technologies exist to satisfy foreign key constraints
        for t_id, t_name, t_cat in [
            (tech_a_id, "CRISPR-Cas9 Nuclease", "crispr_systems"),
            (tech_b_id, "Prime Editing", "base_and_prime_editing"),
        ]:
            if not self.db.get_technology(t_id):
                self.db.upsert_technology({
                    "tech_id": t_id,
                    "name": t_name,
                    "canonical_name": t_id,
                    "domain": "molecular_and_cellular_engineering",
                    "category": t_cat,
                    "maturity_stage": "preclinical",
                    "description": f"Gene editing platform: {t_name}",
                })

        # Store in database
        self.db.insert_competitor_match({
            "comparison_id": comp.comparison_id,
            "technology_a_id": comp.technology_a_id,
            "technology_b_id": comp.technology_b_id,
            "comparison_domain": comp.comparison_domain,
            "shared_target_or_objective": comp.shared_target_or_objective,
            "comparison_matrix": json.dumps(comp.comparison_matrix),
            "incompatibility_warnings": json.dumps(comp.incompatibility_warnings),
            "strategic_takeaway": comp.strategic_takeaway,
        })

        return comp
