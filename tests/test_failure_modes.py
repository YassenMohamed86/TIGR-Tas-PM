import pytest
from modules.sequence_service import parse_raw_sequence, SequenceValidationError
from modules.candidate_generator import generate_candidate_pairs
from modules.geometry_model import compute_geometry_score
from modules.cleavage_model import compute_cleavage_score
from modules.thermodynamics_model import compute_stability_score
from modules.specificity_engine import compute_specificity_score
from modules.results_assembler import assemble_results

def test_fm_1_sequence_service_ambiguous_base():
    with pytest.raises(SequenceValidationError):
        parse_raw_sequence("ATCGNNATCG")

def test_fm_2_candidate_generator_no_valid_pairs():
    # Sequence too short to generate pairs
    seq = parse_raw_sequence("ATCGATCGATCG")
    pairs = generate_candidate_pairs(seq, k=9)
    assert len(pairs) == 0

def test_fm_3_geometry_model_reversed_spacers():
    # pos_b < pos_a should fail gracefully or negative gap phase
    score = compute_geometry_score(pos_a=20, pos_b=5)
    # the function uses abs(), so score is calculated but it shouldn't crash
    assert score > 0

def test_fm_4_cleavage_model_short_spacer():
    # k < CAS9_CLEAVAGE_OFFSET
    # offset is 3, k=2
    score = compute_cleavage_score(pos_a=0, pos_b=10, k=2)
    assert score > 0

def test_fm_5_thermodynamics_model_zero_length():
    score = compute_stability_score("")
    assert score == 0.0

def test_fm_6_specificity_engine_empty_sequence():
    score = compute_specificity_score("ATCG", "", k=4)
    assert score == 1.0

def test_fm_7_results_assembler_empty_candidates():
    seq = "ATCGATCGATCG"
    results = assemble_results([], seq, k=9)
    assert len(results) == 0
