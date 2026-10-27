"""OS022 screenshot-reference controls: no extra SMB buttons in primary UI."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton, QFrame
import fluxor_folder_picker
from fluxor_iniciar import Inicio
from fluxor_design import STYLESHEET


def main():
    with TemporaryDirectory() as directory:
        os.environ["HOME"] = directory
        app = QApplication.instance() or QApplication([])
        win = Inicio()
        win.resize(1050, 690)
        win.show()
        app.processEvents()
        assert win.styleSheet() == STYLESHEET
        assert win.side_home.text().startswith("01")
        assert win.side_library.text().startswith("02")
        assert win.side_organize.text().startswith("03")
        assert win.wordmark.isVisible()
        assert hasattr(win.wordmark, "_letters"), "OS019 original glyphs must be restored"
        assert not hasattr(win.wordmark, "_glyphs"), "OS020 replacement logo still active"
        assert win.zen.ROWS >= 6

        win.navigate(1)
        app.processEvents()
        lib = win.library
        assert lib.index_button.text().strip().endswith("Adicionar pasta")
        assert not hasattr(lib, "smb_button")
        assert lib.advanced_toggle.text().startswith("Filtros e ferramentas")

        win.navigate(2)
        app.processEvents()
        org = win.organizer
        assert org.b_origem.text() == "Escolher origem"
        assert org.b_destino.text() == "Escolher destino"
        assert not hasattr(org, "b_conectar_smb")
        acervo = next(frame for frame in org.findChildren(QFrame)
                      if frame.objectName() == "stageCard"
                      and org.b_origem in frame.findChildren(QPushButton))
        controls = [w.text() for w in acervo.findChildren(QPushButton)]
        assert controls == ["Escolher origem", "Escolher destino"], controls
        assert org.modo.findText("Combinar critérios (ordenar)") >= 0
        assert org.modo_escolhido() == org.modo.currentText()

        calls = []
        before = fluxor_folder_picker.connect_smb
        fluxor_folder_picker.connect_smb = lambda parent: calls.append(parent)
        try:
            picker = fluxor_folder_picker.SafeFolderPicker(
                initial=str(Path(directory))
            )
            picker.show()
            app.processEvents()
            assert picker.network_button.text() == "Conectar SMB (Finder)"
            picker.network_button.click()
            assert calls == [picker]
            picker.close()
        finally:
            fluxor_folder_picker.connect_smb = before
        win.close()
        app.processEvents()
        app.quit()
    print("OS022 screenshot controls, hidden SMB integration and old layout passed")


if __name__ == "__main__":
    main()
