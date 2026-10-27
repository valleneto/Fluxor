"""Fluxor Biblioteca — consulta local, sem copiar ou mover arquivos."""
import sys
from pathlib import Path
from PySide6.QtGui import QShortcut, QKeySequence

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QComboBox, QHeaderView, QTextEdit, QListWidget, QListWidgetItem, QStackedWidget, QStyle, QSplitter, QDialog, QDialogButtonBox, QAbstractItemView,
)
from fluxor_core.library import index_folder, search_files, catalog_summary, storage_diagnosis
from fluxor_core.duplicates import find_exact_duplicates
from fluxor_core.intelligence import radar_report, version_candidates
from fluxor_media import MediaPreview
from fluxor_folder_picker import SafeFolderPicker
from fluxor_network import connect_smb
from fluxor_core.workspace import review_add, review_list, collection_add, collection_list


def human_size(value):
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024


class SortableItem(QTableWidgetItem):
    def __init__(self, label, sort_value=None):
        super().__init__(str(label))
        self.sort_value = sort_value if sort_value is not None else str(label).casefold()

    def __lt__(self, other):
        if isinstance(other, SortableItem):
            return self.sort_value < other.sort_value
        return super().__lt__(other)


class IndexWorker(QObject):
    progress = Signal(int)
    finished = Signal(dict)
    error = Signal(str)
    cancelled = Signal(str)
    done = Signal()

    def __init__(self, folder, db):
        super().__init__()
        self.folder = folder
        self.db = db
        self.cancel_requested = False

    def cancel(self):
        self.cancel_requested = True

    @Slot()
    def run(self):
        try:
            self.finished.emit(index_folder(self.folder, self.db, cancel=lambda: self.cancel_requested, progress=self.progress.emit))
        except InterruptedError as error:
            self.cancelled.emit(str(error))
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
        self.last_outcome = 'idle'
        self.offset = 0
        self.page_size = 100
        self.sort_field = "modified"
        self.sort_descending = True
        self.review_db = Path.home() / '.fluxor' / 'workspace.db'
        self.review_paths = set(review_list(self.review_db))
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)
        eyebrow = QLabel("SEU ACERVO, NO SEU CONTROLE")
        eyebrow.setObjectName("sectionEyebrow")
        root.addWidget(eyebrow)
        title = QLabel("Biblioteca")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        self.folder_label = QLabel("Explore seus arquivos sem movê-los. Selecione um item para ver os detalhes.")
        self.folder_label.setWordWrap(True)
        root.addWidget(self.folder_label)
        controls = QHBoxLayout()
        self.index_button = QPushButton("+  Adicionar pasta")
        self.index_button.setObjectName("primaryAction")
        self.index_button.clicked.connect(self.choose_folder)
        self.smb_button = QPushButton("SMB (Finder)")
        self.smb_button.setToolTip("Solicitar montagem SMB via Finder; após conectar, selecione /Volumes.")
        self.smb_button.clicked.connect(lambda: connect_smb(self))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar por nome…")
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(180)
        self.search_timer.timeout.connect(self.refresh)
        self.search.textChanged.connect(self.delayed_refresh)
        self.project_filter = QComboBox()
        self.project_filter.addItem("Todos os projetos")
        self.project_filter.currentTextChanged.connect(self.refresh)
        self.category = QComboBox()
        self.category.addItem("Todas as categorias")
        self.category.currentTextChanged.connect(self.refresh)
        controls.addWidget(self.index_button)
        controls.addWidget(self.smb_button)
        controls.addWidget(self.search)
        controls.addWidget(self.category)
        root.addLayout(controls)
        tools = QHBoxLayout()
        self.size_filter = QComboBox()
        self.size_filter.addItems(["Qualquer tamanho", "Acima de 10 MB", "Acima de 100 MB", "Acima de 1 GB"])
        self.size_filter.currentTextChanged.connect(self.refresh)
        self.ext_filter = QLineEdit()
        self.ext_filter.setPlaceholderText("Extensão: .pdf")
        self.ext_filter.textChanged.connect(self.delayed_refresh)
        self.analysis_button = QPushButton("Radar · Descobertas")
        self.review_button = QPushButton("Adicionar à revisão")
        self.review_button.clicked.connect(self.add_review)
        self.review_list_button = QPushButton("Ver lista de revisão")
        self.review_list_button.clicked.connect(self.show_review)
        self.collection_button = QPushButton("Salvar coleção")
        self.collection_button.clicked.connect(self.save_collection)
        self.versions_button = QPushButton("Versões possíveis")
        self.versions_button.clicked.connect(self.show_versions)
        self.duplicates_button = QPushButton("Comparar duplicados")
        self.analysis_button.clicked.connect(self.diagnose)
        self.duplicates_button.clicked.connect(self.duplicates)
        # Keep controls usable on 13-inch laptop viewports: avoid one oversized row.
        tools.addWidget(self.ext_filter, 1)
        tools.addWidget(self.size_filter)
        tools.addWidget(self.project_filter)
        self.advanced_toggle = QPushButton("Filtros e ferramentas  ▾")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setToolTip("Mostrar ou ocultar ferramentas secundárias")
        root.addWidget(self.advanced_toggle)
        self.advanced_panel = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_panel)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.addLayout(tools)

        analysis_actions = QHBoxLayout()
        for button in (self.analysis_button, self.versions_button, self.duplicates_button):
            analysis_actions.addWidget(button)
        analysis_actions.addStretch()
        advanced_layout.addLayout(analysis_actions)

        review_actions = QHBoxLayout()
        for button in (self.review_button, self.review_list_button, self.collection_button):
            review_actions.addWidget(button)
        review_actions.addStretch()
        advanced_layout.addLayout(review_actions)

        self.cancel_button = QPushButton("Interromper análise")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_scan)
        self.report = QTextEdit()
        self.report.setReadOnly(True)
        self.report.setMaximumHeight(100)
        self.report.setPlaceholderText("Radar, versões e lista de revisão aparecerão aqui.")
        advanced_layout.addWidget(self.report)
        root.addWidget(self.advanced_panel)
        self.advanced_panel.setVisible(False)
        self.advanced_toggle.toggled.connect(self.advanced_panel.setVisible)
        self.advanced_toggle.toggled.connect(
            lambda open_: self.advanced_toggle.setText(
                "Recolher filtros e ferramentas  ▴" if open_ else "Filtros e ferramentas  ▾"
            )
        )
        self.status = QLabel("Biblioteca local. Nenhum arquivo será copiado.")
        self.status.setWordWrap(True)
        status_bar = QHBoxLayout()
        status_bar.addWidget(self.status, 1)
        status_bar.addWidget(self.cancel_button)
        root.addLayout(status_bar)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Nome", "Categoria", "Projeto sugerido", "Tamanho", "Modificado", "Caminho original"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)
        header.setSortIndicator(4, Qt.SortOrder.DescendingOrder)
        header.sectionClicked.connect(self.sort_by_column)
        self.table.setColumnHidden(5, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(False)
        self.table.itemSelectionChanged.connect(self.inspect)
        self.table.cellClicked.connect(lambda row, column: self.inspect())
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
        self.browser_split = QSplitter(Qt.Orientation.Horizontal)
        self.browser_split.addWidget(self.visual_modes)
        root.addWidget(self.browser_split)
        pages = QHBoxLayout()
        self.prev_button = QPushButton("← Anteriores")
        self.next_button = QPushButton("Próximos →")
        self.prev_button.clicked.connect(lambda: self.turn_page(-1))
        self.next_button.clicked.connect(lambda: self.turn_page(1))
        pages.addWidget(self.prev_button)
        pages.addWidget(self.next_button)
        root.addLayout(pages)
        self.quicklook = QShortcut(QKeySequence("Space"), self.visual_modes)
        self.quicklook.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.quicklook.activated.connect(self.open_preview)
        self.media = MediaPreview(self, embedded=True)
        self.media.close_requested.connect(self.close_inspector)
        self.media.setMinimumWidth(260)
        self.media.setMaximumWidth(440)
        self.browser_split.addWidget(self.media)
        self.browser_split.setStretchFactor(0, 3)
        self.browser_split.setStretchFactor(1, 2)
        self.media.setVisible(False)
        self.table.itemDoubleClicked.connect(self.open_selected)
        self.refresh()

    def choose_folder(self):
        folder = SafeFolderPicker.get_directory(self, "Escolher pasta para Biblioteca (rede montada)")
        if not folder:
            return
        self.index_button.setEnabled(False)
        self.analysis_button.setEnabled(False)
        self.duplicates_button.setEnabled(False)
        self.versions_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setVisible(True)
        self.last_outcome = "running"
        self.status.setText("Indexando metadados em segundo plano...")
        self.thread = QThread(self)
        self.worker = IndexWorker(folder, str(self.db))
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda result: self.indexed(folder, result))
        self.worker.progress.connect(lambda amount: self.status.setText(f"Indexando... {amount:,} arquivos examinados."))
        self.worker.error.connect(self.failed)
        self.worker.cancelled.connect(self.index_cancelled)
        self.worker.done.connect(self.thread.quit)
        self.worker.done.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.cleaned)
        self.thread.start()

    def indexed(self, folder, result):
        self.last_outcome = "partial" if result["warnings"] else "success"
        self.folder_label.setText(f"Última pasta indexada: {folder}")
        self.status.setText(f"Indexados nesta pasta: {result['total']} arquivos; {result['size']} bytes")
        self.refresh()

    def index_cancelled(self, message):
        self.last_outcome = "cancelled"
        self.status.setText(message)

    def failed(self, message):
        self.last_outcome = "error"
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
        self.cancel_button.setVisible(False)

    def sort_by_column(self, column):
        choices = {0: "name", 1: "category", 2: "project", 3: "size", 4: "modified"}
        key = choices.get(column)
        if key is None:
            return
        self.sort_descending = not self.sort_descending if key == self.sort_field else key in ("size", "modified")
        self.sort_field = key
        self.offset = 0
        self.table.horizontalHeader().setSortIndicator(
            column, Qt.SortOrder.DescendingOrder if self.sort_descending else Qt.SortOrder.AscendingOrder
        )
        self.refresh()

    def delayed_refresh(self, *args):
        self.offset = 0
        self.search_timer.start()

    def turn_page(self, direction):
        self.offset = max(0, self.offset + direction * self.page_size)
        self.refresh()

    def refresh(self, *args):
        if hasattr(self, "media"):
            self.close_inspector()
        if self.sender() in (self.search, self.category, self.ext_filter, self.size_filter, self.project_filter):
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
            previous_project = self.project_filter.currentText()
            self.project_filter.blockSignals(True)
            self.project_filter.clear()
            self.project_filter.addItem("Todos os projetos")
            self.project_filter.addItems([name for name, count in summary["projects"]])
            self.project_filter.setCurrentIndex(max(0, self.project_filter.findText(previous_project)))
            self.project_filter.blockSignals(False)
            selected = self.category.currentText()
            rows = search_files(
                self.db, text=self.search.text(),
                category=None if selected == "Todas as categorias" else selected,
                extension=self.ext_filter.text().strip() or None,
                min_size=({1:10,2:100,3:1024}.get(self.size_filter.currentIndex()) or 0)*1024*1024 or None,
                project=self.project_filter.currentText() if self.project_filter.currentIndex() > 0 else None,
                sort=self.sort_field, descending=self.sort_descending,
                limit=self.page_size + 1, offset=self.offset,
            )
        except Exception as error:
            self.status.setText(f"Falha ao consultar índice: {error}")
            return
        has_more = len(rows) > self.page_size
        rows = rows[:self.page_size]
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            from datetime import datetime
            values = (row["name"], row["category"], row["project"], human_size(row["size"]),
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
        self.next_button.setEnabled(has_more)

    def inspect(self):
        row = self.table.currentRow()
        if not self.table.selectedItems() or row < 0 or any(self.table.item(row, col) is None for col in range(6)):
            self.media.setVisible(False)
            return
        values = [self.table.item(row, col).text() for col in range(6)]
        was_hidden = self.media.isHidden()
        self.media.setVisible(True)
        if was_hidden:
            self.browser_split.setSizes([650, 330])
        if self.media.selected != values[5]:
            self.media.select_file(values[5])
        self.media.set_metadata(values)

    def close_inspector(self):
        """Hide previews and return the full content width to the library."""
        if not hasattr(self, "media"):
            return
        self.media.reset_selection()
        self.media.setVisible(False)
        self.table.blockSignals(True)
        self.table.clearSelection()
        self.table.blockSignals(False)
        self.gallery.clearSelection()

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
        if isinstance(self.worker, (DuplicateWorker, IndexWorker)):
            self.worker.cancel()
            self.cancel_button.setEnabled(False)
            self.status.setText("Interrupção solicitada...")

    def open_preview(self):
        """Native popup is preserved; embedded media remains optional."""
        row = self.table.currentRow()
        item = self.table.item(row, 5) if row >= 0 else None
        if item and sys.platform == "darwin":
            import subprocess
            path = Path(item.text())
            if path.is_file():
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
            try:
                review_add(self.review_db, item.text())
            except (OSError, ValueError, __import__("sqlite3").DatabaseError) as error:
                self.status.setText(f"Não foi possível salvar a revisão: {error}")
                return
            self.review_paths.add(item.text())
            self.status.setText(f"Lista de revisão: {len(self.review_paths)} arquivos. Nenhuma alteração realizada.")

    def show_review(self):
        lines = ["LISTA DE REVISÃO — apenas nesta sessão, sem mover nem excluir arquivos."]
        lines.extend(review_list(self.review_db))
        if not self.review_paths:
            lines.append("Selecione um arquivo e clique em Adicionar à revisão.")
        self.report.setPlainText("\n".join(lines))

    def save_collection(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Coleção virtual", "Nome da coleção:")
        if not ok or not name.strip():
            return
        try:
            collection_add(self.review_db, name, review_list(self.review_db))
            summaries = collection_list(self.review_db)
        except (OSError, ValueError, __import__("sqlite3").DatabaseError) as error:
            QMessageBox.warning(self, "Não foi possível salvar", str(error))
            return
        self.report.setPlainText(
            "Coleções virtuais (nenhum arquivo movido):\n" +
            "\n".join(f"{title}: {count} itens" for title, count in summaries)
        )

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
        answer = QMessageBox.question(self, "Comparar conteúdo",
            "A comparação pode ler arquivos de provedores em nuvem. Continue apenas se a pasta for local.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.last_outcome = "running"
        self.status.setText("Comparando candidatos por tamanho e SHA-256...")
        self.index_button.setEnabled(False)
        self.analysis_button.setEnabled(False)
        self.duplicates_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setVisible(True)
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
        self.last_outcome = "cancelled" if data["cancelled"] else "partial" if data["errors"] else "success"
        self.report.setPlainText(
            f"Duplicados verificados: {len(data['groups'])} grupos; "
            f"volume redundante estimado: {data['potential_redundant_bytes']} bytes. "
            "Nenhum arquivo será excluído."
        )
        if data["cancelled"]:
            self.status.setText("Análise interrompida. Resultados parciais descartados.")
            return
        self.status.setText("Comparação concluída com avisos." if data["errors"] else "Comparação concluída. Revise os arquivos antes de decidir.")
        if not data["groups"]:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Duplicate Center · Revisão segura")
        dialog.resize(680, 430)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Arquivos com conteúdo idêntico (SHA-256). Selecione para revisão, sem excluir."))
        choices = QListWidget(dialog)
        choices.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        for number, group in enumerate(data["groups"], 1):
            for path in group["paths"]:
                entry = QListWidgetItem(f"Grupo {number}  •  {path}")
                entry.setData(Qt.ItemDataRole.UserRole, path)
                choices.addItem(entry)
        layout.addWidget(choices)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        add_button = buttons.addButton("Adicionar selecionados à revisão", QDialogButtonBox.ButtonRole.ActionRole)
        def save_selected():
            for entry in choices.selectedItems():
                path = entry.data(Qt.ItemDataRole.UserRole)
                review_add(self.review_db, path)
                self.review_paths.add(path)
            self.status.setText(f"Revisão: {len(self.review_paths)} arquivos salvos; nenhum original alterado.")
            dialog.accept()
        add_button.clicked.connect(save_selected)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

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
