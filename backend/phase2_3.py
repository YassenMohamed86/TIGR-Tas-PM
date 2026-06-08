import sys, os
sys.path.insert(0, os.getcwd())

import numpy as np
from app.scoring.shannon_entropy_weighter import compute_shannon_weights, apply_shannon_weights

failures = []

# Property 1: weights always sum to 1.0 for 500 random matrices
for trial in range(500):
    N = np.random.randint(2, 100)
    M = np.random.rand(N, 4)
    r = compute_shannon_weights(M)
    total = sum(r.weights.values())
    if abs(total - 1.0) > 1e-9:
        failures.append(f"Trial {trial}: weights sum = {total}")

# Property 2: composite scores always in [0,1]
for trial in range(200):
    N = np.random.randint(2, 50)
    M = np.random.rand(N, 4)
    r = compute_shannon_weights(M)
    c = apply_shannon_weights(M, r)
    if not (np.all(c >= 0) and np.all(c <= 1)):
        failures.append(f"Trial {trial}: composite out of [0,1]")

# Property 3: uniform scores → equal weights
M_uniform = np.full((20, 4), 0.5)
r_uniform  = compute_shannon_weights(M_uniform)
for w in r_uniform.weights.values():
    if abs(w - 0.25) > 1e-9:
        failures.append(f"Uniform input did not produce equal weights: {r_uniform.weights}")
        break

# Property 4: fallback for N=1
r_single = compute_shannon_weights(np.array([[0.8,0.6,0.7,0.9]]))
if not r_single.fallback_used:
    failures.append("N=1 input did not trigger fallback")

# Property 5: final_score is ALWAYS None in ScoredPairs
from app.scanner.input.sequence_validator import parse_raw_sequence
from app.scanner.pipeline.guide_scanner import GuideScannerOrchestrator
from app.scoring.results_assembler import assemble_results
scanner   = GuideScannerOrchestrator()
seq       = "GCACTGACGTCAAGACCCCA" * 3 + "CGG"
scan_r    = scanner.scan(seq, cas_variant_id="SpCas9")
if scan_r.candidates:
    seq_obj = parse_raw_sequence(seq)
    scored  = assemble_results(scan_r.candidates, seq_obj)
    for pair in scored:
        if pair.final_score is not None:
            failures.append(f"final_score is {pair.final_score!r}, must be None")
            break

print(f"Shannon entropy: {'PASS — ' + str(500+200+3) + ' checks' if not failures else 'FAIL'}")
for f in failures[:5]:
    print(f"  FAIL: {f}")
if failures:
    sys.exit(f"{len(failures)} Shannon entropy violations")
