import sys

# 2.1 CFD
try:
    from app.offtarget.scoring.cfd.cfd_scorer import CFDScorer
    scorer = CFDScorer()
    # Test perfect match
    score = scorer.score("GCACTGACGTCAAGACCCCA", "GCACTGACGTCAAGACCCCA", "CGG")
    assert abs(score - 1.0) < 0.001, f"CFD perfect match failed: {score}"
    
    # PAM-distal mismatch (pos 20)
    score = scorer.score("GGGGGGGGGGGGGGGGGGGG".replace("T","U"), "GGGGGGGGGGGGGGGGGGAG", "CGG")
    assert score > 0.5, f"CFD PAM-distal failed: {score}"
    
    # Seed mismatch
    seed_score = scorer.score("GGGGGGGGGGGGGGGGGGGG".replace("T","U"), "GGGGGGGGGGGGGGGGGGAG"[::-1][:20], "CGG")
    assert seed_score < 0.3, f"CFD Seed failed: {seed_score}"
    
    # NAG vs NGG
    nag = scorer.score("GCACTGACGTCAAGACCCCA","GCACTGACGTCAAGACCCCA","CAG")
    ngg = scorer.score("GCACTGACGTCAAGACCCCA","GCACTGACGTCAAGACCCCA","CGG")
    assert nag < ngg, f"CFD NAG vs NGG failed: {nag} >= {ngg}"
    
    print("PASS: CFD")
except Exception as e:
    print(f"FAIL: CFD - {e}")

# 2.2 MIT
try:
    from app.offtarget.scoring.mit.aggregate_scorer import MITAggregateScorer
    from app.offtarget.scoring.mit.mit_scorer import MITScorer

    agg = MITAggregateScorer()
    mit = MITScorer()
    
    assert abs(agg.compute_aggregate([]) - 1.0) < 0.001
    assert abs(agg.compute_aggregate([0.5, 0.3, 0.2]) - (100/(100+1.0))) < 0.0001
    
    assert abs(mit.score_site([]) - 1.0) < 0.001
    assert mit.score_site([1]) < 0.1
    assert mit.score_site([20]) > 0.5
    assert mit.score_site([]) > mit.score_site([10]) > mit.score_site([9,10]) > mit.score_site([8,9,10])
    
    score_16_17_18 = mit.score_site([16,17,18])
    assert 0.15 <= score_16_17_18 <= 0.30, f"MIT score [16,17,18] out of bounds: {score_16_17_18}"
    
    print("PASS: MIT")
except Exception as e:
    print(f"FAIL: MIT - {e}")

# 2.3 Shannon
try:
    import numpy as np
    from app.scoring.shannon_entropy_weighter import compute_shannon_weights, apply_shannon_weights
    
    M = np.random.rand(5, 4)
    r = compute_shannon_weights(M)
    assert abs(sum(r.weights.values()) - 1.0) < 1e-9
    
    M_uniform = np.full((20, 4), 0.5)
    r_uniform = compute_shannon_weights(M_uniform)
    assert abs(r_uniform.weights[0] - 0.25) < 1e-9
    
    print("PASS: Shannon")
except Exception as e:
    print(f"FAIL: Shannon - {e}")

# 2.4 C-5 Rule
try:
    from app.export.assembly.cleavage_site_calculator import CleavageSiteCalculator
    from app.scoring.cleavage_model import compute_cut_position, C5_CLEAVAGE_OFFSET
    
    calc = CleavageSiteCalculator()
    for start in [0, 5, 50, 100]:
        assert calc.compute_cleavage_offset_spacer_a(start) == start + 5
        # wait, we updated compute_cut_position in app.scoring.cleavage_model ?
        assert compute_cut_position(start, k=18) == start + 5
        
    print("PASS: C-5 Rule")
except Exception as e:
    print(f"FAIL: C-5 Rule - {e}")
