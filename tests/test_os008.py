"""OS008: bounded pages and safe cancel with synthetic files."""
from pathlib import Path
from tempfile import TemporaryDirectory
from fluxor_core.library import index_folder, search_files
from fluxor_core.duplicates import find_exact_duplicates

def main():
    with TemporaryDirectory() as temp:
        root = Path(temp) / "input"
        root.mkdir()
        for i in range(235):
            (root / f"sample_{i:03}.txt").write_text("value-" + str(i))
        db = Path(temp) / "index.db"
        report = index_folder(root, db)
        assert report["total"] == 235
        first = search_files(db, limit=100, offset=0, sort="name", descending=False)
        second = search_files(db, limit=100, offset=100, sort="name", descending=False)
        third = search_files(db, limit=100, offset=200, sort="name", descending=False)
        assert len(first) == len(second) == 100
        assert len(third) == 35
        assert set(x["path"] for x in first).isdisjoint(x["path"] for x in second)
        assert first[0]["name"] == "sample_000.txt"
        cancelled = find_exact_duplicates(db, cancel=lambda: True)
        assert cancelled["cancelled"] is True
        assert cancelled["groups"] == []
        assert all((root / f"sample_{i:03}.txt").exists() for i in range(235))
    print("OS008 pagination and cancellation: OK")

if __name__ == "__main__":
    main()
