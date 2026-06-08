"""
TIGR-Tas Dual-Guide RNA Scoring Platform — Geometry Model
==========================================================

SELF-AUDIT
----------
Module purpose : Score dual-guide pairs by helical phase alignment.
Evidence level : HELIX_PERIOD_BP is ESTABLISHED; GEOMETRY_SIGMA is HYPOTHESIS.
Magic numbers  : NONE — all constants are named with evidence tags.
Cross-imports  : NONE — this module is fully independent.
eval/exec      : NONE.
Type annotations: Complete on all public functions.
Test data cat. : CATEGORY 2 (synthetic).
"""

import math

# ---------------------------------------------------------------------------
# Named biophysical constants
# ---------------------------------------------------------------------------

HELIX_PERIOD_BP: float = 10.5
# [ESTABLISHED] B-form DNA helix period.
# Watson & Crick 1953, Nature 171:737-738; Wang et al. 1979, Science 205:972

GEOMETRY_SIGMA: float = 2.0
# [HYPOTHESIS] Gaussian width for phase scoring, analogous to
# dual-guide CRISPRa co-occupancy models.


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_geometry_score(pos_a: int, pos_b: int) -> float:
    """Return a [0, 1] score reflecting helical-phase alignment of two guide
    binding positions on B-form DNA.

    A score of 1.0 means the inter-guide gap is an exact multiple of the
    helix period (10.5 bp) — i.e. both guides sit on the same face of the
    double helix.  The score decays as a Gaussian with sigma =
    ``GEOMETRY_SIGMA`` as the phase offset departs from zero.

    Parameters
    ----------
    pos_a : int
        Genomic start position of guide A (bp).
    pos_b : int
        Genomic start position of guide B (bp).

    Returns
    -------
    float
        Geometry score in [0, 1].
    """
    gap: int = abs(pos_b - pos_a)
    phase: float = gap % HELIX_PERIOD_BP

    # Wrap to nearest distance from 0 — phase could be closer from above.
    # Without this wrap, gap=10 would give phase=10.0 (score ≈ 0) instead of
    # the correct phase=0.5 (score ≈ 0.97).
    if phase > HELIX_PERIOD_BP / 2:
        phase = HELIX_PERIOD_BP - phase

    score: float = math.exp(-(phase ** 2) / (2 * GEOMETRY_SIGMA ** 2))
    return score
