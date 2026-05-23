# TIGR-Tas Target Prediction System — GUI v3.0

A professional research-grade GUI for the TIGR-Tas dual-spacer target
prediction pipeline, with CRISPR-Cas9 comparative analysis.

## Quick Start

### 1. Install Python 3.9+
Download from https://python.org if not already installed.

### 2. Install the one dependency (PyQt5)
```bash
pip install PyQt5
```

### 3. Run
```bash
python main.py
```

---

## Project Structure

```
tigr_tas_gui/
├── main.py                        ← Launch here
├── requirements.txt
├── core/
│   ├── analysis.py                ← API bridge (GUI ↔ engine)
│   └── tigr_tas_engine/           ← Full pipeline (no changes needed)
│       ├── scanner.py
│       ├── scoring.py
│       ├── thermodynamics.py
│       ├── geometry.py
│       ├── complexity.py
│       ├── offtarget.py
│       ├── comparison.py
│       └── ...
├── gui/
│   ├── main_window.py             ← Main application window
│   ├── input_panel.py             ← All input controls
│   ├── results_panel.py           ← TIGR + CRISPR results tables
│   ├── comparison_panel.py        ← System comparison + verdict
│   ├── worker.py                  ← Background analysis thread
│   └── styles.py                  ← Dark scientific stylesheet
└── utils/
    └── exporter.py                ← CSV / JSON / text report export
```

---

## How to Use

1. **Paste or load** a DNA sequence (min 40 bp, 200+ bp recommended)
2. Set your **gene name** and **region type**
3. Adjust **spacer length**, **gap range**, **ΔG threshold** as needed
4. Click one of:
   - **Run TIGR-Tas Analysis** — spacer pairs only
   - **Run CRISPR Analysis** — PAM sites only
   - **Compare Systems** — full comparison (recommended)
5. View results in **Results Tables** tab
6. View verdict in **System Comparison** tab
7. **Export** as CSV, JSON, or text report

---

## Colour Coding

| Colour | Meaning |
|--------|---------|
| Green  | Strong / valid / low risk |
| Amber  | Moderate |
| Red    | Weak / high risk |
| Blue   | Informational |

---

## No external bioinformatics libraries required.
## Fully deterministic — no machine learning.
