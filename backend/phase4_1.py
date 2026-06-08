import sys, os
sys.path.insert(0, os.getcwd())

import json, tempfile
from app.scanner.pipeline.guide_scanner import GuideScannerOrchestrator
from app.scanner.input.sequence_validator import parse_raw_sequence
from app.scoring.results_assembler import assemble_results
from app.export.formats.json_exporter import JsonExporter
from app.export.formats.bed_exporter import BedExporter
from app.export.formats.fasta_exporter import FastaExporter
from app.export.validation.export_validator import ExportValidator
from app.scanner.models.scan_result import ScanResult

scanner   = GuideScannerOrchestrator()
validator = ExportValidator()

seq = ("GCACTGACGTCAAGACCCCA" + "CGG" +
       "ATCGATCGATCGATCGATCGATCGATCGATCGATCG" +
       "TGACGTCAAGACCCCA" + "CGG")

scan_result  = scanner.scan(seq, cas_variant_id="SpCas9")
assert len(scan_result.candidates) >= 1, "No candidates — adjust sequence"

seq_obj = parse_raw_sequence(seq)
scored  = assemble_results(scan_result.candidates, seq_obj)

sr = ScanResult(candidates=scan_result.candidates, input_sequence=seq,
                cas_variant_id="SpCas9", total_found=scan_result.total_found,
                scan_time_ms=10)

tmpdir = tempfile.mkdtemp()
paths  = {
    "json":  os.path.join(tmpdir, "test.json"),
    "bed":   os.path.join(tmpdir, "test.bed"),
    "fasta": os.path.join(tmpdir, "test.fa"),
}

JsonExporter().export(sr, paths["json"])
BedExporter().export(sr,  paths["bed"],  write_track_header=False)
FastaExporter().export(sr, paths["fasta"])

results = {
    "json_valid":    validator.validate_json(paths["json"]).is_valid,
    "bed_valid":     validator.validate_bed(paths["bed"]).is_valid,
    "fasta_valid":   validator.validate_fasta(paths["fasta"]).is_valid,
}

data      = json.loads(open(paths["json"]).read())
bed_rows  = sum(1 for l in open(paths["bed"])  if l.strip())
fa_headers= sum(1 for l in open(paths["fasta"]) if l.startswith(">"))

results["json_count_matches"] = data["total_found"] == scan_result.total_found
results["bed_count_matches"]  = bed_rows            == scan_result.total_found * 2 # Since BED has A and B lines
results["fasta_count_matches"]= fa_headers          == scan_result.total_found * 2

for c in data["candidates"]:
    if len(c["protospacer"]) != 20:
        results["protospacer_not_truncated"] = False
        break
else:
    results["protospacer_not_truncated"] = True

for c in data["candidates"]:
    if c.get("final_score") is not None:
        results["final_score_none_in_json"] = False
        break
else:
    results["final_score_none_in_json"] = True

with open(paths["bed"]) as f:
    first_line = f.readline().strip().split("\t")
bed_start = int(first_line[1])
results["bed_0_based"] = bed_start >= 0

import shutil
shutil.rmtree(tmpdir)

for name, passed in results.items():
    print(f"PASS: Integration - {name}" if passed else f"FAIL: Integration - {name}")

if not all(results.values()):
    sys.exit("Integration pipeline failures detected")
