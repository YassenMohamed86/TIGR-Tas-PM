"""
test_integration.py — End-to-End Pipeline Integration Tests
============================================================

Exercises the full pipeline: parse_raw_sequence → generate_candidate_pairs
→ assemble_results.

All test data is CATEGORY 2 (synthetic) — no biological sequences.
"""

from __future__ import annotations

import pytest

from modules.sequence_service import parse_raw_sequence
from modules.candidate_generator import generate_candidate_pairs
from modules.results_assembler import ScoredPair, assemble_results

# ---------------------------------------------------------------------------
# CATEGORY 2 (synthetic) test sequence — 60 nt repeating pattern
# ---------------------------------------------------------------------------
TEST_SEQ: str = (
    "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

def test_full_pipeline_produces_results() -> None:
    """The complete pipeline must yield at least one ScoredPair."""
    seq_obj = parse_raw_sequence(TEST_SEQ)
    candidates = generate_candidate_pairs(seq_obj, k=9, d_min=5, d_max=30)
    results = assemble_results(candidates, seq_obj.sequence, k=9)

    assert len(results) > 0
    assert all(isinstance(r, ScoredPair) for r in results)


def test_all_scores_in_valid_range() -> None:
    """Every sub-score must lie in [0.0, 1.0]."""
    seq_obj = parse_raw_sequence(TEST_SEQ)
    candidates = generate_candidate_pairs(seq_obj, k=9)
    results = assemble_results(candidates, seq_obj.sequence, k=9)

    for r in results:
        assert 0.0 <= r.geometry_score <= 1.0
        assert 0.0 <= r.cleavage_score <= 1.0
        assert 0.0 <= r.stability_score_a <= 1.0
        assert 0.0 <= r.stability_score_b <= 1.0
        assert 0.0 <= r.specificity_score_a <= 1.0
        assert 0.0 <= r.specificity_score_b <= 1.0


def test_final_score_always_none() -> None:
    """final_score is PARAMETER_UNRESOLVED — must be None for every pair."""
    seq_obj = parse_raw_sequence(TEST_SEQ)
    candidates = generate_candidate_pairs(seq_obj, k=9, d_min=5, d_max=15)
    results = assemble_results(candidates, seq_obj.sequence, k=9)

    for r in results:
        assert r.final_score is None


def test_warnings_present_on_all_results() -> None:
    """Every ScoredPair must carry at least one assumption warning."""
    seq_obj = parse_raw_sequence(TEST_SEQ)
    candidates = generate_candidate_pairs(seq_obj, k=9, d_min=5, d_max=15)
    results = assemble_results(candidates, seq_obj.sequence, k=9)

    for r in results:
        assert len(r.assumption_warnings) > 0
