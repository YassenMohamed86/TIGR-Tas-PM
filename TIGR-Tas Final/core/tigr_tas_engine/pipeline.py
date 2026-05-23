"""
pipeline.py — Top-level orchestration with optional parallel processing.

Ties all modules together into a single run() function:

  1. Validate and normalise the input sequence
  2. Detect spacer pairs (scanner)
  3. Score candidates in parallel (scoring)
  4. Rank and filter (scoring.rank_candidates)
  5. Run CRISPR-Cas9 comparison (comparison)
  6. Write outputs (reporter)
  7. Return PipelineResult for programmatic use

Parallelism is implemented with multiprocessing.Pool; the pool is only
created when there are enough candidates to justify the overhead.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from functools import partial
from multiprocessing import Pool, cpu_count
from typing import Dict, List, Optional, Tuple

from .comparison import compare_tigr_vs_crispr, find_crispr_sites, CrisprSite
from .constants import PARALLEL_CHUNK_SIZE, PipelineConfig
from .reporter import print_summary, write_csv, write_json
from .scanner import detect_spacer_pairs
from .scoring import ScoredCandidate, rank_candidates, score_candidate
from .sequence import validate_sequence


# ---------------------------------------------------------------------------
# Result data structure
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """All outputs from a single pipeline run."""
    ranked_candidates:   List[ScoredCandidate] = field(default_factory=list)
    crispr_sites:        List[CrisprSite] = field(default_factory=list)
    comparison_summary:  Dict = field(default_factory=dict)
    metadata:            Dict = field(default_factory=dict)
    csv_path:            Optional[str] = None
    json_path:           Optional[str] = None


# ---------------------------------------------------------------------------
# Worker function (must be module-level for multiprocessing pickling)
# ---------------------------------------------------------------------------

def _score_worker(
    pair,
    reference_seq: str,
    all_spacer_seqs: List[str],
    cfg: PipelineConfig,
) -> ScoredCandidate:
    return score_candidate(pair, reference_seq, all_spacer_seqs, cfg)


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run(
    sequence: str,
    sequence_name: str = "input",
    cfg: Optional[PipelineConfig] = None,
    output_dir: Optional[str] = None,
    write_outputs: bool = True,
    verbose: bool = True,
) -> PipelineResult:
    """
    Execute the full TIGR-Tas prediction pipeline.

    Parameters
    ----------
    sequence      : raw DNA string (will be validated inside)
    sequence_name : label for output files and reports
    cfg           : PipelineConfig (uses defaults if None)
    output_dir    : directory for CSV/JSON output (default: ./output)
    write_outputs : if False, skip writing files (useful for unit tests)
    verbose       : if True, print progress and summary to stdout

    Returns
    -------
    PipelineResult
    """
    if cfg is None:
        cfg = PipelineConfig()

    if output_dir is None:
        output_dir = "output"

    t_start = time.perf_counter()

    # -------------------------------------------------------------------
    # 1. Validate input
    # -------------------------------------------------------------------
    seq = validate_sequence(sequence)
    if verbose:
        print(f"\n[TIGR-Tas] Sequence: {sequence_name} ({len(seq)} bp)")

    # -------------------------------------------------------------------
    # 2. Detect spacer pairs
    # -------------------------------------------------------------------
    if verbose:
        print("[TIGR-Tas] Scanning for spacer pairs …")

    pairs, n_raw_candidates = detect_spacer_pairs(seq, cfg)

    if verbose:
        print(f"[TIGR-Tas]   {n_raw_candidates} single-spacer candidates → "
              f"{len(pairs)} valid pairs")

    if not pairs:
        if verbose:
            print("[TIGR-Tas] No spacer pairs found. "
                  "Try relaxing gap or spacer-length constraints.")
        return PipelineResult(metadata={
            "sequence_name": sequence_name,
            "sequence_length": len(seq),
            "n_candidates": 0,
            "n_ranked": 0,
            "elapsed_s": time.perf_counter() - t_start,
        })

    # Collect all spacer sequences for cross-comparison
    all_spacer_seqs = list({
        sp.sequence
        for pair in pairs
        for sp in (pair.spacer1, pair.spacer2)
    })

    # -------------------------------------------------------------------
    # 3. Score candidates (parallel if warranted)
    # -------------------------------------------------------------------
    if verbose:
        print(f"[TIGR-Tas] Scoring {len(pairs)} pairs …")

    n_workers = cfg.max_workers or cpu_count() or 1
    use_parallel = len(pairs) >= PARALLEL_CHUNK_SIZE and n_workers > 1

    if use_parallel:
        if verbose:
            print(f"[TIGR-Tas]   Using {n_workers} worker processes")
        worker = partial(_score_worker,
                         reference_seq=seq,
                         all_spacer_seqs=all_spacer_seqs,
                         cfg=cfg)
        with Pool(processes=n_workers) as pool:
            scored: List[ScoredCandidate] = pool.map(worker, pairs,
                                                     chunksize=PARALLEL_CHUNK_SIZE)
    else:
        scored = [
            score_candidate(p, seq, all_spacer_seqs, cfg)
            for p in pairs
        ]

    # -------------------------------------------------------------------
    # 4. Rank
    # -------------------------------------------------------------------
    ranked = rank_candidates(scored, cfg.top_n)

    if verbose:
        n_rejected = sum(1 for c in scored if c.rejected)
        print(f"[TIGR-Tas]   {n_rejected} rejected, "
              f"{len(scored) - n_rejected} valid, "
              f"{len(ranked)} returned")

    # -------------------------------------------------------------------
    # 5. CRISPR-Cas9 comparison
    # -------------------------------------------------------------------
    if verbose:
        print("[TIGR-Tas] Running CRISPR-Cas9 comparison …")

    crispr_sites = find_crispr_sites(seq, cfg, top_n=10)
    top_tigr_score = ranked[0].composite_score if ranked else 0.0
    comparison = compare_tigr_vs_crispr(top_tigr_score, crispr_sites)

    # -------------------------------------------------------------------
    # 6. Write outputs
    # -------------------------------------------------------------------
    t_elapsed = time.perf_counter() - t_start

    metadata = {
        "sequence_name":    sequence_name,
        "sequence_length":  len(seq),
        "n_raw_candidates": n_raw_candidates,
        "n_pairs_scanned":  len(pairs),
        "n_rejected":       sum(1 for c in scored if c.rejected),
        "n_ranked":         len(ranked),
        "n_candidates":     len(pairs),
        "elapsed_s":        round(t_elapsed, 3),
        "pipeline_version": "3.0.0",
        "timestamp":        time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    csv_path = json_path = None
    if write_outputs and ranked:
        os.makedirs(output_dir, exist_ok=True)
        safe_name = sequence_name.replace(" ", "_").replace("/", "_")
        csv_path  = os.path.join(output_dir, f"{safe_name}_tigr_tas.csv")
        json_path = os.path.join(output_dir, f"{safe_name}_tigr_tas.json")
        write_csv(ranked, csv_path)
        write_json(ranked, crispr_sites, comparison, metadata, json_path)
        if verbose:
            print(f"[TIGR-Tas] Output written to: {output_dir}/")

    if verbose:
        print_summary(ranked, crispr_sites, comparison, metadata)

    return PipelineResult(
        ranked_candidates=ranked,
        crispr_sites=crispr_sites,
        comparison_summary=comparison,
        metadata=metadata,
        csv_path=csv_path,
        json_path=json_path,
    )
