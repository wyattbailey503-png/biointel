# BioIntel: Autonomous Biotechnology Intelligence & Commercialization Research Engine

**BioIntel** is an independent, local-first biotechnology intelligence and commercialization research platform. It continuously discovers biological developments, grounds findings in experimental evidence, analyzes molecular mechanisms and 3D structures, compares competing technologies under condition-aware constraints, tracks scientific change, and evaluates techno-economic feasibility for deep-tech venture capital and pharma/biotech corporate development.

---

## Key Principles & Architectural Safeguards
1. **Evidence Traceability:** Every technological claim links directly to underlying experiments, recording model systems, replicates, endpoints, and statistical metrics.
2. **Fundamental Comparison Rule:** BioIntel strictly prohibits comparing performance figures measured under incompatible experimental conditions without explicit condition mismatch warnings (e.g., Cas9 indel knockout vs Prime Editing precise transversion).
3. **No Hallucinated Science:** LLM output is never treated as scientific evidence. Calculations (mass balance, unit cost stack, $C_\alpha$ distances) are 100% deterministic and independently auditable.
4. **Local-First & Zero Paid API Dependency:** Operates via SQLite and local Python 3.11 with cached fixtures and open scientific APIs (Europe PMC, RCSB PDB, UniProt).

---

## Directory Structure

```text
biointel/
├── README.md
├── pyproject.toml
├── .gitignore
├── config/
│   ├── sources.yaml            # Monitored API endpoints, rate limits, licensing
│   ├── taxonomy.yaml           # Biotechnology domain and category definitions
│   ├── queries.yaml            # Discovery query groups
│   └── com.biointel.daily.plist # Generated macOS launchd daemon configuration
├── src/biointel/
│   ├── cli.py                  # Unified CLI entry point
│   ├── storage/                # SQLite WAL storage layer & relational schema
│   ├── discovery/              # Source registry & continuous discovery crawler
│   ├── ingestion/              # Europe PMC, RCSB PDB, and UniProt adapters
│   ├── entities/               # Identifier normalization (DOI, PMID, PDB) & models
│   ├── evidence/               # Multi-dimensional quality scoring & contradiction detector
│   ├── mechanisms/             # Typed causal steps (binds, cleaves, edits) & flow renderer
│   ├── structures/             # PDB 3D parser, contact map & B-factor visualizer
│   ├── comparison/             # Condition-aware competitive technology matrix
│   ├── changes/                # Scientific change detection & Change Cards
│   ├── commercialization/      # 8-dimension feasibility framework
│   ├── economics/              # Precision fermentation mass-balance techno-economic model
│   ├── reports/                # Institutional diligence memos & JSON archive exporter
│   └── scheduler/              # Daily/weekly automated routines & launchd integration
├── data/
│   ├── records/                # Ingested raw payloads and document versions
│   ├── structures/             # Downloaded 3D coordinate files (.pdb / .cif)
│   ├── fixtures/               # Verified real-world scientific offline fixtures
│   └── exports/                # Versioned JSON deliverables
├── outputs/
│   ├── research/               # Generated diligence memos & weekly digests
│   └── figures/                # Generated publication-quality PNG and SVG figures
└── tests/
    ├── run_tests.py            # Standalone test runner (zero external test dependencies)
    ├── test_database.py        # Schema, foreign key, and versioning tests
    ├── test_structures.py      # PDB parser and contact matrix tests
    ├── test_economics.py       # Unit economics mass-balance & sensitivity tests
    ├── test_evidence.py        # Quality evaluator & contradiction detection tests
    ├── test_comparison.py      # Condition incompatibility warning tests
    └── test_cli.py             # CLI command verification tests
```

---

## Quickstart & Execution Steps

### 1. Execute Full End-to-End Vertical Slice
Runs all discovery, structure analysis, competitive comparisons, techno-economic models, diligence memos, and JSON exports:

```bash
cd /Users/wyattbailey/.gemini/antigravity/scratch/biointel
PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py run-all
```

### 2. Run Test Suite
Executes the comprehensive internal test harness:

```bash
PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 tests/run_tests.py
```

### 3. Individual CLI Subcommands

- **Discover New Research (Offline or Live):**
  ```bash
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py discover
  # To query live APIs with network permissions:
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py discover --live
  ```

- **Inspect Macromolecular Structure (PDB 7K38):**
  ```bash
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py structure 7K38
  ```

- **Generate Competitive Technology Matrix:**
  ```bash
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py compare crispr_cas9_nuclease prime_editing
  ```

- **Run Techno-Economic Biomanufacturing Model:**
  ```bash
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py teo-model --titer 45.0 --duration 120.0 --volume 50000.0 --sensitivity
  ```

- **View Scientific Change Feed:**
  ```bash
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py change-feed
  ```

- **Generate Institutional Diligence Memo:**
  ```bash
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py memo prime_editing
  ```

- **Export Versioned Research Archive:**
  ```bash
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py export --version v1.0.0
  ```

---

## Mandatory MVP Deliverables Generated
1. **Macromolecular 3D Structure:** PDB `7K38` (KAI2 alpha/beta hydrolase receptor, 2.0 Å resolution).
   - Generates per-residue crystallographic B-factor profile (`outputs/figures/7k38_b_factors.png`).
   - Generates $C_\alpha$ residue contact matrix (`outputs/figures/7k38_contacts.png`).
   - Staged for interactive Mol* 3D rendering via [Biomolecular Structure Viewer](sidecar://science/biomolecular_structure_viewer/ui.html).
2. **Competitive Technology Comparison:** SpCas9 Nuclease vs Prime Editing (PE2/PE3/bi-PE) with explicit experimental condition mismatch flags.
3. **Precision Fermentation Techno-Economic Model:** Biomanufacturing mass balance for 50,000 L reactor volume producing 111.4 MT/year at $24.64/kg with full cost stack decomposition and 2D sensitivity curve (`outputs/figures/fermentation_cost_sensitivity.png`).
4. **Institutional Diligence Memorandum:** 15-section structured diligence report in `outputs/research/memo_prime_editing.md`.
5. **Versioned JSON Archive:** Complete relational state snapshot ready for Git archiving in `data/exports/biointel_archive_v1.0.0.json`.
