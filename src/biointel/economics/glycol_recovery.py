"""Ethylene Glycol (EG) Vapor-Liquid Equilibrium and Distillation Thermal Balance.

Models multi-effect evaporation and vacuum distillation for recovering polymer-grade
mono-ethylene glycol (MEG) from dilute aqueous depolymerization digestate (3-6 wt% EG).
Calculates steam duty, thermal energy balance, recovery economics, and solids-loading breakeven.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class GlycolRecoveryOutputs:
    initial_solids_loading_pct: float
    initial_eg_concentration_wt_pct: float
    kg_eg_produced_per_kg_tpa: float
    water_evaporated_kg_per_kg_eg: float
    evaporator_steam_duty_kg_per_kg_eg: float
    distillation_reboiler_steam_kg_per_kg_eg: float
    total_steam_kg_per_kg_tpa: float
    steam_cost_usd_per_kg_tpa: float
    meg_market_value_usd_per_kg_tpa: float
    installed_distillation_capex_usd_per_kg_tpa: float
    net_glycol_recovery_margin_usd_per_kg_tpa: float
    is_glycol_recovery_profitable: bool
    solids_loading_breakeven_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GlycolDistillationModel:
    """Thermal separation model for aqueous mono-ethylene glycol concentration."""

    MW_PET = 192.17
    MW_TPA = 166.13
    MW_EG = 62.07

    # Stoichiometric MEG produced per kg TPA: 62.07 / 166.13 = 0.3736 kg EG / kg TPA
    THEORETICAL_EG_PER_KG_TPA = 62.07 / 166.13

    @classmethod
    def calculate_glycol_recovery(
        cls,
        initial_solids_pct: float = 16.0,          # 16 wt% solids in depolymerization reactor
        steam_cost_per_kg: float = 0.04,           # $0.04/kg low-pressure process steam ($40/metric ton)
        meg_market_price_kg: float = 0.85,         # $0.85/kg virgin mono-ethylene glycol
        triple_effect_steam_economy: float = 2.4,  # kg water evaporated per kg LP steam
        distillation_reboiler_steam_kg: float = 1.25,# kg steam / kg pure EG in vacuum column
        intermediate_concentrate_pct: float = 65.0,# Evaporator concentrates from feed to 65 wt% EG
        distillation_capex_amort_tpa: float = 0.045,# Amortized evaporator & column CAPEX ($/kg TPA)
    ) -> GlycolRecoveryOutputs:
        """
        Calculates thermal steam balance and net margin.
        """
        # Mass of EG per 100 kg initial slurry:
        # 100 kg slurry contains S kg PET.
        # S kg PET yields S * (62.07 / 192.17) = S * 0.323 kg EG in (100 - S) kg water.
        w_s = initial_solids_pct
        kg_eg_in_slurry = w_s * (cls.MW_EG / cls.MW_PET)
        kg_water_in_slurry = 100.0 - w_s
        x_feed = kg_eg_in_slurry / (kg_eg_in_slurry + kg_water_in_slurry) # Initial EG mass fraction

        # Evaporator water removal per kg EG:
        # Water in feed per kg EG: (1 - x_feed) / x_feed
        # Water in concentrate per kg EG: (1 - x_conc) / x_conc
        x_conc = intermediate_concentrate_pct / 100.0
        water_evap_per_kg_eg = ((1.0 - x_feed) / x_feed) - ((1.0 - x_conc) / x_conc)

        # Steam consumption:
        evap_steam_kg_eg = water_evap_per_kg_eg / triple_effect_steam_economy
        total_steam_kg_eg = evap_steam_kg_eg + distillation_reboiler_steam_kg

        # Per kg TPA produced:
        kg_eg_tpa = cls.THEORETICAL_EG_PER_KG_TPA
        total_steam_tpa = kg_eg_tpa * total_steam_kg_eg
        steam_cost_tpa = total_steam_tpa * steam_cost_per_kg

        meg_value_tpa = kg_eg_tpa * meg_market_price_kg
        net_margin_tpa = meg_value_tpa - steam_cost_tpa - distillation_capex_amort_tpa

        # Breakeven solids loading where net margin = 0
        # If solids < breakeven, feed is too dilute and steam cost exceeds recovered MEG revenue
        # meg_value - capex = steam_cost = (kg_eg_tpa * total_steam_kg_eg) * steam_p
        margin_before_steam = meg_value_tpa - distillation_capex_amort_tpa
        max_allowed_steam_tpa = margin_before_steam / steam_cost_per_kg
        max_allowed_steam_kg_eg = max_allowed_steam_tpa / kg_eg_tpa
        max_allowed_evap_steam = max_allowed_steam_kg_eg - distillation_reboiler_steam_kg
        max_water_evap = max_allowed_evap_steam * triple_effect_steam_economy
        # max_water_evap = ((1 - x_be)/x_be) - (1-x_conc)/x_conc
        term = max_water_evap + ((1.0 - x_conc) / x_conc)
        x_be = 1.0 / (term + 1.0)
        # x_be = (S * 0.323) / (S * 0.323 + 100 - S)
        # Solving for S:
        s_be = (100.0 * x_be) / ((cls.MW_EG / cls.MW_PET) * (1.0 - x_be) + x_be)

        return GlycolRecoveryOutputs(
            initial_solids_loading_pct=initial_solids_pct,
            initial_eg_concentration_wt_pct=round(x_feed * 100.0, 2),
            kg_eg_produced_per_kg_tpa=round(kg_eg_tpa, 4),
            water_evaporated_kg_per_kg_eg=round(water_evap_per_kg_eg, 2),
            evaporator_steam_duty_kg_per_kg_eg=round(evap_steam_kg_eg, 2),
            distillation_reboiler_steam_kg_per_kg_eg=round(distillation_reboiler_steam_kg, 2),
            total_steam_kg_per_kg_tpa=round(total_steam_tpa, 3),
            steam_cost_usd_per_kg_tpa=round(steam_cost_tpa, 4),
            meg_market_value_usd_per_kg_tpa=round(meg_value_tpa, 4),
            installed_distillation_capex_usd_per_kg_tpa=distillation_capex_amort_tpa,
            net_glycol_recovery_margin_usd_per_kg_tpa=round(net_margin_tpa, 4),
            is_glycol_recovery_profitable=net_margin_tpa > 0,
            solids_loading_breakeven_pct=round(s_be, 2),
        )
