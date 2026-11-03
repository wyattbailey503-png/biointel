"""Bibliometric Co-Authorship & Institutional Replication Network Analyzer.

Disambiguates genuine external independent replications from internal circular re-testing
(pseudo-replications) by analyzing co-authorship networks, institutional affiliations,
and patent assignee relationships.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Set, Tuple


@dataclass
class PublicationMetadataNode:
    doi: str
    title: str
    year: int
    authors: List[str]
    senior_author: str
    affiliations: List[str]
    grant_numbers: List[str]
    patent_assignees: List[str]


@dataclass
class ReplicationPairAudit:
    source_doi: str
    target_doi: str
    shared_authors: List[str]
    is_senior_author_shared: bool
    shared_institutions: List[str]
    shared_grants: List[str]
    replication_classification: str
    reproducibility_weight: float  # 0.0 (circular self-citation) to 1.0 (strict independent consortium)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NetworkReplicationSummary:
    total_publications: int
    distinct_institutions_count: int
    distinct_senior_investigators_count: int
    genuine_external_replications_count: int
    internal_followup_count: int
    network_independence_ratio: float
    pairwise_audits: List[ReplicationPairAudit]
    evidence_independence_verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ReplicationNetworkAnalyzer:
    """Graph analyzer detecting pseudo-independent replications in scientific literature."""

    @classmethod
    def _normalize_name(cls, name: str) -> str:
        """Normalizes author name: e.g. 'Beckham, Gregg T.' -> 'beckham, g'."""
        clean = re.sub(r"[^a-zA-Z\s,]", "", name).strip().lower()
        parts = clean.split(",")
        if len(parts) >= 2:
            last = parts[0].strip()
            first = parts[1].strip()
            initial = first[0] if first else ""
            return f"{last}_{initial}"
        words = clean.split()
        if len(words) >= 2:
            return f"{words[-1]}_{words[0][0]}"
        return clean

    @classmethod
    def _normalize_institution(cls, inst: str) -> str:
        """Extracts core institutional keyword: e.g. 'National Renewable Energy Laboratory' -> 'nrel'."""
        s = inst.lower()
        if "nrel" in s or "national renewable energy" in s:
            return "nrel"
        if "portsmouth" in s:
            return "univ_portsmouth"
        if "austin" in s or "texas" in s:
            return "ut_austin"
        if "carbios" in s:
            return "carbios"
        if "toulouse" in s or "insa" in s or "inra" in s:
            return "toulouse_biotech"
        if "kyoto" in s or "kit" in s:
            return "kyoto_inst_tech"
        # Return simplified alphanumeric slug
        return re.sub(r"[^a-z0-9]", "_", s)[:20]

    @classmethod
    def audit_replication_pair(
        cls,
        pub_a: PublicationMetadataNode,
        pub_b: PublicationMetadataNode,
    ) -> ReplicationPairAudit:
        """Audits the degree of independence between two research publications."""
        authors_a = {cls._normalize_name(a) for a in pub_a.authors}
        authors_b = {cls._normalize_name(b) for b in pub_b.authors}
        shared_authors = sorted(list(authors_a.intersection(authors_b)))

        senior_a = cls._normalize_name(pub_a.senior_author)
        senior_b = cls._normalize_name(pub_b.senior_author)
        senior_shared = (senior_a == senior_b) and bool(senior_a)

        insts_a = {cls._normalize_institution(i) for i in pub_a.affiliations}
        insts_b = {cls._normalize_institution(i) for i in pub_b.affiliations}
        shared_insts = sorted(list(insts_a.intersection(insts_b)))

        grants_a = set(pub_a.grant_numbers)
        grants_b = set(pub_b.grant_numbers)
        shared_grants = sorted(list(grants_a.intersection(grants_b)))

        # Classification hierarchy:
        if senior_shared:
            classification = "INTERNAL_SAME_LAB_FOLLOW_UP (SHARED PRINCIPAL INVESTIGATOR)"
            weight = 0.20
        elif len(shared_authors) >= 2:
            classification = "COLLABORATIVE_CONSORTIUM_EXTENSION (SHARED CO-INVESTIGATORS)"
            weight = 0.45
        elif len(shared_insts) > 0 and len(shared_grants) > 0:
            classification = "SAME_INSTITUTION_COMMON_FUNDING (POTENTIAL SHARED SAMPLES/REAGENTS)"
            weight = 0.60
        elif len(shared_insts) > 0:
            classification = "INTRA_INSTITUTIONAL_INDEPENDENT_GROUP"
            weight = 0.75
        else:
            classification = "GENUINE_EXTERNAL_INDEPENDENT_REPLICATION"
            weight = 1.00

        return ReplicationPairAudit(
            source_doi=pub_a.doi,
            target_doi=pub_b.doi,
            shared_authors=shared_authors,
            is_senior_author_shared=senior_shared,
            shared_institutions=shared_insts,
            shared_grants=shared_grants,
            replication_classification=classification,
            reproducibility_weight=weight,
        )

    @classmethod
    def analyze_technology_network(
        cls,
        publications: List[PublicationMetadataNode],
    ) -> NetworkReplicationSummary:
        """Performs full network audit across all publications claiming technology milestones."""
        n = len(publications)
        if n < 1:
            raise ValueError("Network analysis requires at least one publication.")

        distinct_insts: Set[str] = set()
        distinct_seniors: Set[str] = set()

        for p in publications:
            for inst in p.affiliations:
                distinct_insts.add(cls._normalize_institution(inst))
            distinct_seniors.add(cls._normalize_name(p.senior_author))

        pairwise_audits: List[ReplicationPairAudit] = []
        genuine_external = 0
        internal_followup = 0

        # Sort chronologically by publication year
        sorted_pubs = sorted(publications, key=lambda x: x.year)

        for i in range(len(sorted_pubs)):
            for j in range(i + 1, len(sorted_pubs)):
                audit = cls.audit_replication_pair(sorted_pubs[i], sorted_pubs[j])
                pairwise_audits.append(audit)
                if audit.reproducibility_weight >= 0.90:
                    genuine_external += 1
                else:
                    internal_followup += 1

        total_pairs = max(1, len(pairwise_audits))
        independence_ratio = genuine_external / total_pairs

        if independence_ratio >= 0.50 and len(distinct_seniors) >= 3:
            verdict = "ROBUST_INDEPENDENT_SCIENTIFIC_VALIDATION (MULTI-CONSORTIUM CONFIRMED)"
        elif genuine_external >= 1:
            verdict = "PARTIAL_INDEPENDENT_REPLICATION (PREDOMINANTLY FOUNDING LAB CONCENTRATION)"
        else:
            verdict = "CIRCULAR_SINGLE_INSTITUTION_EVALUATION (NO EXTERNAL REPLICATION ESTABLISHED)"

        return NetworkReplicationSummary(
            total_publications=n,
            distinct_institutions_count=len(distinct_insts),
            distinct_senior_investigators_count=len(distinct_seniors),
            genuine_external_replications_count=genuine_external,
            internal_followup_count=internal_followup,
            network_independence_ratio=round(independence_ratio, 3),
            pairwise_audits=pairwise_audits,
            evidence_independence_verdict=verdict,
        )
