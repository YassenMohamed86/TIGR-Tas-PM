"""
geometry.py — Helical geometry and orientation scoring.

TIGR-Tas requires both spacers to be presented on the same face of the
DNA helix for simultaneous binding.  This module computes:

  - Angular phase between two spacers based on inter-spacer distance
  - Multi-turn geometry score (correct for all N full helical turns)
  - Strand orientation validation
  - A composite geometry score [0, 1]
"""

from __future__ import annotations

import math
from typing import Tuple

from .constants import HELICAL_PERIOD, OPTIMAL_PHASE_TOLERANCE
from .sequence import Spacer


# ---------------------------------------------------------------------------
# Core geometry calculations
# ---------------------------------------------------------------------------

def inter_spacer_distance(sp1: Spacer, sp2: Spacer) -> int:
    """
    Return the number of base-pairs between the end of sp1 and the
    start of sp2 (gap length).

    Works for same-strand pairs; caller validates orientation.
    """
    return sp2.start - sp1.end


def helical_phase_angle(distance_bp: float, period: float = HELICAL_PERIOD) -> float:
    """
    Convert a gap distance (bp) to a helical phase angle (degrees).

    0° and 360° mean the two spacers are on the same face of the helix.
    180° means they are on opposite faces (disfavourable).
    """
    turns = distance_bp / period
    angle = (turns % 1.0) * 360.0
    return round(angle, 2)


def phase_deviation(distance_bp: float, period: float = HELICAL_PERIOD) -> float:
    """
    Compute the minimum angular deviation from an in-phase configuration.

    Returns a value in [0, 180] degrees.  0° = perfectly in phase.
    """
    angle = helical_phase_angle(distance_bp, period)
    # Deviation is symmetric: 350° is 10° from 0°
    dev = min(angle, 360.0 - angle)
    return round(dev, 2)


def geometry_score_single(
    gap_bp: int,
    tolerance_bp: float = OPTIMAL_PHASE_TOLERANCE,
    period: float = HELICAL_PERIOD,
) -> float:
    """
    Score the geometry of a single gap length.

    The scoring function rewards gaps that place the two spacers on the
    same helical face, accounting for ALL valid numbers of complete turns.

    Score = exp(−(dev / sigma)²)  where dev is the minimum phase deviation
    and sigma scales with tolerance_bp.

    Returns a value in (0, 1].
    """
    if gap_bp <= 0:
        return 0.0

    # Convert tolerance in bp to degrees
    sigma_deg = (tolerance_bp / period) * 360.0

    dev = phase_deviation(gap_bp, period)
    score = math.exp(-(dev / sigma_deg) ** 2)
    return round(score, 4)


def geometry_score_multi_turn(
    gap_bp: int,
    n_turns_range: Tuple[int, int] = (1, 5),
    period: float = HELICAL_PERIOD,
    tolerance_bp: float = OPTIMAL_PHASE_TOLERANCE,
) -> float:
    """
    Evaluate geometry across multiple helical turn configurations.

    For each integer number of turns N in n_turns_range, compute the ideal
    gap (N × period ± tolerance) and score the actual gap against it.
    Returns the best (maximum) score across all N.

    This ensures that gaps spanning 1, 2, 3, 4 … full turns are all
    rewarded if they achieve in-phase geometry — not just those close
    to a single reference distance.
    """
    best = 0.0
    for n in range(n_turns_range[0], n_turns_range[1] + 1):
        ideal_gap = n * period
        deviation_bp = abs(gap_bp - ideal_gap)
        if deviation_bp <= period / 2:
            # Gaussian reward around each ideal gap
            score = math.exp(-(deviation_bp / tolerance_bp) ** 2)
            best = max(best, score)

    # Also include the fractional-turn score for non-integer configurations
    fractional = geometry_score_single(gap_bp, tolerance_bp, period)
    best = max(best, fractional)

    return round(best, 4)


# ---------------------------------------------------------------------------
# Orientation and strand validation
# ---------------------------------------------------------------------------

def orientation_is_valid(sp1: Spacer, sp2: Spacer) -> Tuple[bool, str]:
    """
    Validate the strand orientation of a spacer pair.

    Accepted configurations:
      - Both spacers on the forward (+) strand, sp1 upstream of sp2
      - sp1 on (+) strand, sp2 on (−) strand (convergent)
      - sp1 on (−) strand, sp2 on (+) strand (divergent)

    Rejected:
      - Both on (−) strand with sp2 upstream (inverted duplication)
      - Any overlap between spacers

    Returns (is_valid: bool, orientation_label: str)
    """
    # Spacers must not overlap
    if sp1.end > sp2.start:
        return False, "OVERLAPPING"

    if sp1.strand == "+" and sp2.strand == "+":
        return True, "FORWARD-FORWARD"
    if sp1.strand == "+" and sp2.strand == "-":
        return True, "FORWARD-REVERSE"
    if sp1.strand == "-" and sp2.strand == "+":
        return True, "REVERSE-FORWARD"
    # Both minus with sp2 downstream is treated as valid in some contexts
    if sp1.strand == "-" and sp2.strand == "-":
        return True, "REVERSE-REVERSE"

    return False, "UNKNOWN"


def orientation_score(orientation_label: str) -> float:
    """
    Score the strand orientation configuration.

    FORWARD-FORWARD  → 1.0  (canonical dual-spacer configuration)
    REVERSE-FORWARD  → 0.8  (divergent; biologically observed)
    FORWARD-REVERSE  → 0.8  (convergent; biologically observed)
    REVERSE-REVERSE  → 0.6  (less common but possible)
    OVERLAPPING      → 0.0  (invalid)
    """
    return {
        "FORWARD-FORWARD": 1.0,
        "REVERSE-FORWARD": 0.8,
        "FORWARD-REVERSE": 0.8,
        "REVERSE-REVERSE": 0.6,
        "OVERLAPPING":     0.0,
    }.get(orientation_label, 0.5)


# ---------------------------------------------------------------------------
# Composite geometry score
# ---------------------------------------------------------------------------

def composite_geometry_score(
    sp1: Spacer,
    sp2: Spacer,
    period: float = HELICAL_PERIOD,
    tolerance_bp: float = OPTIMAL_PHASE_TOLERANCE,
) -> Tuple[float, str, float, float]:
    """
    Compute the full geometry score for a spacer pair.

    Returns
    -------
    (score, orientation_label, phase_angle_deg, phase_deviation_deg)

    score is in [0, 1].
    """
    valid, label = orientation_is_valid(sp1, sp2)
    if not valid:
        return 0.0, label, 0.0, 180.0

    gap = inter_spacer_distance(sp1, sp2)
    if gap < 0:
        return 0.0, "OVERLAPPING", 0.0, 180.0

    phase_score = geometry_score_multi_turn(gap, period=period, tolerance_bp=tolerance_bp)
    orient_s = orientation_score(label)
    angle = helical_phase_angle(gap, period)
    deviation = phase_deviation(gap, period)

    # Combine: phase geometry carries 70% of the score, orientation 30%
    final = round(phase_score * 0.70 + orient_s * 0.30, 4)
    return final, label, angle, deviation
