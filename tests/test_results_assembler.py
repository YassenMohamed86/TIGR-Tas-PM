"""
test_results_assembler.py — Unit Tests for Results Assembly
===========================================================

All test data is CATEGORY 2 (synthetic) — no biological sequences.
"""

from __future__ import annotations

import pytest

from modules.candidate_generator import CandidatePair
from modules.results_assembler import ScoredPair, assemble_results


# ---------------------------------------------------------------------------
# CATEGORY 2 (synthetic) test data
# ---------------------------------------------------------------------------

def _make_pair(
    spacer_a: str = "ATCGATCGA",
    spacer_b: str = "TCGATCGAT",
    pos_a: int = 0,
    pos_b: int = 10,
    gc_a: float = 0.444,
    gc_b: float = 0.444,
    distance: int = 10,
) -> CandidatePair:
    """Convenience factory for synthetic CandidatePair objects."""
    return CandidatePair(
        spacer_a=spacer_a,
        spacer_b=spacer_b,
        pos_a=pos_a,
        pos_b=pos_b,
        strand_a="+",
        strand_b="+",
        gc_a=gc_a,
        gc_b=gc_b,
        distance=distance,
    )


_SYNTHETIC_SEQ: str = "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_empty_candidates_returns_empty() -> None:
    """assemble_results([]) must return an empty list."""
    results = assemble_results([], "ATCGATCG", k=9)
    assert results == []


def test_single_pair_scored_correctly() -> None:
    """A single synthetic pair should produce exactly one ScoredPair."""
    pair = _make_pair()
    results = assemble_results([pair], _SYNTHETIC_SEQ, k=9)

    assert len(results) == 1
    r = results[0]
    assert 0.0 <= r.geometry_score <= 1.0
    assert 0.0 <= r.cleavage_score <= 1.0
    assert 0.0 <= r.stability_score_a <= 1.0
    assert 0.0 <= r.stability_score_b <= 1.0


def test_assumption_warnings_populated() -> None:
    """Every scored pair must surface assumption warnings."""
    pair = _make_pair()
    results = assemble_results([pair], _SYNTHETIC_SEQ, k=9)
    assert len(results[0].assumption_warnings) > 0


def test_final_score_is_none() -> None:
    """final_score is PARAMETER_UNRESOLVED and must be None."""
    pair = _make_pair()
    results = assemble_results([pair], _SYNTHETIC_SEQ, k=9)
    assert results[0].final_score is None


def test_all_scores_in_valid_range() -> None:
    """All six sub-scores must lie in [0, 1]."""
    pair = _make_pair(
        spacer_a="GCGATCGAT",
        spacer_b="ATCGATCGC",
        pos_a=0,
        pos_b=15,
        gc_a=0.556,
        gc_b=0.556,
        distance=15,
    )
    seq = "GCGATCGATATCGATCGATCGATCGATCGATCGATCGATCG"
    results = assemble_results([pair], seq, k=9)
    r = results[0]

    for score_name in [
        "geometry_score",
        "cleavage_score",
        "stability_score_a",
        "stability_score_b",
        "specificity_score_a",
        "specificity_score_b",
    ]:
        val = getattr(r, score_name)
        assert 0.0 <= val <= 1.0, f"{score_name} = {val} out of range"
