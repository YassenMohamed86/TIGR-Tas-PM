import pytest
import math
from modules.geometry_model import compute_geometry_score

def test_geometry_score_gap_21():
    # gap=21: phase=21%10.5=0.0, score=1.0
    score = compute_geometry_score(0, 21)
    assert math.isclose(score, 1.0, rel_tol=1e-5)

def test_geometry_score_gap_10():
    # gap=10: phase=10%10.5=10.0, with wrap: phase=10.5-10=0.5, score≈0.97
    score = compute_geometry_score(0, 10)
    expected = math.exp(-(0.5 ** 2) / (2 * 2.0 ** 2))
    assert math.isclose(score, expected, rel_tol=1e-5)

def test_geometry_score_gap_5():
    # gap=5: phase=5%10.5=5.0, no wrap needed (5<5.25), score=exp(-25/8)≈0.044
    score = compute_geometry_score(0, 5)
    expected = math.exp(-(5.0 ** 2) / (2 * 2.0 ** 2))
    assert math.isclose(score, expected, rel_tol=1e-5)

def test_geometry_score_gap_0():
    # gap=0: phase=0, score=1.0
    score = compute_geometry_score(0, 0)
    assert math.isclose(score, 1.0, rel_tol=1e-5)
