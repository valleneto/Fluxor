"""Fluxor experimental beta: preview-first, safe copying, responsive UI."""
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QCheckBox, QFileDialog, QTextEdit,
    QProgressBar, QMessageBox,
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
                dados = planejar(self.origem, self.destino, self.modo, self.recursivo)
            else:
                dados = executar_plano(
                    self.plano, progresso=self.progresso.emit,
                    cancelar=lambda: self.cancelado,
                )
            self.pronto.emit(dados)
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

        root = QVBoxLayout(self)
        titulo = QLabel("FLUXOR  |  Organização consciente")
        titulo.setStyleSheet("font-size: 24px; font-weight: 650;")
        root.addWidget(titulo)
        root.addWidget(QLabel("Prévia obrigatória. Copia arquivos sem apagar os originais."))

        self.origem_label = QLabel("Origem: selecione uma pasta")
        self.destino_label = QLabel("Destino: selecione uma pasta diferente")
        root.addWidget(self.origem_label)
        root.addWidget(self.destino_label)

        pasta_botoes = QHBoxLayout()
        self.b_origem = QPushButton("Escolher origem")
        self.b_destino = QPushButton("Escolher destino")
        self.b_origem.clicked.connect(self.escolher_origem)
        self.b_destino.clicked.connect(self.escolher_destino)
        pasta_botoes.addWidget(self.b_origem)
        pasta_botoes.addWidget(self.b_destino)
        root.addLayout(pasta_botoes)

        opcoes = QHBoxLayout()
        self.modo = QComboBox()
        self.modo.addItems(MODOS)
        self.modo.currentTextChanged.connect(self.invalidar_previa)
        self.recursivo = QCheckBox("Incluir subpastas")
        self.recursivo.setChecked(True)
        self.recursivo.toggled.connect(self.invalidar_previa)
        opcoes.addWidget(self.modo)
        opcoes.addWidget(self.recursivo)
        root.addLayout(opcoes)

        acoes = QHBoxLayout()
        self.b_previa = QPushButton("1. Pré-visualizar")
        self.b_organizar = QPushButton("2. Organizar")
        self.b_cancelar = QPushButton("Cancelar")
        self.b_abrir = QPushButton("Abrir resultado")
        self.b_previa.clicked.connect(lambda: self.iniciar("preview"))
        self.b_organizar.clicked.connect(lambda: self.iniciar("organizar"))
        self.b_cancelar.clicked.connect(self.cancelar)
        self.b_abrir.clicked.connect(self.abrir)
        for b in (self.b_previa, self.b_organizar, self.b_cancelar, self.b_abrir):
            acoes.addWidget(b)
        root.addLayout(acoes)

        self.status = QLabel("Aguardando seleção.")
        self.barra = QProgressBar()
        self.barra.setValue(0)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        root.addWidget(self.status)
        root.addWidget(self.barra)
        root.addWidget(self.logs)
        self.atualizar_botoes()

    def invalidar_previa(self, *args):
        self.plano = None
        self.barra.setValue(0)
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
        self.b_cancelar.setEnabled(ativo and self.tarefa == "organizar")
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
        self.logs.clear()
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

    def pronto(self, resultado):
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
            if resultado["total_encontrados"] == 0:
                self.barra.setValue(100)

    def falha(self, mensagem):
        self.plano = None
        self.status.setText("Falha na operação.")
        self.logs.append(f"ERRO: {mensagem}")

    def cancelar(self):
        if self.worker and self.tarefa == "organizar":
            self.worker.cancelar()
            self.b_cancelar.setEnabled(False)
            self.status.setText("Aguardando finalizar o arquivo atual...")

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
