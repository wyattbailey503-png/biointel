"""Macromolecular Structural Superposition and Active-Site Delta Tracking.

Computes C-alpha Root Mean Square Deviation (RMSD) between structural generations
(e.g. Wild-type 5XJH vs Austin mutant 6EQE vs FAST-PETase 7SH6)
and calculates Euclidean displacement of catalytic triad residues (Ser-Asp-His).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from biointel.structures.parser import PDBParser, ResidueRecord


@dataclass
class SuperpositionReport:
    structure_a_id: str
    structure_b_id: str
    common_ca_atoms_count: int
    centroid_distance_angstrom: float
    c_alpha_rmsd_angstrom: float
    catalytic_triad_displacements: Dict[str, float]
    structural_similarity_verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StructureSuperposition:
    """Superimposes 3D protein coordinate sets and quantifies structural shifts."""

    @classmethod
    def compare_structures(
        cls,
        parser_a: PDBParser,
        parser_b: PDBParser,
        catalytic_triad_indices: Optional[List[int]] = None,
    ) -> SuperpositionReport:
        """
        Aligns parser_a and parser_b C-alpha coordinates by common residue sequence numbers.
        
        Args:
            parser_a: First parsed structure.
            parser_b: Second parsed structure.
            catalytic_triad_indices: Residue sequence numbers of catalytic triad (e.g. [160, 206, 237]).
        """
        if catalytic_triad_indices is None:
            catalytic_triad_indices = [160, 206, 237]  # Standard PETase triad (Ser160, Asp206, His237)

        # Extract C-alpha coordinates keyed by residue sequence number
        ca_a: Dict[int, Tuple[float, float, float]] = {}
        for (chain, seq), res in parser_a.residues.items():
            if res.ca_atom is not None:
                ca_a[seq] = (res.ca_atom.x, res.ca_atom.y, res.ca_atom.z)

        ca_b: Dict[int, Tuple[float, float, float]] = {}
        for (chain, seq), res in parser_b.residues.items():
            if res.ca_atom is not None:
                ca_b[seq] = (res.ca_atom.x, res.ca_atom.y, res.ca_atom.z)

        # Find intersection of residue sequence numbers
        common_seqs = sorted(set(ca_a.keys()).intersection(set(ca_b.keys())))
        if len(common_seqs) < 10:
            raise ValueError(f"Insufficient overlapping C-alpha residues ({len(common_seqs)}) for structural alignment.")

        coords_a = [ca_a[s] for s in common_seqs]
        coords_b = [ca_b[s] for s in common_seqs]
        n = len(coords_a)

        # 1. Compute Centroids
        cx_a = sum(p[0] for p in coords_a) / n
        cy_a = sum(p[1] for p in coords_a) / n
        cz_a = sum(p[2] for p in coords_a) / n

        cx_b = sum(p[0] for p in coords_b) / n
        cy_b = sum(p[1] for p in coords_b) / n
        cz_b = sum(p[2] for p in coords_b) / n

        centroid_dist = math.sqrt((cx_a - cx_b) ** 2 + (cy_a - cy_b) ** 2 + (cz_a - cz_b) ** 2)

        # 2. Centroid-aligned coordinates
        shifted_a = [(p[0] - cx_a, p[1] - cy_a, p[2] - cz_a) for p in coords_a]
        shifted_b = [(p[0] - cx_b, p[1] - cy_b, p[2] - cz_b) for p in coords_b]

        # 3. Compute C-alpha RMSD over aligned centroids
        sq_dist_sum = 0.0
        for i in range(n):
            dx = shifted_a[i][0] - shifted_b[i][0]
            dy = shifted_a[i][1] - shifted_b[i][1]
            dz = shifted_a[i][2] - shifted_b[i][2]
            sq_dist_sum += (dx ** 2 + dy ** 2 + dz ** 2)

        rmsd = math.sqrt(sq_dist_sum / n)

        # 4. Measure Catalytic Triad Residue Shifts
        triad_displacements: Dict[str, float] = {}
        for res_idx in catalytic_triad_indices:
            if res_idx in ca_a and res_idx in ca_b:
                pt_a = (ca_a[res_idx][0] - cx_a, ca_a[res_idx][1] - cy_a, ca_a[res_idx][2] - cz_a)
                pt_b = (ca_b[res_idx][0] - cx_b, ca_b[res_idx][1] - cy_b, ca_b[res_idx][2] - cz_b)
                disp = math.sqrt((pt_a[0] - pt_b[0]) ** 2 + (pt_a[1] - pt_b[1]) ** 2 + (pt_a[2] - pt_b[2]) ** 2)
                triad_displacements[f"Residue_{res_idx}"] = round(disp, 3)
            else:
                triad_displacements[f"Residue_{res_idx}"] = -1.0  # Not aligned

        # Verdict
        if rmsd < 1.0:
            verdict = "HIGHLY_ISOMORPHIC: Nearly identical backbone scaffold; mutations preserve core tertiary fold."
        elif rmsd < 2.5:
            verdict = "MODERATE_HOMOLOGY: Preserved alpha/beta hydrolase fold with noticeable loop / active-site cleft shifts."
        else:
            verdict = "DISTINCT_CONFORMATION: Significant global domain divergence or different enzyme family."

        return SuperpositionReport(
            structure_a_id=getattr(parser_a, "header_id", None) or parser_a.pdb_file.stem.upper(),
            structure_b_id=getattr(parser_b, "header_id", None) or parser_b.pdb_file.stem.upper(),
            common_ca_atoms_count=n,
            centroid_distance_angstrom=round(centroid_dist, 3),
            c_alpha_rmsd_angstrom=round(rmsd, 3),
            catalytic_triad_displacements=triad_displacements,
            structural_similarity_verdict=verdict,
        )
