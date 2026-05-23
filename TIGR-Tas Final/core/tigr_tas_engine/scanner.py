"""
scanner.py — Dual-spacer detection engine.

Algorithm
---------
1. Build a k-mer index for both the forward strand and its reverse complement.
2. For each window size in [SPACER_MIN_LEN, SPACER_MAX_LEN], enumerate
   all candidate spacers on both strands.
3. Apply fast pre-filters (GC, complexity, thermodynamics) to discard
   low-quality candidates before pairing.
4. Pair all valid spacers whose gap falls within [GAP_MIN, GAP_MAX].
5. Yield SpacerPair objects for downstream scoring.

The scanner is the only module that knows about the raw sequence;
all downstream modules receive SpacerPair objects.
"""

from __future__ import annotations

import itertools
from typing import Generator, Iterator, List, Optional, Tuple

from .complexity import passes_complexity_filter
from .constants import (
    DELTA_G_HARD_CUTOFF,
    GAP_MAX,
    GAP_MIN,
    SPACER_MAX_LEN,
    SPACER_MIN_LEN,
    PipelineConfig,
)
from .sequence import BothStrands, Spacer, SpacerPair, sliding_windows
from .thermodynamics import delta_g_rna_dna


# ---------------------------------------------------------------------------
# Spacer candidate generation
# ---------------------------------------------------------------------------

def _make_spacer(seq: str, start: int, end: int, strand: str) -> Spacer:
    return Spacer(sequence=seq, start=start, end=end, strand=strand, length=end - start)


def _candidate_spacers(
    strands: BothStrands,
    cfg: PipelineConfig,
) -> List[Spacer]:
    """
    Enumerate all candidate spacers on both strands, applying pre-filters.

    Pre-filters applied here (cheap, fast):
      1. GC content within acceptable range
      2. Shannon entropy above minimum
      3. ΔG above hard cutoff (too weak → reject)

    Structural filters (self-complementarity, homopolymers) are applied later
    in the complexity module at scoring time.
    """
    candidates: List[Spacer] = []
    n = len(strands)

    for seq, start, end in sliding_windows(
        strands.forward, cfg.spacer_min_len, cfg.spacer_max_len
    ):
        ok, _ = passes_complexity_filter(seq)
        if not ok:
            continue
        dg = delta_g_rna_dna(seq, cfg.temperature_k)
        if dg > cfg.delta_g_hard_cutoff:
            continue
        candidates.append(_make_spacer(seq, start, end, "+"))

    # Reverse-complement strand: positions are remapped to forward coordinates
    for seq, rc_start, rc_end in sliding_windows(
        strands.reverse, cfg.spacer_min_len, cfg.spacer_max_len
    ):
        ok, _ = passes_complexity_filter(seq)
        if not ok:
            continue
        dg = delta_g_rna_dna(seq, cfg.temperature_k)
        if dg > cfg.delta_g_hard_cutoff:
            continue
        # Convert RC positions back to forward-strand coordinates
        fwd_end   = n - rc_start
        fwd_start = n - rc_end
        candidates.append(_make_spacer(seq, fwd_start, fwd_end, "-"))

    return candidates


# ---------------------------------------------------------------------------
# Spacer pairing
# ---------------------------------------------------------------------------

def _pair_id(sp1: Spacer, sp2: Spacer) -> str:
    return f"{sp1.strand}{sp1.start}-{sp2.strand}{sp2.start}"


def _pair_spacers(
    spacers: List[Spacer],
    cfg: PipelineConfig,
) -> List[SpacerPair]:
    """
    Pair all valid spacers within gap constraints.

    Optimization: spacers are sorted by start position; for each sp1,
    only scan spacers whose start is within [sp1.end + GAP_MIN,
    sp1.end + GAP_MAX + SPACER_MAX_LEN] — no need to check all pairs.
    """
    spacers_sorted = sorted(spacers, key=lambda s: s.start)
    pairs: List[SpacerPair] = []

    for i, sp1 in enumerate(spacers_sorted):
        gap_start_pos = sp1.end + cfg.gap_min
        gap_end_pos   = sp1.end + cfg.gap_max

        for sp2 in spacers_sorted[i + 1:]:
            if sp2.start < gap_start_pos:
                continue
            if sp2.start > gap_end_pos + cfg.spacer_max_len:
                break   # sorted order: no more valid sp2

            gap = sp2.start - sp1.end
            if cfg.gap_min <= gap <= cfg.gap_max:
                pairs.append(SpacerPair(
                    spacer1=sp1,
                    spacer2=sp2,
                    gap=gap,
                    pair_id=_pair_id(sp1, sp2),
                ))

    return pairs


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def detect_spacer_pairs(
    sequence: str,
    cfg: Optional[PipelineConfig] = None,
) -> Tuple[List[SpacerPair], int]:
    """
    Detect all valid dual-spacer pairs in a DNA sequence.

    Parameters
    ----------
    sequence : validated, uppercase DNA string
    cfg      : PipelineConfig (uses defaults if None)

    Returns
    -------
    (pairs, n_candidates_before_pairing)
    """
    if cfg is None:
        cfg = PipelineConfig()

    strands = BothStrands.from_sequence(sequence)
    candidates = _candidate_spacers(strands, cfg)
    pairs = _pair_spacers(candidates, cfg)

    return pairs, len(candidates)
