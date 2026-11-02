-- BioIntel SQLite Schema
-- Normalized relational store for continuous biotechnology discovery and evidence intelligence

PRAGMA foreign_keys = ON;

-- 1. Source Registry
CREATE TABLE IF NOT EXISTS source_registry (
    source_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    publisher TEXT NOT NULL,
    url TEXT NOT NULL,
    category TEXT NOT NULL,
    adapter_type TEXT NOT NULL,
    api_version TEXT,
    rate_limit_per_min INTEGER NOT NULL DEFAULT 60,
    last_successful_retrieval TEXT,
    last_attempt TEXT,
    licensing TEXT,
    retry_state TEXT DEFAULT 'ready',
    priority INTEGER DEFAULT 1,
    monitoring_frequency_hours INTEGER DEFAULT 24,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. Documents and Versions (Raw Payloads)
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT,
    url TEXT,
    content_hash TEXT NOT NULL,
    format TEXT DEFAULT 'json',
    ingestion_status TEXT DEFAULT 'ingested',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES source_registry(source_id)
);

CREATE TABLE IF NOT EXISTS document_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    raw_payload TEXT,
    retrieved_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    UNIQUE (document_id, version_number)
);

-- 3. Publications
CREATE TABLE IF NOT EXISTS publications (
    publication_id TEXT PRIMARY KEY,
    doi TEXT UNIQUE,
    pmid TEXT UNIQUE,
    pmcid TEXT,
    title TEXT NOT NULL,
    authors TEXT,
    journal TEXT,
    volume TEXT,
    issue TEXT,
    pages TEXT,
    pub_year INTEGER,
    pub_date TEXT,
    is_open_access INTEGER DEFAULT 0,
    license TEXT,
    citation_count INTEGER DEFAULT 0,
    abstract TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 4. Organizations & Companies
CREATE TABLE IF NOT EXISTS organizations (
    org_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    org_type TEXT NOT NULL, -- 'company', 'academic', 'institute', 'consortium'
    website TEXT,
    founding_year INTEGER,
    headquarters TEXT,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 5. Technologies & Platforms
CREATE TABLE IF NOT EXISTS technologies (
    tech_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    canonical_name TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    category TEXT NOT NULL,
    maturity_stage TEXT NOT NULL, -- 'discovery', 'lead_optimization', 'preclinical', 'clinical_trial', 'authorized', 'pilot_scale', 'commercial'
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 6. Genes and Proteins
CREATE TABLE IF NOT EXISTS genes (
    gene_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    ncbi_gene_id TEXT,
    ensembl_id TEXT,
    organism TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proteins (
    protein_id TEXT PRIMARY KEY,
    uniprot_accession TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    gene_id TEXT,
    organism TEXT NOT NULL,
    sequence TEXT,
    sequence_length INTEGER,
    molecular_function TEXT,
    subcellular_location TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gene_id) REFERENCES genes(gene_id)
);

-- 7. Molecular Structures
CREATE TABLE IF NOT EXISTS structures (
    structure_id TEXT PRIMARY KEY, -- e.g., 'pdb_7k38'
    pdb_id TEXT UNIQUE NOT NULL,
    protein_id TEXT,
    classification TEXT NOT NULL, -- 'experimental', 'predicted'
    experimental_method TEXT, -- 'X-ray diffraction', 'Cryo-EM', 'NMR', 'AlphaFold'
    resolution_angstrom REAL,
    r_factor_free REAL,
    organism TEXT,
    mutations TEXT,
    bound_ligands TEXT,
    coordinate_path TEXT,
    source_url TEXT NOT NULL,
    download_timestamp TEXT,
    version_revision TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (protein_id) REFERENCES proteins(protein_id)
);

-- 8. Experiments, Assays, and Results
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    publication_id TEXT NOT NULL,
    biological_question TEXT,
    hypothesis TEXT,
    experimental_method TEXT NOT NULL,
    model_system TEXT NOT NULL, -- 'in_vitro', 'cell_line', 'primary_cells', 'organoid', 'animal', 'human_clinical'
    species TEXT,
    cell_line_or_tissue TEXT,
    treatment_intervention TEXT NOT NULL,
    control_group TEXT,
    dose_concentration TEXT,
    exposure_duration TEXT,
    measurement_time TEXT,
    sample_size INTEGER,
    biological_replicates INTEGER,
    technical_replicates INTEGER,
    evidence_category TEXT NOT NULL,
    evidence_location TEXT, -- e.g., 'Fig 2C, p. 6426'
    limitations TEXT,
    experiment_date TEXT,
    publication_date TEXT,
    discovery_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (publication_id) REFERENCES publications(publication_id)
);

CREATE TABLE IF NOT EXISTS assays (
    assay_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    assay_type TEXT NOT NULL,
    target_substrate TEXT,
    readout_technology TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS experimental_results (
    result_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    assay_id TEXT,
    measured_endpoint TEXT NOT NULL, -- 'editing_efficiency', 'titer', 'off_target_rate', 'kd', 'thermal_melting_tm'
    value REAL,
    unit TEXT,
    standard_deviation REAL,
    confidence_interval TEXT,
    p_value REAL,
    statistical_method TEXT,
    effect_size REAL,
    raw_summary TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY (assay_id) REFERENCES assays(assay_id)
);

-- 9. Claims and Evidence Links
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    technology_id TEXT,
    claim_statement TEXT NOT NULL,
    claim_type TEXT NOT NULL, -- 'efficacy', 'specificity', 'safety', 'yield', 'stability', 'scalability'
    mechanistic_assertion TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (technology_id) REFERENCES technologies(tech_id)
);

CREATE TABLE IF NOT EXISTS evidence_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    support_direction TEXT NOT NULL, -- 'supports', 'contradicts', 'inconclusive'
    confidence_score REAL DEFAULT 1.0,
    explanation TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
);

CREATE TABLE IF NOT EXISTS evidence_relationships (
    rel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL, -- 'SUPPORTS', 'CONTRADICTS', 'REPLICATES', 'EXTENDS', 'REFINES', 'USES_METHOD', 'EVALUATES_TECHNOLOGY', 'DEMONSTRATES_SCALE', 'REPORTS_SAFETY_CONCERN', 'ASSOCIATED_WITH_COMPANY'
    confidence_score REAL DEFAULT 1.0,
    explanation TEXT,
    metadata_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 10. Technology Relationships & Lineage
CREATE TABLE IF NOT EXISTS technology_relationships (
    rel_id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_tech_id TEXT NOT NULL,
    target_tech_id TEXT NOT NULL,
    relation_type TEXT NOT NULL, -- 'enables', 'improves_upon', 'competes_with', 'derived_from'
    provenance_doc_id TEXT,
    is_hypothesis INTEGER DEFAULT 0,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_tech_id) REFERENCES technologies(tech_id),
    FOREIGN KEY (target_tech_id) REFERENCES technologies(tech_id)
);

-- 11. Competitor Matches and Condition Comparisons
CREATE TABLE IF NOT EXISTS competitor_matches (
    comparison_id TEXT PRIMARY KEY,
    technology_a_id TEXT NOT NULL,
    technology_b_id TEXT NOT NULL,
    comparison_domain TEXT NOT NULL,
    shared_target_or_objective TEXT NOT NULL,
    comparison_matrix TEXT NOT NULL, -- JSON formatted comparison table
    incompatibility_warnings TEXT, -- JSON array of condition mismatch warnings
    strategic_takeaway TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (technology_a_id) REFERENCES technologies(tech_id),
    FOREIGN KEY (technology_b_id) REFERENCES technologies(tech_id)
);

-- 12. Scientific Changes (Change Feed)
CREATE TABLE IF NOT EXISTS scientific_changes (
    change_id TEXT PRIMARY KEY,
    technology_id TEXT NOT NULL,
    change_type TEXT NOT NULL, -- 'replication', 'contradiction', 'new_evidence', 'scale_up', 'clinical_milestone', 'retraction'
    title TEXT NOT NULL,
    previous_state TEXT NOT NULL,
    new_state TEXT NOT NULL,
    primary_source_id TEXT NOT NULL,
    scientific_significance TEXT NOT NULL,
    commercial_implication TEXT NOT NULL,
    diligence_questions TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (technology_id) REFERENCES technologies(tech_id),
    FOREIGN KEY (primary_source_id) REFERENCES documents(document_id)
);

-- 13. Techno-Economic Scenarios
CREATE TABLE IF NOT EXISTS economic_scenarios (
    scenario_id TEXT PRIMARY KEY,
    technology_id TEXT NOT NULL,
    model_type TEXT NOT NULL, -- 'precision_fermentation', 'cell_gene_therapy', 'therapeutic_rd'
    inputs_json TEXT NOT NULL,
    outputs_json TEXT NOT NULL,
    unit_cost_usd_per_unit REAL NOT NULL,
    annual_capacity_kg REAL,
    break_even_price REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (technology_id) REFERENCES technologies(tech_id)
);

-- 14. Company & Commercial Relationships
CREATE TABLE IF NOT EXISTS company_relationships (
    rel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL,
    tech_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL, -- 'developer', 'licensee', 'spinout', 'collaborator'
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organizations(org_id),
    FOREIGN KEY (tech_id) REFERENCES technologies(tech_id)
);

-- 15. Research Reports (Memos, Tearsheets)
CREATE TABLE IF NOT EXISTS research_reports (
    report_id TEXT PRIMARY KEY,
    technology_id TEXT NOT NULL,
    report_type TEXT NOT NULL, -- 'diligence_memo', 'tearsheet', 'comparison_brief'
    title TEXT NOT NULL,
    content_markdown TEXT NOT NULL,
    version_tag TEXT NOT NULL,
    file_path TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (technology_id) REFERENCES technologies(tech_id)
);

-- 16. Pipeline Runs (Audit & Incremental Ingestion Telemetry)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    run_type TEXT NOT NULL, -- 'discovery', 'incremental', 'full_audit'
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL, -- 'running', 'success', 'failed'
    sources_checked INTEGER DEFAULT 0,
    documents_discovered INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    new_technologies INTEGER DEFAULT 0,
    new_experiments INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    rate_limit_events INTEGER DEFAULT 0,
    report_summary TEXT
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_docs_source ON documents(source_id);
CREATE INDEX IF NOT EXISTS idx_pubs_doi ON publications(doi);
CREATE INDEX IF NOT EXISTS idx_pubs_pmid ON publications(pmid);
CREATE INDEX IF NOT EXISTS idx_experiments_pub ON experiments(publication_id);
CREATE INDEX IF NOT EXISTS idx_exp_results_exp ON experimental_results(experiment_id);
CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence_links(claim_id);
CREATE INDEX IF NOT EXISTS idx_tech_domain ON technologies(domain, category);
CREATE INDEX IF NOT EXISTS idx_changes_tech ON scientific_changes(technology_id);
CREATE INDEX IF NOT EXISTS idx_evidence_rel_src ON evidence_relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_evidence_rel_tgt ON evidence_relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_evidence_rel_type ON evidence_relationships(relation_type);

