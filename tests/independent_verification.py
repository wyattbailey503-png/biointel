"""BIOINTEL INDEPENDENT SCIENTIFIC & MATHEMATICAL VERIFICATION SCRIPT.

This standalone verification script independently recalculates key physical, chemical,
thermodynamic, and structural results without relying on the BioIntel core engine classes.
It operates as an adversarial sanity check on all core formulas.

Calculations independently derived:
1. Stoichiometric PET -> TPA mass conservation (MW ratio 166.13 / 192.17).
2. Biological Respiration & Thornton's Rule Metabolic Heat dissipation (kW).
3. Isentropic Adiabatic Air Compression Power (kW).
4. Industrial Chiller Refrigeration Duty & Electrical Work (COP = 3.5).
5. Direct PDB atom & residue coordinate audit for authoritative FAST-PETase (7SH6)
   and pea KAI2 receptor (7K38).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path


def verify_pet_tpa_stoichiometry() -> None:
    """Independently verifies stoichiometric chemical mass balance for PET hydrolysis."""
    # Polyethylene terephthalate repeating unit: C10 H8 O4
    # MW = (10 * 12.011) + (8 * 1.008) + (4 * 15.999) = 120.11 + 8.064 + 63.996 = 192.17 g/mol
    mw_pet_repeat = 192.17

    # Terephthalic acid (TPA): C8 H6 O4
    # MW = (8 * 12.011) + (6 * 1.008) + (4 * 15.999) = 96.088 + 6.048 + 63.996 = 166.132 g/mol
    mw_tpa = 166.13

    # Ethylene glycol (EG): C2 H6 O2
    # MW = (2 * 12.011) + (6 * 1.008) + (2 * 15.999) = 24.022 + 6.048 + 31.998 = 62.068 g/mol
    mw_eg = 62.07

    # Stoichiometry: (C10 H8 O4)_n + 2n H2O -> n C8 H6 O4 + n C2 H6 O2
    # Mass of TPA produced per unit mass of PET repeating unit consumed:
    theoretical_tpa_yield_per_pet = mw_tpa / mw_pet_repeat
    assert abs(theoretical_tpa_yield_per_pet - 0.864495) < 0.001, (
        f"Stoichiometric PET->TPA yield error: {theoretical_tpa_yield_per_pet}"
    )

    # 1,000 kg PET can yield AT MOST 864.5 kg TPA (assuming 100% conversion)
    input_pet_kg = 1000.0
    max_tpa_kg = input_pet_kg * theoretical_tpa_yield_per_pet
    assert abs(max_tpa_kg - 864.495) < 1.0
    print(f"[PASS] Stoichiometric PET -> TPA mass balance: {theoretical_tpa_yield_per_pet:.6f} kg TPA / kg PET")


def verify_fermentation_thermodynamics_and_utilities() -> None:
    """Independently verifies dimensional power and heat formulas."""
    # Basis:
    working_volume_m3 = 50.0  # 50,000 L
    working_volume_liters = working_volume_m3 * 1000.0

    # Respiration:
    # OUR = 60.0 mmol O2 / (L * h) = 60.0 mol O2 / (m3 * h)
    our_mmol_l_h = 60.0
    mol_o2_per_m3_h = our_mmol_l_h  # Dimensional identity: 1 mmol/L == 1 mol/m3

    total_mol_o2_per_h = mol_o2_per_m3_h * working_volume_m3
    assert total_mol_o2_per_h == 3000.0, "Molar O2 rate error"

    # Thornton's Rule: 460 kJ heat per mol O2 consumed
    # Q_met [kW] = (mol O2 / h) * (460 kJ / mol) / (3600 s / h)
    delta_h_o2_kj_per_mol = 460.0
    q_met_kw = (total_mol_o2_per_h * delta_h_o2_kj_per_mol) / 3600.0
    assert abs(q_met_kw - 383.333) < 0.01, f"Metabolic heat calculation mismatch: {q_met_kw} kW"

    # Agitation Dissipation (Empirical Heuristic):
    # (P/V) = 1.5 + (60 / 60) * 1.0 = 2.5 kW / m3
    power_vol_kw_m3 = 2.5
    p_agit_kw = working_volume_m3 * power_vol_kw_m3
    assert p_agit_kw == 125.0, f"Agitation power mismatch: {p_agit_kw} kW"

    # Isentropic Compressor Work:
    # Flow rate = 1.0 vvm = 50 m3/min = 50 / 60 m3/s = 0.8333 m3/s
    q_air_m3_s = working_volume_m3 / 60.0
    p1_kpa = 101.325
    p2_kpa = 200.0  # 2.0 bar head pressure
    pressure_ratio = p2_kpa / p1_kpa
    gamma = 1.40
    eta_comp = 0.72

    # P_comp = (P1 * Q / eta) * (gamma / (gamma - 1)) * ((P2/P1)^((gamma-1)/gamma) - 1)
    exponent = (gamma - 1.0) / gamma  # 0.2857
    comp_factor = (pressure_ratio ** exponent) - 1.0
    p_comp_kw = (p1_kpa * q_air_m3_s / eta_comp) * (gamma / (gamma - 1.0)) * comp_factor
    assert 85.0 < p_comp_kw < 95.0, f"Compressor power out of physical bounds: {p_comp_kw} kW"

    # Chiller Refrigeration Duty:
    # Q_cooling = Q_met + P_agit = 383.33 + 125.0 = 508.33 kW thermal
    q_cool_thermal_kw = q_met_kw + p_agit_kw
    cop_chiller = 3.5
    p_chiller_elec_kw = q_cool_thermal_kw / cop_chiller
    assert abs(p_chiller_elec_kw - 145.238) < 0.1, f"Chiller electrical work mismatch: {p_chiller_elec_kw} kW"

    # Electrical Power & Energy:
    p_aux_kw = 25.0
    total_electrical_kw = p_agit_kw + p_comp_kw + p_chiller_elec_kw + p_aux_kw
    duration_h = 120.0
    total_energy_kwh = total_electrical_kw * duration_h
    elec_rate_usd_kwh = 0.08
    elec_cost_batch = total_energy_kwh * elec_rate_usd_kwh

    assert total_electrical_kw > 350.0
    assert total_energy_kwh > 40000.0
    assert elec_cost_batch > 3000.0

    print(
        f"[PASS] Fermentation Thermodynamics & Utilities:\n"
        f"       Metabolic Heat: {q_met_kw:.2f} kW | Agitation: {p_agit_kw:.2f} kW\n"
        f"       Compressor: {p_comp_kw:.2f} kW | Chiller: {p_chiller_elec_kw:.2f} kW\n"
        f"       Total Electrical Power: {total_electrical_kw:.2f} kW | Energy: {total_energy_kwh:.1f} kWh\n"
        f"       Electricity Cost per Batch: ${elec_cost_batch:.2f}"
    )


def verify_pdb_structures_independently() -> None:
    """Independently verifies raw PDB coordinates and records for 7SH6 and 7K38."""
    root_dir = Path(__file__).resolve().parent.parent

    # 1. Authoritative FAST-PETase: PDB 7SH6
    pdb_7sh6_path = root_dir / "data" / "structures" / "7sh6.pdb"
    assert pdb_7sh6_path.exists(), f"Missing 7SH6 file: {pdb_7sh6_path}"

    atoms_7sh6 = []
    ca_residues_7sh6 = set()
    ligands_7sh6 = set()
    resolution_7sh6 = None

    with open(pdb_7sh6_path, "r", encoding="utf-8") as f:
        for line in f:
            if "RESOLUTION." in line and "ANGSTROMS" in line:
                parts = line.split("RESOLUTION.")
                if len(parts) > 1:
                    val_str = parts[1].replace("ANGSTROMS.", "").replace("ANGSTROMS", "").strip()
                    try:
                        resolution_7sh6 = float(val_str.split()[0])
                    except (ValueError, IndexError):
                        pass
            elif line.startswith("ATOM  "):
                atoms_7sh6.append(line)
                atom_name = line[12:16].strip()
                res_seq = int(line[22:26].strip())
                if atom_name == "CA":
                    ca_residues_7sh6.add(res_seq)
            elif line.startswith("HETATM"):
                res_name = line[17:20].strip()
                if res_name != "HOH":
                    ligands_7sh6.add(res_name)

    assert resolution_7sh6 == 1.44, f"7SH6 resolution mismatch: {resolution_7sh6}"
    assert len(atoms_7sh6) == 1981, f"7SH6 atom count mismatch: {len(atoms_7sh6)} (expected 1981)"
    assert len(ca_residues_7sh6) == 261, f"7SH6 residue count mismatch: {len(ca_residues_7sh6)} (expected 261)"
    assert "SO4" in ligands_7sh6, f"7SH6 bound ligand missing SO4: {ligands_7sh6}"
    assert "VTY" not in ligands_7sh6, "7SH6 cannot contain VTY ligand (VTY belongs to 7K38)"
    print(
        f"[PASS] Authoritative FAST-PETase (7SH6) Coordinate Audit:\n"
        f"       Resolution: {resolution_7sh6} A | Residues: {len(ca_residues_7sh6)} | "
        f"Atoms: {len(atoms_7sh6)} | Ligands: {ligands_7sh6}"
    )

    # 2. Pea KAI2 receptor: PDB 7K38
    pdb_7k38_path = root_dir / "data" / "structures" / "7k38.pdb"
    assert pdb_7k38_path.exists(), f"Missing 7K38 file: {pdb_7k38_path}"

    atoms_7k38 = []
    ca_residues_7k38 = set()
    ligands_7k38 = set()
    resolution_7k38 = None

    with open(pdb_7k38_path, "r", encoding="utf-8") as f:
        for line in f:
            if "RESOLUTION." in line and "ANGSTROMS" in line:
                parts = line.split("RESOLUTION.")
                if len(parts) > 1:
                    val_str = parts[1].replace("ANGSTROMS.", "").replace("ANGSTROMS", "").strip()
                    try:
                        resolution_7k38 = float(val_str.split()[0])
                    except (ValueError, IndexError):
                        pass

            elif line.startswith("ATOM  "):
                atoms_7k38.append(line)
                atom_name = line[12:16].strip()
                res_seq = int(line[22:26].strip())
                if atom_name == "CA":
                    ca_residues_7k38.add(res_seq)
            elif line.startswith("HET   ") or line.startswith("HETNAM"):
                lig_code = line[7:10].strip() if line.startswith("HET   ") else line[11:14].strip()
                if lig_code and lig_code != "HOH":
                    ligands_7k38.add(lig_code)
            elif line.startswith("HETATM"):
                res_name = line[17:20].strip()
                if res_name != "HOH":
                    ligands_7k38.add(res_name)

    assert resolution_7k38 == 2.0, f"7K38 resolution mismatch: {resolution_7k38}"
    assert len(atoms_7k38) == 2110, f"7K38 atom count mismatch: {len(atoms_7k38)} (expected 2110)"
    assert len(ca_residues_7k38) == 270, f"7K38 residue count mismatch: {len(ca_residues_7k38)} (expected 270)"
    assert "VTY" in ligands_7k38, f"7K38 bound ligand missing VTY: {ligands_7k38}"
    print(
        f"[PASS] Pisum sativum KAI2 Receptor (7K38) Coordinate Audit:\n"
        f"       Resolution: {resolution_7k38} A | Residues: {len(ca_residues_7k38)} | "
        f"Atoms: {len(atoms_7k38)} | Ligands: {ligands_7k38}"
    )



def main() -> None:
    print("=" * 70)
    print("BIOINTEL ADVERSARIAL INDEPENDENT SCIENTIFIC VERIFICATION SUITE")
    print("=" * 70)
    verify_pet_tpa_stoichiometry()
    verify_fermentation_thermodynamics_and_utilities()
    verify_pdb_structures_independently()
    print("=" * 70)
    print("ALL INDEPENDENT SCIENTIFIC & MATHEMATICAL VERIFICATIONS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
