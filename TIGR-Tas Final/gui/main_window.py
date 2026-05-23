"""
gui/main_window.py — v4-style main window shell for v3 backend.
Only GUI shell changed — all backend calls identical to original v3.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QLabel, QProgressBar, QPushButton,
    QToolBar, QStatusBar, QMessageBox, QFileDialog,
    QSizePolicy, QTabWidget,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui  import QFont

from core.analysis   import AnalysisRequest, AnalysisResult
from gui.worker      import AnalysisWorker
from gui.input_panel import InputPanel
from gui.results_panel    import ResultsPanel
from gui.comparison_panel import ComparisonPanel
from utils.exporter  import export_csv, export_json


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TIGR-Tas Target Prediction System  v3.0")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        self._last_result = None
        self._worker      = None
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        tb = QToolBar("Main", self)
        tb.setMovable(False)
        tb.setStyleSheet(
            "QToolBar{background:#161b22;border-bottom:1px solid #2d333b;"
            "spacing:6px;padding:4px 14px;}"
        )
        self.addToolBar(tb)

        logo = QLabel("TIGR-Tas")
        logo.setFont(QFont("Segoe UI", 14, QFont.Bold))
        logo.setStyleSheet("color:#539bf5;margin-right:6px;")
        tb.addWidget(logo)

        sub = QLabel("Target Prediction Pipeline  v3.0")
        sub.setStyleSheet("color:#636e7b;font-size:12px;")
        tb.addWidget(sub)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        self._export_btns = []
        for label, tip, slot in [
            ("Export CSV",    "Save results as CSV files", self._export_csv),
            ("Export JSON",   "Save full results as JSON", self._export_json),
        ]:
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            btn.setEnabled(False)
            tb.addWidget(btn)
            self._export_btns.append(btn)

    # ── Central widget ────────────────────────────────────────────────────────

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        lay = QHBoxLayout(central)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        lay.addWidget(splitter)

        # Left panel
        left = QWidget()
        left.setMinimumWidth(330)
        left.setMaximumWidth(420)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 8, 0)
        ll.setSpacing(0)
        self.input_panel = InputPanel()
        self.input_panel.run_requested.connect(self._on_run)
        self.input_panel.crispr_requested.connect(self._on_run)
        self.input_panel.compare_requested.connect(self._on_run)
        ll.addWidget(self.input_panel)
        splitter.addWidget(left)

        # Right panel
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 0, 0, 0)
        rl.setSpacing(8)

        self.results_tabs = QTabWidget()
        self.results_tabs.setDocumentMode(True)
        self.results_panel    = ResultsPanel()
        self.comparison_panel = ComparisonPanel()
        self.results_tabs.addTab(self.results_panel,    "  Results Tables  ")
        self.results_tabs.addTab(self.comparison_panel, "  System Comparison  ")
        rl.addWidget(self.results_tabs)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([370, 1070])

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.status_lbl = QLabel("Ready")
        sb.addWidget(self.status_lbl, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(180)
        self.progress.setVisible(False)
        sb.addPermanentWidget(self.progress)
        self.time_lbl = QLabel("")
        self.time_lbl.setStyleSheet("color:#636e7b;margin-right:8px;")
        sb.addPermanentWidget(self.time_lbl)

    # ── Analysis ──────────────────────────────────────────────────────────────

    def _on_run(self, request: AnalysisRequest):
        if self._worker and self._worker.isRunning():
            return
        self.input_panel.set_running(True)
        self.progress.setVisible(True)
        self.status_lbl.setText("Analysing …")
        self.time_lbl.setText("")
        self._worker = AnalysisWorker(request, self)
        self._worker.progress.connect(self.status_lbl.setText)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, result: AnalysisResult):
        self.progress.setVisible(False)
        self.input_panel.set_running(False)

        if result.error:
            print(f"[TIGR-Tas ERROR]\n{result.error}", flush=True)
            self.status_lbl.setText(f"Error: {result.error.splitlines()[0]}")
            QMessageBox.critical(self, "Analysis Error", result.error.splitlines()[0])
            return

        self._last_result = result
        self.results_panel.load(result)

        if result.comparison:
            self.comparison_panel.load(result.comparison)
            self.input_panel.update_live_counts(
                result.comparison.tigr_dp_count,
                result.comparison.crispr_pam_count,
            )

        self.status_lbl.setText(
            f"Done  —  {len(result.tigr_candidates)} TIGR candidates  |  "
            f"{len(result.crispr_candidates)} CRISPR sites"
        )
        self.time_lbl.setText(f"{result.elapsed_s:.2f} s")
        for btn in self._export_btns:
            btn.setEnabled(True)
        self.results_tabs.setCurrentIndex(1)

    # ── Export ────────────────────────────────────────────────────────────────

    def _require_result(self):
        if not self._last_result:
            QMessageBox.information(self, "No Results", "Run an analysis first.")
            return False
        return True

    def _export_csv(self):
        if not self._require_result(): return
        d = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if d:
            t, c = export_csv(self._last_result, d)
            QMessageBox.information(self, "Exported", f"CSV files saved:\n{t}\n{c}")

    def _export_json(self):
        if not self._require_result(): return
        name = self._last_result.request.gene_name.replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save JSON", f"{name}_tigr_tas.json", "JSON files (*.json)")
        if path:
            export_json(self._last_result, path)
            QMessageBox.information(self, "Exported", f"JSON saved:\n{path}")
