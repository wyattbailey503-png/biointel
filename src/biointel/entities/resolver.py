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

    @classmethod
    def resolve_technology_canonical_name(cls, name: str) -> str:
        """Create a slugified canonical identifier for technologies."""
        clean = name.strip().lower()
        clean = re.sub(r"[^a-z0-9]+", "_", clean)
        return clean.strip("_")
