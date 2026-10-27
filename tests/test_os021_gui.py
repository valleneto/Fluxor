"""OS021 Qt offscreen: order controls, dangerous stale URL and keyset paging."""
import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from fluxor_folder_picker import SafeFolderPicker, PAGE
from fluxor_iniciar import Inicio


def until(app, predicate):
    end = time.monotonic() + 12
    while time.monotonic() < end:
        app.processEvents()
        if predicate():
            return
        time.sleep(.01)
    raise AssertionError("Folder navigation did not finish")


def main():
    with TemporaryDirectory() as d:
        os.environ["HOME"] = d
        root = Path(d) / "folders"
        root.mkdir()
        for i in range(PAGE + 10):
            (root / f"folder{i:03d}").mkdir()
        picker_app = QApplication.instance() or QApplication([])
        picker = SafeFolderPicker(initial=str(root))
        picker.show()
        until(picker_app, lambda: not picker._busy)
        assert picker.folders.count() == PAGE
        first = [picker.folders.item(i).data(256) for i in range(PAGE)]
        # File additions before the last cursor cannot duplicate older entries.
        (root / "aaa-new").mkdir()
        picker._more()
        until(picker_app, lambda: not picker._busy)
        all_paths = [picker.folders.item(i).data(256) for i in range(picker.folders.count())]
        assert len(all_paths) == PAGE + 10, len(all_paths)
        assert all_paths[:PAGE] == first
        assert len(set(all_paths)) == len(all_paths)
        picker.address.setText("smb://host/share")
        picker._go_address()
        assert picker._path == "" and not picker.choose_button.isEnabled()
        picker.close()

        window = Inicio()
        window.show()
        window.navigate(2)
        picker_app.processEvents()
        o = window.organizer
        o.modo.setCurrentText("Combinar critérios (ordenar)")
        o.criterios[0].setCurrentText("Ano/mês")
        o.criterios[1].setCurrentText("Tipo")
        assert o.criterios_painel.isVisible()
        assert o.modo_escolhido() == "Combinar: Ano/mês > Tipo"
        assert not o.b_organizar.isEnabled()
        assert o.b_conectar_smb is not None
        window.close()
        picker_app.processEvents()
    print("OS021 Qt criteria order, SMB affordance and stable keyset pagination passed")


if __name__ == "__main__":
    main()
