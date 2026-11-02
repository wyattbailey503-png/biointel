"""PDB Coordinate and Macromolecular Structure Parser.

Parses experimental and predicted .pdb coordinate files to extract
chains, residue sequences, B-factors, secondary structures, ligands,
and pairwise C-alpha distance contact matrices.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AtomRecord:
    serial: int
    name: str
    alt_loc: str
    res_name: str
    chain_id: str
    res_seq: int
    x: float
    y: float
    z: float
    occupancy: float
    temp_factor: float
    element: str


@dataclass
class ResidueRecord:
    chain_id: str
    res_seq: int
    res_name: str
    ca_atom: Optional[AtomRecord] = None
    mean_b_factor: float = 0.0
    sec_struct: str = "C"  # H (Helix), E (Sheet), C (Coil/Loop)


class PDBParser:
    """Extracts structural coordinates and topology from PDB format files."""

    def __init__(self, pdb_file: str | Path) -> None:
        self.pdb_file = Path(pdb_file)
        if not self.pdb_file.exists():
            raise FileNotFoundError(f"PDB file not found: {self.pdb_file}")
        self.header_title: str = ""
        self.resolution: Optional[float] = None
        self.helices: List[Tuple[str, int, int]] = []  # (chain, start, end)
        self.sheets: List[Tuple[str, int, int]] = []   # (chain, start, end)
        self.atoms: List[AtomRecord] = []
        self.residues: Dict[Tuple[str, int], ResidueRecord] = {}
        self.ligand_names: List[str] = []
        self._parse()

    def _parse(self) -> None:
        lines = self.pdb_file.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines:
            rec_type = line[:6].strip()

            if rec_type == "TITLE":
                self.header_title += " " + line[10:80].strip()

            elif rec_type == "REMARK":
                # Check for resolution remark (REMARK   2)
                if line[7:10].strip() == "2" and "RESOLUTION." in line:
                    parts = line.split("RESOLUTION.")
                    if len(parts) > 1:
                        val_str = parts[1].replace("ANGSTROMS", "").strip()
                        try:
                            self.resolution = float(val_str.split()[0])
                        except (ValueError, IndexError):
                            pass

            elif rec_type == "HELIX":
                chain = line[19].strip()
                try:
                    start_res = int(line[21:25].strip())
                    end_res = int(line[33:37].strip())
                    self.helices.append((chain, start_res, end_res))
                except ValueError:
                    pass

            elif rec_type == "SHEET":
                chain = line[21].strip()
                try:
                    start_res = int(line[22:26].strip())
                    end_res = int(line[33:37].strip())
                    self.sheets.append((chain, start_res, end_res))
                except ValueError:
                    pass

            elif rec_type in ("ATOM", "HETATM"):
                try:
                    serial = int(line[6:11].strip())
                    name = line[12:16].strip()
                    alt_loc = line[16].strip()
                    res_name = line[17:20].strip()
                    chain_id = line[21].strip() or "A"
                    res_seq = int(line[22:26].strip())
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip())
                    z = float(line[46:54].strip())
                    occ = float(line[54:60].strip()) if len(line) >= 60 and line[54:60].strip() else 1.0
                    temp = float(line[60:66].strip()) if len(line) >= 66 and line[60:66].strip() else 0.0
                    elem = line[76:78].strip() if len(line) >= 78 else name[0]

                    atom = AtomRecord(
                        serial=serial, name=name, alt_loc=alt_loc, res_name=res_name,
                        chain_id=chain_id, res_seq=res_seq, x=x, y=y, z=z,
                        occupancy=occ, temp_factor=temp, element=elem
                    )

                    if rec_type == "ATOM":
                        self.atoms.append(atom)
                        key = (chain_id, res_seq)
                        if key not in self.residues:
                            self.residues[key] = ResidueRecord(chain_id=chain_id, res_seq=res_seq, res_name=res_name)
                        if name == "CA":
                            self.residues[key].ca_atom = atom
                            self.residues[key].mean_b_factor = temp
                    elif rec_type == "HETATM" and res_name not in ("HOH", "WAT"):
                        if res_name not in self.ligand_names:
                            self.ligand_names.append(res_name)
                except (ValueError, IndexError):
                    continue

        self._assign_secondary_structure()

    def _assign_secondary_structure(self) -> None:
        """Label residues with Helix (H) or Sheet (E)."""
        for chain, start, end in self.helices:
            for r in range(start, end + 1):
                key = (chain, r)
                if key in self.residues:
                    self.residues[key].sec_struct = "H"

        for chain, start, end in self.sheets:
            for r in range(start, end + 1):
                key = (chain, r)
                if key in self.residues:
                    self.residues[key].sec_struct = "E"

    def get_ca_distance_matrix(self, chain_id: str = "A") -> Tuple[List[int], List[List[float]]]:
        """Compute pairwise C-alpha Euclidean distances for residues in a chain."""
        chain_res = [res for (ch, r), res in sorted(self.residues.items()) if ch == chain_id and res.ca_atom is not None]
        res_nums = [r.res_seq for r in chain_res]
        n = len(chain_res)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            a1 = chain_res[i].ca_atom
            for j in range(i + 1, n):
                a2 = chain_res[j].ca_atom
                assert a1 is not None and a2 is not None
                dist = math.sqrt((a1.x - a2.x)**2 + (a1.y - a2.y)**2 + (a1.z - a2.z)**2)
                matrix[i][j] = dist
                matrix[j][i] = dist

        return res_nums, matrix

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Return structural quality and composition summary."""
        ca_count = sum(1 for r in self.residues.values() if r.ca_atom is not None)
        b_factors = [r.mean_b_factor for r in self.residues.values() if r.ca_atom is not None]
        avg_b = sum(b_factors) / len(b_factors) if b_factors else 0.0

        helix_count = sum(1 for r in self.residues.values() if r.sec_struct == "H")
        sheet_count = sum(1 for r in self.residues.values() if r.sec_struct == "E")
        coil_count = ca_count - (helix_count + sheet_count)

        return {
            "pdb_id": self.pdb_file.stem.upper(),
            "title": self.header_title.strip(),
            "resolution_angstrom": self.resolution,
            "total_atoms": len(self.atoms),
            "total_residues": ca_count,
            "chains": list(set(r.chain_id for r in self.residues.values())),
            "average_b_factor": round(avg_b, 2),
            "helix_residues": helix_count,
            "sheet_residues": sheet_count,
            "coil_residues": coil_count,
            "bound_ligands": self.ligand_names,
        }
