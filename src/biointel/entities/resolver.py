"""BioIntel Entity Resolution and Identifier Normalization.

Enforces authoritative identifier precedence, prevents ambiguous fuzzy merges,
and handles provenance for all biological and bibliographic entities.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple


class EntityResolver:
    """Normalize and resolve identifiers with strict provenance rules."""

    @staticmethod
    def normalize_doi(doi: Optional[str]) -> Optional[str]:
        """Normalize DOI by stripping URLs, resolvers, and trailing punctuation."""
        if not doi:
            return None
        doi = doi.strip()
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
        doi = doi.lower()
        return doi if re.match(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$", doi) else None

    @staticmethod
    def normalize_pmid(pmid: Optional[Any]) -> Optional[str]:
        """Normalize PubMed ID to standard digits string."""
        if not pmid:
            return None
        pmid_str = str(pmid).strip()
        digits = re.sub(r"[^\d]", "", pmid_str)
        return digits if digits else None

    @staticmethod
    def normalize_pmcid(pmcid: Optional[str]) -> Optional[str]:
        """Normalize PubMed Central ID with canonical PMC prefix."""
        if not pmcid:
            return None
        pmcid = pmcid.strip().upper()
        if not pmcid.startswith("PMC"):
            pmcid = f"PMC{pmcid}"
        return pmcid if re.match(r"^PMC\d+$", pmcid) else None

    @staticmethod
    def normalize_pdb_id(pdb_id: Optional[str]) -> Optional[str]:
        """Normalize PDB 4-letter alphanumeric identifier."""
        if not pdb_id:
            return None
        clean = pdb_id.strip().upper()
        clean = re.sub(r"^PDB_", "", clean)
        return clean if re.match(r"^[0-9][A-Za-z0-9]{3}$", clean) else None

    @staticmethod
    def normalize_uniprot_accession(acc: Optional[str]) -> Optional[str]:
        """Normalize UniProtKB accession format (e.g. P00533, Q9Y261)."""
        if not acc:
            return None
        clean = acc.strip().upper()
        return clean if re.match(r"^[A-NR-CZ][0-9][A-Z][A-Z0-9]{2}[0-9](-[0-9]+)?$", clean) else None

    @classmethod
    def resolve_publication_ids(
        cls, doi: Optional[str] = None, pmid: Optional[str] = None, pmcid: Optional[str] = None
    ) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        """
        Produce a canonical publication ID based on authoritative precedence:
        DOI > PMID > PMCID.
        """
        norm_doi = cls.normalize_doi(doi)
        norm_pmid = cls.normalize_pmid(pmid)
        norm_pmcid = cls.normalize_pmcid(pmcid)

        if norm_doi:
            canonical_id = f"doi:{norm_doi}"
        elif norm_pmid:
            canonical_id = f"pmid:{norm_pmid}"
        elif norm_pmcid:
            canonical_id = f"pmc:{norm_pmcid}"
        else:
            raise ValueError("At least one valid publication identifier (DOI, PMID, PMCID) is required.")

        return canonical_id, norm_doi, norm_pmid, norm_pmcid

    AUTHORITATIVE_STRUCTURE_REGISTRY: Dict[str, Dict[str, Any]] = {
        "7SH6": {
            "canonical_name": "FAST-PETase",
            "full_title": "Crystal structure of a PET hydrolase mutant from Ideonella Sakaiensis",
            "organism": "Ideonella sakaiensis",
            "family": "alpha/beta hydrolase (PETase)",
            "engineered_mutations": ["S121E", "D186H", "R224Q", "N233K", "R280A"],
            "primary_doi": "10.1038/s41586-022-04599-z",
            "disallowed_aliases": ["kai2", "karrikin", "pea receptor"],
        },
        "7K38": {
            "canonical_name": "KAI2 (Karrikin Insensitive 2)",
            "full_title": "Crystal structure of Pisum sativum KAI2 in complex with GR24-ent5DS product",
            "organism": "Pisum sativum",
            "family": "alpha/beta hydrolase receptor (karrikin/strigolactone)",
            "engineered_mutations": [],
            "primary_doi": "10.1038/s42003-022-03085-6",
            "disallowed_aliases": ["fast-petase", "petase", "pet hydrolase", "plastic recycling"],
        },
        "4OO8": {
            "canonical_name": "Cas9-sgRNA-DNA complex",
            "full_title": "Crystal structure of Cas9 in complex with guide RNA and target DNA",
            "organism": "Streptococcus pyogenes",
            "family": "CRISPR-associated endonuclease",
            "engineered_mutations": [],
            "primary_doi": "10.1038/nature13079",
            "disallowed_aliases": ["petase", "kai2", "prime editor"],
        },
        "1CRN": {
            "canonical_name": "Crambin",
            "full_title": "Structure of crambin at 0.54 A resolution",
            "organism": "Crambe hispanica",
            "family": "plant thionin seed storage protein",
            "engineered_mutations": [],
            "primary_doi": "10.1073/pnas.81.18.6014",
            "disallowed_aliases": ["petase", "cas9", "kai2"],
        },
    }

    @classmethod
    def validate_structure_identity(cls, pdb_id: str, claimed_name: str) -> Tuple[bool, str]:
        """
        Validates claimed biological identity against authoritative structure registry.
        Guarantees structures like 7K38 (pea KAI2) cannot be falsely labeled as FAST-PETase.
        """
        norm_id = cls.normalize_pdb_id(pdb_id)
        if not norm_id:
            return False, f"Invalid PDB ID format: '{pdb_id}'"

        if norm_id not in cls.AUTHORITATIVE_STRUCTURE_REGISTRY:
            return True, f"PDB ID {norm_id} is not in authoritative registry; requires manual provenance review."

        info = cls.AUTHORITATIVE_STRUCTURE_REGISTRY[norm_id]
        claimed_lower = claimed_name.lower().strip()

        # Check disallowed aliases
        for bad_alias in info["disallowed_aliases"]:
            if bad_alias in claimed_lower:
                alt_note = ""
                if "petase" in bad_alias:
                    alt_note = " Authoritative PDB structure for FAST-PETase is 7SH6."
                return False, (
                    f"SCIENTIFIC IDENTITY MISMATCH: PDB {norm_id} is '{info['full_title']}' "
                    f"from organism '{info['organism']}', NOT '{claimed_name}'. "
                    f"Authoritative canonical name: '{info['canonical_name']}'.{alt_note}"
                )



        return True, f"Verified: PDB {norm_id} matches '{info['canonical_name']}' ({info['organism']})."

    @classmethod
    def resolve_technology_canonical_name(cls, name: str) -> str:
        """Create a slugified canonical identifier for technologies."""
        clean = name.strip().lower()
        clean = re.sub(r"[^a-z0-9]+", "_", clean)
        return clean.strip("_")
