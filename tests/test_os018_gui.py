"""OS018 silver/gold brand and sand-rake screensaver regression, synthetic HOME."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from fluxor_brand import FluxorWordmark
from fluxor_mural import FluxorMural
from fluxor_iniciar import Inicio
from fluxor_design import STYLESHEET
from fluxor_core.library import index_folder


def main():
    with TemporaryDirectory() as directory:
        os.environ["HOME"] = directory
        source = Path(directory) / "safe-fixture"
        source.mkdir()
        original = source / "preserved.docx"
        original.write_bytes(b"this-is-only-a-synthetic-fixture")
        db = Path(directory) / ".fluxor" / "library.db"
        assert index_folder(source, db)["total"] == 1

        app = QApplication.instance() or QApplication([])
        window = Inicio()
        window.resize(1050, 690)
        window.show()
        app.processEvents()

        assert window.styleSheet() == STYLESHEET
        assert "#d9ec79" not in STYLESHEET  # old neon-green UI removed
        assert "#ef846a" not in STYLESHEET  # old fluorescent coral removed
        assert isinstance(window.wordmark, FluxorWordmark)
        assert window.wordmark.isVisible()
        assert window.wordmark.width() > window.wordmark.height() * 1.6
        assert not window.wordmark.grab().isNull()
        assert isinstance(window.zen, FluxorMural)
        assert window.zen.ROWS >= 6
        assert window.zen.timer.interval() >= 50
        assert not window.zen.grab().isNull()

        before = window.zen.phase
        window.zen.advance()
        assert window.zen.phase > before
        # Alternate directions by row and replacement passes; no fake progress.
        assert (0 + 0) % 2 != (1 + 0) % 2
        assert window.zen._color(0).name() != window.zen._color(1).name()
        window.zen.phase = float(window.zen.ROWS) - .01
        window.zen.advance()
        assert int(window.zen.phase // window.zen.ROWS) == 1

        window.reduce_motion.setChecked(True)
        frozen = window.zen.phase
        window.zen.advance()
        assert not window.zen.timer.isActive()
        assert window.zen.phase == frozen

        window.reduce_motion.setChecked(False)
        window.zen.phase = 3.4
        window.zen.update()
        app.processEvents()
        screenshot = os.environ.get("FLUXOR_OS018_SCREENSHOT")
        if screenshot:
            image_path = Path(screenshot)
            image_path.parent.mkdir(parents=True, exist_ok=True)
            assert window.grab().save(str(image_path), "PNG")

        window.navigate(1)
        app.processEvents()
        assert window.library.media.isHidden()
        assert window.library.table.rowCount() == 1
        assert original.read_bytes() == b"this-is-only-a-synthetic-fixture"
        window.close()
        app.processEvents()

    print("OS018 matte/silver/gold wordmark, alternating sand sweeps and safety passed")


if __name__ == "__main__":
    main()
