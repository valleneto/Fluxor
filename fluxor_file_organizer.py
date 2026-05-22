from PySide6.QtWidgets import *
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QPixmap
from pathlib import Path
from datetime import datetime
import sys, shutil, time, re, subprocess

CATEGORIAS = {
    "Imagens": [".jpg", ".jpeg", ".png", ".heic", ".webp", ".gif", ".bmp", ".tiff", ".svg"],
    "Videos": [".mp4", ".mov", ".avi", ".m4v", ".mkv", ".wmv", ".flv", ".webm"],
    "Audio": [".mp3", ".wav", ".aiff", ".aif", ".flac", ".m4a", ".ogg", ".aac", ".mid", ".midi"],
    "PDFs": [".pdf"],
    "Documentos": [".doc", ".docx", ".txt", ".rtf", ".odt", ".pages"],
    "Planilhas": [".xls", ".xlsx", ".csv", ".numbers"],
    "Apresentacoes": [".ppt", ".pptx", ".key"],
    "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Executaveis": [".exe", ".msi", ".dmg", ".pkg", ".app"],
    "Projetos_Codigo": [".py", ".js", ".html", ".css", ".json", ".xml", ".sql", ".sh", ".md"],
}

class Worker(QThread):
    progresso = Signal(int)
    log = Signal(str)
    status = Signal(str)
    fim = Signal(str)

    def __init__(self, origem, destino, nome_pasta, modo, agrupamento, limite_teste):
        super().__init__()
        self.origem = Path(origem)
        nome_limpo = re.sub(r'[^\w\s\-]', '', nome_pasta).strip() or "Fluxor_Organizado"
        self.destino = Path(destino) / nome_limpo
        self.modo = modo
        self.agrupamento = agrupamento
        self.limite_teste = limite_teste

    def gb(self, n):
        return round(n / 1024 / 1024 / 1024, 2)

    def data_arquivo(self, p):
        try:
            return datetime.fromtimestamp(p.stat().st_mtime)
        except:
            return None

    def categoria(self, p):
        ext = p.suffix.lower()
        for nome, exts in CATEGORIAS.items():
            if ext in exts:
                return nome
        return "Outros"

    def pasta_data(self, base, data):
        if self.agrupamento == "ano":
            return base / str(data.year)
        if self.agrupamento == "ano_mes":
            return base / str(data.year) / f"{data.month:02d}"
        return base / str(data.year) / f"{data.month:02d}" / f"{data.day:02d}"

    def destino_arquivo(self, p):
        cat = self.categoria(p)
        ext = p.suffix.lower()
        data = self.data_arquivo(p)

        if cat in ["Imagens", "Videos"] and data:
            return self.pasta_data(self.destino / cat, data)

        if cat == "Audio":
            return self.destino / "Audio" / (ext.replace(".", "").upper() or "SEM_EXTENSAO")

        if cat == "Outros":
            return self.destino / "Revisar" / "Outros"

        return self.destino / cat

    def copiar_seguro(self, src, pasta):
        pasta.mkdir(parents=True, exist_ok=True)
        dst = pasta / src.name
        c = 1

        while dst.exists():
            dst = pasta / f"{src.stem}_{c}{src.suffix}"
            c += 1

        shutil.copy2(src, dst)

        if src.stat().st_size != dst.stat().st_size:
            raise Exception("falha de validação de tamanho")

        return dst

    def run(self):
        try:
            self.destino.mkdir(parents=True, exist_ok=True)
            teste = self.destino / ".fluxor_write_test"
            teste.write_text("ok", encoding="utf-8")
            teste.unlink()
        except Exception as e:
            self.fim.emit(f"Destino não gravável. Escolha Desktop ou HD com escrita liberada.\nErro: {e}")
            return

        self.status.emit("Mapeando arquivos...")
        arquivos = [p for p in self.origem.rglob("*") if p.is_file()]

        if self.limite_teste:
            arquivos = arquivos[:100]

        total = len(arquivos)

        if total == 0:
            self.fim.emit("Nenhum arquivo encontrado.")
            return

        tamanho = sum((p.stat().st_size for p in arquivos if p.exists()), 0)
        livre = shutil.disk_usage(self.destino).free

        if livre < tamanho:
            self.fim.emit(f"Espaço insuficiente. Faltam {self.gb(tamanho-livre)} GB.")
            return

        self.log.emit("SEGURANÇA")
        self.log.emit("✓ Nenhum arquivo será apagado.")
        self.log.emit("✓ Tudo será copiado primeiro.")
        self.log.emit("✓ O original permanecerá intacto.")
        self.log.emit("")
        self.log.emit(f"Arquivos encontrados: {total}")
        self.log.emit(f"Tamanho estimado: {self.gb(tamanho)} GB")
        self.log.emit(f"Destino: {self.destino}")
        self.log.emit(f"Modo teste: {'ativado' if self.limite_teste else 'desativado'}")

        if self.modo == "preview":
            contagem = {}
            pastas = set()

            for i, p in enumerate(arquivos, 1):
                cat = self.categoria(p)
                contagem[cat] = contagem.get(cat, 0) + 1
                pastas.add(str(self.destino_arquivo(p)))
                self.progresso.emit(int(i / total * 100))

            self.log.emit("")
            self.log.emit("PRÉ-VISUALIZAÇÃO")
            for k, v in sorted(contagem.items()):
                self.log.emit(f"• {k}: {v}")

            self.log.emit("")
            self.log.emit(f"Pastas que serão criadas: {len(pastas)}")
            self.log.emit("Exemplos:")
            for p in list(sorted(pastas))[:16]:
                self.log.emit(f"📁 {p}")

            self.fim.emit("Prévia finalizada. Nenhum arquivo foi copiado.")
            return

        self.status.emit("Organizando com segurança...")
        copiados = erros = 0
        inicio = time.time()
        relatorio = self.destino / "Relatorio_Fluxor.txt"

        with open(relatorio, "w", encoding="utf-8") as r:
            r.write("RELATÓRIO FLUXOR FILE ORGANIZER\n")
            r.write(f"Início: {datetime.now()}\n")
            r.write(f"Origem: {self.origem}\n")
            r.write(f"Destino: {self.destino}\n")
            r.write(f"Arquivos: {total}\n")
            r.write(f"Tamanho: {self.gb(tamanho)} GB\n\n")

            for i, p in enumerate(arquivos, 1):
                try:
                    pasta = self.destino_arquivo(p)
                    dst = self.copiar_seguro(p, pasta)
                    copiados += 1
                    r.write(f"OK: {p} -> {dst}\n")
                except Exception as e:
                    erros += 1
                    r.write(f"ERRO: {p} -> {e}\n")

                if i % 10 == 0 or i == total:
                    pct = int(i / total * 100)
                    self.progresso.emit(pct)
                    restante = int((time.time() - inicio) / i * (total - i))
                    self.status.emit(f"{i}/{total} arquivos • ETA {restante}s")
                    self.log.emit(f"{i}/{total} | {pct}% | ETA {restante}s")

            r.write("\nFINALIZADO\n")
            r.write(f"Copiados: {copiados}\n")
            r.write(f"Erros: {erros}\n")

        self.fim.emit(f"Tudo pronto.\nCopiados: {copiados}\nErros: {erros}\nRelatório: {relatorio}")

class Fluxor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluxor File Organizer")
        self.resize(1280, 860)
        self.origem_path = ""
        self.destino_path = ""
        self.ultimo_destino = ""

        self.setStyleSheet("""
        QWidget { background:#F5F7FA; color:#0F172A; font-family: Helvetica Neue, Arial; }
        QScrollArea { border:none; background:#F5F7FA; }
        QFrame#Card { background:white; border:1px solid #E2E8F0; border-radius:28px; }
        QLabel#Title { font-size:20px; font-weight:700; color:#0F172A; }
        QLabel#Sub { color:#64748B; font-size:14px; }
        QPushButton { background:white; border:1px solid #DCE5F0; border-radius:18px; padding:16px; color:#0F172A; font-size:15px; }
        QPushButton:hover { border:1px solid #7CB6FF; background:#F8FBFF; }
        QPushButton#Primary { background:#5EA8FF; color:white; font-weight:700; border:none; }
        QTextEdit { background:#FBFDFF; border:1px solid #E2E8F0; border-radius:22px; padding:18px; color:#334155; font-size:13px; }
        QLineEdit { background:white; border:1px solid #E2E8F0; border-radius:18px; padding:15px; font-size:14px; }
        QProgressBar { height:34px; border-radius:17px; background:#EDF2F7; border:none; text-align:center; color:#0F172A; font-weight:600; }
        QProgressBar::chunk { background:#5EA8FF; border-radius:17px; }
        QRadioButton, QCheckBox { color:#475569; padding:6px; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 26, 30, 26)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(22)

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        pix = QPixmap("assets/fluxor_logo.png")
        if not pix.isNull():
            logo.setPixmap(pix.scaledToWidth(460, Qt.SmoothTransformation))
        else:
            logo.setText("Fluxor File Organizer")
            logo.setStyleSheet("font-size:48px;font-weight:700;")
        layout.addWidget(logo)

        subtitle = QLabel("Organização segura para arquivos digitais.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size:18px;color:#64748B;")
        layout.addWidget(subtitle)

        safety = QLabel("Seus arquivos não saem do dispositivo • Nada é apagado automaticamente • Você revisa antes de organizar")
        safety.setAlignment(Qt.AlignCenter)
        safety.setStyleSheet("font-size:14px;color:#7C98B6;")
        layout.addWidget(safety)

        content = QHBoxLayout()
        content.setSpacing(22)

        left = self.card("1. Escolha o acervo", "Selecione a pasta bagunçada e o destino.")
        self.nome = QLineEdit()
        self.nome.setText("Fluxor_Organizado")
        left.layout().addWidget(self.nome)

        self.origem = QLabel("Origem: não escolhida")
        self.origem.setObjectName("Sub")
        self.origem.setWordWrap(True)
        left.layout().addWidget(self.origem)

        borigem = QPushButton("Selecionar pasta")
        borigem.clicked.connect(self.escolher_origem)
        left.layout().addWidget(borigem)

        self.destino = QLabel("Destino: não escolhido")
        self.destino.setObjectName("Sub")
        self.destino.setWordWrap(True)
        left.layout().addWidget(self.destino)

        bdestino = QPushButton("Escolher destino")
        bdestino.clicked.connect(self.escolher_destino)
        left.layout().addWidget(bdestino)

        self.modo_teste = QCheckBox("Modo teste: organizar apenas 100 arquivos primeiro")
        self.modo_teste.setChecked(True)
        left.layout().addWidget(self.modo_teste)
        left.layout().addStretch()

        center = self.card("2. Organização", "Prévia antes da organização definitiva.")
        self.status = QLabel("Aguardando seleção.")
        self.status.setObjectName("Sub")
        center.layout().addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        center.layout().addWidget(self.progress)

        prev = QPushButton("Pré-visualizar")
        prev.clicked.connect(lambda: self.rodar("preview"))
        center.layout().addWidget(prev)

        organizar = QPushButton("ORGANIZAR COM SEGURANÇA")
        organizar.setObjectName("Primary")
        organizar.clicked.connect(lambda: self.rodar("organizar"))
        center.layout().addWidget(organizar)

        abrir = QPushButton("Abrir pasta organizada")
        abrir.clicked.connect(self.abrir_destino)
        center.layout().addWidget(abrir)

        center.layout().addStretch()

        right = self.card("3. Relatório", "Prévia, estrutura e resumo.")
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setText("Fluxor pronto.\n\nEscolha uma pasta, pré-visualize e organize com segurança.")
        right.layout().addWidget(self.logs)

        content.addWidget(left, 30)
        content.addWidget(center, 30)
        content.addWidget(right, 40)

        layout.addLayout(content)

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

    def escolher_origem(self):
        p = QFileDialog.getExistingDirectory(self, "Selecionar pasta bagunçada")
        if p:
            self.origem_path = p
            self.origem.setText(f"Origem: {p}")

    def escolher_destino(self):
        p = QFileDialog.getExistingDirectory(self, "Escolher destino")
        if p:
            self.destino_path = p
            self.destino.setText(f"Destino: {p}")

    def rodar(self, modo):
        if not self.origem_path or not self.destino_path:
            self.logs.append("Escolha origem e destino primeiro.")
            return

        self.logs.clear()
        self.progress.setValue(0)
        self.status.setText("Iniciando...")

        self.ultimo_destino = str(Path(self.destino_path) / self.nome.text())

        self.worker = Worker(
            self.origem_path,
            self.destino_path,
            self.nome.text(),
            modo,
            "ano_mes",
            self.modo_teste.isChecked()
        )

        self.worker.progresso.connect(self.progress.setValue)
        self.worker.log.connect(self.logs.append)
        self.worker.status.connect(self.status.setText)
        self.worker.fim.connect(self.finalizar)
        self.worker.start()

    def finalizar(self, texto):
        self.status.setText(texto)
        self.logs.append("")
        self.logs.append(texto)

    def abrir_destino(self):
        if self.ultimo_destino:
            subprocess.run(["open", self.ultimo_destino])

app = QApplication(sys.argv)
w = Fluxor()
w.show()
sys.exit(app.exec())
