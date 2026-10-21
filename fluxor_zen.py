"""Fluxor Zen Core — lightweight QPainter animation, no media/assets or external libraries."""
import math
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


def phase_for_state(state):
    return {"idle": 0.22, "scanning": 0.85, "organizing": 1.15, "complete": 0.0}.get(state, 0.22)


class ZenCore(QWidget):
    """Calm procedural sand-like rings; repaint at most 20 fps while visible."""
    def __init__(self, parent=None, compact=False):
        super().__init__(parent)
        self.state = "idle"
        self.phase = 0.0
        self.reduced_motion = False
        self.setMinimumSize(100, 100) if compact else self.setMinimumSize(260, 240)
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.advance)
        self.timer.start()

    def set_state(self, state):
        if state not in ("idle", "scanning", "organizing", "complete"):
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
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        outer = max(30.0, min(w * 0.43, h * 0.44))
        p.fillRect(self.rect(), QColor("#121f2c"))
        # Static rake lines: deliberately low visual contrast and no per-pixel effects.
        for i in range(8):
            radius = outer * (0.28 + i * 0.085)
            a = 30 + int(22 * (1 - i / 9))
            p.setPen(QPen(QColor(115, 181, 190, a), 1.25))
            p.drawEllipse(QRectF(cx-radius, cy-radius, 2*radius, 2*radius))
        p.setPen(QPen(QColor("#4f8790"), 1.5))
        p.drawEllipse(QRectF(cx-outer*.17, cy-outer*.17, outer*.34, outer*.34))
        # Slow traveling trace, representing work without claiming measurable progress.
        angle = math.radians(self.phase - 90)
        radius = outer * .72
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#90dce1"))
        p.drawEllipse(QRectF(x-3.5, y-3.5, 7, 7))
        p.end()
