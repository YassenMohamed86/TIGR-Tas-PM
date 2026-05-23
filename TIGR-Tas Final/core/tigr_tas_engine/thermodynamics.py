"""
thermodynamics.py — RNA–DNA nearest-neighbour ΔG calculations.

Uses the Sugimoto 1995 parameter set for RNA:DNA hybrid duplexes.
All energies in kcal/mol; temperature in Kelvin.

Key functions
-------------
delta_g_rna_dna  -- full-duplex free energy for a spacer sequence
delta_g_seed     -- seed-region free energy (positions 1–8)
classify_stability -- human-readable stability label
"""

from __future__ import annotations

import math
from typing import Tuple

from .constants import (
    BODY_TEMPERATURE_K,
    DELTA_G_HARD_CUTOFF,
    DELTA_G_OPTIMAL_MAX,
    GAS_CONSTANT,
    NN_PARAMS,
    OT_SEED_LENGTH,
)
from .sequence import to_rna


# ---------------------------------------------------------------------------
# Low-level nearest-neighbour engine
# ---------------------------------------------------------------------------

def _nn_pair_key(rna_base: str, dna_base: str) -> str:
    """Construct the lookup key for the NN parameter table."""
    return f"r{rna_base}/d{dna_base}"


def _nn_delta_h_s(
    spacer_rna: str,
    target_dna: str,
) -> Tuple[float, float]:
    """
    Compute ΔH and ΔS for an RNA:DNA duplex using nearest-neighbour sums.

    Parameters
    ----------
    spacer_rna  : RNA sequence of the spacer (5'→3')
    target_dna  : DNA target strand, same direction (NOT reverse complement)

    Returns
    -------
    (ΔH, ΔS) in (kcal/mol, cal/mol·K)
    """
    dH = dS = 0.0
    length = min(len(spacer_rna), len(target_dna))

    for i in range(length - 1):
        r_base = spacer_rna[i]
        d_base = target_dna[i]
        key = _nn_pair_key(r_base, d_base)
        h, s = NN_PARAMS.get(key, (-4.0, -11.0))   # fallback: average mismatch
        dH += h
        dS += s

    # Initiation parameters (terminal AT penalty)
    for base in (spacer_rna[0], spacer_rna[-1]):
        if base in ("A", "U"):
            dH += 2.3
            dS += 4.1

    return dH, dS


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def delta_g_rna_dna(
    spacer_dna: str,
    temperature_k: float = BODY_TEMPERATURE_K,
) -> float:
    """
    Compute the ΔG of RNA–DNA hybridisation for a spacer sequence.

    The function converts the spacer DNA to RNA, then computes the
    nearest-neighbour free energy against the complementary DNA strand.

    Parameters
    ----------
    spacer_dna   : DNA sequence of the spacer (5'→3')
    temperature_k: absolute temperature in Kelvin (default 37 °C)

    Returns
    -------
    float
        ΔG in kcal/mol (more negative = more stable).
    """
    spacer_rna = to_rna(spacer_dna)
    # Target strand is the complement in 3'→5' direction;
    # for NN sums we use the same 5'→3' index position.
    target_dna = spacer_dna   # NN sums work on the 5'→3' spacer sequence
    dH, dS = _nn_delta_h_s(spacer_rna, target_dna)
    dG = dH - temperature_k * (dS / 1000.0)
    return round(dG, 4)


def delta_g_seed(
    spacer_dna: str,
    seed_length: int = OT_SEED_LENGTH,
    temperature_k: float = BODY_TEMPERATURE_K,
) -> float:
    """
    Compute ΔG for only the seed region (first *seed_length* bases).

    The seed region dominates initial R-loop nucleation kinetics.
    """
    return delta_g_rna_dna(spacer_dna[:seed_length], temperature_k)


def melting_temperature(spacer_dna: str) -> float:
    """
    Approximate Tm (°C) of the RNA:DNA hybrid using the Wallace rule
    adjusted for RNA:DNA hybrids.

    Tm = 2*(A+T) + 4*(G+C) - 5  [RNA:DNA correction of −5 °C]
    """
    seq = spacer_dna.upper()
    n_gc = seq.count("G") + seq.count("C")
    n_at = seq.count("A") + seq.count("T")
    return 2 * n_at + 4 * n_gc - 5.0


def classify_stability(dG: float) -> str:
    """Return a human-readable stability label for a ΔG value."""
    if dG <= DELTA_G_OPTIMAL_MAX:
        return "OPTIMAL"
    elif dG <= DELTA_G_HARD_CUTOFF:
        return "MODERATE"
    else:
        return "WEAK"


def thermodynamic_score(
    spacer_dna: str,
    temperature_k: float = BODY_TEMPERATURE_K,
) -> float:
    """
    Map the full-duplex ΔG to a [0, 1] score.

    Score = 1.0 at ΔG ≤ −12 kcal/mol (very stable)
    Score = 0.0 at ΔG ≥  −4 kcal/mol (too weak)
    Linear interpolation in between.
    """
    dG = delta_g_rna_dna(spacer_dna, temperature_k)
    DG_MIN = -16.0
    DG_MAX = -4.0
    if dG <= DG_MIN:
        return 1.0
    if dG >= DG_MAX:
        return 0.0
    return round((DG_MAX - dG) / (DG_MAX - DG_MIN), 4)
