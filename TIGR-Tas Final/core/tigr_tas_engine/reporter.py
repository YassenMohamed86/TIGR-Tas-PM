"""
reporter.py — Structured output: CSV, JSON, and terminal summary.

Produces:
  - A flat CSV with all scoring components clearly separated
  - A nested JSON with full candidate detail
  - A terminal summary table (no external dependencies)
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from .comparison import CrisprSite
from .scoring import ScoredCandidate


# ---------------------------------------------------------------------------
# CSV fields (order preserved)
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "rank",
    "pair_id",
    "confidence_tier",
    "composite_score",
    # Spacer positions
    "spacer1_seq",
    "spacer1_start",
    "spacer1_strand",
    "spacer1_len",
    "spacer2_seq",
    "spacer2_start",
    "spacer2_strand",
    "spacer2_len",
    "gap_bp",
    # Component scores
    "score_gc",
    "score_length",
    "score_geometry",
    "score_thermodynamics",
    "score_complexity",
    "score_structure",
    "score_off_target",
    # Thermodynamics detail
    "sp1_dg_kcal_mol",
    "sp2_dg_kcal_mol",
    "sp1_tm_c",
    "sp2_tm_c",
    # Geometry detail
    "orientation",
    "phase_angle_deg",
    "phase_deviation_deg",
    # Complexity detail
    "sp1_gc_fraction",
    "sp2_gc_fraction",
    "sp1_entropy_bits",
    "sp2_entropy_bits",
    "sp1_self_comp",
    "sp2_self_comp",
    # Off-target detail
    "ot_min_penalty",
    "ot_risk_level",
    "ot_n_near_matches",
]


def _candidate_to_row(rank: int, c: ScoredCandidate) -> Dict[str, Any]:
    return {
        "rank":                  rank,
        "pair_id":               c.pair_id,
        "confidence_tier":       c.confidence_tier,
        "composite_score":       c.composite_score,
        "spacer1_seq":           c.spacer1_seq,
        "spacer1_start":         c.spacer1_start,
        "spacer1_strand":        c.spacer1_strand,
        "spacer1_len":           len(c.spacer1_seq),
        "spacer2_seq":           c.spacer2_seq,
        "spacer2_start":         c.spacer2_start,
        "spacer2_strand":        c.spacer2_strand,
        "spacer2_len":           len(c.spacer2_seq),
        "gap_bp":                c.gap_bp,
        "score_gc":              c.components.gc_content,
        "score_length":          c.components.length,
        "score_geometry":        c.components.geometry,
        "score_thermodynamics":  c.components.thermodynamics,
        "score_complexity":      c.components.complexity,
        "score_structure":       c.components.structure,
        "score_off_target":      c.components.off_target,
        "sp1_dg_kcal_mol":       c.sp1_dg,
        "sp2_dg_kcal_mol":       c.sp2_dg,
        "sp1_tm_c":              c.sp1_tm,
        "sp2_tm_c":              c.sp2_tm,
        "orientation":           c.orientation_label,
        "phase_angle_deg":       c.phase_angle,
        "phase_deviation_deg":   c.phase_deviation,
        "sp1_gc_fraction":       round(c.sp1_gc, 4),
        "sp2_gc_fraction":       round(c.sp2_gc, 4),
        "sp1_entropy_bits":      round(c.sp1_entropy, 4),
        "sp2_entropy_bits":      round(c.sp2_entropy, 4),
        "sp1_self_comp":         round(c.sp1_self_comp, 4),
        "sp2_self_comp":         round(c.sp2_self_comp, 4),
        "ot_min_penalty":        c.ot_min_penalty,
        "ot_risk_level":         c.ot_risk_level,
        "ot_n_near_matches":     c.ot_n_near_matches,
    }


def _crispr_to_dict(rank: int, site: CrisprSite) -> Dict[str, Any]:
    return {
        "rank":           rank,
        "protospacer":    site.protospacer,
        "pam":            site.pam,
        "pam_start":      site.pam_start,
        "strand":         site.strand,
        "spacer_start":   site.spacer_start,
        "spacer_end":     site.spacer_end,
        "gc_fraction":    round(site.gc_fraction, 4),
        "dg_kcal_mol":    site.dg,
        "entropy_bits":   round(site.entropy, 4),
        "gc_score":       site.gc_score,
        "thermo_score":   site.thermo_score,
        "complexity":     site.complexity,
        "structure":      site.structure,
        "pam_context":    site.pam_context,
        "composite":      site.composite,
    }


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_csv(
    candidates: List[ScoredCandidate],
    path: str,
) -> None:
    """Write ranked candidates to a CSV file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for rank, cand in enumerate(candidates, start=1):
            writer.writerow(_candidate_to_row(rank, cand))


def write_json(
    candidates: List[ScoredCandidate],
    crispr_sites: List[CrisprSite],
    comparison_summary: dict,
    metadata: dict,
    path: str,
) -> None:
    """Write the full analysis as a structured JSON file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    payload = {
        "metadata": metadata,
        "tigr_tas_candidates": [
            _candidate_to_row(rank, c)
            for rank, c in enumerate(candidates, start=1)
        ],
        "crispr_cas9_sites": [
            _crispr_to_dict(rank, s)
            for rank, s in enumerate(crispr_sites, start=1)
        ],
        "comparison": comparison_summary,
    }
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)


# ---------------------------------------------------------------------------
# Terminal summary
# ---------------------------------------------------------------------------

_TIER_COLOUR = {
    "A": "\033[92m",   # green
    "B": "\033[94m",   # blue
    "C": "\033[93m",   # yellow
    "D": "\033[91m",   # red
}
_RESET = "\033[0m"

_RISK_COLOUR = {
    "NONE":   "\033[92m",
    "LOW":    "\033[92m",
    "MEDIUM": "\033[93m",
    "HIGH":   "\033[91m",
}


def _bar(value: float, width: int = 20) -> str:
    filled = int(round(value * width))
    return "█" * filled + "░" * (width - filled)


def print_summary(
    candidates: List[ScoredCandidate],
    crispr_sites: List[CrisprSite],
    comparison: dict,
    metadata: dict,
    use_colour: bool = True,
) -> None:
    """Print a formatted summary to stdout."""
    use_colour = use_colour and sys.stdout.isatty()

    def c(text: str, colour: str) -> str:
        return f"{colour}{text}{_RESET}" if use_colour else text

    print()
    print("=" * 72)
    print("  TIGR-Tas Target Prediction Pipeline  —  Results Summary")
    print("=" * 72)
    print(f"  Sequence:   {metadata.get('sequence_name', 'unnamed')} "
          f"({metadata.get('sequence_length', '?')} bp)")
    print(f"  Run time:   {metadata.get('elapsed_s', '?'):.2f} s")
    print(f"  Candidates: {metadata.get('n_candidates', '?')} pairs scanned, "
          f"{metadata.get('n_ranked', '?')} ranked")
    print()

    print("  ┌─ TOP TIGR-Tas CANDIDATES ─────────────────────────────────────┐")
    for rank, cand in enumerate(candidates, start=1):
        tier_col = _TIER_COLOUR.get(cand.confidence_tier, "")
        risk_col = _RISK_COLOUR.get(cand.ot_risk_level, "")
        bar = _bar(cand.composite_score)
        tier_str = c(f"[{cand.confidence_tier}]", tier_col)
        risk_str = c(cand.ot_risk_level, risk_col)
        print(
            f"  #{rank:02d} {tier_str}  {bar}  {cand.composite_score:.4f}  "
            f"OT:{risk_str}  gap={cand.gap_bp}bp"
        )
        print(
            f"       S1: {cand.spacer1_seq[:20]}…  "
            f"pos={cand.spacer1_start} ({cand.spacer1_strand})"
        )
        print(
            f"       S2: {cand.spacer2_seq[:20]}…  "
            f"pos={cand.spacer2_start} ({cand.spacer2_strand})"
        )
        print(
            f"       GC={cand.components.gc_content:.2f}  "
            f"Thermo={cand.components.thermodynamics:.2f}  "
            f"Geom={cand.components.geometry:.2f}  "
            f"ΔG₁={cand.sp1_dg:.1f}  ΔG₂={cand.sp2_dg:.1f} kcal/mol"
        )
        if rank < len(candidates):
            print()
    print("  └────────────────────────────────────────────────────────────────┘")
    print()

    if crispr_sites:
        print("  ┌─ TOP CRISPR-Cas9 SITES ───────────────────────────────────────┐")
        for rank, site in enumerate(crispr_sites[:5], start=1):
            bar = _bar(site.composite)
            print(
                f"  #{rank:02d}  {bar}  {site.composite:.4f}  "
                f"PAM={site.pam}  GC={site.gc_fraction:.2f}  "
                f"ΔG={site.dg:.1f}  strand={site.strand}"
            )
            print(f"       {site.protospacer}  pos={site.spacer_start}")
        print("  └────────────────────────────────────────────────────────────────┘")
        print()
        print("  ┌─ COMPARISON ─────────────────────────────────────────────────┐")
        for k, v in comparison.items():
            print(f"  {k:35s}: {v}")
        print("  └────────────────────────────────────────────────────────────────┘")

    print()
