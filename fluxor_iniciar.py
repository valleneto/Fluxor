"""Fluxor Control — single-window navigation with preserved page state."""
import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QMessageBox,
)
from fluxor_biblioteca import Biblioteca
from fluxor_app_integrado import FluxorIntegrado


class Inicio(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluxor Control — Beta")
        self.resize(1000, 700)
        self.setStyleSheet("""
            QWidget { background-color: #101720; color: #eef4fa; font-family: 'Helvetica Neue'; font-size: 13px; }
            QLabel { background: transparent; }
            QLabel#eyebrow { color: #81c9d0; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            QPushButton { background: #202d3d; color: #e9f2fa; border: 1px solid #314358;
                          padding: 9px 14px; border-radius: 9px; }
            QPushButton:hover { background: #2b4053; border-color: #5cbac5; }
            QPushButton:pressed { background: #24565e; }
            QPushButton:disabled { color: #718194; background: #182330; border-color: #243141; }
            QLineEdit, QComboBox { background: #182433; border: 1px solid #314358;
                                  padding: 8px; border-radius: 8px; selection-background-color: #287987; }
            QTableWidget, QListWidget, QTextEdit { background: #151f2c; alternate-background-color: #1b2939;
                        color: #e6eff7; border: 1px solid #304255; border-radius: 11px;
                        gridline-color: #253547; selection-background-color: #225864; }
            QHeaderView::section { background: #243347; color: #d8e5f0; border: none;
                                   border-right: 1px solid #33465b; padding: 9px; }
            QStackedWidget { border: none; }
            QWidget#mediaPanel { background: #182433; border: 1px solid #304255; border-radius: 14px; }
            QScrollBar:vertical { background: #14202d; width: 10px; }
            QScrollBar::handle:vertical { background: #43566b; border-radius: 4px; min-height: 22px; }
        """)
        self.history = []
        self.future = []
        root = QVBoxLayout(self)

        nav = QHBoxLayout()
        self.back_button = QPushButton("← Voltar")
        self.forward_button = QPushButton("Avançar →")
        self.home_button = QPushButton("⌂ Início")
        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.home_button.clicked.connect(lambda: self.navigate(0))
        for button in (self.back_button, self.forward_button, self.home_button):
            nav.addWidget(button)
        nav.addStretch()
        root.addLayout(nav)

        self.pages = QStackedWidget()
        start = QWidget()
        start_layout = QVBoxLayout(start)
        title = QLabel("FLUXOR")
        title.setStyleSheet("font-size: 38px; font-weight: 800; letter-spacing: 3px; color: #8fe5e5;")
        start_layout.addWidget(title)
        start_layout.addWidget(QLabel("Encontre o que importa. Organize com segurança."))
        start_layout.addWidget(QLabel("Biblioteca: consulta sem mover. Organizar: cópia após prévia."))
        browse = QPushButton("Explorar Biblioteca — sem mover arquivos")
        organize = QPushButton("Organizar — prévia antes de copiar")
        browse.clicked.connect(lambda: self.navigate(1))
        organize.clicked.connect(lambda: self.navigate(2))
        start_layout.addWidget(browse)
        start_layout.addWidget(organize)
        start_layout.addStretch()
        start_layout.addWidget(QLabel("Beta experimental. Teste com pastas pequenas."))
        self.pages.addWidget(start)
        self.library = Biblioteca()
        self.organizer = FluxorIntegrado()
        self.pages.addWidget(self.library)
        self.pages.addWidget(self.organizer)
        root.addWidget(self.pages)
        self.refresh_nav()

    def navigate(self, target):
        current = self.pages.currentIndex()
        if current == target:
            return
        if self.active_operation():
            QMessageBox.information(
                self, "Operação em andamento",
                "Espere a operação terminar antes de trocar de tela."
            )
            return
        self.history.append(current)
        self.future.clear()
        self.pages.setCurrentIndex(target)
        self.refresh_nav()

    def active_operation(self):
        return self.library.thread is not None or self.organizer.thread is not None

    def go_back(self):
        if not self.history or self.active_operation():
            return
        current = self.pages.currentIndex()
        target = self.history.pop()
        self.future.append(current)
        self.pages.setCurrentIndex(target)
        self.refresh_nav()

    def go_forward(self):
        if not self.future or self.active_operation():
            return
        current = self.pages.currentIndex()
        target = self.future.pop()
        self.history.append(current)
        self.pages.setCurrentIndex(target)
        self.refresh_nav()

    def refresh_nav(self):
        self.back_button.setEnabled(bool(self.history))
        self.forward_button.setEnabled(bool(self.future))
        self.home_button.setEnabled(self.pages.currentIndex() != 0)

    def closeEvent(self, event):
        if self.active_operation():
            QMessageBox.information(self, "Operação ativa", "Aguarde terminar antes de fechar.")
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Inicio()
    window.show()
    sys.exit(app.exec())
