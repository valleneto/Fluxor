"""Exact duplicate report: size prefilter, streaming SHA-256, no deletion."""
import sqlite3
from pathlib import Path
from collections import defaultdict
from fluxor_core.plan import sha256_arquivo


def find_exact_duplicates(database_path, cancel=None, progress=None):
    with sqlite3.connect(database_path) as con:
        rows = con.execute(
            "SELECT path, size FROM files WHERE size IN "
            "(SELECT size FROM files GROUP BY size HAVING COUNT(*) > 1) "
            "ORDER BY size, path"
        ).fetchall()
    by_size = defaultdict(list)
    for path, size in rows:
        by_size[size].append(path)
    found = defaultdict(list)
    errors = []
    checked = 0
    interrupted = False
    for size, paths in by_size.items():
        for path in paths:
            if cancel and cancel():
                interrupted = True
                break
            try:
                item = Path(path)
                if item.is_symlink() or not item.is_file() or item.stat().st_size != size:
                    continue
                found[(size, sha256_arquivo(item))].append(path)
            except OSError as error:
                errors.append({"path": path, "error": str(error)})
            checked += 1
            if progress:
                progress(checked, len(rows))
        if interrupted:
            break
    groups = [
        {"size": size, "sha256": digest, "paths": files}
        for (size, digest), files in found.items() if len(files) > 1
    ]
    groups.sort(key=lambda group: group["size"] * (len(group["paths"]) - 1), reverse=True)
    return {
        "groups": groups,
        "candidates": len(rows),
        "checked": checked,
        "cancelled": interrupted,
        "errors": errors,
        "potential_redundant_bytes": sum(
            x["size"] * (len(x["paths"]) - 1) for x in groups
        ),
    }
