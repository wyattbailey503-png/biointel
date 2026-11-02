# Biophysical Comparison & Delivery Packaging Methodology

## 1. AAV Vector Packaging Limits
Adeno-associated virus (AAV) capsids physically package single-stranded DNA genomes up to an upper packaging ceiling:
$$L_{max} \approx 4.7\text{ kb (including inverted terminal repeats, ITRs, } 2 \times 145\text{ bp} = 290\text{ bp})$$
Available internal coding payload:
$$L_{payload} = 4,700 - 290 - L_{promoter} - L_{polyA} - L_{gRNA/pegRNA}$$

For typical minimal regulatory elements:
- $L_{promoter} \approx 250\text{ bp}$ (e.g. minimal CMV or short EFS)
- $L_{polyA} \approx 100\text{ bp}$ (e.g. synthetic polyA)
- $L_{gRNA} \approx 100\text{ bp}$; $L_{pegRNA} \approx 140\text{ bp}$
- Maximum allowed open reading frame (ORF):
  $$L_{ORF}^{max} \approx 4,700 - 290 - 250 - 100 - 140 = 3,920\text{ bp}$$

### Editor Size Comparison
- **SpCas9 (WT):** $4,104\text{ bp}$ ($1,368\text{ aa}$) $\implies$ Borderline/exceeds with full promoter; fits with split or minimal promoter.
- **ABE8e / BE4max:** $4,500–5,100\text{ bp}$ $\implies$ Exceeds single AAV; requires compact Cas9 orthologs (e.g. SaCas9, CjCas9) to fit single vector.
- **PE2 / PEmax:** SpCas9 nickase ($4,104\text{ bp}$) + engineered M-MLV RT ($2,031\text{ bp}$) + linkers/NLS ($200\text{ bp}$) = $6,335\text{ bp}$ ($2,112\text{ aa}$) $\implies$ Strictly impossible in single AAV; requires dual-AAV with split inteins.

## 2. Chemical Synthesis Yield of Extended Guides
The coupling yield of solid-phase phosphoramidite oligonucleotide synthesis for a guide of length $N$ nucleotides with per-cycle coupling efficiency $E$ ($0.992 \le E \le 0.996$):

$$Y_{full\_length} = E^{N-1}$$

- Canonical Cas9 sgRNA ($N=100\text{ nt}$, $E=0.995$):
  $$Y = (0.995)^{99} \approx 60.9\%$$
- Prime Editing pegRNA ($N=145\text{ nt}$, $E=0.995$):
  $$Y = (0.995)^{144} \approx 48.6\%$$
The $20\%$ drop in full-length purity increases synthesis truncation products that compete for Cas9 binding.
