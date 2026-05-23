"""
offtarget.py — Position-weighted mismatch off-target detection.

Implements a deterministic off-target risk analysis using:
  - Hamming distance with position-specific weights
  - Seed-region weighting (2×) vs. tail-region weighting (1×)
  - Risk classification (HIGH / MEDIUM / LOW)
  - Off-target density counting

This is an internal off-target analysis comparing each candidate spacer
against all other spacers in the input sequence.  For genome-wide
scanning, candidates should be compared against a pre-indexed reference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .constants import (
    OT_HIGH_RISK_MAX,
    OT_MAX_MISMATCHES,
    OT_MEDIUM_RISK_MAX,
    OT_SEED_LENGTH,
    OT_SEED_WEIGHT,
    OT_TAIL_WEIGHT,
)
from .sequence import reverse_complement


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class OffTargetHit:
    """A single off-target match between a query spacer and a target."""
    query:            str
    target:           str
    target_start:     int
    target_strand:    str
    weighted_penalty: float
    n_mismatches:     int
    seed_mismatches:  int
    tail_mismatches:  int
    risk_level:       str


@dataclass
class OffTargetSummary:
    """Aggregated off-target analysis for one spacer candidate."""
    spacer_seq:         str
    hits:               List[OffTargetHit] = field(default_factory=list)
    min_penalty:        float = float("inf")
    mean_penalty:       float = 0.0
    n_high_risk:        int = 0
    n_medium_risk:      int = 0
    n_low_risk:         int = 0
    overall_risk:       str = "UNKNOWN"
    ot_score:           float = 1.0   # 1.0 = no off-targets; lower = riskier


# ---------------------------------------------------------------------------
# Core mismatch engine
# ---------------------------------------------------------------------------

def weighted_mismatch_penalty(
    query: str,
    target: str,
    seed_length: int = OT_SEED_LENGTH,
    seed_weight: float = OT_SEED_WEIGHT,
    tail_weight: float = OT_TAIL_WEIGHT,
) -> Tuple[float, int, int, int]:
    """
    Compute the position-weighted mismatch penalty between two sequences.

    Positions 0..(seed_length-1) are weighted by *seed_weight*.
    Positions seed_length..end are weighted by *tail_weight*.

    Returns
    -------
    (weighted_penalty, total_mismatches, seed_mismatches, tail_mismatches)
    """
    n = min(len(query), len(target))
    total_penalty = 0.0
    seed_mm = tail_mm = 0

    for i in range(n):
        if query[i] != target[i]:
            if i < seed_length:
                total_penalty += seed_weight
                seed_mm += 1
            else:
                total_penalty += tail_weight
                tail_mm += 1

    # Length difference also contributes (treat as mismatches)
    length_diff = abs(len(query) - len(target))
    total_penalty += length_diff * tail_weight

    return round(total_penalty, 2), seed_mm + tail_mm, seed_mm, tail_mm


def risk_level(weighted_penalty: float) -> str:
    """Classify a weighted mismatch penalty into risk categories."""
    if weighted_penalty <= OT_HIGH_RISK_MAX:
        return "HIGH"
    if weighted_penalty <= OT_MEDIUM_RISK_MAX:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Off-target scanning against a pool of sequences
# ---------------------------------------------------------------------------

def scan_off_targets(
    query: str,
    reference_seq: str,
    max_mismatches: int = OT_MAX_MISMATCHES,
    seed_length: int = OT_SEED_LENGTH,
    seed_weight: float = OT_SEED_WEIGHT,
    tail_weight: float = OT_TAIL_WEIGHT,
) -> OffTargetSummary:
    """
    Scan the reference sequence for off-target binding sites of *query*.

    Slides a window equal to len(query) across both strands of the
    reference, computing the weighted mismatch penalty at each position.
    Only positions with penalty ≤ max_mismatches × tail_weight are
    reported (adjusted for length).

    Parameters
    ----------
    query         : spacer sequence to test
    reference_seq : full DNA sequence to scan
    max_mismatches: maximum weighted penalty threshold to include a hit

    Returns
    -------
    OffTargetSummary
    """
    summary = OffTargetSummary(spacer_seq=query)
    q_len = len(query)
    max_penalty = max_mismatches * tail_weight + seed_length * (seed_weight - tail_weight)

    for strand, seq in [("+", reference_seq), ("-", reverse_complement(reference_seq))]:
        for i in range(len(seq) - q_len + 1):
            target_window = seq[i:i + q_len]

            # Skip exact match (this is the query itself)
            if target_window == query:
                continue

            penalty, n_mm, seed_mm, tail_mm = weighted_mismatch_penalty(
                query, target_window, seed_length, seed_weight, tail_weight
            )

            if penalty > max_penalty:
                continue

            rl = risk_level(penalty)
            hit = OffTargetHit(
                query=query,
                target=target_window,
                target_start=i,
                target_strand=strand,
                weighted_penalty=penalty,
                n_mismatches=n_mm,
                seed_mismatches=seed_mm,
                tail_mismatches=tail_mm,
                risk_level=rl,
            )
            summary.hits.append(hit)

            if rl == "HIGH":
                summary.n_high_risk += 1
            elif rl == "MEDIUM":
                summary.n_medium_risk += 1
            else:
                summary.n_low_risk += 1

    if summary.hits:
        penalties = [h.weighted_penalty for h in summary.hits]
        summary.min_penalty = round(min(penalties), 2)
        summary.mean_penalty = round(sum(penalties) / len(penalties), 2)
    else:
        summary.min_penalty = float("inf")
        summary.mean_penalty = 0.0

    summary.overall_risk = _overall_risk(summary)
    summary.ot_score = _ot_score(summary, max_penalty)
    return summary


def _overall_risk(s: OffTargetSummary) -> str:
    if s.n_high_risk > 0:
        return "HIGH"
    if s.n_medium_risk > 0:
        return "MEDIUM"
    if s.n_low_risk > 0:
        return "LOW"
    return "NONE"


def _ot_score(s: OffTargetSummary, max_penalty: float) -> float:
    """
    Map off-target characteristics to a [0, 1] specificity score.

    1.0 = no off-targets detected.
    0.0 = severe off-target burden.
    """
    if not s.hits:
        return 1.0

    # Penalty from hit counts, weighted by risk
    hit_penalty = (
        s.n_high_risk * 0.4 +
        s.n_medium_risk * 0.2 +
        s.n_low_risk * 0.05
    )
    # Additional penalty from minimum distance (closer = worse)
    if s.min_penalty < max_penalty:
        proximity_penalty = 0.3 * (1.0 - s.min_penalty / max_penalty)
    else:
        proximity_penalty = 0.0

    raw_score = 1.0 - min(hit_penalty + proximity_penalty, 1.0)
    return round(raw_score, 4)


# ---------------------------------------------------------------------------
# Spacer-pool comparison
# ---------------------------------------------------------------------------

def cross_compare_spacers(
    candidate_seq: str,
    all_spacer_seqs: List[str],
    max_mismatches: int = OT_MAX_MISMATCHES,
) -> Tuple[float, str, int]:
    """
    Compare *candidate_seq* against a pool of other spacer sequences.

    Returns (min_weighted_penalty, risk_level, n_near_matches).
    Used when a full genomic reference is not available.
    """
    min_pen = float("inf")
    n_near = 0

    for other in all_spacer_seqs:
        if other == candidate_seq:
            continue
        pen, *_ = weighted_mismatch_penalty(candidate_seq, other)
        if pen <= max_mismatches * OT_TAIL_WEIGHT:
            n_near += 1
            min_pen = min(min_pen, pen)

    if min_pen == float("inf"):
        return float("inf"), "NONE", 0

    return min_pen, risk_level(min_pen), n_near
