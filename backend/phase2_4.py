import sys, os
sys.path.insert(0, os.getcwd())

from app.export.assembly.cleavage_site_calculator import CleavageSiteCalculator
from app.scoring.cleavage_model import compute_cut_position, C5_CLEAVAGE_OFFSET

calc = CleavageSiteCalculator()
failures = []

# C-5 rule: offset = spacer_start + 5
for start in [0, 5, 50, 100, 1000, 41246000]:
    expected = start + 5
    got_calc  = calc.compute_cleavage_offset_spacer_a(start)
    got_model = compute_cut_position(start, k=18)

    if got_calc != expected:
        failures.append(f"Calculator: C-5 rule violated — start={start}, expected={expected}, got={got_calc}")
    if got_model != expected:
        failures.append(f"Model: C-5 rule violated — start={start}, expected={expected}, got={got_model}")

if C5_CLEAVAGE_OFFSET != 5:
    failures.append(f"C5_CLEAVAGE_OFFSET = {C5_CLEAVAGE_OFFSET}, must be 5 [Faure 2025]")

print(f"C-5 rule: {'PASS — 6 positions verified' if not failures else 'FAIL'}")
for f in failures:
    print(f"  FAIL: {f}")
if failures:
    sys.exit("C-5 CLEAVAGE RULE VIOLATIONS — patient safety risk")
