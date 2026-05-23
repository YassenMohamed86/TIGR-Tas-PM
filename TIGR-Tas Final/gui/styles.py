"""gui/styles.py — v4 scientific dark theme applied to v3 GUI."""

STYLESHEET = """
QWidget {
    background-color: #1c2128;
    color: #cdd9e5;
    font-family: "Segoe UI", "Roboto", Arial, sans-serif;
    font-size: 13px;
}
QMainWindow { background-color: #161b22; }

QGroupBox {
    border: 1px solid #2d333b;
    border-radius: 5px;
    margin-top: 12px;
    padding: 12px 10px 10px 10px;
    font-size: 11px;
    font-weight: 600;
    color: #768390;
    letter-spacing: 0.8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #539bf5;
    font-size: 10px;
}

QLabel { color: #cdd9e5; background: transparent; }
QLabel#metaLabel  { color: #768390; font-size: 11px; }
QLabel#verdictLabel {
    font-size: 13px; font-weight: 600; color: #e6edf3;
    background: #22272e; border: 1px solid #2d333b;
    border-radius: 4px; padding: 10px 14px;
}
QLabel#statValue {
    font-size: 22px; font-weight: 700; color: #539bf5;
}
QLabel#statLabel { font-size: 10px; color: #636e7b; letter-spacing: 0.8px; }
QLabel#fieldLabel  { color: #909dab; font-size: 12px; }
QLabel#sliderValue {
    color: #539bf5; font-size: 12px; font-weight: 600;
    font-family: "Consolas", monospace; min-width: 48px;
}
QLabel#seqCounter { font-size: 11px; color: #636e7b; font-family: "Consolas", monospace; }

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #22272e;
    border: 1px solid #2d333b;
    border-radius: 4px;
    padding: 5px 8px;
    color: #cdd9e5;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #539bf5;
}
QTextEdit {
    background-color: #161b22;
    border: 1px solid #2d333b;
    border-radius: 4px;
    color: #cdd9e5;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 10px;
}
QTextEdit:focus { border: 1px solid #539bf5; }
QComboBox::drop-down { border: none; padding-right: 6px; }
QComboBox QAbstractItemView {
    background: #161b22; border: 1px solid #2d333b;
    selection-background-color: #1f6feb; color: #cdd9e5;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: #2d333b; border: none; width: 16px;
}

QSlider::groove:horizontal { height: 3px; background: #2d333b; border-radius: 2px; }
QSlider::handle:horizontal {
    background: #539bf5; width: 13px; height: 13px;
    margin: -5px 0; border-radius: 7px;
}
QSlider::sub-page:horizontal { background: #1f6feb; border-radius: 2px; }

QPushButton {
    background-color: #22272e; border: 1px solid #2d333b;
    border-radius: 5px; padding: 7px 16px;
    color: #cdd9e5; font-weight: 500; min-height: 32px;
}
QPushButton:hover  { background: #2d333b; border-color: #539bf5; color: #e6edf3; }
QPushButton:pressed { background: #1f6feb; border-color: #539bf5; }
QPushButton:disabled { background: #161b22; color: #444c56; border-color: #22272e; }

QPushButton#btnRunTigr {
    background: #1f6feb; border: 1px solid #388bfd;
    color: #fff; font-weight: 600; font-size: 13px; min-height: 38px;
}
QPushButton#btnRunTigr:hover { background: #388bfd; }
QPushButton#btnRunCrispr {
    background: #22272e; border: 1px solid #238636;
    color: #3fb950; font-weight: 600; min-height: 38px;
}
QPushButton#btnRunCrispr:hover { background: #1b4721; border-color: #3fb950; }
QPushButton#btnCompare {
    background: #22272e; border: 1px solid #6e40c9;
    color: #a371f7; font-weight: 600; min-height: 38px;
}
QPushButton#btnCompare:hover { background: #271052; border-color: #a371f7; }

QTableWidget {
    background: #161b22; alternate-background-color: #1c2128;
    border: 1px solid #2d333b; gridline-color: #22272e;
    color: #cdd9e5; font-size: 12px;
}
QTableWidget::item { padding: 4px 6px; border: none; }
QTableWidget::item:selected { background: #1f6feb; color: #fff; }
QHeaderView::section {
    background: #22272e; color: #636e7b; border: none;
    border-right: 1px solid #2d333b; border-bottom: 1px solid #2d333b;
    padding: 5px 6px; font-size: 10px; font-weight: 600; letter-spacing: 0.5px;
}

QTabWidget::pane { border: 1px solid #2d333b; background: #1c2128; border-radius: 4px; }
QTabBar::tab {
    background: #22272e; border: 1px solid #2d333b; border-bottom: none;
    padding: 6px 16px; margin-right: 2px; color: #636e7b;
    border-radius: 4px 4px 0 0; font-size: 12px;
}
QTabBar::tab:selected { background: #1c2128; color: #cdd9e5; border-bottom: 2px solid #539bf5; }
QTabBar::tab:hover    { background: #2d333b; color: #cdd9e5; }

QScrollBar:vertical   { background: #161b22; width: 8px; border: none; }
QScrollBar:horizontal { background: #161b22; height: 8px; border: none; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #2d333b; border-radius: 4px; min-height: 20px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: #444c56; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }

QProgressBar {
    background: #22272e; border: 1px solid #2d333b;
    border-radius: 3px; height: 6px; color: transparent;
}
QProgressBar::chunk { background: #1f6feb; border-radius: 3px; }
QStatusBar { background: #161b22; color: #636e7b; border-top: 1px solid #2d333b; font-size: 11px; }
QSplitter::handle { background: #2d333b; }
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:hover { background: #539bf5; }
QToolTip { background: #22272e; color: #cdd9e5; border: 1px solid #2d333b; padding: 4px 8px; }
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #2d333b; background: #2d333b; max-height: 1px;
}
"""

COLOUR_STRONG   = "#3fb950"
COLOUR_MODERATE = "#d29922"
COLOUR_WEAK     = "#f85149"
COLOUR_BLUE     = "#539bf5"
COLOUR_MUTED    = "#636e7b"

RISK_COLOURS = {
    "NONE":   COLOUR_STRONG,
    "LOW":    COLOUR_STRONG,
    "MEDIUM": COLOUR_MODERATE,
    "HIGH":   COLOUR_WEAK,
}
CONFIDENCE_COLOURS = {
    "A": COLOUR_STRONG,
    "B": COLOUR_BLUE,
    "C": COLOUR_MODERATE,
    "D": COLOUR_WEAK,
}

def score_colour(score: float) -> str:
    if score >= 0.70: return COLOUR_STRONG
    if score >= 0.45: return COLOUR_MODERATE
    return COLOUR_WEAK
