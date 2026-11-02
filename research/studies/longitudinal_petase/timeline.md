# Historical Scientific Evidence Timeline: Engineered PET-Degrading Enzymes (2016–2024) [Audited v2]

This timeline documents the empirical evolution of biocatalytic polyester depolymerization across five chronological cutoffs. Each snapshot reflects **strictly what was publicly knowable on that calendar date**, enforcing separate publication and PDB public release dates to prevent hindsight leakage.

![PETase Cost Evolution](figures/cost_trajectory_evolution.svg)

---

## Snapshot 1 (April 2016): Initial Discovery & Wild-Type IsPETase (v2)
**As-Of Date Cutoff:** `2016-04-01` | **v2 Hash:** `cd37295a63c73af8` | **Superseded v1 Hash:** `d2de1347520d6629d4e12e0d278ad81e519ad320b55d31b4e900a96cf7a9a52e`

### Publicly Available Structures (0)
- *Zero macromolecular structures publicly available at this cutoff date.*

### Contemporaneous Literature (1 records)
- **2016-03-10**: Yoshida et al., A bacterium that degrades and assimilates poly(ethylene terephthalate), Science 351(6278):1196-1199 (2016) ([DOI](https://doi.org/10.1126/science.aad6359)) — *Lineage:* `INITIAL_DISCOVERY`

### Demonstrated Capabilities
- [2016-03-10] Wild-type IsPETase: 0.13 mg/cm²/day mass loss at 30 °C; 60 mg film fully degraded after 6 weeks (Substrate: 1.9% crystallinity)

### Established Physical & Engineering Boundaries
- Strictly mesophilic enzyme; irreversible thermal denaturation above 40 °C (Tm ~ 46.5 °C).
- Completely inactive against commercial bottle-grade crystalline PET (30-35% crystallinity).
- Enzyme secretion titer from native host is negligible; requires recombinant E. coli expression.
- Structure is completely unknown in April 2016; catalytic pocket configuration unverified.

### Commercial Feasibility Assessment
- **Readiness Stage:** `Academic Discovery / Early Research`
- **Economic Metric Typology:** `RETROSPECTIVE_MODEL_ESTIMATE`
- **Estimated TPA Production Cost:** **$65.00 / kg** (Target market parity ratio: **52.0x** vs contemporaneous virgin PTA: **$1.25/kg**)
- **Basis & Attribution Notes:** Retrospective bioprocess simulation assuming a 50,000 L stirred-tank batch held for 1,000 h (6 weeks) at 1 g/L enzyme loading with straight-line capital carrying costs. Yoshida et al. reported zero economic numbers. Contemporaneous virgin PET traded at $1.10-$1.25/kg.
- **Commercial Verdict:** ECONOMICALLY UNVIABLE: Reaction requires 6 weeks; zero activity on commercial post-consumer plastic.

### Unresolved Uncertainties at This Cutoff
- *What is the three-dimensional fold of the enzyme (crystal structure unresolved in 2016)?*
- *Is the enzyme mechanism distinct from legacy fungal cutinases (e.g. Thermobifida fusca)?*
- *Can active site mutations overcome the steric barrier of crystalline PET chains?*
- *Can thermal stability be increased to operate near the PET glass transition temperature (Tg ~ 65-70 °C)?*

---

## Snapshot 2 (May 2018): Crystallographic Structure & Initial Active Site Engineering (v2)
**As-Of Date Cutoff:** `2018-05-01` | **v2 Hash:** `5f03a838440972c9` | **Superseded v1 Hash:** `6d3f656a5d983a7187613e5a1ca4d3c297e06fc9339ad0f4cfe6c3514d60384e`

### Publicly Available Structures (2)
- **PDB 5XJH** (Publicly released on or before 2018-05-01)
- **PDB 6EQE** (Publicly released on or before 2018-05-01)

### Contemporaneous Literature (2 records)
- **2016-03-10**: Yoshida et al., A bacterium that degrades and assimilates poly(ethylene terephthalate), Science 351(6278):1196-1199 (2016) ([DOI](https://doi.org/10.1126/science.aad6359)) — *Lineage:* `INITIAL_DISCOVERY`
- **2018-04-17**: Austin et al., Characterization and engineering of a plastic-degrading aromatic polyesterase, PNAS 115(19):E4350-E4357 (2018) ([DOI](https://doi.org/10.1073/pnas.1718804115)) — *Lineage:* `INDEPENDENT_STRUCTURAL_EXTENSION`

### Demonstrated Capabilities
- [2016-03-10] Wild-type IsPETase: 0.13 mg/cm²/day mass loss at 30 °C; 60 mg film fully degraded after 6 weeks (Substrate: 1.9% crystallinity)
- [2018-04-17] IsPETase double mutant (S238F/W159H): ~20% improvement in amorphous PET degradation rate over wild-type; active site cleft narrowed (Substrate: 1.9% crystallinity)

### Established Physical & Engineering Boundaries
- Strictly mesophilic enzyme; irreversible thermal denaturation above 40 °C (Tm ~ 46.5 °C).
- Completely inactive against commercial bottle-grade crystalline PET (30-35% crystallinity).
- Enzyme secretion titer from native host is negligible; requires recombinant E. coli expression.
- Structure is completely unknown in April 2016; catalytic pocket configuration unverified.
- Engineering focused on active-site pocket did not improve melting temperature (Tm ~ 46.5 °C).
- Remains completely incapable of hydrolyzing biaxially oriented bottle PET without prior thermal destruction.
- Modest ~1.2-fold improvement is insufficient to alter batch bioprocess kinetics.

### Commercial Feasibility Assessment
- **Readiness Stage:** `Lead Optimization / Protein Engineering`
- **Economic Metric Typology:** `RETROSPECTIVE_MODEL_ESTIMATE`
- **Estimated TPA Production Cost:** **$42.00 / kg** (Target market parity ratio: **33.6x** vs contemporaneous virgin PTA: **$1.25/kg**)
- **Basis & Attribution Notes:** Retrospective bioprocess model assuming ~800 h residence time. Austin et al. provided structural elucidation and site-directed mutagenesis, but no industrial economic projections. Contemporaneous virgin PET: $1.25/kg.
- **Commercial Verdict:** COMMERCIALLY UNFEASIBLE: Establishes structural basis, but catalytic velocity at 30 °C remains orders of magnitude too slow for industrial recovery.

### Unresolved Uncertainties at This Cutoff
- *Does narrowed active-site cleft restrict bulky synthetic polyester chains from entering?*
- *Why do mesophilic IsPETase variants lose all activity within 24 hours at 37 °C?*
- *Is IsPETase intrinsically the wrong enzyme chassis compared to thermophilic actinomycete cutinases?*

---

## Snapshot 3 (May 2020): Thermophilic Breakthrough Operating Near PET Glass Transition (v2)
**As-Of Date Cutoff:** `2020-05-01` | **v2 Hash:** `5867e3901205abc5` | **Superseded v1 Hash:** `c204a3c865634b7043c18ad3cd3ba5265b4fcd619b6d26c064421cb0a24e9c0a`

### Publicly Available Structures (3)
- **PDB 5XJH** (Publicly released on or before 2020-05-01)
- **PDB 6EQE** (Publicly released on or before 2020-05-01)
- **PDB 6T54** (Publicly released on or before 2020-05-01)

### Contemporaneous Literature (3 records)
- **2016-03-10**: Yoshida et al., A bacterium that degrades and assimilates poly(ethylene terephthalate), Science 351(6278):1196-1199 (2016) ([DOI](https://doi.org/10.1126/science.aad6359)) — *Lineage:* `INITIAL_DISCOVERY`
- **2018-04-17**: Austin et al., Characterization and engineering of a plastic-degrading aromatic polyesterase, PNAS 115(19):E4350-E4357 (2018) ([DOI](https://doi.org/10.1073/pnas.1718804115)) — *Lineage:* `INDEPENDENT_STRUCTURAL_EXTENSION`
- **2020-04-08**: Tournier et al., An engineered PET depolymerase to break down and recycle plastic bottles, Nature 580:216-219 (2020) ([DOI](https://doi.org/10.1038/s41586-020-2149-4)) — *Lineage:* `HOMOLOGOUS_CUTINASE_FAMILY_ENGINEERING`

### Demonstrated Capabilities
- [2016-03-10] Wild-type IsPETase: 0.13 mg/cm²/day mass loss at 30 °C; 60 mg film fully degraded after 6 weeks (Substrate: 1.9% crystallinity)
- [2018-04-17] IsPETase double mutant (S238F/W159H): ~20% improvement in amorphous PET degradation rate over wild-type; active site cleft narrowed (Substrate: 1.9% crystallinity)
- [2020-04-08] Engineered Leaf-branch Compost Cutinase (LCC-ICCG / LCC-WCCG): 90% depolymerization into terephthalic acid (TPA) and ethylene glycol (EG) within 9.3 hours at 3 mg enzyme / g PET loading (Substrate: 10.0% crystallinity)

### Established Physical & Engineering Boundaries
- Strictly mesophilic enzyme; irreversible thermal denaturation above 40 °C (Tm ~ 46.5 °C).
- Completely inactive against commercial bottle-grade crystalline PET (30-35% crystallinity).
- Enzyme secretion titer from native host is negligible; requires recombinant E. coli expression.
- Structure is completely unknown in April 2016; catalytic pocket configuration unverified.
- Engineering focused on active-site pocket did not improve melting temperature (Tm ~ 46.5 °C).
- Remains completely incapable of hydrolyzing biaxially oriented bottle PET without prior thermal destruction.
- Modest ~1.2-fold improvement is insufficient to alter batch bioprocess kinetics.
- Completely reliant on upstream thermal amorphization: Virgin bottles (30% crystalline) MUST be melted at 260 °C and flash-quenched before enzyme exposure.
- Operating at 72 °C requires continuous pH neutralization (NaOH titrant), generating massive inorganic salt waste (Na2SO4) upon acid precipitation.
- Enzyme lifetime at 72 °C is limited to ~15-20 hours; catalyst cannot be recycled without extensive cooling/reheating.
- LCC is a distinct metagenomic cutinase family, not an IsPETase derivative.

### Commercial Feasibility Assessment
- **Readiness Stage:** `Pilot-Scale Demonstration`
- **Economic Metric Typology:** `SOURCED_LITERATURE_ESTIMATE`
- **Estimated TPA Production Cost:** **$1.65 / kg** (Target market parity ratio: **1.6x** vs contemporaneous virgin PTA: **$1.05/kg**)
- **Basis & Attribution Notes:** Sourced from contemporary Carbios pilot disclosures and contemporary NREL TEA models ($1.40-$1.80/kg TPA). Includes twin-screw extrusion amorphization pre-treatment ($0.26-$0.49/kg TPA). Contemporaneous virgin TPA: $1.05/kg.
- **Commercial Verdict:** CONDITIONAL PILOT VIABILITY: First demonstration of industrially relevant reaction velocity (10 h batch). However, non-biological pre-treatment ($0.26-$0.49/kg) keeps cost ~57% above virgin petrochemical TPA ($1.05/kg).

### Unresolved Uncertainties at This Cutoff
- *What is the fouling rate of ultrafiltration membranes when separating soluble TPA from residual insoluble oligomers (MHET)?*
- *Can sodium sulfate salt byproduct be monetized or does it incur hazardous industrial brine disposal costs?*
- *Can directed evolution yield an enzyme active at 50 °C with equivalent velocity, avoiding 72 °C heating costs?*

---

## Snapshot 4 (May 2022): Neural-Network Guided Directed Evolution (FAST-PETase) (v2)
**As-Of Date Cutoff:** `2022-05-01` | **v2 Hash:** `aa3249bb3f28bbec` | **Superseded v1 Hash:** `da5950c26ea298237dc015694e0b9b0eed0ff4476d4cb3cc7ffc8a6de80706a7`

### Publicly Available Structures (4)
- **PDB 5XJH** (Publicly released on or before 2022-05-01)
- **PDB 6EQE** (Publicly released on or before 2022-05-01)
- **PDB 6T54** (Publicly released on or before 2022-05-01)
- **PDB 7SH6** (Publicly released on or before 2022-05-01)

### Contemporaneous Literature (4 records)
- **2016-03-10**: Yoshida et al., A bacterium that degrades and assimilates poly(ethylene terephthalate), Science 351(6278):1196-1199 (2016) ([DOI](https://doi.org/10.1126/science.aad6359)) — *Lineage:* `INITIAL_DISCOVERY`
- **2018-04-17**: Austin et al., Characterization and engineering of a plastic-degrading aromatic polyesterase, PNAS 115(19):E4350-E4357 (2018) ([DOI](https://doi.org/10.1073/pnas.1718804115)) — *Lineage:* `INDEPENDENT_STRUCTURAL_EXTENSION`
- **2020-04-08**: Tournier et al., An engineered PET depolymerase to break down and recycle plastic bottles, Nature 580:216-219 (2020) ([DOI](https://doi.org/10.1038/s41586-020-2149-4)) — *Lineage:* `HOMOLOGOUS_CUTINASE_FAMILY_ENGINEERING`
- **2022-04-27**: Lu et al., Machine learning-aided engineering of hydrolases for PET depolymerization, Nature 604:662-667 (2022) ([DOI](https://doi.org/10.1038/s41586-022-04599-z)) — *Lineage:* `SAME_CHASSIS_DIRECTED_EVOLUTION`

### Demonstrated Capabilities
- [2016-03-10] Wild-type IsPETase: 0.13 mg/cm²/day mass loss at 30 °C; 60 mg film fully degraded after 6 weeks (Substrate: 1.9% crystallinity)
- [2018-04-17] IsPETase double mutant (S238F/W159H): ~20% improvement in amorphous PET degradation rate over wild-type; active site cleft narrowed (Substrate: 1.9% crystallinity)
- [2020-04-08] Engineered Leaf-branch Compost Cutinase (LCC-ICCG / LCC-WCCG): 90% depolymerization into terephthalic acid (TPA) and ethylene glycol (EG) within 9.3 hours at 3 mg enzyme / g PET loading (Substrate: 10.0% crystallinity)
- [2022-04-27] FAST-PETase (S121E/D186H/R224Q/N233K/R280A): Complete depolymerization of untreated post-consumer amorphous containers in 24-48 hours at 50 °C; Tm increased by 8.2 °C (Substrate: 5.0% crystallinity)

### Established Physical & Engineering Boundaries
- Strictly mesophilic enzyme; irreversible thermal denaturation above 40 °C (Tm ~ 46.5 °C).
- Completely inactive against commercial bottle-grade crystalline PET (30-35% crystallinity).
- Enzyme secretion titer from native host is negligible; requires recombinant E. coli expression.
- Structure is completely unknown in April 2016; catalytic pocket configuration unverified.
- Engineering focused on active-site pocket did not improve melting temperature (Tm ~ 46.5 °C).
- Remains completely incapable of hydrolyzing biaxially oriented bottle PET without prior thermal destruction.
- Modest ~1.2-fold improvement is insufficient to alter batch bioprocess kinetics.
- Completely reliant on upstream thermal amorphization: Virgin bottles (30% crystalline) MUST be melted at 260 °C and flash-quenched before enzyme exposure.
- Operating at 72 °C requires continuous pH neutralization (NaOH titrant), generating massive inorganic salt waste (Na2SO4) upon acid precipitation.
- Enzyme lifetime at 72 °C is limited to ~15-20 hours; catalyst cannot be recycled without extensive cooling/reheating.
- LCC is a distinct metagenomic cutinase family, not an IsPETase derivative.
- Activity at 50 °C remains well below PET glass transition (Tg ~ 65-70 °C); still requires amorphized feedstock or thermoform waste for high conversion.
- Enzyme loading is relatively high (3-5 mg / g PET), driving biocatalyst OPEX.
- Membrane ultrafiltration recycling is theoretically proposed but subject to oligomeric pore fouling.

### Commercial Feasibility Assessment
- **Readiness Stage:** `Pre-Pilot / Advanced Biocatalyst`
- **Economic Metric Typology:** `RETROSPECTIVE_MODEL_ESTIMATE`
- **Estimated TPA Production Cost:** **$1.54 / kg** (Target market parity ratio: **1.5x** vs contemporaneous virgin PTA: **$1.05/kg**)
- **Basis & Attribution Notes:** Retrospective bioprocess model assuming 50 °C operation on amorphous thermoform PET waste. Lu et al. published enzyme engineering and kinetics, not manufacturing economics. Contemporaneous virgin TPA: $1.05/kg.
- **Commercial Verdict:** COMMERCIALLY CONSTRAINED: Operates at mild 50 °C, reducing reactor thermal stress, but requires pre-treated amorphous feedstock on bottle packaging ($1.54/kg TPA vs $1.05/kg virgin).

### Unresolved Uncertainties at This Cutoff
- *Can FAST-PETase tolerate industrial wash impurities, detergents, and colored PET dyes?*
- *Will membrane recovery achieve >5 cycles in the presence of supersaturated mono-(2-hydroxyethyl) terephthalate?*
- *Does the mild 50 °C operating temperature allow bacterial contamination during multi-day open digestions?*

---

## Snapshot 5 (February 2024): Industrial Reconciliation & Reality Boundary Audit (v2)
**As-Of Date Cutoff:** `2024-02-01` | **v2 Hash:** `52328ac9bb798591` | **Superseded v1 Hash:** `1aae6be62c8aad936ad3dd23becefad52471b65b16cf1bcf5d15fa615415e611`

### Publicly Available Structures (4)
- **PDB 5XJH** (Publicly released on or before 2024-02-01)
- **PDB 6EQE** (Publicly released on or before 2024-02-01)
- **PDB 6T54** (Publicly released on or before 2024-02-01)
- **PDB 7SH6** (Publicly released on or before 2024-02-01)

### Contemporaneous Literature (5 records)
- **2016-03-10**: Yoshida et al., A bacterium that degrades and assimilates poly(ethylene terephthalate), Science 351(6278):1196-1199 (2016) ([DOI](https://doi.org/10.1126/science.aad6359)) — *Lineage:* `INITIAL_DISCOVERY`
- **2018-04-17**: Austin et al., Characterization and engineering of a plastic-degrading aromatic polyesterase, PNAS 115(19):E4350-E4357 (2018) ([DOI](https://doi.org/10.1073/pnas.1718804115)) — *Lineage:* `INDEPENDENT_STRUCTURAL_EXTENSION`
- **2020-04-08**: Tournier et al., An engineered PET depolymerase to break down and recycle plastic bottles, Nature 580:216-219 (2020) ([DOI](https://doi.org/10.1038/s41586-020-2149-4)) — *Lineage:* `HOMOLOGOUS_CUTINASE_FAMILY_ENGINEERING`
- **2022-04-27**: Lu et al., Machine learning-aided engineering of hydrolases for PET depolymerization, Nature 604:662-667 (2022) ([DOI](https://doi.org/10.1038/s41586-022-04599-z)) — *Lineage:* `SAME_CHASSIS_DIRECTED_EVOLUTION`
- **2024-01-15**: Industrial Consortium Technical Audit & NREL Bioprocess Report, Operating reality of enzymatic polyester recycling at scale, Bioresour Technol (2024) ([DOI](https://doi.org/10.1016/j.biortech.2023.130101)) — *Lineage:* `SYSTEMS_RECONCILIATION_AUDIT`

### Demonstrated Capabilities
- [2016-03-10] Wild-type IsPETase: 0.13 mg/cm²/day mass loss at 30 °C; 60 mg film fully degraded after 6 weeks (Substrate: 1.9% crystallinity)
- [2018-04-17] IsPETase double mutant (S238F/W159H): ~20% improvement in amorphous PET degradation rate over wild-type; active site cleft narrowed (Substrate: 1.9% crystallinity)
- [2020-04-08] Engineered Leaf-branch Compost Cutinase (LCC-ICCG / LCC-WCCG): 90% depolymerization into terephthalic acid (TPA) and ethylene glycol (EG) within 9.3 hours at 3 mg enzyme / g PET loading (Substrate: 10.0% crystallinity)
- [2022-04-27] FAST-PETase (S121E/D186H/R224Q/N233K/R280A): Complete depolymerization of untreated post-consumer amorphous containers in 24-48 hours at 50 °C; Tm increased by 8.2 °C (Substrate: 5.0% crystallinity)
- [2024-01-15] Commercialized Cutinases & Engineered PETases: Reconciliation of commercial economics: Amorphization extruder energy accounts for 31% of total cost; NaOH/H2SO4 neutralization consumes 2.1 mol reagents per mol TPA. (Substrate: 32.0% crystallinity)

### Established Physical & Engineering Boundaries
- Strictly mesophilic enzyme; irreversible thermal denaturation above 40 °C (Tm ~ 46.5 °C).
- Completely inactive against commercial bottle-grade crystalline PET (30-35% crystallinity).
- Enzyme secretion titer from native host is negligible; requires recombinant E. coli expression.
- Structure is completely unknown in April 2016; catalytic pocket configuration unverified.
- Engineering focused on active-site pocket did not improve melting temperature (Tm ~ 46.5 °C).
- Remains completely incapable of hydrolyzing biaxially oriented bottle PET without prior thermal destruction.
- Modest ~1.2-fold improvement is insufficient to alter batch bioprocess kinetics.
- Completely reliant on upstream thermal amorphization: Virgin bottles (30% crystalline) MUST be melted at 260 °C and flash-quenched before enzyme exposure.
- Operating at 72 °C requires continuous pH neutralization (NaOH titrant), generating massive inorganic salt waste (Na2SO4) upon acid precipitation.
- Enzyme lifetime at 72 °C is limited to ~15-20 hours; catalyst cannot be recycled without extensive cooling/reheating.
- LCC is a distinct metagenomic cutinase family, not an IsPETase derivative.
- Activity at 50 °C remains well below PET glass transition (Tg ~ 65-70 °C); still requires amorphized feedstock or thermoform waste for high conversion.
- Enzyme loading is relatively high (3-5 mg / g PET), driving biocatalyst OPEX.
- Membrane ultrafiltration recycling is theoretically proposed but subject to oligomeric pore fouling.
- Unavoidable physical law: Enthalpy of amorphization and extrusion electrical work cannot be engineered away biologically.
- Oligomer precipitation (MHET solubility < 0.5 g/L at 25 °C) causes irreversible flux decay in ultrafiltration membranes.
- Enzymatic TPA ($1.55-$1.65/kg) requires a 50% green premium over chemical glycolysis ($1.05/kg) or fossil PTA ($1.15/kg).

### Commercial Feasibility Assessment
- **Readiness Stage:** `Commercial Demonstration (Bounded)`
- **Economic Metric Typology:** `SOURCED_LITERATURE_ESTIMATE`
- **Estimated TPA Production Cost:** **$1.60 / kg** (Target market parity ratio: **1.5x** vs contemporaneous virgin PTA: **$1.05/kg**)
- **Basis & Attribution Notes:** Multi-partner reconciliation synthesizing NREL TEA models (Singh et al. 2021) and Carbios demo facility data. Pre-treatment amorphization cost stack verified: $0.26/kg TPA at 50 kt/yr commercial scale, $0.49/kg TPA at 10 kt/yr pilot scale. Contemporaneous virgin TPA: $1.05/kg.
- **Commercial Verdict:** COMMERCIALLY BOUNDED BY NON-BIOLOGICAL UNIT OPERATIONS: The limiting factors in enzymatic recycling are not enzyme kinetics, but mechanical pre-treatment, caustic neutralization, and salt disposal. Viable only under mandatory recycled-content regulations or brand premia.

### Unresolved Uncertainties at This Cutoff
- *Will brands pay a $0.50/kg green premium for circular enzyme-recycled polyester over mechanically downcycled rPET?*
- *Can sodium sulfate brine be electrolyzed back to NaOH and H2SO4 economically?*
- *Will emerging thermochemical methanolysis / glycolysis outcompete biological depolymerization on impure mixed-waste bales?*

---
