"""OS025-C: NTFS junction/reparse/volume safety. Synthetic temporary files only."""
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from fluxor_core.windows_safety import require_local_ntfs, reject_windows_reparse
from fluxor_core.plan import planejar, executar_plano
from fluxor_core.library import index_folder
from fluxor_core.atomic_copy import copy_verified


def must_block(fn, title):
    try:
        fn()
    except (OSError, ValueError) as error:
        print("BLOCKED", title, str(error)[:180], flush=True)
        return
    raise AssertionError("Failed to block unsafe path: " + title)


def junction(target, link):
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                            check=False, capture_output=True, text=True)
    if result.returncode != 0 or not link.exists():
        raise RuntimeError("Junction fixture unavailable: " + result.stderr)
    reject = link.lstat().st_file_attributes
    assert reject & 0x400, "Junction fixture does not have reparse attribute"


def main():
    assert os.name == "nt", "Run only in Windows gated CI"
    with TemporaryDirectory(prefix="fluxor-os025c-junction-") as folder:
        root = Path(folder).resolve()
        require_local_ntfs(root)
        must_block(lambda: require_local_ntfs(r"\\server\not-connected\files"),
                   "UNC must not connect")

        original = root / "original"
        original.mkdir()
        (original / "protected.txt").write_bytes(b"never-read-via-junction")
        alias = root / "alias"
        junction(original, alias)
        must_block(lambda: reject_windows_reparse(alias / "protected.txt"),
                   "reparse path component")
        must_block(lambda: planejar(alias, root / "output"),
                   "source root junction")
        must_block(lambda: index_folder(alias, root / "catalog.db"),
                   "library root junction")

        source = root / "source"
        source.mkdir()
        (source / "photo.jpg").write_bytes(b"safe-original")
        junction(original, source / "linked")
        out = root / "destination"
        out.mkdir()
        plan = planejar(source, out)
        assert not plan["completa"] and plan["bloqueios"], plan
        must_block(lambda: executar_plano(plan),
                   "incomplete preview must not copy")
        assert (source / "photo.jpg").read_bytes() == b"safe-original"
        assert (original / "protected.txt").read_bytes() == b"never-read-via-junction"
        assert not (out / "Fluxor_Organizado").exists()
        must_block(lambda: index_folder(source, root / "catalog2.db"),
                   "nested junction in indexed root")

        # Direct atomic copy cannot use a source under a reparse component.
        collection = root / "other" / "Fluxor_Organizado"
        category = collection / "Textos"
        category.mkdir(parents=True)
        other = alias / "protected.txt"
        must_block(lambda: copy_verified(
            collection, other, category, other.name, other.stat(), "Por tipo"
        ), "source for direct copy")
        assert not (category / "protected.txt").exists()

    print("OS025-C NTFS junction, UNC and fail-closed probes PASS", flush=True)


if __name__ == "__main__":
    main()
