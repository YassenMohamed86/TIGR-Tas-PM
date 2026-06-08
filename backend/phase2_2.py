import sys, os
sys.path.insert(0, os.getcwd())

from app.offtarget.scoring.mit.aggregate_scorer import MITAggregateScorer
from app.offtarget.scoring.mit.mit_scorer import MITScorer

agg = MITAggregateScorer()
mit = MITScorer()

checks = {
    "zero_offtargets_returns_1.0":
        abs(agg.compute_aggregate([]) - 1.0) < 0.001,
    "formula_correct_known_input":
        abs(agg.compute_aggregate([0.5, 0.3, 0.2]) - (100/(100+1.0))) < 0.0001,
    "10000_offtargets_still_in_0_1":
        0.0 <= agg.compute_aggregate([1.0]*10000) <= 1.0,
    "zero_mm_site_score_1.0":
        abs(mit.score_site([]) - 1.0) < 0.001,
    "pos1_mismatch_lt_0.1":
        mit.score_site([1]) < 0.1,
    "pos20_mismatch_gt_0.5":
        mit.score_site([20]) > 0.5,
    "monotonic_more_mm_lower_score":
        mit.score_site([]) > mit.score_site([10]) > mit.score_site([9,10]) > mit.score_site([8,9,10]),
    "published_ts25_ot8_approx_0.21":
        0.15 <= mit.score_site([16,17,18]) <= 0.30,
}

for name, passed in checks.items():
    print(f"PASS: MIT - {name}" if passed else f"FAIL: MIT - {name}")

if not all(checks.values()):
    sys.exit("MIT FORMULA FAILURES — certification blocked")
