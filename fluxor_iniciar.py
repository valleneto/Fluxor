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
            QWidget { font-size: 13px; }
            QPushButton { padding: 8px 12px; border-radius: 8px; }
            QPushButton:hover { background-color: palette(midlight); }
            QPushButton:disabled { color: palette(mid); }
            QLineEdit, QComboBox { padding: 6px; border-radius: 6px; }
            QTableWidget { gridline-color: palette(midlight); }
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
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
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
