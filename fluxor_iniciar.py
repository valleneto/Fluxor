"""Fluxor Control — single-window navigation with preserved page state."""
import sys
from pathlib import Path
from PySide6.QtCore import QTimer

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QMessageBox, QFrame, QCheckBox,
)
from fluxor_biblioteca import Biblioteca, human_size
from fluxor_app_integrado import FluxorIntegrado
from fluxor_zen import ZenCore
from fluxor_mural import FluxorMural
from fluxor_brand import FluxorWordmark, fluxor_app_icon
from fluxor_design import STYLESHEET
from fluxor_core.library import catalog_summary


class Inicio(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FLUXOR — Seu fluxo. Seu controle.")
        self.setWindowIcon(fluxor_app_icon())
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            self.resize(
                min(1100, max(640, available.width() - 48)),
                min(700, max(480, available.height() - 64)),
            )
        else:
            self.resize(1000, 650)
        self.setStyleSheet(STYLESHEET)
        self.history = []
        self.future = []
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(16)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        self.sidebar = sidebar
        sidebar.setFixedWidth(192)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(12, 18, 12, 14)
        side.setSpacing(9)
        self.wordmark = FluxorWordmark(sidebar)
        side.addWidget(self.wordmark)
        strap = QLabel("ORDEM. CONTROLE. FLUXO.")
        strap.setObjectName("sidebarCaption")
        strap.setWordWrap(True)
        side.addWidget(strap)
        side.addSpacing(20)
        self.side_home = QPushButton("01   /   INÍCIO")
        self.side_library = QPushButton("02   /   BIBLIOTECA")
        self.side_organize = QPushButton("03   /   ORGANIZAR")
        for nav_button in (self.side_home, self.side_library, self.side_organize):
            nav_button.setObjectName("navButton")
            nav_button.setCheckable(True)
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
        trust = QLabel("ARQUIVOS PRESERVADOS\nSem exclusão automática.")
        trust.setObjectName("sidebarCaption")
        trust.setWordWrap(True)
        side.addWidget(trust)
        root.addWidget(sidebar)
        main = QVBoxLayout()
        root.addLayout(main, 1)

        nav = QHBoxLayout()
        self.back_button = QPushButton("← Voltar")
        self.forward_button = QPushButton("Avançar →")
        self.home_button = QPushButton("Início")
        for nav_control in (self.back_button, self.forward_button, self.home_button):
            nav_control.setObjectName("quietAction")
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
        start_layout.setContentsMargins(16, 12, 16, 12)
        start_layout.setSpacing(12)
        eyebrow = QLabel("SEU ACERVO  /  VISÃO GERAL")
        eyebrow.setObjectName("sectionEyebrow")
        start_layout.addWidget(eyebrow)
        title = QLabel("Organização em movimento.")
        title.setObjectName("heroTitle")
        title.setWordWrap(True)
        start_layout.addWidget(title)
        tagline = QLabel("Explore seu acervo. Revise antes de organizar. Preserve cada original.")
        tagline.setObjectName("muted")
        tagline.setWordWrap(True)
        start_layout.addWidget(tagline)
        center = QFrame()
        center.setObjectName("heroPanel")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(22, 16, 22, 16)
        center_layout.setSpacing(4)
        self.zen = FluxorMural(center)
        center_layout.addWidget(self.zen, 1)
        self.zen_state = QLabel("AMBIENTE PRONTO")
        self.zen_state.setAlignment(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignCenter)
        self.zen_state.setObjectName("eyebrow")
        center_layout.addWidget(self.zen_state)
        self.home_stats = QLabel("Escolha uma pasta na Biblioteca para começar.")
        self.home_stats.setAlignment(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignCenter)
        self.home_stats.setObjectName("muted")
        self.home_stats.setWordWrap(True)
        center_layout.addWidget(self.home_stats)
        start_layout.addWidget(center, 1)
        actions = QHBoxLayout()
        browse = QPushButton("Abrir Biblioteca  →")
        browse.setObjectName("primaryAction")
        organize = QPushButton("Organizar arquivos")
        browse.clicked.connect(lambda: self.navigate(1))
        organize.clicked.connect(lambda: self.navigate(2))
        actions.addWidget(browse)
        actions.addWidget(organize)
        actions.addStretch()
        start_layout.addLayout(actions)
        self.reduce_motion = QCheckBox("Pausar animação")
        self.reduce_motion.setToolTip("Desativa a animação sem impedir o funcionamento do aplicativo")
        self.reduce_motion.toggled.connect(self.zen.set_reduced_motion)
        self.reduce_motion.toggled.connect(self.sidebar_zen.set_reduced_motion)
        start_layout.addWidget(self.reduce_motion)
        self.pages.addWidget(start)
        self.library = Biblioteca()
        self.organizer = FluxorIntegrado()
        self.pages.addWidget(self.library)
        self.pages.addWidget(self.organizer)
        main.addWidget(self.pages)
        self.refresh_zen()
        self.activity_poll = QTimer(self)
        self.activity_poll.setInterval(700)
        self.activity_poll.timeout.connect(self.poll_activity)
        self.activity_poll.start()
        self.was_active = False
        self.last_active_kind = None
        self.refresh_nav()

    def navigate(self, target):
        current = self.pages.currentIndex()
        if current == target:
            # Checkable buttons toggle on click; synchronize even on same page.
            self.refresh_nav()
            return
        if self.active_operation():
            QMessageBox.information(
                self, "Operação em andamento",
                "Espere a operação terminar antes de trocar de tela."
            )
            self.refresh_nav()
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
            self.zen_state.setText("AMBIENTE PRONTO")
        if self.pages.currentIndex() != 0:
            return
        if self.library.db.exists():
            try:
                info = catalog_summary(self.library.db)
                count = info["total"]
                filename_text = "arquivo catalogado" if count == 1 else "arquivos catalogados"
                self.home_stats.setText(
                    f"{count:,} {filename_text}  ·  {human_size(info['size'])} no índice"
                )
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
        for idx, button in enumerate((self.side_home, self.side_library, self.side_organize)):
            button.setChecked(self.pages.currentIndex() == idx)

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
