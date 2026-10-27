"""Read-only-to-user-files benchmark: writes only disposable synthetic fixtures."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from fluxor_core.library import index_folder, search_files, catalog_summary


def main():
    parser = argparse.ArgumentParser(description="FLUXOR synthetic index benchmark")
    parser.add_argument("--count", type=int, default=1000)
    args = parser.parse_args()
    if not 1 <= args.count <= 100000:
        parser.error("--count must be between 1 and 100000")
    with TemporaryDirectory(prefix="fluxor-bench-") as temp:
        root = Path(temp) / "source"
        root.mkdir()
        for i in range(args.count):
            (root / f"item_{i:06d}.txt").write_text(f"synthetic {i}", encoding="utf-8")
        db = Path(temp) / "catalog.sqlite"
        begin = perf_counter()
        result = index_folder(root, db)
        elapsed = max(.001, perf_counter() - begin)
        search_start = perf_counter()
        rows = search_files(db, text="item_", limit=100)
        search_ms = (perf_counter() - search_start) * 1000
        print(f"files={result['total']} seconds={elapsed:.3f} files_per_s={result['total']/elapsed:.1f}")
        print(f"search_100_ms={search_ms:.2f} catalog_files={catalog_summary(db)['total']}")
        assert len(rows) == min(args.count, 100)


if __name__ == "__main__":
    main()
