"""FLUXOR folder browser optimized for large and network-mounted directories.

A deliberately non-native navigator: lists FOLDERS only, never follows
symlinks/aliases and executes filesystem calls on a daemon worker thread.
SMB/AFP-mounted volumes appear under /Volumes. It does not mount SFTP URLs.
"""
import os
import threading
import heapq
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QMessageBox,
)
from fluxor_network import connect_smb

PAGE = 140


class _FolderResults(QObject):
    ready = Signal(int, str, object, bool, str, bool)


class SafeFolderPicker(QDialog):
    """Nonblocking, page-at-a-time directory navigator. Read-only browsing."""

    def __init__(self, parent=None, title="Escolher pasta", initial=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(540, 395)
        self.setModal(True)
        self.selected_path = ""
        self._path = ""
        self._offset = 0
        self._cursor = None
        self._ticket = 0
        self._busy = False
        self._loading_select = False
        self._results = _FolderResults()
        self._results.ready.connect(self._on_ready)

        root = QVBoxLayout(self)
        tip = QLabel(
            "Pastas em disco ou compartilhamentos montados. "
            "Atalhos e links simbólicos não são seguidos."
        )
        tip.setWordWrap(True)
        root.addWidget(tip)
        line = QHBoxLayout()
        self.address = QLineEdit()
        self.address.setPlaceholderText("Caminho local ou montado, ex.: /Volumes/Compartilhamento")
        self.address.returnPressed.connect(self._go_address)
        line.addWidget(self.address, 1)
        self.go_button = QPushButton("Ir")
        self.go_button.clicked.connect(self._go_address)
        line.addWidget(self.go_button)
        root.addLayout(line)

        shortcuts = QHBoxLayout()
        for title_text, path in (
            ("Início", str(Path.home())),
            ("Downloads", str(Path.home() / "Downloads")),
            ("Rede montada", "/Volumes"),
        ):
            button = QPushButton(title_text)
            button.clicked.connect(lambda _, value=path: self._start(value))
            shortcuts.addWidget(button)
        # Preserve the two-button organization screen and simple library toolbar.
        # Network connection lives here, at the point where folders are chosen.
        self.network_button = QPushButton("Conectar SMB (Finder)")
        self.network_button.setToolTip(
            "Solicita a montagem no Finder. Depois escolha a pasta em /Volumes."
        )
        self.network_button.clicked.connect(lambda: connect_smb(self))
        shortcuts.addWidget(self.network_button)
        root.addLayout(shortcuts)

        self.folders = QListWidget()
        self.folders.itemDoubleClicked.connect(self._open_item)
        root.addWidget(self.folders, 1)
        self.status = QLabel("Selecione uma pasta ou cole um caminho completo.")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        actions = QHBoxLayout()
        self.up_button = QPushButton("Pasta acima")
        self.up_button.clicked.connect(self._up)
        actions.addWidget(self.up_button)
        self.more_button = QPushButton("Mostrar mais pastas")
        self.more_button.clicked.connect(self._more)
        actions.addWidget(self.more_button)
        actions.addStretch()
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        actions.addWidget(self.cancel_button)
        self.choose_button = QPushButton("Selecionar esta pasta")
        self.choose_button.setObjectName("primaryAction")
        self.choose_button.clicked.connect(self._choose)
        actions.addWidget(self.choose_button)
        root.addLayout(actions)

        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.setInterval(9000)
        self._timeout.timeout.connect(self._slow_notice)
        self._start(initial or str(Path.home()))

    def _slow_notice(self):
        if self._busy:
            self.status.setText(
                "A rede está demorando para responder. A janela continua ativa. "
                "Você pode tentar outro caminho ou cancelar; o sistema ainda pode "
                "estar aguardando a conexão anterior."
            )

    def _go_address(self):
        typed = self.address.text().strip()
        if typed.lower().startswith(("sftp://", "ssh://", "smb://", "afp://")):
            # Invalidate a previous valid folder; a wrong address must NEVER
            # leave the former selection silently active.
            self._ticket += 1
            self._timeout.stop()
            self._busy = False
            self._path = ""
            self.selected_path = ""
            self._cursor = None
            self.folders.clear()
            self.more_button.setVisible(False)
            self._set_enabled()
            self.status.setText(
                "Este navegador usa pastas montadas pelo macOS, não URLs. "
                "Monte o compartilhamento SMB pelo Finder e selecione a pasta em /Volumes."
            )
            return
        if typed:
            self._start(typed)

    def _start(self, requested, offset=0, select=False):
        self._ticket += 1
        token = self._ticket
        cursor = self._cursor if offset and requested == self._path else None
        self._offset = offset
        if cursor is None:
            self._cursor = None
        self._busy = True
        self._loading_select = select
        self._set_enabled()
        self.status.setText("Lendo apenas nomes de pastas, sem examinar seus arquivos…")
        self._timeout.start()
        job = threading.Thread(
            target=self._scan,
            args=(token, requested, cursor, select),
            daemon=True, name="fluxor-folder-picker",
        )
        job.start()

    def _scan(self, token, requested, cursor, select):
        """Filesystem calls never run in the Qt main GUI thread."""
        try:
            path = Path(requested).expanduser()
            if not path.is_absolute():
                raise ValueError("Informe um caminho completo que comece por '/'.")
            # Refuse aliases/symlinks in any path component, to avoid Finder loops.
            if any(p.is_symlink() for p in (path, *path.parents)):
                raise ValueError(
                    "O caminho contém um atalho ou link simbólico. "
                    "Navegue até a pasta real, por exemplo em /Volumes."
                )
            if not path.is_dir():
                raise ValueError("Pasta inexistente, indisponível ou sem acesso.")
            canonical = str(path.resolve())
            if select:
                self._results.ready.emit(token, canonical, [], False, "", True)
                return
            # Keyset paging: no repeated/omitted entries due to unstable
            # os.scandir ordering. Bound memory to PAGE+1 while scanning.
            def folders_after_cursor():
                with os.scandir(path) as entries:
                    for item in entries:
                        if token != self._ticket:
                            return
                        if item.is_symlink() or not item.is_dir(follow_symlinks=False):
                            continue
                        name = item.name
                        key = (name.casefold(), name)
                        if cursor is None or key > cursor:
                            yield (key, name, item.path)
            page = heapq.nsmallest(PAGE + 1, folders_after_cursor(),
                                    key=lambda value: value[0])
            has_more = len(page) > PAGE
            items = [(name, absolute) for _, name, absolute in page[:PAGE]]

            self._results.ready.emit(token, canonical, items, has_more, "", False)
        except (OSError, ValueError) as exc:
            self._results.ready.emit(token, requested, [], False, str(exc), select)

    def _on_ready(self, token, path, entries, has_more, error, select):
        if token != self._ticket:
            return
        self._timeout.stop()
        self._busy = False
        if error:
            # Prevent accidentally selecting the PREVIOUS folder after a failed
            # network jump or a refused symlink.
            self._path = ""
            self._cursor = None
            self.folders.clear()
            self.more_button.setVisible(False)
            self._set_enabled()
            self.status.setText("Não foi possível acessar: " + error)
            return
        if select:
            self.selected_path = path
            self.accept()
            return
        self._path = path
        self.address.setText(path)
        if self._offset == 0:
            self.folders.clear()
        for name, absolute in entries:
            item = QListWidgetItem("  " + name)
            item.setData(Qt.ItemDataRole.UserRole, absolute)
            self.folders.addItem(item)
        if entries:
            last_name = entries[-1][0]
            self._cursor = (last_name.casefold(), last_name)
        self.more_button.setVisible(has_more)
        self._set_enabled()
        self.status.setText(
            f"{self.folders.count()} pastas exibidas em ordem alfabética. "
            "A pasta pode mudar na rede; recarregue para conferir alterações. "
            "Dê dois cliques para entrar ou escolha esta pasta."
        )

    def _set_enabled(self):
        # Choosing is always explicit; do not accept during a pending scan.
        self.choose_button.setEnabled(not self._busy and bool(self._path))
        self.more_button.setEnabled(not self._busy)
        self.up_button.setEnabled(not self._busy and bool(self._path))
        self.go_button.setEnabled(True)

    def _open_item(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self._start(path)

    def _up(self):
        if self._path:
            self._start(str(Path(self._path).parent))

    def _more(self):
        if self._path and not self._busy:
            self._start(self._path, self._offset + PAGE)

    def _choose(self):
        if self._path and not self._busy:
            self._start(self._path, select=True)

    @classmethod
    def get_directory(cls, parent=None, title="Escolher pasta", initial=None):
        dialog = cls(parent, title=title, initial=initial)
        return dialog.selected_path if dialog.exec() == QDialog.DialogCode.Accepted else ""
