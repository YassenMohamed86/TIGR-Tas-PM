"""gui/comparison_panel.py — v4-style comparison panel for v3 backend."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from gui.styles import score_colour, COLOUR_STRONG, COLOUR_MODERATE, COLOUR_WEAK, COLOUR_BLUE, COLOUR_MUTED


class _StatCard(QWidget):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background:#22272e;border:1px solid #2d333b;border-radius:5px;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(3)
        self._num = QLabel("—")
        self._num.setObjectName("statValue")
        self._num.setAlignment(Qt.AlignCenter)
        self._num.setFont(QFont("Segoe UI", 22, QFont.Bold))
        lay.addWidget(self._num)
        lbl = QLabel(label.upper())
        lbl.setObjectName("statLabel")
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)

    def set_value(self, text, colour=COLOUR_BLUE):
        self._num.setText(text)
        self._num.setStyleSheet(f"color:{colour};font-size:22px;font-weight:700;")


class _ScoreBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(14)
        self.setMinimumWidth(200)
        self.setStyleSheet("background:#22272e;border:1px solid #2d333b;border-radius:3px;")

    def set_value(self, v):
        v = max(0.0, min(1.0, v))
        col = score_colour(v)
        s2 = f"{min(v+0.001,1):.3f}"
        self.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {col},stop:{v:.3f} {col},stop:{s2} #22272e,stop:1 #22272e);"
            "border:1px solid #2d333b;border-radius:3px;"
        )


class ComparisonPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(16)

        # Stat cards
        cg = QGroupBox("System Metrics")
        cl = QHBoxLayout(cg); cl.setSpacing(8)
        self._c_tigr   = _StatCard("TIGR-Tas dp")
        self._c_crispr = _StatCard("CRISPR PAM")
        self._c_ratio  = _StatCard("Access. ratio")
        self._c_delta  = _StatCard("Δ score")
        self._c_gc     = _StatCard("Seq GC")
        self._c_winner = _StatCard("Winner")
        for c in (self._c_tigr,self._c_crispr,self._c_ratio,self._c_delta,self._c_gc,self._c_winner):
            cl.addWidget(c)
        root.addWidget(cg)

        # Score bars
        sg = QGroupBox("Best Score Comparison")
        sl = QGridLayout(sg)
        sl.setVerticalSpacing(10)
        sl.setColumnMinimumWidth(0, 160)
        sl.setColumnStretch(2, 1)

        sl.addWidget(self._rl("TIGR-Tas best score:"), 0, 0)
        self._tigr_lbl = QLabel("—")
        self._tigr_lbl.setFont(QFont("Consolas", 13, QFont.Bold))
        self._tigr_lbl.setFixedWidth(72)
        sl.addWidget(self._tigr_lbl, 0, 1)
        self._tigr_bar = _ScoreBar()
        sl.addWidget(self._tigr_bar, 0, 2)

        sl.addWidget(self._rl("CRISPR-Cas9 best score:"), 1, 0)
        self._crispr_lbl = QLabel("—")
        self._crispr_lbl.setFont(QFont("Consolas", 13, QFont.Bold))
        self._crispr_lbl.setFixedWidth(72)
        sl.addWidget(self._crispr_lbl, 1, 1)
        self._crispr_bar = _ScoreBar()
        sl.addWidget(self._crispr_bar, 1, 2)
        root.addWidget(sg)

        # Verdict
        vg = QGroupBox("System Verdict")
        vl = QVBoxLayout(vg)
        self._verdict = QLabel("Run an analysis to see the verdict.")
        self._verdict.setObjectName("verdictLabel")
        self._verdict.setWordWrap(True)
        self._verdict.setMinimumHeight(52)
        vl.addWidget(self._verdict)
        self._sub = QLabel("")
        self._sub.setObjectName("metaLabel")
        self._sub.setWordWrap(True)
        vl.addWidget(self._sub)
        root.addWidget(vg)
        root.addStretch(1)

    def _rl(self, text):
        l = QLabel(text); l.setObjectName("fieldLabel")
        l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return l

    def load(self, comp):
        # comp is a ComparisonSummary dataclass
        tn = comp.tigr_dp_count
        cn = comp.crispr_pam_count
        ts = comp.tigr_best_score
        cs = comp.crispr_best_score
        d  = comp.delta_score
        winner = "TIGR-Tas" if d >= 0 else "CRISPR-Cas9"

        tc = COLOUR_STRONG if tn >= 3 else (COLOUR_MODERATE if tn >= 1 else COLOUR_WEAK)
        cc = COLOUR_STRONG if cn >= 3 else (COLOUR_MODERATE if cn >= 1 else COLOUR_WEAK)

        self._c_tigr.set_value(str(tn), tc)
        self._c_crispr.set_value(str(cn), cc)
        self._c_ratio.set_value(f"{comp.accessibility_ratio:.2f}",
            COLOUR_STRONG if comp.accessibility_ratio >= 1.0 else COLOUR_MODERATE)
        self._c_delta.set_value(f"{d:+.4f}", COLOUR_STRONG if d >= 0 else COLOUR_WEAK)
        self._c_gc.set_value(f"{comp.gc_fraction_seq:.2f}", COLOUR_BLUE)
        self._c_winner.set_value(
            "TIGR" if winner == "TIGR-Tas" else "CRISPR",
            COLOUR_STRONG if winner == "TIGR-Tas" else COLOUR_MODERATE
        )

        self._tigr_lbl.setText(f"{ts:.4f}")
        self._tigr_lbl.setStyleSheet(f"color:{score_colour(ts)};")
        self._crispr_lbl.setText(f"{cs:.4f}")
        self._crispr_lbl.setStyleSheet(f"color:{score_colour(cs)};")
        self._tigr_bar.set_value(ts)
        self._crispr_bar.set_value(cs)

        vc = COLOUR_STRONG if winner == "TIGR-Tas" else COLOUR_MODERATE
        self._verdict.setText(comp.verdict)
        self._verdict.setStyleSheet(
            f"color:{vc};background:#22272e;border:1px solid #2d333b;"
            "border-radius:4px;padding:10px 14px;"
        )
        self._sub.setText(
            f"Sequence: {comp.seq_length} bp  |  "
            f"GC: {comp.gc_fraction_seq:.3f}  |  "
            f"Region: {comp.region_class}  |  "
            f"Ratio: {comp.accessibility_ratio:.2f}×"
        )

    def clear(self):
        self._verdict.setText("Run an analysis to see the verdict.")
        self._verdict.setStyleSheet(
            f"color:{COLOUR_MUTED};background:#22272e;border:1px solid #2d333b;"
            "border-radius:4px;padding:10px 14px;")
        self._sub.setText("")
        for c in (self._c_tigr,self._c_crispr,self._c_ratio,self._c_delta,self._c_gc,self._c_winner):
            c.set_value("—", COLOUR_MUTED)
        self._tigr_bar.set_value(0); self._crispr_bar.set_value(0)
        self._tigr_lbl.setText("—"); self._crispr_lbl.setText("—")
