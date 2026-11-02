# Study 02: Platform Diligence & Trade-Off Analysis: Prime Editing vs. Base Editing

## Executive Summary
This study evaluates the biophysical, translational, and clinical delivery trade-offs between **Prime Editing (PEmax)** and **Base Editing (CBE / ABE8e)** to inform a therapeutic platform in-licensing decision for monogenic CNS and hepatic indications.

### Core Findings
1. **Editing Versatility vs. Delivery Payload:** Prime Editing can install all 12 transition and transversion point mutations, micro-insertions up to $100\text{ bp}$, and targeted deletions without double-strand breaks. However, the PEmax ribonucleoprotein complex ($> 6.3\text{ kb}$ coding sequence) strictly exceeds the packaging ceiling of a single adeno-associated virus (AAV, $< 4.7\text{ kb}$), necessitating dual-AAV intein trans-splicing or mRNA lipid nanoparticle (LNP) delivery.
2. **Mismatch Repair (MMR) Antagonism:** In mismatch repair-proficient primary cells, human MMR complexes (MutS$\alpha$, MutL$\alpha$) recognize the reverse-transcribed 3'-flap and preferentially excise the edited strand, suppressing prime editing efficiency by $3–8$-fold unless transiently inhibited via dominant-negative MLH1 (MLH1dn). Base editors do not trigger 3'-flap MMR excision.
3. **Purity & Bystander Penalties:** Base editing achieves higher raw on-target conversion ($50\%–75\%$) but creates uncontrolled bystander deaminations if multiple target bases fall within the $4–8\text{ nt}$ activity window, alongside transcriptome-wide off-target RNA deamination. Prime editing exhibits near-zero bystander editing ($< 0.5\%$).
4. **Verdict:** **ALLOCATE BY INDICATION**. Base editing is superior for ex vivo liver and hematology transitions where no bystander cytosines/adenines exist. Prime editing is mandatory for transversions and insertions, but restricted to LNP-accessible tissues (liver, spleen) until split-AAV in vivo transduction efficiencies improve.

---

## Directory Structure
- `question.md`: Diligence decision and target product profiles (TPP).
- `methods.md`: Biophysical comparison metrics and delivery packaging models.
- `sources.json`: Primary peer-reviewed citations (Anzalone 2019, Chen 2021, Komor 2016, Gaudelli 2017).
- `evidence.csv`: Experimental observations with error margins and cell line tags.
- `assumptions.yaml`: Model parameters classified by evidence grade.
- `calculations.py`: Deterministic trade-off and packaging calculator.
- `figures/`: Vector comparison charts and packaging limits.
- `results/`: Output JSON summaries.
- `limitations.md`: Biological boundaries and falsification criteria.
- `verification.json`: Software checksums and gate review.
