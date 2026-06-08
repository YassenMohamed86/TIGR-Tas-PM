import pytest
from modules.specificity_engine import (
    count_mismatches, count_seed_mismatches, scan_offtargets,
    compute_specificity_score, OffTargetHit
)

SPACER = "ATCGATCGC"
SEQ_NO_OT = "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
SEQ_WITH_OT = "ATCGATCGCTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"

def test_zero_mismatches_identical():
    assert count_mismatches("ATCGATCGC", "ATCGATCGC") == 0

def test_correct_mismatch_count():
    assert count_mismatches("ATCGATCGC", "ATCGTTCGC") == 1
    assert count_mismatches("ATCGATCGC", "TTCGTTCGC") == 2

def test_seed_mismatch_count():
    seed_mm = count_seed_mismatches("ATCGATCGC", "ATCTATCGC")
    assert seed_mm == 1
    non_seed_mm = count_seed_mismatches("ATCGATCGC", "ATCGATCGT")
    assert non_seed_mm == 0

def test_exact_match_detected():
    hits = scan_offtargets(SPACER, SEQ_WITH_OT, k=9)
    assert len(hits) > 0
    exact_hits = [h for h in hits if h.mismatch_count == 0]
    assert len(exact_hits) > 0
    assert exact_hits[0].risk_level == "HIGH"

def test_no_offtarget_on_dissimilar_sequence():
    hits = scan_offtargets(SPACER, SEQ_NO_OT, k=9)
    high_risk = [h for h in hits if h.risk_level == "HIGH"]
    assert len(high_risk) == 0

def test_exact_match_low_specificity_score():
    score = compute_specificity_score(SPACER, SEQ_WITH_OT, k=9)
    assert score <= 0.2

def test_no_offtarget_high_specificity():
    score = compute_specificity_score(SPACER, SEQ_NO_OT, k=9)
    assert score == 1.0
