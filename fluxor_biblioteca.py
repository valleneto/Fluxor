"""Fluxor Biblioteca — consulta local, sem copiar ou mover arquivos."""
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QComboBox, QHeaderView,
)
from fluxor_core.library import index_folder, search_files, catalog_summary


class IndexWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    done = Signal()

    def __init__(self, folder, db):
        super().__init__()
        self.folder = folder
        self.db = db

    @Slot()
    def run(self):
        try:
            self.finished.emit(index_folder(self.folder, self.db))
        except Exception as error:
            self.error.emit(str(error))
        finally:
            self.done.emit()


class Biblioteca(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluxor | Biblioteca")
        self.resize(940, 650)
        self.db = Path.home() / ".fluxor" / "library.db"
        self.thread = None
        self.worker = None
        root = QVBoxLayout(self)
        title = QLabel("Fluxor Biblioteca — sem mover arquivos")
        title.setStyleSheet("font-size: 22px; font-weight: 650")
        root.addWidget(title)
        self.folder_label = QLabel("Nenhuma pasta indexada nesta sessão")
        root.addWidget(self.folder_label)
        controls = QHBoxLayout()
        self.index_button = QPushButton("Adicionar / atualizar pasta")
        self.index_button.clicked.connect(self.choose_folder)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar pelo nome do arquivo")
        self.search.textChanged.connect(self.refresh)
        self.category = QComboBox()
        self.category.addItem("Todas as categorias")
        self.category.currentTextChanged.connect(self.refresh)
        controls.addWidget(self.index_button)
        controls.addWidget(self.search)
        controls.addWidget(self.category)
        root.addLayout(controls)
        self.status = QLabel("Biblioteca local. Nenhum arquivo será copiado.")
        root.addWidget(self.status)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nome", "Categoria", "Projeto sugerido", "Tamanho", "Caminho original"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.table)
        self.refresh()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Escolher pasta para Biblioteca")
        if not folder:
            return
        self.index_button.setEnabled(False)
        self.status.setText("Indexando metadados em segundo plano...")
        self.thread = QThread(self)
        self.worker = IndexWorker(folder, str(self.db))
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda result: self.indexed(folder, result))
        self.worker.error.connect(self.failed)
        self.worker.done.connect(self.thread.quit)
        self.worker.done.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.cleaned)
        self.thread.start()

    def indexed(self, folder, result):
        self.folder_label.setText(f"Última pasta indexada: {folder}")
        self.status.setText(f"Indexados nesta pasta: {result['total']} arquivos; {result['size']} bytes")
        self.refresh()

    def failed(self, message):
        QMessageBox.warning(self, "Não foi possível indexar", message)
        self.status.setText("Falha na indexação.")

    def cleaned(self):
        self.thread = None
        self.worker = None
        self.index_button.setEnabled(True)

    def refresh(self, *args):
        if not self.db.exists():
            return
        try:
            summary = catalog_summary(self.db)
            current = self.category.currentText()
            self.category.blockSignals(True)
            self.category.clear()
            self.category.addItem("Todas as categorias")
            self.category.addItems([category for category, count in summary["categories"]])
            match = self.category.findText(current)
            self.category.setCurrentIndex(match if match >= 0 else 0)
            self.category.blockSignals(False)
            selected = self.category.currentText()
            rows = search_files(
                self.db, text=self.search.text(),
                category=None if selected == "Todas as categorias" else selected,
            )
        except Exception as error:
            self.status.setText(f"Falha ao consultar índice: {error}")
            return
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, key in enumerate(("name", "category", "project", "size", "path")):
                self.table.setItem(i, j, QTableWidgetItem(str(row[key])))

    def closeEvent(self, event):
        if self.thread is not None:
            QMessageBox.information(self, "Indexação", "Aguarde a indexação terminar.")
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Biblioteca()
    window.show()
    sys.exit(app.exec())
