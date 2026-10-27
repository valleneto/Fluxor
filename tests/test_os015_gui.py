"""OS015: contextual Inspector, compact layout and read-only preview smoke.

Only synthetic files in TemporaryDirectory; never touches the user's library.
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QApplication
from fluxor_core.library import index_folder
from fluxor_iniciar import Inicio


def find_row(table, name):
    for row in range(table.rowCount()):
        if table.item(row, 0).text() == name:
            return row
    raise AssertionError(f"file not found in Qt table: {name}")


def main():
    with TemporaryDirectory() as temp:
        os.environ["HOME"] = temp
        source = Path(temp) / "source"
        source.mkdir()
        photo = source / "sample.png"
        image = QImage(24, 24, QImage.Format.Format_RGB32)
        image.fill(QColor("#8fe5e5"))
        assert image.save(str(photo))
        (source / "document.docx").write_bytes(b"synthetic-docx-no-private-data")
        (source / "notes.txt").write_text("metadata only")
        cloud = source / "CloudStorage"
        cloud.mkdir()
        cloud_image = cloud / "cloud.png"
        assert image.save(str(cloud_image))
        db = Path(temp) / ".fluxor" / "library.db"
        assert index_folder(source, db)["total"] == 4

        app = QApplication.instance() or QApplication([])
        window = Inicio()
        window.show()
        window.resize(980, 610)
        window.navigate(1)
        window.library.refresh()
        app.processEvents()
        library = window.library
        assert library.table.rowCount() == 4
        assert library.media.isHidden()
        assert library.media.selected is None
        assert library.advanced_panel.isHidden()
        assert library.media.pick_button.isHidden()

        library.table.selectRow(find_row(library.table, "document.docx"))
        app.processEvents()
        assert library.media.isVisible()
        assert library.media.selected.endswith("document.docx")
        assert "document.docx" in library.media.metadata.text()
        assert "bytes bytes" not in library.media.metadata.text()
        assert not library.media.motion_button.isVisible()
        assert library.media.pick_button.isHidden()

        library.media.close_button.click()
        app.processEvents()
        assert library.media.isHidden()
        assert library.media.selected is None
        assert not library.table.selectedItems()

        library.table.selectRow(find_row(library.table, "sample.png"))
        app.processEvents()
        assert library.media.selected == str(photo)
        assert library.media.isVisible()
        pixmap = library.media.picture.pixmap()
        assert pixmap is not None and not pixmap.isNull()

        library.table.selectRow(find_row(library.table, "cloud.png"))
        app.processEvents()
        assert "nuvem" in library.media.note.text()
        assert not library.media.still_button.isEnabled()

        library.table.selectRow(find_row(library.table, "notes.txt"))
        app.processEvents()
        assert library.media.isVisible()
        assert not library.media.still_button.isVisible()
        assert "notes.txt" in library.media.metadata.text()
        library.refresh()
        app.processEvents()
        assert library.media.isHidden()
        assert not library.table.selectedItems()

        library.advanced_toggle.click()
        app.processEvents()
        assert library.advanced_panel.isVisible()
        library.advanced_toggle.click()
        app.processEvents()
        assert library.advanced_panel.isHidden()

        window.close()
        app.processEvents()
    print("OS015 contextual Inspector and responsive library smoke passed")


if __name__ == "__main__":
    main()
