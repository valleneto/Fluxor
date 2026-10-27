"""OS020 offscreen GUI: async paged folder picker and combined modes."""
import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog
from fluxor_folder_picker import PAGE, SafeFolderPicker
from fluxor_iniciar import Inicio


def wait_until(app, callback, timeout=8):
    expires = time.monotonic() + timeout
    while time.monotonic() < expires:
        app.processEvents()
        if callback():
            return
        time.sleep(.008)
    raise AssertionError("Async folder listing did not complete")


def main():
    with TemporaryDirectory() as tmp:
        os.environ["HOME"] = tmp
        path = Path(tmp) / "many"
        path.mkdir()
        for index in range(PAGE + 15):
            (path / f"folder{index:03d}").mkdir()
        # Files in the folder do not appear in folder-only selector.
        for index in range(11):
            (path / f"file{index}.mp4").write_bytes(b"fixture")
        (path / "loop").symlink_to(path, target_is_directory=True)

        app = QApplication.instance() or QApplication([])
        picker = SafeFolderPicker(initial=str(path))
        picker.show()
        wait_until(app, lambda: not picker._busy)
        assert picker._path == str(path)
        assert picker.folders.count() == PAGE
        assert picker.more_button.isVisible()
        assert all("loop" not in picker.folders.item(n).text()
                   for n in range(picker.folders.count()))

        picker._more()
        wait_until(app, lambda: not picker._busy)
        assert picker.folders.count() == PAGE + 15
        assert not picker.more_button.isVisible()

        picker.address.setText("sftp://192.168.0.27/Volumes/SAMSUNG")
        picker._go_address()
        assert "Monte" in picker.status.text(), picker.status.text()
        picker.address.setText(str(path / "loop"))
        picker._go_address()
        wait_until(app, lambda: not picker._busy)
        assert "link simbólico" in picker.status.text(), picker.status.text()

        picker.address.setText(str(path))
        picker._go_address()
        wait_until(app, lambda: not picker._busy)
        picker._choose()
        wait_until(app, lambda: picker.result() == QDialog.DialogCode.Accepted)
        assert picker.selected_path == str(path)

        window = Inicio()
        window.show()
        window.navigate(2)
        app.processEvents()
        assert "Por tipo e ano" in [
            window.organizer.modo.itemText(i)
            for i in range(window.organizer.modo.count())
        ]
        assert "Por tipo, ano e mês" in [
            window.organizer.modo.itemText(i)
            for i in range(window.organizer.modo.count())
        ]
        assert "última modificação" in window.organizer.modo.toolTip()
        assert not window.organizer.b_organizar.isEnabled()
        window.close()
        app.processEvents()
    print("OS020 paged browser, cycle refusal, URL guidance and mode controls passed")


if __name__ == "__main__":
    main()
