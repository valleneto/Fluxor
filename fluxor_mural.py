"""FLUXOR Sand Flow — procedural Japanese-garden screen animation.

Lines are progressively raked across the canvas, first row to last, changing
direction on each row. After the last row a new muted silver/gold pass gently
redraws the previous patterns. No photographs, giant logo, bloom or fake data.
"""
import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QBrush, QLinearGradient, QPainter, QPainterPath, QPen

from fluxor_zen import ZenCore


class FluxorMural(ZenCore):
    """A restrained sand-rake screensaver, compatible with ZenCore controls."""

    ROWS = 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self.phase = 1.25  # Visible grooves on the first frame, not an empty canvas.
        self.setMinimumSize(235, 175)
        self.timer.setInterval(50)  # 20 FPS at most.

    def advance(self):
        if self.reduced_motion or not self.isVisible():
            return
        if self.state in ("complete", "error"):
            return
        rate = 0.012 if self.state == "idle" else 0.019
        self.phase += rate
        # Keep floating point bounded; each pass has 7 rows.
        if self.phase >= self.ROWS * 6:
            self.phase -= self.ROWS * 4
        self.update()

    @staticmethod
    def _color(passage):
        """Alternating natural-garden tones: silver mineral and brushed sand gold."""
        return QColor("#d4d0c6") if passage % 2 == 0 else QColor("#bda57d")

    @staticmethod
    def _line_path(w, y, h, lane, passage, row):
        """Only straight segments with controlled bends; never concentric rings."""
        offset = (lane - 2.5) * max(3.1, h * .092)
        y += offset
        drift = h * (.12 if (row + passage) % 2 == 0 else -.115)
        shift = (passage % 3 - 1) * h * .10
        p = QPainterPath(QPointF(-6, y))
        p.lineTo(w * .17, y)
        p.lineTo(w * .245, y + drift)
        p.lineTo(w * .38, y + drift)
        p.lineTo(w * .47, y - drift * .42 + shift)
        p.lineTo(w * .71, y - drift * .42 + shift)
        p.lineTo(w * .79, y + drift * .20)
        p.lineTo(w + 6, y + drift * .20)
        return p

    @classmethod
    def _draw_grooves(cls, painter, w, center_y, row_h, passage, row):
        color = cls._color(passage)
        # Sand incision: dark shadow below, slender pearly/mineral ridge above.
        for lane in range(6):
            curve = cls._line_path(w, center_y, row_h, lane, passage, row)
            painter.setPen(QPen(QColor(8, 9, 11, 180), 3.2,
                                Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap,
                                Qt.PenJoinStyle.MiterJoin))
            painter.drawPath(curve)
            painter.save()
            painter.translate(0, -1.25)
            painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 205),
                                1.35, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin))
            painter.drawPath(curve)
            painter.restore()

        # Sparse direction motif carved in the same material as the lines.
        if row % 3 == 1:
            x = w * (.80 if (row + passage) % 2 == 0 else .20)
            arrow = 1 if (row + passage) % 2 == 0 else -1
            y = center_y - row_h * .34
            size = min(11, row_h * .20)
            painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 115),
                                1.5, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin))
            painter.drawLine(QPointF(x - arrow * size, y - size * .60), QPointF(x, y))
            painter.drawLine(QPointF(x - arrow * size, y + size * .60), QPointF(x, y))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = float(self.width()), float(self.height())
        if w <= 2 or h <= 2:
            painter.end()
            return

        sand = QLinearGradient(0, 0, w, h)
        sand.setColorAt(0, QColor("#141517"))
        sand.setColorAt(.55, QColor("#1d1b19"))
        sand.setColorAt(1, QColor("#0f1114"))
        painter.fillRect(self.rect(), QBrush(sand))

        # Deterministic, quiet sand grain; not high-cost noise or bright particles.
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(250):
            x = ((i * 97 + 31) % 991) / 991.0 * w
            y = ((i * 191 + 73) % 983) / 983.0 * h
            c = QColor(178, 166, 146, 15 if i % 3 else 26)
            painter.setBrush(c)
            d = .40 + (i % 3) * .27
            painter.drawEllipse(QRectF(x, y, d, d))

        rows = self.ROWS
        pad = max(12.0, min(h * .055, 25.0))
        row_height = (h - pad * 2) / rows
        passage = int(self.phase // rows)
        active_row = int(self.phase % rows)
        fraction = self.phase - int(self.phase)

        for row in range(rows):
            top = pad + row * row_height
            middle = top + row_height * .50
            rectangle = QRectF(0, top, w, row_height)
            painter.save()
            painter.setClipRect(rectangle)
            # Rows yet to be redrawn keep the marks from the preceding pass.
            if passage > 0:
                self._draw_grooves(painter, w, middle, row_height, passage - 1, row)

            if row < active_row or (row == active_row and fraction > 0):
                completed = row < active_row
                sweep = 1.0 if completed else fraction
                ltr = (row + passage) % 2 == 0
                active_box = QRectF(0 if ltr else w * (1-sweep),
                                    top, w * sweep, row_height)
                painter.save()
                painter.setClipRect(active_box, Qt.ClipOperation.IntersectClip)
                # The new rake pass replaces the previous traces in its wake.
                if passage > 0:
                    painter.fillRect(active_box, QColor("#1b1a18"))
                self._draw_grooves(painter, w, middle, row_height, passage, row)
                painter.restore()

                if not completed:
                    # Six slim tooth marks follow the leading edge; no literal 3D rake.
                    edge = w * sweep if ltr else w * (1 - sweep)
                    tone = self._color(passage)
                    painter.setPen(QPen(QColor(tone.red(), tone.green(), tone.blue(), 150),
                                        1.2, Qt.PenStyle.SolidLine,
                                        Qt.PenCapStyle.RoundCap))
                    for tooth in range(6):
                        ty = middle + (tooth - 2.5) * max(3.1, row_height * .092)
                        painter.drawLine(QPointF(edge, ty - 3.5), QPointF(edge, ty + 3.5))
            painter.restore()

        # A faint horizon line, for depth without photorealistic sand or stones.
        painter.setPen(QPen(QColor(171, 154, 127, 32), 1))
        painter.drawLine(QPointF(0, h - pad * .55), QPointF(w, h - pad * .55))
        painter.end()
