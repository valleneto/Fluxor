"""OS024-C: regression for reentrant thumbnail cancellation (synthetic only)."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication
from fluxor_media import MediaPreview


class FakeProcess:
    def __init__(self, callback, running=True):
        self.callback = callback
        self.running = running
        self.deleted = 0
        self.killed = 0
        self.waited = 0

    def state(self):
        return (QProcess.ProcessState.Running if self.running
                else QProcess.ProcessState.NotRunning)

    def kill(self):
        self.killed += 1
        self.running = False

    def waitForFinished(self, milliseconds):
        assert milliseconds == 100
        self.waited += 1
        # Reproduce QProcess.finished emitted synchronously during the wait.
        self.callback()
        return True

    def deleteLater(self):
        self.deleted += 1


class FakeFolder:
    def __init__(self, path):
        self.name = str(path)
        self.cleaned = 0

    def cleanup(self):
        self.cleaned += 1


def main():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(prefix="fluxor-os024c-test-") as temp:
        preview = MediaPreview(embedded=True)
        folder = FakeFolder(Path(temp))
        preview.thumbnail_folder = folder
        process = FakeProcess(lambda: preview.thumbnail_ready(process, preview.generation, 0))
        preview.thumbnail_process = process
        preview.cancel_thumbnail()
        assert preview.thumbnail_process is None
        assert preview.thumbnail_folder is None
        assert process.deleted == 1 and process.killed == 1 and process.waited == 1
        assert folder.cleaned == 1
        preview.cancel_thumbnail()  # Must be idempotent.
        assert process.deleted == 1 and folder.cleaned == 1

        # Process that already finished: no kill and no wait.
        folder2 = FakeFolder(Path(temp))
        process2 = FakeProcess(lambda: None, running=False)
        preview.thumbnail_process, preview.thumbnail_folder = process2, folder2
        preview.cancel_thumbnail()
        assert process2.deleted == 1 and process2.killed == 0 and process2.waited == 0
        assert folder2.cleaned == 1
        preview.close()
        app.processEvents()
    print("OS024-C thumbnail reentrancy regression PASS")


if __name__ == "__main__":
    main()
