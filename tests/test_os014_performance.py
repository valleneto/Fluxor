"""OS014 catalog scale smoke, synthetic metadata only (no user file access)."""
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
import sqlite3

from fluxor_core.library import SCHEMA, search_files, catalog_summary
from fluxor_core.intelligence import radar_report


def main():
    with TemporaryDirectory() as tmp:
        db = Path(tmp) / "catalog.sqlite3"
        with sqlite3.connect(db) as conn:
            conn.executescript(SCHEMA)
            conn.executemany(
                "INSERT INTO files VALUES (?,?,?,?,?,?,?,?)",
                [(
                    f"/synthetic/p{index % 20}/asset_{index:05d}.mp4",
                    "/synthetic", f"asset_{index:05d}.mp4", "Vídeos", ".mp4",
                    (index % 1000 + 1) * 10000, 1690000000.0 + index,
                    f"p{index % 20}",
                )
                for index in range(50000)]
            )
        start = perf_counter()
        times = []
        for number in range(20):
            tick = perf_counter()
            rows = search_files(db, text=f"asset_{number}", limit=101, sort="size")
            assert isinstance(rows, list)
            times.append(perf_counter() - tick)
        summary = catalog_summary(db)
        report = radar_report(db)
        assert summary["total"] == report["total"] == 50000
        assert report["size"] > 0
        times.sort()
        print(f"OS014 synthetic 50k catalog: p95 search={times[18]*1000:.1f}ms, total={perf_counter()-start:.2f}s")


if __name__ == "__main__":
    main()
