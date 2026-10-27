"""OS020 Qt: combined modes, safe picker flags, direct-path fallback, no real files."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDir
from PySide6.QtWidgets import QApplication, QFileDialog
from fluxor_app_integrado import FluxorIntegrado


def main():
    with TemporaryDirectory() as temp:
        os.environ["HOME"] = temp
        app = QApplication.instance() or QApplication([])
        w = FluxorIntegrado()
        w.show()
        app.processEvents()

        options = [w.modo.itemText(i) for i in range(w.modo.count())]
        assert "Por tipo e ano" in options
        assert "Por tipo, ano e mês" in options
        w.modo.setCurrentText("Por tipo, ano e mês")
        assert w.modo.currentText() == "Por tipo, ano e mês"
        assert w.plano is None

        # Instantiating QFileDialog inside the Linux offscreen test triggers a
        # Qt native backend teardown crash. Verify the actual factory calls
        # with a fake; native picker interaction must be validated on macOS.
        class FakePicker:
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

        with patch("fluxor_app_integrado.QFileDialog", FakePicker):
            picker = w.criar_seletor_pasta("Synthetic test")
        assert picker.parent is w
        assert picker.file_mode == QFileDialog.FileMode.Directory
        assert picker.options[QFileDialog.Option.DontUseNativeDialog]
        assert picker.options[QFileDialog.Option.DontResolveSymlinks]
        assert picker.options[QFileDialog.Option.ShowDirsOnly]
        assert bool(picker.flags & QDir.Filter.NoSymLinks)

        origin = Path(temp) / "synthetic-folder"
        origin.mkdir()
        w.origem_caminho.setText(str(origin))
        w.aplicar_origem_digitada()
        assert w.origem == str(origin)
        assert w.plano is None
        w.origem_caminho.setText("~/synthetic-folder")
        w.aplicar_origem_digitada()
        assert w.origem == str(origin)

        w.destino_tipo.setCurrentIndex(1)
        app.processEvents()
        assert w.plano is None
        assert not w.b_organizar.isEnabled()

        w.close()
        app.processEvents()
    print("OS020 Qt composite modes, non-native no-symlink picker and manual origin path passed")


if __name__ == "__main__":
    main()
