import sys, os
sys.path.insert(0, os.getcwd())

import json, tempfile
from app.scanner.models.candidate_guide import CandidateGuide
from app.scanner.models.scan_result import ScanResult
from app.export.formats.json_exporter import JsonExporter
from app.export.formats.fasta_exporter import FastaExporter

SPACER_A = "AAAAAAAAAAAAAAAAAAA"
SPACER_B = "GGGGGGGGGGGGGGGGGGG"

guide = CandidateGuide(
    protospacer=SPACER_A, pam_sequence="NONE", pam_pattern="NONE",
    cas_variant_id="TIGR-Tas", guide_length=19, strand="+",
    chrom="chr1", start=100, end=119, gc_content=0.0,
    quality_flags=frozenset(), seed_sequence=SPACER_A[-8:],
    seed_gc_content=0.0, pam_position="dual",
)
if hasattr(guide, '__dict__'):
    guide.spacer_a = SPACER_A
    guide.spacer_b = SPACER_B

r = ScanResult(candidates=[guide], input_sequence="TEST",
               cas_variant_id="TIGR-Tas", total_found=1, scan_time_ms=1)

tmpdir = tempfile.mkdtemp()
failures = []

json_path = os.path.join(tmpdir, "swap_test.json")
JsonExporter().export(r, json_path)
data = json.loads(open(json_path).read())
c = data["candidates"][0]
if "spacer_a" in c and c["spacer_a"] and "G" in c["spacer_a"]:
    failures.append(f"JSON: spacer_a column contains G's — spacers are SWAPPED: {c['spacer_a']}")
if "spacer_b" in c and c["spacer_b"] and "A" == c["spacer_b"][0]:
    failures.append(f"JSON: spacer_b column starts with A — spacers may be SWAPPED: {c['spacer_b']}")

fa_path = os.path.join(tmpdir, "swap_test.fa")
FastaExporter().export(r, fa_path)
with open(fa_path) as f:
    fasta_content = f.read()

import re
if "spacerA=" in fasta_content:
    match = re.search(r"spacerA=([ACGT]+)", fasta_content)
    if match and "G" in match.group(1):
        failures.append(f"FASTA: spacerA= contains G — SWAPPED: {match.group(1)}")

import shutil; shutil.rmtree(tmpdir)

for f in failures:
    print(f"CRITICAL FAIL: SPACER SWAP — {f}")
if failures:
    sys.exit(f"SPACER A/B SWAP DETECTED IN {len(failures)} FORMAT(S).")
else:
    print("PASS: Spacer A/B not swapped in JSON and FASTA exports")
