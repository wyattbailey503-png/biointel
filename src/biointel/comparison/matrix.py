"""Competitive Technology Analysis and Condition-Aware Comparison Matrices.

Enforces the Fundamental Comparison Rule: never compare figures measured
under incompatible conditions without explicit flags and experimental context.
Includes MultiFactorAssayBoundaryEngine for multi-factor incompatibility checks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
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


@dataclass
class BoundaryCondition:
    assay_type: str
    substrate_or_target: str
    temperature_c: Optional[float] = None
    cell_model_or_host: Optional[str] = None
    delivery_system: Optional[str] = None
    replicate_type: str = "biological"  # biological or technical


@dataclass
class CompatibilityVerdict:
    is_comparable: bool
    compatibility_score: float  # 0.0 to 1.0
    mismatch_types: List[str]
    audit_warning: str
    reconciliation_guidance: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_comparable": self.is_comparable,
            "compatibility_score": round(self.compatibility_score, 2),
            "mismatch_types": self.mismatch_types,
            "audit_warning": self.audit_warning,
            "reconciliation_guidance": self.reconciliation_guidance,
        }


class MultiFactorAssayBoundaryEngine:
    """Evaluates multi-factor boundary incompatibilities between two experimental measurements."""

    @classmethod
    def evaluate_boundary(
        cls,
        cond_a: BoundaryCondition,
        cond_b: BoundaryCondition,
    ) -> CompatibilityVerdict:
        mismatches: List[str] = []
        score = 1.0

        # 1. Assay Method Mismatch (e.g. In vitro cleavage vs Intracellular targeted HTS)
        assay_a = cond_a.assay_type.lower()
        assay_b = cond_b.assay_type.lower()
        if ("in_vitro" in assay_a and "in_vivo" in assay_b) or ("in_vitro" in assay_b and "in_vivo" in assay_a):
            mismatches.append("ASSAY_TRANSLATIONAL_MISMATCH: In vitro cell-free assay compared directly against in vivo organism.")
            score -= 0.50
        elif ("t7e1" in assay_a or "tide" in assay_a) and ("hts" in assay_b or "ngs" in assay_b):
            mismatches.append("ASSAY_RESOLUTION_MISMATCH: Enzymatic mismatch cleavage (T7E1/TIDE) lacks sensitivity of high-throughput deep sequencing (HTS).")
            score -= 0.35

        # 2. Substrate State Mismatch (e.g. Amorphous PET film vs Crystalline PET bottle flake)
        sub_a = cond_a.substrate_or_target.lower()
        sub_b = cond_b.substrate_or_target.lower()
        if ("amorphous" in sub_a and "crystalline" in sub_b) or ("amorphous" in sub_b and "crystalline" in sub_a):
            mismatches.append("SUBSTRATE_CRYSTALLINITY_MISMATCH: Amorphous substrate (Xc < 5%) compared to crystalline material (Xc > 30%).")
            score -= 0.40

        # 3. Temperature Mismatch (e.g. 50 °C vs 72 °C)
        if cond_a.temperature_c is not None and cond_b.temperature_c is not None:
            delta_t = abs(cond_a.temperature_c - cond_b.temperature_c)
            if delta_t >= 15.0:
                mismatches.append(f"TEMPERATURE_REGIME_MISMATCH: Operating temperature delta is {delta_t:.1f} °C (different kinetic regimes).")
                score -= 0.30

        # 4. Host Cell / Organism Mismatch (e.g. HEK293T vs Primary Stem Cells or Neurons)
        host_a = (cond_a.cell_model_or_host or "").lower()
        host_b = (cond_b.cell_model_or_host or "").lower()
        if ("hek293" in host_a and "primary" in host_b) or ("hek293" in host_b and "primary" in host_a):
            mismatches.append("HOST_PHYSIOLOGY_MISMATCH: Transformed hypotriploid cell line (HEK293T) compared to primary human cells.")
            score -= 0.35

        # 5. Delivery System Mismatch (e.g. Plasmid Lipofection vs RNP Electroporation vs AAV)
        del_a = (cond_a.delivery_system or "").lower()
        del_b = (cond_b.delivery_system or "").lower()
        if del_a and del_b and del_a != del_b:
            if ("plasmid" in del_a and "rnp" in del_b) or ("plasmid" in del_b and "rnp" in del_a):
                mismatches.append("DELIVERY_MODALITY_MISMATCH: Plasmid overexpression has persistent expression and delayed kinetics vs transient RNP.")
                score -= 0.25

        # 6. Replicate Mismatch
        if cond_a.replicate_type != cond_b.replicate_type:
            mismatches.append(f"REPLICATE_TYPE_MISMATCH: Comparing {cond_a.replicate_type} replicates with {cond_b.replicate_type} replicates.")
            score -= 0.20

        comp_score = max(0.0, score)
        is_comp = len(mismatches) == 0

        if is_comp:
            audit_warn = "COMPATIBLE: Experimental parameters are within comparable physical and biological regimes."
            guidance = "Direct quantitative comparison justified."
        else:
            audit_warn = f"INCOMPATIBLE COMPARISON (CONDITION MISMATCH, {len(mismatches)} incompatibilities detected): " + "; ".join(mismatches)
            guidance = "Do not rank technologies directly. Present side-by-side with explicit condition caveats or produce a comparison-gap report."

        return CompatibilityVerdict(
            is_comparable=is_comp,
            compatibility_score=comp_score,
            mismatch_types=mismatches,
            audit_warning=audit_warn,
            reconciliation_guidance=guidance,
        )


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
        # Run boundary engine on the key efficiency metric
        cond_cas9 = BoundaryCondition(
            assay_type="T7E1/TIDE Indel Cleavage",
            substrate_or_target="HEK3 indel knockout",
            cell_model_or_host="HEK293T",
            delivery_system="Plasmid Transfection",
            replicate_type="biological",
        )
        cond_pe = BoundaryCondition(
            assay_type="Targeted HTS Deep Sequencing",
            substrate_or_target="HEK3 precise C->T transversion",
            cell_model_or_host="HEK293T",
            delivery_system="Plasmid Transfection",
            replicate_type="biological",
        )
        boundary_check = MultiFactorAssayBoundaryEngine.evaluate_boundary(cond_cas9, cond_pe)

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
                is_condition_compatible=boundary_check.is_comparable,
                warning_note=boundary_check.audit_warning,
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
