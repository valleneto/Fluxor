"""OS019 Qt offscreen: append mode user controls, no personal files or copies."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from fluxor_iniciar import Inicio


def main():
    with TemporaryDirectory() as tmp:
        os.environ["HOME"] = tmp
        app = QApplication.instance() or QApplication([])
        window = Inicio()
        window.show()
        window.resize(1024, 650)
        window.navigate(2)
        app.processEvents()
        panel = window.organizer
        assert panel.destino_tipo.count() == 2
        assert panel.destino_tipo.currentIndex() == 0
        assert not panel.merge_hint.isVisible()

        panel.destino = "/synthetic/parent-folder"
        panel.destino_tipo.setCurrentIndex(1)
        app.processEvents()
        assert panel.destino == "", "a mode switch must clear old destination"
        assert panel.merge_hint.isVisible()
        assert "Fluxor_Organizado" in panel.destino_label.text()
        assert "Fluxor_Organizado" in panel.b_destino.text()
        assert panel.plano is None
        assert not panel.b_organizar.isEnabled()

        panel.destino = "/synthetic/Fluxor_Organizado"
        panel.destino_tipo.setCurrentIndex(0)
        app.processEvents()
        assert panel.destino == "", "switching back cannot reuse old path"
        assert not panel.merge_hint.isVisible()
        assert not panel.b_organizar.isEnabled()

        # Worker receives the append flag without performing IO in this smoke.
        from fluxor_app_integrado import Tarefa
        worker = Tarefa("preview", "/origin", "/dest/Fluxor_Organizado",
                        "Por tipo", True, acrescentar=True)
        assert worker.acrescentar is True

        window.close()
        app.processEvents()
    print("OS019 Qt add-to-existing destination workflow and mode-reset passed")


if __name__ == "__main__":
    main()
