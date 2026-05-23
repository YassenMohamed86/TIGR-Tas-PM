"""
utils/exporter.py  —  Export AnalysisResult to CSV / JSON / text report.
"""

from __future__ import annotations
import csv, json, os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.analysis import AnalysisResult


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def export_csv(result: "AnalysisResult", directory: str) -> tuple[str, str]:
    """Write TIGR + CRISPR tables. Returns (tigr_path, crispr_path)."""
    os.makedirs(directory, exist_ok=True)
    name = result.request.gene_name.replace(" ", "_")

    tigr_path = os.path.join(directory, f"{name}_tigr_candidates.csv")
    crispr_path = os.path.join(directory, f"{name}_crispr_sites.csv")

    # TIGR CSV
    tigr_fields = ["rank","pair_id","spacer1","spacer2","gap","geometry",
                   "dg1","dg2","gc","thermo","complexity","structure",
                   "ot_risk","confidence","score","orientation","phase_angle"]
    with open(tigr_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=tigr_fields)
        w.writeheader()
        for c in result.tigr_candidates:
            w.writerow({k: getattr(c, k) for k in tigr_fields})

    # CRISPR CSV
    crispr_fields = ["rank","sequence","pam","position","strand","gc","dg","score","pam_ctx"]
    with open(crispr_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=crispr_fields)
        w.writeheader()
        for c in result.crispr_candidates:
            w.writerow({k: getattr(c, k) for k in crispr_fields})

    return tigr_path, crispr_path


def export_json(result: "AnalysisResult", path: str) -> str:
    """Write full structured JSON."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def _dc(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: _dc(v) for k, v in obj.__dict__.items()}
        if isinstance(obj, list):
            return [_dc(i) for i in obj]
        return obj

    payload = {
        "generated": _ts(),
        "pipeline_version": "3.0.0-gui",
        "request": _dc(result.request),
        "tigr_candidates": _dc(result.tigr_candidates),
        "crispr_candidates": _dc(result.crispr_candidates),
        "comparison": _dc(result.comparison),
        "metadata": {
            "sequence_length": result.sequence_length,
            "pairs_scanned": result.n_pairs_scanned,
            "elapsed_s": result.elapsed_s,
        },
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    return path


def export_text_report(result: "AnalysisResult", path: str) -> str:
    """Write a human-readable analysis report."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    req  = result.request
    comp = result.comparison

    lines = [
        "=" * 72,
        "  TIGR-Tas Analysis Report",
        f"  Generated : {_ts()}",
        f"  Gene/Name : {req.gene_name}",
        f"  Region    : {req.region_type}",
        "=" * 72,
        "",
        "SEQUENCE INFORMATION",
        f"  Length         : {result.sequence_length} bp",
        f"  GC fraction    : {comp.gc_fraction_seq:.3f}" if comp else "",
        f"  Region class   : {comp.region_class}" if comp else "",
        "",
        "ANALYSIS PARAMETERS",
        f"  Spacer length  : {req.spacer_min}–{req.spacer_max} bp",
        f"  Gap range      : {req.gap_min}–{req.gap_max} bp",
        f"  ΔG threshold   : {req.dg_threshold} kcal/mol",
        f"  Temperature    : {req.temperature_c} °C",
        f"  PAM (CRISPR)   : {req.pam_sequence}",
        "",
        "SYSTEM COMPARISON",
    ]
    if comp:
        lines += [
            f"  TIGR-Tas dp count      : {comp.tigr_dp_count}",
            f"  CRISPR PAM site count  : {comp.crispr_pam_count}",
            f"  Accessibility ratio    : {comp.accessibility_ratio}",
            f"  TIGR best score        : {comp.tigr_best_score}",
            f"  CRISPR best score      : {comp.crispr_best_score}",
            f"  Delta score            : {comp.delta_score:+.4f}",
            f"  Verdict                : {comp.verdict}",
        ]
    lines += [
        "",
        f"TOP TIGR-Tas CANDIDATES  ({len(result.tigr_candidates)} returned)",
        "-" * 72,
    ]
    for c in result.tigr_candidates:
        lines.append(
            f"  #{c.rank:02d} [{c.confidence}]  Score={c.score:.4f}  "
            f"OT={c.ot_risk}  Gap={c.gap}bp"
        )
        lines.append(f"       S1: {c.spacer1}  ΔG={c.dg1:.1f}")
        lines.append(f"       S2: {c.spacer2}  ΔG={c.dg2:.1f}")
        lines.append(
            f"       GC={c.gc:.2f}  Thermo={c.thermo:.2f}  "
            f"Geom={c.geometry:.2f}  Orient={c.orientation}"
        )
        lines.append("")

    lines += [
        f"TOP CRISPR-Cas9 SITES  ({len(result.crispr_candidates)} returned)",
        "-" * 72,
    ]
    for c in result.crispr_candidates:
        lines.append(
            f"  #{c.rank:02d}  {c.sequence}  PAM={c.pam}  "
            f"pos={c.position}  strand={c.strand}  "
            f"GC={c.gc:.2f}  ΔG={c.dg:.1f}  Score={c.score:.4f}"
        )

    lines += ["", f"  Analysis completed in {result.elapsed_s:.2f} s", "=" * 72]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path
