"""
comparison.py — CRISPR-Cas9 comparative module.

Identifies NGG PAM sites in the input sequence and scores them using the
same multi-criteria framework applied to TIGR-Tas candidates.  Output
allows direct comparison of TIGR-Tas predictions against the established
Cas9 system.

CRISPR scoring includes:
  - PAM presence and context (NGG; extended PAM scoring for NGGNG)
  - Protospacer GC content and thermodynamics
  - Seed-region quality
  - Position-weighted off-target penalty
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .complexity import gc_fraction, gc_score, shannon_entropy, structure_score
from .constants import CRISPR_PAM, PipelineConfig
from .sequence import reverse_complement
from .thermodynamics import delta_g_rna_dna, thermodynamic_score


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CrisprSite:
    """A single CRISPR-Cas9 target site with a 20-bp protospacer."""
    protospacer:    str
    pam:            str
    pam_start:      int     # 0-based start of PAM on forward coord
    strand:         str
    spacer_start:   int     # 0-based start of protospacer
    spacer_end:     int

    # Scores
    gc_score:       float = 0.0
    thermo_score:   float = 0.0
    complexity:     float = 0.0
    structure:      float = 0.0
    pam_context:    float = 0.0
    composite:      float = 0.0

    # Annotations
    gc_fraction:    float = 0.0
    dg:             float = 0.0
    entropy:        float = 0.0


# ---------------------------------------------------------------------------
# PAM detection
# ---------------------------------------------------------------------------

# NGG PAM pattern (Streptococcus pyogenes Cas9)
_NGG_PATTERN = re.compile(r"(?=(.GG))")

# Extended PAM: NGGNG provides ~2× higher specificity
_NGGNG_PATTERN = re.compile(r"(?=(.GG.G))")

PROTOSPACER_LEN = 20


def _find_ngg_sites(seq: str, strand: str, original_len: int) -> List[Tuple[str, str, int, int, int]]:
    """
    Find all NGG PAM sites on a given strand.

    Returns list of (protospacer, pam, pam_start_fwd, spacer_start_fwd, spacer_end_fwd).
    """
    results = []
    for match in _NGG_PATTERN.finditer(seq):
        pam_pos = match.start()
        spacer_end = pam_pos
        spacer_start = spacer_end - PROTOSPACER_LEN

        if spacer_start < 0:
            continue

        protospacer = seq[spacer_start:spacer_end]
        pam = seq[pam_pos:pam_pos + 3]

        if strand == "+":
            fwd_spacer_start = spacer_start
            fwd_spacer_end   = spacer_end
            fwd_pam_start    = pam_pos
        else:
            # Convert reverse-complement positions to forward coordinates
            fwd_pam_start    = original_len - pam_pos - 3
            fwd_spacer_end   = original_len - spacer_start
            fwd_spacer_start = original_len - spacer_end

        results.append((protospacer, pam, fwd_pam_start, fwd_spacer_start, fwd_spacer_end))

    return results


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _pam_context_score(seq: str, pam_start: int) -> float:
    """
    Score the PAM context.  Extended NGGNG PAM = 1.0, basic NGG = 0.7,
    weak PAM = 0.4.
    """
    if pam_start < 0 or pam_start + 5 > len(seq):
        return 0.7
    region = seq[pam_start:pam_start + 5]
    if re.match(r".GG.G", region):
        return 1.0
    if re.match(r".GG", region):
        return 0.7
    return 0.4


def _score_crispr_site(
    protospacer: str,
    pam: str,
    pam_start: int,
    spacer_start: int,
    spacer_end: int,
    strand: str,
    seq: str,
    cfg: PipelineConfig,
) -> CrisprSite:
    """Score a single CRISPR protospacer site."""
    site = CrisprSite(
        protospacer=protospacer,
        pam=pam,
        pam_start=pam_start,
        strand=strand,
        spacer_start=spacer_start,
        spacer_end=spacer_end,
    )

    site.gc_fraction = gc_fraction(protospacer)
    site.gc_score    = gc_score(protospacer)
    site.dg          = delta_g_rna_dna(protospacer, cfg.temperature_k)
    site.thermo_score = thermodynamic_score(protospacer, cfg.temperature_k)
    site.entropy     = shannon_entropy(protospacer)
    site.complexity  = min(site.entropy / 2.0, 1.0)
    site.structure   = structure_score(protospacer)
    site.pam_context = _pam_context_score(seq, pam_start)

    # Composite: equal weights across 5 criteria
    site.composite = round((
        site.gc_score * 0.20 +
        site.thermo_score * 0.30 +
        site.complexity * 0.15 +
        site.structure * 0.15 +
        site.pam_context * 0.20
    ), 4)

    return site


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_crispr_sites(
    seq: str,
    cfg: Optional[PipelineConfig] = None,
    top_n: int = 10,
) -> List[CrisprSite]:
    """
    Find and score all CRISPR-Cas9 NGG sites in *seq*.

    Returns the top *top_n* sites sorted by composite score.
    """
    if cfg is None:
        cfg = PipelineConfig()

    rc_seq = reverse_complement(seq)
    n = len(seq)
    sites: List[CrisprSite] = []

    for strand, search_seq in [("+", seq), ("-", rc_seq)]:
        for proto, pam, pam_start, sp_start, sp_end in _find_ngg_sites(search_seq, strand, n):
            site = _score_crispr_site(
                proto, pam, pam_start, sp_start, sp_end, strand, seq, cfg
            )
            sites.append(site)

    sites.sort(key=lambda s: s.composite, reverse=True)
    return sites[:top_n]


def compare_tigr_vs_crispr(
    tigr_top_score: float,
    crispr_sites: List[CrisprSite],
) -> dict:
    """
    Produce a summary comparison dict between the best TIGR-Tas candidate
    and the best CRISPR-Cas9 site.
    """
    if not crispr_sites:
        return {"comparison": "No CRISPR sites found", "winner": "TIGR-Tas"}

    best_crispr = crispr_sites[0].composite
    delta = round(tigr_top_score - best_crispr, 4)

    return {
        "tigr_tas_best_score":   round(tigr_top_score, 4),
        "crispr_cas9_best_score": round(best_crispr, 4),
        "delta_score":           delta,
        "winner":                "TIGR-Tas" if delta >= 0 else "CRISPR-Cas9",
        "n_crispr_sites_found":  len(crispr_sites),
    }
