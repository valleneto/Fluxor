"""Fluxor Biblioteca — consulta local, sem copiar ou mover arquivos."""
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QComboBox, QHeaderView, QTextEdit,
)
from fluxor_core.library import index_folder, search_files, catalog_summary, storage_diagnosis
from fluxor_core.duplicates import find_exact_duplicates


class SortableItem(QTableWidgetItem):
    def __init__(self, label, sort_value=None):
        super().__init__(str(label))
        self.sort_value = sort_value if sort_value is not None else str(label).casefold()

    def __lt__(self, other):
        if isinstance(other, SortableItem):
            return self.sort_value < other.sort_value
        return super().__lt__(other)


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


class DuplicateWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    done = Signal()

    def __init__(self, database):
        super().__init__()
        self.database = database

    @Slot()
    def run(self):
        try:
            self.finished.emit(find_exact_duplicates(self.database))
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
        tools = QHBoxLayout()
        self.ext_filter = QLineEdit()
        self.ext_filter.setPlaceholderText("Extensão: .pdf")
        self.ext_filter.textChanged.connect(self.refresh)
        self.analysis_button = QPushButton("Diagnóstico")
        self.duplicates_button = QPushButton("Comparar duplicados")
        self.analysis_button.clicked.connect(self.diagnose)
        self.duplicates_button.clicked.connect(self.duplicates)
        tools.addWidget(self.ext_filter)
        tools.addWidget(self.analysis_button)
        tools.addWidget(self.duplicates_button)
        root.addLayout(tools)
        self.report = QTextEdit()
        self.report.setReadOnly(True)
        self.report.setMaximumHeight(115)
        root.addWidget(self.report)
        self.status = QLabel("Biblioteca local. Nenhum arquivo será copiado.")
        root.addWidget(self.status)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Nome", "Categoria", "Projeto sugerido", "Tamanho", "Modificado", "Caminho original"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.itemSelectionChanged.connect(self.inspect)
        root.addWidget(self.table)
        self.inspector = QLabel("Selecione um arquivo para conferir seus dados. Clique duas vezes para abrir com o aplicativo padrão.")
        self.inspector.setWordWrap(True)
        root.addWidget(self.inspector)
        self.table.itemDoubleClicked.connect(self.open_selected)
        self.refresh()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Escolher pasta para Biblioteca")
        if not folder:
            return
        self.index_button.setEnabled(False)
        self.analysis_button.setEnabled(False)
        self.duplicates_button.setEnabled(False)
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
        self.analysis_button.setEnabled(True)
        self.duplicates_button.setEnabled(True)

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
                extension=self.ext_filter.text().strip() or None,
            )
        except Exception as error:
            self.status.setText(f"Falha ao consultar índice: {error}")
            return
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            from datetime import datetime
            values = (row["name"], row["category"], row["project"], row["size"],
                      datetime.fromtimestamp(row["modified"]).strftime("%d/%m/%Y %H:%M"), row["path"])
            for j, value in enumerate(values):
                cell = SortableItem(value, row["size"] if j == 3 else row["modified"] if j == 4 else None)
                self.table.setItem(i, j, cell)
        self.table.setSortingEnabled(True)

    def inspect(self):
        rows = self.table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        values = [self.table.item(row, col).text() for col in range(6)]
        self.inspector.setText(
            f"Arquivo: {values[0]}  |  Categoria: {values[1]}  |  "
            f"Tamanho: {values[3]} bytes  |  Alterado: {values[4]}  |  "
            f"Local: {values[5]}"
        )

    def open_selected(self, item):
        import subprocess
        path_item = self.table.item(item.row(), 5)
        if not path_item:
            return
        path = Path(path_item.text())
        if path.is_file():
            subprocess.Popen(["open", str(path)])

    def diagnose(self):
        if not self.db.exists():
            return
        data = storage_diagnosis(self.db)
        self.report.setPlainText(
            f"Arquivos: {data['total']} | Volume: {data['size']} bytes\\n"
            + "Categorias por espaço: "
            + ", ".join(f"{cat}: {size} bytes" for cat, count, size in data["categories"][:5])
            + "\\nMaiores: "
            + ", ".join(f"{name} ({size} bytes)" for path, name, size in data["largest"][:5])
        )

    def duplicates(self):
        if not self.db.exists() or self.thread is not None:
            return
        self.status.setText("Comparando candidatos por tamanho e SHA-256...")
        self.index_button.setEnabled(False)
        self.analysis_button.setEnabled(False)
        self.duplicates_button.setEnabled(False)
        self.thread = QThread(self)
        self.worker = DuplicateWorker(str(self.db))
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.show_duplicates)
        self.worker.error.connect(self.failed)
        self.worker.done.connect(self.thread.quit)
        self.worker.done.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.cleaned)
        self.thread.start()

    def show_duplicates(self, data):
        self.report.setPlainText(
            f"Grupos idênticos: {len(data['groups'])} | "
            f"Espaço redundante potencial: {data['potential_redundant_bytes']} bytes\\n"
            + "\\n".join(" = ".join(group["paths"]) for group in data["groups"][:12])
        )
        self.status.setText("Comparação concluída. Nenhum arquivo foi excluído.")

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
