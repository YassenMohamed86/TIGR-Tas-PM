"""
gui/results_panel.py — v4-style tables for v3 backend.
Backend data (AnalysisResult) unchanged.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel,
    QAbstractItemView, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from core.analysis import AnalysisResult
from gui.styles    import score_colour, RISK_COLOURS, CONFIDENCE_COLOURS, COLOUR_BLUE, COLOUR_MUTED

_MONO = QFont("Consolas", 11)


def _item(text, colour=None, align=Qt.AlignCenter):
    it = QTableWidgetItem(str(text))
    it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
    it.setTextAlignment(align)
    if colour:
        it.setForeground(QColor(colour))
    return it

def _score_it(v):
    it = _item(f"{v:.4f}", score_colour(v))
    it.setFont(_MONO)
    return it

def _mono_it(text, colour=None):
    it = _item(text, colour, Qt.AlignLeft | Qt.AlignVCenter)
    it.setFont(_MONO)
    return it

def _make_table(cols):
    t = QTableWidget(0, cols)
    t.setAlternatingRowColors(True)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSortingEnabled(True)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    t.verticalHeader().setVisible(False)
    t.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return t


class TigrTable(QWidget):
    HEADERS = [
        "#", "Conf", "Score",
        "Spacer 1", "Spacer 2",
        "pos", "Gap",
        "ΔG₁", "ΔG₂",
        "GC", "Thermo", "Geometry",
        "Complexity", "Structure",
        "OT Risk", "Orientation",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        self.info = QLabel("No analysis run yet.")
        self.info.setObjectName("metaLabel")
        lay.addWidget(self.info)
        self.table = _make_table(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        lay.addWidget(self.table)

    def load(self, result: AnalysisResult):
        cands = result.tigr_candidates
        self.info.setText(
            f"{len(cands)} TIGR-Tas candidates  |  "
            f"{result.n_pairs_scanned} pairs scanned  |  "
            f"{result.elapsed_s:.2f} s  |  "
            f"{result.sequence_length} bp"
        )
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(cands))

        for row, c in enumerate(cands):
            cc = CONFIDENCE_COLOURS.get(c.confidence, COLOUR_MUTED)
            rc = RISK_COLOURS.get(c.ot_risk, COLOUR_MUTED)

            self.table.setItem(row, 0,  _item(str(c.rank)))
            self.table.setItem(row, 1,  _item(c.confidence, cc))
            self.table.setItem(row, 2,  _score_it(c.score))
            self.table.setItem(row, 3,  _mono_it(c.spacer1))
            self.table.setItem(row, 4,  _mono_it(c.spacer2))
            self.table.setItem(row, 5,  _item(str(c.spacer1_start) if hasattr(c,'spacer1_start') else str(getattr(c,'pos_a',0))))
            self.table.setItem(row, 6,  _item(str(c.gap)))
            self.table.setItem(row, 7,  _item(f"{c.dg1:.2f}", COLOUR_BLUE))
            self.table.setItem(row, 8,  _item(f"{c.dg2:.2f}", COLOUR_BLUE))
            self.table.setItem(row, 9,  _item(f"{c.gc:.3f}", score_colour(c.gc)))
            self.table.setItem(row, 10, _item(f"{c.thermo:.3f}", score_colour(c.thermo)))
            self.table.setItem(row, 11, _item(f"{c.geometry:.3f}", score_colour(c.geometry)))
            self.table.setItem(row, 12, _item(f"{c.complexity:.3f}", score_colour(c.complexity)))
            self.table.setItem(row, 13, _item(f"{c.structure:.3f}", score_colour(c.structure)))
            self.table.setItem(row, 14, _item(c.ot_risk, rc))
            self.table.setItem(row, 15, _item(getattr(c,'orientation_label', getattr(c,'orientation',''))))

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()


class CrisprTable(QWidget):
    HEADERS = ["#", "Protospacer", "PAM", "Position", "Strand", "GC", "ΔG", "Score"]

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        self.info = QLabel("No CRISPR analysis run yet.")
        self.info.setObjectName("metaLabel")
        lay.addWidget(self.info)
        self.table = _make_table(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        lay.addWidget(self.table)

    def load(self, result: AnalysisResult):
        cands = result.crispr_candidates
        self.info.setText(f"{len(cands)} CRISPR-Cas9 sites  |  PAM: {result.request.pam_sequence}")
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(cands))
        for row, c in enumerate(cands):
            self.table.setItem(row, 0, _item(str(c.rank)))
            self.table.setItem(row, 1, _mono_it(c.sequence))
            self.table.setItem(row, 2, _item(c.pam, COLOUR_BLUE))
            self.table.setItem(row, 3, _item(str(c.position)))
            self.table.setItem(row, 4, _item(c.strand))
            self.table.setItem(row, 5, _item(f"{c.gc:.3f}", score_colour(c.gc)))
            self.table.setItem(row, 6, _item(f"{c.dg:.2f}", COLOUR_BLUE))
            self.table.setItem(row, 7, _score_it(c.score))
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()


class ResultsPanel(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tigr_tab   = TigrTable()
        self.crispr_tab = CrisprTable()
        self.addTab(self.tigr_tab,   "  TIGR-Tas Candidates  ")
        self.addTab(self.crispr_tab, "  CRISPR-Cas9 Sites  ")

    def load(self, result: AnalysisResult):
        self.tigr_tab.load(result)
        self.crispr_tab.load(result)
        self.setCurrentIndex(0)
