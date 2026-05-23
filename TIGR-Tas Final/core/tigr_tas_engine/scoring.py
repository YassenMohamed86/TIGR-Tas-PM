"""
scoring.py — Multi-criteria deterministic scoring and candidate ranking.

Each SpacerPair receives a ScoredCandidate containing:
  - Individual component scores (GC, length, geometry, thermodynamics,
    complexity, structure, off-target)
  - Weighted composite score
  - Confidence tier (A / B / C / D)
  - Reject flag with reason

All scoring is deterministic: same input → same output every time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .complexity import (
    entropy_score,
    gc_score,
    structure_score,
    passes_complexity_filter,
    gc_fraction,
    shannon_entropy,
    self_complementarity_score,
)
from .constants import (
    DELTA_G_HARD_CUTOFF,
    DELTA_G_OPTIMAL_MAX,
    SPACER_OPTIMAL_MAX,
    SPACER_OPTIMAL_MIN,
    PipelineConfig,
)
from .geometry import composite_geometry_score
from .offtarget import cross_compare_spacers
from .sequence import SpacerPair
from .thermodynamics import thermodynamic_score, delta_g_rna_dna, melting_temperature


# ---------------------------------------------------------------------------
# Score data structures
# ---------------------------------------------------------------------------

@dataclass
class ComponentScores:
    """Individual component scores, each normalised to [0, 1]."""
    gc_content:     float = 0.0
    length:         float = 0.0
    geometry:       float = 0.0
    thermodynamics: float = 0.0
    complexity:     float = 0.0
    structure:      float = 0.0
    off_target:     float = 0.0


@dataclass
class ScoredCandidate:
    """A fully scored SpacerPair candidate ready for ranking."""
    pair:               SpacerPair
    components:         ComponentScores = field(default_factory=ComponentScores)
    composite_score:    float = 0.0
    confidence_tier:    str = "D"

    # Annotation fields
    pair_id:            str = ""
    spacer1_seq:        str = ""
    spacer2_seq:        str = ""
    spacer1_start:      int = 0
    spacer2_start:      int = 0
    spacer1_strand:     str = "+"
    spacer2_strand:     str = "+"
    gap_bp:             int = 0

    # Thermodynamics
    sp1_dg:             float = 0.0
    sp2_dg:             float = 0.0
    sp1_tm:             float = 0.0
    sp2_tm:             float = 0.0

    # Geometry detail
    orientation_label:  str = ""
    phase_angle:        float = 0.0
    phase_deviation:    float = 0.0

    # Complexity detail
    sp1_gc:             float = 0.0
    sp2_gc:             float = 0.0
    sp1_entropy:        float = 0.0
    sp2_entropy:        float = 0.0
    sp1_self_comp:      float = 0.0
    sp2_self_comp:      float = 0.0

    # Off-target
    ot_min_penalty:     float = 0.0
    ot_risk_level:      str = "NONE"
    ot_n_near_matches:  int = 0

    # Filter
    rejected:           bool = False
    reject_reason:      str = ""


# ---------------------------------------------------------------------------
# Individual scoring functions
# ---------------------------------------------------------------------------

def _length_score(sp_len: int) -> float:
    """Score spacer length: optimal range [20, 23], accept [18, 25]."""
    if SPACER_OPTIMAL_MIN <= sp_len <= SPACER_OPTIMAL_MAX:
        return 1.0
    dist = min(abs(sp_len - SPACER_OPTIMAL_MIN), abs(sp_len - SPACER_OPTIMAL_MAX))
    return round(max(1.0 - dist * 0.15, 0.2), 4)


def _pair_length_score(sp1_len: int, sp2_len: int) -> float:
    """Average length score across both spacers."""
    return round(((_length_score(sp1_len) + _length_score(sp2_len)) / 2), 4)


def _pair_gc_score(sp1: str, sp2: str) -> float:
    """Worst-case GC score across the pair (bottleneck logic)."""
    return round(min(gc_score(sp1), gc_score(sp2)), 4)


def _pair_thermo_score(sp1: str, sp2: str, temp_k: float) -> Tuple[float, float, float, float, float]:
    """
    Returns (composite_score, sp1_dg, sp2_dg, sp1_tm, sp2_tm).
    Uses geometric mean to penalise pairs where one spacer is weak.
    """
    s1 = thermodynamic_score(sp1, temp_k)
    s2 = thermodynamic_score(sp2, temp_k)
    dg1 = delta_g_rna_dna(sp1, temp_k)
    dg2 = delta_g_rna_dna(sp2, temp_k)
    tm1 = melting_temperature(sp1)
    tm2 = melting_temperature(sp2)
    # Geometric mean: both spacers must bind well
    combined = round(math.sqrt(s1 * s2), 4)
    return combined, dg1, dg2, tm1, tm2


def _pair_complexity_score(sp1: str, sp2: str) -> Tuple[float, float, float]:
    """Returns (score, sp1_entropy, sp2_entropy)."""
    e1 = entropy_score(sp1)
    e2 = entropy_score(sp2)
    combined = round(min(e1, e2), 4)   # bottleneck
    return combined, shannon_entropy(sp1), shannon_entropy(sp2)


def _pair_structure_score(sp1: str, sp2: str) -> Tuple[float, float, float]:
    """Returns (score, sp1_self_comp, sp2_self_comp)."""
    sc1 = self_complementarity_score(sp1)
    sc2 = self_complementarity_score(sp2)
    s1  = structure_score(sp1)
    s2  = structure_score(sp2)
    combined = round(min(s1, s2), 4)
    return combined, sc1, sc2


# ---------------------------------------------------------------------------
# Composite scoring
# ---------------------------------------------------------------------------

def _weighted_composite(components: ComponentScores, weights: Dict[str, float]) -> float:
    """Compute the weighted sum of component scores."""
    total = (
        components.gc_content     * weights.get("gc_content", 0.15) +
        components.length         * weights.get("length", 0.10) +
        components.geometry       * weights.get("geometry", 0.20) +
        components.thermodynamics * weights.get("thermodynamics", 0.25) +
        components.complexity     * weights.get("complexity", 0.10) +
        components.structure      * weights.get("structure", 0.10) +
        components.off_target     * weights.get("off_target", 0.10)
    )
    return round(min(max(total, 0.0), 1.0), 4)


def _confidence_tier(score: float, rejected: bool) -> str:
    """
    Assign a confidence tier:
      A ≥ 0.75 — high confidence, recommend for validation
      B ≥ 0.55 — moderate confidence
      C ≥ 0.35 — low confidence, use with caution
      D  < 0.35 or rejected — not recommended
    """
    if rejected:
        return "D"
    if score >= 0.75:
        return "A"
    if score >= 0.55:
        return "B"
    if score >= 0.35:
        return "C"
    return "D"


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_candidate(
    pair: SpacerPair,
    reference_seq: str,
    all_spacer_seqs: List[str],
    cfg: PipelineConfig,
) -> ScoredCandidate:
    """
    Score a single SpacerPair and return a ScoredCandidate.

    Parameters
    ----------
    pair           : SpacerPair to score
    reference_seq  : the full input DNA sequence (for off-target scanning)
    all_spacer_seqs: sequences of all other detected spacers
    cfg            : PipelineConfig
    """
    sp1 = pair.spacer1
    sp2 = pair.spacer2

    cand = ScoredCandidate(
        pair=pair,
        pair_id=pair.pair_id,
        spacer1_seq=sp1.sequence,
        spacer2_seq=sp2.sequence,
        spacer1_start=sp1.start,
        spacer2_start=sp2.start,
        spacer1_strand=sp1.strand,
        spacer2_strand=sp2.strand,
        gap_bp=pair.gap,
    )

    # --- Hard rejection checks ---
    for sp_seq, label in [(sp1.sequence, "Spacer1"), (sp2.sequence, "Spacer2")]:
        ok, reason = passes_complexity_filter(sp_seq)
        if not ok:
            cand.rejected = True
            cand.reject_reason = f"{label}: {reason}"
            cand.confidence_tier = "D"
            return cand

    # --- Component scores ---
    comp = ComponentScores()

    # GC
    comp.gc_content = _pair_gc_score(sp1.sequence, sp2.sequence)
    cand.sp1_gc = gc_fraction(sp1.sequence)
    cand.sp2_gc = gc_fraction(sp2.sequence)

    # Length
    comp.length = _pair_length_score(sp1.length, sp2.length)

    # Geometry
    (comp.geometry,
     cand.orientation_label,
     cand.phase_angle,
     cand.phase_deviation) = composite_geometry_score(sp1, sp2)

    # Thermodynamics
    (comp.thermodynamics,
     cand.sp1_dg,
     cand.sp2_dg,
     cand.sp1_tm,
     cand.sp2_tm) = _pair_thermo_score(sp1.sequence, sp2.sequence, cfg.temperature_k)

    # Complexity / entropy
    (comp.complexity,
     cand.sp1_entropy,
     cand.sp2_entropy) = _pair_complexity_score(sp1.sequence, sp2.sequence)

    # Structure / self-complementarity
    (comp.structure,
     cand.sp1_self_comp,
     cand.sp2_self_comp) = _pair_structure_score(sp1.sequence, sp2.sequence)

    # Off-target
    all_others = [s for s in all_spacer_seqs if s not in (sp1.sequence, sp2.sequence)]
    ot_penalty, ot_risk, ot_n = cross_compare_spacers(
        sp1.sequence, all_others, cfg.ot_max_mismatches
    )
    sp2_penalty, sp2_risk, _ = cross_compare_spacers(
        sp2.sequence, all_others, cfg.ot_max_mismatches
    )
    # Use worst-case spacer for off-target score
    worst_penalty = min(ot_penalty, sp2_penalty)   # lower penalty = higher risk
    cand.ot_min_penalty = worst_penalty if worst_penalty != float("inf") else 999.0
    cand.ot_risk_level  = ot_risk if ot_penalty <= sp2_penalty else sp2_risk
    cand.ot_n_near_matches = ot_n

    # Map penalty to [0, 1] score (higher = safer)
    max_pen = cfg.ot_max_mismatches * cfg.ot_tail_weight + \
              cfg.ot_seed_length * (cfg.ot_seed_weight - cfg.ot_tail_weight)
    if worst_penalty == float("inf"):
        comp.off_target = 1.0
    else:
        comp.off_target = round(min(worst_penalty / max_pen, 1.0), 4)

    # --- Composite score ---
    cand.components      = comp
    cand.composite_score = _weighted_composite(comp, cfg.score_weights)
    cand.confidence_tier = _confidence_tier(cand.composite_score, cand.rejected)

    return cand


# ---------------------------------------------------------------------------
# Batch ranking
# ---------------------------------------------------------------------------

def rank_candidates(
    candidates: List[ScoredCandidate],
    top_n: int,
) -> List[ScoredCandidate]:
    """
    Sort candidates by composite score (descending), excluding rejected ones.
    Returns the top *top_n* non-rejected candidates.
    """
    valid = [c for c in candidates if not c.rejected]
    valid.sort(key=lambda c: c.composite_score, reverse=True)
    return valid[:top_n]
