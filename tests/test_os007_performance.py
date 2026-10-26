"""Small repeatable performance smoke test with synthetic SQLite data."""
import sqlite3
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from fluxor_core.library import SCHEMA, search_files, storage_diagnosis


def main():
    with TemporaryDirectory() as tmp:
        db = Path(tmp) / "benchmark.db"
        with sqlite3.connect(db) as con:
            con.executescript(SCHEMA)
            con.executemany(
                "INSERT INTO files VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ((f"/synthetic/{i}.mp4", "/synthetic", f"{i}.mp4", "Videos",
                  ".mp4", i * 1024, float(i), "Sem projeto") for i in range(10000))
            )
        started = time.perf_counter()
        for _ in range(20):
            assert len(search_files(db, category="Videos", limit=100)) == 100
        query_seconds = time.perf_counter() - started
        started = time.perf_counter()
        result = storage_diagnosis(db)
        diagnosis_seconds = time.perf_counter() - started
        assert result["total"] == 10000
        print(f"10000 synthetic records: 20 searches={query_seconds:.3f}s; diagnosis={diagnosis_seconds:.3f}s")
        # Measurements only: shared CI runners have variable performance.


if __name__ == "__main__":
    main()
