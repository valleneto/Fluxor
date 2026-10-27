"""FLUXOR Zen Core — original low-cost, procedural, responsive motion.

The generative field communicates activity, never a fake progress percentage.
No photography, video, 3D, particles, online assets or heavy libraries.
"""
import math

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


def phase_for_state(state):
    """Degrees advanced per 50ms, kept low for calm interface motion."""
    return {"idle": 0.18, "scanning": 0.72, "organizing": 0.95,
            "complete": 0.0, "error": 0.0}.get(state, 0.18)


class ZenCore(QWidget):
    """Sparse, animated flow contours in a circular field. At most 20 FPS."""
    def __init__(self, parent=None, compact=False):
        super().__init__(parent)
        self.state = "idle"
        self.phase = 0.0
        self.reduced_motion = False
        self.compact = compact
        self.setMinimumSize(100, 100) if compact else self.setMinimumSize(240, 180)
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.advance)
        self.timer.start()

    def set_state(self, state):
        if state not in ("idle", "scanning", "organizing", "complete", "error"):
            raise ValueError("Unknown Zen Core state")
        self.state = state
        self.update()

    def set_reduced_motion(self, enabled):
        self.reduced_motion = bool(enabled)
        if self.reduced_motion:
            self.timer.stop()
        elif self.isVisible():
            self.timer.start()
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.reduced_motion:
            self.timer.start()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def advance(self):
        if self.isVisible() and not self.reduced_motion:
            self.phase = (self.phase + phase_for_state(self.state)) % 360.0
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        cx, cy = width * 0.5, height * 0.5
        size = max(26.0, min(width * 0.41, height * 0.42))
        painter.fillRect(self.rect(), QColor("#131e2a"))
        phase = math.radians(self.phase)
        active = self.state in ("scanning", "organizing")
        frozen = self.state in ("complete", "error")
        color = QColor("#dfb38f") if self.state == "error" else QColor("#a9dfe6")
        # Breathing contours: 5 simple closed vector curves, no particle effects.
        for band in range(5):
            radius = size * (0.25 + 0.13 * band)
            wave = size * 0.018 * (1 + int(active))
            path = QPainterPath()
            segments = 72 if not self.compact else 40
            for point in range(segments + 1):
                angle = (2.0 * math.pi * point) / segments
                ripple = wave * math.sin(angle * 3.0 + phase * 1.2 + band * 0.64)
                drift = size * 0.013 * math.cos(angle * 2 - phase + band * 0.5)
                rr = radius + ripple + drift
                px = cx + math.cos(angle) * rr
                py = cy + math.sin(angle) * rr * 0.83
                if point == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)
            alpha = int(52 + band * 20)
            painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), alpha),
                                1.1 if self.compact else 1.45))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        # One orbit accent: signal of activity, deliberately not progress.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        orbit_angle = phase - math.pi / 2
        orbit_radius = size * 0.77
        dot = 2.3 if self.compact else 3.0
        painter.setOpacity(0.6 if frozen else 0.88)
        painter.drawEllipse(QRectF(
            cx + math.cos(orbit_angle) * orbit_radius - dot,
            cy + math.sin(orbit_angle) * orbit_radius * 0.83 - dot,
            2 * dot, 2 * dot
        ))
        painter.end()
