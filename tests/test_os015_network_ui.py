"""OS015 regressions: failures on network shares must not corrupt a catalog.

All fixtures are synthetic and temporary. GUI layouts are syntax-checked
without importing a native Qt runtime.
"""
import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fluxor_core.library import index_folder, catalog_summary
from fluxor_core.plan import planejar


BASE = Path(__file__).resolve().parents[1]


def _interrupted_walk(*args, **kwargs):
    yield (str(args[0]), [], ["keep.txt"])
    kwargs["onerror"](OSError("synthetic SMB disconnect"))


def test_index_network_failure_rollback():
    with TemporaryDirectory() as temp:
        root = Path(temp) / "source"
        root.mkdir()
        (root / "keep.txt").write_text("synthetic", encoding="utf-8")
        database = Path(temp) / "catalog.db"
        index_folder(root, database)
        before = catalog_summary(database)
        try:
            with patch("fluxor_core.library.os.walk", side_effect=_interrupted_walk):
                index_folder(root, database)
        except OSError as error:
            assert "SMB disconnect" in str(error)
        else:
            raise AssertionError("Disconnected share must fail the scan.")
        assert catalog_summary(database) == before


def test_preview_network_failure():
    with TemporaryDirectory() as temp:
        root = Path(temp) / "source"
        dest = Path(temp) / "output"
        root.mkdir()
        dest.mkdir()
        (root / "keep.txt").write_text("synthetic", encoding="utf-8")
        try:
            with patch("fluxor_core.plan.os.walk", side_effect=_interrupted_walk):
                planejar(root, dest)
        except OSError as error:
            assert "SMB disconnect" in str(error)
        else:
            raise AssertionError("Incomplete preview must not be accepted.")
        assert list(dest.iterdir()) == []


def test_gui_source_syntax_and_contracts():
    for relative in ("fluxor_iniciar.py", "fluxor_zen.py",
                     "fluxor_network.py", "fluxor_biblioteca.py",
                     "fluxor_app_integrado.py"):
        ast.parse((BASE / relative).read_text(encoding="utf-8"))
    home = (BASE / "fluxor_iniciar.py").read_text(encoding="utf-8")
    assert "QScrollArea" in home and "def resizeEvent" in home
    assert "QGridLayout" in home and "self.action_grid" in home
    network = (BASE / "fluxor_network.py").read_text(encoding="utf-8")
    assert '"/Volumes"' in network and 'parsed.scheme.lower() != "smb"' in network
    animation = (BASE / "fluxor_zen.py").read_text(encoding="utf-8")
    assert "QPainter" in animation and "set_reduced_motion" in animation
    assert "QMovie" not in animation and "QWebEngine" not in animation


def main():
    test_index_network_failure_rollback()
    test_preview_network_failure()
    test_gui_source_syntax_and_contracts()
    print("OS015 network rollback, preview and GUI syntax contracts passed")


if __name__ == "__main__":
    main()
