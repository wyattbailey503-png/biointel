"""Deterministic Precision Fermentation Techno-Economic Model.

Rigorous unit economics, mass-balance calculations, cost stack decomposition,
and scale sensitivity analysis for industrial biomanufacturing.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class FermentationInputs:
    titer_g_per_l: float = 45.0
    duration_hours: float = 120.0
    turnaround_hours: float = 16.0
    working_volume_liters: float = 50000.0  # 50 m³
    recovery_efficiency: float = 0.85        # 85% DSP recovery
    feedstock_price_usd_per_kg: float = 0.35 # $0.35/kg dextrose
    yield_product_per_substrate: float = 0.38 # 0.38 g product per g dextrose
    utilities_cost_usd_per_batch: float = 4500.0
    dsp_consumables_usd_per_kg: float = 2.80
    annual_labor_overhead_usd: float = 1200000.0
    annual_capex_depreciation_usd: float = 850000.0
    operating_hours_per_year: float = 7920.0  # 330 operating days
    use_dynamic_utilities: bool = False
    facility_type: str = "brownfield"  # "brownfield" or "greenfield"
    electricity_usd_per_kwh: float = 0.08
    biomass_yield_g_per_g: float = 0.50
    greenfield_capex_usd: float = 35000000.0
    greenfield_depreciation_years: float = 15.0


@dataclass
class FermentationOutputs:
    product_mass_per_batch_kg: float
    volumetric_productivity_g_l_h: float
    batch_cycle_time_hours: float
    batches_per_year: float
    annual_production_volume_kg: float
    annual_production_volume_mt: float
    effective_capacity_utilization_pct: float
    feedstock_cost_per_kg: float
    utilities_cost_per_kg: float
    dsp_cost_per_kg: float
    labor_overhead_cost_per_kg: float
    capex_depreciation_per_kg: float
    total_cost_per_kg: float
    break_even_price_20pct_margin: float
    cost_stack_breakdown_pct: Dict[str, float]


class TechnoEconomicFermentationModel:
    """Calculates deterministic mass balance and unit economics for microbial biomanufacturing."""

    @classmethod
    def calculate(cls, inputs: FermentationInputs) -> FermentationOutputs:
        # Dimensional validation
        if inputs.titer_g_per_l <= 0 or inputs.duration_hours <= 0 or inputs.working_volume_liters <= 0:
            raise ValueError("Titer, duration, and working volume must be strictly positive.")
        if not (0 < inputs.recovery_efficiency <= 1.0):
            raise ValueError("Recovery efficiency must be in (0, 1.0].")
        if not (0 < inputs.yield_product_per_substrate <= 1.0):
            raise ValueError("Yield product/substrate must be in (0, 1.0].")

        # 1. Mass balance per batch
        raw_product_kg = (inputs.working_volume_liters * inputs.titer_g_per_l) / 1000.0
        recovered_product_batch_kg = raw_product_kg * inputs.recovery_efficiency
        productivity = inputs.titer_g_per_l / inputs.duration_hours

        # 2. Plant throughput
        cycle_time = inputs.duration_hours + inputs.turnaround_hours
        batches_per_yr = inputs.operating_hours_per_year / cycle_time
        annual_kg = batches_per_yr * recovered_product_batch_kg
        annual_mt = annual_kg / 1000.0
        capacity_utilization = (batches_per_yr * cycle_time / inputs.operating_hours_per_year) * 100.0

        # 3. Cost stack ($/kg of recovered product)
        # Feedstock needed per kg recovered product:
        substrate_kg_per_kg_product = 1.0 / (inputs.yield_product_per_substrate * inputs.recovery_efficiency)
        feedstock_cost_per_kg = substrate_kg_per_kg_product * inputs.feedstock_price_usd_per_kg

        # Utilities: Dynamic physics-based scaling or fixed lump sum
        if inputs.use_dynamic_utilities:
            # First-principles utility estimation:
            # 1. Biomass & Oxygen Uptake
            substrate_batch_kg = raw_product_kg / inputs.yield_product_per_substrate
            biomass_batch_kg = substrate_batch_kg * inputs.biomass_yield_g_per_g
            dcw_g_per_l = (biomass_batch_kg * 1000.0) / inputs.working_volume_liters
            v_working_m3 = inputs.working_volume_liters / 1000.0
            
            # Respiration and OUR (mmol O2 / L broth / h)
            avg_our = max(20.0, dcw_g_per_l * 1.5)
            
            # Agitation & Aeration power (P/V in kW/m3)
            power_vol_kw_m3 = max(1.5, min(4.5, 1.5 + (avg_our / 60.0) * 1.0))
            p_agitation_kw = v_working_m3 * power_vol_kw_m3
            
            # Metabolic heat dissipation (Q_met in kW)
            # ~460 kJ/mol O2 consumed (Thornton's rule)
            q_metabolic_kw = (avg_our * v_working_m3 * 460.0) / 3600.0
            
            # Chiller refrigeration duty (COP = 3.5)
            q_cooling_total_kw = q_metabolic_kw + p_agitation_kw
            p_chiller_kw = q_cooling_total_kw / 3.5
            
            # Plant electrical baseline (pumps, air compressor, instrumentation)
            p_baseline_kw = 35.0
            p_total_electrical_kw = p_agitation_kw + p_chiller_kw + p_baseline_kw
            
            electricity_kwh_per_batch = p_total_electrical_kw * inputs.duration_hours
            electricity_cost_batch = electricity_kwh_per_batch * inputs.electricity_usd_per_kwh
            
            # Saturated steam sterilization (0.4 kg steam / L vessel @ $0.025/kg steam)
            steam_cost_batch = inputs.working_volume_liters * 0.4 * 0.025
            
            effective_utilities_batch = electricity_cost_batch + steam_cost_batch
        else:
            effective_utilities_batch = inputs.utilities_cost_usd_per_batch

        utilities_cost_per_kg = effective_utilities_batch / recovered_product_batch_kg
        dsp_cost_per_kg = inputs.dsp_consumables_usd_per_kg
        labor_cost_per_kg = inputs.annual_labor_overhead_usd / annual_kg

        # CAPEX Depreciation (Greenfield vs Brownfield)
        if inputs.facility_type.lower() == "greenfield":
            annual_depreciation = inputs.greenfield_capex_usd / inputs.greenfield_depreciation_years
        else:
            annual_depreciation = inputs.annual_capex_depreciation_usd

        depreciation_cost_per_kg = annual_depreciation / annual_kg

        total_cost_per_kg = (
            feedstock_cost_per_kg
            + utilities_cost_per_kg
            + dsp_cost_per_kg
            + labor_cost_per_kg
            + depreciation_cost_per_kg
        )

        break_even_20 = total_cost_per_kg / 0.80  # 20% gross margin target

        pcts = {
            "Feedstock": round((feedstock_cost_per_kg / total_cost_per_kg) * 100, 1),
            "Utilities": round((utilities_cost_per_kg / total_cost_per_kg) * 100, 1),
            "Downstream_DSP": round((dsp_cost_per_kg / total_cost_per_kg) * 100, 1),
            "Labor_and_Overhead": round((labor_cost_per_kg / total_cost_per_kg) * 100, 1),
            "CAPEX_Depreciation": round((depreciation_cost_per_kg / total_cost_per_kg) * 100, 1),
        }

        return FermentationOutputs(
            product_mass_per_batch_kg=round(recovered_product_batch_kg, 2),
            volumetric_productivity_g_l_h=round(productivity, 3),
            batch_cycle_time_hours=round(cycle_time, 1),
            batches_per_year=round(batches_per_yr, 1),
            annual_production_volume_kg=round(annual_kg, 1),
            annual_production_volume_mt=round(annual_mt, 2),
            effective_capacity_utilization_pct=round(capacity_utilization, 1),
            feedstock_cost_per_kg=round(feedstock_cost_per_kg, 2),
            utilities_cost_per_kg=round(utilities_cost_per_kg, 2),
            dsp_cost_per_kg=round(dsp_cost_per_kg, 2),
            labor_overhead_cost_per_kg=round(labor_cost_per_kg, 2),
            capex_depreciation_per_kg=round(depreciation_cost_per_kg, 2),
            total_cost_per_kg=round(total_cost_per_kg, 2),
            break_even_price_20pct_margin=round(break_even_20, 2),
            cost_stack_breakdown_pct=pcts,
        )

    @classmethod
    def sensitivity_analysis(
        cls,
        base_inputs: FermentationInputs,
        titers: Optional[List[float]] = None,
        feedstock_prices: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Generate 2D matrix of unit costs across titer and feedstock prices."""
        titers = titers or [15.0, 30.0, 45.0, 60.0, 80.0, 100.0]
        prices = feedstock_prices or [0.25, 0.35, 0.50, 0.65, 0.80]

        matrix: List[Dict[str, Any]] = []
        for t in titers:
            row_data = {"titer_g_per_l": t}
            for p in prices:
                modified = FermentationInputs(**asdict(base_inputs))
                modified.titer_g_per_l = t
                modified.feedstock_price_usd_per_kg = p
                out = cls.calculate(modified)
                row_data[f"cost_feedstock_{p:.2f}"] = out.total_cost_per_kg
            matrix.append(row_data)

        return {
            "titers_evaluated": titers,
            "feedstock_prices_evaluated": prices,
            "sensitivity_matrix": matrix,
        }

    @classmethod
    def render_sensitivity_chart(
        cls,
        sensitivity_results: Dict[str, Any],
        output_dir: Optional[str | Path] = None,
        filename_stem: str = "fermentation_cost_sensitivity",
    ) -> Dict[str, Path]:
        """Renders cost sensitivity curve over titers (SVG + PNG)."""
        out_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent / "outputs" / "figures"
        out_dir.mkdir(parents=True, exist_ok=True)
        svg_path = out_dir / f"{filename_stem}.svg"
        png_path = out_dir / f"{filename_stem}.png"

        titers = sensitivity_results["titers_evaluated"]
        prices = sensitivity_results["feedstock_prices_evaluated"]
        matrix = sensitivity_results["sensitivity_matrix"]

        # Build clean SVG
        width, height = 700, 400
        ml, mr, mt, mb = 60, 40, 40, 50
        pw = width - ml - mr
        ph = height - mt - mb

        all_costs = []
        for row in matrix:
            for p in prices:
                all_costs.append(row[f"cost_feedstock_{p:.2f}"])
        max_cost = max(all_costs) if all_costs else 60.0
        min_cost = 0.0

        colors = ["#16a34a", "#2563eb", "#ea580c", "#dc2626", "#7c3aed"]
        lines_svg = []
        for p_idx, p in enumerate(prices):
            pts = []
            c = colors[p_idx % len(colors)]
            for row in matrix:
                t = row["titer_g_per_l"]
                cost = row[f"cost_feedstock_{p:.2f}"]
                x = ml + ((t - min(titers)) / max(1, max(titers) - min(titers))) * pw
                y = mt + ph - (cost / max_cost) * ph
                pts.append(f"{x:.1f},{y:.1f}")
            poly = " ".join(pts)
            lines_svg.append(f'<polyline fill="none" stroke="{c}" stroke-width="2.5" points="{poly}"/>')
            # Legend label
            lines_svg.append(f'<text x="{width - 180}" y="{mt + 20 + p_idx*18}" font-family="sans-serif" font-size="10" fill="{c}">■ Glucose: ${p:.2f}/kg</text>')

        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="{width/2}" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="14" font-weight="bold" fill="#0f172a">Biomanufacturing Unit Cost Sensitivity to Titer ($/kg)</text>
<line x1="{ml}" y1="{mt+ph}" x2="{ml+pw}" y2="{mt+ph}" stroke="#64748b" stroke-width="1.5"/>
<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ph}" stroke="#64748b" stroke-width="1.5"/>
{"".join(lines_svg)}
<text x="{ml}" y="{height-15}" font-family="sans-serif" font-size="11" fill="#475569">{min(titers)} g/L</text>
<text x="{ml+pw}" y="{height-15}" text-anchor="end" font-family="sans-serif" font-size="11" fill="#475569">{max(titers)} g/L</text>
<text x="{width/2}" y="{height-15}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#475569">Fermentation Titer (g/L)</text>
<text x="15" y="{mt+ph/2}" font-family="sans-serif" font-size="11" fill="#475569" transform="rotate(-90 15 {mt+ph/2})" text-anchor="middle">Unit Cost ($/kg)</text>
</svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        # Render PNG via matplotlib
        try:
            os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_biointel"
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
            for p_idx, p in enumerate(prices):
                c = colors[p_idx % len(colors)]
                costs = [row[f"cost_feedstock_{p:.2f}"] for row in matrix]
                ax.plot(titers, costs, marker="o", lw=2, color=c, label=f"Glucose: ${p:.2f}/kg")

            ax.set_title("Biomanufacturing Unit Cost Sensitivity to Titer", fontsize=12, fontweight="bold")
            ax.set_xlabel("Fermentation Titer (g/L)", fontsize=10)
            ax.set_ylabel("Unit Production Cost ($/kg)", fontsize=10)
            ax.grid(True, linestyle="--", alpha=0.5)
            ax.legend(title="Substrate Price", fontsize=9)
            plt.tight_layout()
            fig.savefig(png_path)
            plt.close(fig)
        except Exception:
            pass

        return {"svg": svg_path, "png": png_path if png_path.exists() else svg_path}
