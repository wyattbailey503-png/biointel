"""Europe PMC Ingestion Adapter.

Fetches bibliographic metadata, abstract, full-text identifiers,
and open-access license information from Europe PMC REST API.
"""

from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
from biointel.entities.models import PublicationRecord
from biointel.entities.resolver import EntityResolver


class EuropePMCAdapter:
    """Ingestion client for Europe PMC REST API."""

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def __init__(self, user_agent: str = "BioIntel/1.0 (mailto:researcher@local)") -> None:
        self.user_agent = user_agent

    def search(self, query: str, page_size: int = 10, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Perform search query against Europe PMC."""
        params = {
            "query": query,
            "format": "json",
            "pageSize": page_size,
            "resultType": "lite",
        }
        if cursor:
            params["cursorMark"] = cursor

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data

    def parse_result_to_publication(self, item: Dict[str, Any]) -> PublicationRecord:
        """Transform raw Europe PMC JSON item into PublicationRecord."""
        raw_doi = item.get("doi")
        raw_pmid = item.get("pmid")
        raw_pmcid = item.get("pmcid")

        canonical_id, norm_doi, norm_pmid, norm_pmcid = EntityResolver.resolve_publication_ids(
            doi=raw_doi, pmid=raw_pmid, pmcid=raw_pmcid
        )

        title = item.get("title", "Untitled Publication").rstrip(".")
        authors = item.get("authorString")
        journal = item.get("journalTitle")
        volume = str(item.get("journalVolume", "")) or None
        issue = str(item.get("issue", "")) or None
        pages = item.get("pageInfo")
        pub_year = int(item["pubYear"]) if "pubYear" in item and str(item["pubYear"]).isdigit() else None
        pub_date = item.get("firstPublicationDate")
        is_oa = 1 if item.get("isOpenAccess") == "Y" else 0
        citation_count = int(item.get("citedByCount", 0))

        return PublicationRecord(
            publication_id=canonical_id,
            title=title,
            doi=norm_doi,
            pmid=norm_pmid,
            pmcid=norm_pmcid,
            authors=authors,
            journal=journal,
            volume=volume,
            issue=issue,
            pages=pages,
            pub_year=pub_year,
            pub_date=pub_date,
            is_open_access=is_oa,
            license="Open Access" if is_oa else "Subscription",
            citation_count=citation_count,
            abstract=item.get("abstractText"),
        )
