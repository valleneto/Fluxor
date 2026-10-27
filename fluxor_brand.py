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

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        bounds = self._bounds
        if bounds.width() <= 0 or bounds.height() <= 0:
            p.end()
            return
        scale = min((w - 14) / (bounds.width() + 11),
                    (h - 18) / (bounds.height() + 15))
        p.save()
        p.translate(w * .50, h * .47)
        p.shear(-.10, 0.0)
        p.scale(scale, scale)
        p.translate(-bounds.center().x(), -bounds.center().y())

        # Angular extrusion in gold; silver face = deliberately only two inks.
        p.save()
        p.translate(7, 7)
        p.setBrush(QColor("#9b7d4b"))
        p.setPen(QPen(QColor("#a98a57"), 8, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPath(self._letters)
        p.restore()

        silver = QLinearGradient(bounds.left(), bounds.top(),
                                 bounds.left(), bounds.bottom())
        silver.setColorAt(0, QColor("#f1f0eb"))
        silver.setColorAt(.46, QColor("#bac0c4"))
        silver.setColorAt(1, QColor("#777f86"))
        p.setBrush(silver)
        p.setPen(QPen(QColor("#252a2d"), 5, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPath(self._letters)
        p.restore()

        # Two angular slashes and a sharp arrow tail, instead of a square logo.
        p.setPen(QPen(QColor("#ae905c"), 2.0, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin))
        tail = QPainterPath(QPointF(w * .45, h * .88))
        tail.lineTo(w * .76, h * .82)
        tail.lineTo(w * .72, h * .75)
        p.drawPath(tail)
        p.drawLine(QPointF(w * .77, h * .16), QPointF(w * .82, h * .11))
        p.drawLine(QPointF(w * .81, h * .20), QPointF(w * .87, h * .14))
        p.end()

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
