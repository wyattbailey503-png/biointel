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
