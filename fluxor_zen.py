"""FLUXOR Signal Field — lightweight procedural activity visualization.

Four quiet data routes converge into a central marker. Activity states control
speed only; the animation never pretends to be task progress.
"""
import math
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


def phase_for_state(state):
    return {"idle": 0.22, "scanning": 0.85, "organizing": 1.15,
            "complete": 0.0, "error": 0.0}.get(state, 0.22)


def bezier(a, b, c, d, t):
    u = 1.0 - t
    return QPointF(
        u*u*u*a.x() + 3*u*u*t*b.x() + 3*u*t*t*c.x() + t*t*t*d.x(),
        u*u*u*a.y() + 3*u*u*t*b.y() + 3*u*t*t*c.y() + t*t*t*d.y(),
    )


class ZenCore(QWidget):
    """Subtle signal routes rendered with QPainter; at most 20 fps."""
    def __init__(self, parent=None, compact=False):
        super().__init__(parent)
        self.state = "idle"
        self.phase = 0.0
        self.reduced_motion = False
        self.compact = compact
        self.setMinimumSize(95, 95) if compact else self.setMinimumSize(180, 155)
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.advance)
        self.timer.start()

    def set_state(self, state):
        if state not in ("idle", "scanning", "organizing", "complete", "error"):
            raise ValueError("Unknown FLUXOR visual state")
        self.state = state
        # Lower idle repaint frequency on older MacBooks.
        self.timer.setInterval(100 if state == "idle" else 50)
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
        w, h = float(self.width()), float(self.height())
        painter.fillRect(self.rect(), QColor("#0c1525"))
        cx, cy = w * 0.5, h * 0.5
        rx, ry = w * 0.36, h * 0.31
        center = QPointF(cx, cy)
        accent = ["#31d4ee", "#a58aff", "#4eacff", "#54d7ca"]
        positions = [
            QPointF(cx-rx, cy-ry), QPointF(cx+rx, cy-ry),
            QPointF(cx-rx, cy+ry), QPointF(cx+rx, cy+ry),
        ]
        for i, start in enumerate(positions):
            bend = -1.0 if i % 2 == 0 else 1.0
            c1 = QPointF(start.x()+bend*rx*0.13, start.y()+(-ry*.15 if i < 2 else ry*.15))
            c2 = QPointF(cx-bend*rx*.45, cy)
            curve = QPainterPath(start)
            curve.cubicTo(c1, c2, center)
            line = QColor(accent[i])
            line.setAlpha(85)
            painter.setPen(QPen(line, 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(curve)

            # Sparse geometric endpoints: deliberate, not decorative fake metrics.
            size = max(5.0, min(11.0, min(w, h) * 0.027))
            painter.setPen(QPen(QColor(accent[i]), 1.4))
            painter.setBrush(QColor("#15243c"))
            painter.drawRoundedRect(QRectF(start.x()-size, start.y()-size,
                                           size*2, size*2), 3.0, 3.0)

            if self.state not in ("complete", "error"):
                t = (self.phase / 360.0 + i * .23) % 1.0
                if self.reduced_motion:
                    t = .35 + i*.06
                point = bezier(start, c1, c2, center, t)
                glow = QColor(accent[i])
                glow.setAlpha(38)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(glow)
                painter.drawEllipse(QRectF(point.x()-7, point.y()-7, 14, 14))
                painter.setBrush(QColor(accent[i]))
                painter.drawEllipse(QRectF(point.x()-2.2, point.y()-2.2, 4.4, 4.4))

        # Central diamond: files converge without implying transfer or completion.
        center_color = QColor("#ec9f80") if self.state == "error" else QColor("#53d9f5")
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(45)
        side = max(27.0, min(52.0, min(w, h)*0.17))
        painter.setBrush(QColor("#10253d"))
        painter.setPen(QPen(center_color, 2.2))
        painter.drawRoundedRect(QRectF(-side/2, -side/2, side, side), 6, 6)
        painter.setBrush(QColor("#172d48"))
        painter.drawRoundedRect(QRectF(-side*.28, -side*.28, side*.56, side*.56), 4, 4)
        painter.restore()

        if not self.compact:
            painter.setPen(QPen(QColor(59, 105, 148, 50), 1.0))
            margin = min(w, h)*.07
            painter.drawLine(QPointF(margin, margin), QPointF(margin+22, margin))
            painter.drawLine(QPointF(w-margin-22, h-margin), QPointF(w-margin, h-margin))
        painter.end()
