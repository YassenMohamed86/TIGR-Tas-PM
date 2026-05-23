"""
core/analysis.py  —  Clean API bridge between GUI and pipeline engine.

The GUI never imports from tigr_tas_engine directly; it always goes
through AnalysisRequest / AnalysisResult.
"""

from __future__ import annotations
import sys, os, time
from dataclasses import dataclass, field
from typing import List, Optional

_CORE = os.path.dirname(__file__)
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from tigr_tas_engine.constants   import PipelineConfig
from tigr_tas_engine.sequence    import validate_sequence
from tigr_tas_engine.scanner     import detect_spacer_pairs
from tigr_tas_engine.scoring     import score_candidate, rank_candidates, ScoredCandidate
from tigr_tas_engine.comparison  import find_crispr_sites, CrisprSite
from tigr_tas_engine.complexity  import gc_fraction


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class AnalysisRequest:
    sequence:       str
    gene_name:      str   = "unnamed"
    region_type:    str   = "full_gene"   # promoter | exon | full_gene
    spacer_min:     int   = 18
    spacer_max:     int   = 25
    gap_min:        int   = 8
    gap_max:        int   = 14
    dg_threshold:   float = -5.0
    geometry_tol:   float = 1.5
    pam_sequence:   str   = "NGG"
    top_n:          int   = 10
    temperature_c:  float = 37.0


@dataclass
class TigrCandidate:
    rank:       int
    pair_id:    str
    spacer1:    str
    spacer2:    str
    gap:        int
    geometry:   float
    dg1:        float
    dg2:        float
    gc:         float
    thermo:     float
    complexity: float
    structure:  float
    ot_risk:    str
    confidence: str
    score:      float
    orientation: str
    phase_angle: float


@dataclass
class CrisprCandidate:
    rank:     int
    sequence: str
    pam:      str
    position: int
    strand:   str
    gc:       float
    dg:       float
    score:    float
    pam_ctx:  float


@dataclass
class ComparisonSummary:
    tigr_dp_count:       int
    crispr_pam_count:    int
    accessibility_ratio: float
    tigr_best_score:     float
    crispr_best_score:   float
    delta_score:         float
    verdict:             str
    region_class:        str
    gc_fraction_seq:     float
    seq_length:          int


@dataclass
class AnalysisResult:
    request:           AnalysisRequest
    tigr_candidates:   List[TigrCandidate]   = field(default_factory=list)
    crispr_candidates: List[CrisprCandidate] = field(default_factory=list)
    comparison:        Optional[ComparisonSummary] = None
    elapsed_s:         float = 0.0
    error:             Optional[str] = None
    sequence_length:   int = 0
    n_pairs_scanned:   int = 0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _region_class(seq: str, region_type: str) -> str:
    gc = gc_fraction(seq)
    if region_type == "promoter": return "Regulatory"
    if region_type == "exon":     return "Coding"
    if gc < 0.35:  return "AT-rich"
    if gc > 0.65:  return "GC-rich"
    return "Mixed"


def _verdict(tigr_n: int, crispr_n: int) -> str:
    if tigr_n >= 3 and crispr_n < 2:
        return "TIGR-Tas is suitable; CRISPR targeting is limited in this region"
    if tigr_n >= 3 and crispr_n >= 3:
        return "Both systems applicable; TIGR-Tas offers PAM-independent access"
    if tigr_n < 2 and crispr_n >= 3:
        return "CRISPR-Cas9 is suitable; TIGR-Tas spacer density is low"
    if tigr_n < 2 and crispr_n < 2:
        return "Low targetability region — consider relaxing constraints"
    return "Moderate targetability — review individual candidates carefully"


# ── Main analysis entry point ─────────────────────────────────────────────────

def run_analysis(req: AnalysisRequest) -> AnalysisResult:
    """Full TIGR-Tas + CRISPR analysis. Call from a worker thread."""
    t0     = time.perf_counter()
    result = AnalysisResult(request=req)

    try:
        seq = validate_sequence(req.sequence)
        result.sequence_length = len(seq)

        cfg = PipelineConfig(
            spacer_min_len=req.spacer_min,
            spacer_max_len=req.spacer_max,
            gap_min=req.gap_min,
            gap_max=req.gap_max,
            delta_g_hard_cutoff=req.dg_threshold,
            top_n=req.top_n,
            temperature_k=req.temperature_c + 273.15,
        )

        # ── TIGR-Tas ──────────────────────────────────────────────────────────
        pairs, _ = detect_spacer_pairs(seq, cfg)
        result.n_pairs_scanned = len(pairs)
        all_seqs = list({sp.sequence for p in pairs
                         for sp in (p.spacer1, p.spacer2)})
        scored = [score_candidate(p, seq, all_seqs, cfg) for p in pairs]
        ranked = rank_candidates(scored, req.top_n)

        result.tigr_candidates = [
            TigrCandidate(
                rank=i+1,
                pair_id=c.pair_id,
                spacer1=c.spacer1_seq,
                spacer2=c.spacer2_seq,
                gap=c.gap_bp,
                geometry=round(c.components.geometry, 4),
                dg1=c.sp1_dg,
                dg2=c.sp2_dg,
                gc=round((c.sp1_gc + c.sp2_gc) / 2, 3),
                thermo=round(c.components.thermodynamics, 4),
                complexity=round(c.components.complexity, 4),
                structure=round(c.components.structure, 4),
                ot_risk=c.ot_risk_level,
                confidence=c.confidence_tier,
                score=c.composite_score,
                orientation=c.orientation_label,
                phase_angle=round(c.phase_angle, 1),
            )
            for i, c in enumerate(ranked)
        ]

        # ── CRISPR ────────────────────────────────────────────────────────────
        crispr_sites = find_crispr_sites(seq, cfg, top_n=req.top_n)
        result.crispr_candidates = [
            CrisprCandidate(
                rank=i+1,
                sequence=s.protospacer,
                pam=s.pam,
                position=s.spacer_start,
                strand=s.strand,
                gc=round(s.gc_fraction, 3),
                dg=s.dg,
                score=round(s.composite, 4),
                pam_ctx=round(s.pam_context, 3),
            )
            for i, s in enumerate(crispr_sites)
        ]

        # ── Comparison ────────────────────────────────────────────────────────
        tigr_n   = len(ranked)
        crispr_n = len(crispr_sites)
        result.comparison = ComparisonSummary(
            tigr_dp_count=tigr_n,
            crispr_pam_count=crispr_n,
            accessibility_ratio=round(tigr_n / max(crispr_n, 1), 3),
            tigr_best_score=round(ranked[0].composite_score if ranked else 0.0, 4),
            crispr_best_score=round(crispr_sites[0].composite if crispr_sites else 0.0, 4),
            delta_score=round(
                (ranked[0].composite_score if ranked else 0.0) -
                (crispr_sites[0].composite if crispr_sites else 0.0), 4),
            verdict=_verdict(tigr_n, crispr_n),
            region_class=_region_class(seq, req.region_type),
            gc_fraction_seq=round(gc_fraction(seq), 3),
            seq_length=len(seq),
        )

    except Exception as exc:
        import traceback
        result.error = f"{exc}\n\nTraceback:\n{traceback.format_exc()}"

    result.elapsed_s = round(time.perf_counter() - t0, 3)
    return result
