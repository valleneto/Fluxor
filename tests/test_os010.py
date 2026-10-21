from pathlib import Path
from tempfile import TemporaryDirectory
from fluxor_core.library import index_folder
from fluxor_core.intelligence import radar_report, version_candidates, normalize_version_name

def main():
    assert normalize_version_name("projeto_final_v2.mp4") == "projeto"
    with TemporaryDirectory() as temp:
        root = Path(temp) / "source"
        root.mkdir()
        for name, data in [("projeto.mp4",b"aaa"),("projeto_final_v2.mp4",b"bbb"),("outro.pdf",b"xx")]:
            (root / name).write_bytes(data)
        db = Path(temp) / "library.db"
        index_folder(root, db)
        radar = radar_report(db)
        assert radar["total"] == 3 and radar["size"] == 8
        assert radar["same_size_groups_unverified"] == 1
        groups = version_candidates(db)
        assert len(groups) == 1 and len(groups[0]["files"]) == 2
        assert all((root / n).exists() for n in ["projeto.mp4","projeto_final_v2.mp4","outro.pdf"])
    print("OS010 Radar and Versions passed")

if __name__ == "__main__":
    main()
