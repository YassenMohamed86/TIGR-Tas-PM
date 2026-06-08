import pytest
from modules.cleavage_model import compute_cut_position, compute_overhang, compute_cleavage_score

def test_compute_cut_position():
    assert compute_cut_position(10, 9) == 16  # 10 + (9 - 3) = 16

def test_compute_overhang():
    assert compute_overhang(10, 20, 9) == 10  # cut_a=16, cut_b=26, abs(26-16)=10

def test_compute_cleavage_score_optimal():
    # Overhang in [7, 9] -> 1.0
    assert compute_cleavage_score(0, 8, 9) == 1.0  # overhang 8

def test_compute_cleavage_score_acceptable():
    # Overhang in [5, 7) or (9, 12] -> 0.6
    assert compute_cleavage_score(0, 6, 9) == 0.6  # overhang 6
    assert compute_cleavage_score(0, 11, 9) == 0.6 # overhang 11

def test_compute_cleavage_score_poor():
    # Otherwise -> 0.2
    assert compute_cleavage_score(0, 4, 9) == 0.2  # overhang 4
    assert compute_cleavage_score(0, 15, 9) == 0.2 # overhang 15
