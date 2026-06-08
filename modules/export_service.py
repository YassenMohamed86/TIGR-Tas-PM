"""
TIGR-Tas Dual-Guide RNA Scoring Platform — Export Service
=========================================================

SELF-AUDIT
----------
Module purpose : Convert ScoredPairs to CSV, JSON, and FASTA export formats.
Evidence level : N/A — pure data transformation, no biological constants.
                 No [ESTABLISHED] or [HYPOTHESIS] parameters used.
Magic numbers  : NONE.
Cross-imports  : Imports ScoredPair from results_assembler only.
eval/exec      : NONE.
Type annotations: Present on all public functions.
Test data cat. : CATEGORY 2 (synthetic).
"""

import csv
import json
import io
from typing import List
from modules.results_assembler import ScoredPair

def export_to_csv(candidates: List[ScoredPair]) -> str:
    """Exports candidates to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "Rank", "Spacer A", "Spacer B", "Pos A", "Pos B", "Distance", 
        "Strand A", "Strand B", "GC A", "GC B", 
        "Geometry Score", "Cleavage Score", "Stability A", "Stability B",
        "Specificity A", "Specificity B", "Final Score"
    ]
    writer.writerow(headers)
    
    for i, c in enumerate(candidates):
        writer.writerow([
            i + 1,
            c.spacer_a, c.spacer_b, c.pos_a, c.pos_b, c.distance,
            c.strand_a, c.strand_b, f"{c.gc_a:.2f}", f"{c.gc_b:.2f}",
            f"{c.geometry_score:.3f}", f"{c.cleavage_score:.3f}", 
            f"{c.stability_score_a:.3f}", f"{c.stability_score_b:.3f}",
            f"{c.specificity_score_a:.3f}", f"{c.specificity_score_b:.3f}",
            f"{c.final_score:.3f}" if c.final_score is not None else "N/A"
        ])
        
    return output.getvalue()

def export_to_json(candidates: List[ScoredPair]) -> str:
    """Exports candidates to JSON format."""
    # Convert dataclass to dict
    data = []
    for c in candidates:
        d = c.__dict__.copy()
        data.append(d)
        
    return json.dumps(data, indent=2)

def export_to_fasta(candidates: List[ScoredPair]) -> str:
    """Exports candidates to FASTA format."""
    output = io.StringIO()
    
    for i, c in enumerate(candidates):
        output.write(f">Candidate_{i+1}_A pos={c.pos_a} strand={c.strand_a}\n")
        output.write(f"{c.spacer_a}\n")
        output.write(f">Candidate_{i+1}_B pos={c.pos_b} strand={c.strand_b}\n")
        output.write(f"{c.spacer_b}\n")
        
    return output.getvalue()
