# BioIntel Phase 4: Improvement Register & Targeted Refinement Plan

**Author:** Biotechnology Platform Architect & Lead Diligence Systems Engineer  
**Audit Target:** BioIntel Architecture & Algorithmic Capabilities  
**Audit Date:** November 2026  
**Document Classification:** Prioritized Engineering Improvement Register  

---

## 1. Comprehensive Register of Candidate Improvements (15 Candidates)

Each candidate improvement is grounded in demonstrated operational evidence, failures, or diligence friction observed during Phases 1–4.

| ID | User Diligence Problem | Demonstrated Failure / Friction | Proposed Solution | Expected Benefit | Complexity | Operating Burden | Required Data | Validation Method | Priority |
| :- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IMP-01** | Unverifiable claims pass through automated drafts without citation verification. | Automated extraction can attach a valid DOI without checking whether the referenced number appears in the paper. | Enforce `ClaimProvenance` requiring exact quotation excerpt and paragraph location; gate transitions through `SOURCE_CHECKED`. | Eliminates phantom citations and orphan numbers. | Low | Low | Primary text/PDF | Automated regex/offset search | **HIGH (Selected Fix 1)** |
| **IMP-02** | Misleading comparison of disparate experimental conditions (e.g. in vitro vs in vivo, or raw plastic vs amorphous film). | Naive comparators rank technologies based on raw percentage numbers without checking assay or substrate context. | Multi-factor boundary engine evaluating assay, temperature, substrate crystallinity, host cell, and replicate type. | Blocks false equivalences and misleading technology rankings. | Medium | Low | Assay metadata | Comparison unit tests with edge cases | **HIGH (Selected Fix 2)** |
| **IMP-03** | Research studies are difficult to independently audit and execute deterministically. | Studies exist as static markdown memos; third-party auditors cannot easily re-run underlying mass balances or verify inputs. | Implement standard reproducible research package CLI runner (`biointel study verify <id>` and `biointel study run <id>`). | Guarantees 100% mathematical auditability and deterministic execution. | Medium | Low | Package files | CLI execution test across all 3 study packages | **HIGH (Selected Fix 3)** |
| **IMP-04** | Large macromolecular complexes (>100k atoms) fail PDB parser. | Cryo-EM ribosome complexes exceed single PDB format atom limits (99,999 atoms). | Implement mmCIF/PDBx format parser alongside standard PDB parser. | Enables analysis of large asymmetric multi-protein assemblies. | High | Low | mmCIF files | Parser unit tests on large wwPDB entries | Medium |
| **IMP-05** | Lack of solvent-accessible surface area (SASA) computation. | Contact maps show distance contacts but cannot quantify catalytic active site pocket depth. | Implement Shrake-Rupley or Lee-Richards numerical SASA algorithm in pure Python. | Quantifies pocket burial and solvent exposure of engineered mutations. | Medium | Low | PDB coordinates | Comparison against DSSP/PyMOL benchmarks | Medium |
| **IMP-06** | Manual entry required for missing fermentation parameters. | Users must guess vessel cooling jacket surface area or overall heat transfer coefficient $U$. | Built-in physical vessel sizing heuristics based on standard industrial aspect ratios ($H/D = 3.0$). | Reduces user setup time and prevents unphysical geometry inputs. | Low | Low | Vessel volume | Heat balance unit tests | Medium |
| **IMP-07** | Inability to track patent expiration and freedom-to-operate (FTO). | Diligence memos note general IP risks but lack specific patent family filing and expiration dates. | Ingest public USPTO/EPO patent metadata via open APIs (e.g. Google Patents / Lens.org). | Identifies patent cliffs and licensing barriers for prime/base editing. | High | Medium | Patent XML/JSON | Patent metadata parsing tests | Medium |
| **IMP-08** | Lack of continuous fed-batch kinetic ODE solver. | Fermentation economics currently uses cycle-averaged yields rather than dynamic time-course ODE integration. | Implement Runge-Kutta 4th order (RK4) solver for Monod cell growth, substrate consumption, and product inhibition. | Models fed-batch feeding profiles and peak oxygen consumption dynamically. | Medium | Low | Kinetic parameters ($\mu_{max}, K_s, K_i$) | Comparison against SciPy ODE solutions | Low |
| **IMP-09** | Clinical trial phase progression tracking. | Clinical milestones must be manually cross-referenced against ClinicalTrials.gov. | Ingest ClinicalTrials.gov API v2 JSON records (NCT ID, enrollment, primary completion date). | Automatically alerts when a trial completes or posts results. | Medium | Low | ClinicalTrials.gov JSON | API schema parser tests | Medium |
| **IMP-10** | Heterologous protein glycosylation mismatch detection. | BioIntel does not flag hypermannosylation differences between *P. pastoris* and human milk proteins. | Sequence-based N-glycosylation motif scanner ($N-X-S/T$) with host-specific glycan rules. | Warns of immunogenicity and clearance issues for recombinant biologics. | Medium | Low | Amino acid sequences | Synthetic sequence unit tests | Low |
| **IMP-11** | Interactive 3D web structure rendering. | Users must click external Mol* links to explore 3D atomic coordinates. | Embed lightweight HTML5/WebGL 3Dmol.js viewer directly into generated local study reports. | Seamless 3D inspection within browser artifacts. | Medium | Low | PDB files | DevTools headless render check | Low |
| **IMP-12** | Automatic extraction of enzyme kinetic parameters from BRENDA. | $k_{cat}$ and $K_M$ values must be extracted manually from primary literature. | REST API connector to BRENDA / SABIO-RK enzyme kinetic databases. | Automatically retrieves substrate kinetic affinities. | High | Medium | BRENDA SOAP/REST | API response parsing tests | Low |
| **IMP-13** | Multiple sequence alignment (MSA) conservation scoring. | Parser analyzes single PDB files but does not compute evolutionary conservation across homologous enzymes. | Integrate lightweight Clustal-compatible profile alignment for catalytic pockets. | Identifies mutable vs immutable residues in protein engineering. | High | Medium | FASTA sequences | MSA test suite | Low |
| **IMP-14** | Automated PDF text extraction with character offset preservation. | System relies on Europe PMC XML; downloaded PDFs require OCR or manual transcription. | Local PDF text extraction pipeline using standard Python tools. | Extracted quotes retain exact page and bounding box offsets. | High | Medium | Open-access PDFs | PDF parser regression tests | Low |
| **IMP-15** | Cash-flow Net Present Value (NPV) & Internal Rate of Return (IRR) financial model. | Economic model calculates production cost per kg ($/kg) but not discounted project cash flows. | Add 10-year discounted cash flow (DCF) module with WACC and tax amortization. | Evaluates private equity / venture capital return hurdles. | Low | Low | Financial assumptions | Spreadsheet reconciliation tests | Low |

---

## 2. Selection of the Three Targeted Fixes

In strict accordance with the Phase 4 mandate (**"Select no more than three targeted fixes based on correcting demonstrated research errors, improving decision usefulness, and improving reproducibility"**), we selected:

1. **Targeted Fix 1 (IMP-01): Hard Quality Gate & Evidence Provenance Engine**
   - *Rationale:* Eliminates ungrounded numbers by enforcing `ClaimProvenance` (exact text excerpt, paragraph location, DOI verification) and rigid quality gate state transitions (`DRAFT` $\to$ `SOURCE_CHECKED` $\to$ `CALCULATION_CHECKED` $\to$ `READY_FOR_REVIEW`).
2. **Targeted Fix 2 (IMP-02): Multi-Factor Incomparability & Assay Boundary Engine**
   - *Rationale:* Directly prevents false equivalences across incompatible biological assays, temperatures, substrate crystallinities, and cell lines, elevating the rigor of technology benchmarking.
3. **Targeted Fix 3 (IMP-03): Reproducible Research Package CLI Runner**
   - *Rationale:* Transforms BioIntel studies from static markdown text into fully executable, auditable research instruments (`biointel study verify <id>` and `biointel study run <id>`) with automated checksum validation and figure generation.
