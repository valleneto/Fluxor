from pathlib import Path
from tempfile import TemporaryDirectory
from fluxor_core.library import index_folder, search_files, storage_diagnosis
from fluxor_core.duplicates import find_exact_duplicates

def main():
    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        origin = base / "source"
        origin.mkdir()
        (origin / "one.mp4").write_bytes(b"same")
        (origin / "two.mp4").write_bytes(b"same")
        (origin / "three.pdf").write_bytes(b"other-data")
        db = base / "index.db"
        index_folder(origin, db)
        data = storage_diagnosis(db)
        assert data["total"] == 3 and data["size"] == 18
        assert data["categories"][0][0] == "PDFs"
        assert len(search_files(db, extension=".mp4", min_size=4, max_size=4)) == 2
        report = find_exact_duplicates(db)
        assert len(report["groups"]) == 1
        assert report["potential_redundant_bytes"] == 4
        assert len(report["groups"][0]["paths"]) == 2
        assert not report["cancelled"]
        assert (origin / "one.mp4").read_bytes() == b"same"
        stopped = find_exact_duplicates(db, cancel=lambda: True)
        assert stopped["cancelled"] and stopped["checked"] == 0
    print("OS007 diagnostics and duplicates passed")

if __name__ == "__main__":
    main()
