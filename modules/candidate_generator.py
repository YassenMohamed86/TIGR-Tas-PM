"""
TIGR-Tas Dual-Guide RNA Scoring Platform — Candidate Generator Module
==================================================================

SELF-AUDIT
----------
- [x] Generates candidate pairs of spacer A and B.
- [x] Checks GC content and distance constraints.
- [x] No scoring logic present.
- [x] CandidatePair dataclass defined exactly as specified.
- [x] Type annotations on all functions.
"""

from dataclasses import dataclass
from typing import List

from modules.sequence_service import SequenceObject, _reverse_complement


@dataclass
class CandidatePair:
    spacer_a: str
    spacer_b: str
    pos_a: int
    pos_b: int
    strand_a: str
    strand_b: str
    gc_a: float
    gc_b: float
    distance: int


def _gc_content(seq: str) -> float:
    """Calculate GC content of a sequence as a float between 0 and 1."""
    if not seq:
        return 0.0
    return sum(1 for base in seq if base in "GC") / len(seq)


def generate_candidate_pairs(
    sequence_obj: SequenceObject,
    k: int = 9,
    d_min: int = 5,        # [HYPOTHESIS] Minimum inter-guide distance
    d_max: int = 50,       # [HYPOTHESIS] Maximum inter-guide distance
    gc_min: float = 0.30,  # [HYPOTHESIS] Minimum GC content filter
    gc_max: float = 0.70,  # [HYPOTHESIS] Maximum GC content filter
) -> List[CandidatePair]:
    """Generate all valid candidate guide pairs from a sequence.

    Constraints:
    - Distance d between spacers: d_min <= d <= d_max
    - GC content for each spacer: gc_min <= gc <= gc_max
    - Valid bases only.
    - Spacer B is downstream of Spacer A, and reverse complemented.
    """
    pairs: List[CandidatePair] = []
    seq: str = sequence_obj.sequence
    valid_bases = set("ATCG")

    for i in range(len(seq) - k + 1):
        spacer_a = seq[i : i + k]
        
        # Check invalid bases and GC content
        if not set(spacer_a).issubset(valid_bases):
            continue
        gc_a = _gc_content(spacer_a)
        if not (gc_min <= gc_a <= gc_max):
            continue

        # Spacer B must be downstream, starting at i + d_min
        for j in range(i + d_min, min(i + d_max + 1, len(seq) - k + 1)):
            spacer_b_fwd = seq[j : j + k]
            
            if not set(spacer_b_fwd).issubset(valid_bases):
                continue
                
            gc_b = _gc_content(spacer_b_fwd)
            if not (gc_min <= gc_b <= gc_max):
                continue

            spacer_b_rev = _reverse_complement(spacer_b_fwd)
            distance = j - i

            pairs.append(
                CandidatePair(
                    spacer_a=spacer_a,
                    spacer_b=spacer_b_rev,
                    pos_a=i,
                    pos_b=j,
                    strand_a="+",
                    strand_b="-",
                    gc_a=gc_a,
                    gc_b=gc_b,
                    distance=distance,
                )
            )

    return pairs
