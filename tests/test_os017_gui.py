"""OS017 mural, navigation and backward-compatibility smoke with synthetic files."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from fluxor_mural import FluxorMural
from fluxor_iniciar import Inicio
from fluxor_core.library import index_folder


def image_digest(widget):
    image = widget.grab().toImage()
    assert not image.isNull()
    return sha256(bytes(image.bits())).hexdigest()


def main():
    with TemporaryDirectory() as d:
        os.environ["HOME"] = d
        source = Path(d) / "fixture"
        source.mkdir()
        sample = source / "do-not-change.txt"
        sample.write_bytes(b"original-intact")
        db = Path(d) / ".fluxor" / "library.db"
        assert index_folder(source, db)["total"] == 1
        app = QApplication.instance() or QApplication([])
        window = Inicio()
        window.resize(1010, 710)
        window.show()
        app.processEvents()

        mural = window.zen
        assert isinstance(mural, FluxorMural)
        assert mural.timer.interval() >= 50
        assert mural.isVisible()
        assert mural.width() > 240
        first = image_digest(mural)
        mural.phase += 53
        mural.update()
        app.processEvents()
        second = image_digest(mural)
        assert first != second, "mural must be animated, not a static photograph"

        window.reduce_motion.setChecked(True)
        app.processEvents()
        assert mural.reduced_motion
        assert not mural.timer.isActive()
        frozen = image_digest(mural)
        app.processEvents()
        assert image_digest(mural) == frozen
        window.reduce_motion.setChecked(False)
        assert not mural.reduced_motion

        assert window.side_home.isChecked()
        window.side_home.click()  # same route must not toggle nav to none
        assert window.side_home.isChecked()
        window.navigate(1)
        app.processEvents()
        assert window.side_library.isChecked()
        assert window.library.media.isHidden()
        assert window.library.table.rowCount() == 1
        window.navigate(0)
        app.processEvents()
        assert window.side_home.isChecked()
        assert image_digest(mural)

        assert sample.read_bytes() == b"original-intact"
        window.close()
        app.processEvents()
    print("OS017 graffiti vector mural, reduced motion, nav and file safety passed")


if __name__ == "__main__":
    main()
