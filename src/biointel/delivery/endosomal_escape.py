"""Intracellular Delivery, Endosomal Escape & Nuclear Translocation PK/PD Model.

Models the fundamental biophysical bottleneck of non-viral gene editing therapeutics (LNP mRNA / pegRNA):
1. Whole-body organ biodistribution partitioning (hepatic parenchymal vs Kupffer vs extrahepatic).
2. Endocytic internalization into early endosomes.
3. Endosomal entrapment & escape dynamics: quantifies the benchmark physical constraint that
   98.0% - 99.0% of endocytosed nanoparticle cargo is trapped and routed to lysosomal degradation.
4. Cytosolic translation, ribonucleoprotein (RNP) assembly, and active nuclear pore import.
5. Predicts effective nuclear dose fraction and clinical therapeutic index (ALT/AST margin).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class DeliveryPKPDOutputs:
    administered_dose_mg_per_kg: float
    target_organ: str
    target_organ_biodistribution_fraction: float
    reticuloendothelial_clearance_fraction: float
    cellular_endocytosis_efficiency: float
    endosomal_escape_efficiency: float
    lysosomal_degradation_fraction: float
    cytosolic_intact_fraction: float
    nuclear_translocation_efficiency: float
    effective_nuclear_payload_fraction: float
    cytosolic_effective_copies_per_cell: float
    nuclear_effective_copies_per_cell: float
    clinical_toxicity_risk: str
    diligence_verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IntracellularDeliveryPKPDModel:
    """Rigorous pharmacokinetic/pharmacodynamic intracellular barrier model."""

    # Typical LNP specifications: ~80 nm diameter, ~500 mRNA molecules / LNP
    AVOGADRO = 6.02214076e23
    MW_PRIME_EDITOR_MRNA_G_MOL = 2.1e6   # ~6,300 nt mRNA ~ 2.1 MDa
    HEPATOCYTES_PER_GRAM_LIVER = 1.35e8
    AVERAGE_HUMAN_LIVER_GRAMS = 1500.0

    @classmethod
    def evaluate_delivery_barriers(
        cls,
        administered_dose_mg_per_kg: float = 0.50,
        patient_weight_kg: float = 70.0,
        target_tissue: str = "LIVER_HEPATOCYTES", # vs "EXTRAHEPATIC_CNS" or "EXTRAHEPATIC_HEART"
        endosomal_escape_efficiency: float = 0.015, # 1.5% escape (typical benchmark 1-2%)
        nuclear_import_efficiency: float = 0.65,    # 65% NLS-mediated nuclear import
    ) -> DeliveryPKPDOutputs:
        """
        Solves sequential organ, cellular, endosomal, and nuclear delivery barriers.
        """
        # 1. Whole-body biodistribution
        if target_tissue == "LIVER_HEPATOCYTES":
            f_target = 0.70      # 70% to liver parenchyma via ApoE / LDLR
            f_clearance = 0.25   # 25% cleared by splenic macrophages / Kupffer
        elif target_tissue == "EXTRAHEPATIC_CNS":
            f_target = 0.005     # <0.5% crosses blood-brain barrier without disruption
            f_clearance = 0.95
        elif target_tissue == "EXTRAHEPATIC_HEART":
            f_target = 0.03      # ~3% to myocardium
            f_clearance = 0.90
        else:
            f_target = 0.05
            f_clearance = 0.85

        f_endocytosis = 0.85     # 85% of bound target LNPs internalized

        # 2. Endosomal escape vs lysosomal destruction
        eta_esc = max(0.001, min(0.10, endosomal_escape_efficiency))
        f_lysosomal = 1.0 - eta_esc

        # 3. Overall effective nuclear delivery fraction:
        # Phi_nuc = f_target * f_endocytosis * eta_escape * eta_nuclear
        f_cytosol = f_target * f_endocytosis * eta_esc
        f_nuclear = f_cytosol * nuclear_import_efficiency

        # Total mRNA molecules administered
        total_dose_mg = administered_dose_mg_per_kg * patient_weight_kg
        total_moles_mrna = (total_dose_mg * 1e-3) / cls.MW_PRIME_EDITOR_MRNA_G_MOL
        total_molecules_mrna = total_moles_mrna * cls.AVOGADRO

        # Number of target cells (e.g. liver: ~2.0e11 hepatocytes)
        if target_tissue == "LIVER_HEPATOCYTES":
            total_target_cells = cls.HEPATOCYTES_PER_GRAM_LIVER * cls.AVERAGE_HUMAN_LIVER_GRAMS  # ~2.025e11
        else:
            total_target_cells = 1.0e10

        cytosolic_copies_per_cell = (total_molecules_mrna * f_cytosol) / total_target_cells
        nuclear_copies_per_cell = (total_molecules_mrna * f_nuclear) / total_target_cells

        # Clinical toxicity risk evaluation:
        # At doses > 0.7 mg/kg in non-human primates, standard ionizable lipids cause ALT/AST elevations
        if administered_dose_mg_per_kg > 0.75:
            tox_risk = "SEVERE_HEPATOTOXICITY_RISK: Dose exceeds clinical MTD (ALT/AST grade 3/4 risk)."
        elif administered_dose_mg_per_kg > 0.35:
            tox_risk = "MODERATE_ELEVATION_RISK: Reversible transient transaminitis expected."
        else:
            tox_risk = "LOW_SYSTEMIC_TOXICITY: Well within clinical safety window."

        if f_nuclear < 0.001:
            verdict = (
                f"DELIVERY INFEASIBLE: Effective nuclear fraction ({f_nuclear*100:.3f}%) is too low "
                f"to achieve therapeutic editing threshold in {target_tissue}. Target organ requires viral AAV or engineered VLP."
            )
        elif nuclear_copies_per_cell < 10.0:
            verdict = (
                f"MARGINAL EFFICACY: Nuclear copy number ({nuclear_copies_per_cell:.1f} copies/cell) "
                f"insufficient for high-efficiency allelic modification. In vitro claims fail in vivo."
            )
        else:
            verdict = (
                f"POTENTIALLY FEASIBLE FOR MONOGENIC DISORDER: Delivers {nuclear_copies_per_cell:.1f} nuclear "
                f"editor molecules/cell at clinically tolerable {administered_dose_mg_per_kg} mg/kg."
            )

        return DeliveryPKPDOutputs(
            administered_dose_mg_per_kg=administered_dose_mg_per_kg,
            target_organ=target_tissue,
            target_organ_biodistribution_fraction=round(f_target, 4),
            reticuloendothelial_clearance_fraction=round(f_clearance, 4),
            cellular_endocytosis_efficiency=round(f_endocytosis, 3),
            endosomal_escape_efficiency=round(eta_esc, 4),
            lysosomal_degradation_fraction=round(f_lysosomal, 4),
            cytosolic_intact_fraction=round(f_cytosol, 6),
            nuclear_translocation_efficiency=round(nuclear_import_efficiency, 3),
            effective_nuclear_payload_fraction=round(f_nuclear, 6),
            cytosolic_effective_copies_per_cell=round(cytosolic_copies_per_cell, 1),
            nuclear_effective_copies_per_cell=round(nuclear_copies_per_cell, 1),
            clinical_toxicity_risk=tox_risk,
            diligence_verdict=verdict,
        )
