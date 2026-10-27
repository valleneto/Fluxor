"""FLUXOR visual system — street-art / premium design (OS017).

Pure QSS: no external fonts, animations, assets or dependencies.
Works with Qt 6 and keeps native focus cues for keyboard navigation.
"""

GRAPHITE = "#0b1015"
SURFACE = "#151c24"
ELEVATED = "#202933"
STROKE = "#37434b"
ICE = "#d9ec79"
TEXT = "#f3f1e9"
MUTED = "#aebbc1"

STYLESHEET = """
QWidget {
    background-color: #0b1015;
    color: #f3f1e9;
    font-family: "Helvetica Neue", "Arial", sans-serif;
    font-size: 13px;
}
QLabel {
    background: transparent;
}
QLabel#eyebrow, QLabel#sectionEyebrow {
    color: #d9ec79;
    font-size: 11px;
    font-weight: 650;
}
QLabel#pageTitle {
    color: #f3f1e9;
    font-size: 26px;
    font-weight: 650;
}
QLabel#heroTitle {
    color: #f3f1e9;
    font-size: 31px;
    font-weight: 700;
}
QLabel#muted, QLabel#sidebarCaption {
    color: #aebbc1;
}
QFrame#sidebar {
    background-color: #141b22;
    border: 1px solid #36414a;
    border-radius: 16px;
}
QFrame#heroPanel, QFrame#stageCard, QFrame#metricCard {
    background-color: #0e141c;
    border: 1px solid #48525a;
    border-radius: 16px;
}
QPushButton {
    background-color: #25303a;
    border: 1px solid #47545d;
    border-radius: 10px;
    padding: 8px 12px;
    color: #f0f0e9;
}
QPushButton:hover {
    background-color: #32424b;
    border-color: #9fc7b8;
}
QPushButton:pressed {
    background-color: #3c4d56;
}
QPushButton:focus {
    border: 1px solid #d9ec79;
}
QPushButton:disabled {
    color: #829199;
    background-color: #161f25;
    border-color: #303a42;
}
QPushButton#primaryAction {
    color: #18201c;
    background-color: #d9ec79;
    border: 1px solid #d9ec79;
    font-weight: 700;
}
QPushButton#primaryAction:hover {
    background-color: #eef69f;
    border: 1px solid #eef69f;
}
QPushButton#primaryAction:disabled {
    background-color: #465445;
    border-color: #465445;
    color: #abb6a4;
}
QPushButton#navButton {
    text-align: left;
    color: #bbc4c5;
    background-color: transparent;
    border: 1px solid transparent;
    padding: 11px 12px;
    font-weight: 550;
}
QPushButton#navButton:hover {
    background-color: #263039;
}
QPushButton#navButton:checked {
    background-color: #263039;
    border: 1px solid #414e55;
    color: #e9f49b;
}
QPushButton#quietAction {
    color: #c6ced0;
    background-color: transparent;
    border: 1px solid #414e55;
}
QPushButton#quietAction:hover {
    color: #f6f6ed;
    background-color: #263039;
}
QLineEdit, QComboBox {
    background-color: #19232c;
    border: 1px solid #4a5860;
    border-radius: 9px;
    padding: 7px 10px;
    selection-background-color: #607e78;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #d9ec79;
}
QTableWidget, QListWidget, QTextEdit {
    background-color: #111b22;
    alternate-background-color: #1a252e;
    color: #e9efec;
    border: 1px solid #3a4a51;
    border-radius: 12px;
    gridline-color: #304047;
    selection-background-color: #405c5a;
    selection-color: #f8f8f0;
}
QHeaderView::section {
    background-color: #263039;
    color: #e0e5d8;
    border: 0;
    border-right: 1px solid #3c4a50;
    padding: 8px;
    font-weight: 550;
}
QStackedWidget {
    border: none;
}
QWidget#mediaPanel {
    background-color: #1c2730;
    border: 1px solid #4b5b61;
    border-radius: 14px;
}
QProgressBar {
    background-color: #19252d;
    border: 1px solid #435158;
    border-radius: 6px;
    text-align: center;
    height: 11px;
}
QProgressBar::chunk {
    background-color: #d9ec79;
    border-radius: 5px;
}
QScrollBar:vertical {
    background-color: #111b22;
    width: 10px;
}
QScrollBar::handle:vertical {
    background-color: #647f7a;
    border-radius: 5px;
    min-height: 23px;
}
QScrollBar:horizontal {
    background-color: #111b22;
    height: 9px;
}
QScrollBar::handle:horizontal {
    background-color: #647f7a;
    border-radius: 4px;
    min-width: 20px;
}
QSplitter::handle {
    background-color: #3e4c52;
}
QCheckBox {
    spacing: 8px;
    color: #c8d1ce;
}
QToolTip {
    color: #f3f1e9;
    background-color: #304047;
    border: 1px solid #718e85;
}
"""

# Graffiti is street lettering and painted motion, not a grey-only UI theme.
STYLESHEET += """
QLabel#brandName {
    font-family: "Arial Black", "Helvetica Neue", sans-serif;
    color: #f3f1e9;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 2px;
}
QFrame#sidebar {
    border-left: 3px solid #d9ec79;
    border-radius: 10px;
}
QFrame#heroPanel {
    border-bottom: 3px solid #ef846a;
    border-radius: 10px;
}
QFrame#stageCard {
    border-left: 3px solid #647f7a;
    border-radius: 10px;
}
QPushButton#primaryAction {
    color: #18201c;
    background-color: #d9ec79;
    border: 1px solid #d9ec79;
    font-weight: 800;
}
QPushButton#navButton {
    border-radius: 4px;
    border-left: 3px solid transparent;
    font-weight: 700;
}
QPushButton#navButton:checked {
    color: #e9f49b;
    border-left: 3px solid #d9ec79;
}
QWidget#mediaPanel {
    border-top: 3px solid #d9ec79;
}
QScrollArea#stageScroll {
    border: none;
    background-color: transparent;
}
"""
