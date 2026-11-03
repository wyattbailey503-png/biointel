"""Thermal Pinch Analysis & Heat Exchanger Network Integration.

Applies first-principles thermodynamic pinch analysis (Linhoff problem table algorithm)
to optimize heat recovery in commercial enzymatic PET recycling plants:
1. Matches hot streams (digestate cooling, distillation condenser, neutralization heat)
   against cold streams (slurry preheating, reboiler duty).
2. Calculates minimum hot utility Q_H,min (steam required) and minimum cold utility Q_C,min.
3. Identifies pinch temperature T_pinch (at Delta T_min = 10 K).
4. Quantifies annual energy cost savings and Scope 1 boiler carbon reduction.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class ProcessStream:
    name: str
    stream_type: str  # 'HOT' (needs cooling) or 'COLD' (needs heating)
    t_supply_c: float
    t_target_c: float
    heat_capacity_flowrate_kw_per_k: float  # CP = m_dot * Cp [kW / K]
    enthalpy_duty_kw: float


@dataclass
class PinchAnalysisOutputs:
    delta_t_min_k: float
    pinch_temperature_hot_c: float
    pinch_temperature_cold_c: float
    total_hot_duty_available_kw: float
    total_cold_duty_required_kw: float
    minimum_hot_utility_kw: float   # External process steam needed
    minimum_cold_utility_kw: float  # External cooling water/chiller needed
    maximum_internal_heat_recovery_kw: float
    energy_recovery_efficiency_pct: float
    steam_cost_savings_usd_per_year: float
    avoided_boiler_ghg_mt_co2e_per_year: float
    pinch_verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ThermalPinchAnalyzer:
    """Thermodynamic heat integration and pinch point calculation engine."""

    @classmethod
    def evaluate_plant_heat_integration(
        cls,
        scale_mt_tpa_year: float = 50000.0,
        operating_hours_per_year: float = 8000.0,
        steam_cost_per_mwh_th: float = 38.0,      # ~$38/MWh thermal ($0.038/kWh thermal)
        boiler_emission_factor_kg_co2_mwh: float = 202.0, # Natural gas boiler emissions
        delta_t_min_k: float = 10.0,
    ) -> PinchAnalysisOutputs:
        """
        Executes problem table algorithm for a standard commercial depolymerization plant.
        """
        # Flowrates based on 50,000 MT/year plant: ~6250 kg TPA / hr = ~1.736 kg TPA / s
        # Total slurry throughput (~16 wt% solids) ~ 40,000 kg slurry / hr = ~11.11 kg/s
        # Specific heat of aqueous slurry ~ 3.8 kJ / kg / K -> CP ~ 42.2 kW / K

        streams = [
            # Stream 1: Hot digestate effluent cooling from 65 °C to 30 °C before precipitation
            ProcessStream(
                name="Digestate Effluent Cooling",
                stream_type="HOT",
                t_supply_c=65.0,
                t_target_c=30.0,
                heat_capacity_flowrate_kw_per_k=42.2,
                enthalpy_duty_kw=42.2 * (65.0 - 30.0), # 1477.0 kW
            ),
            # Stream 2: Hot EG overhead distillation vapor condensation at 110 °C down to 70 °C
            ProcessStream(
                name="EG Distillation Condenser",
                stream_type="HOT",
                t_supply_c=110.0,
                t_target_c=70.0,
                heat_capacity_flowrate_kw_per_k=18.5,
                enthalpy_duty_kw=18.5 * (110.0 - 70.0), # 740.0 kW
            ),
            # Stream 3: Cold incoming PET flake slurry preheating from 20 °C to 65 °C
            ProcessStream(
                name="Slurry Reactor Preheating",
                stream_type="COLD",
                t_supply_c=20.0,
                t_target_c=65.0,
                heat_capacity_flowrate_kw_per_k=42.2,
                enthalpy_duty_kw=42.2 * (65.0 - 20.0), # 1899.0 kW
            ),
            # Stream 4: Cold EG column feed preheating from 35 °C to 95 °C
            ProcessStream(
                name="EG Column Feed Preheating",
                stream_type="COLD",
                t_supply_c=35.0,
                t_target_c=95.0,
                heat_capacity_flowrate_kw_per_k=14.0,
                enthalpy_duty_kw=14.0 * (95.0 - 35.0), # 840.0 kW
            ),
        ]

        total_hot_duty = sum(s.enthalpy_duty_kw for s in streams if s.stream_type == "HOT")
        total_cold_duty = sum(s.enthalpy_duty_kw for s in streams if s.stream_type == "COLD")

        # Problem Table Algorithm:
        # Shift temperatures: Hot streams shifted down by Delta T_min / 2; Cold shifted up by Delta T_min / 2
        shift_half = delta_t_min_k / 2.0
        interval_temps: set[float] = set()

        for s in streams:
            if s.stream_type == "HOT":
                interval_temps.add(s.t_supply_c - shift_half)
                interval_temps.add(s.t_target_c - shift_half)
            else:
                interval_temps.add(s.t_supply_c + shift_half)
                interval_temps.add(s.t_target_c + shift_half)

        sorted_intervals = sorted(list(interval_temps), reverse=True)

        # Calculate heat balance in each temperature interval
        heat_surpluses: List[float] = []
        for i in range(len(sorted_intervals) - 1):
            t_high = sorted_intervals[i]
            t_low = sorted_intervals[i + 1]
            delta_t_interval = t_high - t_low

            # Sum CP_hot - Sum CP_cold for active streams in this interval
            cp_hot_sum = 0.0
            cp_cold_sum = 0.0

            for s in streams:
                if s.stream_type == "HOT":
                    s_high = s.t_supply_c - shift_half
                    s_low = s.t_target_c - shift_half
                    if s_high >= t_high and s_low <= t_low:
                        cp_hot_sum += s.heat_capacity_flowrate_kw_per_k
                else:
                    s_low = s.t_supply_c + shift_half
                    s_high = s.t_target_c + shift_half
                    if s_high >= t_high and s_low <= t_low:
                        cp_cold_sum += s.heat_capacity_flowrate_kw_per_k

            interval_delta_h = (cp_hot_sum - cp_cold_sum) * delta_t_interval
            heat_surpluses.append(interval_delta_h)

        # Heat cascade from 0 external hot utility
        heat_cascade = [0.0]
        for surplus in heat_surpluses:
            heat_cascade.append(heat_cascade[-1] + surplus)

        # Minimum hot utility is the most negative value in the cascade (heat deficit)
        min_cascade_val = min(heat_cascade)
        q_h_min = max(0.0, -min_cascade_val)

        # Feasible cascade with Q_H,min added
        feasible_cascade = [val + q_h_min for val in heat_cascade]
        q_c_min = feasible_cascade[-1]

        # Identify pinch point (where feasible cascade equals zero)
        pinch_index = feasible_cascade.index(0.0)
        t_pinch_shifted = sorted_intervals[pinch_index]
        t_pinch_hot = t_pinch_shifted + shift_half
        t_pinch_cold = t_pinch_shifted - shift_half

        # Max internal heat recovery:
        heat_recovery_kw = total_cold_duty - q_h_min
        recovery_efficiency_pct = (heat_recovery_kw / max(1.0, total_cold_duty)) * 100.0

        # Annual economic and carbon savings:
        annual_recovered_mwh_th = (heat_recovery_kw * operating_hours_per_year) / 1000.0
        annual_steam_savings_usd = annual_recovered_mwh_th * steam_cost_per_mwh_th
        annual_avoided_co2_mt = (annual_recovered_mwh_th * boiler_emission_factor_kg_co2_mwh) / 1000.0

        verdict = (
            f"PINCH CONFIRMED at T_hot = {t_pinch_hot:.1f} °C, T_cold = {t_pinch_cold:.1f} °C. "
            f"Internal heat recovery slashes required boiler steam from {total_cold_duty:.0f} kW to {q_h_min:.0f} kW "
            f"({recovery_efficiency_pct:.1f}% reduction)."
        )

        return PinchAnalysisOutputs(
            delta_t_min_k=delta_t_min_k,
            pinch_temperature_hot_c=round(t_pinch_hot, 1),
            pinch_temperature_cold_c=round(t_pinch_cold, 1),
            total_hot_duty_available_kw=round(total_hot_duty, 1),
            total_cold_duty_required_kw=round(total_cold_duty, 1),
            minimum_hot_utility_kw=round(q_h_min, 1),
            minimum_cold_utility_kw=round(q_c_min, 1),
            maximum_internal_heat_recovery_kw=round(heat_recovery_kw, 1),
            energy_recovery_efficiency_pct=round(recovery_efficiency_pct, 1),
            steam_cost_savings_usd_per_year=round(annual_steam_savings_usd, 2),
            avoided_boiler_ghg_mt_co2e_per_year=round(annual_avoided_co2_mt, 1),
            pinch_verdict=verdict,
        )
