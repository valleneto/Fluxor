"""Fluxor experimental beta: preview-first, safe copying, responsive UI."""
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QCheckBox, QFileDialog, QTextEdit,
    QProgressBar, QMessageBox, QFrame,
)

from fluxor_core.plan import MODOS, planejar, executar_plano


class Tarefa(QObject):
    progresso = Signal(int, int)
    pronto = Signal(dict)
    falha = Signal(str)
    finalizado = Signal()

    def __init__(self, tipo, origem, destino, modo, recursivo, plano=None):
        super().__init__()
        self.tipo = tipo
        self.origem = origem
        self.destino = destino
        self.modo = modo
        self.recursivo = recursivo
        self.plano = plano
        self.cancelado = False

    @Slot()
    def executar(self):
        try:
            if self.tipo == "preview":
                dados = planejar(self.origem, self.destino, self.modo, self.recursivo, cancelar=lambda: self.cancelado)
            else:
                dados = executar_plano(
                    self.plano, progresso=self.progresso.emit,
                    cancelar=lambda: self.cancelado,
                )
            self.pronto.emit(dados)
        except InterruptedError:
            self.falha.emit('Operação cancelada pelo usuário.')
        except Exception as erro:
            self.falha.emit(str(erro))
        finally:
            self.finalizado.emit()

    def cancelar(self):
        self.cancelado = True


class FluxorIntegrado(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluxor — Beta experimental")
        self.resize(900, 650)
        self.origem = ""
        self.destino = ""
        self.saida = ""
        self.plano = None
        self.thread = None
        self.worker = None
        self.tarefa = None
        self.last_outcome = 'idle'
        self.started_at = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)
        eyebrow = QLabel("CÓPIA SEGURA · ORIGINAL PRESERVADO")
        eyebrow.setObjectName("sectionEyebrow")
        root.addWidget(eyebrow)
        titulo = QLabel("Organize com tranquilidade.")
        titulo.setObjectName("pageTitle")
        root.addWidget(titulo)
        subtitle = QLabel("Escolha o acervo, confira a prévia e só então autorize a cópia.")
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        acervo = QFrame()
        acervo.setObjectName("stageCard")
        acervo_layout = QVBoxLayout(acervo)
        acervo_layout.setContentsMargins(16, 12, 16, 12)
        acervo_layout.setSpacing(7)
        acervo_title = QLabel("01  ACERVO")
        acervo_title.setObjectName("sectionEyebrow")
        acervo_layout.addWidget(acervo_title)
        self.origem_label = QLabel("Origem: selecione uma pasta")
        self.destino_label = QLabel("Destino: selecione uma pasta diferente")
        for path_label in (self.origem_label, self.destino_label):
            path_label.setWordWrap(True)
            path_label.setObjectName("muted")
        pasta_botoes = QHBoxLayout()
        self.b_origem = QPushButton("Escolher origem")
        self.b_destino = QPushButton("Escolher destino")
        self.b_origem.clicked.connect(self.escolher_origem)
        self.b_destino.clicked.connect(self.escolher_destino)
        pasta_botoes.addWidget(self.b_origem)
        pasta_botoes.addWidget(self.b_destino)
        acervo_layout.addWidget(self.origem_label)
        acervo_layout.addWidget(self.destino_label)
        acervo_layout.addLayout(pasta_botoes)
        root.addWidget(acervo)

        process = QFrame()
        process.setObjectName("stageCard")
        process_layout = QVBoxLayout(process)
        process_layout.setContentsMargins(16, 12, 16, 12)
        process_layout.setSpacing(8)
        process_title = QLabel("02  ORGANIZAÇÃO")
        process_title.setObjectName("sectionEyebrow")
        process_layout.addWidget(process_title)
        opcoes = QHBoxLayout()
        self.modo = QComboBox()
        self.modo.addItems(MODOS)
        self.modo.currentTextChanged.connect(self.invalidar_previa)
        self.recursivo = QCheckBox("Incluir subpastas")
        self.recursivo.setChecked(True)
        self.recursivo.toggled.connect(self.invalidar_previa)
        opcoes.addWidget(self.modo, 1)
        opcoes.addWidget(self.recursivo)
        process_layout.addLayout(opcoes)
        acoes = QHBoxLayout()
        self.b_previa = QPushButton("1  Pré-visualizar")
        self.b_previa.setObjectName("primaryAction")
        self.b_organizar = QPushButton("2  Copiar com segurança")
        self.b_cancelar = QPushButton("Interromper")
        self.b_abrir = QPushButton("Abrir resultado")
        self.b_abrir.setObjectName("quietAction")
        self.b_previa.clicked.connect(lambda: self.iniciar("preview"))
        self.b_organizar.clicked.connect(lambda: self.iniciar("organizar"))
        self.b_cancelar.clicked.connect(self.cancelar)
        self.b_abrir.clicked.connect(self.abrir)
        for button in (self.b_previa, self.b_organizar, self.b_cancelar):
            acoes.addWidget(button)
        process_layout.addLayout(acoes)
        root.addWidget(process)

        report = QFrame()
        report.setObjectName("stageCard")
        report_layout = QVBoxLayout(report)
        report_layout.setContentsMargins(16, 12, 16, 12)
        report_layout.setSpacing(7)
        report_header = QHBoxLayout()
        report_title = QLabel("03  RELATÓRIO")
        report_title.setObjectName("sectionEyebrow")
        report_header.addWidget(report_title)
        report_header.addStretch()
        report_header.addWidget(self.b_abrir)
        report_layout.addLayout(report_header)
        self.status = QLabel("Aguardando seleção.")
        self.status.setWordWrap(True)
        self.status.setObjectName("muted")
        report_layout.addWidget(self.status)
        self.barra = QProgressBar()
        self.barra.setValue(0)
        report_layout.addWidget(self.barra)
        self.eta = QLabel("Tempo restante: —")
        self.eta.setObjectName("muted")
        report_layout.addWidget(self.eta)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMinimumHeight(100)
        self.logs.setPlaceholderText("A prévia e o resultado da cópia aparecerão aqui.")
        report_layout.addWidget(self.logs, 1)
        root.addWidget(report, 1)
        self.atualizar_botoes()

    def invalidar_previa(self, *args):
        self.plano = None
        self.barra.setValue(0)
        self.eta.setText("Tempo restante: —")
        self.atualizar_botoes()

    def escolher_origem(self):
        pasta = QFileDialog.getExistingDirectory(self, "Escolher origem")
        if pasta:
            self.origem = pasta
            self.origem_label.setText(f"Origem: {pasta}")
            self.invalidar_previa()

    def escolher_destino(self):
        pasta = QFileDialog.getExistingDirectory(self, "Escolher destino")
        if pasta:
            self.destino = pasta
            self.destino_label.setText(f"Destino: {pasta}")
            self.invalidar_previa()

    def atualizar_botoes(self):
        ativo = self.thread is not None
        for b in (self.b_origem, self.b_destino, self.b_previa, self.modo, self.recursivo):
            b.setEnabled(not ativo)
        self.b_organizar.setEnabled(not ativo and self.plano is not None)
        self.b_cancelar.setEnabled(ativo)
        self.b_abrir.setEnabled(not ativo and bool(self.saida) and Path(self.saida).is_dir())

    def iniciar(self, tipo):
        if self.thread is not None:
            return
        if not self.origem or not self.destino:
            QMessageBox.warning(self, "Pastas", "Selecione origem e destino.")
            return
        if tipo == "organizar" and self.plano is None:
            QMessageBox.warning(self, "Prévia", "Faça a prévia antes de organizar.")
            return
        self.tarefa = tipo
        self.last_outcome = "running"
        self.logs.clear()
        self.started_at = time.monotonic()
        self.eta.setText("Estimativa: calculando apenas durante a cópia." if tipo == "organizar" else "Prévia: tempo variável conforme o acervo.")
        self.barra.setValue(0)
        self.status.setText("Analisando..." if tipo == "preview" else "Copiando arquivos...")
        self.thread = QThread(self)
        self.worker = Tarefa(
            tipo, self.origem, self.destino,
            self.modo.currentText(), self.recursivo.isChecked(), self.plano,
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.executar)
        self.worker.progresso.connect(self.progresso)
        self.worker.pronto.connect(self.pronto)
        self.worker.falha.connect(self.falha)
        self.worker.finalizado.connect(self.thread.quit)
        self.worker.finalizado.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.liberar)
        self.atualizar_botoes()
        self.thread.start()

    def progresso(self, atual, total):
        self.barra.setValue(round(atual * 100 / total) if total else 100)
        self.status.setText(f"Processados {atual}/{total}")
        if self.started_at is not None and 3 <= atual < total:
            elapsed = max(0, time.monotonic() - self.started_at)
            estimate = (total - atual) * elapsed / atual
            self.eta.setText(f"Tempo restante aproximado: {max(1, round(estimate))} s · estimativa por arquivo")
        elif total and atual >= total:
            self.eta.setText("Cópia concluída.")

    def pronto(self, resultado):
        self.last_outcome = ("partial" if resultado["avisos"] else "success") if self.tarefa == "preview" else ("cancelled" if resultado["cancelado"] else "partial" if resultado["total_erros"] else "success")
        if self.tarefa == "preview":
            self.plano = resultado
            self.logs.append(f"Arquivos: {resultado['total_arquivos']}")
            self.logs.append(f"Tamanho estimado: {resultado['tamanho_total']} bytes")
            self.logs.append(f"Modo: {resultado['modo']}")
            self.logs.append(f"Destino: {resultado['destino_base']}\n")
            for item in resultado["arquivos"][:150]:
                self.logs.append(f"{item['origem']} → {item['destino_relativo']}")
            if resultado["total_arquivos"] > 150:
                self.logs.append(f"... e mais {resultado['total_arquivos'] - 150} arquivos")
            for aviso in resultado["avisos"]:
                self.logs.append(f"AVISO: {aviso}")
            self.barra.setValue(100)
            self.status.setText("Prévia concluída. Confira a lista antes de organizar.")
            self.eta.setText("Prévia concluída. A duração da cópia dependerá dos arquivos e do disco.")
        else:
            self.plano = None
            self.saida = resultado["destino_base"]
            self.logs.append(f"Copiados: {resultado['total_copiados']}")
            self.logs.append(f"Erros: {resultado['total_erros']}")
            self.logs.append(f"Cancelado: {resultado['cancelado']}")
            self.logs.append(f"Destino: {self.saida}")
            for erro in resultado["erros"][:100]:
                self.logs.append(f"ERRO: {erro['origem']} — {erro['erro']}")
            self.status.setText("Cancelado." if resultado["cancelado"] else
                                "Concluído com erros." if resultado["total_erros"] else "Concluído.")
            self.eta.setText("Operação finalizada; confira o relatório.")
            if resultado["total_encontrados"] == 0:
                self.barra.setValue(100)

    def falha(self, mensagem):
        self.last_outcome = "cancelled" if mensagem.startswith("Operação cancelada") else "error"
        self.plano = None
        self.status.setText("Falha na operação.")
        self.eta.setText("Tempo indisponível após falha.")
        self.logs.append(f"ERRO: {mensagem}")

    def cancelar(self):
        if self.worker:
            self.worker.cancelar()
            self.b_cancelar.setEnabled(False)
            self.status.setText("Cancelamento solicitado; aguardando ponto seguro...")

    def liberar(self):
        self.thread = None
        self.worker = None
        self.tarefa = None
        self.atualizar_botoes()

    def abrir(self):
        if self.saida and Path(self.saida).is_dir():
            subprocess.Popen(["open", self.saida])

    def closeEvent(self, event):
        if self.thread is not None:
            QMessageBox.information(self, "Operação ativa", "Espere terminar ou solicite cancelamento.")
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = FluxorIntegrado()
    janela.show()
    sys.exit(app.exec())
