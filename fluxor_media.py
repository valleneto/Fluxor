"""On-demand image/video preview panel. No persistent thumbnail cache."""
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, QProcess
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget
)
from fluxor_core.media_policy import preview_allowed, media_kind, cloud_risk


class MediaPreview(QWidget):
    """Only the selected file is decoded; motion player is loaded on first click."""
    def __init__(self, parent=None):
        super().__init__(parent)
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

        layout = QVBoxLayout(self)
        self.heading = QLabel("Prévia visual")
        layout.addWidget(self.heading)
        self.stack = QStackedWidget()
        self.picture = QLabel("Selecione uma imagem ou vídeo.")
        self.picture.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.picture.setMinimumHeight(150)
        self.picture.setMaximumHeight(245)
        self.picture.setStyleSheet("background: palette(base); border-radius: 8px;")
        self.stack.addWidget(self.picture)
        layout.addWidget(self.stack)
        controls = QHBoxLayout()
        self.still_button = QPushButton("Mostrar quadro")
        self.motion_button = QPushButton("▶ Trecho de 4 s (sem som)")
        self.stop_button = QPushButton("Parar")
        self.still_button.clicked.connect(self.show_still)
        self.motion_button.clicked.connect(self.play_motion)
        self.stop_button.clicked.connect(self.stop_motion)
        for button in (self.still_button, self.motion_button, self.stop_button):
            controls.addWidget(button)
        layout.addLayout(controls)
        self.note = QLabel("A prévia só é carregada quando você solicitar.")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.update_controls()

    def select_file(self, path):
        self.stop_motion()
        self.cancel_thumbnail()
        self.generation += 1
        self.selected = str(path) if path else None
        self.picture.clear()
        self.picture.setText("Selecione Mostrar quadro para carregar a prévia.")
        self.stack.setCurrentWidget(self.picture)
        self.note.setText("Nada é decodificado automaticamente.")
        self.update_controls()

    def update_controls(self):
        kind = media_kind(self.selected) if self.selected else "other"
        self.still_button.setEnabled(kind in ("image", "video"))
        self.motion_button.setEnabled(kind == "video")
        self.stop_button.setEnabled(self.player is not None)
        if self.selected and cloud_risk(self.selected):
            self.still_button.setEnabled(False)
            self.motion_button.setEnabled(False)
            self.note.setText("Arquivo possivelmente em nuvem: prévia automática bloqueada.")

    def show_still(self):
        if not self.selected or not preview_allowed(self.selected):
            self.note.setText("Prévia indisponível ou arquivo não local. Abra no aplicativo padrão.")
            return
        self.stop_motion()
        path = Path(self.selected)
        self.picture.setText("Não foi possível gerar um quadro. Use o aplicativo padrão.")
        self.stack.setCurrentWidget(self.picture)
        if media_kind(path) == "image":
            pixmap = QPixmap(str(path))
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
            self.note.setText("Quadro indisponível. Abra o vídeo pelo aplicativo padrão.")
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
            self.output.setMuted(True)
            self.player.setAudioOutput(self.output)
            self.video_surface = QVideoWidget(self)
            self.stack.addWidget(self.video_surface)
            self.player.setVideoOutput(self.video_surface)
            self.player.errorOccurred.connect(self.player_error)
        self.timer.stop()
        self.player.stop()
        self.stack.setCurrentWidget(self.video_surface)
        self.player.setSource(QUrl.fromLocalFile(self.selected))
        self.player.play()
        self.timer.start(4000)
        self.note.setText("Trecho silencioso em reprodução. Parada automática em 4 segundos.")
        self.update_controls()

    def player_error(self, *args):
        self.stop_motion()
        self.note.setText("Codec não suportado no player. Use Mostrar quadro ou duplo clique.")

    def stop_motion(self):
        self.timer.stop()
        if self.player is not None:
            self.player.stop()
            self.player.setSource(QUrl())
        self.stack.setCurrentWidget(self.picture)
        self.update_controls()

    def closeEvent(self, event):
        self.stop_motion()
        self.cancel_thumbnail()
        super().closeEvent(event)
