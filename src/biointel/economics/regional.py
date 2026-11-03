"""Multi-Regional Techno-Economic Benchmark Matrix Engine.

Eliminates 'Geographic / Western Baseline Bias' by evaluating unit economics across
distinct regional industrial clusters:
1. US_GULF_COAST: Standard benchmark for chemical and petrochemical infrastructure.
2. WESTERN_EUROPE: High energy costs, carbon tariffs, and regulatory recycled content premiums.
3. EAST_ASIA: Low modular fabrication CapEx, lower labor rates, and competitive electricity.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class GeographicRegion(str, Enum):
    US_GULF_COAST = "US_GULF_COAST"
    WESTERN_EUROPE = "WESTERN_EUROPE"
    EAST_ASIA = "EAST_ASIA"


@dataclass(frozen=True)
class RegionalEconomicParameters:
    region_id: GeographicRegion
    region_name: str
    industrial_electricity_usd_per_kwh: float
    process_steam_usd_per_mwh_th: float
    loaded_operator_labor_usd_per_year: float
    baled_pet_scrap_usd_per_kg: float
    capex_lang_installation_factor: float
    weighted_average_cost_of_capital_pct: float
    carbon_tax_usd_per_mt_co2e: float


@dataclass(frozen=True)
class RegionalCostOutput:
    region_id: str
    region_name: str
    unit_cost_usd: float
    cost_delta_vs_us_pct: float
    electricity_contribution_usd: float
    labor_contribution_usd: float
    capex_contribution_usd: float
    feedstock_contribution_usd: float
    commercial_viability_verdict: str


class RegionalCostEngine:
    """Calculates multi-regional comparative cost structures for biotechnology processes."""

    REGIONAL_BENCHMARKS: Dict[GeographicRegion, RegionalEconomicParameters] = {
        GeographicRegion.US_GULF_COAST: RegionalEconomicParameters(
            region_id=GeographicRegion.US_GULF_COAST,
            region_name="United States (Gulf Coast Industrial Hub)",
            industrial_electricity_usd_per_kwh=0.08,
            process_steam_usd_per_mwh_th=38.0,
            loaded_operator_labor_usd_per_year=140_000.0,
            baled_pet_scrap_usd_per_kg=0.35,
            capex_lang_installation_factor=4.0,
            weighted_average_cost_of_capital_pct=8.0,
            carbon_tax_usd_per_mt_co2e=0.0,
        ),
        GeographicRegion.WESTERN_EUROPE: RegionalEconomicParameters(
            region_id=GeographicRegion.WESTERN_EUROPE,
            region_name="Western Europe (Antwerp / Rhine Cluster)",
            industrial_electricity_usd_per_kwh=0.16,
            process_steam_usd_per_mwh_th=62.0,
            loaded_operator_labor_usd_per_year=125_000.0,
            baled_pet_scrap_usd_per_kg=0.45,  # EU packaging mandate premium
            capex_lang_installation_factor=4.5,
            weighted_average_cost_of_capital_pct=7.0,
            carbon_tax_usd_per_mt_co2e=85.0,  # EU ETS carbon allowance price
        ),
        GeographicRegion.EAST_ASIA: RegionalEconomicParameters(
            region_id=GeographicRegion.EAST_ASIA,
            region_name="East Asia (Coastal China / Southeast Asia)",
            industrial_electricity_usd_per_kwh=0.05,
            process_steam_usd_per_mwh_th=26.0,
            loaded_operator_labor_usd_per_year=45_000.0,
            baled_pet_scrap_usd_per_kg=0.22,
            capex_lang_installation_factor=2.8,  # Highly efficient domestic equipment supply chain
            weighted_average_cost_of_capital_pct=9.0,
            carbon_tax_usd_per_mt_co2e=12.0,
        ),
    }

    @classmethod
    def evaluate_regional_matrix(
        cls,
        base_us_cost: float,
        power_intensity_kwh_per_unit: float,
        labor_hours_per_unit: float,
        feedstock_kg_per_unit: float,
        base_capex_per_unit: float,
    ) -> Dict[str, RegionalCostOutput]:
        """
        Transforms base engineering requirements across all 3 regional parameter profiles.
        """
        us_params = cls.REGIONAL_BENCHMARKS[GeographicRegion.US_GULF_COAST]
        results: Dict[str, RegionalCostOutput] = {}

        for reg_key, params in cls.REGIONAL_BENCHMARKS.items():
            # Adjust variable components
            power_cost = power_intensity_kwh_per_unit * params.industrial_electricity_usd_per_kwh
            # Labor hourly basis: 2000 hours/year
            labor_rate_hr = params.loaded_operator_labor_usd_per_year / 2000.0
            labor_cost = labor_hours_per_unit * labor_rate_hr
            feedstock_cost = feedstock_kg_per_unit * params.baled_pet_scrap_usd_per_kg
            # CapEx scaled by Lang factor relative to US
            capex_adj = base_capex_per_unit * (params.capex_lang_installation_factor / us_params.capex_lang_installation_factor)

            # Total adjusted cost
            unit_total = round(power_cost + labor_cost + feedstock_cost + capex_adj, 4)
            pct_delta = round(((unit_total - base_us_cost) / base_us_cost) * 100.0, 1)

            verdict = "HIGHLY_COMPETITIVE" if pct_delta < -10 else ("COST_PARITY" if abs(pct_delta) <= 10 else "COST_PREMIUM_BURDEN")

            results[reg_key.value] = RegionalCostOutput(
                region_id=reg_key.value,
                region_name=params.region_name,
                unit_cost_usd=unit_total,
                cost_delta_vs_us_pct=pct_delta,
                electricity_contribution_usd=round(power_cost, 4),
                labor_contribution_usd=round(labor_cost, 4),
                capex_contribution_usd=round(capex_adj, 4),
                feedstock_contribution_usd=round(feedstock_cost, 4),
                commercial_viability_verdict=verdict,
            )

        return results
