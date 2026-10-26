"""Read-only SQLite catalog for user-selected folders.

The database stores metadata and paths, never file contents.
"""
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from fluxor_core.classifier import classificar_arquivo


SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    root TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    extension TEXT NOT NULL,
    size INTEGER NOT NULL,
    modified REAL NOT NULL,
    project TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_files_name ON files(name);
CREATE INDEX IF NOT EXISTS idx_files_category ON files(category);
CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified);
CREATE INDEX IF NOT EXISTS idx_files_size ON files(size);
CREATE INDEX IF NOT EXISTS idx_files_project ON files(project);
"""


def suggest_project(relative_path):
    """A conservative suggestion, based on an existing parent folder."""
    parent = relative_path.parent
    if str(parent) in ("", "."):
        return "Sem projeto"
    return parent.parts[0]


def index_folder(root, database_path, recursive=True):
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("A origem deve ser uma pasta existente.")
    database_path = Path(database_path).expanduser().resolve()
    # Refuse to create the database inside the indexed source.
    if database_path == root or root in database_path.parents:
        raise ValueError("O banco da biblioteca precisa ficar fora da origem.")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    warnings = []
    indexed = 0
    bytes_total = 0
    batch = []
    with closing(sqlite3.connect(database_path)) as con:
        con.executescript(SCHEMA)
        with con:
            con.execute("DELETE FROM files WHERE root=?", (str(root),))
            for folder, subdirs, names in os.walk(root, followlinks=False):
                subdirs[:] = sorted(
                    name for name in subdirs
                    if not (Path(folder) / name).is_symlink()
                    and not name.lower().endswith((".app", ".bundle", ".photoslibrary", ".pkg"))
                ) if recursive else []
                for name in sorted(names):
                    item = Path(folder) / name
                    if item.is_symlink() or not item.is_file():
                        continue
                    try:
                        info = item.stat()
                        relative = item.relative_to(root)
                        record = (
                            str(item), str(root), item.name,
                            classificar_arquivo(item), item.suffix.lower(),
                            info.st_size, info.st_mtime, suggest_project(relative),
                        )
                        batch.append(record)
                        indexed += 1
                        bytes_total += info.st_size
                        if len(batch) >= 500:
                            con.executemany('INSERT OR REPLACE INTO files VALUES (?,?,?,?,?,?,?,?)', batch)
                            batch.clear()
                    except OSError as error:
                        warnings.append(f"{item}: {error}")

            if batch:
                con.executemany('INSERT OR REPLACE INTO files VALUES (?,?,?,?,?,?,?,?)', batch)
    return {"total": indexed, "size": bytes_total, "warnings": warnings,
            "database": str(database_path)}


def search_files(database_path, text="", category=None, project=None, limit=500, extension=None, min_size=None, max_size=None, offset=0, sort='modified', descending=True):
    limit = max(1, min(int(limit), 5000))
    clauses = []
    params = []
    if text:
        clauses.append("instr(lower(name), lower(?)) > 0")
        params.append(text)
    if category:
        clauses.append("category = ?")
        params.append(category)
    if project:
        clauses.append("project = ?")
        params.append(project)
    if extension:
        clauses.append("extension = ?")
        params.append(extension.lower())
    if min_size is not None:
        clauses.append("size >= ?")
        params.append(int(min_size))
    if max_size is not None:
        clauses.append("size <= ?")
        params.append(int(max_size))
    query = ("SELECT path, name, category, extension, size, modified, project "
             "FROM files")
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    order = {'name':'name COLLATE NOCASE', 'size':'size', 'modified':'modified', 'category':'category COLLATE NOCASE'}.get(sort, 'modified')
    query += ' ORDER BY ' + order + (' DESC' if descending else ' ASC') + ', path LIMIT ? OFFSET ?'
    params.extend((limit, max(0, int(offset))))
    with sqlite3.connect(database_path) as con:
        rows = con.execute(query, params).fetchall()
    return [dict(zip(("path", "name", "category", "extension", "size", "modified", "project"), row))
            for row in rows]


def catalog_summary(database_path):
    with sqlite3.connect(database_path) as con:
        total, size = con.execute("SELECT COUNT(*), COALESCE(SUM(size), 0) FROM files").fetchone()
        categories = con.execute(
            "SELECT category, COUNT(*) FROM files GROUP BY category ORDER BY COUNT(*) DESC"
        ).fetchall()
        projects = con.execute(
            "SELECT project, COUNT(*) FROM files WHERE project != 'Sem projeto' "
            "GROUP BY project ORDER BY COUNT(*) DESC LIMIT 10"
        ).fetchall()
    return {"total": total, "size": size, "categories": categories, "projects": projects}


def storage_diagnosis(database_path, limit=10):
    """Metadata-only diagnostics, no file reads."""
    with sqlite3.connect(database_path) as con:
        total, size = con.execute("SELECT COUNT(*), COALESCE(SUM(size),0) FROM files").fetchone()
        categories = con.execute(
            "SELECT category, COUNT(*), SUM(size) FROM files "
            "GROUP BY category ORDER BY SUM(size) DESC"
        ).fetchall()
        largest = con.execute(
            "SELECT path, name, size FROM files ORDER BY size DESC LIMIT ?",
            (max(1, min(int(limit), 100)),)
        ).fetchall()
    return {"total": total, "size": size, "categories": categories, "largest": largest}
