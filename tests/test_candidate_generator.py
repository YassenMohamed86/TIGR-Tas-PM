import pytest
from modules.sequence_service import parse_raw_sequence
from modules.candidate_generator import generate_candidate_pairs, CandidatePair

# All test data is CATEGORY 2 (synthetic).
SEQ = parse_raw_sequence("ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG")

def test_returns_list_of_pairs():
    pairs = generate_candidate_pairs(SEQ)
    assert isinstance(pairs, list)
    assert len(pairs) > 0
    assert all(isinstance(p, CandidatePair) for p in pairs)
    print(f"PASS: generated {len(pairs)} candidate pairs")

def test_distances_within_bounds():
    pairs = generate_candidate_pairs(SEQ, d_min=5, d_max=20)
    for p in pairs:
        assert 5 <= p.distance <= 20, (
            f"Distance {p.distance} out of range [5, 20] "
            f"for pair ({p.spacer_a}, {p.spacer_b})"
        )
    print("PASS: all distances within configured bounds")

def test_gc_within_bounds():
    pairs = generate_candidate_pairs(SEQ, gc_min=0.30, gc_max=0.70)
    for p in pairs:
        assert 0.30 <= p.gc_a <= 0.70, f"GC of spacer A out of range: {p.gc_a:.2f}"
        assert 0.30 <= p.gc_b <= 0.70, f"GC of spacer B out of range: {p.gc_b:.2f}"
    print("PASS: all GC contents within configured bounds")

def test_no_ambiguous_bases():
    valid = set("ATCG")
    pairs = generate_candidate_pairs(SEQ)
    for p in pairs:
        assert set(p.spacer_a).issubset(valid), f"Invalid base in spacer A: {p.spacer_a}"
        assert set(p.spacer_b).issubset(valid), f"Invalid base in spacer B: {p.spacer_b}"
    print("PASS: no ambiguous bases in generated pairs")
