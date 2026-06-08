import sys, os
sys.path.insert(0, os.getcwd())

from app.offtarget.scoring.cfd.cfd_scorer import CFDScorer
scorer = CFDScorer()

cases = [
    ('GCACTGACGTCAAGACCCCA', 'GCACTGACGTCAAGACCCCA', 'CGG', (0.999, 1.001), 'Perfect match must return 1.0'),
    ('GGGGGGGGGGGGGGGGGGGG', 'GGGGGGGGGGGGGGGGGGAG', 'CGG', (0.5, 1.0),     'PAM-distal mismatch (pos 20) must score > 0.5'),
    ('GGGGGGGGGGGGGGGGGGGG', 'GGGGGGGGGGGGGGGGGGAG'[::-1][:20], 'CGG', None, 'Seed mismatch score (pos 2) must score < 0.3'),
    ('GCACTGACGTCAAGACCCCA', 'GCACTGACGTCAAGACCCCA', 'CAG', (0.0, 0.99),    'NAG PAM must score lower than NGG'),
]

seed_score = scorer.score(
    guide_rna='GGGGGGGGGGGGGGGGGGGG'.replace('T','U'),
    target_dna='GGGGGGGGGGGGGGGGGGAG',
    pam='CGG'
)

results = {
    'perfect_match_1.0':     abs(scorer.score('GCACUGACGUCAAGACCCCA', 'GCACTGACGTCAAGACCCCA', 'CGG') - 1.0) < 0.001,
    'pam_distal_gt_0.5':     scorer.score('GGGGGGGGGGGGGGGGGGG'.replace('T','U')+'G', 'AGGGGGGGGGGGGGGGGGGGG'[:20], 'CGG') > 0.5,
    'seed_mismatch_lt_0.3':  seed_score < 0.3,
    'nag_lt_ngg':            scorer.score('GCACUGACGUCAAGACCCCA','GCACTGACGTCAAGACCCCA','CAG') <
                             scorer.score('GCACUGACGUCAAGACCCCA','GCACTGACGTCAAGACCCCA','CGG'),
    '1000_random_in_0_1':    True,
}

import random
bases = 'ATCG'
for _ in range(1000):
    g = ''.join(random.choice(bases) for _ in range(20)).replace('T','U')
    t = ''.join(random.choice(bases) for _ in range(20))
    s = scorer.score(g, t, 'CGG')
    if not 0.0 <= s <= 1.0:
        results['1000_random_in_0_1'] = False
        break

for name, passed in results.items():
    print(f"PASS: CFD - {name}" if passed else f"FAIL: CFD - {name}")

if not all(results.values()):
    sys.exit('CFD FORMULA FAILURES DETECTED — certification blocked')
