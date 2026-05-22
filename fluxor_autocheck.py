from pathlib import Path
import subprocess
import shutil
import time

ROOT = Path.cwd()

print("\nFLUXOR AUTOCHECK\n")

pastas = [
    "core",
    "database",
    "reports",
    "logs",
    "templates"
]

for pasta in pastas:
    (ROOT / pasta).mkdir(exist_ok=True)

gitignore = ROOT / ".gitignore"

extras = [
    "fluxor.db",
    "__pycache__/",
    ".DS_Store",
    "logs/*.txt"
]

conteudo = ""

if gitignore.exists():
    conteudo = gitignore.read_text()

for item in extras:
    if item not in conteudo:
        conteudo += f"\n{item}"

gitignore.write_text(conteudo)

desktop_app = ROOT / "fluxor_desktop.py"

desktop_app.write_text('''
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTextEdit
)

import sys
import subprocess
import shutil
from pathlib import Path

class Fluxor(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Fluxor")
        self.resize(800, 600)

        self.origem = ""
        self.destino = ""

        layout = QVBoxLayout()

        titulo = QLabel("Fluxor")
        titulo.setStyleSheet("font-size:32px;font-weight:bold;")
        layout.addWidget(titulo)

        self.label_origem = QLabel("Origem não selecionada")
        layout.addWidget(self.label_origem)

        btn_origem = QPushButton("Escolher origem")
        btn_origem.clicked.connect(self.escolher_origem)
        layout.addWidget(btn_origem)

        self.label_destino = QLabel("Destino não selecionado")
        layout.addWidget(self.label_destino)

        btn_destino = QPushButton("Escolher destino")
        btn_destino.clicked.connect(self.escolher_destino)
        layout.addWidget(btn_destino)

        btn_espaco = QPushButton("Analisar espaço")
        btn_espaco.clicked.connect(self.analisar)
        layout.addWidget(btn_espaco)

        btn_organize = QPushButton("Rodar organize")
        btn_organize.clicked.connect(self.organizar)
        layout.addWidget(btn_organize)

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        layout.addWidget(self.logs)

        self.setLayout(layout)

    def log(self, texto):
        self.logs.append(texto)

    def escolher_origem(self):

        pasta = QFileDialog.getExistingDirectory(
            self,
            "Escolha origem"
        )

        if pasta:
            self.origem = pasta
            self.label_origem.setText(pasta)

    def escolher_destino(self):

        pasta = QFileDialog.getExistingDirectory(
            self,
            "Escolha destino"
        )

        if pasta:
            self.destino = pasta
            self.label_destino.setText(pasta)

    def gb(self, valor):
        return round(valor / 1024 / 1024 / 1024, 2)

    def analisar(self):

        if not self.origem or not self.destino:
            self.log("Escolha origem e destino.")
            return

        self.log("Analisando espaço...")

        total = 0

        for arquivo in Path(self.origem).rglob("*"):

            if arquivo.is_file():

                try:
                    total += arquivo.stat().st_size
                except:
                    pass

        livre = shutil.disk_usage(self.destino).free

        self.log(f"Origem: {self.gb(total)} GB")
        self.log(f"Livre destino: {self.gb(livre)} GB")

        if livre >= total:
            self.log("OK: espaço suficiente.")
        else:
            self.log(
                f"INSUFICIENTE: faltam {self.gb(total-livre)} GB"
            )

    def organizar(self):

        self.log("Rodando organize.py")

        resultado = subprocess.run(
            ["python3", "organize.py"],
            capture_output=True,
            text=True
        )

        self.log(resultado.stdout)

        if resultado.stderr:
            self.log(resultado.stderr)

        self.log("Finalizado.")

app = QApplication(sys.argv)

window = Fluxor()

window.show()

sys.exit(app.exec())
''')

print("App desktop criado.")

print("\nRodando verificações...\n")

subprocess.run(["python3", "fluxor.py", "summary"])

print("\nFLUXOR AUTOCHECK FINALIZADO")
print("\nAbra o app com:\n")
print("python3 fluxor_desktop.py")
