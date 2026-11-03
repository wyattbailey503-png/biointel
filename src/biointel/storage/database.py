"""BioIntel SQLite Storage Layer.

Provides thread-safe access, transaction management, schema migrations,
and domain-specific query/persistence helpers.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


class Database:
    """SQLite Database manager for BioIntel."""

    def __init__(self, db_path: str | Path = "biointel.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Create a connection with standard row factories and pragmas."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        """Context manager for atomic database transactions."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_schema(self) -> None:
        """Execute schema.sql idempotently."""
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")

        schema_sql = schema_path.read_text(encoding="utf-8")
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            # Automatic schema migration for existing tables
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(experiments);")
            exp_cols = [col[1] for col in cur.fetchall()]
            for col in ["experiment_date", "publication_date", "discovery_date"]:
                if col not in exp_cols:
                    cur.execute(f"ALTER TABLE experiments ADD COLUMN {col} TEXT;")


    # -------------------------------------------------------------------------
    # Sources & Discovery
    # -------------------------------------------------------------------------
    def upsert_source(self, source_dict: Dict[str, Any]) -> None:
        """Upsert a source into source_registry."""
        sql = """
        INSERT INTO source_registry (
            source_id, name, publisher, url, category, adapter_type,
            api_version, rate_limit_per_min, licensing, priority,
            monitoring_frequency_hours, last_successful_retrieval,
            last_attempt, retry_state
        ) VALUES (
            :source_id, :name, :publisher, :url, :category, :adapter_type,
            :api_version, :rate_limit_per_min, :licensing, :priority,
            :monitoring_frequency_hours, :last_successful_retrieval,
            :last_attempt, :retry_state
        ) ON CONFLICT(source_id) DO UPDATE SET
            name = excluded.name,
            publisher = excluded.publisher,
            url = excluded.url,
            category = excluded.category,
            adapter_type = excluded.adapter_type,
            rate_limit_per_min = excluded.rate_limit_per_min,
            licensing = excluded.licensing,
            priority = excluded.priority,
            monitoring_frequency_hours = excluded.monitoring_frequency_hours,
            last_successful_retrieval = COALESCE(excluded.last_successful_retrieval, source_registry.last_successful_retrieval),
            last_attempt = COALESCE(excluded.last_attempt, source_registry.last_attempt),
            retry_state = excluded.retry_state,
            updated_at = CURRENT_TIMESTAMP;
        """
        with self.transaction() as cur:
            cur.execute(sql, {
                "source_id": source_dict["source_id"],
                "name": source_dict["name"],
                "publisher": source_dict["publisher"],
                "url": source_dict["url"],
                "category": source_dict["category"],
                "adapter_type": source_dict.get("adapter_type", source_dict["source_id"]),
                "api_version": source_dict.get("api_version"),
                "rate_limit_per_min": source_dict.get("rate_limit_per_min", 60),
                "licensing": source_dict.get("licensing", "Open"),
                "priority": source_dict.get("priority", 1),
                "monitoring_frequency_hours": source_dict.get("monitoring_frequency_hours", 24),
                "last_successful_retrieval": source_dict.get("last_successful_retrieval"),
                "last_attempt": source_dict.get("last_attempt"),
                "retry_state": source_dict.get("retry_state", "ready"),
            })

    def get_sources(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM source_registry ORDER BY priority ASC, name ASC").fetchall()
            return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Documents & Publications
    # -------------------------------------------------------------------------
    def upsert_document(self, doc_dict: Dict[str, Any], raw_payload: Optional[str] = None) -> bool:
        """Upsert document. Returns True if new or updated version was created."""
        with self.transaction() as cur:
            cur.execute(
                "SELECT content_hash FROM documents WHERE document_id = ?",
                (doc_dict["document_id"],)
            )
            existing = cur.fetchone()

            is_new_or_updated = False
            if not existing:
                cur.execute(
                    """
                    INSERT INTO documents (document_id, source_id, external_id, title, url, content_hash, format, ingestion_status)
                    VALUES (:document_id, :source_id, :external_id, :title, :url, :content_hash, :format, :ingestion_status)
                    """,
                    doc_dict
                )
                cur.execute(
                    """
                    INSERT INTO document_versions (document_id, version_number, content_hash, raw_payload)
                    VALUES (?, 1, ?, ?)
                    """,
                    (doc_dict["document_id"], doc_dict["content_hash"], raw_payload)
                )
                is_new_or_updated = True
            elif existing["content_hash"] != doc_dict["content_hash"]:
                cur.execute(
                    """
                    UPDATE documents
                    SET title = :title, url = :url, content_hash = :content_hash, updated_at = CURRENT_TIMESTAMP
                    WHERE document_id = :document_id
                    """,
                    doc_dict
                )
                cur.execute(
                    "SELECT MAX(version_number) AS max_v FROM document_versions WHERE document_id = ?",
                    (doc_dict["document_id"],)
                )
                next_v = (cur.fetchone()["max_v"] or 0) + 1
                cur.execute(
                    """
                    INSERT INTO document_versions (document_id, version_number, content_hash, raw_payload)
                    VALUES (?, ?, ?, ?)
                    """,
                    (doc_dict["document_id"], next_v, doc_dict["content_hash"], raw_payload)
                )
                is_new_or_updated = True

            return is_new_or_updated

    def upsert_publication(self, pub_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT INTO publications (
            publication_id, doi, pmid, pmcid, title, authors, journal,
            volume, issue, pages, pub_year, pub_date, is_open_access,
            license, citation_count, abstract
        ) VALUES (
            :publication_id, :doi, :pmid, :pmcid, :title, :authors, :journal,
            :volume, :issue, :pages, :pub_year, :pub_date, :is_open_access,
            :license, :citation_count, :abstract
        ) ON CONFLICT(publication_id) DO UPDATE SET
            doi = COALESCE(excluded.doi, publications.doi),
            pmid = COALESCE(excluded.pmid, publications.pmid),
            pmcid = COALESCE(excluded.pmcid, publications.pmcid),
            title = excluded.title,
            authors = excluded.authors,
            journal = excluded.journal,
            volume = excluded.volume,
            issue = excluded.issue,
            pages = excluded.pages,
            pub_year = excluded.pub_year,
            pub_date = excluded.pub_date,
            is_open_access = excluded.is_open_access,
            license = excluded.license,
            citation_count = excluded.citation_count,
            abstract = excluded.abstract;
        """
        with self.transaction() as cur:
            cur.execute(sql, pub_dict)

    def get_publications(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM publications ORDER BY pub_year DESC, pub_date DESC").fetchall()
            return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Technologies
    # -------------------------------------------------------------------------
    def upsert_technology(self, tech_dict: Dict[str, Any]) -> None:
        c_name = tech_dict.get("canonical_name") or tech_dict["tech_id"]
        payload = dict(tech_dict)
        payload["canonical_name"] = c_name
        with self.transaction() as cur:
            row = cur.execute(
                "SELECT tech_id FROM technologies WHERE tech_id = ? OR canonical_name = ?",
                (payload["tech_id"], c_name),
            ).fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE technologies
                    SET name = :name,
                        canonical_name = :canonical_name,
                        domain = :domain,
                        category = :category,
                        maturity_stage = :maturity_stage,
                        description = :description,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE tech_id = :existing_id
                    """,
                    {**payload, "existing_id": row[0]},
                )
            else:
                cur.execute(
                    """
                    INSERT INTO technologies (tech_id, name, canonical_name, domain, category, maturity_stage, description)
                    VALUES (:tech_id, :name, :canonical_name, :domain, :category, :maturity_stage, :description)
                    """,
                    payload,
                )


    def get_technology(self, tech_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM technologies WHERE tech_id = ? OR canonical_name = ?", (tech_id, tech_id)).fetchone()
            return dict(row) if row else None

    def get_technologies(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM technologies ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Molecular Structures
    # -------------------------------------------------------------------------
    def upsert_structure(self, struct_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT INTO structures (
            structure_id, pdb_id, protein_id, classification, experimental_method,
            resolution_angstrom, r_factor_free, organism, mutations, bound_ligands,
            coordinate_path, source_url, download_timestamp, version_revision
        ) VALUES (
            :structure_id, :pdb_id, :protein_id, :classification, :experimental_method,
            :resolution_angstrom, :r_factor_free, :organism, :mutations, :bound_ligands,
            :coordinate_path, :source_url, :download_timestamp, :version_revision
        ) ON CONFLICT(pdb_id) DO UPDATE SET
            classification = excluded.classification,
            experimental_method = excluded.experimental_method,
            resolution_angstrom = excluded.resolution_angstrom,
            r_factor_free = excluded.r_factor_free,
            organism = excluded.organism,
            mutations = excluded.mutations,
            bound_ligands = excluded.bound_ligands,
            coordinate_path = excluded.coordinate_path,
            source_url = excluded.source_url,
            download_timestamp = excluded.download_timestamp,
            version_revision = excluded.version_revision;
        """
        with self.transaction() as cur:
            cur.execute(sql, struct_dict)

    def get_structure(self, pdb_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM structures WHERE pdb_id = ? OR structure_id = ?", (pdb_id.upper(), pdb_id)).fetchone()
            return dict(row) if row else None

    # -------------------------------------------------------------------------
    # Experiments & Results
    # -------------------------------------------------------------------------
    def insert_experiment(self, exp_dict: Dict[str, Any]) -> None:
        d = dict(exp_dict)
        defaults = {
            "biological_question": None,
            "hypothesis": None,
            "species": None,
            "cell_line_or_tissue": None,
            "control_group": None,
            "dose_concentration": None,
            "exposure_duration": None,
            "measurement_time": None,
            "sample_size": None,
            "biological_replicates": None,
            "technical_replicates": None,
            "evidence_location": None,
            "limitations": None,
            "experiment_date": None,
            "publication_date": None,
            "discovery_date": None,
        }
        for k, v in defaults.items():
            d.setdefault(k, v)
        sql = """
        INSERT OR REPLACE INTO experiments (
            experiment_id, publication_id, biological_question, hypothesis,
            experimental_method, model_system, species, cell_line_or_tissue,
            treatment_intervention, control_group, dose_concentration,
            exposure_duration, measurement_time, sample_size, biological_replicates,
            technical_replicates, evidence_category, evidence_location, limitations,
            experiment_date, publication_date, discovery_date
        ) VALUES (
            :experiment_id, :publication_id, :biological_question, :hypothesis,
            :experimental_method, :model_system, :species, :cell_line_or_tissue,
            :treatment_intervention, :control_group, :dose_concentration,
            :exposure_duration, :measurement_time, :sample_size, :biological_replicates,
            :technical_replicates, :evidence_category, :evidence_location, :limitations,
            :experiment_date, :publication_date, :discovery_date
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, d)

    def insert_evidence_relationship(self, rel_dict: Dict[str, Any]) -> int:
        sql = """
        INSERT INTO evidence_relationships (
            source_id, target_id, relation_type, confidence_score, explanation, metadata_json
        ) VALUES (
            :source_id, :target_id, :relation_type, :confidence_score, :explanation, :metadata_json
        );
        """
        d = dict(rel_dict)
        d.setdefault("confidence_score", 1.0)
        d.setdefault("explanation", "")
        if isinstance(d.get("metadata_json"), (dict, list)):
            d["metadata_json"] = json.dumps(d["metadata_json"])
        else:
            d.setdefault("metadata_json", None)
        with self.transaction() as cur:
            cur.execute(sql, d)
            return cur.lastrowid or 0

    def get_evidence_relationships(self, source_or_target_id: Optional[str] = None, relation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM evidence_relationships WHERE 1=1"
        params: List[Any] = []
        if source_or_target_id:
            query += " AND (source_id = ? OR target_id = ?)"
            params.extend([source_or_target_id, source_or_target_id])
        if relation_type:
            query += " AND relation_type = ?"
            params.append(relation_type)
        query += " ORDER BY created_at ASC"
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_technology_evidence_timeline(self, tech_id: str, as_of_date: Optional[str] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                p.publication_id, p.doi, p.title, p.pub_date, p.pub_year, p.authors,
                e.experiment_id, e.experimental_method, e.model_system, e.treatment_intervention,
                e.limitations, e.experiment_date, e.publication_date,
                r.result_id, r.measured_endpoint, r.value, r.unit, r.p_value,
                c.claim_id, c.claim_statement, c.claim_type
            FROM claims c
            JOIN evidence_links el ON c.claim_id = el.claim_id
            JOIN experiments e ON el.experiment_id = e.experiment_id
            JOIN publications p ON e.publication_id = p.publication_id
            LEFT JOIN experimental_results r ON e.experiment_id = r.experiment_id
            WHERE c.technology_id = ?
        """
        params: List[Any] = [tech_id]
        if as_of_date:
            query += " AND (COALESCE(e.publication_date, p.pub_date, CAST(p.pub_year AS TEXT)) <= ?)"
            params.append(as_of_date)
        query += " ORDER BY COALESCE(e.publication_date, p.pub_date, CAST(p.pub_year AS TEXT)) ASC"

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def insert_experimental_result(self, res_dict: Dict[str, Any]) -> None:
        d = dict(res_dict)
        defaults = {
            "assay_id": None,
            "standard_deviation": None,
            "confidence_interval": None,
            "p_value": None,
            "statistical_method": None,
            "effect_size": None,
            "raw_summary": None,
        }
        for k, v in defaults.items():
            d.setdefault(k, v)
        sql = """
        INSERT OR REPLACE INTO experimental_results (
            result_id, experiment_id, assay_id, measured_endpoint, value,
            unit, standard_deviation, confidence_interval, p_value,
            statistical_method, effect_size, raw_summary
        ) VALUES (
            :result_id, :experiment_id, :assay_id, :measured_endpoint, :value,
            :unit, :standard_deviation, :confidence_interval, :p_value,
            :statistical_method, :effect_size, :raw_summary
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, d)


    def get_experiments_for_publication(self, pub_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT e.*, r.measured_endpoint, r.value, r.unit, r.standard_deviation, r.p_value, r.effect_size
                FROM experiments e
                LEFT JOIN experimental_results r ON e.experiment_id = r.experiment_id
                WHERE e.publication_id = ?
            """, (pub_id,)).fetchall()
            return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Claims & Evidence Links
    # -------------------------------------------------------------------------
    def insert_claim(self, claim_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT OR REPLACE INTO claims (claim_id, technology_id, claim_statement, claim_type, mechanistic_assertion)
        VALUES (:claim_id, :technology_id, :claim_statement, :claim_type, :mechanistic_assertion);
        """
        with self.transaction() as cur:
            cur.execute(sql, claim_dict)

    def link_evidence(self, link_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT INTO evidence_links (claim_id, experiment_id, support_direction, confidence_score, explanation)
        VALUES (:claim_id, :experiment_id, :support_direction, :confidence_score, :explanation);
        """
        with self.transaction() as cur:
            cur.execute(sql, link_dict)

    # -------------------------------------------------------------------------
    # Competitor Comparisons & Scientific Changes
    # -------------------------------------------------------------------------
    def insert_competitor_match(self, match_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT OR REPLACE INTO competitor_matches (
            comparison_id, technology_a_id, technology_b_id, comparison_domain,
            shared_target_or_objective, comparison_matrix, incompatibility_warnings,
            strategic_takeaway
        ) VALUES (
            :comparison_id, :technology_a_id, :technology_b_id, :comparison_domain,
            :shared_target_or_objective, :comparison_matrix, :incompatibility_warnings,
            :strategic_takeaway
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, match_dict)

    def insert_scientific_change(self, change_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT OR REPLACE INTO scientific_changes (
            change_id, technology_id, change_type, title, previous_state,
            new_state, primary_source_id, scientific_significance,
            commercial_implication, diligence_questions
        ) VALUES (
            :change_id, :technology_id, :change_type, :title, :previous_state,
            :new_state, :primary_source_id, :scientific_significance,
            :commercial_implication, :diligence_questions
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, change_dict)

    def get_scientific_changes(self, tech_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if tech_id:
                rows = conn.execute("SELECT * FROM scientific_changes WHERE technology_id = ? ORDER BY created_at DESC", (tech_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM scientific_changes ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def insert_technology_milestone(self, milestone_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT OR REPLACE INTO technology_milestones (
            milestone_id, technology_id, milestone_date, title, milestone_type,
            doi, primary_source, previous_state, new_state,
            scientific_significance, commercial_implication,
            structures_json, limitations_json, metrics_json
        ) VALUES (
            :milestone_id, :technology_id, :milestone_date, :title, :milestone_type,
            :doi, :primary_source, :previous_state, :new_state,
            :scientific_significance, :commercial_implication,
            :structures_json, :limitations_json, :metrics_json
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, milestone_dict)

    def get_technology_milestones(
        self, tech_id: str, as_of_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM technology_milestones WHERE technology_id = ?"
        params: List[Any] = [tech_id]
        if as_of_date:
            query += " AND milestone_date <= ?"
            params.append(as_of_date)
        query += " ORDER BY milestone_date ASC, created_at ASC"
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Techno-Economics & Reports

    # -------------------------------------------------------------------------
    def insert_economic_scenario(self, scenario_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT OR REPLACE INTO economic_scenarios (
            scenario_id, technology_id, model_type, inputs_json, outputs_json,
            unit_cost_usd_per_unit, annual_capacity_kg, break_even_price
        ) VALUES (
            :scenario_id, :technology_id, :model_type, :inputs_json, :outputs_json,
            :unit_cost_usd_per_unit, :annual_capacity_kg, :break_even_price
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, scenario_dict)

    def insert_research_report(self, report_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT OR REPLACE INTO research_reports (
            report_id, technology_id, report_type, title, content_markdown,
            version_tag, file_path
        ) VALUES (
            :report_id, :technology_id, :report_type, :title, :content_markdown,
            :version_tag, :file_path
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, report_dict)

    # -------------------------------------------------------------------------
    # Pipeline Runs Audit
    # -------------------------------------------------------------------------
    def record_pipeline_run(self, run_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT OR REPLACE INTO pipeline_runs (
            run_id, run_type, started_at, completed_at, status, sources_checked,
            documents_discovered, documents_updated, new_technologies,
            new_experiments, failed_requests, rate_limit_events, report_summary
        ) VALUES (
            :run_id, :run_type, :started_at, :completed_at, :status, :sources_checked,
            :documents_discovered, :documents_updated, :new_technologies,
            :new_experiments, :failed_requests, :rate_limit_events, :report_summary
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, run_dict)

    # -------------------------------------------------------------------------
    # Long-Horizon Prediction Contracts & Resolutions
    # -------------------------------------------------------------------------
    def insert_prediction_contract(self, contract_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT OR REPLACE INTO prediction_contracts (
            contract_id, technology_id, horizon_years, target_date, target_metric,
            p10_estimate, p50_estimate, p90_estimate, unit, falsification_criteria,
            comparator_hypothesis, status, model_provenance_seal
        ) VALUES (
            :contract_id, :technology_id, :horizon_years, :target_date, :target_metric,
            :p10_estimate, :p50_estimate, :p90_estimate, :unit, :falsification_criteria,
            :comparator_hypothesis, :status, :model_provenance_seal
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, contract_dict)

    def get_prediction_contracts(
        self, tech_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM prediction_contracts WHERE 1=1"
        params: List[Any] = []
        if tech_id:
            query += " AND technology_id = ?"
            params.append(tech_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY target_date ASC, created_at ASC"
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_prediction_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM prediction_contracts WHERE contract_id = ?", (contract_id,)).fetchone()
            return dict(row) if row else None

    def insert_prediction_resolution(self, res_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT OR REPLACE INTO prediction_resolutions (
            resolution_id, contract_id, resolved_date, empirical_value, primary_source_doi,
            residual_error, relative_error_pct, brier_score, outcome_status,
            parameter_attribution_json, resolution_notes
        ) VALUES (
            :resolution_id, :contract_id, :resolved_date, :empirical_value, :primary_source_doi,
            :residual_error, :relative_error_pct, :brier_score, :outcome_status,
            :parameter_attribution_json, :resolution_notes
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, res_dict)
            cur.execute(
                "UPDATE prediction_contracts SET status = :status WHERE contract_id = :contract_id",
                {"status": res_dict.get("outcome_status", "RESOLVED"), "contract_id": res_dict["contract_id"]},
            )

    def get_prediction_resolutions(self) -> List[Dict[str, Any]]:
        query = """
        SELECT pr.*, pc.technology_id, pc.target_metric, pc.target_date, pc.p50_estimate
        FROM prediction_resolutions pr
        JOIN prediction_contracts pc ON pr.contract_id = pc.contract_id
        ORDER BY pr.resolved_date ASC
        """
        with self.get_connection() as conn:
            rows = conn.execute(query).fetchall()
            return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Technology Graveyard & Dead-End Autopsies
    # -------------------------------------------------------------------------
    def insert_graveyard_entry(self, entry_dict: Dict[str, Any]) -> None:
        sql = """
        INSERT OR REPLACE INTO technology_graveyard (
            graveyard_id, technology_id, platform_name, domain, failure_mode,
            fatal_flaw_summary, terminal_doi, terminal_year, capital_consumed_usd,
            autopsy_markdown
        ) VALUES (
            :graveyard_id, :technology_id, :platform_name, :domain, :failure_mode,
            :fatal_flaw_summary, :terminal_doi, :terminal_year, :capital_consumed_usd,
            :autopsy_markdown
        );
        """
        with self.transaction() as cur:
            cur.execute(sql, entry_dict)

    def get_graveyard_entries(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM technology_graveyard WHERE 1=1"
        params: List[Any] = []
        if domain:
            query += " AND domain = ?"
            params.append(domain)
        query += " ORDER BY terminal_year DESC, capital_consumed_usd DESC"
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def search_graveyard(self, query_str: str) -> List[Dict[str, Any]]:
        pattern = f"%{query_str.lower()}%"
        sql = """
        SELECT * FROM technology_graveyard
        WHERE LOWER(technology_id) LIKE ?
           OR LOWER(platform_name) LIKE ?
           OR LOWER(fatal_flaw_summary) LIKE ?
           OR LOWER(failure_mode) LIKE ?
           OR LOWER(domain) LIKE ?
        ORDER BY terminal_year DESC
        """
        with self.get_connection() as conn:
            rows = conn.execute(sql, (pattern, pattern, pattern, pattern, pattern)).fetchall()
            return [dict(r) for r in rows]

