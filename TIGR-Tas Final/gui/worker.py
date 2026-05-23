"""
gui/worker.py  —  QThread worker so analysis never blocks the UI.
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt5.QtCore import QThread, pyqtSignal
from core.analysis import AnalysisRequest, AnalysisResult, run_analysis


class AnalysisWorker(QThread):
    finished = pyqtSignal(object)   # AnalysisResult
    progress = pyqtSignal(str)      # status message

    def __init__(self, request: AnalysisRequest, parent=None):
        super().__init__(parent)
        self.request = request

    def run(self):
        self.progress.emit("Validating sequence …")
        result = run_analysis(self.request)
        self.finished.emit(result)
