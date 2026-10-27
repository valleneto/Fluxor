"""FLUXOR 018 — matte black, brushed silver, muted gold.

No fluorescent palette. The graffiti identity stays in the left sidebar;
the screensaver owns the main center. Pure Qt stylesheet, no remote assets.
"""
BLACK = "#0f1012"
MATTE = "#17191c"
SILVER = "#d1d0cb"
GOLD = "#ac9060"
TEXT = "#e8e7e3"
MUTED = "#a5a5a4"

STYLESHEET = """
QWidget {
    background-color: #0f1012;
    color: #e8e7e3;
    font-family: "Helvetica Neue", "Arial", sans-serif;
    font-size: 13px;
}
QLabel { background: transparent; }
QLabel#eyebrow, QLabel#sectionEyebrow { color: #b9a17a; font-size: 11px; font-weight: 650; }
QLabel#pageTitle { color: #ecebe7; font-size: 25px; font-weight: 700; }
QLabel#heroTitle { color: #eeece8; font-size: 28px; font-weight: 700; }
QLabel#muted, QLabel#sidebarCaption { color: #a5a5a4; }
QFrame#sidebar {
    background-color: #151719; border: 1px solid #363737; border-radius: 12px;
}
QFrame#heroPanel {
    background-color: #131416; border: 1px solid #43413d; border-radius: 12px;
}
QFrame#stageCard, QFrame#metricCard {
    background-color: #1a1c1f; border: 1px solid #393a3b; border-radius: 10px;
}
QPushButton {
    color: #dfded8; background-color: #27292c; border: 1px solid #4a4a49;
    border-radius: 8px; padding: 8px 12px; font-weight: 550;
}
QPushButton:hover { color: #ffffff; background-color: #343537; border-color: #938c7c; }
QPushButton:pressed { background-color: #404044; }
QPushButton:focus { border: 2px solid #b6a17d; }
QPushButton:disabled { color: #828384; background-color: #1b1e21; border-color: #323436; }
QPushButton#primaryAction {
    color: #141518; background-color: #c5ad83; border: 1px solid #ccb78e;
    font-weight: 700;
}
QPushButton#primaryAction:hover { background-color: #e1c99e; border-color: #e1c99e; }
QPushButton#primaryAction:disabled {
    color: #a6a3a0; background-color: #57544e; border-color: #57544e;
}
QPushButton#navButton {
    text-align: left; color: #bcbdbb; background-color: transparent;
    border: 1px solid transparent; border-left: 3px solid transparent;
    border-radius: 6px; padding: 10px 9px; font-weight: 600;
}
QPushButton#navButton:hover { background-color: #252628; }
QPushButton#navButton:checked {
    background-color: #302e2b; border: 1px solid #53504b;
    border-left: 3px solid #bba06f; color: #e9e3d7;
}
QPushButton#quietAction {
    background: transparent; color: #b7b8b5; border: 1px solid #424242;
}
QPushButton#quietAction:hover { background-color: #28292a; color: #f1eee8; }
QLineEdit, QComboBox {
    background-color: #222427; color: #e8e7e3; border: 1px solid #48494a;
    border-radius: 7px; padding: 7px 9px; selection-background-color: #766954;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #baa27d; }
QTableWidget, QListWidget, QTextEdit {
    background-color: #181a1d; alternate-background-color: #222427; color: #ecebe7;
    border: 1px solid #3c3f40; border-radius: 9px; gridline-color: #313436;
    selection-background-color: #5b5143; selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #282a2c; color: #d0ceca; border: none;
    border-right: 1px solid #414140; padding: 8px; font-weight: 600;
}
QStackedWidget { border: none; }
QWidget#mediaPanel {
    background-color: #202225; border: 1px solid #4e4b46; border-radius: 10px;
}
QScrollArea#stageScroll { border: none; background-color: transparent; }
QProgressBar {
    background-color: #222426; color: #ddd7ca; border: 1px solid #444446;
    border-radius: 5px; text-align: center; height: 11px;
}
QProgressBar::chunk { background-color: #bba078; border-radius: 4px; }
QScrollBar:vertical { background-color: #1a1c1e; width: 10px; }
QScrollBar::handle:vertical {
    background-color: #646461; border-radius: 4px; min-height: 22px;
}
QScrollBar:horizontal { background-color: #1a1c1e; height: 9px; }
QScrollBar::handle:horizontal {
    background-color: #646461; border-radius: 4px; min-width: 20px;
}
QSplitter::handle { background-color: #454647; }
QCheckBox { spacing: 8px; color: #c4c2be; }
QToolTip {
    color: #e8e7e3; background-color: #2a2b2d; border: 1px solid #70695d;
}
"""
