"""OS016 premium layout smoke — synthetic data and offscreen Qt only."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame
from PySide6.QtCore import QPoint
from PySide6.QtGui import QImage
from fluxor_core.library import index_folder
from fluxor_iniciar import Inicio
from fluxor_design import STYLESHEET


def main():
    with TemporaryDirectory() as directory:
        os.environ["HOME"] = directory
        root = Path(directory) / "source"
        root.mkdir()
        fixture = root / "safe.docx"
        fixture.write_bytes(b"synthetic-file-only")
        index_folder(root, Path(directory) / ".fluxor" / "library.db")
        app = QApplication.instance() or QApplication([])
        window = Inicio()
        window.resize(980, 700)
        window.show()
        app.processEvents()
        assert "QPushButton#primaryAction" in STYLESHEET
        assert window.styleSheet() == STYLESHEET
        assert window.sidebar.objectName() == "sidebar"
        assert window.side_home.isChecked()
        assert not window.side_library.isChecked()
        assert window.zen.timer.interval() == 50
        assert not window.zen.grab().isNull()

        window.reduce_motion.setChecked(True)
        assert not window.zen.timer.isActive()
        assert window.zen.reduced_motion
        window.reduce_motion.setChecked(False)

        window.navigate(1)
        app.processEvents()
        assert window.side_library.isChecked()
        assert not window.side_home.isChecked()
        assert window.library.media.isHidden()
        assert window.library.advanced_panel.isHidden()
        assert window.library.index_button.objectName() == "primaryAction"

        window.navigate(2)
        app.processEvents()
        assert window.side_organize.isChecked()
        assert window.organizer.b_previa.objectName() == "primaryAction"
        assert window.organizer.b_organizar.isEnabled() is False
        assert window.organizer.status.isVisible()
        assert window.organizer.logs.isVisible()
        cards = [x for x in window.organizer.findChildren(QFrame)
                 if x.objectName() == "stageCard"]
        assert len(cards) == 3
        for card in cards:
            assert card.isVisible()
            # Report must stay in the viewport on a typical 13-inch display.
            bottom = card.mapTo(window, QPoint(0, card.height())).y()
            assert bottom <= window.height() + 6, (card.objectName(), bottom, window.height())

        assert window.organizer.stages_scroll.isVisible()
        # On a smaller laptop viewport the report remains visible,
        # while source/options can scroll independently.
        window.resize(900, 580)
        app.processEvents()
        report = cards[-1]
        report_bottom = report.mapTo(window, QPoint(0, report.height())).y()
        assert report_bottom <= window.height() + 6, (
            "report is cut off", report_bottom, window.height())
        assert window.organizer.logs.isVisible()

        assert fixture.read_bytes() == b"synthetic-file-only"
        window.close()
        app.processEvents()
    print("OS016 premium visual hierarchy, motion and report smoke passed")


if __name__ == "__main__":
    main()
