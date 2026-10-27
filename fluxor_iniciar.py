"""Fluxor Control — single-window navigation with preserved page state."""
import sys
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QMessageBox, QFrame, QCheckBox, QScrollArea, QGridLayout,
)
from fluxor_biblioteca import Biblioteca
from fluxor_app_integrado import FluxorIntegrado
from fluxor_zen import ZenCore
from fluxor_core.library import catalog_summary


class Inicio(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FLUXOR — Find what matters")
        asset_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        logo_path = asset_root / "assets" / "fluxor_logo.png"
        if logo_path.is_file():
            self.setWindowIcon(QIcon(str(logo_path)))
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            self.resize(
                min(1100, max(640, available.width() - 48)),
                min(700, max(480, available.height() - 64)),
            )
        else:
            self.resize(1000, 650)
        self.setStyleSheet("""
            QWidget { background-color: #0b101b; color: #e7f1fb; font-family: 'Helvetica Neue'; font-size: 13px; }
            QLabel { background: transparent; }
            QLabel#eyebrow { color: #67def1; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            QPushButton { background: #151f33; color: #e9f2fa; border: 1px solid #263a54;
                          padding: 9px 14px; border-radius: 9px; }
            QPushButton:hover { background: #202c47; border-color: #24c8eb; }
            QPushButton:pressed { background: #283b64; }
            QPushButton:disabled { color: #718194; background: #182330; border-color: #243141; }
            QLineEdit, QComboBox { background: #182433; border: 1px solid #314358;
                                  padding: 8px; border-radius: 8px; selection-background-color: #287987; }
            QTableWidget, QListWidget, QTextEdit { background: #151f2c; alternate-background-color: #1b2939;
                        color: #e6eff7; border: 1px solid #304255; border-radius: 11px;
                        gridline-color: #253547; selection-background-color: #225864; }
            QHeaderView::section { background: #243347; color: #d8e5f0; border: none;
                                   border-right: 1px solid #33465b; padding: 9px; }
            QStackedWidget, QScrollArea { border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QWidget#mediaPanel { background: #182433; border: 1px solid #304255; border-radius: 14px; }
            QFrame#sidebar { background: #111827; border: 1px solid #25334f; border-radius: 13px; }
            QScrollBar:vertical { background: #14202d; width: 10px; }
            QScrollBar::handle:vertical { background: #43566b; border-radius: 4px; min-height: 22px; }
        """)
        self.history = []
        self.future = []
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(14)
        sidebar = QFrame()
        self.sidebar = sidebar
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)
        side = QVBoxLayout(sidebar)
        wordmark = QLabel("FLUXOR /")
        wordmark.setStyleSheet("color: #69dcf5; font-family: 'Arial Black'; font-size: 24px; font-style: italic; font-weight: 900; padding: 18px 4px 5px 4px;")
        side.addWidget(wordmark)
        side.addWidget(QLabel("Find what matters."))
        self.side_home = QPushButton("⌂   Visão geral")
        self.side_library = QPushButton("▤   Biblioteca")
        self.side_organize = QPushButton("◈   Organização segura")
        self.side_home.clicked.connect(lambda: self.navigate(0))
        self.side_library.clicked.connect(lambda: self.navigate(1))
        self.side_organize.clicked.connect(lambda: self.navigate(2))
        for button in (self.side_home, self.side_library, self.side_organize):
            side.addWidget(button)
        side.addStretch()
        self.sidebar_zen = ZenCore(sidebar, compact=True)
        self.sidebar_zen.setFixedHeight(130)
        self.sidebar_zen.setVisible(False)
        side.addWidget(self.sidebar_zen)
        self.sidebar_activity = QLabel("Atividade em andamento")
        self.sidebar_activity.setVisible(False)
        side.addWidget(self.sidebar_activity)
        side.addWidget(QLabel("BETA  •  Seus arquivos permanecem seus."))
        root.addWidget(sidebar)
        main = QVBoxLayout()
        root.addLayout(main, 1)

        nav = QHBoxLayout()
        self.back_button = QPushButton("← Voltar")
        self.forward_button = QPushButton("Avançar →")
        self.home_button = QPushButton("⌂ Início")
        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.home_button.clicked.connect(lambda: self.navigate(0))
        for button in (self.back_button, self.forward_button, self.home_button):
            nav.addWidget(button)
        nav.addStretch()
        main.addLayout(nav)

        self.pages = QStackedWidget()
        start = QWidget()
        start_layout = QVBoxLayout(start)
        start_layout.setSpacing(14)
        title = QLabel("Encontre o que importa.")
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 31px; font-weight: 800; color: #e7f1fb;")
        start_layout.addWidget(title)
        start_layout.addWidget(QLabel("Explore seu acervo. Organize com prévia e preserve os originais."))
        center = QFrame()
        center.setObjectName("sidebar")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(22, 18, 22, 18)
        self.zen = ZenCore(center)
        center_layout.addWidget(self.zen, 1)
        self.zen_state = QLabel("SEU ACERVO EM FOCO")
        self.zen_state.setAlignment(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignCenter)
        self.zen_state.setStyleSheet("font-size: 15px; font-weight: 700; color: #b5dbe1;")
        center_layout.addWidget(self.zen_state)
        self.home_stats = QLabel("Sua Biblioteca espera a primeira leitura.")
        self.home_stats.setAlignment(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.home_stats)
        start_layout.addWidget(center, 1)
        actions = QGridLayout()
        self.action_grid = actions
        browse = QPushButton("Explorar Biblioteca  →")
        organize = QPushButton("Organizar com segurança  →")
        self.browse_button = browse
        self.organize_button = organize
        browse.clicked.connect(lambda: self.navigate(1))
        organize.clicked.connect(lambda: self.navigate(2))
        actions.addWidget(browse, 0, 0)
        actions.addWidget(organize, 0, 1)
        actions.setColumnStretch(0, 1)
        actions.setColumnStretch(1, 1)
        start_layout.addLayout(actions)
        self.reduce_motion = QCheckBox("Reduzir movimento")
        self.reduce_motion.toggled.connect(self.zen.set_reduced_motion)
        self.reduce_motion.toggled.connect(self.sidebar_zen.set_reduced_motion)
        start_layout.addWidget(self.reduce_motion)
        self.zen.setToolTip("Animação de atividade. Não representa porcentagem de progresso.")
        for_page = QScrollArea()
        for_page.setWidgetResizable(True)
        for_page.setWidget(start)
        self.pages.addWidget(for_page)
        self.library = Biblioteca()
        self.organizer = FluxorIntegrado()
        for widget in (self.library, self.organizer):
            page = QScrollArea()
            page.setWidgetResizable(True)
            page.setWidget(widget)
            self.pages.addWidget(page)
        main.addWidget(self.pages)
        self.refresh_zen()
        self.activity_poll = QTimer(self)
        self.activity_poll.setInterval(700)
        self.activity_poll.timeout.connect(self.poll_activity)
        self.activity_poll.start()
        self.was_active = False
        self.last_active_kind = None
        self.refresh_nav()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "action_grid"):
            return
        # On 13-inch screens and smaller windows, preserve complete button labels.
        compact = self.width() < 900
        self.sidebar.setFixedWidth(165 if compact else 205)
        self.side_organize.setText("◈   Organizar" if compact else "◈   Organização segura")
        self.action_grid.addWidget(self.browse_button, 0, 0)
        self.action_grid.addWidget(self.organize_button, 1 if compact else 0, 0 if compact else 1)

    def navigate(self, target):
        current = self.pages.currentIndex()
        if current == target:
            return
        if self.active_operation():
            QMessageBox.information(
                self, "Operação em andamento",
                "Espere a operação terminar antes de trocar de tela."
            )
            return
        self.history.append(current)
        self.future.clear()
        self.pages.setCurrentIndex(target)
        self.refresh_zen()
        self.refresh_nav()

    def poll_activity(self):
        active = self.active_operation()
        self.sidebar_zen.setVisible(active)
        self.sidebar_activity.setVisible(active)
        if active:
            kind = "library" if self.library.thread is not None else "organizer"
            self.last_active_kind = kind
            state = "scanning" if kind == "library" else "organizing"
            self.sidebar_zen.set_state(state)
            self.sidebar_activity.setText("Analisando..." if kind == "library" else "Organizando...")
        if active != self.was_active:
            self.was_active = active
            if not active:
                kind = self.last_active_kind
                outcome = self.library.last_outcome if kind == "library" else self.organizer.last_outcome
                if outcome == "success":
                    self.zen.set_state("complete")
                    self.zen_state.setText("OPERAÇÃO CONCLUÍDA")
                else:
                    self.zen.set_state("error")
                    self.zen_state.setText({
                        "cancelled": "OPERAÇÃO INTERROMPIDA",
                        "partial": "CONCLUÍDO COM AVISOS",
                        "error": "OPERAÇÃO COM ERRO",
                    }.get(outcome, "ESTADO NÃO CONFIRMADO"))
                QTimer.singleShot(2300, self.refresh_zen)
            else:
                self.refresh_zen()

    def refresh_zen(self):
        if self.library.thread is not None:
            self.zen.set_state("scanning")
            self.zen_state.setText("LENDO SEU ACERVO")
        elif self.organizer.thread is not None:
            self.zen.set_state("organizing")
            self.zen_state.setText("ORGANIZANDO COM CUIDADO")
        else:
            self.zen.set_state("idle")
            self.zen_state.setText("SEU ACERVO EM FOCO")
        if self.pages.currentIndex() != 0:
            return
        if self.library.db.exists():
            try:
                info = catalog_summary(self.library.db)
                self.home_stats.setText(f"{info['total']:,} arquivos catalogados  ·  {info['size'] / (1024**3):.2f} GB indexados")
            except Exception:
                self.home_stats.setText("Resumo da Biblioteca indisponível.")
        else:
            self.home_stats.setText("Escolha uma pasta na Biblioteca para começar.")

    def active_operation(self):
        return self.library.thread is not None or self.organizer.thread is not None

    def go_back(self):
        if not self.history or self.active_operation():
            return
        current = self.pages.currentIndex()
        target = self.history.pop()
        self.future.append(current)
        self.pages.setCurrentIndex(target)
        self.refresh_zen()
        self.refresh_nav()

    def go_forward(self):
        if not self.future or self.active_operation():
            return
        current = self.pages.currentIndex()
        target = self.future.pop()
        self.history.append(current)
        self.pages.setCurrentIndex(target)
        self.refresh_zen()
        self.refresh_nav()

    def refresh_nav(self):
        self.back_button.setEnabled(bool(self.history))
        self.forward_button.setEnabled(bool(self.future))
        self.home_button.setEnabled(self.pages.currentIndex() != 0)

    def closeEvent(self, event):
        if self.active_operation():
            QMessageBox.information(self, "Operação ativa", "Aguarde terminar antes de fechar.")
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Inicio()
    window.show()
    sys.exit(app.exec())
