"""FLUXOR identity — compact non-square two-ink throw-up wordmark.

Brushed silver and muted gold, entirely vector drawn. No stock fonts bundled,
external image, square badge, crown, fluorescent colors or third-party assets.
"""
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class FluxorWordmark(QWidget):
    """Horizontal graffiti-influenced wordmark for the left sidebar only."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("fluxorWordmark")
        self.setMinimumSize(135, 52)
        self.setMaximumHeight(80)
        self.setToolTip("FLUXOR")
        font = QFont("Arial Black")
        font.setPixelSize(120)
        font.setBold(True)
        font.setItalic(True)
        self._letters = QPainterPath()
        self._letters.addText(QPointF(0, 0), font, "FLUXOR")
        self._bounds = self._letters.boundingRect()

    @staticmethod
    def _arrow(painter, start, tip, color, width=2.7):
        """A directional arrow, part of the tag, not a separate badge."""
        import math
        painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin))
        painter.drawLine(start, tip)
        angle = math.atan2(tip.y() - start.y(), tip.x() - start.x())
        length = max(5.0, width * 3.0)
        spread = .58
        for delta in (spread, -spread):
            dx = length * math.cos(angle + math.pi + delta)
            dy = length * math.sin(angle + math.pi + delta)
            painter.drawLine(tip, QPointF(tip.x() + dx, tip.y() + dy))

    def paintEvent(self, event):
        """Two-color hand-composed tag with interwoven arrows through the glyphs."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        b = self._bounds
        if b.width() <= 0 or b.height() <= 0:
            painter.end()
            return
        scale = min((w - 17) / (b.width() + 42),
                    (h - 19) / (b.height() + 30))
        painter.save()
        painter.translate(w * .51, h * .51)
        painter.shear(-.12, 0.0)
        painter.scale(scale, scale)
        painter.translate(-b.center().x(), -b.center().y())

        gold = QColor("#ad9162")
        silver = QColor("#d6d8d7")
        shadow = QColor("#0f1114")
        left, top, bw, bh = b.left(), b.top(), b.width(), b.height()

        # Angular tracks behind the main tag, stretching past the first/last glyph.
        tracks = [
            [( -.09, .64), (.13, .28), (.24, .48), (.39, .13), (.51, .45), (.73, .20), (1.08, .12)],
            [( -.07, .87), (.18, .55), (.35, .81), (.52, .40), (.68, .71), (.89, .39), (1.08, .53)],
        ]
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for n, points in enumerate(tracks):
            route = QPainterPath()
            for j, (ux, uy) in enumerate(points):
                point = QPointF(left + bw * ux, top + bh * uy)
                if not j:
                    route.moveTo(point)
                else:
                    route.lineTo(point)
            painter.setPen(QPen(shadow, 20, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin))
            painter.drawPath(route)
            painter.setPen(QPen(gold if n == 0 else silver, 10,
                                Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                Qt.PenJoinStyle.MiterJoin))
            painter.drawPath(route)

        # Offset throw-up letter volume. Negative ink prevents a glossy corporate logo.
        painter.save()
        painter.translate(10, 8)
        painter.setBrush(gold)
        painter.setPen(QPen(shadow, 9, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(self._letters)
        painter.restore()
        gradient = QLinearGradient(left, top, left + bw * .22, top + bh)
        gradient.setColorAt(0, QColor("#f0f0eb"))
        gradient.setColorAt(.60, QColor("#bfc4c7"))
        gradient.setColorAt(1, QColor("#899296"))
        painter.setBrush(gradient)
        painter.setPen(QPen(shadow, 7, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(self._letters)

        # A gold path weaves OVER the body only where it intersects the letters.
        # Every second segment resumes BEHIND the glyphs, so the stroke alternates
        # visually through the wordmark, like traditional wildstyle graffiti.
        weave = QPainterPath()
        weave.moveTo(QPointF(left - bw * .02, top + bh * .81))
        for ux, uy in ((.16,.67), (.29,.39), (.40,.66), (.57,.24),
                       (.70,.51), (.86,.32), (1.03,.09)):
            weave.lineTo(QPointF(left + bw * ux, top + bh * uy))
        painter.save()
        painter.setClipPath(self._letters)
        painter.setPen(QPen(shadow, 20, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin))
        painter.drawPath(weave)
        painter.setPen(QPen(gold, 11, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin))
        painter.drawPath(weave)
        painter.restore()

        # End arrows point in different directions, embedded in the letter flow.
        self._arrow(
            painter,
            QPointF(left + bw * .83, top + bh * .25),
            QPointF(left + bw * 1.10, top + bh * .04), silver, 11,
        )
        self._arrow(
            painter,
            QPointF(left + bw * .20, top + bh * .73),
            QPointF(left - bw * .09, top + bh * 1.03), gold, 10,
        )
        self._arrow(
            painter,
            QPointF(left + bw * .70, top + bh * .84),
            QPointF(left + bw * .91, top + bh * 1.04), gold, 8,
        )
        painter.restore()

        # Crisp two-ink cross arrows in the margins; no crown, square or badge.
        self._arrow(
            painter, QPointF(w * .07, h * .22), QPointF(w * .21, h * .10),
            QColor("#ad9162"), 2.0
        )
        self._arrow(
            painter, QPointF(w * .74, h * .84), QPointF(w * .96, h * .68),
            QColor("#d6d8d7"), 2.0
        )
        painter.end()

def fluxor_app_icon():
    """Transparent F insignia; no old square photograph or colored badge."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    font = QFont("Arial Black")
    font.setBold(True)
    font.setItalic(True)
    font.setPixelSize(48)
    p.setFont(font)
    p.setPen(QColor("#d3d4d1"))
    p.drawText(QRectF(4, 2, 50, 56), Qt.AlignmentFlag.AlignCenter, "F")
    p.setPen(QPen(QColor("#ad9263"), 4.0, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(29, 55), QPointF(57, 19))
    p.end()
    return QIcon(pixmap)
