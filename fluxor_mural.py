"""FLUXOR Mural — vector street-art motion, no images or network assets.

Art direction: spray-painted street lettering, rhythmic ribbons and purposeful
movement. 100% QPainter, reusable in the existing safe desktop Qt app.
"""
import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath,
    QPen, QRadialGradient, QTransform,
)

from fluxor_zen import ZenCore


class FluxorMural(ZenCore):
    """Original authored mural. Keeps ZenCore state and reduced-motion API."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(240, 170)
        # Same 20fps ceiling as ZenCore, essential for older Macs.
        self.timer.setInterval(50)
        # Cache vector glyphs: QPainterPath.addText does font shaping and should
        # never run sixty times a minute just to redraw a slow motion ribbon.
        font = QFont("Arial Black")
        font.setBold(True)
        font.setItalic(True)
        font.setPixelSize(130)
        self._lettering = QPainterPath()
        self._lettering.addText(0, 0, font, "FLUXOR")
        self._letter_bounds = self._lettering.boundingRect()

    def advance(self):
        """Keep the field visibly alive without accelerating in background."""
        if not self.isVisible() or self.reduced_motion:
            return
        speed = {
            "idle": 0.95,
            "scanning": 1.45,
            "organizing": 1.65,
            "complete": 0.0,
            "error": 0.0,
        }.get(self.state, 0.95)
        if speed:
            self.phase = (self.phase + speed) % 360.0
            self.update()

    @staticmethod
    def _ribbon(p, w, h, phase, lane, color):
        offset = math.sin(phase * (0.8 + lane * 0.12) + lane) * h * 0.022
        y = h * (0.22 + lane * 0.23) + offset
        path = QPainterPath(QPointF(-w * .12, y + h * .16))
        path.cubicTo(
            QPointF(w * .23, y - h * .31 + offset),
            QPointF(w * .42, y + h * .30),
            QPointF(w * .70, y - h * .11),
        )
        path.cubicTo(
            QPointF(w * .84, y - h * .29 - offset),
            QPointF(w * 1.04, y + h * .19),
            QPointF(w * 1.13, y - h * .15),
        )
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(color, max(1.6, h * (.008 if lane != 1 else .011)),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(path)
        lighter = QColor(color)
        lighter.setAlpha(55)
        p.setPen(QPen(lighter, max(2.0, h * .035),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(path)

    @staticmethod
    def _spray(p, w, h):
        """Deterministic tiny dots: textural finish, not an animated particle field."""
        p.setPen(Qt.PenStyle.NoPen)
        # Fixed distribution, no random state or file reads.
        for i in range(115):
            x = ((i * 79 + 37) % 997) / 997 * w
            y = ((i * 127 + 59) % 991) / 991 * h
            edge = abs(x / max(1, w) - .5)
            tone = QColor(197, 207, 210, 14 if edge < .25 else 28)
            p.setBrush(tone)
            diameter = 0.65 + (i % 3) * 0.35
            p.drawEllipse(QRectF(x, y, diameter, diameter))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = float(self.width()), float(self.height())
        if w < 2 or h < 2:
            p.end()
            return

        background = QLinearGradient(0, 0, w, h)
        background.setColorAt(0.0, QColor("#0b1016"))
        background.setColorAt(0.55, QColor("#161823"))
        background.setColorAt(1.0, QColor("#0c1116"))
        p.fillRect(self.rect(), QBrush(background))

        glow = QRadialGradient(QPointF(w * .50, h * .47), max(w, h) * .54)
        glow.setColorAt(0.0, QColor(46, 83, 84, 125))
        glow.setColorAt(0.60, QColor(29, 46, 58, 57))
        glow.setColorAt(1.0, QColor(10, 17, 25, 0))
        p.fillRect(self.rect(), QBrush(glow))

        # Architectural concrete grid, deliberately irregular and low contrast.
        p.setPen(QPen(QColor(157, 173, 181, 19), 1))
        spacing = max(35, int(w / 13))
        for x in range(-spacing, int(w) + spacing, spacing):
            p.drawLine(x, 0, x + int(h * .08), int(h))
        p.setPen(QPen(QColor(157, 173, 181, 12), 1))
        for y in (h * .20, h * .52, h * .86):
            p.drawLine(QPointF(0, y), QPointF(w, y - h * .055))

        phase = math.radians(self.phase)
        intensity = 1 if self.state in ("scanning", "organizing") else .55
        t = phase * intensity
        self._ribbon(p, w, h, t, 0, QColor(116, 218, 207, 170))
        self._ribbon(p, w, h, -t * .7, 1, QColor(236, 105, 83, 200))
        self._ribbon(p, w, h, t * .55, 2, QColor(213, 235, 108, 185))
        self._spray(p, w, h)

        # Raw angled marks, reminiscent of paint dashes but kept legible.
        accent = QColor("#d8eb76") if self.state != "error" else QColor("#fd886f")
        p.setPen(QPen(accent, max(2, h * .010), Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(w * .12, h * .27), QPointF(w * .18, h * .15))
        p.drawLine(QPointF(w * .83, h * .83), QPointF(w * .89, h * .72))
        p.setPen(QPen(QColor("#e77b69"), max(2, h * .007), Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(w * .77, h * .19), QPointF(w * .86, h * .16))

        # Hand-composed lettering: stretched, slanted, outlined, layered like
        # a clean graffiti piece. All geometry remains scalable and local.
        lettering = self._lettering
        bounds = self._letter_bounds
        target_w, target_h = w * .79, h * .37
        scale = min(target_w / max(bounds.width(), 1),
                    target_h / max(bounds.height(), 1))
        # Tilt in the painter keeps letterforms crisp at any size.
        p.save()
        p.translate(w * .50, h * .51)
        p.rotate(-5)
        p.scale(scale, scale)
        p.translate(-bounds.center().x(), -bounds.center().y())

        def offset_layer(dx, dy, fill, edge=None, thick=0):
            p.save()
            p.translate(dx, dy)
            p.setBrush(QColor(fill))
            p.setPen(QPen(QColor(edge), thick, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin) if edge
                     else Qt.PenStyle.NoPen)
            p.drawPath(lettering)
            p.restore()

        offset_layer(17, 20, "#05080d", "#05080d", 13)
        offset_layer(9, 11, "#ee7d66", "#0c1017", 8)
        offset_layer(-4, -3, "#d8eb76", "#0c1017", 12)
        offset_layer(0, 0, "#f5f0e4", "#14171c", 6)
        p.restore()

        # Restrained hand-tag underline; the pulse is aesthetic, not progress.
        p.setPen(QPen(QColor("#78e0d4"), max(2.4, h * .009),
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        underline = QPainterPath(QPointF(w * .20, h * .75))
        underline.cubicTo(QPointF(w * .40, h * (.84 + math.sin(t) * .01)),
                          QPointF(w * .59, h * .71),
                          QPointF(w * .81, h * .77))
        p.drawPath(underline)

        # Always readable, even with reduced motion enabled.
        p.setFont(QFont("Arial", max(8, int(min(12, h * .034)))))
        p.setPen(QColor("#a9c0c3"))
        p.drawText(QRectF(w * .03, h * .88, w * .94, h * .075),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                   "FIND YOUR FLOW  /  001")
        p.end()
