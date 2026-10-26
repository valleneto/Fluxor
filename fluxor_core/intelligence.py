"""Metadata-only actionable discoveries and conservative filename version candidates."""
import re
import sqlite3
from collections import defaultdict


def normalize_version_name(name):
    stem = name.rsplit(".", 1)[0].casefold()
    stem = re.sub(r"(?i)(?:[\s._-]*(?:copy|copia|cópia|final|novo|versao|versão|v)[\s._-]*\d*|[\s._-]+\(\d+\))+$", "", stem)
    return re.sub(r"[\s._-]+", " ", stem).strip()


def version_candidates(database_path, limit=30):
    """Groups are suggestions ONLY; never assert content equality."""
    with sqlite3.connect(database_path) as con:
        rows = con.execute("SELECT path,name,extension,size,modified FROM files ORDER BY name").fetchall()
    grouped = defaultdict(list)
    for path, name, ext, size, modified in rows:
        key = (normalize_version_name(name), ext)
        if key[0]:
            grouped[key].append({"path": path, "name": name, "size": size, "modified": modified})
    candidates = [{"label": key[0], "extension": key[1], "files": items}
                  for key, items in grouped.items()
                  if len(items) > 1 and len({item["name"].casefold() for item in items}) > 1]
    return sorted(candidates, key=lambda group: (-len(group["files"]), group["label"]))[:limit]


def radar_report(database_path, limit=8):
    """Fast SQL aggregation of metadata already indexed, no file content reads."""
    with sqlite3.connect(database_path) as con:
        total, size = con.execute("SELECT COUNT(*),COALESCE(SUM(size),0) FROM files").fetchone()
        largest = con.execute("SELECT name,path,size FROM files ORDER BY size DESC LIMIT ?", (limit,)).fetchall()
        categories = con.execute("SELECT category,COUNT(*),SUM(size) FROM files GROUP BY category ORDER BY SUM(size) DESC LIMIT ?", (limit,)).fetchall()
        similar_sizes = con.execute("SELECT COUNT(*) FROM (SELECT size FROM files WHERE size > 0 GROUP BY size HAVING COUNT(*) > 1)").fetchone()[0]
    return {"total": total, "size": size, "largest": largest,
            "categories": categories, "same_size_groups_unverified": similar_sizes}
