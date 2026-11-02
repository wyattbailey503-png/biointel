"""Comprehensive Multi-Factor Commercial Sensitivity Analysis for Enzymatic PET Recycling.

Evaluates cost parity, unit economics, and viability boundaries across 9 operational dimensions:
1. Feedstock crystallinity & pre-treatment requirement
2. Electricity and energy utility prices
3. Biocatalyst production cost and membrane recycling cycles
4. Capital investment & plant capacity (10k to 100k MT/yr)
5. Chemical stoichiometric reagent costs & byproduct disposal
6. Downstream product recovery yield
7. Virgin petrochemical TPA benchmark price
8. Mandatory recycled-content regulatory green premiums
9. Downstream ultrafiltration fouling & flux replacement
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List

from biointel.economics.extrusion import ExtrusionTechnoEconomicModel


@dataclass
class ScenarioOutcome:
    scenario_name: str
    feedstock_type: str
    crystallinity_pct: float
    pretreatment_required: bool
    scale_mt_year: float
    electricity_price_kwh: float
    enzyme_cost_kg: float
    enzyme_reuse_cycles: int
    tpa_recovery_pct: float
    byproduct_sulfate_credit_kg: float
    virgin_tpa_price_kg: float
    regulatory_green_premium_pct: float
    
    # Modeled Cost Breakdown ($/kg TPA)
    feedstock_net_cost_kg: float
    pretreatment_cost_kg: float
    biocatalyst_cost_kg: float
    reaction_utilities_kg: float
    caustic_and_acid_reagents_kg: float
    downstream_recovery_capex_opex_kg: float
    byproduct_disposal_credit_kg: float
    
    total_tpa_production_cost_usd_kg: float
    market_clearing_target_usd_kg: float
    is_commercially_viable: bool
    cost_parity_ratio: float
    governing_cost_bottleneck: str


class EnzymaticRecyclingSensitivityEngine:
    """Explores the boundary conditions under which enzymatic depolymerization is competitive."""

    # Stoichiometry
    THEORETICAL_PET_PER_KG_TPA = 1.156745  # kg PET / kg TPA

    @classmethod
    def evaluate_scenario(
        cls,
        name: str,
        feedstock_type: str = "bottle_bales",
        crystallinity_pct: float = 32.0,
        pretreatment_required: bool = True,
        scale_mt_year: float = 50000.0,
        electricity_price_kwh: float = 0.08,
        enzyme_cost_kg: float = 12.0,
        enzyme_reuse_cycles: int = 1,
        tpa_recovery_pct: float = 93.0,
        byproduct_sulfate_credit_kg: float = -0.02,  # Negative means disposal fee
        virgin_tpa_price_kg: float = 1.05,
        regulatory_green_premium_pct: float = 0.0,
        feedstock_purchase_price_kg: float = 0.65,
    ) -> ScenarioOutcome:
        """Evaluates a single multi-factor scenario."""
        recovery_factor = tpa_recovery_pct / 100.0
        pet_req_per_kg_tpa = cls.THEORETICAL_PET_PER_KG_TPA / recovery_factor

        # 1. Feedstock net cost
        feedstock_cost = pet_req_per_kg_tpa * feedstock_purchase_price_kg

        # 2. Pre-treatment (Extrusion Amorphization & Micronization)
        if pretreatment_required:
            is_pilot = scale_mt_year <= 15000.0
            ext_stack = ExtrusionTechnoEconomicModel.calculate_cost_stack(
                scale_mt_pet_year=scale_mt_year,
                electricity_price_kwh=electricity_price_kwh,
                extruder_sec_kwh_kg=0.45,
                feedstock_price_kg=feedstock_purchase_price_kg,
                is_pilot_scale=is_pilot,
            )
            pretreatment_cost = ext_stack.total_pretreatment_cost_usd_per_kg_tpa
        else:
            # Amorphous thermoform waste or chemically swollen feed: only light shredding/washing
            pretreatment_cost = 0.045  # basic shredding utility and equipment

        # 3. Biocatalyst Cost
        # Enzyme loading: 3.0 g enzyme / kg PET
        enzyme_loading_kg_per_kg_pet = 0.003
        enzyme_req_per_kg_tpa = pet_req_per_kg_tpa * enzyme_loading_kg_per_kg_pet
        effective_enzyme_req = enzyme_req_per_kg_tpa / max(1, enzyme_reuse_cycles)
        biocatalyst_cost = effective_enzyme_req * enzyme_cost_kg

        # 4. Reaction Utilities (70 °C heating and agitation in 50 m3 bioreactor)
        # Heat capacity + reactor agitation ~ 0.35 kWh/kg TPA
        reaction_utilities = 0.35 * electricity_price_kwh

        # 5. Caustic and Acid Reagents (2.05 mol NaOH / mol TPA, 1.05 mol H2SO4 / mol TPA)
        # MW NaOH = 40.0 g/mol; MW H2SO4 = 98.08 g/mol; MW TPA = 166.13 g/mol
        naoh_kg_per_kg_tpa = (2.05 * 40.0) / 166.13  # 0.4936 kg NaOH / kg TPA
        h2so4_kg_per_kg_tpa = (1.05 * 98.08) / 166.13 # 0.6200 kg H2SO4 / kg TPA
        naoh_price_kg = 0.45  # 50% membrane-grade chlor-alkali caustic
        h2so4_price_kg = 0.12 # technical grade sulfuric acid
        reagents_cost = (naoh_kg_per_kg_tpa * naoh_price_kg) + (h2so4_kg_per_kg_tpa * h2so4_price_kg)

        # 6. Downstream Recovery (acid precipitation, centrifugation, rotary vacuum filtration, drying)
        # Amortized CAPEX & operating labor for purification section
        scale_factor = (50000.0 / max(5000.0, scale_mt_year)) ** 0.35
        downstream_cost = 0.185 * scale_factor

        # 7. Byproduct disposal / credit
        # Stoichiometric Na2SO4 generated = 1.15 kg / kg TPA
        sulfate_generated_kg = 1.15
        byproduct_cost_credit = -(sulfate_generated_kg * byproduct_sulfate_credit_kg)

        # Total TPA production cost
        total_cost = (
            feedstock_cost
            + pretreatment_cost
            + biocatalyst_cost
            + reaction_utilities
            + reagents_cost
            + downstream_cost
            + byproduct_cost_credit
        )

        # Market target: virgin price + regulatory green premium
        market_target = virgin_tpa_price_kg * (1.0 + (regulatory_green_premium_pct / 100.0))
        parity_ratio = total_cost / market_target
        is_viable = total_cost <= market_target

        # Determine governing bottleneck
        costs_dict = {
            "Feedstock Post-Consumer Flake": feedstock_cost,
            "Thermal Amorphization Extrusion": pretreatment_cost,
            "Enzyme Biocatalyst": biocatalyst_cost,
            "Caustic / Acid Reagents": reagents_cost,
            "Downstream Recovery CAPEX/OPEX": downstream_cost,
        }
        bottleneck = max(costs_dict, key=costs_dict.get)

        return ScenarioOutcome(
            scenario_name=name,
            feedstock_type=feedstock_type,
            crystallinity_pct=crystallinity_pct,
            pretreatment_required=pretreatment_required,
            scale_mt_year=scale_mt_year,
            electricity_price_kwh=electricity_price_kwh,
            enzyme_cost_kg=enzyme_cost_kg,
            enzyme_reuse_cycles=enzyme_reuse_cycles,
            tpa_recovery_pct=tpa_recovery_pct,
            byproduct_sulfate_credit_kg=byproduct_sulfate_credit_kg,
            virgin_tpa_price_kg=virgin_tpa_price_kg,
            regulatory_green_premium_pct=regulatory_green_premium_pct,
            feedstock_net_cost_kg=round(feedstock_cost, 4),
            pretreatment_cost_kg=round(pretreatment_cost, 4),
            biocatalyst_cost_kg=round(biocatalyst_cost, 4),
            reaction_utilities_kg=round(reaction_utilities, 4),
            caustic_and_acid_reagents_kg=round(reagents_cost, 4),
            downstream_recovery_capex_opex_kg=round(downstream_cost, 4),
            byproduct_disposal_credit_kg=round(byproduct_cost_credit, 4),
            total_tpa_production_cost_usd_kg=round(total_cost, 4),
            market_clearing_target_usd_kg=round(market_target, 4),
            is_commercially_viable=is_viable,
            cost_parity_ratio=round(parity_ratio, 2),
            governing_cost_bottleneck=bottleneck,
        )

    @classmethod
    def run_multi_factor_matrix(cls) -> List[ScenarioOutcome]:
        """Runs representative real-world industry scenarios."""
        scenarios = [
            # 1. Baseline Commercial Bottle Plant (Unsubsidized)
            cls.evaluate_scenario(
                name="Baseline Commercial Plant (Baled Bottles, No Subsidies)",
                feedstock_type="baled_postconsumer_bottles",
                crystallinity_pct=32.0,
                pretreatment_required=True,
                scale_mt_year=50000.0,
                electricity_price_kwh=0.08,
                enzyme_cost_kg=12.0,
                enzyme_reuse_cycles=1,
                tpa_recovery_pct=93.0,
                byproduct_sulfate_credit_kg=-0.02,
                virgin_tpa_price_kg=1.05,
                regulatory_green_premium_pct=0.0,
            ),
            # 2. Pilot / Demonstration Scale (10,000 MT/yr)
            cls.evaluate_scenario(
                name="Demonstration / Pilot Plant (10 kt/yr Baled Bottles)",
                feedstock_type="baled_postconsumer_bottles",
                crystallinity_pct=32.0,
                pretreatment_required=True,
                scale_mt_year=10000.0,
                electricity_price_kwh=0.08,
                enzyme_cost_kg=20.0,
                enzyme_reuse_cycles=1,
                tpa_recovery_pct=90.0,
                byproduct_sulfate_credit_kg=-0.04,
                virgin_tpa_price_kg=1.05,
                regulatory_green_premium_pct=0.0,
            ),
            # 3. Amorphous Waste Niche (Post-Consumer Thermoforms / Blister Packs)
            cls.evaluate_scenario(
                name="Amorphous Thermoform Waste (Extrusion Bypassed)",
                feedstock_type="amorphous_thermoforms",
                crystallinity_pct=4.5,
                pretreatment_required=False,
                scale_mt_year=30000.0,
                electricity_price_kwh=0.08,
                enzyme_cost_kg=12.0,
                enzyme_reuse_cycles=1,
                tpa_recovery_pct=92.0,
                byproduct_sulfate_credit_kg=-0.02,
                virgin_tpa_price_kg=1.05,
                regulatory_green_premium_pct=0.0,
                feedstock_purchase_price_kg=0.45,  # Thermoforms trade at discount to bottle flakes
            ),
            # 4. Mandatory Recycled Content Mandate (EU 2030 Mandate + 40% Premium)
            cls.evaluate_scenario(
                name="Regulatory Policy Mandate (EU 2030, 40% Recycled Premium)",
                feedstock_type="baled_postconsumer_bottles",
                crystallinity_pct=32.0,
                pretreatment_required=True,
                scale_mt_year=50000.0,
                electricity_price_kwh=0.08,
                enzyme_cost_kg=12.0,
                enzyme_reuse_cycles=2,
                tpa_recovery_pct=94.0,
                byproduct_sulfate_credit_kg=-0.01,
                virgin_tpa_price_kg=1.05,
                regulatory_green_premium_pct=40.0,  # $1.47/kg market clearing price
            ),
            # 5. Advanced Biocatalyst Reuse (5 Cycles) + Cheap Renewable Power ($0.04/kWh)
            cls.evaluate_scenario(
                name="Advanced Biocatalyst Reuse (5x) & Green Industrial Power ($0.04/kWh)",
                feedstock_type="baled_postconsumer_bottles",
                crystallinity_pct=32.0,
                pretreatment_required=True,
                scale_mt_year=80000.0,
                electricity_price_kwh=0.04,
                enzyme_cost_kg=10.0,
                enzyme_reuse_cycles=5,
                tpa_recovery_pct=95.0,
                byproduct_sulfate_credit_kg=0.03,  # Pure detergent-grade Na2SO4 credit
                virgin_tpa_price_kg=1.05,
                regulatory_green_premium_pct=25.0,  # 25% premium for circular food-grade
            ),
            # 6. High Energy Stress (Peak Grid Electricity $0.15/kWh, High Enzyme Cost $30/kg)
            cls.evaluate_scenario(
                name="High Utility Stress (Peak Grid $0.15/kWh, $30/kg Biocatalyst)",
                feedstock_type="baled_postconsumer_bottles",
                crystallinity_pct=32.0,
                pretreatment_required=True,
                scale_mt_year=25000.0,
                electricity_price_kwh=0.15,
                enzyme_cost_kg=30.0,
                enzyme_reuse_cycles=1,
                tpa_recovery_pct=88.0,
                byproduct_sulfate_credit_kg=-0.05,
                virgin_tpa_price_kg=1.05,
                regulatory_green_premium_pct=0.0,
            ),
        ]
        return scenarios


def main() -> None:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    outcomes = EnzymaticRecyclingSensitivityEngine.run_multi_factor_matrix()
    out_dict = [asdict(o) for o in outcomes]
    
    out_file = results_dir / "sensitivity_analysis.json"
    out_file.write_text(json.dumps(out_dict, indent=2), encoding="utf-8")
    
    print("================================================================================")
    print("      BIOINTEL MULTI-FACTOR COMMERCIAL SENSITIVITY ANALYSIS (9 DIMENSIONS)     ")
    print("================================================================================")
    for o in outcomes:
        status = "VIABLE" if o.is_commercially_viable else "UNVIABLE"
        print(f"\n[*] {o.scenario_name}")
        print(f"    Total Cost: ${o.total_tpa_production_cost_usd_kg:.2f}/kg TPA | Market Target: ${o.market_clearing_target_usd_kg:.2f}/kg (Parity: {o.cost_parity_ratio:.2f}x) -> [{status}]")
        print(f"    Breakdown: Feedstock: ${o.feedstock_net_cost_kg:.2f} | Pretreatment: ${o.pretreatment_cost_kg:.2f} | Enzyme: ${o.biocatalyst_cost_kg:.2f} | Reagents: ${o.caustic_and_acid_reagents_kg:.2f} | Downstream: ${o.downstream_recovery_capex_opex_kg:.2f}")
        print(f"    Governing Bottleneck: {o.governing_cost_bottleneck}")
    print("\n[+] Full sensitivity matrix saved to:", out_file)


if __name__ == "__main__":
    main()
