"""Mechanistic Pathway and Process Diagram Renderer.

Generates high-contrast, publication-grade vector schematics showing
molecular binding, catalysis, cleaving, and functional cell transitions.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional
from biointel.mechanisms.model import MechanismOfActionProfile


class PathwayRenderer:
    """Renders typed biological mechanisms as flowchart and pathway diagrams."""

    def __init__(self, output_dir: Optional[str | Path] = None) -> None:
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent.parent.parent / "outputs" / "figures"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_mechanism_flow(self, profile: MechanismOfActionProfile, filename_stem: str = "mechanism_pathway") -> Dict[str, Path]:
        """Render a horizontal step-by-step molecular mechanism flow."""
        svg_path = self.output_dir / f"{filename_stem}.svg"
        png_path = self.output_dir / f"{filename_stem}.png"

        steps = profile.steps
        n = max(1, len(steps))

        box_w, box_h = 170, 75
        gap = 45
        padding = 40
        total_w = padding * 2 + n * box_w + (n - 1) * gap
        total_h = 240

        nodes_svg = []
        arrows_svg = []

        for i, step in enumerate(steps):
            x = padding + i * (box_w + gap)
            y = 85

            # Arrow to next step
            if i < n - 1:
                ax1 = x + box_w
                ay1 = y + box_h / 2
                ax2 = ax1 + gap
                ay2 = ay1
                rel_color = "#dc2626" if step.relation_type in ("cleaves", "edits", "inhibits") else "#2563eb"
                arrows_svg.append(f"""
                <line x1="{ax1}" y1="{ay1}" x2="{ax2}" y2="{ay2}" stroke="{rel_color}" stroke-width="2.5" marker-end="url(#arrowhead)"/>
                <text x="{ax1 + gap/2}" y="{ay1 - 8}" text-anchor="middle" font-family="sans-serif" font-size="10" font-weight="bold" fill="{rel_color}">{step.relation_type.upper()}</text>
                """)

            # Box
            border_color = "#3b82f6" if step.is_causal else "#6b7280"
            stroke_style = "" if step.is_causal else 'stroke-dasharray="4,4"'
            nodes_svg.append(f"""
            <g transform="translate({x}, {y})">
                <rect width="{box_w}" height="{box_h}" rx="6" fill="#f8fafc" stroke="{border_color}" stroke-width="2" {stroke_style}/>
                <text x="10" y="20" font-family="sans-serif" font-size="10" font-weight="bold" fill="#64748b">STEP {step.step_number}</text>
                <text x="10" y="38" font-family="sans-serif" font-size="12" font-weight="bold" fill="#0f172a">{step.source_entity}</text>
                <text x="10" y="54" font-family="sans-serif" font-size="10" fill="#334155">Target: {step.target_entity}</text>
                <text x="10" y="68" font-family="sans-serif" font-size="9" fill="#94a3b8">{step.cellular_compartment or 'cell'}</text>
            </g>
            """)

        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" width="{total_w}" height="{total_h}">
<defs>
    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" fill="#2563eb"/>
    </marker>
</defs>
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="{total_w/2}" y="32" text-anchor="middle" font-family="system-ui, sans-serif" font-size="15" font-weight="bold" fill="#0f172a">Mechanism of Action Flow: {profile.target_or_pathway}</text>
<text x="{total_w/2}" y="52" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#475569">{profile.molecular_mechanism} ({profile.cell_or_organism_context})</text>
{"".join(arrows_svg)}
{"".join(nodes_svg)}
<text x="{padding}" y="{total_h - 15}" font-family="sans-serif" font-size="10" fill="#64748b">Intended Outcome: {profile.intended_functional_outcome}</text>
</svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        # Try to render PNG with matplotlib
        try:
            os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_biointel"
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches

            fig, ax = plt.subplots(figsize=(max(8, n * 2.8), 3.5), dpi=300)
            ax.set_xlim(0, total_w)
            ax.set_ylim(0, total_h)
            ax.axis("off")

            # Simple proxy render
            for i, step in enumerate(steps):
                x = padding + i * (box_w + gap)
                y = 80
                rect = patches.FancyBboxPatch((x, y), box_w, box_h, boxstyle="round,pad=0.2", ec="#2563eb", fc="#f8fafc", lw=1.5)
                ax.add_patch(rect)
                ax.text(x + 10, y + box_h - 18, f"STEP {step.step_number}", fontsize=8, color="#64748b", weight="bold")
                ax.text(x + 10, y + box_h - 36, step.source_entity, fontsize=10, color="#0f172a", weight="bold")
                ax.text(x + 10, y + box_h - 52, f"-> {step.target_entity}", fontsize=9, color="#334155")
                ax.text(x + 10, y + 8, step.relation_type.upper(), fontsize=8, color="#dc2626" if "cleave" in step.relation_type or "edit" in step.relation_type else "#2563eb", weight="bold")

                if i < n - 1:
                    ax.annotate("", xy=(x + box_w + gap - 5, y + box_h/2), xytext=(x + box_w + 5, y + box_h/2),
                                arrowprops=dict(arrowstyle="->", color="#2563eb", lw=2))

            ax.text(total_w/2, total_h - 25, f"Mechanism of Action: {profile.target_or_pathway}", ha="center", fontsize=12, weight="bold", color="#0f172a")
            ax.text(total_w/2, total_h - 45, f"{profile.molecular_mechanism}", ha="center", fontsize=9, color="#475569")
            fig.savefig(png_path, bbox_inches="tight")
            plt.close(fig)
        except Exception:
            pass

        return {"svg": svg_path, "png": png_path if png_path.exists() else svg_path}
