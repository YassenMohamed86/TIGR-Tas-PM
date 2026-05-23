"""
TIGR-Tas Target Prediction Pipeline
====================================
A fully deterministic, rule-based bioinformatics pipeline for predicting
high-efficiency dual-spacer targeting sites in DNA sequences.

Modules
-------
constants    -- biological constants and scoring weights
sequence     -- sequence utilities, validation, k-mer tools
scanner      -- sliding-window spacer-pair detection on both strands
thermodynamics -- RNA-DNA nearest-neighbour ΔG calculations
geometry     -- helical periodicity and orientation scoring
offtarget    -- position-weighted mismatch off-target analysis
complexity   -- GC content, entropy, self-complementarity filters
scoring      -- multi-criteria deterministic scoring and ranking
comparison   -- CRISPR-Cas9 comparative module
reporter     -- CSV / JSON structured output
pipeline     -- top-level orchestration
cli          -- command-line interface
"""

__version__ = "3.0.0"
__author__  = "TIGR-Tas Pipeline"
