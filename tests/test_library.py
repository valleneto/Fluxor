from pathlib import Path
from tempfile import TemporaryDirectory

from fluxor_core.library import index_folder, search_files, catalog_summary


def main():
    with TemporaryDirectory(prefix="fluxor_library_") as temp:
        base = Path(temp)
        root = base / "source"
        db = base / "metadata" / "library.db"
        (root / "Projeto_A").mkdir(parents=True)
        (root / "Projeto_A" / "foto.png").write_bytes(b"abc")
        (root / "Projeto_A" / "roteiro.pdf").write_bytes(b"12345")
        (root / "isolado.txt").write_bytes(b"X")
        (root / "atalho.jpg").symlink_to(root / "Projeto_A" / "foto.png")
        (root / "Fake.app").mkdir()
        (root / "Fake.app" / "hidden.pdf").write_bytes(b"ignore")

        report = index_folder(root, db)
        assert report["total"] == 3
        assert report["size"] == 9
        assert catalog_summary(db)["total"] == 3
        assert len(search_files(db, text="foto")) == 1
        assert len(search_files(db, category="PDFs")) == 1
        assert len(search_files(db, project="Projeto_A")) == 2
        assert search_files(db, project="Projeto_A")[0]["project"] == "Projeto_A"
        assert (root / "Projeto_A" / "foto.png").read_bytes() == b"abc"

        (root / "isolado.txt").unlink()
        assert index_folder(root, db)["total"] == 2
        assert len(search_files(db)) == 2
        try:
            index_folder(root, root / "index.db")
        except ValueError:
            pass
        else:
            raise AssertionError("Index within source should be rejected")
        print("BIBLIOTECA SQLITE: TESTES APROVADOS")


if __name__ == "__main__":
    main()
