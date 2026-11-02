"""UniProtKB Ingestion Adapter.

Fetches protein sequence, functional annotations, catalytic sites, and gene symbols.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any, Dict, Optional
from biointel.entities.resolver import EntityResolver


class UniProtAdapter:
    """Ingestion client for UniProtKB REST API."""

    BASE_URL = "https://rest.uniprot.org/uniprotkb"

    def __init__(self, user_agent: str = "BioIntel/1.0") -> None:
        self.user_agent = user_agent

    def fetch_entry(self, accession: str) -> Dict[str, Any]:
        """Fetch protein entry details by accession."""
        clean_acc = EntityResolver.normalize_uniprot_accession(accession)
        if not clean_acc:
            raise ValueError(f"Invalid UniProt accession: {accession}")

        url = f"{self.BASE_URL}/{clean_acc}.json"
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def parse_entry_to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract core protein attributes."""
        acc = data.get("primaryAccession", "")
        name = data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "Unknown protein")
        gene_name = None
        genes = data.get("genes", [])
        if genes and "geneName" in genes[0]:
            gene_name = genes[0]["geneName"].get("value")

        organism = data.get("organism", {}).get("scientificName", "Unknown")
        seq_info = data.get("sequence", {})
        seq = seq_info.get("value", "")
        length = seq_info.get("length", len(seq))

        comments = data.get("comments", [])
        function_desc = ""
        for c in comments:
            if c.get("commentType") == "FUNCTION":
                texts = c.get("texts", [])
                if texts:
                    function_desc = texts[0].get("value", "")
                break

        return {
            "protein_id": f"uniprot_{acc.lower()}",
            "uniprot_accession": acc,
            "name": name,
            "gene_name": gene_name,
            "organism": organism,
            "sequence": seq,
            "sequence_length": length,
            "molecular_function": function_desc,
        }
