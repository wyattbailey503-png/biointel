# Study 03: Reconciling Contradictory Scale-Up Data for Recombinant Human Lactoferrin (rhLF) Biomanufacturing

## Executive Summary
This study investigates a material discrepancy in biomanufacturing evidence: a venture startup claims a $40.0\text{ g/L}$ commercial fermentation titer in $50,000\text{ L}$ industrial bioreactors for recombinant human lactoferrin (rhLF) expressed in *Pichia pastoris*, whereas academic literature and pilot-scale trials report titers of $1.8–4.8\text{ g/L}$ (Liu et al. 2020) and $12.0\text{ g/L}$ in highly optimized 1,000 L pilot runs.

### Core Findings
1. **Physical Oxygen Transfer ($k_L a$) Bottlenecks:** To support a cell density required for $40.0\text{ g/L}$ secreted protein in methanol-induced *P. pastoris*, the oxygen uptake rate exceeds $180\text{ mmol } \text{O}_2 / L / h$. In a $50,000\text{ L}$ commercial vessel, the achievable volumetric oxygen transfer coefficient ($k_L a$) rarely exceeds $120–140\text{ h}^{-1}$ without dangerous pure oxygen enrichment, leading to anoxic broth zones and product proteolysis.
2. **Cooling Duty Constraints:** Methanol metabolism by alcohol oxidase ($\text{AOX1}$) is intensely exothermic ($\Delta H \approx 727\text{ kJ/mol methanol}$). At $40\text{ g/L}$ target productivity, heat generation exceeds the cooling jacket capacity of standard industrial $50,000\text{ L}$ tanks, requiring external heat exchangers or broth dilution.
3. **Downstream Purification Recovery Decay:** Lactoferrin ($80\text{ kDa}$, pI $\approx 8.7$) binds non-specifically to acidic cell debris. At high cell densities ($> 120\text{ g/L}$ DCW), tangential flow microfiltration and cation exchange chromatography yields drop from $85\%$ to $< 60\%$.
4. **Verdict:** **CONTRADICTORY CLAIM REJECTED AS PHYSICALLY UNFEASIBLE**. The $40.0\text{ g/L}$ commercial claim violates industrial oxygen and heat-transfer limits. Realizable commercial titer is bounded between $12.0–16.0\text{ g/L}$, resulting in an actual production cost of $\$85–\$110/kg$, compared to the company's advertised $\$22/kg$.

---

## Directory Structure
- `question.md`: Formal diligence inquiry on scale-up contradictions.
- `methods.md`: Gas-liquid mass transfer ($k_L a$) and exothermic heat-duty models.
- `sources.json`: Primary academic papers and pilot run logs.
- `evidence.csv`: Reported titers across scales with oxygen transfer numbers.
- `assumptions.yaml`: Vessel geometry and transport parameters.
- `calculations.py`: Deterministic oxygen transfer, heat duty, and cost stack calculator.
- `figures/`: Vector plots of oxygen transfer limits and scale-up titer collapse.
- `results/`: Output JSON summary.
- `limitations.md`: Boundaries, assumptions, and audit criteria.
- `verification.json`: Checksums and review status.
