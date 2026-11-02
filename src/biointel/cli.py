"""BioIntel Unified Command-Line Interface.

Command runner for discovery, molecular structure analysis, competitive comparisons,
techno-economic unit modeling, institutional memos, and data archiving.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from biointel.changes.detector import ChangeDetector
from biointel.commercialization.framework import CommercializationEvaluator
from biointel.comparison.matrix import TechnologyComparator
from biointel.discovery.crawler import DiscoveryCrawler
from biointel.economics.fermentation import FermentationInputs, TechnoEconomicFermentationModel
from biointel.mechanisms.model import MechanismOfActionProfile, MechanismStep
from biointel.mechanisms.pathway import PathwayRenderer
from biointel.reports.export import ResearchExporter
from biointel.reports.memo_generator import DiligenceMemoGenerator
from biointel.scheduler.runner import BioIntelScheduler
from biointel.storage.database import Database
from biointel.structures.parser import PDBParser
from biointel.structures.visualizer import StructureVisualizer


def get_db() -> Database:
    db_path = Path.cwd() / "biointel.db"
    return Database(db_path)


def cmd_discover(args: argparse.Namespace) -> None:
    db = get_db()
    crawler = DiscoveryCrawler(db)
    mode = "live" if args.live else "offline"
    print(f"[*] Running BioIntel continuous discovery pipeline in '{mode.upper()}' mode...")
    report = crawler.run_discovery_pipeline(mode=mode)
    print(report.summary_markdown)


def cmd_compare(args: argparse.Namespace) -> None:
    db = get_db()
    comparator = TechnologyComparator(db)
    print(f"[*] Comparing technologies: '{args.tech_a}' vs '{args.tech_b}'...")
    comp = comparator.generate_gene_editing_comparison(args.tech_a, args.tech_b)

    print("\n=== COMPETITIVE COMPARISON MATRIX ===")
    print(f"Domain: {comp.comparison_domain}")
    print(f"Objective: {comp.shared_target_or_objective}\n")

    for dim in comp.comparison_matrix["dimensions"]:
        compat_str = "COMPATIBLE" if dim["compatible"] else "CONDITION MISMATCH"
        print(f"--- [{dim['metric']}] ({compat_str}) ---")
        print(f"  Technology A: {dim['technology_a']} (Context: {dim['context_a']})")
        print(f"  Technology B: {dim['technology_b']} (Context: {dim['context_b']})")
        if dim.get("warning"):
            print(f"  ! WARNING: {dim['warning']}")
        print()

    print("=== STRATEGIC TAKEAWAY ===")
    print(comp.strategic_takeaway)


def cmd_teo_model(args: argparse.Namespace) -> None:
    inputs = FermentationInputs(
        titer_g_per_l=args.titer,
        duration_hours=args.duration,
        working_volume_liters=args.volume,
        recovery_efficiency=args.recovery,
        feedstock_price_usd_per_kg=args.feedstock_price,
    )
    outputs = TechnoEconomicFermentationModel.calculate(inputs)

    print("\n=== PRECISION FERMENTATION TECHNO-ECONOMIC MASS BALANCE ===")
    print(f"Titer: {inputs.titer_g_per_l} g/L | Duration: {inputs.duration_hours} h | Recovery: {int(inputs.recovery_efficiency*100)}%")
    print(f"Recovered Mass per Batch: {outputs.product_mass_per_batch_kg:,.1f} kg")
    print(f"Annual Production Capacity: {outputs.annual_production_volume_mt:,.2f} Metric Tons / year")
    print(f"Volumetric Productivity: {outputs.volumetric_productivity_g_l_h:.3f} g/L/h")
    print("\n=== COST STACK DECOMPOSITION ($/kg product) ===")
    print(f"  Feedstock (Dextrose):   ${outputs.feedstock_cost_per_kg:.2f}/kg ({outputs.cost_stack_breakdown_pct['Feedstock']}%)")
    print(f"  Utilities (Power/Steam):${outputs.utilities_cost_per_kg:.2f}/kg ({outputs.cost_stack_breakdown_pct['Utilities']}%)")
    print(f"  Downstream DSP:         ${outputs.dsp_cost_per_kg:.2f}/kg ({outputs.cost_stack_breakdown_pct['Downstream_DSP']}%)")
    print(f"  Labor & Plant Overhead: ${outputs.labor_overhead_cost_per_kg:.2f}/kg ({outputs.cost_stack_breakdown_pct['Labor_and_Overhead']}%)")
    print(f"  CAPEX Depreciation:     ${outputs.capex_depreciation_per_kg:.2f}/kg ({outputs.cost_stack_breakdown_pct['CAPEX_Depreciation']}%)")
    print(f"--------------------------------------------------")
    print(f"TOTAL PRODUCTION COST:   ${outputs.total_cost_per_kg:.2f} / kg")
    print(f"Break-even Price (20% margin): ${outputs.break_even_price_20pct_margin:.2f} / kg\n")

    if args.sensitivity:
        print("[*] Running 2D sensitivity matrix across titers and substrate prices...")
        sens = TechnoEconomicFermentationModel.sensitivity_analysis(inputs)
        figures = TechnoEconomicFermentationModel.render_sensitivity_chart(sens)
        print(f"[+] Sensitivity chart saved to: {figures['svg']}")


def cmd_memo(args: argparse.Namespace) -> None:
    db = get_db()
    gen = DiligenceMemoGenerator(db)
    print(f"[*] Generating institutional diligence memo for '{args.technology}'...")
    memo = gen.generate_gene_editing_memo(args.technology, save_file=True)
    out_file = Path("outputs/research") / f"memo_{args.technology}.md"
    print(f"[+] Successfully generated diligence memo: {out_file} ({out_file.stat().st_size} bytes)")


def cmd_structure(args: argparse.Namespace) -> None:
    pdb_path = Path("data/structures") / f"{args.pdb_id.lower()}.pdb"
    if not pdb_path.exists():
        print(f"[!] PDB file not found at {pdb_path}. Running discovery first...")
        db = get_db()
        DiscoveryCrawler(db).run_discovery_pipeline(mode="offline")

    print(f"[*] Parsing macromolecular structure: {pdb_path}...")
    parser = PDBParser(pdb_path)
    metrics = parser.get_summary_metrics()

    print("\n=== MACROMOLECULAR STRUCTURE METRICS ===")
    print(f"PDB ID: {metrics['pdb_id']}")
    print(f"Title: {metrics['title']}")
    print(f"Resolution: {metrics['resolution_angstrom']} Å")
    print(f"Total C-alpha Residues: {metrics['total_residues']}")
    print(f"Mean B-factor: {metrics['average_b_factor']} Å²")
    print(f"Secondary Structure: {metrics['helix_residues']} Helices, {metrics['sheet_residues']} Sheets, {metrics['coil_residues']} Coils")
    print(f"Bound Ligands: {', '.join(metrics['bound_ligands']) or 'None'}")

    vis = StructureVisualizer()
    b_figs = vis.render_b_factor_profile(parser, f"{args.pdb_id.lower()}_b_factors")
    c_figs = vis.render_contact_map(parser, f"{args.pdb_id.lower()}_contacts")
    print(f"[+] B-factor profile figure: {b_figs['svg']}")
    print(f"[+] C-alpha contact map figure: {c_figs['svg']}")


def cmd_pathway(args: argparse.Namespace) -> None:
    print(f"[*] Rendering mechanism-of-action pathway diagram for '{args.technology}'...")
    profile = MechanismOfActionProfile(
        technology_id=args.technology,
        biological_substrate="Genomic DNA Target Locus",
        target_or_pathway="Search-and-Replace Prime Editing Pathway",
        molecular_mechanism="Cas9(H840A) Nickase + M-MLV Reverse Transcriptase fusion directed by pegRNA",
        cell_or_organism_context="Human Eukaryotic Nucleus",
        intended_functional_outcome="Single-base transversion and micro-insertion without double-strand breaks",
        steps=[
            MechanismStep(1, "pegRNA:Cas9 Fusion", "binds", "Target PAM & DNA Strand", is_causal=True),
            MechanismStep(2, "Cas9 Nickase", "cleaves", "Non-target DNA strand", is_causal=True),
            MechanismStep(3, "Primer Binding Site", "binds", "Liberated 3' DNA Flap", is_causal=True),
            MechanismStep(4, "M-MLV RT", "edits", "Target DNA via RNA-templated extension", is_causal=True),
            MechanismStep(5, "DNA Repair Machinery", "regulates", "Flap resolution and mismatch repair", is_causal=True),
        ],
    )
    renderer = PathwayRenderer()
    figs = renderer.render_mechanism_flow(profile, "prime_editing_pathway")
    print(f"[+] Pathway flowchart rendered: {figs['svg']}")


def cmd_change_feed(args: argparse.Namespace) -> None:
    db = get_db()
    detector = ChangeDetector(db)
    # Ensure change card exists for demonstration
    detector.create_change_card(
        change_id="change_prime_editing_bipe_2022",
        technology_id="prime_editing",
        change_type="methodological_breakthrough",
        title="Bi-Directional Priming (Bi-PE) Enhances Prime Editing Efficiency 2.5-fold",
        previous_state="Canonical PE3 achieved 15% – 28% precise editing at difficult genomic targets with substantial byproduct indels.",
        new_state="Bi-PE employs dual-opposing pegRNAs to achieve 45% – 60% editing efficiency with lower indel ratios.",
        primary_source_id="doi:10.1093/nar/gkac506",
        scientific_significance="Dual-flap homology prevents premature flap resection and stimulates preferential double-flap resolution.",
        commercial_implication="Expands therapeutic viability to low-efficiency genomic loci previously considered untreatable by standard prime editors.",
        diligence_questions=[
            "Does dual-pegRNA transfection increase off-target nicking rates at secondary homologous loci?",
            "What is the viral vector or LNP packaging efficiency when co-delivering two long pegRNAs?",
        ],
    )
    changes = detector.get_timeline_for_technology("prime_editing")
    print("\n=== SCIENTIFIC CHANGE DETECTION FEED ===")
    for c in changes:
        print(f"[{c['change_type'].upper()}] {c['title']}")
        print(f"  Previous State: {c['previous_state']}")
        print(f"  New Evidence State: {c['new_state']}")
        print(f"  Scientific Significance: {c['scientific_significance']}")
        print(f"  Commercial Implication: {c['commercial_implication']}")
        if c.get("diligence_questions"):
            print(f"  Diligence Questions: {c['diligence_questions']}")
        print()


def cmd_export(args: argparse.Namespace) -> None:
    db = get_db()
    exporter = ResearchExporter(db)
    print(f"[*] Exporting complete BioIntel archive (version: {args.version})...")
    path = exporter.export_full_archive(args.version)
    print(f"[+] Exported structured JSON archive to: {path} ({path.stat().st_size:,.0f} bytes)")


def cmd_run_all(args: argparse.Namespace) -> None:
    """Executes the full vertical slice end-to-end and outputs all deliverables."""
    print("=================================================================")
    print("   BIOINTEL: AUTONOMOUS BIOTECHNOLOGY INTELLIGENCE ENGINE")
    print("   Executing Complete End-to-End Scientific & Commercial Slice")
    print("=================================================================\n")

    # Step 1: Discovery & Ingestion
    cmd_discover(argparse.Namespace(live=False))

    # Step 2: Molecular Structure Parser & Visualizer
    print("\n-----------------------------------------------------------------")
    cmd_structure(argparse.Namespace(pdb_id="7K38"))

    # Step 3: Technology Comparison Matrix
    print("\n-----------------------------------------------------------------")
    cmd_compare(argparse.Namespace(tech_a="crispr_cas9_nuclease", tech_b="prime_editing"))

    # Step 4: Mechanism of Action Flowchart
    print("\n-----------------------------------------------------------------")
    cmd_pathway(argparse.Namespace(technology="prime_editing"))

    # Step 5: Techno-Economic Fermentation Model & Sensitivity
    print("\n-----------------------------------------------------------------")
    cmd_teo_model(argparse.Namespace(titer=45.0, duration=120.0, volume=50000.0, recovery=0.85, feedstock_price=0.35, sensitivity=True))

    # Step 6: Scientific Change Detection Feed
    print("\n-----------------------------------------------------------------")
    cmd_change_feed(argparse.Namespace())

    # Step 7: Commercialization 8-Dimension Assessment
    print("\n-----------------------------------------------------------------")
    print("[*] Running 8-dimension science-to-commercialization assessment...")
    assessment = CommercializationEvaluator.evaluate_precision_fermentation()
    print(f"Readiness: {assessment.overall_commercial_readiness}")
    print(f"Strategic Recommendation: {assessment.strategic_recommendation}")

    # Step 8: Institutional Investment Diligence Memorandum
    print("\n-----------------------------------------------------------------")
    cmd_memo(argparse.Namespace(technology="prime_editing"))

    # Step 9: Structured JSON Versioned Export
    print("\n-----------------------------------------------------------------")
    cmd_export(argparse.Namespace(version="v1.0.0"))

    # Step 10: Scheduler & launchd configuration
    print("\n-----------------------------------------------------------------")
    scheduler = BioIntelScheduler(get_db())
    plist = scheduler.generate_launchd_plist()
    print(f"[+] Generated macOS launchd plist at: {plist}")
    digest = scheduler.run_weekly_digest()
    print(f"[+] Weekly innovation digest written to: {digest}")

    print("\n=================================================================")
    print("   BIOINTEL VERTICAL SLICE COMPLETED SUCCESSFULLY")
    print("=================================================================\n")


def cmd_study(args: argparse.Namespace) -> None:
    from biointel.reports.study_runner import StudyPackageRunner
    runner = StudyPackageRunner()

    if args.action == "list":
        studies = runner.list_studies()
        print("\n=== BIOINTEL REPRODUCIBLE RESEARCH STUDIES ===")
        for s in studies:
            print(f"  - {s}")
        print()
    elif args.action in ["verify", "run"]:
        if not args.study_id:
            print("Error: Specify a study_id (e.g. study_01_petase_plastics_bioprocess)")
            sys.exit(1)
        print(f"[*] Executing verification for study: '{args.study_id}'...")
        res = runner.verify_study(args.study_id)
        if not res["verified"]:
            print(f"[!] FAILED: {res.get('error')}")
            sys.exit(1)
        print(f"[+] Status: {res['status']}")
        print(f"[+] Primary Sources Verified: {res['num_primary_sources']}")
        print(f"[+] Figures Generated: {', '.join(res['figures_generated'])}")
        print(f"[+] Recommendation / Verdict: {res['calculations_summary']}")
        print(f"[+] Verification completed successfully.")



def main() -> None:
    parser = argparse.ArgumentParser(
        prog="biointel",
        description="BioIntel: Autonomous Biotechnology Intelligence & Commercialization Research Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # discover
    p_disc = subparsers.add_parser("discover", help="Run automated continuous discovery pipeline")
    p_disc.add_argument("--live", action="store_true", help="Execute live network calls instead of cached fixtures")

    # compare
    p_comp = subparsers.add_parser("compare", help="Compare two competing biotechnology platforms")
    p_comp.add_argument("tech_a", nargs="?", default="crispr_cas9_nuclease", help="First technology identifier")
    p_comp.add_argument("tech_b", nargs="?", default="prime_editing", help="Second technology identifier")

    # teo-model
    p_teo = subparsers.add_parser("teo-model", help="Run precision fermentation techno-economic model")
    p_teo.add_argument("--titer", type=float, default=45.0, help="Titer in g/L")
    p_teo.add_argument("--duration", type=float, default=120.0, help="Fermentation duration in hours")
    p_teo.add_argument("--volume", type=float, default=50000.0, help="Working volume in liters")
    p_teo.add_argument("--recovery", type=float, default=0.85, help="DSP recovery fraction (0-1)")
    p_teo.add_argument("--feedstock-price", type=float, default=0.35, help="Substrate price in $/kg")
    p_teo.add_argument("--sensitivity", action="store_true", help="Compute 2D sensitivity matrix and chart")

    # memo
    p_memo = subparsers.add_parser("memo", help="Generate institutional diligence memorandum")
    p_memo.add_argument("technology", nargs="?", default="prime_editing", help="Technology identifier")

    # structure
    p_struct = subparsers.add_parser("structure", help="Parse macromolecular structure and generate figures")
    p_struct.add_argument("pdb_id", nargs="?", default="7K38", help="PDB 4-letter identifier")

    # pathway
    p_path = subparsers.add_parser("pathway", help="Render mechanism-of-action pathway diagram")
    p_path.add_argument("technology", nargs="?", default="prime_editing", help="Technology identifier")

    # change-feed
    subparsers.add_parser("change-feed", help="View scientific and commercial change feed")

    # export
    p_exp = subparsers.add_parser("export", help="Export versioned JSON archive")
    p_exp.add_argument("--version", default="v1.0.0", help="Version tag for exported package")

    # run-all
    # study
    p_study = subparsers.add_parser("study", help="Manage and verify reproducible research study packages")
    p_study.add_argument("action", choices=["list", "verify", "run"], help="Action to execute")
    p_study.add_argument("study_id", nargs="?", default="", help="Study identifier (e.g. study_01_petase_plastics_bioprocess)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "discover": cmd_discover,
        "compare": cmd_compare,
        "teo-model": cmd_teo_model,
        "memo": cmd_memo,
        "structure": cmd_structure,
        "pathway": cmd_pathway,
        "change-feed": cmd_change_feed,
        "export": cmd_export,
        "run-all": cmd_run_all,
        "study": cmd_study,
    }

    cmd_fn = cmds.get(args.command)
    if cmd_fn:
        cmd_fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

