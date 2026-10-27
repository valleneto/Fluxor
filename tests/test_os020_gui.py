"""OS020 Qt controller contract without native offscreen widget teardown.

Qt's Linux CI backend segfaults on QApplication finalization in this particular
picker smoke even though every assertion passes. Existing OS019/018 tests still
exercise real Qt windows; this test verifies the new controller and flags.
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QDir
from PySide6.QtWidgets import QFileDialog
from fluxor_app_integrado import FluxorIntegrado
from fluxor_core.plan import MODOS


class FakePicker:
    FileMode = QFileDialog.FileMode
    Option = QFileDialog.Option

    def __init__(self, parent, title, start):
        self.parent, self.title, self.start = parent, title, start
        self.options = {}
        self.flags = QDir.Filter.NoFilter

    def setFileMode(self, mode):
        self.file_mode = mode

    def setOption(self, option, enabled):
        self.options[option] = enabled

    def setFilter(self, flags):
        self.flags = flags


class TextStub:
    def __init__(self, text=""):
        self.value = text

    def text(self):
        return self.value

    def setText(self, value):
        self.value = value


class OriginUIStub:
    def __init__(self):
        self.origem = ""
        self.origem_caminho = TextStub()
        self.origem_label = TextStub()
        self.plano = object()

    def invalidar_previa(self):
        self.plano = None


def main():
    assert "Por tipo e ano" in MODOS
    assert "Por tipo, ano e mês" in MODOS

    with TemporaryDirectory() as temp:
        os.environ["HOME"] = temp
        with patch("fluxor_app_integrado.QFileDialog", FakePicker):
            picker = FluxorIntegrado.criar_seletor_pasta(None, "Synthetic")
        assert picker.file_mode == QFileDialog.FileMode.Directory
        assert picker.options[QFileDialog.Option.DontUseNativeDialog]
        assert picker.options[QFileDialog.Option.DontResolveSymlinks]
        assert picker.options[QFileDialog.Option.ShowDirsOnly]
        assert bool(picker.flags & QDir.Filter.NoSymLinks)

        ui = OriginUIStub()
        local = Path(temp) / "folder"
        local.mkdir()
        ui.origem_caminho.setText(str(local))
        FluxorIntegrado.aplicar_origem_digitada(ui)
        assert ui.origem == str(local)
        assert ui.plano is None
        ui.plano = object()
        ui.origem_caminho.setText("~/folder")
        FluxorIntegrado.aplicar_origem_digitada(ui)
        assert ui.origem == str(local)
        assert ui.plano is None
        assert "folder" in ui.origem_label.text()

    print("OS020 picker flags, combined options and source-path controller passed")


if __name__ == "__main__":
    main()
