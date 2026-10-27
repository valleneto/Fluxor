"""FLUXOR visual system — restrained graphite / ice design (OS016).

Pure QSS: no external fonts, animations, assets or dependencies.
Works with Qt 6 and keeps native focus cues for keyboard navigation.
"""

GRAPHITE = "#0c1118"
SURFACE = "#131c27"
ELEVATED = "#182432"
STROKE = "#2b3948"
ICE = "#b7e5ec"
TEXT = "#ecf3f7"
MUTED = "#a5b4c2"

STYLESHEET = """
QWidget {
    background-color: #0c1118;
    color: #ecf3f7;
    font-family: "Helvetica Neue", "Arial", sans-serif;
    font-size: 13px;
}
QLabel {
    background: transparent;
}
QLabel#eyebrow, QLabel#sectionEyebrow {
    color: #a8c7d0;
    font-size: 11px;
    font-weight: 650;
}
QLabel#pageTitle {
    color: #f0f6f9;
    font-size: 26px;
    font-weight: 650;
}
QLabel#heroTitle {
    color: #f0f6f9;
    font-size: 31px;
    font-weight: 700;
}
QLabel#muted, QLabel#sidebarCaption {
    color: #a5b4c2;
}
QFrame#sidebar {
    background-color: #111a24;
    border: 1px solid #263443;
    border-radius: 16px;
}
QFrame#heroPanel, QFrame#stageCard, QFrame#metricCard {
    background-color: #131e2a;
    border: 1px solid #2a3a49;
    border-radius: 16px;
}
QPushButton {
    background-color: #1c2a38;
    border: 1px solid #334354;
    border-radius: 10px;
    padding: 8px 12px;
    color: #e8f0f5;
}
QPushButton:hover {
    background-color: #293c4d;
    border-color: #7396a3;
}
QPushButton:pressed {
    background-color: #314758;
}
QPushButton:focus {
    border: 1px solid #b7e5ec;
}
QPushButton:disabled {
    color: #778997;
    background-color: #131d29;
    border-color: #243241;
}
QPushButton#primaryAction {
    color: #10222b;
    background-color: #b7e5ec;
    border: 1px solid #b7e5ec;
    font-weight: 700;
}
QPushButton#primaryAction:hover {
    background-color: #d0f0f4;
    border: 1px solid #d0f0f4;
}
QPushButton#primaryAction:disabled {
    background-color: #455762;
    border-color: #455762;
    color: #b7c3ca;
}
QPushButton#navButton {
    text-align: left;
    color: #b6c6d1;
    background-color: transparent;
    border: 1px solid transparent;
    padding: 11px 12px;
    font-weight: 550;
}
QPushButton#navButton:hover {
    background-color: #1b2a38;
}
QPushButton#navButton:checked {
    background-color: #223846;
    border: 1px solid #426273;
    color: #d9f5f8;
}
QPushButton#quietAction {
    color: #a9bac6;
    background-color: transparent;
    border: 1px solid #344452;
}
QPushButton#quietAction:hover {
    color: #e7f4f7;
    background-color: #1b2a38;
}
QLineEdit, QComboBox {
    background-color: #131f2d;
    border: 1px solid #344657;
    border-radius: 9px;
    padding: 7px 10px;
    selection-background-color: #3d6674;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #9bd2dc;
}
QTableWidget, QListWidget, QTextEdit {
    background-color: #111b27;
    alternate-background-color: #172431;
    color: #e6eef4;
    border: 1px solid #2b3b4b;
    border-radius: 12px;
    gridline-color: #243545;
    selection-background-color: #355565;
    selection-color: #f0f8fa;
}
QHeaderView::section {
    background-color: #1b2a38;
    color: #b7cad6;
    border: 0;
    border-right: 1px solid #304353;
    padding: 8px;
    font-weight: 550;
}
QStackedWidget {
    border: none;
}
QWidget#mediaPanel {
    background-color: #162330;
    border: 1px solid #344958;
    border-radius: 14px;
}
QProgressBar {
    background-color: #15222e;
    border: 1px solid #344553;
    border-radius: 6px;
    text-align: center;
    height: 11px;
}
QProgressBar::chunk {
    background-color: #a4d7e0;
    border-radius: 5px;
}
QScrollBar:vertical {
    background-color: #111b27;
    width: 10px;
}
QScrollBar::handle:vertical {
    background-color: #4b6576;
    border-radius: 5px;
    min-height: 23px;
}
QScrollBar:horizontal {
    background-color: #111b27;
    height: 9px;
}
QScrollBar::handle:horizontal {
    background-color: #4b6576;
    border-radius: 4px;
    min-width: 20px;
}
QSplitter::handle {
    background-color: #2a3949;
}
QCheckBox {
    spacing: 8px;
    color: #bccbd4;
}
QToolTip {
    color: #ecf3f7;
    background-color: #203243;
    border: 1px solid #53707f;
}
"""
