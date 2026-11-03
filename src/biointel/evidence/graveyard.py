"""Institutional Technology Graveyard & Dead-End Autopsy Registry.

Records empirical autopsies of failed technology platforms, unviable scale-ups,
and thermodynamic dead-ends over 30+ years to prevent capital misallocation
and recurring historical mistakes.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from biointel.storage.database import Database


@dataclass
class GraveyardEntry:
    graveyard_id: str
    technology_id: str
    platform_name: str
    domain: str
    failure_mode: str
    fatal_flaw_summary: str
    terminal_doi: Optional[str]
    terminal_year: int
    capital_consumed_usd: float
    autopsy_markdown: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TechnologyGraveyardRegistry:
    """Archival registry and automated diligence auditor for failed technology lineages."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or Database()

    def record_failure(
        self,
        technology_id: str,
        platform_name: str,
        domain: str,
        failure_mode: str,
        fatal_flaw_summary: str,
        terminal_year: int,
        capital_consumed_usd: float,
        terminal_doi: Optional[str] = None,
        autopsy_markdown: str = "",
        graveyard_id: Optional[str] = None,
    ) -> GraveyardEntry:
        """Record an immutable autopsy of an abandoned technology or failed scale-up."""
        clean_tech = technology_id.strip().lower()
        if not graveyard_id:
            seed = f"{clean_tech}:{terminal_year}:{failure_mode.strip()}"
            graveyard_id = f"grave_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"

        record = {
            "graveyard_id": graveyard_id,
            "technology_id": clean_tech,
            "platform_name": platform_name.strip(),
            "domain": domain.strip().lower(),
            "failure_mode": failure_mode.strip().upper(),
            "fatal_flaw_summary": fatal_flaw_summary.strip(),
            "terminal_doi": terminal_doi.strip() if terminal_doi else None,
            "terminal_year": int(terminal_year),
            "capital_consumed_usd": float(capital_consumed_usd),
            "autopsy_markdown": autopsy_markdown.strip(),
        }

        self.db.insert_graveyard_entry(record)

        return GraveyardEntry(
            graveyard_id=graveyard_id,
            technology_id=clean_tech,
            platform_name=record["platform_name"],
            domain=record["domain"],
            failure_mode=record["failure_mode"],
            fatal_flaw_summary=record["fatal_flaw_summary"],
            terminal_doi=record["terminal_doi"],
            terminal_year=record["terminal_year"],
            capital_consumed_usd=record["capital_consumed_usd"],
            autopsy_markdown=record["autopsy_markdown"],
        )

    def query_dead_ends(self, query_str: str) -> List[GraveyardEntry]:
        """Search historical autopsies across keywords, failure modes, and domains."""
        self.seed_default_graveyard()
        rows = self.db.search_graveyard(query_str)
        return [
            GraveyardEntry(
                graveyard_id=r["graveyard_id"],
                technology_id=r["technology_id"],
                platform_name=r["platform_name"],
                domain=r["domain"],
                failure_mode=r["failure_mode"],
                fatal_flaw_summary=r["fatal_flaw_summary"],
                terminal_doi=r.get("terminal_doi"),
                terminal_year=r["terminal_year"],
                capital_consumed_usd=float(r["capital_consumed_usd"]),
                autopsy_markdown=r.get("autopsy_markdown", ""),
            )
            for r in rows
        ]

    def audit_technology_against_graveyard(self, tech_id: str) -> List[Dict[str, Any]]:
        """Audit a candidate platform against 30 years of recorded failure modes."""
        self.seed_default_graveyard()
        clean_tech = tech_id.strip().lower()
        tech = self.db.get_technology(clean_tech)
        warnings: List[Dict[str, Any]] = []

        if not tech:
            return warnings

        # Match domain and category against graveyard entries
        entries = self.db.get_graveyard_entries(domain=tech.get("domain"))
        desc = (tech.get("description") or "").lower()

        for entry in entries:
            plat_name = entry["platform_name"].lower()
            flaw = entry["fatal_flaw_summary"].lower()
            overlap_reasons = []

            if ("biofuel" in desc or "fuel" in desc) and ("fuel" in flaw or "biofuel" in flaw or "biofuel" in plat_name):
                overlap_reasons.append("Thermodynamic conversion of food-grade sugar into combustible hydrocarbons.")
            if "fermentation" in desc and ("viscosity" in flaw or "emulsion" in flaw or "ferment" in flaw):
                overlap_reasons.append("Downstream phase separation and high-viscosity broth handling limitations.")
            if ("crystallinity" in desc or "pet" in desc) and ("glass transition" in flaw or "crystallinity" in flaw):
                overlap_reasons.append("Operating below polymer substrate glass transition temperature prevents access to crystalline tie-chains.")
            if "delivery" in desc and ("endosomal" in flaw or "exonuclease" in flaw):
                overlap_reasons.append("In vivo systemic clearance and cellular barrier degradation.")

            if overlap_reasons:
                warnings.append({
                    "historical_analogy_platform": entry["platform_name"],
                    "failure_mode": entry["failure_mode"],
                    "fatal_flaw": entry["fatal_flaw_summary"],
                    "terminal_year": entry["terminal_year"],
                    "capital_sunk_usd": entry["capital_consumed_usd"],
                    "audit_findings": overlap_reasons,
                })

        return warnings

    def seed_default_graveyard(self) -> None:
        """Seed foundational industrial biotechnology failure autopsies."""
        existing = {e["technology_id"] for e in self.db.get_graveyard_entries()}

        defaults = [
            (
                "solazyme_algal_biofuels",
                "Solazyme / TerraVia Heterotrophic Algal Biofuels",
                "industrial_biotechnology",
                "ECONOMIC_UNCOMPETITIVE",
                "Heterotrophic microalgae fed refined food-grade sucrose yielded fuel oil at $12-$18/gallon. Converting $0.35/kg dextrose (4.0 kcal/g) into fuel (10.0 kcal/g) violates basic thermodynamic energy density economics.",
                2017,
                650_000_000.0,
                "10.1038/nbt.3061",
                "Full forensic autopsy of Solazyme: CapEx exceeding $40,000/ton capacity combined with 3.2:1 dextrose-to-oil conversion stoichiometry guaranteed insolvency against fossil crude.",
            ),
            (
                "amyris_bulk_farnesene_biofuels",
                "Amyris Bulk Farnesene Biofuel Scale-up",
                "industrial_biotechnology",
                "SCALEUP_PHASE_INVERSION",
                "Engineered yeast mevalonate pathway suffered metabolic burden and cellular instability in 200 m3 industrial fermenters. Downstream separation of farnesene required expensive solvent extraction and broke emulsions poorly at production titers.",
                2017,
                1_200_000_000.0,
                "10.1016/j.biotechadv.2017.07.009",
                "Amyris Brotas facility autopsy: Volumetric productivity collapsed 60% upon transition from 10 L pilot to 200,000 L commercial vessels due to oxygen transfer rate (OTR) gradients.",
            ),
            (
                "first_gen_mesophilic_ispetase",
                "Wild-Type & Mesophilic IsPETase Biorecycling",
                "industrial_biotechnology",
                "THERMODYNAMIC_UNVIABLE",
                "Wild-type IsPETase denatures within hours at temperatures above 37°C. Commercial post-consumer PET has a glass transition temperature Tg of ~75°C and crystallinity >15%, where enzyme turnover rate is negligible.",
                2018,
                35_000_000.0,
                "10.1073/pnas.1718804115",
                "First-generation enzyme autopsy: Thermal melting temperature (Tm = 48.8°C) locked reaction kinetics in the glassy polymer regime, requiring high-temperature directed evolution.",
            ),
        ]

        for tech_id, name, domain, mode, flaw, year, cap, doi, md in defaults:
            if tech_id not in existing:
                self.record_failure(
                    technology_id=tech_id,
                    platform_name=name,
                    domain=domain,
                    failure_mode=mode,
                    fatal_flaw_summary=flaw,
                    terminal_year=year,
                    capital_consumed_usd=cap,
                    terminal_doi=doi,
                    autopsy_markdown=md,
                )
