"""Ingestion adapters package for BioIntel."""
from biointel.ingestion.europe_pmc import EuropePMCAdapter
from biointel.ingestion.rcsb_pdb import RCSBPDBAdapter
from biointel.ingestion.uniprot import UniProtAdapter

__all__ = ["EuropePMCAdapter", "RCSBPDBAdapter", "UniProtAdapter"]
