"""Fluxor: prototipo integrado e responsivo para o modo 'Por tipo'.

Executar apos validar os testes: python3 fluxor_app_integrado.py
Nao substitui fluxor_mvp_v2.py.
"""
import sys
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QObject, Slot
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QProgressBar, QTextEdit, QMessageBox,
)

from fluxor_core.organizer import organizar_por_tipo, validar_pastas
from fluxor_core.scanner import escanear_pasta


class Tarefa(QObject):
    progresso = Signal(int, int)
    pronto = Signal(dict)
    falha = Signal(str)
    finalizado = Signal()

    def __init__(self, tipo, origem, destino=None):
        super().__init__()
        self.tipo = tipo
        self.origem = origem
        self.destino = destino
        self.cancelado = False

    @Slot()
    def executar(self):
        try:
            if self.tipo == "preview":
                resultado = escanear_pasta(self.origem)
            else:
                resultado = organizar_por_tipo(
                    self.origem, self.destino,
                    progresso=self.progresso.emit,
                    cancelar=lambda: self.cancelado,
                )
            self.pronto.emit(resultado)
        except Exception as erro:
            self.falha.emit(str(erro))
        finally:
            self.finalizado.emit()

    def cancelar(self):
        self.cancelado = True


class FluxorIntegrado(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluxor — Beta de integração")
        self.resize(850, 620)
        self.origem = ""
        self.destino = ""
        self.saida = ""
        self.thread = None
        self.worker = None
        self.tipo_tarefa = None

        root = QVBoxLayout(self)
        titulo = QLabel("Fluxor | Beta de integração")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold;")
        root.addWidget(titulo)
        root.addWidget(QLabel("Modo experimental: organização POR TIPO, somente primeiro nível da pasta."))
        self.label_origem = QLabel("Origem não selecionada")
        self.label_destino = QLabel("Destino não selecionado")
        root.addWidget(self.label_origem)
        root.addWidget(self.label_destino)

        opcoes = QHBoxLayout()
        self.botao_origem = QPushButton("Selecionar origem")
        self.botao_destino = QPushButton("Selecionar destino")
        self.botao_origem.clicked.connect(self.escolher_origem)
        self.botao_destino.clicked.connect(self.escolher_destino)
        opcoes.addWidget(self.botao_origem)
        opcoes.addWidget(self.botao_destino)
        root.addLayout(opcoes)

        comandos = QHBoxLayout()
        self.botao_preview = QPushButton("Pré-visualizar")
        self.botao_organizar = QPushButton("Organizar por tipo")
        self.botao_cancelar = QPushButton("Cancelar")
        self.botao_abrir = QPushButton("Abrir pasta organizada")
        self.botao_preview.clicked.connect(lambda: self.iniciar("preview"))
        self.botao_organizar.clicked.connect(lambda: self.iniciar("organizar"))
        self.botao_cancelar.clicked.connect(self.cancelar)
        self.botao_abrir.clicked.connect(self.abrir)
        self.botao_cancelar.setEnabled(False)
        self.botao_abrir.setEnabled(False)
        for botao in (self.botao_preview, self.botao_organizar, self.botao_cancelar, self.botao_abrir):
            comandos.addWidget(botao)
        root.addLayout(comandos)

        self.status = QLabel("Aguardando seleção.")
        root.addWidget(self.status)
        self.barra = QProgressBar()
        self.barra.setValue(0)
        root.addWidget(self.barra)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        root.addWidget(self.logs)

    def escolher_origem(self):
        pasta = QFileDialog.getExistingDirectory(self, "Pasta de origem")
        if pasta:
            self.origem = pasta
            self.label_origem.setText(f"Origem: {pasta}")

    def escolher_destino(self):
        pasta = QFileDialog.getExistingDirectory(self, "Pasta de destino")
        if pasta:
            self.destino = pasta
            self.label_destino.setText(f"Destino: {pasta}")

    def iniciar(self, tipo):
        if self.thread is not None:
            return
        if not self.origem or (tipo == "organizar" and not self.destino):
            QMessageBox.warning(self, "Seleção incompleta", "Escolha as pastas necessárias.")
            return
        if tipo == "organizar":
            try:
                validar_pastas(self.origem, self.destino)
            except ValueError as erro:
                QMessageBox.warning(self, "Destino inseguro", str(erro))
                return
        self.tipo_tarefa = tipo
        self.barra.setValue(0)
        self.logs.clear()
        self.status.setText("Analisando..." if tipo == "preview" else "Organizando...")
        self.alternar_botoes(True)
        self.thread = QThread(self)
        self.worker = Tarefa(tipo, self.origem, self.destino)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.executar)
        self.worker.progresso.connect(self.progresso)
        self.worker.pronto.connect(self.concluido)
        self.worker.falha.connect(self.falhou)
        self.worker.finalizado.connect(self.thread.quit)
        self.worker.finalizado.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.liberar)
        self.thread.start()

    def alternar_botoes(self, trabalhando):
        for botao in (self.botao_origem, self.botao_destino, self.botao_preview, self.botao_organizar):
            botao.setEnabled(not trabalhando)
        self.botao_cancelar.setEnabled(trabalhando and self.tipo_tarefa == "organizar")

    def progresso(self, atual, total):
        self.barra.setValue(int(atual * 100 / total) if total else 100)
        self.status.setText(f"Processados: {atual}/{total}")

    def concluido(self, dados):
        if self.tipo_tarefa == "preview":
            self.logs.append(f"Arquivos: {dados['total_arquivos']}")
            self.logs.append(f"Tamanho: {dados['tamanho_total']} bytes")
            for nome, total in sorted(dados["resumo"].items()):
                self.logs.append(f"{nome}: {total}")
            self.barra.setValue(100)
            self.status.setText("Prévia concluída (primeiro nível).")
        else:
            self.saida = dados["destino_base"]
            self.botao_abrir.setEnabled(Path(self.saida).is_dir())
            for erro in dados["erros"]:
                self.logs.append(f"ERRO: {erro['origem']} — {erro['erro']}")
            self.logs.append(f"Copiados: {dados['total_copiados']}")
            self.logs.append(f"Erros: {dados['total_erros']}")
            self.logs.append(f"Cancelado: {'sim' if dados['cancelado'] else 'não'}")
            self.status.setText("Operação cancelada." if dados["cancelado"] else
                                "Concluído com erros." if dados["total_erros"] else "Concluído.")
            if dados["total_encontrados"] == 0:
                self.barra.setValue(100)

    def falhou(self, mensagem):
        self.logs.append(f"Falha: {mensagem}")
        self.status.setText("Operação não concluída.")

    def cancelar(self):
        if self.worker is not None and self.tipo_tarefa == "organizar":
            self.worker.cancelar()
            self.botao_cancelar.setEnabled(False)
            self.status.setText("Cancelamento solicitado; aguardando cópia atual...")

    def liberar(self):
        self.thread = None
        self.worker = None
        self.tipo_tarefa = None
        self.alternar_botoes(False)

    def abrir(self):
        if self.saida and Path(self.saida).is_dir():
            subprocess.Popen(["open", self.saida])

    def closeEvent(self, event):
        if self.thread is not None:
            QMessageBox.information(self, "Operação ativa",
                                    "Aguarde a finalização ou solicite cancelamento.")
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = FluxorIntegrado()
    janela.show()
    sys.exit(app.exec())
