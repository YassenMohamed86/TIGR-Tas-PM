"""
gui/input_panel.py — v4-style left panel for v3 GUI.
Strict QGridLayout, fixed label widths, v4 spacing rules.
Backend logic (AnalysisRequest fields) unchanged from v3.
"""
from __future__ import annotations
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QTextEdit,
    QSpinBox, QDoubleSpinBox, QComboBox,
    QPushButton, QSlider, QFileDialog, QFrame,
    QSizePolicy, QScrollArea,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui  import QFont

from core.analysis import AnalysisRequest

LBL_W   = 130
FIELD_H = 28
SPACING = 11
PAD     = 12


def _lbl(text):
    l = QLabel(text)
    l.setObjectName("fieldLabel")
    l.setFixedWidth(LBL_W)
    l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return l

def _unit(text):
    u = QLabel(text)
    u.setObjectName("metaLabel")
    u.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return u

def _sep():
    f = QFrame(); f.setFrameShape(QFrame.HLine); return f


class _Slider(QWidget):
    """Label above + live value to the right."""
    valueChanged = pyqtSignal(float)

    def __init__(self, label, lo, hi, default, scale=1.0, suffix="", parent=None):
        super().__init__(parent)
        self._scale = scale
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        top = QHBoxLayout()
        lbl = QLabel(label); lbl.setObjectName("fieldLabel")
        top.addWidget(lbl); top.addStretch(1)
        self._val = QLabel(f"{default * scale:.1f}{suffix}")
        self._val.setObjectName("sliderValue")
        top.addWidget(self._val)
        lay.addLayout(top)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(lo, hi)
        self._slider.setValue(default)
        self._slider.valueChanged.connect(self._on_change)
        lay.addWidget(self._slider)
        self._suffix = suffix

    def _on_change(self, v):
        real = v * self._scale
        self._val.setText(f"{real:.1f}{self._suffix}")
        self.valueChanged.emit(real)

    def value(self):
        return self._slider.value() * self._scale

    def setValue(self, v):
        self._slider.setValue(int(v / self._scale))


class InputPanel(QScrollArea):
    run_requested     = pyqtSignal(object)
    crispr_requested  = pyqtSignal(object)
    compare_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)

        inner = QWidget()
        self.setWidget(inner)
        root = QVBoxLayout(inner)
        root.setContentsMargins(4, 4, 8, 4)
        root.setSpacing(24)

        root.addWidget(self._build_seq())
        root.addWidget(self._build_params())
        root.addWidget(self._build_crispr())
        root.addWidget(self._build_actions())
        root.addStretch(1)

    # ── Sequence section ──────────────────────────────────────────────────────

    def _build_seq(self):
        grp = QGroupBox("Sequence Input")
        g   = QGridLayout(grp)
        g.setContentsMargins(PAD, PAD, PAD, PAD)
        g.setVerticalSpacing(SPACING)
        g.setHorizontalSpacing(8)
        g.setColumnMinimumWidth(0, LBL_W)
        g.setColumnStretch(1, 1)

        # Gene name
        g.addWidget(_lbl("Gene name:"), 0, 0)
        self.gene_name = QLineEdit()
        self.gene_name.setPlaceholderText("e.g. BRCA1, TP53 (optional)")
        self.gene_name.setFixedHeight(FIELD_H)
        g.addWidget(self.gene_name, 0, 1, 1, 2)

        # Region type
        g.addWidget(_lbl("Region type:"), 1, 0)
        self.region_type = QComboBox()
        self.region_type.addItems(["full_gene", "exon", "promoter"])
        self.region_type.setFixedHeight(FIELD_H)
        g.addWidget(self.region_type, 1, 1, 1, 2)

        g.addWidget(_sep(), 2, 0, 1, 3)

        seq_lbl = QLabel("DNA sequence  (A / T / C / G only):")
        seq_lbl.setObjectName("fieldLabel")
        g.addWidget(seq_lbl, 3, 0, 1, 3)

        self.seq_edit = QTextEdit()
        self.seq_edit.setPlaceholderText(
            "Paste or type your DNA sequence here …\n\n"
            "Minimum 40 bp  |  200+ bp recommended"
        )
        self.seq_edit.setMinimumHeight(110)
        self.seq_edit.setMaximumHeight(180)
        g.addWidget(self.seq_edit, 4, 0, 1, 3)

        # Buttons + counter
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_fasta = QPushButton("Load FASTA")
        btn_fasta.setObjectName("btnSmall")
        btn_fasta.clicked.connect(self._load_fasta)
        btn_clear = QPushButton("Clear")
        btn_clear.setObjectName("btnSmall")
        btn_clear.clicked.connect(self.seq_edit.clear)
        btn_row.addWidget(btn_fasta)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch(1)
        self._seq_counter = QLabel("0 bp")
        self._seq_counter.setObjectName("seqCounter")
        btn_row.addWidget(self._seq_counter)
        g.addLayout(btn_row, 5, 0, 1, 3)

        self._val_timer = QTimer(self)
        self._val_timer.setSingleShot(True)
        self._val_timer.setInterval(300)
        self._val_timer.timeout.connect(self._validate_seq)
        self.seq_edit.textChanged.connect(lambda: self._val_timer.start())

        return grp

    # ── Parameters section ────────────────────────────────────────────────────

    def _build_params(self):
        grp = QGroupBox("Analysis Parameters")
        lay = QVBoxLayout(grp)
        lay.setContentsMargins(PAD, PAD, PAD, PAD)
        lay.setSpacing(20)

        # ── A. Spacer Configuration ───────────────────────────────────────────
        spacer_grp = QGroupBox("Spacer Configuration")
        g = QGridLayout(spacer_grp)
        g.setContentsMargins(PAD, PAD, PAD, PAD)
        g.setVerticalSpacing(SPACING)
        g.setHorizontalSpacing(8)
        g.setColumnMinimumWidth(0, LBL_W)
        g.setColumnStretch(1, 1)

        # Spacer length (min–max inline)
        g.addWidget(_lbl("Spacer length:"), 0, 0)
        hl = QHBoxLayout(); hl.setSpacing(6)
        self.spacer_min = QSpinBox()
        self.spacer_min.setRange(12, 30); self.spacer_min.setValue(18)
        self.spacer_min.setFixedHeight(FIELD_H); self.spacer_min.setFixedWidth(64)
        self.spacer_max = QSpinBox()
        self.spacer_max.setRange(12, 30); self.spacer_max.setValue(25)
        self.spacer_max.setFixedHeight(FIELD_H); self.spacer_max.setFixedWidth(64)
        hl.addWidget(self.spacer_min)
        hl.addWidget(QLabel("–"))
        hl.addWidget(self.spacer_max)
        hl.addStretch(1)
        g.addLayout(hl, 0, 1)
        g.addWidget(_unit("bp"), 0, 2)

        # Gap range
        g.addWidget(_lbl("Gap range:"), 1, 0)
        gl = QHBoxLayout(); gl.setSpacing(6)
        self.gap_min = QSpinBox()
        self.gap_min.setRange(2, 40); self.gap_min.setValue(8)
        self.gap_min.setFixedHeight(FIELD_H); self.gap_min.setFixedWidth(64)
        self.gap_max = QSpinBox()
        self.gap_max.setRange(2, 40); self.gap_max.setValue(14)
        self.gap_max.setFixedHeight(FIELD_H); self.gap_max.setFixedWidth(64)
        gl.addWidget(self.gap_min)
        gl.addWidget(QLabel("–"))
        gl.addWidget(self.gap_max)
        gl.addStretch(1)
        g.addLayout(gl, 1, 1)
        g.addWidget(_unit("bp"), 1, 2)

        lay.addWidget(spacer_grp)

        # ── B. Physical Constraints ───────────────────────────────────────────
        phys_grp = QGroupBox("Physical Constraints")
        pl = QVBoxLayout(phys_grp)
        pl.setContentsMargins(PAD, PAD, PAD, PAD)
        pl.setSpacing(16)

        self._dg_slider = _Slider(
            "ΔG threshold:", 0, 300, 50, scale=0.1, suffix=" kcal/mol"
        )
        # Map: slider 0–300 → ΔG -30.0–0.0  (negative range)
        # Override: we'll use the raw value as -value/10
        # Simpler: store as negative
        self._dg_slider_raw = QWidget()
        dg_lay = QVBoxLayout(self._dg_slider_raw)
        dg_lay.setContentsMargins(0,0,0,0); dg_lay.setSpacing(4)
        dg_top = QHBoxLayout()
        dg_lbl = QLabel("ΔG threshold:"); dg_lbl.setObjectName("fieldLabel")
        dg_top.addWidget(dg_lbl); dg_top.addStretch(1)
        self._dg_val_lbl = QLabel("-5.0 kcal/mol"); self._dg_val_lbl.setObjectName("sliderValue")
        dg_top.addWidget(self._dg_val_lbl)
        dg_lay.addLayout(dg_top)
        self.dg_slider = QSlider(Qt.Horizontal)
        self.dg_slider.setRange(0, 300); self.dg_slider.setValue(50)
        self.dg_slider.valueChanged.connect(
            lambda v: self._dg_val_lbl.setText(f"{-v/10:.1f} kcal/mol"))
        dg_lay.addWidget(self.dg_slider)
        pl.addWidget(self._dg_slider_raw)

        self._geom_slider_raw = QWidget()
        gs_lay = QVBoxLayout(self._geom_slider_raw)
        gs_lay.setContentsMargins(0,0,0,0); gs_lay.setSpacing(4)
        gs_top = QHBoxLayout()
        gs_lbl = QLabel("Geometry tolerance:"); gs_lbl.setObjectName("fieldLabel")
        gs_top.addWidget(gs_lbl); gs_top.addStretch(1)
        self._geom_val_lbl = QLabel("1.5 bp"); self._geom_val_lbl.setObjectName("sliderValue")
        gs_top.addWidget(self._geom_val_lbl)
        gs_lay.addLayout(gs_top)
        self.geom_slider = QSlider(Qt.Horizontal)
        self.geom_slider.setRange(5, 40); self.geom_slider.setValue(15)
        self.geom_slider.valueChanged.connect(
            lambda v: self._geom_val_lbl.setText(f"{v/10:.1f} bp"))
        gs_lay.addWidget(self.geom_slider)
        pl.addWidget(self._geom_slider_raw)

        # Temperature
        tg = QGridLayout()
        tg.setContentsMargins(0,0,0,0); tg.setVerticalSpacing(SPACING)
        tg.setColumnMinimumWidth(0, LBL_W)
        tg.setColumnStretch(1,1)
        tg.addWidget(_lbl("Temperature:"), 0, 0)
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(4.0, 95.0); self.temperature.setValue(37.0)
        self.temperature.setSuffix(" °C"); self.temperature.setFixedHeight(FIELD_H)
        self.temperature.setFixedWidth(100)
        tg.addWidget(self.temperature, 0, 1)
        pl.addLayout(tg)

        lay.addWidget(phys_grp)

        # ── C. Output Control ─────────────────────────────────────────────────
        out_grp = QGroupBox("Output Control")
        og = QGridLayout(out_grp)
        og.setContentsMargins(PAD, PAD, PAD, PAD)
        og.setVerticalSpacing(SPACING)
        og.setColumnMinimumWidth(0, LBL_W)
        og.setColumnStretch(1,1)
        og.addWidget(_lbl("Top N results:"), 0, 0)
        self.top_n = QSpinBox()
        self.top_n.setRange(1, 50); self.top_n.setValue(10)
        self.top_n.setFixedHeight(FIELD_H); self.top_n.setFixedWidth(72)
        og.addWidget(self.top_n, 0, 1)
        lay.addWidget(out_grp)

        return grp

    # ── CRISPR comparison section ─────────────────────────────────────────────

    def _build_crispr(self):
        grp = QGroupBox("CRISPR Comparison")
        g   = QGridLayout(grp)
        g.setContentsMargins(PAD, PAD, PAD, PAD)
        g.setVerticalSpacing(SPACING)
        g.setHorizontalSpacing(8)
        g.setColumnMinimumWidth(0, LBL_W)
        g.setColumnStretch(1, 1)

        g.addWidget(_lbl("PAM sequence:"), 0, 0)
        self.pam_seq = QLineEdit("NGG")
        self.pam_seq.setFixedHeight(FIELD_H); self.pam_seq.setFixedWidth(80)
        g.addWidget(self.pam_seq, 0, 1)

        g.addWidget(_sep(), 1, 0, 1, 3)

        for row, (attr, label) in enumerate([
            ("pam_density_label", "PAM count:"),
            ("tigr_dp_label",     "TIGR dp count:"),
        ], start=2):
            g.addWidget(_lbl(label), row, 0)
            lbl = QLabel("—")
            lbl.setObjectName("fieldLabel")
            lbl.setStyleSheet("color:#539bf5;font-weight:600;font-size:13px;")
            setattr(self, attr, lbl)
            g.addWidget(lbl, row, 1)

        return grp

    # ── Action buttons ────────────────────────────────────────────────────────

    def _build_actions(self):
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self.btn_tigr    = QPushButton("  Run TIGR-Tas Analysis")
        self.btn_crispr  = QPushButton("  Run CRISPR Analysis")
        self.btn_compare = QPushButton("  Compare Systems")
        self.btn_tigr.setObjectName("btnRunTigr")
        self.btn_crispr.setObjectName("btnRunCrispr")
        self.btn_compare.setObjectName("btnCompare")

        self.btn_tigr.clicked.connect(lambda: self.run_requested.emit(self._build_request()))
        self.btn_crispr.clicked.connect(lambda: self.crispr_requested.emit(self._build_request()))
        self.btn_compare.clicked.connect(lambda: self.compare_requested.emit(self._build_request()))

        for b in (self.btn_tigr, self.btn_crispr, self.btn_compare):
            lay.addWidget(b)
        return w

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _validate_seq(self):
        raw   = self.seq_edit.toPlainText().upper()
        valid = re.sub(r"[^ACGT]", "", raw)
        total = len(raw.replace("\n","").replace(" ",""))
        n_inv = total - len(valid)
        col   = "#f85149" if n_inv > 0 else "#636e7b"
        msg   = f"{len(valid)} bp"
        if n_inv: msg += f"  |  ⚠ {n_inv} invalid"
        self._seq_counter.setText(msg)
        self._seq_counter.setStyleSheet(f"color:{col};")

    def _load_fasta(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open FASTA", "",
            "FASTA files (*.fasta *.fa *.txt);;All files (*)"
        )
        if not path: return
        name, seq = "", []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    if name: break
                    name = line[1:].split()[0]
                else:
                    seq.append(line)
        if seq: self.seq_edit.setPlainText("".join(seq))
        if name: self.gene_name.setText(name)

    def _build_request(self):
        return AnalysisRequest(
            sequence=self.seq_edit.toPlainText(),
            gene_name=self.gene_name.text().strip() or "unnamed",
            region_type=self.region_type.currentText(),
            spacer_min=self.spacer_min.value(),
            spacer_max=self.spacer_max.value(),
            gap_min=self.gap_min.value(),
            gap_max=self.gap_max.value(),
            dg_threshold=-(self.dg_slider.value() / 10.0),
            geometry_tol=self.geom_slider.value() / 10.0,
            pam_sequence=self.pam_seq.text().strip().upper() or "NGG",
            top_n=self.top_n.value(),
            temperature_c=self.temperature.value(),
        )

    def set_running(self, running: bool):
        for b in (self.btn_tigr, self.btn_crispr, self.btn_compare):
            b.setEnabled(not running)

    def update_live_counts(self, tigr_n: int, crispr_n: int):
        self.tigr_dp_label.setText(str(tigr_n))
        self.pam_density_label.setText(str(crispr_n))
