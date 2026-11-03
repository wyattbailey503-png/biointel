"""Bipolar Membrane Electrodialysis (BMED) Salt Recovery Techno-Economic Model.

Rigorous chemical engineering model for closed-loop electrochemical splitting of sodium sulfate:
Na2SO4 + 2 H2O -> 2 NaOH + H2SO4
Evaluates electrical duty, membrane stack CAPEX, recovered chemical value, and breakeven electricity price.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class BMEDOutputs:
    scale_mt_tpa_year: float
    sodium_sulfate_kg_per_kg_tpa: float
    cell_pair_voltage_volts: float
    current_efficiency_pct: float
    specific_energy_kwh_per_kg_salt: float
    bmed_power_consumption_kwh_per_kg_tpa: float
    electricity_price_kwh: float
    electricity_cost_usd_per_kg_tpa: float
    
    # Recovered Chemical Values ($/kg TPA)
    recovered_naoh_kg_per_kg_tpa: float
    naoh_market_value_usd_per_kg_tpa: float
    recovered_h2so4_kg_per_kg_tpa: float
    h2so4_market_value_usd_per_kg_tpa: float
    avoided_brine_disposal_fee_usd_per_kg_tpa: float
    total_gross_savings_usd_per_kg_tpa: float
    
    # Capital & Membrane Maintenance
    membrane_stack_capex_usd: float
    capex_amortization_usd_per_kg_tpa: float
    membrane_replacement_usd_per_kg_tpa: float
    total_bmed_cost_usd_per_kg_tpa: float
    
    # Net Benefit & Breakeven
    net_economic_benefit_usd_per_kg_tpa: float
    breakeven_electricity_price_usd_per_kwh: float
    is_economically_favorable: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BipolarElectrodialysisModel:
    """First-principles mass and energy balance for electrochemical salt splitting."""

    FARADAY_CONSTANT = 96485.33  # C / mol electrons
    MW_NA2SO4 = 142.04           # g / mol
    MW_NAOH = 40.00              # g / mol
    MW_H2SO4 = 98.08             # g / mol
    MW_TPA = 166.13              # g / mol

    @classmethod
    def calculate_bmed_economics(
        cls,
        scale_mt_tpa_year: float = 40000.0,
        electricity_price_kwh: float = 0.08,
        naoh_market_price_kg: float = 0.45,
        h2so4_market_price_kg: float = 0.12,
        brine_disposal_fee_per_kg_salt: float = 0.03,
        cell_pair_voltage_volts: float = 2.1,
        current_efficiency: float = 0.80,
        current_density_a_m2: float = 800.0,
        membrane_life_years: float = 3.0,
        discount_rate: float = 0.08,
        plant_life_years: int = 15,
    ) -> BMEDOutputs:
        """
        Calculates full electrochemical mass balance and unit economics.
        
        Basis: Stoichiometric PET -> TPA depolymerization neutralization generates
        2.05 mol NaOH / mol TPA neutralized with 1.025 mol H2SO4 / mol TPA,
        yielding 1.025 mol Na2SO4 / mol TPA = 1.1534 kg Na2SO4 / kg TPA.
        """
        # 1. Stoichiometric mass balance per kg TPA
        mol_tpa = 1000.0 / cls.MW_TPA
        mol_salt = mol_tpa * 1.025
        kg_salt_per_kg_tpa = (mol_salt * cls.MW_NA2SO4) / 1000.0  # ~1.1534 kg/kg TPA
        kg_naoh_per_kg_tpa = (mol_tpa * 2.05 * cls.MW_NAOH) / 1000.0  # ~0.4936 kg/kg TPA
        kg_h2so4_per_kg_tpa = (mol_tpa * 1.025 * cls.MW_H2SO4) / 1000.0 # ~0.6052 kg/kg TPA

        # 2. Electrochemical Energy Requirement
        # z = 2 electrons transferred per mole of Na2SO4 split
        z = 2.0
        # W [J / mol] = z * F * V_cell / eta_curr
        joules_per_mol_salt = (z * cls.FARADAY_CONSTANT * cell_pair_voltage_volts) / current_efficiency
        kwh_per_kg_salt = (joules_per_mol_salt / 3.6e6) / (cls.MW_NA2SO4 / 1000.0)
        kwh_per_kg_tpa = kg_salt_per_kg_tpa * kwh_per_kg_salt
        electricity_cost_tpa = kwh_per_kg_tpa * electricity_price_kwh

        # 3. Chemical Valuation & Avoided Disposal
        naoh_val_tpa = kg_naoh_per_kg_tpa * naoh_market_price_kg
        h2so4_val_tpa = kg_h2so4_per_kg_tpa * h2so4_market_price_kg
        avoided_disp_tpa = kg_salt_per_kg_tpa * brine_disposal_fee_per_kg_salt
        gross_savings_tpa = naoh_val_tpa + h2so4_val_tpa + avoided_disp_tpa

        # 4. Capital & Membrane Maintenance
        # Active membrane area required: A = I / i = (mol_salt/s * z * F / eta) / current_density
        annual_salt_kg = scale_mt_tpa_year * 1000.0 * kg_salt_per_kg_tpa
        annual_operating_seconds = 8000.0 * 3600.0
        mols_salt_per_second = (annual_salt_kg * 1000.0 / cls.MW_NA2SO4) / annual_operating_seconds
        total_current_amperes = (mols_salt_per_second * z * cls.FARADAY_CONSTANT) / current_efficiency
        membrane_area_m2 = total_current_amperes / current_density_a_m2

        # Membrane stack installed cost: ~$1,800 per m2 (bipolar + cation + anion membrane trio + titanium frames)
        stack_cost_per_m2 = 1800.0
        installed_capex = membrane_area_m2 * stack_cost_per_m2 * 1.6  # 1.6x multiplier for balance of plant, pumps, rectifiers
        
        # Capital Recovery Factor
        r = discount_rate
        n = plant_life_years
        crf = (r * ((1.0 + r) ** n)) / (((1.0 + r) ** n) - 1.0)
        annual_capex = installed_capex * crf
        capex_tpa = annual_capex / (scale_mt_tpa_year * 1000.0)

        # Membrane replacement (triennial stack refurbishment ~25% of stack Capex every 3 years)
        membrane_maint_tpa = (membrane_area_m2 * stack_cost_per_m2 * 0.25 / membrane_life_years) / (scale_mt_tpa_year * 1000.0)

        total_bmed_cost_tpa = electricity_cost_tpa + capex_tpa + membrane_maint_tpa
        net_benefit_tpa = gross_savings_tpa - total_bmed_cost_tpa

        # Breakeven electricity price: (gross_savings - capex - membrane_maint) / kwh_per_kg_tpa
        breakeven_elec_price = (gross_savings_tpa - capex_tpa - membrane_maint_tpa) / kwh_per_kg_tpa

        return BMEDOutputs(
            scale_mt_tpa_year=scale_mt_tpa_year,
            sodium_sulfate_kg_per_kg_tpa=round(kg_salt_per_kg_tpa, 4),
            cell_pair_voltage_volts=cell_pair_voltage_volts,
            current_efficiency_pct=round(current_efficiency * 100.0, 1),
            specific_energy_kwh_per_kg_salt=round(kwh_per_kg_salt, 3),
            bmed_power_consumption_kwh_per_kg_tpa=round(kwh_per_kg_tpa, 3),
            electricity_price_kwh=electricity_price_kwh,
            electricity_cost_usd_per_kg_tpa=round(electricity_cost_tpa, 4),
            recovered_naoh_kg_per_kg_tpa=round(kg_naoh_per_kg_tpa, 4),
            naoh_market_value_usd_per_kg_tpa=round(naoh_val_tpa, 4),
            recovered_h2so4_kg_per_kg_tpa=round(kg_h2so4_per_kg_tpa, 4),
            h2so4_market_value_usd_per_kg_tpa=round(h2so4_val_tpa, 4),
            avoided_brine_disposal_fee_usd_per_kg_tpa=round(avoided_disp_tpa, 4),
            total_gross_savings_usd_per_kg_tpa=round(gross_savings_tpa, 4),
            membrane_stack_capex_usd=round(installed_capex, 2),
            capex_amortization_usd_per_kg_tpa=round(capex_tpa, 4),
            membrane_replacement_usd_per_kg_tpa=round(membrane_maint_tpa, 4),
            total_bmed_cost_usd_per_kg_tpa=round(total_bmed_cost_tpa, 4),
            net_economic_benefit_usd_per_kg_tpa=round(net_benefit_tpa, 4),
            breakeven_electricity_price_usd_per_kwh=round(breakeven_elec_price, 4),
            is_economically_favorable=net_benefit_tpa > 0,
        )
