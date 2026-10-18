"""Fluxor beta launcher: choose copy organization or virtual library."""
import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton


class Inicio(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluxor | Dois modos")
        self.resize(520, 290)
        root = QVBoxLayout(self)
        title = QLabel("FLUXOR")
        title.setStyleSheet("font-size: 30px; font-weight: bold")
        root.addWidget(title)
        root.addWidget(QLabel("Escolha como quer trabalhar com seus arquivos."))
        organizar = QPushButton("Organizar — criar cópias em pastas")
        biblioteca = QPushButton("Biblioteca — pesquisar sem mover")
        organizar.clicked.connect(lambda: self.open_mode("fluxor_app_integrado.py"))
        biblioteca.clicked.connect(lambda: self.open_mode("fluxor_biblioteca.py"))
        root.addWidget(organizar)
        root.addWidget(biblioteca)
        root.addWidget(QLabel("Beta experimental. Use pastas pequenas de teste."))
        self.child = None

    def open_mode(self, filename):
        script = Path(__file__).resolve().parent / filename
        subprocess.Popen([sys.executable, str(script)], cwd=str(script.parent))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Inicio()
    window.show()
    sys.exit(app.exec())
