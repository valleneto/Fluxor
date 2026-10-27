"""On-demand image/video preview panel. No persistent thumbnail cache."""
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, QProcess, Signal
from PySide6.QtGui import QPixmap, QImageReader
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QFileDialog
)
from fluxor_core.media_policy import preview_allowed, media_kind, cloud_risk


class MediaPreview(QWidget):
    """Only selected local files are previewed; no persistent thumbnails."""
    close_requested = Signal()

    def __init__(self, parent=None, embedded=False):
        super().__init__(parent)
        self.embedded = embedded
        self.selected = None
        self.player = None
        self.output = None
        self.video_surface = None
        self.generation = 0
        self.thumbnail_process = None
        self.thumbnail_folder = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.stop_motion)
        self.start_timeout = QTimer(self)
        self.start_timeout.setSingleShot(True)
        self.start_timeout.timeout.connect(self.motion_start_failed)

        layout = QVBoxLayout(self)
        self.setObjectName("mediaPanel")
        self.setAcceptDrops(True)
        self.heading = QLabel("INSPECTOR · Arquivo selecionado")
        self.heading.setObjectName("eyebrow")
        header = QHBoxLayout()
        header.addWidget(self.heading)
        header.addStretch()
        self.close_button = QPushButton("Fechar ×")
        self.close_button.setToolTip("Fechar Inspector e voltar à lista completa")
        self.close_button.clicked.connect(self.close_requested.emit)
        self.close_button.setVisible(embedded)
        header.addWidget(self.close_button)
        layout.addLayout(header)
        self.stack = QStackedWidget()
        self.picture = QLabel("Selecione uma imagem ou vídeo.")
        self.picture.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.picture.setMinimumHeight(150)
        self.picture.setMaximumHeight(245)
        self.picture.setStyleSheet("background: #101827; color: #9cabc1; border-radius: 14px; padding: 16px;")
        self.stack.addWidget(self.picture)
        layout.addWidget(self.stack)
        controls = QHBoxLayout()
        self.pick_button = QPushButton("Escolher arquivo…")
        self.pick_button.clicked.connect(self.pick_file)
        self.still_button = QPushButton("Mostrar quadro")
        self.motion_button = QPushButton("▶ Prévia · 4 s")
        self.stop_button = QPushButton("Parar")
        self.still_button.clicked.connect(self.show_still)
        self.motion_button.clicked.connect(self.play_motion)
        self.stop_button.clicked.connect(self.stop_motion)
        for button in (self.still_button, self.motion_button, self.stop_button):
            controls.addWidget(button)
        layout.addLayout(controls)
        layout.addWidget(self.pick_button)
        self.pick_button.setVisible(not embedded)
        self.note = QLabel("Selecione um arquivo na Biblioteca.")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.metadata = QLabel("Nenhum arquivo selecionado.")
        self.metadata.setWordWrap(True)
        self.metadata.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.metadata.setStyleSheet("color: #b5ccdc; font-size: 12px; padding-top: 4px;")
        layout.addWidget(self.metadata)
        self.update_controls()

    def reset_selection(self):
        """Release all previews and return to an unselected Inspector state."""
        self.stop_motion()
        self.cancel_thumbnail()
        self.generation += 1
        self.selected = None
        self.picture.clear()
        self.picture.setText("Selecione um arquivo na Biblioteca.")
        self.metadata.setText("Nenhum arquivo selecionado.")
        self.note.setText("A lista ocupa toda a área até uma seleção.")
        self.stack.setCurrentWidget(self.picture)
        self.update_controls()

    def pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Escolher mídia local", str(Path.home()),
            "Mídia (*.mp4 *.mov *.m4v *.mkv *.avi *.webm *.jpg *.jpeg *.png *.webp *.heic);;Todos os arquivos (*)"
        )
        if path:
            self.select_file(path)
            self.show_still()

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if len(urls) == 1 and urls[0].isLocalFile() and media_kind(urls[0].toLocalFile()) != "other":
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if len(urls) == 1 and urls[0].isLocalFile():
            self.select_file(urls[0].toLocalFile())
            self.show_still()
            event.acceptProposedAction()
        else:
            event.ignore()

    def set_metadata(self, values):
        """Display catalog metadata without opening or decoding the file."""
        if not values:
            self.metadata.setText("Nenhum arquivo selecionado.")
            return
        name, category, project, size, modified, path = values
        self.metadata.setText(
            f"{name}\n{category} · {project} · {size}\n"
            f"Modificado em {modified}\n{path}"
        )

    def select_file(self, path):
        self.stop_motion()
        self.cancel_thumbnail()
        self.generation += 1
        self.selected = str(path) if path else None
        self.metadata.setText(self.selected if self.selected else "Nenhum arquivo selecionado.")
        self.picture.clear()
        kind = media_kind(self.selected) if self.selected else "other"
        self.picture.setText("Prévia sob demanda" if kind in ("image", "video", "document") else "Informações do arquivo")
        self.stack.setCurrentWidget(self.picture)
        self.note.setText("Arquivo selecionado: " + Path(self.selected).name if self.selected else "Selecione ou arraste uma imagem/vídeo.")
        self.update_controls()
        if self.selected and kind in ("image", "document") and preview_allowed(self.selected):
            if kind == "image" or sys.platform == "darwin":
                QTimer.singleShot(0, self.show_still)
        elif self.selected and kind == "other":
            self.note.setText("Metadados disponíveis. Abra o arquivo no aplicativo padrão com duplo clique.")

    def update_controls(self):
        kind = media_kind(self.selected) if self.selected else "other"
        self.still_button.setVisible(kind in ("image", "video", "document"))
        self.still_button.setText("Atualizar prévia" if kind in ("image", "document") else "Mostrar quadro")
        self.still_button.setEnabled(kind in ("image", "video") or (kind == "document" and sys.platform == "darwin"))
        self.motion_button.setVisible(kind == "video")
        self.motion_button.setEnabled(kind == "video")
        self.stop_button.setVisible(kind == "video")
        self.stop_button.setEnabled(self.player is not None and (self.timer.isActive() or self.start_timeout.isActive()))
        if self.selected and cloud_risk(self.selected):
            self.still_button.setEnabled(False)
            self.motion_button.setEnabled(False)
            self.note.setText("Possível arquivo em nuvem: prévia bloqueada para evitar downloads.")

    def show_still(self):
        if not self.selected or not preview_allowed(self.selected):
            self.note.setText("Prévia indisponível ou arquivo não local. Abra no aplicativo padrão.")
            return
        self.stop_motion()
        path = Path(self.selected)
        self.picture.setText("Não foi possível gerar um quadro. Use o aplicativo padrão.")
        self.stack.setCurrentWidget(self.picture)
        if media_kind(path) == "image":
            reader = QImageReader(str(path))
            reader.setAutoTransform(True)
            dimensions = reader.size()
            if dimensions.isValid():
                if dimensions.width() * dimensions.height() > 100_000_000:
                    self.note.setText("Imagem grande demais para uma prévia segura; use Quick Look.")
                    return
                if max(dimensions.width(), dimensions.height()) > 1024:
                    reader.setScaledSize(dimensions.scaled(1024, 1024, Qt.AspectRatioMode.KeepAspectRatio))
            pixmap = QPixmap.fromImage(reader.read())
        elif sys.platform == "darwin":
            self.cancel_thumbnail()
            self.thumbnail_folder = tempfile.TemporaryDirectory(prefix="fluxor-preview-")
            process = QProcess(self)
            self.thumbnail_process = process
            token = self.generation
            process.finished.connect(lambda code, status: self.thumbnail_ready(process, token, code))
            process.start("qlmanage", ["-t", "-s", "480", "-o", self.thumbnail_folder.name, str(path)])
            QTimer.singleShot(12000, lambda: self.thumbnail_timeout(process))
            self.note.setText("Gerando quadro sem bloquear a navegação...")
            return
        else:
            pixmap = QPixmap()
        if pixmap.isNull():
            self.note.setText("Formato sem quadro disponível no sistema. Use duplo clique para abrir.")
            return
        self.picture.setPixmap(pixmap.scaled(480, 245, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.note.setText("Quadro local carregado sob demanda; nenhum cache persistente.")
 
    def cancel_thumbnail(self):
        if self.thumbnail_process is not None:
            try:
                if self.thumbnail_process.state() != QProcess.ProcessState.NotRunning:
                    self.thumbnail_process.kill()
                    self.thumbnail_process.waitForFinished(100)
            except RuntimeError:
                pass
            self.thumbnail_process.deleteLater()
            self.thumbnail_process = None
        if self.thumbnail_folder is not None:
            self.thumbnail_folder.cleanup()
            self.thumbnail_folder = None

    def thumbnail_timeout(self, process):
        if process is self.thumbnail_process and process.state() != QProcess.ProcessState.NotRunning:
            process.kill()
            self.note.setText("Tempo limite para gerar o quadro. Use duplo clique.")

    def thumbnail_ready(self, process, token, code):
        if process is not self.thumbnail_process or token != self.generation:
            return
        images = list(Path(self.thumbnail_folder.name).glob("*.png")) if self.thumbnail_folder else []
        pixmap = QPixmap(str(images[0])) if code == 0 and images else QPixmap()
        if pixmap.isNull():
            self.note.setText("Prévia indisponível. Abra no aplicativo padrão com duplo clique.")
        else:
            self.picture.setPixmap(pixmap.scaled(480, 245, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.note.setText("Quadro gerado sob demanda; cache temporário removido.")
        self.cancel_thumbnail()

    def play_motion(self):
        if not self.selected or media_kind(self.selected) != "video" or not preview_allowed(self.selected):
            self.note.setText("Trecho indisponível para este arquivo.")
            return
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
            from PySide6.QtMultimediaWidgets import QVideoWidget
        except ImportError:
            self.note.setText("Módulo de vídeo indisponível. Use Mostrar quadro ou duplo clique.")
            return
        if self.player is None:
            self.player = QMediaPlayer(self)
            self.output = QAudioOutput(self)
            self.output.setVolume(0.5)
            self.player.setAudioOutput(self.output)
            self.video_surface = QVideoWidget(self)
            self.stack.addWidget(self.video_surface)
            self.player.setVideoOutput(self.video_surface)
            self.player.errorOccurred.connect(self.player_error)
            self.player.positionChanged.connect(self.on_position)
        self.timer.stop()
        self.start_timeout.stop()
        self.player.stop()
        self.stack.setCurrentWidget(self.video_surface)
        self.player.setSource(QUrl.fromLocalFile(self.selected))
        self.player.play()
        self.start_timeout.start(15000)
        self.note.setText("Preparando o vídeo... A contagem começa quando ele iniciar.")
        self.update_controls()

    def on_position(self, position):
        if position > 0 and self.start_timeout.isActive():
            self.start_timeout.stop()
            self.timer.start(4000)
            self.note.setText("Reproduzindo trecho de 4 segundos dentro do Fluxor.")
            self.update_controls()

    def motion_start_failed(self):
        self.stop_motion()
        self.note.setText("Não foi possível iniciar o vídeo em 15 segundos. Use o Quick Look.")

    def player_error(self, *args):
        self.stop_motion()
        self.note.setText("Codec não suportado no player. Use Mostrar quadro ou duplo clique.")

    def stop_motion(self):
        self.timer.stop()
        self.start_timeout.stop()
        if self.player is not None:
            self.player.stop()
            self.player.setSource(QUrl())
        self.stack.setCurrentWidget(self.picture)
        self.update_controls()

    def closeEvent(self, event):
        self.stop_motion()
        self.cancel_thumbnail()
        super().closeEvent(event)
