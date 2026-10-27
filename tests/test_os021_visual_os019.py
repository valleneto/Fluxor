"""OS021 classic presentation: OS019 logo and original action buttons,
with modern safety, advanced composition and optional SMB dialog.
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from fluxor_iniciar import Inicio
from fluxor_folder_picker import SafeFolderPicker
from fluxor_brand import FluxorWordmark

def main():
    with TemporaryDirectory() as directory:
        os.environ["HOME"] = directory
        app = QApplication.instance() or QApplication([])
        window = Inicio()
        window.show()
        app.processEvents()
        assert isinstance(window.wordmark, FluxorWordmark)
        assert window.zen.timer.interval() >= 50
        window.navigate(2)
        app.processEvents()
        organizer = window.organizer
        assert organizer.b_origem.text() == "Escolher origem"
        assert organizer.b_destino.text() == "Escolher destino"
        assert not hasattr(organizer, "b_conectar_smb")
        assert not organizer.criterios_painel.isVisible()
        assert organizer.modo.currentText() == "Por tipo"
        assert organizer.destino_tipo.count() == 2
        assert organizer.destino_tipo.itemText(1) == "Acrescentar a uma organização existente"
        # Extended composition remains accessible by explicit opt-in.
        organizer.modo.setCurrentText("Combinar critérios (ordenar)")
        app.processEvents()
        assert organizer.criterios_painel.isVisible()
        window.navigate(1)
        app.processEvents()
        assert not hasattr(window.library, "smb_button")
        picker = SafeFolderPicker(initial=directory)
        picker.show()
        app.processEvents()
        assert picker.connect_smb_button.text() == "Conectar SMB (Finder)…"
        picker.close()
        window.close()
        app.processEvents()
    print("OS019 interface/layout/wordmark restored, OS021 advanced features retained")

if __name__ == "__main__":
    main()
