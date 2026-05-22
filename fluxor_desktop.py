from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QTextEdit, QProgressBar, QFrame
)
from PySide6.QtCore import QThread, Signal, Qt
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime

LOG_PATH = Path("logs/desktop_run.txt")
LOG_PATH.parent.mkdir(exist_ok=True)

class Worker(QThread):
    progresso = Signal(int)
    texto = Signal(str)
    arquivo_atual = Signal(str)
    stats = Signal(str)
    terminou = Signal(str)

    def __init__(self, origem, destino, modo):
        super().__init__()
        self.origem = Path(origem)
        self.destino = Path(destino)
        self.modo = modo
        self.cancelado = False

    def cancelar(self):
        self.cancelado = True

    def gb(self, n):
        return round(n / 1024 / 1024 / 1024, 2)

    def log(self, msg):
        linha = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        self.texto.emit(linha)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(linha + "\n")

    def run(self):
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.write("FLUXOR DESKTOP RUN\n")
            f.write(f"Início: {datetime.now()}\n\n")

        if not self.origem.exists():
            self.terminou.emit("Erro: origem não existe.")
            return

        if not self.destino.exists():
            self.terminou.emit("Erro: destino não existe.")
            return

        self.log(f"Origem: {self.origem}")
        self.log(f"Destino: {self.destino}")
        self.log(f"Modo: {self.modo}")

        self.log("Listando arquivos...")
        arquivos = []

        for f in self.origem.rglob("*"):
            if self.cancelado:
                self.terminou.emit("Cancelado.")
                return
            if f.is_file():
                arquivos.append(f)

        total = len(arquivos)

        if total == 0:
            self.terminou.emit("Nenhum arquivo encontrado.")
            return

        self.log(f"Encontrados {total} arquivos.")

        tamanho_total = 0
        for i, f in enumerate(arquivos, start=1):
            if self.cancelado:
                self.terminou.emit("Cancelado.")
                return
            try:
                tamanho_total += f.stat().st_size
            except:
                pass
            if i % 500 == 0:
                self.progresso.emit(int((i / total) * 20))

        livre = shutil.disk_usage(self.destino).free

        self.log(f"Tamanho estimado da origem: {self.gb(tamanho_total)} GB")
        self.log(f"Espaço livre no destino: {self.gb(livre)} GB")

        if livre < tamanho_total:
            falta = tamanho_total - livre
            self.log(f"ESPAÇO INSUFICIENTE. Faltam {self.gb(falta)} GB.")
            self.terminou.emit("Espaço insuficiente. Conecte um HD com mais espaço.")
            return

        self.log("Espaço suficiente.")
        self.log("Iniciando análise segura...")

        inicio = time.time()
        fotos = videos = audios = documentos = outros = 0

        for i, arquivo in enumerate(arquivos, start=1):
            if self.cancelado:
                self.terminou.emit("Cancelado.")
                return

            ext = arquivo.suffix.lower()

            if ext in [".jpg", ".jpeg", ".png", ".heic", ".webp"]:
                fotos += 1
            elif ext in [".mp4", ".mov", ".avi", ".m4v", ".mkv"]:
                videos += 1
            elif ext in [".mp3", ".wav", ".aiff", ".flac", ".m4a"]:
                audios += 1
            elif ext in [".pdf", ".doc", ".docx", ".txt", ".rtf", ".xls", ".xlsx"]:
                documentos += 1
            else:
                outros += 1

            pct = 20 + int((i / total) * 80)
            self.progresso.emit(pct)

            if i % 100 == 0 or i == total:
                decorrido = time.time() - inicio
                media = decorrido / i
                restante = int((total - i) * media)
                self.arquivo_atual.emit(str(arquivo.name))
                self.stats.emit(
                    f"{i}/{total} arquivos | ETA: {restante}s | "
                    f"Fotos: {fotos} | Vídeos: {videos} | Áudios: {audios} | Docs: {documentos}"
                )
                self.log(f"Analisado: {i}/{total} - {arquivo.name}")

            time.sleep(0.0005)

        resumo = f"""
FINALIZADO

Arquivos analisados: {total}
Tamanho total: {self.gb(tamanho_total)} GB

Fotos: {fotos}
Vídeos: {videos}
Áudios: {audios}
Documentos: {documentos}
Outros: {outros}

Relatório: {LOG_PATH}
"""
        self.log(resumo)
        self.terminou.emit("Análise finalizada com sucesso.")

class FluxorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluxor")
        self.resize(980, 720)
        self.worker = None
        self.origem = ""
        self.destino = ""

        self.setStyleSheet("""
            QWidget { background:#0f1115; color:#f8fafc; font-family:Arial; }
            QLabel { font-size:14px; }
            QPushButton {
                background:#2563eb;
                color:white;
                padding:12px;
                border-radius:10px;
                font-size:15px;
            }
            QPushButton:hover { background:#1d4ed8; }
            QTextEdit {
                background:#020617;
                color:#86efac;
                border:1px solid #334155;
                border-radius:10px;
                padding:10px;
                font-family:Menlo;
            }
            QProgressBar {
                border:1px solid #334155;
                border-radius:8px;
                text-align:center;
                height:26px;
                background:#111827;
            }
            QProgressBar::chunk {
                background:#22c55e;
                border-radius:8px;
            }
        """)

        layout = QVBoxLayout()

        titulo = QLabel("Fluxor")
        titulo.setStyleSheet("font-size:42px;font-weight:bold;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Organize seu acervo com segurança. Primeiro analisa, depois decide.")
        subtitulo.setStyleSheet("color:#cbd5e1;font-size:16px;")
        layout.addWidget(subtitulo)

        self.label_origem = QLabel("Origem: não selecionada")
        layout.addWidget(self.label_origem)

        btn_origem = QPushButton("Escolher pasta de origem")
        btn_origem.clicked.connect(self.escolher_origem)
        layout.addWidget(btn_origem)

        self.label_destino = QLabel("Destino: não selecionado")
        layout.addWidget(self.label_destino)

        btn_destino = QPushButton("Escolher pasta de destino")
        btn_destino.clicked.connect(self.escolher_destino)
        layout.addWidget(btn_destino)

        self.barra = QProgressBar()
        self.barra.setValue(0)
        layout.addWidget(self.barra)

        self.status = QLabel("Aguardando ação.")
        layout.addWidget(self.status)

        self.arquivo = QLabel("Arquivo atual: -")
        layout.addWidget(self.arquivo)

        row = QHBoxLayout()

        btn_analisar = QPushButton("Analisar espaço e acervo")
        btn_analisar.clicked.connect(self.analisar)
        row.addWidget(btn_analisar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background:#dc2626;")
        btn_cancelar.clicked.connect(self.cancelar)
        row.addWidget(btn_cancelar)

        layout.addLayout(row)

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        layout.addWidget(self.logs)

        self.setLayout(layout)

    def log(self, texto):
        self.logs.append(texto)

    def escolher_origem(self):
        pasta = QFileDialog.getExistingDirectory(self, "Escolha a pasta bagunçada")
        if pasta:
            self.origem = pasta
            self.label_origem.setText(f"Origem: {pasta}")

    def escolher_destino(self):
        pasta = QFileDialog.getExistingDirectory(self, "Escolha onde ficará organizado")
        if pasta:
            self.destino = pasta
            self.label_destino.setText(f"Destino: {pasta}")

    def analisar(self):
        if not self.origem or not self.destino:
            self.log("Escolha origem e destino antes.")
            return

        self.barra.setValue(0)
        self.logs.clear()
        self.status.setText("Rodando análise...")
        self.arquivo.setText("Arquivo atual: -")

        self.worker = Worker(self.origem, self.destino, "analise_segura")
        self.worker.progresso.connect(self.barra.setValue)
        self.worker.texto.connect(self.log)
        self.worker.arquivo_atual.connect(lambda x: self.arquivo.setText(f"Arquivo atual: {x}"))
        self.worker.stats.connect(self.status.setText)
        self.worker.terminou.connect(self.finalizado)
        self.worker.start()

    def cancelar(self):
        if self.worker:
            self.worker.cancelar()
            self.log("Cancelamento solicitado...")

    def finalizado(self, msg):
        self.status.setText(msg)
        self.log(msg)

app = QApplication(sys.argv)
window = FluxorApp()
window.show()
sys.exit(app.exec())
