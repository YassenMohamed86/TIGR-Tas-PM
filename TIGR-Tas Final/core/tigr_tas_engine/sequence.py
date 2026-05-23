"""
sequence.py — Core sequence utilities.

Provides:
  - Input validation and normalisation
  - Reverse-complement computation (DNA and RNA)
  - K-mer index construction for O(1) position lookup
  - Strand enumeration helper
"""

from __future__ import annotations

import re
from typing import Dict, Generator, Iterator, List, NamedTuple, Tuple

from .constants import COMPLEMENT, DNA_BASES


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

class Spacer(NamedTuple):
    """A detected spacer sequence with positional metadata."""
    sequence:  str
    start:     int          # 0-based, inclusive
    end:       int          # 0-based, exclusive
    strand:    str          # "+" or "-"
    length:    int


class SpacerPair(NamedTuple):
    """A validated dual-spacer candidate ready for scoring."""
    spacer1:   Spacer       # upstream spacer
    spacer2:   Spacer       # downstream spacer
    gap:       int          # bp between spacer1.end and spacer2.start
    pair_id:   str          # human-readable identifier


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_VALID_DNA_RE = re.compile(r"^[ACGTacgt]+$")


def validate_sequence(seq: str) -> str:
    """
    Validate and normalise a DNA sequence.

    Returns the uppercase sequence or raises ValueError.
    """
    if not seq:
        raise ValueError("Empty sequence provided.")
    seq = seq.strip().upper().replace(" ", "").replace("\n", "")
    if not _VALID_DNA_RE.match(seq):
        illegal = set(seq) - DNA_BASES
        raise ValueError(
            f"Sequence contains non-DNA characters: {illegal!r}. "
            "Only A, C, G, T are accepted."
        )
    if len(seq) < 40:
        raise ValueError(
            f"Sequence too short ({len(seq)} bp). "
            "Minimum is 40 bp for meaningful spacer detection."
        )
    return seq


# ---------------------------------------------------------------------------
# Complement / reverse-complement
# ---------------------------------------------------------------------------

def complement(seq: str) -> str:
    """Return the DNA complement (5'→3' direction preserved)."""
    try:
        return "".join(COMPLEMENT[b] for b in seq)
    except KeyError as exc:
        raise ValueError(f"Non-DNA character in sequence: {exc}") from exc


def reverse_complement(seq: str) -> str:
    """Return the reverse complement of a DNA sequence."""
    return complement(seq)[::-1]


def to_rna(dna: str) -> str:
    """Convert a DNA sequence to its RNA equivalent (T → U)."""
    return dna.upper().replace("T", "U")


# ---------------------------------------------------------------------------
# K-mer index
# ---------------------------------------------------------------------------

KmerIndex = Dict[str, List[int]]


def build_kmer_index(seq: str, k: int) -> KmerIndex:
    """
    Build an index mapping every k-mer to its list of start positions.

    Parameters
    ----------
    seq : str
        The target DNA sequence (uppercase).
    k : int
        K-mer length.

    Returns
    -------
    KmerIndex
        dict[kmer_string, [pos0, pos1, ...]]
    """
    index: KmerIndex = {}
    for i in range(len(seq) - k + 1):
        kmer = seq[i:i + k]
        index.setdefault(kmer, []).append(i)
    return index


def kmer_positions(seq: str, query: str) -> List[int]:
    """Return all start positions of *query* in *seq* (exact match)."""
    positions = []
    start = 0
    while True:
        pos = seq.find(query, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1
    return positions


# ---------------------------------------------------------------------------
# Sliding window generator
# ---------------------------------------------------------------------------

def sliding_windows(
    seq: str,
    min_len: int,
    max_len: int,
    step: int = 1,
) -> Iterator[Tuple[str, int, int]]:
    """
    Yield (subsequence, start, end) for all windows of length min_len..max_len.

    Iterates outer loop over positions, inner loop over lengths so that
    all windows starting at the same position are yielded together —
    cache-friendly for position-indexed scoring.
    """
    n = len(seq)
    for pos in range(0, n, step):
        for length in range(min_len, max_len + 1):
            end = pos + length
            if end > n:
                break
            yield seq[pos:end], pos, end


# ---------------------------------------------------------------------------
# Both-strand sequence representation
# ---------------------------------------------------------------------------

class BothStrands(NamedTuple):
    """Convenience wrapper holding the forward and reverse-complement strands."""
    forward: str
    reverse: str   # reverse complement of forward

    @classmethod
    def from_sequence(cls, seq: str) -> "BothStrands":
        fwd = validate_sequence(seq)
        return cls(forward=fwd, reverse=reverse_complement(fwd))

    def __len__(self) -> int:
        return len(self.forward)
