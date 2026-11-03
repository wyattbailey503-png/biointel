"""Life Cycle Assessment (LCA) Scope 1-3 Greenhouse Gas (GHG) Accounting.

Computes cradle-to-gate Global Warming Potential (GWP in kg CO2e / kg TPA)
for enzymatic PET recycling vs petrochemical virgin purified terephthalic acid (PTA).
Evaluates sensitivity to regional electrical grid emission factors (coal vs renewable/nuclear).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class LCAOutputs:
    grid_emission_factor_kg_co2_per_kwh: float
    grid_region_description: str
    electricity_gwp_kg_co2e_per_kg_tpa: float
    steam_gwp_kg_co2e_per_kg_tpa: float
    chemical_reagents_gwp_kg_co2e_per_kg_tpa: float
    enzyme_production_gwp_kg_co2e_per_kg_tpa: float
    avoided_incineration_credit_kg_co2e: float
    net_enzymatic_gwp_kg_co2e_per_kg_tpa: float
    virgin_petrochemical_pta_gwp_baseline: float
    avoided_ghg_emissions_kg_co2e_per_kg_tpa: float
    ghg_reduction_pct_vs_virgin: float
    is_carbon_beneficial: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LifeCycleAssessmentModel:
    """Cradle-to-gate carbon accounting engine for biocatalytic plastics recycling."""

    VIRGIN_PTA_GWP_BASELINE = 1.95  # kg CO2e / kg virgin petrochemical PTA (ecoinvent / PlasticsEurope)

    @classmethod
    def evaluate_carbon_footprint(
        cls,
        grid_co2_kg_per_kwh: float = 0.38,  # US national average grid factor
        grid_region: str = "US Average Grid (Mix of Natural Gas, Coal, Nuclear, Renewables)",
        extruder_electricity_kwh_tpa: float = 0.539,
        bioreactor_electricity_kwh_tpa: float = 0.350,
        steam_consumption_kg_tpa: float = 3.11,
        steam_co2_kg_per_kg: float = 0.22,  # Natural gas boiler steam (54 kg CO2/GJ)
        naoh_consumption_kg_tpa: float = 0.4936,
        naoh_co2_kg_per_kg: float = 1.30,   # Chlor-alkali process carbon footprint
        h2so4_consumption_kg_tpa: float = 0.6052,
        h2so4_co2_kg_per_kg: float = 0.11,  # Contact process sulfuric acid
        enzyme_kg_tpa: float = 0.0036,
        enzyme_co2_kg_per_kg: float = 8.50, # Precision fermentation biocatalyst production
        avoided_incineration_credit_kg: float = 0.45,# EoL avoided municipal waste incineration
    ) -> LCAOutputs:
        """
        Calculates net GWP and emissions delta against fossil incumbent.
        """
        # 1. Total electricity GWP
        total_elec_kwh = extruder_electricity_kwh_tpa + bioreactor_electricity_kwh_tpa
        elec_gwp = total_elec_kwh * grid_co2_kg_per_kwh

        # 2. Process steam GWP
        steam_gwp = steam_consumption_kg_tpa * steam_co2_kg_per_kg

        # 3. Reagents GWP
        naoh_gwp = naoh_consumption_kg_tpa * naoh_co2_kg_per_kg
        h2so4_gwp = h2so4_consumption_kg_tpa * h2so4_co2_kg_per_kg
        reagents_gwp = naoh_gwp + h2so4_gwp

        # 4. Enzyme production GWP
        enzyme_gwp = enzyme_kg_tpa * enzyme_co2_kg_per_kg

        # 5. Net enzymatic recycling GWP (Scope 1 + Scope 2 + Scope 3 upstream - credits)
        net_gwp = elec_gwp + steam_gwp + reagents_gwp + enzyme_gwp - avoided_incineration_credit_kg

        avoided_co2 = cls.VIRGIN_PTA_GWP_BASELINE - net_gwp
        reduct_pct = (avoided_co2 / cls.VIRGIN_PTA_GWP_BASELINE) * 100.0

        return LCAOutputs(
            grid_emission_factor_kg_co2_per_kwh=grid_co2_kg_per_kwh,
            grid_region_description=grid_region,
            electricity_gwp_kg_co2e_per_kg_tpa=round(elec_gwp, 4),
            steam_gwp_kg_co2e_per_kg_tpa=round(steam_gwp, 4),
            chemical_reagents_gwp_kg_co2e_per_kg_tpa=round(reagents_gwp, 4),
            enzyme_production_gwp_kg_co2e_per_kg_tpa=round(enzyme_gwp, 4),
            avoided_incineration_credit_kg_co2e=round(avoided_incineration_credit_kg, 4),
            net_enzymatic_gwp_kg_co2e_per_kg_tpa=round(net_gwp, 4),
            virgin_petrochemical_pta_gwp_baseline=cls.VIRGIN_PTA_GWP_BASELINE,
            avoided_ghg_emissions_kg_co2e_per_kg_tpa=round(avoided_co2, 4),
            ghg_reduction_pct_vs_virgin=round(reduct_pct, 1),
            is_carbon_beneficial=avoided_co2 > 0,
        )
