# TIGR-TasR: Dual-Guide RNA Computational Scoring Platform

TIGR-TasR scores and ranks dual-spacer RNA-guided DNA targeting candidates for the TIGR-Tas nuclease system (Faure et al., 2025, *Science* 388:eadv9789). Given a DNA sequence or a gene promoter fetched from NCBI or Ensembl, it generates all valid spacer A + spacer B candidate pairs, scores each pair across four biophysical models, and displays results in a scrollable table.

Try the platform at http://localhost:5000 after following the installation steps below.

> **Note:** Several scoring parameters are working hypotheses transferred from Cas9/CRISPR systems and have not been experimentally validated for TIGR-Tas. All such assumptions are explicitly labelled in `parameter_registry.md`. The composite final score is intentionally left blank — scoring weights cannot be assigned without experimental TIGR-Tas data.

---

## Installation

Install Python dependencies:

```bash
pip install flask
pip install biopython
pip install requests
pip install numpy
pip install pandas
pip install reportlab
pip install pytest
pip install pytest-cov
```

When you run the platform, it should serve the interface at `http://localhost:5000`.

---

## Usage

### Command line

```bash
python app.py
```

The platform will start a local development server. Open `http://localhost:5000` in a browser.

### Input modes

**Raw sequence** — paste a DNA sequence (A, T, C, G only) directly into the text box or upload a FASTA file.

**Gene promoter** — enter a gene name or accession number, organism, and upstream region size. The platform fetches the sequence from NCBI Entrez or the Ensembl REST API. A valid email address is required for NCBI access.

### Parameters

| Parameter | Default | Description |
|---|---|---|
| Spacer length k | 9 nt | Length of each spacer |
| Min spacer distance | 5 bp | Minimum gap between spacer A and spacer B |
| Max spacer distance | 50 bp | Maximum gap between spacer A and spacer B |
| Min GC content | 0.30 | Minimum GC fraction for both spacers |
| Max GC content | 0.70 | Maximum GC fraction for both spacers |

---

## Running tests

```bash
pytest tests/ -v --cov=modules --cov-report=term-missing
```

Expected results:

```
sequence_service:      8 tests —  8 passed
candidate_generator:   7 tests —  7 passed
geometry_model:        6 tests —  6 passed
cleavage_model:        6 tests —  6 passed
thermodynamics_model:  6 tests —  6 passed
specificity_engine:    7 tests —  7 passed
results_assembler:     5 tests —  5 passed
api:                   4 tests —  4 passed
integration:           4 tests —  4 passed
─────────────────────────────────────────
Total:                53 tests — 53 passed, 0 failed
```

Network-dependent tests (NCBI, Ensembl) are skipped by default. Run them manually:

```bash
pytest tests/ -k "ncbi or ensembl" -v -s
```

---

## File structure

```
project_root/
│
├── app.py                        # Flask entry point, routes, API endpoints
│
├── modules/
│   ├── sequence_service.py       # Input parsing, FASTA, NCBI fetch, Ensembl fetch
│   ├── candidate_generator.py    # Spacer pair generation, sliding window, constraints
│   ├── geometry_model.py         # DNA helix geometry scoring (10.5 bp/turn)
│   ├── cleavage_model.py         # Cut site prediction, overhang scoring
│   ├── thermodynamics_model.py   # ΔG estimation (simplified nearest-neighbour)
│   ├── specificity_engine.py     # Seed-region mismatch scan, off-target risk
│   └── results_assembler.py      # Collects per-pair scores, builds results table
│
├── templates/
│   ├── index.html                # Main input page
│   └── results.html              # Results table + sequence overview bar
│
├── static/
│   ├── css/                      # Stylesheets
│   └── js/                       # main.js, results.js
│
├── tests/                        # All pytest test files
├── parameter_registry.md         # Scientific assumption registry
├── requirements.txt              # All pip dependencies
└── README.md                     # This file
```

---

## Scoring models

All scores are in **[0.0, 1.0]**. The composite final score is not computed — this is intentional (see `parameter_registry.md`).

| Score | Formula | Key assumption |
|---|---|---|
| Geometry | Gaussian on `gap % 10.5` | DNA B-form helix period 10.5 bp/turn [ESTABLISHED] |
| Cleavage | Tier score based on overhang length | Optimal overhang 7–9 bp [HYPOTHESIS — CROSS-SYSTEM] |
| Stability A / B | `ΔG = −(2×GC + 1×AT)`, normalised | GC:AT weighting [ESTABLISHED]; normalisation [HYPOTHESIS] |
| Specificity A / B | Seed-region mismatch scan of submitted sequence | Seed region 0–7 bp [HYPOTHESIS — CROSS-SYSTEM] |
| Final score | — | **Not computed** — weights are PARAMETER_UNRESOLVED |

Score cells marked ⚠ depend on parameters that are hypotheses transferred from Cas9 and have not been validated for TIGR-Tas.

---

## Genome fetch sources

The platform fetches sequences **only** from these authorised sources:

- **NCBI Entrez** — `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` via Biopython. Requires a valid email address.
- **Ensembl REST API** — `https://rest.ensembl.org`. No API key required for low-volume academic use.

No other genome sources are used.

---

## Clinically relevant loci

The platform is designed and tested against: **CXCR4**, **VEGFA**, and **B2M**.

---

## References

Faure G. et al. (2025). TIGR-Tas: A family of modular RNA-guided DNA-targeting systems in prokaryotes and their viruses. *Science* 388:eadv9789.

Watson J.D. & Crick F.H.C. (1953). Molecular structure of nucleic acids. *Nature* 171:737–738.

Wang A.H.J. et al. (1979). Molecular structure of a left-handed double helical DNA fragment at atomic resolution. *Science* 205:972–974.

SantaLucia J. (1998). A unified view of polymer, dumbbell, and oligonucleotide DNA nearest-neighbor thermodynamics. *PNAS* 95:1460–1465.

Sternberg S.H. et al. (2014). DNA interrogation by the CRISPR RNA-guided endonuclease Cas9. *Nature* 507:62–67.

---

## Authors

Boraay & Yassen Mohamed — New Cairo STEM School

---

## License

GPLv3 — see LICENSE.txt
