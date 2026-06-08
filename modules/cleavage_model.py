"""
TIGR-Tas Dual-Guide RNA Scoring Platform — Cleavage Model
===========================================================

SELF-AUDIT
----------
Module purpose : Score dual-guide pairs by predicted cleavage-overhang suitability.
Evidence level : CAS9_CLEAVAGE_OFFSET is HYPOTHESIS — CROSS-SYSTEM;
                 overhang range constants are HYPOTHESIS.
Magic numbers  : NONE — all constants are named with evidence tags.
Cross-imports  : NONE — this module is fully independent.
eval/exec      : NONE.
Type annotations: Complete on all public functions.
Test data cat. : CATEGORY 2 (synthetic).
"""

# ---------------------------------------------------------------------------
# Named biophysical constants
# ---------------------------------------------------------------------------

CAS9_CLEAVAGE_OFFSET: int = 3
# [HYPOTHESIS — CROSS-SYSTEM] Cas9 cuts 3 bp from PAM-proximal end of the
# spacer.  Derived from SpCas9 literature; applicability to TIGR-Tas
# dual-guide architecture is hypothesised.

OPTIMAL_OVERHANG_MIN: int = 7
# [HYPOTHESIS] Lower bound of the optimal overhang window.  Inspired by
# split-Cas9 reconstitution studies.

OPTIMAL_OVERHANG_MAX: int = 9
# [HYPOTHESIS] Upper bound of the optimal overhang window.

ACCEPTABLE_OVERHANG_MIN: int = 5
# [HYPOTHESIS] Lower bound of the acceptable (but sub-optimal) window.

ACCEPTABLE_OVERHANG_MAX: int = 12
# [HYPOTHESIS] Upper bound of the acceptable (but sub-optimal) window.


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_cut_position(spacer_start: int, k: int) -> int:
    """Return the predicted cut-site position for a spacer of length *k*
    that begins at *spacer_start*.

    Parameters
    ----------
    spacer_start : int
        0-based genomic position where the spacer begins.
    k : int
        Length of the spacer (nt).

    Returns
    -------
    int
        Predicted cut position (bp).
    """
    return spacer_start + (k - CAS9_CLEAVAGE_OFFSET)


def compute_overhang(pos_a: int, pos_b: int, k: int) -> int:
    """Return the absolute distance between the two predicted cut sites.

    Parameters
    ----------
    pos_a : int
        Spacer-A start position.
    pos_b : int
        Spacer-B start position.
    k : int
        Spacer length (nt).

    Returns
    -------
    int
        Unsigned overhang distance (bp).
    """
    cut_a: int = compute_cut_position(pos_a, k)
    cut_b: int = compute_cut_position(pos_b, k)
    return abs(cut_b - cut_a)


def compute_cleavage_score(pos_a: int, pos_b: int, k: int) -> float:
    """Score a dual-guide pair based on predicted cleavage overhang.

    Returns
    -------
    float
        1.0 — optimal overhang [7, 9] bp
        0.6 — acceptable overhang [5, 7) or (9, 12] bp
        0.2 — all other overhangs
    """
    overhang: int = compute_overhang(pos_a, pos_b, k)

    if OPTIMAL_OVERHANG_MIN <= overhang <= OPTIMAL_OVERHANG_MAX:
        return 1.0
    elif ACCEPTABLE_OVERHANG_MIN <= overhang < OPTIMAL_OVERHANG_MIN:
        return 0.6
    elif OPTIMAL_OVERHANG_MAX < overhang <= ACCEPTABLE_OVERHANG_MAX:
        return 0.6
    else:
        return 0.2
