# Chemical Engineering & Transport Phenomena Methodology

## 1. Oxygen Transfer Rate (OTR) vs. Oxygen Uptake Rate (OUR)
Steady-state aerobic fermentation requires:
$$\text{OTR} \ge \text{OUR}$$

Volumetric Oxygen Transfer Rate:
$$\text{OTR} = k_L a \cdot (C^* - C_L)$$

Where:
- $k_L a$ = Volumetric mass transfer coefficient ($h^{-1}$). In a standard industrial $50,000\text{ L}$ tank with Rushton impellers, maximum achievable $k_L a \approx 120–150\text{ h}^{-1}$ (without pure $\text{O}_2$ enrichment).
- $C^*$ = Dissolved oxygen solubility at $30\text{ °C}$ in saline broth under $1.5\text{ bar}$ head pressure $\approx 0.25\text{ mmol/L}$.
- $C_L$ = Critical dissolved oxygen concentration to avoid cell starvation ($20\% \text{ air sat} \approx 0.05\text{ mmol/L}$).
- Maximum achievable $\text{OTR}_{max} = 140 \cdot (0.25 - 0.05) \approx 28.0\text{ mmol } \text{O}_2 / L / h$ (or $\sim 0.90\text{ g } \text{O}_2 / L / h$).

Oxygen Uptake Rate required for cell growth and protein expression on methanol:
$$\text{OUR} = \frac{\mu \cdot X}{Y_{X/O}} + m_O \cdot X + \frac{q_p \cdot X}{Y_{P/O}}$$

For *P. pastoris* growing at $X = 100\text{ g/L}$ DCW on methanol, experimental OUR ranges from $120–180\text{ mmol } \text{O}_2 / L / h$. This exceeds maximum air-sparged OTR by **4- to 6-fold**, proving that maintaining aerobic conditions at $40\text{ g/L}$ titer is impossible without pure liquid oxygen injection ($> 50\% \text{ O}_2$), which poses severe explosion hazards in methanol-rich off-gas.

## 2. Metabolic Heat Generation & Cooling Duty
Heat generated during methanol oxidation:
$$Q_{met} = \Delta H_{c,MeOH} \cdot r_{MeOH} \approx 727\text{ kJ / mol methanol}$$

Heat removal capacity through tank jacket:
$$Q_{cool} = U \cdot A \cdot \Delta T_{lm}$$

Where:
- $U$ = Overall heat transfer coefficient ($\approx 500\text{ W / m}^2\text{ K}$)
- $A$ = Tank wetted surface area for $50,000\text{ L}$ ($H/D = 3 \implies A \approx 75\text{ m}^2$)
- $\Delta T_{lm}$ = Log-mean temperature difference with $15\text{ °C}$ cooling water and $30\text{ °C}$ broth $\approx 12\text{ °C}$.
- Maximum heat removal capacity:
  $$Q_{cool}^{max} = 500 \cdot 75 \cdot 12 = 450,000\text{ W} = 450\text{ kW}$$

At $X = 100\text{ g/L}$ DCW and methanol consumption rate of $1.5\text{ g/L/h}$ in $40,000\text{ L}$ working volume:
$$Q_{met} = \frac{40,000 \cdot 1.5}{32.04} \cdot 727,000\text{ J/h} \approx 1,361,000\text{ kJ/h} = 378\text{ kW}$$
At peak feeding ($> 2.5\text{ g/L/h}$ required for $40\text{ g/L}$ protein), $Q_{met}$ rises to $> 630\text{ kW}$, exceeding jacket cooling capacity by $> 40\%$. The broth will overheat, denaturing lactoferrin and killing host cells.
