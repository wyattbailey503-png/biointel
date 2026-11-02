# BioIntel Baseline Audit: Longitudinal Scientific Intelligence & Evidence Evolution

**Audit Date:** November 2, 2026  
**Auditor:** BioIntel Scientific Intelligence Audit Engine  
**Workspace:** `/Users/wyattbailey/.gemini/antigravity/scratch/biointel`  
**Git Commit Baseline:** `e19c432` (*Remediate scientific identity (7SH6), dimensional utilities, and commercialization scoring*)

---

## 1. Executive Summary

This baseline establishes the actual operational state of BioIntel prior to implementing the longitudinal intelligence, evidence evolution, and commercialization inflection architecture. It distinguishes functional code from seeded benchmarks, identifies evidence extraction boundaries, catalogs missing longitudinal capabilities, and establishes an evidence-backed baseline for subsequent historical replay and evolution tracking.

---

## 2. Actual Functionality vs. Seeded Records

| Subsystem | Operational Implementation | Seeded vs. Live Status | Integrity Assessment |
| :--- | :--- | :--- | :--- |
| **Relational Storage (`biointel.db`)** | SQLite 3 with WAL mode, foreign keys, and indexes. 17 tables defined in `schema.sql`. | **Mixed:** 5 sources, 5 documents, 5 document versions, 3 technologies, 2 structures, 2 experiments, 2 results, 22 pipeline runs. | **Solid:** Schema enforces referential integrity; version table tracks SHA-256 hashes. |
| **Source Registry & Crawler** | `SourceRegistry` and `DiscoveryCrawler` supporting 'live' HTTP and 'offline' fixture modes with exponential backoff and rate-limit tracking. | **Live & Cached:** Live HTTP adapters exist for Europe PMC, RCSB PDB, UniProt, USPTO, and bioRxiv. Offline runs use validated JSON fixtures in `data/fixtures/`. | **Functional:** In offline mode, deduplication works cleanly without ghost record inflation. |
| **Entity Resolution & Structure Registry** | `EntityResolver` with authoritative registry for `7SH6` (FAST-PETase), `7K38` (KAI2), `4OO8` (Cas9), and `1CRN` (Crambin). | **Authoritative:** Hardcoded registry with runtime validation rejecting false alias claims. | **Remediated & Verified:** `7K38` misattribution is blocked and regression-tested. |
| **Evidence Quality & Contradiction** | `EvidenceQualityEvaluator` evaluating replicates, controls, and p-values; `ContradictionDetector` checking endpoint divergence; `MultiFactorAssayBoundary` checking assay resolution. | **Deterministic Engine:** Analyzes `ExperimentRecord` and `ResultRecord` dataclasses. | **Partially Flawed (Needs Revision):** Penalizes $p > 0.05$ as low quality, conflating study design quality with failure to reject the null hypothesis. |
| **Bioprocess Economics** | `TechnoEconomicFermentationModel` calculating mass balance, Thornton's rule metabolic heat, compressor power, and chiller work. | **First-Principles Engine:** Deterministic thermodynamic calculations. | **High Rigor:** Fully separated physical rates (kW, kWh) from dollar expenditures ($/kg, $/batch). |
| **Commercialization Scoring** | `CommercializationEvaluator` evaluating gross margin vs target selling price and parity ratio vs incumbent routes. | **Dynamic Engine:** Replaced static thresholds with product-specific margins. | **Sound:** Falls back to `Qualitative / Context-Dependent` when market prices are unknown. |
| **Reproducible Studies** | 3 research packages (`study_01`, `study_02`, `study_03`) in `research/studies/` with `calculations.py`, `sources.json`, and verification hashes. | **Curated Deep Dives:** Hand-curated primary sources and deterministic Python verification scripts. | **Verified:** All 3 pass `study verify` hash checks. |
| **Longitudinal Intelligence** | `scientific_changes` table exists with 1 seeded row (`change_prime_editing_bipe_2022`). | **Nascent / Unimplemented:** No automated timeline builder, no date-cutoff snapshot replay, no automated replication classification. | **Critical Gap:** Needs full evidence evolution engine. |

---

## 3. Detailed Data & Evidence Census

### 3.1 Relational Database Records (`biointel.db`)
- **Technologies (3):**
  1. `engineered_hydrolase_kai2`: *Pisum sativum* KAI2 receptor hydrolase (preclinical).
  2. `crispr_cas9_nuclease`: SpCas9 double-strand break nuclease (commercial).
  3. `prime_editing`: Search-and-replace gene editing fusing Cas9 nickase with M-MLV RT (clinical trial).
- **Structures (2):**
  - `7SH6`: FAST-PETase (1.44 Å, 261 residues, mature catalytic core).
  - `7K38`: Pea KAI2 receptor (2.0 Å, 270 residues, `VTY` ligand).
- **Documents & Publications (3 live / 2 fixtures):**
  - DOI `10.1093/nar/gkac506` (Bi-PE, 2022)
  - DOI `10.1097/hco.0000000000000985` (Prime editing CVD, 2022)
  - PMC `PMC13654590` (CRISPR cardiovascular review, 2026)
- **Scientific Changes (1):**
  - `change_prime_editing_bipe_2022`: Documents Bi-PE 2.5-fold efficiency improvement over PE3.

---

## 4. Current Limitations & Missing Capabilities

1. **Absence of Historical Cutoff Engine:**
   - The current crawler and diligence memo generators query all available records simultaneously.
   - There is no mechanism to enforce an `as_of_date` or publication-date cutoff, risking hindsight leakage in retrospective analyses.
2. **Conflation of Negative Results with Low Quality:**
   - `EvidenceQualityEvaluator` currently docks points if $p > 0.05$.
   - A well-powered negative study (e.g. proving an enzyme fails to degrade crystalline PET, or an editor fails in post-mitotic neurons) is high-rigor evidence that weakens a hypothesis, not "low-quality research."
3. **Missing Granular Evidence Graph Relationships:**
   - The current `evidence_links` table only supports `supports`, `contradicts`, and `inconclusive`.
   - Richer relationships (`REPLICATES`, `EXTENDS`, `REFINES`, `USES_METHOD`, `DEMONSTRATES_SCALE`, `REPORTS_SAFETY_CONCERN`, `ASSOCIATED_WITH_COMPANY`) are absent from the schema.
4. **Lack of Automated Replication Classification:**
   - BioIntel cannot currently differentiate direct independent replication, conceptual replication, cross-system extension, or repeated experiments from the same lab.
5. **No Commercialization Inflection Detector:**
   - The platform can calculate static unit costs, but cannot automatically evaluate whether a newly published experimental finding shifts an economic bottleneck or moves a technology across a readiness boundary.
6. **No Date Triad Tracking:**
   - Records lack explicit differentiation between:
     a) `experiment_date` (when the wet-lab experiment occurred)
     b) `publication_date` (when the paper was published or posted as a preprint)
     c) `discovery_date` (when BioIntel ingested it)

---

## 5. Technology Selection for Real Historical Validation

To satisfy the primary objective, we select **Engineered PET-Degrading Enzymes (PETase / FAST-PETase / Leaf-branch Compost Cutinase LCC)** as the primary technology platform for historical validation.

### Rationale:
1. **Clear, Accessible Primary Literature:**
   - **2016 (Baseline Discovery):** Yoshida et al. (*Science* 2016, DOI: `10.1126/science.aad6359`) discovers *Ideonella sakaiensis* 201-F6 and wild-type PETase (`PDB 5XJH`).
   - **2018 (Structure & Initial Engineering):** Austin et al. (*PNAS* 2018, DOI: `10.1073/pnas.1718804115`) determines crystal structure (`PDB 6EQE`) and engineers active site (W159H/S238F).
   - **2020 (Thermal Breakthrough & Pretreatment Realization):** Tournier et al. (*Nature* 2020, DOI: `10.1038/s41586-020-2149-4`) develops engineered LCC cutinase (`WCCG` mutant) operating at 72 °C, proving depolymerization requires operating near PET glass transition ($T_g$).
   - **2022 (Machine Learning Optimization):** Lu et al. (*Nature* 2022, DOI: `10.1038/s41586-022-04599-z`) uses structure-guided neural network (mutCompute) to generate FAST-PETase (`PDB 7SH6`) with high activity at 50 °C.
   - **2023–2024 (Industrial Diligence & Reality Boundaries):** Independent studies by commercial consortia (Carbios pilot data, NREL techno-economic evaluations) demonstrate the severe cost penalties of thermal amorphization, membrane fouling, and caustic/acid consumption.
2. **Direct Connection to Existing Bioprocess Economics:**
   - PET depolymerization directly exercises BioIntel's precision fermentation economic model (enzyme production cost) and Study 01's mass balance equations.
3. **Auditable Non-Inference:**
   - Each milestone is tethered to public peer-reviewed papers, official RCSB structures, and verified industrial pilot disclosures.

---

## 6. Architectural Plan for Phase Execution

1. **Schema Extension (Backward-Compatible):**
   - Add `evidence_relationships` table supporting `SUPPORTS`, `CONTRADICTS`, `REPLICATES`, `EXTENDS`, `REFINES`, `USES_METHOD`, `DEMONSTRATES_SCALE`, `REPORTS_SAFETY_CONCERN`, `ASSOCIATED_WITH_COMPANY`.
   - Add explicit date triad (`experiment_date`, `publication_date`, `discovery_date`) to evidence records.
2. **Quality Evaluator Overhaul:**
   - Decouple study methodological rigor (replicates, controls, assay resolution) from statistical hypothesis confirmation (effect size, p-value direction).
3. **Longitudinal Replay & Snapshot Engine:**
   - Build historical replay engine supporting `as_of_date` query cutoffs (Snapshots 2016, 2018, 2020, 2022, 2024).
4. **Inflection & Economic Change Propagation:**
   - Connect validated experimental parameter shifts (e.g. thermostability $T_m$, specific activity U/mg, required amorphization energy) to conditional sensitivity scenarios in the bioprocess engine.
5. **Adversarial Validation Suite:**
   - Permanent tests covering the 8 required adversarial scenarios.
