"""
constants.py — Biological constants and configurable scoring weights.

All numeric values that appear more than once in the pipeline live here.
Researchers can override defaults by editing this file or passing a
config dict through PipelineConfig.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple


# ---------------------------------------------------------------------------
# DNA / RNA alphabet
# ---------------------------------------------------------------------------

DNA_BASES: frozenset = frozenset("ACGT")
RNA_BASES: frozenset = frozenset("ACGU")

COMPLEMENT: Dict[str, str] = {
    "A": "T", "T": "A", "C": "G", "G": "C",
    "a": "t", "t": "a", "c": "g", "g": "c",
}

RNA_COMPLEMENT: Dict[str, str] = {
    "A": "U", "U": "A", "C": "G", "G": "C",
}


# ---------------------------------------------------------------------------
# Spacer / window parameters
# ---------------------------------------------------------------------------

SPACER_MIN_LEN: int = 18
SPACER_MAX_LEN: int = 25
SPACER_OPTIMAL_MIN: int = 20
SPACER_OPTIMAL_MAX: int = 23

GAP_MIN: int = 8
GAP_MAX: int = 14


# ---------------------------------------------------------------------------
# Helical geometry
# ---------------------------------------------------------------------------

HELICAL_PERIOD: float = 10.5       # bp per full turn (B-form DNA)
OPTIMAL_PHASE_TOLERANCE: float = 1.5   # bp deviation still considered "in phase"


# ---------------------------------------------------------------------------
# Thermodynamics
# ---------------------------------------------------------------------------

GAS_CONSTANT: float = 1.987e-3      # kcal / (mol·K)
BODY_TEMPERATURE_K: float = 310.15  # 37 °C in Kelvin

# Nearest-neighbour RNA:DNA hybrid parameters (Sugimoto 1995)
# Keys are "rN1/dN2" where N1 is the RNA base, N2 is the DNA base
# Values are (ΔH kcal/mol, ΔS cal/mol·K)
NN_PARAMS: Dict[str, Tuple[float, float]] = {
    "rA/dT": (-7.8, -21.9),
    "rC/dG": (-9.7, -24.2),
    "rG/dC": (-7.0, -19.7),
    "rU/dA": (-7.8, -21.9),
    "rA/dA": (-2.7,  -8.8),
    "rC/dA": (-5.4, -13.7),
    "rG/dA": (-2.9,  -9.8),
    "rU/dA": (-7.8, -21.9),
    "rA/dC": (-3.1,  -9.5),
    "rC/dC": (-7.4, -19.3),
    "rG/dC": (-7.0, -19.7),
    "rU/dC": (-6.5, -17.1),
    "rA/dG": (-1.8,  -3.8),
    "rC/dG": (-9.7, -24.2),
    "rG/dG": (-2.8,  -7.7),
    "rU/dG": (-3.9, -10.5),
    "rA/dT": (-7.8, -21.9),
    "rC/dT": (-5.0, -13.8),
    "rG/dT": (-4.8, -12.9),
    "rU/dT": (-3.2,  -9.3),
}

# ΔG thresholds (kcal/mol) — more negative = more stable
DELTA_G_OPTIMAL_MAX: float = -8.0   # must be at least this stable
DELTA_G_HARD_CUTOFF: float = -5.0   # below this → reject outright


# ---------------------------------------------------------------------------
# GC content and complexity
# ---------------------------------------------------------------------------

GC_OPTIMAL_LOW:  float = 0.40
GC_OPTIMAL_HIGH: float = 0.65
GC_ACCEPT_LOW:   float = 0.30
GC_ACCEPT_HIGH:  float = 0.75

ENTROPY_MIN: float = 1.5            # bits — reject low-complexity spacers
SELF_COMP_MAX_SCORE: float = 0.4    # fraction — reject highly self-complementary


# ---------------------------------------------------------------------------
# Off-target detection
# ---------------------------------------------------------------------------

OT_MAX_MISMATCHES: int = 4          # maximum weighted mismatches to report
OT_SEED_LENGTH: int = 8             # positions counted as "seed" from 5' end
OT_SEED_WEIGHT: float = 2.0         # penalty multiplier for seed mismatches
OT_TAIL_WEIGHT: float = 1.0         # penalty multiplier for non-seed mismatches

# Risk thresholds (weighted mismatch score)
OT_HIGH_RISK_MAX:   float = 3.0
OT_MEDIUM_RISK_MAX: float = 6.0
# > OT_MEDIUM_RISK_MAX → LOW risk


# ---------------------------------------------------------------------------
# Scoring weights  (must sum to 1.0)
# ---------------------------------------------------------------------------

SCORE_WEIGHTS: Dict[str, float] = {
    "gc_content":        0.15,
    "length":            0.10,
    "geometry":          0.20,
    "thermodynamics":    0.25,
    "complexity":        0.10,
    "structure":         0.10,
    "off_target":        0.10,
}

assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-9, \
    "SCORE_WEIGHTS must sum to 1.0"


# ---------------------------------------------------------------------------
# CRISPR-Cas9 comparison
# ---------------------------------------------------------------------------

CRISPR_PAM: str = "NGG"


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------

PARALLEL_CHUNK_SIZE: int = 500      # candidates per worker chunk
MAX_WORKERS: int = 0                # 0 = use os.cpu_count()


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

TOP_N_RESULTS: int = 10
REPORT_DECIMAL_PLACES: int = 4


@dataclass
class PipelineConfig:
    """
    Single configuration object passed through the entire pipeline.
    Override any constant by setting the corresponding attribute.
    """
    spacer_min_len: int = SPACER_MIN_LEN
    spacer_max_len: int = SPACER_MAX_LEN
    gap_min: int = GAP_MIN
    gap_max: int = GAP_MAX
    helical_period: float = HELICAL_PERIOD
    delta_g_hard_cutoff: float = DELTA_G_HARD_CUTOFF
    delta_g_optimal_max: float = DELTA_G_OPTIMAL_MAX
    gc_optimal_low: float = GC_OPTIMAL_LOW
    gc_optimal_high: float = GC_OPTIMAL_HIGH
    gc_accept_low: float = GC_ACCEPT_LOW
    gc_accept_high: float = GC_ACCEPT_HIGH
    entropy_min: float = ENTROPY_MIN
    self_comp_max: float = SELF_COMP_MAX_SCORE
    ot_max_mismatches: int = OT_MAX_MISMATCHES
    ot_seed_length: int = OT_SEED_LENGTH
    ot_seed_weight: float = OT_SEED_WEIGHT
    ot_tail_weight: float = OT_TAIL_WEIGHT
    score_weights: Dict[str, float] = field(
        default_factory=lambda: dict(SCORE_WEIGHTS)
    )
    top_n: int = TOP_N_RESULTS
    max_workers: int = MAX_WORKERS
    temperature_k: float = BODY_TEMPERATURE_K
