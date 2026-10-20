"""Fluxor Biblioteca — consulta local, sem copiar ou mover arquivos."""
import sys
from pathlib import Path
from PySide6.QtGui import QShortcut, QKeySequence

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QComboBox, QHeaderView, QTextEdit, QListWidget, QListWidgetItem, QStackedWidget, QStyle,
)
from fluxor_core.library import index_folder, search_files, catalog_summary, storage_diagnosis
from fluxor_core.duplicates import find_exact_duplicates
from fluxor_core.intelligence import radar_report, version_candidates
from fluxor_media import MediaPreview


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
        self.cancel_requested = False

    def cancel(self):
        self.cancel_requested = True

    @Slot()
    def run(self):
        try:
            self.finished.emit(find_exact_duplicates(self.database, cancel=lambda: self.cancel_requested))
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
        self.offset = 0
        self.page_size = 100
        self.review_paths = set()
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
        self.analysis_button = QPushButton("Radar · Descobertas")
        self.review_button = QPushButton("Adicionar à revisão")
        self.review_button.clicked.connect(self.add_review)
        self.review_list_button = QPushButton("Ver lista de revisão")
        self.review_list_button.clicked.connect(self.show_review)
        self.versions_button = QPushButton("Versões possíveis")
        self.versions_button.clicked.connect(self.show_versions)
        self.duplicates_button = QPushButton("Comparar duplicados")
        self.analysis_button.clicked.connect(self.diagnose)
        self.duplicates_button.clicked.connect(self.duplicates)
        tools.addWidget(self.ext_filter)
        tools.addWidget(self.analysis_button)
        tools.addWidget(self.versions_button)
        tools.addWidget(self.review_button)
        tools.addWidget(self.review_list_button)
        tools.addWidget(self.duplicates_button)
        self.cancel_button = QPushButton("Interromper análise")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_scan)
        tools.addWidget(self.cancel_button)
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
        self.visual_modes = QStackedWidget()
        self.visual_modes.addWidget(self.table)
        self.gallery = QListWidget()
        self.gallery.setViewMode(QListWidget.ViewMode.IconMode)
        self.gallery.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.gallery.setIconSize(__import__("PySide6.QtCore", fromlist=["QSize"]).QSize(44, 44))
        self.gallery.setGridSize(__import__("PySide6.QtCore", fromlist=["QSize"]).QSize(145, 100))
        self.gallery.itemClicked.connect(self.gallery_selected)
        self.visual_modes.addWidget(self.gallery)
        self.gallery_button = QPushButton("Alternar lista / galeria")
        self.gallery_button.clicked.connect(self.toggle_gallery)
        root.addWidget(self.gallery_button)
        root.addWidget(self.visual_modes)
        pages = QHBoxLayout()
        self.prev_button = QPushButton("← Anteriores")
        self.next_button = QPushButton("Próximos →")
        self.prev_button.clicked.connect(lambda: self.turn_page(-1))
        self.next_button.clicked.connect(lambda: self.turn_page(1))
        pages.addWidget(self.prev_button)
        pages.addWidget(self.next_button)
        root.addLayout(pages)
        self.quicklook = QShortcut(QKeySequence("Space"), self.table)
        self.quicklook.activated.connect(self.open_preview)
        self.inspector = QLabel("Selecione um arquivo para conferir seus dados. Clique duas vezes para abrir com o aplicativo padrão.")
        self.inspector.setWordWrap(True)
        root.addWidget(self.inspector)
        self.media = MediaPreview(self)
        self.media.setVisible(False)
        root.addWidget(self.media)
        self.table.itemDoubleClicked.connect(self.open_selected)
        self.refresh()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Escolher pasta para Biblioteca")
        if not folder:
            return
        self.index_button.setEnabled(False)
        self.analysis_button.setEnabled(False)
        self.duplicates_button.setEnabled(False)
        self.versions_button.setEnabled(False)
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
        self.versions_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def turn_page(self, direction):
        self.offset = max(0, self.offset + direction * self.page_size)
        self.refresh()

    def refresh(self, *args):
        if self.sender() in (self.search, self.category, self.ext_filter):
            self.offset = 0
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
                limit=self.page_size, offset=self.offset,
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
        self.gallery.clear()
        for index, row in enumerate(rows):
            item = QListWidgetItem(row["name"])
            item.setData(Qt.ItemDataRole.UserRole, row["path"])
            standard = QStyle.StandardPixmap.SP_FileIcon
            item.setIcon(self.style().standardIcon(standard))
            self.gallery.addItem(item)
        self.prev_button.setEnabled(self.offset > 0)
        self.next_button.setEnabled(len(rows) == self.page_size)

    def inspect(self):
        rows = self.table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        values = [self.table.item(row, col).text() for col in range(6)]
        self.media.setVisible(True)
        self.media.select_file(values[5])
        self.inspector.setText(
            f"Arquivo: {values[0]}  |  Categoria: {values[1]}  |  "
            f"Tamanho: {values[3]} bytes  |  Alterado: {values[4]}  |  "
            f"Local: {values[5]}"
        )

    def toggle_gallery(self):
        current = self.visual_modes.currentIndex()
        self.visual_modes.setCurrentIndex(1 - current)

    def gallery_selected(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        for row in range(self.table.rowCount()):
            cell = self.table.item(row, 5)
            if cell and cell.text() == path:
                self.table.selectRow(row)
                self.inspect()
                break

    def cancel_scan(self):
        if isinstance(self.worker, DuplicateWorker):
            self.worker.cancel()
            self.cancel_button.setEnabled(False)
            self.status.setText("Interrupção solicitada...")

    def open_preview(self):
        row = self.table.currentRow()
        item = self.table.item(row, 5) if row >= 0 else None
        if item and sys.platform == "darwin":
            path = Path(item.text())
            if path.is_file():
                import subprocess
                subprocess.Popen(["qlmanage", "-p", str(path)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def open_selected(self, item):
        import subprocess
        path_item = self.table.item(item.row(), 5)
        if not path_item:
            return
        path = Path(path_item.text())
        if path.is_file():
            subprocess.Popen(["open", str(path)])

    def add_review(self):
        row = self.table.currentRow()
        item = self.table.item(row, 5) if row >= 0 else None
        if item:
            self.review_paths.add(item.text())
            self.status.setText(f"Lista de revisão: {len(self.review_paths)} arquivos. Nenhuma alteração realizada.")

    def show_review(self):
        lines = ["LISTA DE REVISÃO — apenas nesta sessão, sem mover nem excluir arquivos."]
        lines.extend(sorted(self.review_paths))
        if not self.review_paths:
            lines.append("Selecione um arquivo e clique em Adicionar à revisão.")
        self.report.setPlainText("\n".join(lines))

    def show_versions(self):
        if not self.db.exists():
            return
        groups = version_candidates(self.db)
        lines = ["VERSÕES POSSÍVEIS — nomes semelhantes não confirmam igualdade."]
        for group in groups[:8]:
            lines.append(group["label"] + ": " + " | ".join(x["name"] for x in group["files"][:5]))
        if not groups:
            lines.append("Nenhuma versão provável detectada.")
        self.report.setPlainText("\n".join(lines))

    def diagnose(self):
        if not self.db.exists():
            return
        data = radar_report(self.db)
        lines = [
            f"RADAR — {data['total']} arquivos, {data['size']} bytes indexados",
            f"Grupos com tamanho igual (não verificados): {data['same_size_groups_unverified']}",
            "Categorias: " + ", ".join(f"{cat} — {size} bytes" for cat, count, size in data["categories"][:5]),
            "Maiores: " + ", ".join(f"{name} ({size} bytes)" for name, path, size in data["largest"][:5]),
        ]
        self.report.setPlainText("\n".join(lines))

    def duplicates(self):
        if not self.db.exists() or self.thread is not None:
            return
        self.status.setText("Comparando candidatos por tamanho e SHA-256...")
        self.index_button.setEnabled(False)
        self.analysis_button.setEnabled(False)
        self.duplicates_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
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
        self.status.setText("Análise interrompida." if data["cancelled"] else "Comparação concluída. Nenhum arquivo foi excluído.")

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
