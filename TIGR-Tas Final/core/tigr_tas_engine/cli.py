"""
cli.py — Command-line interface for the TIGR-Tas pipeline.

Usage examples:

  # Analyse a sequence directly
  python -m tigr_tas --sequence ATGCATGC... --name my_gene

  # Read from a FASTA file
  python -m tigr_tas --fasta my_gene.fasta

  # Customise constraints
  python -m tigr_tas --fasta gene.fasta --gap-min 8 --gap-max 12 --top 20

  # Write outputs to a specific directory
  python -m tigr_tas --fasta gene.fasta --output results/

  # Increase spacer length range
  python -m tigr_tas --fasta gene.fasta --spacer-min 18 --spacer-max 25
"""

from __future__ import annotations

import argparse
import sys
import textwrap

from .constants import (
    GAP_MAX,
    GAP_MIN,
    SPACER_MAX_LEN,
    SPACER_MIN_LEN,
    TOP_N_RESULTS,
    PipelineConfig,
)
from .pipeline import run


# ---------------------------------------------------------------------------
# FASTA parser (no BioPython dependency)
# ---------------------------------------------------------------------------

def read_fasta(path: str) -> tuple[str, str]:
    """
    Read the first sequence from a FASTA file.

    Returns (sequence_name, sequence_string).
    """
    name = "sequence"
    seq_parts = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if seq_parts:
                    break   # only first record
                name = line[1:].split()[0]
            else:
                seq_parts.append(line)
    if not seq_parts:
        raise ValueError(f"No sequence found in FASTA file: {path}")
    return name, "".join(seq_parts)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tigr_tas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            TIGR-Tas Target Prediction Pipeline v3.0
            =========================================
            Deterministic, rule-based prediction of dual-spacer targeting
            sites for TIGR-Tas genome editing systems.
        """),
        epilog=textwrap.dedent("""\
            Examples:
              python -m tigr_tas --sequence ATGCATGCATGC... --name demo
              python -m tigr_tas --fasta gene.fasta --output results/ --top 20
        """),
    )

    # --- Input ---
    inp = parser.add_mutually_exclusive_group(required=True)
    inp.add_argument(
        "--sequence", "-s",
        metavar="SEQ",
        help="DNA sequence string (A/C/G/T only)",
    )
    inp.add_argument(
        "--fasta", "-f",
        metavar="PATH",
        help="Path to a FASTA file (first record used)",
    )

    # --- Sequence metadata ---
    parser.add_argument(
        "--name", "-n",
        default="input",
        metavar="NAME",
        help="Sequence/gene name for output file naming (default: input)",
    )

    # --- Scanning parameters ---
    scan = parser.add_argument_group("scanning parameters")
    scan.add_argument(
        "--spacer-min",
        type=int,
        default=SPACER_MIN_LEN,
        metavar="INT",
        help=f"Minimum spacer length in bp (default: {SPACER_MIN_LEN})",
    )
    scan.add_argument(
        "--spacer-max",
        type=int,
        default=SPACER_MAX_LEN,
        metavar="INT",
        help=f"Maximum spacer length in bp (default: {SPACER_MAX_LEN})",
    )
    scan.add_argument(
        "--gap-min",
        type=int,
        default=GAP_MIN,
        metavar="INT",
        help=f"Minimum inter-spacer gap in bp (default: {GAP_MIN})",
    )
    scan.add_argument(
        "--gap-max",
        type=int,
        default=GAP_MAX,
        metavar="INT",
        help=f"Maximum inter-spacer gap in bp (default: {GAP_MAX})",
    )

    # --- Thermodynamics ---
    thermo = parser.add_argument_group("thermodynamic parameters")
    thermo.add_argument(
        "--temperature",
        type=float,
        default=37.0,
        metavar="CELSIUS",
        help="Reaction temperature in Celsius (default: 37.0)",
    )
    thermo.add_argument(
        "--dg-cutoff",
        type=float,
        default=-5.0,
        metavar="KCAL",
        help="Hard ΔG cutoff in kcal/mol (default: -5.0; more negative = stricter)",
    )

    # --- Output ---
    out = parser.add_argument_group("output options")
    out.add_argument(
        "--output", "-o",
        default="output",
        metavar="DIR",
        help="Output directory for CSV and JSON files (default: ./output)",
    )
    out.add_argument(
        "--top",
        type=int,
        default=TOP_N_RESULTS,
        metavar="INT",
        help=f"Number of top candidates to report (default: {TOP_N_RESULTS})",
    )
    out.add_argument(
        "--no-files",
        action="store_true",
        help="Print summary only; do not write CSV/JSON files",
    )
    out.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages (errors still printed)",
    )

    # --- Performance ---
    perf = parser.add_argument_group("performance options")
    perf.add_argument(
        "--workers",
        type=int,
        default=0,
        metavar="INT",
        help="Number of parallel worker processes (0 = auto; default: 0)",
    )

    return parser


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # --- Read sequence ---
    try:
        if args.sequence:
            seq = args.sequence
            name = args.name
        else:
            name, seq = read_fasta(args.fasta)
            if args.name != "input":
                name = args.name   # override with --name if provided
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    # --- Build config ---
    cfg = PipelineConfig(
        spacer_min_len=args.spacer_min,
        spacer_max_len=args.spacer_max,
        gap_min=args.gap_min,
        gap_max=args.gap_max,
        temperature_k=args.temperature + 273.15,
        delta_g_hard_cutoff=args.dg_cutoff,
        top_n=args.top,
        max_workers=args.workers,
    )

    # --- Run ---
    try:
        run(
            sequence=seq,
            sequence_name=name,
            cfg=cfg,
            output_dir=args.output,
            write_outputs=not args.no_files,
            verbose=not args.quiet,
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
