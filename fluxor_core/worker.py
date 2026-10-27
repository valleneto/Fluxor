"""Worker de organizacao: executar fora da thread principal da interface.

Ainda NAO conectado a fluxor_mvp_v2.py. Integrar somente apos validar
os testes de seguranca e o comportamento no macOS.
"""
from PySide6.QtCore import QObject, Signal, Slot

from fluxor_core.organizer import organizar_por_tipo


class OrganizarWorker(QObject):
    progresso = Signal(int, int)
    concluido = Signal(dict)
    falhou = Signal(str)
    terminou = Signal()

    def __init__(self, origem, destino):
        super().__init__()
        self.origem = origem
        self.destino = destino
        self._cancelar = False

    @Slot()
    def executar(self):
        try:
            resultado = organizar_por_tipo(
                self.origem,
                self.destino,
                progresso=self.progresso.emit,
                cancelar=lambda: self._cancelar,
            )
            self.concluido.emit(resultado)
        except Exception as erro:
            self.falhou.emit(str(erro))
        finally:
            self.terminou.emit()

    @Slot()
    def solicitar_cancelamento(self):
        # Chamadas diretas ao metodo sao seguras para este indicador simples.
        # O motor verifica o indicador entre arquivos.
        self._cancelar = True
