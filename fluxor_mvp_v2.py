from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from pathlib import Path
import sys
import shutil
import subprocess

CATEGORIAS = {
    "Imagens": [
        ".jpg", ".jpeg", ".png",
        ".heic", ".webp", ".gif", ".bmp"
    ],

    "Videos": [
        ".mp4", ".mov", ".avi",
        ".mkv", ".webm"
    ],

    "Audio": [
        ".mp3", ".wav", ".flac",
        ".aac", ".m4a"
    ],

    "PDFs": [
        ".pdf"
    ],

    "Documentos": [
        ".doc", ".docx", ".txt",
        ".rtf", ".pages"
    ],

    "Planilhas": [
        ".xls", ".xlsx", ".csv"
    ],

    "Compactados": [
        ".zip", ".rar", ".7z",
        ".tar", ".gz"
    ],

    "Apps": [
        ".dmg", ".pkg", ".app"
    ]
}

class Fluxor(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Fluxor File Organizer"
        )

        self.resize(1320, 860)

        self.origem = ""
        self.destino = ""

        self.setStyleSheet("""

        QWidget {
            background:#F6F8FB;
            color:#101828;
            font-family:Helvetica Neue;
        }

        QFrame#Panel {
            background:white;
            border:1px solid #E4EAF2;
            border-radius:28px;
        }

        QLabel#Title {
            font-size:22px;
            font-weight:700;
        }

        QLabel#Muted {
            color:#667085;
            font-size:13px;
        }

        QPushButton {
            background:white;
            border:1px solid #D8E2EE;
            border-radius:18px;
            padding:15px;
            font-size:15px;
        }

        QPushButton:hover {
            background:#F2F7FF;
            border:1px solid #65A9FF;
        }

        QPushButton#Primary {
            background:#5EA8FF;
            color:white;
            font-weight:700;
            border:none;
        }

        QPushButton#Primary:hover {
            background:#7CB6FF;
        }

        QTextEdit, QLineEdit, QComboBox {
            background:white;
            border:1px solid #E4EAF2;
            border-radius:18px;
            padding:14px;
        }

        QTextEdit {
            font-family:Menlo;
            font-size:12px;
        }

        QProgressBar {
            height:34px;
            border-radius:17px;
            background:#EAF0F6;
            border:none;
            text-align:center;
            font-weight:700;
        }

        QProgressBar::chunk {
            background:#5EA8FF;
            border-radius:17px;
        }

        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)

        pix = QPixmap("assets/fluxor_logo.png")

        if not pix.isNull():

            logo.setPixmap(
                pix.scaledToWidth(
                    520,
                    Qt.SmoothTransformation
                )
            )

        else:

            logo.setText(
                "Fluxor File Organizer"
            )

        root.addWidget(logo)
        subtitle = QLabel(
            "Organize Downloads, Desktop e pastas bagunçadas."
        )

        subtitle.setAlignment(Qt.AlignCenter)

        subtitle.setStyleSheet("""
            color:#667085;
            font-size:16px;
        """)

        root.addWidget(subtitle)

        grid = QHBoxLayout()
        grid.setSpacing(22)

        left = self.panel()
        ll = left.layout()

        t1 = QLabel("1. Acervo")
        t1.setObjectName("Title")
        ll.addWidget(t1)

        self.nome = QLineEdit()
        self.nome.setText(
            "Fluxor_Organizado"
        )

        ll.addWidget(self.nome)

        self.origem_label = QLabel(
            "Origem: não selecionada"
        )

        self.origem_label.setObjectName(
            "Muted"
        )

        self.origem_label.setWordWrap(True)

        ll.addWidget(self.origem_label)

        borigem = QPushButton(
            "Selecionar pasta bagunçada"
        )

        borigem.clicked.connect(
            self.escolher_origem
        )

        ll.addWidget(borigem)

        self.destino_label = QLabel(
            "Destino: não selecionado"
        )

        self.destino_label.setObjectName(
            "Muted"
        )

        self.destino_label.setWordWrap(True)

        ll.addWidget(self.destino_label)

        bdestino = QPushButton(
            "Escolher destino"
        )

        bdestino.clicked.connect(
            self.escolher_destino
        )

        ll.addWidget(bdestino)

        self.combo = QComboBox()

        self.combo.addItems([
            "Por tipo",
            "Por extensão",
            "Por ano",
            "Por ano e mês"
        ])

        ll.addWidget(self.combo)

        ll.addStretch()

        middle = self.panel()
        ml = middle.layout()

        t2 = QLabel("2. Organização")
        t2.setObjectName("Title")

        ml.addWidget(t2)

        self.status = QLabel(
            "Aguardando seleção."
        )

        self.status.setObjectName(
            "Muted"
        )

        ml.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setValue(0)

        ml.addWidget(self.progress)

        preview = QPushButton(
            "Pré-visualizar"
        )

        preview.clicked.connect(
            self.preview_real
        )

        ml.addWidget(preview)

        organizar = QPushButton(
            "ORGANIZAR COM SEGURANÇA"
        )

        organizar.setObjectName(
            "Primary"
        )

        organizar.clicked.connect(
            self.organizar_real
        )

        ml.addWidget(organizar)

        abrir = QPushButton(
            "Abrir pasta organizada"
        )

        abrir.clicked.connect(
            self.abrir_destino
        )

        ml.addWidget(abrir)

        ml.addStretch()

        right = self.panel()
        rl = right.layout()

        t3 = QLabel("3. Relatório")
        t3.setObjectName("Title")

        rl.addWidget(t3)

        self.logs = QTextEdit()

        self.logs.setReadOnly(True)

        self.logs.setText(
            "Fluxor pronto.\n\n"
            "Selecione uma pasta para começar."
        )

        rl.addWidget(self.logs)

        grid.addWidget(left, 30)
        grid.addWidget(middle, 30)
        grid.addWidget(right, 40)

        root.addLayout(grid)

    def panel(self):

        frame = QFrame()

        frame.setObjectName("Panel")

        layout = QVBoxLayout(frame)

        layout.setContentsMargins(
            26,
            24,
            26,
            24
        )

        layout.setSpacing(16)

        return frame

    def escolher_origem(self):

        pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecionar pasta"
        )

        if pasta:

            self.origem = pasta

            self.origem_label.setText(
                f"Origem: {pasta}"
            )

    def escolher_destino(self):

        pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecionar destino"
        )

        if pasta:

            self.destino = pasta

            self.destino_label.setText(
                f"Destino: {pasta}"
            )

    def detectar_categoria(self, arquivo):

        ext = Path(arquivo).suffix.lower()

        for nome, lista in CATEGORIAS.items():

            if ext in lista:
                return nome

        return "Outros"

    def preview_real(self):

        if not self.origem:

            self.logs.setText(
                "Selecione uma pasta primeiro."
            )

            return

        self.logs.clear()

        arquivos = list(
            Path(self.origem).rglob("*")
        )

        arquivos = [
            a for a in arquivos
            if a.is_file()
        ]

        total = len(arquivos)

        contagem = {}

        for arq in arquivos:

            cat = self.detectar_categoria(arq)

            contagem[cat] = (
                contagem.get(cat, 0) + 1
            )

        self.logs.append(
            f"Arquivos encontrados: {total}\n"
        )

        for cat, qtd in sorted(contagem.items()):

            self.logs.append(
                f"• {cat}: {qtd}"
            )

        self.logs.append("")
        self.logs.append(
            "Prévia concluída."
        )

        self.progress.setValue(35)

        self.status.setText(
            f"{total} arquivos encontrados."
        )

    def organizar_real(self):

        if not self.origem or not self.destino:

            self.logs.append(
                "\nEscolha origem e destino."
            )

            return

        nome_pasta = (
            self.nome.text().strip()
            or "Fluxor_Organizado"
        )

        pasta_base = (
            Path(self.destino)
            / nome_pasta
        )

        pasta_base.mkdir(
            parents=True,
            exist_ok=True
        )

        arquivos = list(
            Path(self.origem).rglob("*")
        )

        arquivos = [
            a for a in arquivos
            if a.is_file()
        ]

        total = len(arquivos)

        self.logs.append("")
        self.logs.append(
            "Organização iniciada...\n"
        )

        copiados = 0

        for i, arq in enumerate(arquivos):

            categoria = self.detectar_categoria(arq)

            destino_final = (
                pasta_base / categoria
            )

            destino_final.mkdir(
                parents=True,
                exist_ok=True
            )

            destino_arquivo = (
                destino_final / arq.name
            )

            contador = 1

            while destino_arquivo.exists():

                destino_arquivo = (
                    destino_final /
                    f"{arq.stem}_{contador}{arq.suffix}"
                )

                contador += 1

            try:

                shutil.copy2(
                    arq,
                    destino_arquivo
                )

                copiados += 1

            except Exception as erro:

                self.logs.append(
                    f"ERRO: {arq.name}"
                )

            pct = int(
                ((i + 1) / total) * 100
            )

            self.progress.setValue(pct)

        self.logs.append("")
        self.logs.append(
            f"✓ {copiados} arquivos organizados."
        )

        self.logs.append(
            f"Destino:\n{pasta_base}"
        )

        self.status.setText(
            "Tudo organizado com sucesso."
        )

        self.destino_final = str(
            pasta_base
        )

    def abrir_destino(self):

        if hasattr(self, "destino_final"):

            subprocess.run([
                "open",
                self.destino_final
            ])

app = QApplication(sys.argv)

window = Fluxor()

window.show()

sys.exit(app.exec())
