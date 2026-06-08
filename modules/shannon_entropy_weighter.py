"""
TIGR-Tas Dual-Guide RNA Scoring Platform — Shannon Entropy Weighter
===================================================================

SELF-AUDIT
----------
Module purpose : Compute empirical composite weights using Shannon Entropy.
Evidence level : Shannon entropy weights are [PARAMETER_UNRESOLVED] —
                 derived empirically at runtime, not from biological data.
Magic numbers  : NONE — fallback weights are 0.25 each (equal).
Cross-imports  : Imports ScoredPair from results_assembler only.
eval/exec      : NONE.
Type annotations: Complete on all public functions.
- [x] Computes empirical composite weights using Shannon Entropy.
- [x] Resolves the PARAMETER_UNRESOLVED final_score.
"""

import math
from typing import List, Tuple
from modules.results_assembler import ScoredPair

def calculate_entropy_weights(candidates: List[ScoredPair]) -> Tuple[float, float, float, float]:
    """
    Calculates dynamic weights for the 4 scoring models using Shannon Entropy.
    Returns weights for: (geometry, cleavage, stability, specificity).
    
    A model with high variance (discriminative) gets a higher weight.
    A model where every candidate scores the same gets zero weight.
    """
    n = len(candidates)
    if n <= 1:
        return (0.25, 0.25, 0.25, 0.25)
        
    scores_g = []
    scores_c = []
    scores_stab = []
    scores_spec = []
    
    for c in candidates:
        scores_g.append(c.geometry_score)
        scores_c.append(c.cleavage_score)
        # Combine dual scores for stability and specificity (average)
        scores_stab.append((c.stability_score_a + c.stability_score_b) / 2.0)
        scores_spec.append((c.specificity_score_a + c.specificity_score_b) / 2.0)
        
    def get_weight(scores: List[float]) -> float:
        total = sum(scores)
        if total == 0:
            return 0.0
            
        entropy = 0.0
        for s in scores:
            if s > 0:
                p = s / total
                entropy -= p * math.log(p)
                
        # Normalize by max possible entropy (ln(n))
        max_entropy = math.log(n)
        if max_entropy == 0:
            return 0.0
            
        e_norm = entropy / max_entropy
        return max(0.0, 1.0 - e_norm)  # Degree of diversification

    d_g = get_weight(scores_g)
    d_c = get_weight(scores_c)
    d_stab = get_weight(scores_stab)
    d_spec = get_weight(scores_spec)
    
    total_d = d_g + d_c + d_stab + d_spec
    if total_d == 0:
        return (0.25, 0.25, 0.25, 0.25)
        
    return (d_g / total_d, d_c / total_d, d_stab / total_d, d_spec / total_d)

def apply_weights(candidates: List[ScoredPair]) -> None:
    """Modifies the candidates in-place to calculate final_score."""
    if not candidates:
        return
        
    w_g, w_c, w_stab, w_spec = calculate_entropy_weights(candidates)
    
    for c in candidates:
        if c.error:
            c.final_score = 0.0
            continue
            
        avg_stab = (c.stability_score_a + c.stability_score_b) / 2.0
        avg_spec = (c.specificity_score_a + c.specificity_score_b) / 2.0
        
        fs = (
            w_g * c.geometry_score +
            w_c * c.cleavage_score +
            w_stab * avg_stab +
            w_spec * avg_spec
        )
        c.final_score = fs
        
        # Remove ASSUMP-009 since weights are now resolved
        c.assumption_warnings = [w for w in c.assumption_warnings if "ASSUMP-009" not in w]
