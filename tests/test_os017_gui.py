"""OS017 mural, navigation and backward-compatibility smoke with synthetic files."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from fluxor_mural import FluxorMural
from fluxor_iniciar import Inicio
from fluxor_core.library import index_folder


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
        # One Qt paint-smoke; repeated pixmap conversions on some Linux Qt
        # builds can crash the Python interpreter *after* a successful test.
        frame = mural.grab()
        assert not frame.isNull()
        screenshot = os.environ.get("FLUXOR_OS017_SCREENSHOT")
        if screenshot:
            image_path = Path(screenshot)
            image_path.parent.mkdir(parents=True, exist_ok=True)
            assert frame.save(str(image_path), "PNG")
        before = mural.phase
        mural.advance()
        assert mural.phase != before, "animation timer must advance its phase"

        window.reduce_motion.setChecked(True)
        app.processEvents()
        assert mural.reduced_motion
        assert not mural.timer.isActive()
        frozen = mural.phase
        mural.advance()
        assert mural.phase == frozen
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

        assert sample.read_bytes() == b"original-intact"
        window.close()
        app.processEvents()
    print("OS017 graffiti mural paint, motion state, navigation and file safety passed")


if __name__ == "__main__":
    main()
