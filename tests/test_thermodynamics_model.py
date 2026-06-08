import pytest
from modules.thermodynamics_model import compute_deltaG, compute_stability_score

def test_high_gc_higher_stability():
    low_gc = compute_stability_score("AUAUAUAUA")
    high_gc = compute_stability_score("GCGCGCGCG")
    assert high_gc > low_gc

def test_t_treated_as_u():
    dg_with_t = compute_deltaG("ATATATATA")
    dg_with_u = compute_deltaG("AUAUAUAUA")
    assert abs(dg_with_t - dg_with_u) < 0.001
