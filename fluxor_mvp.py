from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import sys
import subprocess

class Fluxor(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fluxor")
        self.resize(1280, 860)

        self.setStyleSheet("""
        QWidget {
            background:#F5F7FA;
            color:#0F172A;
            font-family: Helvetica Neue, Arial;
        }

        QScrollArea {
            border:none;
            background:#F5F7FA;
        }

        QFrame#Card {
            background:white;
            border:1px solid #E2E8F0;
            border-radius:28px;
        }

        QLabel#Title {
            font-size:20px;
            font-weight:700;
            color:#0F172A;
        }

        QLabel#Sub {
            color:#64748B;
            font-size:14px;
        }

        QPushButton {
            background:white;
            border:1px solid #DCE5F0;
            border-radius:18px;
            padding:16px;
            color:#0F172A;
            font-size:15px;
        }

        QPushButton:hover {
            border:1px solid #7CB6FF;
            background:#F8FBFF;
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

        QTextEdit {
            background:#FBFDFF;
            border:1px solid #E2E8F0;
            border-radius:22px;
            padding:18px;
            color:#334155;
            font-size:13px;
        }

        QLineEdit {
            background:white;
            border:1px solid #E2E8F0;
            border-radius:18px;
            padding:15px;
            font-size:14px;
        }

        QProgressBar {
            height:34px;
            border-radius:17px;
            background:#EDF2F7;
            border:none;
            text-align:center;
            color:#0F172A;
            font-weight:600;
        }

        QProgressBar::chunk {
            background:#5EA8FF;
            border-radius:17px;
        }

        QRadioButton, QCheckBox {
            color:#475569;
            padding:6px;
        }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 26, 30, 26)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)

        # LOGO
        logo_wrap = QWidget()
        logo_layout = QVBoxLayout(logo_wrap)
        logo_layout.setContentsMargins(0,0,0,0)

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)

        pix = QPixmap("assets/fluxor_logo.png")

        if not pix.isNull():
            pix = pix.scaledToWidth(340, Qt.SmoothTransformation)
            logo.setPixmap(pix)
        else:
            logo.setText("FLUXOR")
            logo.setStyleSheet("""
                font-size:64px;
                font-weight:700;
                letter-spacing:10px;
                color:#0F172A;
            """)

        logo_layout.addWidget(logo)

        layout.addWidget(logo_wrap)

        subtitle = QLabel("")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size:18px;
            color:#64748B;
            margin-top:0px;
            margin-bottom:0px;
        """)
        layout.addWidget(subtitle)

        safety = QLabel(
            "Seus arquivos não saem do dispositivo • Nada é apagado automaticamente • Você revisa antes de organizar"
        )

        safety.setAlignment(Qt.AlignCenter)
        safety.setStyleSheet("""
            font-size:14px;
            color:#7C98B6;
            margin-bottom:16px;
        """)

        layout.addWidget(safety)

        content = QHBoxLayout()
        content.setSpacing(22)

        # COLUNA 1
        left = self.card(
            "1. Escolha o acervo",
            "Selecione a pasta bagunçada e o destino da organização."
        )

        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Nome da pasta organizada")
        self.nome.setText("Fluxor_Organizado")

        left.layout().addWidget(self.nome)

        self.origem = QLabel("Origem: não escolhida")
        self.origem.setObjectName("Sub")
        self.origem.setWordWrap(True)
        left.layout().addWidget(self.origem)

        borigem = QPushButton("Selecionar pasta")
        left.layout().addWidget(borigem)

        self.destino = QLabel("Destino: não escolhido")
        self.destino.setObjectName("Sub")
        self.destino.setWordWrap(True)
        left.layout().addWidget(self.destino)

        bdestino = QPushButton("Escolher destino")
        left.layout().addWidget(bdestino)

        left.layout().addSpacing(10)

        tipo = QLabel("Tipo de acervo")
        tipo.setObjectName("Title")
        left.layout().addWidget(tipo)

        left.layout().addWidget(QRadioButton("Fotos e vídeos"))
        left.layout().addWidget(QRadioButton("Áudio / Beats"))
        left.layout().addWidget(QRadioButton("Documentos"))

        left.layout().addStretch()

        # COLUNA 2
        center = self.card(
            "2. Organização",
            "Prévia antes da organização definitiva."
        )

        self.status = QLabel("Aguardando seleção.")
        self.status.setObjectName("Sub")
        self.status.setWordWrap(True)
        center.layout().addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        center.layout().addWidget(self.progress)

        prev = QPushButton("Pré-visualizar")
        center.layout().addWidget(prev)

        organizar = QPushButton("ORGANIZAR COM SEGURANÇA")
        organizar.setObjectName("Primary")
        center.layout().addWidget(organizar)

        abrir = QPushButton("Abrir pasta organizada")
        center.layout().addWidget(abrir)

        infos = QLabel(
            "✓ Nada será apagado\n"
            "✓ Organização local\n"
            "✓ Revisão antes de mover"
        )

        infos.setObjectName("Sub")
        infos.setStyleSheet("""
            color:#5EA8FF;
            font-size:14px;
            margin-top:20px;
        """)

        center.layout().addWidget(infos)
        center.layout().addStretch()

        # COLUNA 3
        right = self.card(
            "3. Relatório",
            "Prévia, estrutura e resumo da organização."
        )

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)

        self.logs.setText(
            "Fluxor pronto.\n\n"
            "1. Escolha a pasta bagunçada.\n"
            "2. Escolha o destino.\n"
            "3. Pré-visualize.\n"
            "4. Organize com segurança."
        )

        right.layout().addWidget(self.logs)

        content.addWidget(left, 30)
        content.addWidget(center, 30)
        content.addWidget(right, 40)

        layout.addLayout(content)

        footer = QLabel("Fluxor MVP • organização local • seguro por padrão")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("""
            color:#94A3B8;
            margin-top:18px;
            margin-bottom:12px;
        """)

        layout.addWidget(footer)

        scroll.setWidget(page)
        root.addWidget(scroll)

    def card(self, title, subtitle):
        frame = QFrame()
        frame.setObjectName("Card")

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(26, 24, 26, 24)
        lay.setSpacing(16)

        t = QLabel(title)
        t.setObjectName("Title")
        lay.addWidget(t)

        s = QLabel(subtitle)
        s.setObjectName("Sub")
        s.setWordWrap(True)
        lay.addWidget(s)

        return frame

app = QApplication(sys.argv)
w = Fluxor()
w.show()
sys.exit(app.exec())
