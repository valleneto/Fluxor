"""Headless Qt smoke: home, navigation, library selection, and still Inspector.

Runs exclusively with synthetic files and a temporary HOME.
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QColor
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication
from fluxor_core.library import index_folder
from fluxor_iniciar import Inicio


def main():
    with TemporaryDirectory() as temp:
        os.environ["HOME"] = temp
        source = Path(temp) / "source"
        source.mkdir()
        still = source / "frame.png"
        image = QImage(32, 32, QImage.Format.Format_RGB32)
        image.fill(QColor("#8fe5e5"))
        assert image.save(str(still))
        database = Path(temp) / ".fluxor" / "library.db"
        index_folder(source, database)

        app = QApplication.instance() or QApplication([])
        window = Inicio()
        window.show()
        app.processEvents()
        assert window.pages.count() == 3
        assert window.zen is not None
        window.resize(1100, 700)
        window.navigate(1)
        window.library.refresh()
        app.processEvents()
        assert window.library.table.rowCount() == 1
        # Regression: all primary actions must fit on a 13-inch laptop window.
        for button in (
            window.library.analysis_button,
            window.library.versions_button,
            window.library.duplicates_button,
            window.library.review_button,
            window.library.review_list_button,
            window.library.collection_button,
        ):
            right = button.mapTo(window, QPoint(button.width(), 0)).x()
            assert right <= window.width(), (button.text(), right, window.width())
        window.library.table.setCurrentCell(0, 0)
        window.library.inspect()
        app.processEvents()
        assert window.library.media.selected == str(still)
        window.library.media.show_still()
        pixmap = window.library.media.picture.pixmap()
        assert pixmap is not None and not pixmap.isNull()
        window.navigate(0)
        window.reduce_motion.setChecked(True)
        assert window.zen.reduced_motion
        assert not window.zen.timer.isActive()
        window.close()
        app.processEvents()
    print("OS014 Qt offscreen smoke passed")


if __name__ == "__main__":
    main()
