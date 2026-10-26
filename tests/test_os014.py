"""OS014 fault-injection and integrity tests using temporary synthetic fixtures only."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3

import fluxor_core.library as library
from fluxor_core.duplicates import find_exact_duplicates
from fluxor_core.workspace import _connect, review_list, review_add


def test_index_rollback():
    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        source = base / "source"
        source.mkdir()
        (source / "one.txt").write_text("initial")
        database = base / "catalog.sqlite3"
        library.index_folder(source, database)
        before = library.catalog_summary(database)
        (source / "z.trigger").write_text("must roll back")
        original = library.classificar_arquivo
        try:
            def fail_on_second(path):
                if path.suffix == ".trigger":
                    raise RuntimeError("synthetic index failure")
                return original(path)
            library.classificar_arquivo = fail_on_second
            try:
                library.index_folder(source, database)
            except RuntimeError:
                pass
            else:
                raise AssertionError("index must propagate the synthetic failure")
        finally:
            library.classificar_arquivo = original
        assert library.catalog_summary(database) == before


def test_workspace_rollback():
    with TemporaryDirectory() as tmp:
        database = Path(tmp) / "review.sqlite3"
        review_add(database, "/synthetic/keep.txt")
        try:
            with _connect(database) as conn:
                conn.execute("INSERT INTO review_queue(path) VALUES ('/synthetic/rollback.txt')")
                raise RuntimeError("synthetic aborted write")
        except RuntimeError:
            pass
        assert review_list(database) == ["/synthetic/keep.txt"]


def test_cloud_skip_and_local_equality():
    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        source = base / "input"
        source.mkdir()
        for name in ("a.dat", "b.dat"):
            (source / name).write_bytes(b"same content")
        cloud = source / "CloudStorage"
        cloud.mkdir()
        for name in ("cloud_a.dat", "cloud_b.dat"):
            (cloud / name).write_bytes(b"another identical content")
        database = base / "catalog.sqlite3"
        library.index_folder(source, database)
        report = find_exact_duplicates(database)
        assert any(set(group["paths"]) == {str(source / "a.dat"), str(source / "b.dat")} for group in report["groups"])
        assert all("CloudStorage" not in path for group in report["groups"] for path in group["paths"])
        assert sum("CloudStorage" in item["path"] for item in report["errors"]) == 2
        assert all((source / name).read_bytes() == b"same content" for name in ("a.dat", "b.dat"))


def main():
    test_index_rollback()
    test_workspace_rollback()
    test_cloud_skip_and_local_equality()
    print("OS014 atomic index, workspace rollback and cloud policy tests passed")


if __name__ == "__main__":
    main()
