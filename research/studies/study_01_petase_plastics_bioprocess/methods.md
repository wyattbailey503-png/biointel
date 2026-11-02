# Biophysical & Chemical Engineering Methodology

## 1. Stoichiometry & Depolymerization Mass Balance
Polyethylene terephthalate (PET) has a repeating monomeric unit formula of $\text{C}_{10}\text{H}_8\text{O}_4$ with a repeating molecular mass of $M_{PET} = 192.17\text{ g/mol}$.
Enzymatic hydrolysis requires 2 water molecules per repeating unit to yield 1 mole of terephthalic acid (TPA, $\text{C}_8\text{H}_6\text{O}_4$, $166.13\text{ g/mol}$) and 1 mole of ethylene glycol (EG, $\text{C}_2\text{H}_6\text{O}_2$, $62.07\text{ g/mol}$):

$$\text{PET} + 2\text{ H}_2\text{O} \longrightarrow \text{TPA} + \text{EG}$$

- Theoretical mass yield of TPA from PET:
  $$Y_{TPA/PET}^{theo} = \frac{166.13}{192.17} = 0.8645\text{ kg TPA / kg PET}$$
- Theoretical mass yield of EG from PET:
  $$Y_{EG/PET}^{theo} = \frac{62.07}{192.17} = 0.3230\text{ kg EG / kg PET}$$

## 2. Substrate Crystallinity Kinetics
Polymer degradation rate $r_{deg}$ ($g\text{ TPA}/L/h$) is modeled as a function of the amorphous polymer fraction $f_{amorphous} = 1 - X_c$ (where $X_c$ is fractional crystallinity, $0.0 \le X_c \le 0.45$) and operational temperature $T$:

$$r_{deg}(T, X_c) = k_0 \cdot \exp\left(-\frac{E_a}{R T}\right) \cdot (1 - X_c)^\beta \cdot \frac{[E]}{K_M + [S]}$$

Where:
- $X_c$ for amorphous film: $0.03–0.05$ ($3–5\%$).
- $X_c$ for post-consumer bottle flake: $0.32–0.38$ ($32–38\%$).
- $\beta \approx 3.2$ reflects the severe suppression of ester bond accessibility in ordered crystalline lamellae below the glass transition temperature ($T_g \approx 65–70\text{ °C}$).

## 3. Techno-Economic Cost Stack Decomposition
Total cost per kg of recovered TPA ($C_{TPA}$) is calculated as:

$$C_{TPA} = C_{feedstock} + C_{pretreat} + C_{enzyme} + C_{utilities} + C_{DSP} + C_{labor\_overhead} + C_{CAPEX}$$

Where:
- $C_{feedstock} = \frac{P_{PET}}{Y_{TPA/PET}^{theo} \cdot \eta_{conv} \cdot \eta_{rec}}$
- $C_{enzyme} = \frac{L_{enz} \cdot P_{enz}}{\eta_{rec}}$ ($L_{enz}$ = enzyme loading, $g\text{ enzyme}/g\text{ PET}$; $P_{enz}$ = enzyme production cost, $\$/kg$)
- $C_{pretreat}$ = Amorphization extrusion and micronization cost ($\$0.35/kg$ PET).

## 4. Authoritative Macromolecular Structure Identification
The authoritative crystal structure for the engineered FAST-PETase variant (N233K/R224Q/S121E/D186H/R280A) is:
- **PDB ID:** `7SH6` (Lu et al. *Nature* 604, 662–667, 2022)
- **Title:** Crystal structure of a PET hydrolase mutant from *Ideonella sakaiensis*
- **Resolution:** 1.44 Å (X-ray diffraction)
- **Wild-Type Reference:** PDB `5XG0` / `6EQU`
- *Disambiguation Note:* Earlier drafts conflated PDB `7K38` with FAST-PETase; PDB `7K38` is the plant Karrikin receptor KAI2 from *Pisum sativum* (Guercio et al. *Commun Biol* 2022) and must not be used for PETase analyses.

## 5. Separation of Demonstrated Outcomes vs. Theoretical Projections
- **Experimentally Demonstrated in Literature:**
  - FAST-PETase achieves $52.3 \pm 2.8\%$ depolymerization on amorphous PET film at 50 °C within 24 hours (Lu et al. 2022).
  - On crystalline post-consumer bottle flake ($X_c \approx 34\%$), depolymerization collapses to $<5\%$.
  - High-temperature extrusion amorphization is mandatory to achieve industrial conversions, adding $\$0.49/\text{kg TPA}$.
- **Theoretical Techno-Economic Projection (Unverified Industrially):**
  - 5-cycle ultrafiltration membrane recovery (80% retention) is modeled as an exploratory bioprocess scenario.
  - In practice, severe membrane fouling by hydrophobic oligomers (MHET, BHET) and insolubility of TPA at non-alkaline pH present major unmitigated industrial engineering barriers.
