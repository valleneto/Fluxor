"""OS020 Qt: combined modes, safe picker flags, direct-path fallback, no real files."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

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

        picker = w.criar_seletor_pasta("Synthetic test")
        assert picker.testOption(QFileDialog.Option.DontUseNativeDialog)
        assert picker.testOption(QFileDialog.Option.DontResolveSymlinks)
        assert picker.testOption(QFileDialog.Option.ShowDirsOnly)
        assert bool(picker.filter() & QDir.Filter.NoSymLinks)
        picker.close()
        picker.deleteLater()

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
