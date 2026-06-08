"""
results_assembler.py — Score Collection and Results Table Assembly
=================================================================

SELF-AUDIT
----------
Magic numbers   : NONE — no numerical constants in this module; all scoring
                  constants live in the respective scoring modules.
Cross-imports   : This is the ONLY integration point that imports from all four
                  scoring modules.  No scoring module imports from another.
eval/exec       : NONE
Inline styles   : N/A (no HTML)
Type annotations: COMPLETE — every function signature fully annotated.
Test data        : CATEGORY 2 (synthetic) — see tests/test_results_assembler.py
Assumptions     : final_score is PARAMETER_UNRESOLVED — composite weights
                  (w1–w4) have no empirical basis yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from modules.geometry_model import compute_geometry_score
from modules.cleavage_model import compute_cleavage_score
from modules.thermodynamics_model import compute_stability_score
from modules.specificity_engine import compute_specificity_score
from modules.candidate_generator import CandidatePair

# ---------------------------------------------------------------------------
# Assumption-warning catalogue
# ---------------------------------------------------------------------------
# Each entry is surfaced on every scored pair so the user knows which
# [HYPOTHESIS] assumptions feed into the result.
_ASSUMPTION_WARNINGS: List[str] = [
    "ASSUMP-002: Gaussian phase model is hypothetical for TIGR-Tas "
    "(evidence: CRISPRa analogy)",
    "ASSUMP-003: Cleavage offset (3 bp) borrowed from Cas9 "
    "[HYPOTHESIS — CROSS-SYSTEM]",
    "ASSUMP-004: Optimal overhang range 7–9 bp is hypothetical "
    "(evidence: split-Cas9 literature)",
    "ASSUMP-005: Simplified ΔG model (Wallace rule) used instead of "
    "full nearest-neighbour SantaLucia model [HYPOTHESIS]",
    "ASSUMP-006: Seed region positions 0–7 borrowed from Cas9 "
    "[HYPOTHESIS — CROSS-SYSTEM]",
    "ASSUMP-007: Mismatch risk thresholds (1, 3) are engineering "
    "judgements [HYPOTHESIS]",
    "ASSUMP-009: Composite weights (w1–w4) are UNRESOLVED — "
    "final_score is None",
]


# ---------------------------------------------------------------------------
# Data class — one per scored candidate pair
# ---------------------------------------------------------------------------
@dataclass
class ScoredPair:
    """A fully-scored spacer-A / spacer-B candidate pair."""

    spacer_a: str
    spacer_b: str
    pos_a: int
    pos_b: int
    strand_a: str
    strand_b: str
    gc_a: float
    gc_b: float
    distance: int
    geometry_score: float
    cleavage_score: float
    stability_score_a: float
    stability_score_b: float
    specificity_score_a: float
    specificity_score_b: float
    final_score: Optional[float] = None          # [PARAMETER_UNRESOLVED] — weights not derived
    assumption_warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def assemble_results(
    candidates: List[CandidatePair],
    sequence: str,
    k: int = 9,
) -> List[ScoredPair]:
    """Score every candidate pair and return a list of :class:`ScoredPair`.

    Parameters
    ----------
    candidates:
        Output of :func:`modules.candidate_generator.generate_candidate_pairs`.
    sequence:
        The full target DNA sequence (upper-case, validated).
    k:
        Spacer length in nucleotides.

    Returns
    -------
    List[ScoredPair]
        One entry per candidate, ordered the same as *candidates*.
    """
    if not candidates:
        return []

    scored: List[ScoredPair] = []

    for pair in candidates:
        try:
            geometry: float = compute_geometry_score(pair.pos_a, pair.pos_b)
            cleavage: float = compute_cleavage_score(pair.pos_a, pair.pos_b, k)
            stab_a: float = compute_stability_score(pair.spacer_a)
            stab_b: float = compute_stability_score(pair.spacer_b)
            spec_a: float = compute_specificity_score(
                pair.spacer_a, sequence, k,
            )
            spec_b: float = compute_specificity_score(
                pair.spacer_b, sequence, k,
            )

            scored.append(
                ScoredPair(
                    spacer_a=pair.spacer_a,
                    spacer_b=pair.spacer_b,
                    pos_a=pair.pos_a,
                    pos_b=pair.pos_b,
                    strand_a=pair.strand_a,
                    strand_b=pair.strand_b,
                    gc_a=pair.gc_a,
                    gc_b=pair.gc_b,
                    distance=pair.distance,
                    geometry_score=geometry,
                    cleavage_score=cleavage,
                    stability_score_a=stab_a,
                    stability_score_b=stab_b,
                    specificity_score_a=spec_a,
                    specificity_score_b=spec_b,
                    final_score=None,  # [PARAMETER_UNRESOLVED]
                    assumption_warnings=list(_ASSUMPTION_WARNINGS),
                )
            )

        except Exception as exc:  # noqa: BLE001 — broad catch is intentional
            scored.append(
                ScoredPair(
                    spacer_a=pair.spacer_a,
                    spacer_b=pair.spacer_b,
                    pos_a=pair.pos_a,
                    pos_b=pair.pos_b,
                    strand_a=pair.strand_a,
                    strand_b=pair.strand_b,
                    gc_a=pair.gc_a,
                    gc_b=pair.gc_b,
                    distance=pair.distance,
                    geometry_score=0.0,
                    cleavage_score=0.0,
                    stability_score_a=0.0,
                    stability_score_b=0.0,
                    specificity_score_a=0.0,
                    specificity_score_b=0.0,
                    final_score=None,
                    assumption_warnings=list(_ASSUMPTION_WARNINGS),
                    error=str(exc),
                )
            )

    return scored
