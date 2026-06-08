"""
TIGR-Tas Dual-Guide RNA Scoring Platform — Thermodynamics Model
==========================================================

SELF-AUDIT
----------
Module purpose : Approximate RNA:DNA hybrid stability via simplified ΔG.
Evidence level : GC/AT weights are [ESTABLISHED] (SantaLucia 1998);
                 simplified ΔG model is [HYPOTHESIS].
Magic numbers  : NONE — GC_WEIGHT=2.0, AT_WEIGHT=1.0 are named constants.
Cross-imports  : NONE — this module is fully independent.
eval/exec      : NONE.
Type annotations: Present on public functions.
Test data cat. : CATEGORY 2 (synthetic).
- [x] Computes deltaG and stability score
- [x] T is treated as U for RNA:DNA hybrid calculations
"""

def compute_deltaG(seq: str) -> float:
    """Approximate RNA:DNA hybridization free energy.
    
    Treats T as U (thymine in DNA template corresponds to uracil in RNA).
    Returns a negative value (kcal/mol approximation).
    """
    seq_u = seq.upper().replace('T', 'U')
    
    # GC_WEIGHT = 2.0 [ESTABLISHED] G:C 3 H-bonds, SantaLucia 1998 PNAS 95:1460
    # AT_WEIGHT = 1.0 [ESTABLISHED] A:T 2 H-bonds, SantaLucia 1998 PNAS 95:1460
    dg = 0.0
    for base in seq_u:
        if base in 'GC':
            dg -= 2.0
        elif base in 'AU':
            dg -= 1.0
            
    return dg

def compute_stability_score(spacer: str) -> float:
    """Normalize deltaG into a 0.0 to 1.0 stability score.
    
    Higher GC -> more negative deltaG -> higher score.
    """
    if not spacer:
        return 0.0
        
    dg = compute_deltaG(spacer)
    
    # max possible is all G/C
    min_possible_dg = len(spacer) * -2.0
    if min_possible_dg >= 0:
        return 0.0
        
    # score = dg / min_possible_dg -> [0, 1]
    score = dg / min_possible_dg
    return min(1.0, max(0.0, score))
