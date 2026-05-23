"""
complexity.py — Sequence complexity and structural-risk filters.

Provides deterministic rules for:
  - GC content scoring
  - Shannon entropy (low-complexity rejection)
  - Self-complementarity estimation (hairpin risk)
  - Homopolymer detection
  - Dinucleotide repeat detection
"""

from __future__ import annotations

import math
from typing import List, Tuple

from .constants import (
    ENTROPY_MIN,
    GC_ACCEPT_HIGH,
    GC_ACCEPT_LOW,
    GC_OPTIMAL_HIGH,
    GC_OPTIMAL_LOW,
    SELF_COMP_MAX_SCORE,
)
from .sequence import reverse_complement


# ---------------------------------------------------------------------------
# GC content
# ---------------------------------------------------------------------------

def gc_fraction(seq: str) -> float:
    """Return the GC fraction of *seq* (0.0 – 1.0)."""
    if not seq:
        return 0.0
    gc = sum(1 for b in seq.upper() if b in "GC")
    return gc / len(seq)


def gc_score(seq: str, low: float = GC_OPTIMAL_LOW, high: float = GC_OPTIMAL_HIGH) -> float:
    """
    Score GC content on [0, 1].

    1.0  → within optimal window [low, high]
    0.5  → within acceptable window but outside optimal
    0.2  → outside acceptable range (potential instability)
    0.0  → extreme deviation
    """
    gc = gc_fraction(seq)
    if low <= gc <= high:
        return 1.0
    dist_to_optimal = min(abs(gc - low), abs(gc - high))
    if GC_ACCEPT_LOW <= gc <= GC_ACCEPT_HIGH:
        # Smooth penalty: closer to optimal = higher score
        return round(max(0.5 - dist_to_optimal * 2.0, 0.2), 4)
    return round(max(0.2 - dist_to_optimal * 1.5, 0.0), 4)


# ---------------------------------------------------------------------------
# Shannon entropy (sequence complexity)
# ---------------------------------------------------------------------------

def shannon_entropy(seq: str) -> float:
    """
    Compute the per-position Shannon entropy (bits) of the nucleotide
    frequency distribution.

    Maximum value for 4 equally frequent bases is log2(4) = 2.0 bits.
    Values below ENTROPY_MIN indicate low-complexity / repetitive sequence.
    """
    seq = seq.upper()
    if not seq:
        return 0.0
    freq = {b: seq.count(b) / len(seq) for b in "ACGT"}
    return round(
        -sum(p * math.log2(p) for p in freq.values() if p > 0),
        4
    )


def entropy_score(seq: str) -> float:
    """Map Shannon entropy to a [0, 1] score."""
    h = shannon_entropy(seq)
    max_h = math.log2(4)    # 2.0 bits
    return round(min(h / max_h, 1.0), 4)


def is_low_complexity(seq: str) -> bool:
    """Return True if the sequence is too repetitive to be a good spacer."""
    return shannon_entropy(seq) < ENTROPY_MIN


# ---------------------------------------------------------------------------
# Homopolymer detection
# ---------------------------------------------------------------------------

def max_homopolymer_run(seq: str) -> int:
    """Return the length of the longest mononucleotide run."""
    if not seq:
        return 0
    max_run = current_run = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i - 1]:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1
    return max_run


def homopolymer_penalty(seq: str) -> float:
    """
    Return a [0, 1] penalty factor (0 = bad, 1 = good).

    Runs ≥ 4 of the same base → instability signal.
    """
    run = max_homopolymer_run(seq.upper())
    if run <= 3:
        return 1.0
    if run == 4:
        return 0.7
    if run == 5:
        return 0.4
    return 0.1


# ---------------------------------------------------------------------------
# Dinucleotide repeat detection
# ---------------------------------------------------------------------------

def dinucleotide_repeat_score(seq: str) -> float:
    """
    Detect tandem dinucleotide repeats (e.g., ATATATAT, GCGCGCGC).

    Returns a penalty score in [0, 1] where 1.0 means no problematic repeats.
    """
    seq = seq.upper()
    worst_fraction = 0.0
    for i in range(len(seq) - 1):
        dinuc = seq[i:i + 2]
        # Count non-overlapping occurrences
        count = 0
        pos = 0
        while True:
            found = seq.find(dinuc, pos)
            if found == -1:
                break
            count += 1
            pos = found + 2   # non-overlapping
        fraction = (count * 2) / len(seq)
        worst_fraction = max(worst_fraction, fraction)
    return round(max(1.0 - worst_fraction, 0.0), 4)


# ---------------------------------------------------------------------------
# Self-complementarity (hairpin risk)
# ---------------------------------------------------------------------------

def self_complementarity_score(seq: str, min_stem: int = 4) -> float:
    """
    Estimate self-complementarity as the fraction of bases that could
    participate in a hairpin stem.

    Algorithm: compare the sequence against its reverse complement using
    a sliding comparison; find the longest near-complementary region.

    Parameters
    ----------
    seq      : DNA spacer sequence
    min_stem : minimum stem length to consider

    Returns
    -------
    float
        Fraction of bases in matched stems (0.0 = none, 1.0 = fully palindromic).
    """
    seq = seq.upper()
    rc = reverse_complement(seq)
    n = len(seq)
    if n < 2 * min_stem:
        return 0.0

    max_matched = 0
    # Slide rc relative to seq and count matching positions
    for offset in range(-n + min_stem, n - min_stem + 1):
        matched = 0
        for i in range(n):
            j = i + offset
            if 0 <= j < n and seq[i] == rc[j]:
                matched += 1
        max_matched = max(max_matched, matched)

    return round(max_matched / n, 4)


def structure_score(seq: str) -> float:
    """
    Combined structural suitability score [0, 1].

    Penalises homopolymer runs, low complexity, and self-complementarity.
    """
    sc = self_complementarity_score(seq)
    sc_penalty = max(0.0, 1.0 - sc / SELF_COMP_MAX_SCORE)
    hp = homopolymer_penalty(seq)
    dr = dinucleotide_repeat_score(seq)
    combined = (sc_penalty * 0.5) + (hp * 0.3) + (dr * 0.2)
    return round(min(combined, 1.0), 4)


# ---------------------------------------------------------------------------
# Composite complexity pass/fail
# ---------------------------------------------------------------------------

def passes_complexity_filter(seq: str) -> Tuple[bool, str]:
    """
    Return (True, "") if the spacer passes all complexity filters,
    or (False, reason) if it should be rejected.
    """
    gc = gc_fraction(seq)
    if gc < GC_ACCEPT_LOW or gc > GC_ACCEPT_HIGH:
        return False, f"GC fraction {gc:.2f} outside acceptable range [{GC_ACCEPT_LOW}, {GC_ACCEPT_HIGH}]"

    h = shannon_entropy(seq)
    if h < ENTROPY_MIN:
        return False, f"Shannon entropy {h:.2f} below minimum {ENTROPY_MIN}"

    run = max_homopolymer_run(seq)
    if run >= 6:
        return False, f"Homopolymer run of {run} detected"

    sc = self_complementarity_score(seq)
    if sc > SELF_COMP_MAX_SCORE:
        return False, f"Self-complementarity {sc:.2f} exceeds maximum {SELF_COMP_MAX_SCORE}"

    return True, ""
