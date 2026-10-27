"""FLUXOR identity — compact non-square two-ink throw-up wordmark.

Brushed silver and muted gold, entirely vector drawn. No stock fonts bundled,
external image, square badge, crown, fluorescent colors or third-party assets.
"""
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPainterPathStroker, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class FluxorWordmark(QWidget):
    """Hand-composed angular wildstyle letters, not a font with arrows added."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("fluxorWordmark")
        self.setMinimumSize(145, 66)
        self.setMaximumHeight(94)
        self.setToolTip("FLUXOR · wildstyle em prata e dourado")

        def figure(*points):
            path = QPainterPath(QPointF(*points[0]))
            for point in points[1:]:
                path.lineTo(QPointF(*point))
            return path

        # Six individually authored letter skeletons, joined with negative
        # spaces, linked directional strokes and crossing layers.
        self._glyphs = [
            # F
            figure((13,88), (8,25), (59,16)),
            figure((13,57), (44,47)),
            # L
            figure((70,16), (67,86), (110,75)),
            # U
            figure((118,21), (116,69), (134,86), (153,73), (159,19)),
            # X
            figure((170,18), (209,85)),
            figure((208,17), (169,88)),
            # O
            figure((225,24), (243,16), (266,28), (265,70),
                   (246,86), (225,74), (225,24)),
            # R
            figure((279,86), (279,24), (308,19), (323,34), (313,52),
                   (279,57)),
            figure((304,53), (333,84)),
        ]
        stroker = QPainterPathStroker()
        stroker.setWidth(19)
        stroker.setCapStyle(Qt.PenCapStyle.SquareCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        self._filled_letters = QPainterPath()
        for glyph in self._glyphs:
            self._filled_letters.addPath(stroker.createStroke(glyph))

        self._under = [
            figure((-4,96), (52,65), (94,81), (149,40),
                   (189,69), (240,31), (339,12)),
            figure((1,8), (76,42), (133,11), (200,78),
                   (258,49), (334,98)),
        ]
        self._over = figure(
            (6,93), (66,52), (126,73), (175,19),
            (229,76), (281,35), (334,11),
        )

    @staticmethod
    def _trace(painter, path, ink, width, edge="#0c0d0e", edge_width=None):
        edge_pen = QPen(QColor(edge), edge_width or width + 6,
                        Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap,
                        Qt.PenJoinStyle.MiterJoin)
        painter.setPen(edge_pen)
        painter.drawPath(path)
        painter.setPen(QPen(QColor(ink), width, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin))
        painter.drawPath(path)

    @staticmethod
    def _arrow(painter, tip, direction, ink, width=5):
        """Straight arrow head terminating an actual letter/connector stroke."""
        import math
        angle = math.atan2(direction[1], direction[0])
        span = 15
        painter.setPen(QPen(QColor("#0c0d0e"), width + 6,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap,
                            Qt.PenJoinStyle.MiterJoin))
        for offset in (-.68, .68):
            other = QPointF(tip[0] - span * math.cos(angle + offset),
                            tip[1] - span * math.sin(angle + offset))
            painter.drawLine(QPointF(*tip), other)
        painter.setPen(QPen(QColor(ink), width, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin))
        for offset in (-.68, .68):
            other = QPointF(tip[0] - span * math.cos(angle + offset),
                            tip[1] - span * math.sin(angle + offset))
            painter.drawLine(QPointF(*tip), other)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        scale = min((w - 6) / 365.0, (h - 4) / 122.0)
        painter.translate((w - 350 * scale) * .5, (h - 110 * scale) * .5)
        painter.scale(scale, scale)
        painter.shear(-.045, 0)

        gold = "#b79b6d"
        silver = "#d8d9d7"
        charcoal = "#0c0d0e"

        # Wildstyle requires true crossings: the paths are laid BELOW the
        # geometric letters, then selected segments continue ABOVE the faces.
        painter.setBrush(Qt.BrushStyle.NoBrush)
        self._trace(painter, self._under[0], gold, 6, charcoal, 13)
        self._trace(painter, self._under[1], silver, 5, charcoal, 12)

        painter.save()
        painter.translate(5, 7)
        for glyph in self._glyphs:
            self._trace(painter, glyph, gold, 18, charcoal, 29)
        painter.restore()

        for glyph in self._glyphs:
            self._trace(painter, glyph, silver, 18, charcoal, 29)
        # Second ink cuts ACROSS the actual letter geometry, without leaving
        # the silver letter bodies. Not an ornamental arrow sticker.
        painter.save()
        painter.setClipPath(self._filled_letters)
        self._trace(painter, self._over, gold, 6, charcoal, 11)
        painter.restore()

        # Tip directions derive from the outgoing connector segments.
        self._arrow(painter, (339, 12), (1, -.45), gold, 5)
        self._arrow(painter, (334, 98), (1, .25), silver, 5)
        self._arrow(painter, (-4, 96), (-1, .47), gold, 5)
        self._arrow(painter, (334, 11), (1, -.64), gold, 4)
        # A few ink cuts inside the letterforms signal spray/tag treatment
        # without colors, characters, crowns or decorative clutter.
        painter.setPen(QPen(QColor("#756953"), 2))
        painter.drawLine(QPointF(94, 10), QPointF(120, 0))
        painter.drawLine(QPointF(211, 101), QPointF(236, 91))
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
