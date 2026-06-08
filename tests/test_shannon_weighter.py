import pytest
from modules.shannon_entropy_weighter import calculate_entropy_weights, apply_weights
from modules.results_assembler import ScoredPair
import math

def test_entropy_weights_uniform_scores():
    # If all scores are equal, entropy is max, so weights should be equal
    c1 = ScoredPair(spacer_a="", spacer_b="", pos_a=1, pos_b=10, strand_a="+", strand_b="+", gc_a=0.5, gc_b=0.5, distance=10,
                    geometry_score=0.5, cleavage_score=0.5, stability_score_a=0.5, stability_score_b=0.5,
                    specificity_score_a=0.5, specificity_score_b=0.5)
    c2 = ScoredPair(spacer_a="", spacer_b="", pos_a=2, pos_b=11, strand_a="+", strand_b="+", gc_a=0.5, gc_b=0.5, distance=10,
                    geometry_score=0.5, cleavage_score=0.5, stability_score_a=0.5, stability_score_b=0.5,
                    specificity_score_a=0.5, specificity_score_b=0.5)
    w_g, w_c, w_stab, w_spec = calculate_entropy_weights([c1, c2])
    
    assert math.isclose(w_g, 0.25, rel_tol=1e-5)
    assert math.isclose(w_c, 0.25, rel_tol=1e-5)
    assert math.isclose(w_stab, 0.25, rel_tol=1e-5)
    assert math.isclose(w_spec, 0.25, rel_tol=1e-5)

def test_entropy_weights_high_variance():
    # If one model has high variance (one candidate 1.0, other 0.0), it should get higher weight
    c1 = ScoredPair(spacer_a="", spacer_b="", pos_a=1, pos_b=10, strand_a="+", strand_b="+", gc_a=0.5, gc_b=0.5, distance=10,
                    geometry_score=1.0, cleavage_score=0.5, stability_score_a=0.5, stability_score_b=0.5,
                    specificity_score_a=0.5, specificity_score_b=0.5)
    c2 = ScoredPair(spacer_a="", spacer_b="", pos_a=2, pos_b=11, strand_a="+", strand_b="+", gc_a=0.5, gc_b=0.5, distance=10,
                    geometry_score=0.1, cleavage_score=0.5, stability_score_a=0.5, stability_score_b=0.5,
                    specificity_score_a=0.5, specificity_score_b=0.5)
                    
    w_g, w_c, w_stab, w_spec = calculate_entropy_weights([c1, c2])
    
    assert w_g > w_c
    assert math.isclose(w_c, w_stab)
    assert math.isclose(w_stab, w_spec)

def test_apply_weights():
    c1 = ScoredPair(spacer_a="", spacer_b="", pos_a=1, pos_b=10, strand_a="+", strand_b="+", gc_a=0.5, gc_b=0.5, distance=10,
                    geometry_score=1.0, cleavage_score=1.0, stability_score_a=1.0, stability_score_b=1.0,
                    specificity_score_a=1.0, specificity_score_b=1.0)
    c2 = ScoredPair(spacer_a="", spacer_b="", pos_a=2, pos_b=11, strand_a="+", strand_b="+", gc_a=0.5, gc_b=0.5, distance=10,
                    geometry_score=0.5, cleavage_score=0.5, stability_score_a=0.5, stability_score_b=0.5,
                    specificity_score_a=0.5, specificity_score_b=0.5)
                    
    apply_weights([c1, c2])
    
    assert c1.final_score is not None
    assert c2.final_score is not None
    # If all have same variance, weights are 0.25, so c1=1.0, c2=0.5
    assert math.isclose(c1.final_score, 1.0, rel_tol=1e-5)
    assert math.isclose(c2.final_score, 0.5, rel_tol=1e-5)
