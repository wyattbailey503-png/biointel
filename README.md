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

- **Manage & Verify Reproducible Research Studies:**
  ```bash
  # List all available study packages:
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py study list

  # Deterministically verify and execute a study package:
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py study verify study_01_petase_plastics_bioprocess
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py study verify study_02_prime_vs_base_editing_diligence
  PYTHONPATH=src /Users/wyattbailey/.local/bin/python3.11 src/biointel/cli.py study verify study_03_lactoferrin_fermentation_scaleup
  ```

---

## Phase 4: Reproducible Research Study Packages

BioIntel enforces standard research study packages under `research/studies/<study-id>/`:

| Study ID | Domain | Diligence Question & Finding | Status |
| :--- | :--- | :--- | :--- |
| **`study_01_petase_plastics_bioprocess`** | Protein Engineering & Biomanufacturing | **FAST-PETase Plastic Recycling Parity:** Depolymerization on 34% crystalline bottle flake collapses from 52% to <5% without thermal amorphization; total cost ($1.60/kg TPA) is 52% higher than chemical glycolysis. **Verdict: REJECT PILOT FUNDING.** | `CALCULATION_CHECKED` |
| **`study_02_prime_vs_base_editing_diligence`** | Gene Editing & Delivery Vectors | **Prime Editing vs. Base Editing Triage:** PEmax exceeds single AAV limit by 2.3 kb; MMR excises 3'-flaps in primary cells, reducing efficiency by 65%. Base editing preferred for clean transitions; Prime editing reserved for LNP liver transversions. **Verdict: ALLOCATE BY ROUTE.** | `CALCULATION_CHECKED` |
| **`study_03_lactoferrin_fermentation_scaleup`** | Industrial Precision Fermentation | **Scale-Up Contradiction Audit:** 40 g/L pitch deck claim requires unphysical OUR (240 mmol/L/h) and generates 620 kW heat (exceeding 450 kW jacket limit). True commercial titer is bounded at 14 g/L, driving COGS to $92.50/kg (4.2x claimed). **Verdict: REJECT CLAIMED ECONOMICS.** | `CALCULATION_CHECKED` |

---

## Phase 4 Audit Deliverables (`docs/phase4/`)
1. [`implementation_reality_check.md`](docs/phase4/implementation_reality_check.md): Unvarnished line-by-line audit classifying all modules (Live vs. Seeded vs. Offline vs. Mocked).
2. [`scientific_quality_audit.md`](docs/phase4/scientific_quality_audit.md): Ten dimensions of research quality and hard review gate lifecycle (`DRAFT` $\to$ `READY_FOR_REVIEW` $\to$ `HUMAN_REVIEWED` / `REJECTED`).
3. [`research_benchmark.md`](docs/phase4/research_benchmark.md): Curated 20-observation ground-truth benchmark and adversarial failure modes.
4. [`product_wedge_assessment.md`](docs/phase4/product_wedge_assessment.md): Head-to-head comparison of Candidate A (Industrial Biotech) vs. Candidate B (Therapeutics) and concrete workflow selection.
5. [`baseline_comparison.md`](docs/phase4/baseline_comparison.md): Empirical scorecard comparing BioIntel against PubMed and general LLMs.
6. [`improvement_register.md`](docs/phase4/improvement_register.md): 15 candidate improvements and selection of 3 targeted fixes.
7. [`research_originality_assessment.md`](docs/phase4/research_originality_assessment.md): Epistemic ledger separating retrieved facts from newly derived calculations.
8. [`scientific_adversarial_review.md`](docs/phase4/scientific_adversarial_review.md): Multi-perspective reviews (Scientist, Investor, Software Maintainer) and external review package.
9. [`final_value_assessment.md`](docs/phase4/final_value_assessment.md): Prompt critique and definitive answers to all 11 closing questions.

