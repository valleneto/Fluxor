"""Persistent, non-destructive review queue and user-defined virtual collections."""
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS review_queue(
 path TEXT PRIMARY KEY, added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS collections(
 name TEXT PRIMARY KEY COLLATE NOCASE
);
CREATE TABLE IF NOT EXISTS collection_items(
 collection TEXT NOT NULL, path TEXT NOT NULL,
 PRIMARY KEY(collection,path),
 FOREIGN KEY(collection) REFERENCES collections(name) ON DELETE CASCADE
);
"""

def _connect(database):
    path = Path(database).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    return conn

def review_add(database, path):
    with _connect(database) as conn:
        conn.execute("INSERT OR IGNORE INTO review_queue(path) VALUES (?)", (str(path),))

def review_remove(database, path):
    with _connect(database) as conn:
        conn.execute("DELETE FROM review_queue WHERE path=?", (str(path),))

def review_list(database, limit=500):
    with _connect(database) as conn:
        return [r[0] for r in conn.execute("SELECT path FROM review_queue ORDER BY added_at DESC,path LIMIT ?",(min(5000,max(1,int(limit))),))]

def collection_add(database, name, paths=()):
    name = name.strip()
    if not name or len(name)>100:
        raise ValueError("Nome de coleção inválido.")
    with _connect(database) as conn:
        conn.execute("INSERT OR IGNORE INTO collections(name) VALUES (?)",(name,))
        conn.executemany("INSERT OR IGNORE INTO collection_items(collection,path) VALUES (?,?)",((name,str(path)) for path in paths))

def collection_list(database):
    with _connect(database) as conn:
        return conn.execute("SELECT c.name,COUNT(i.path) FROM collections c LEFT JOIN collection_items i ON c.name=i.collection GROUP BY c.name ORDER BY c.name").fetchall()

def collection_paths(database, name):
    with _connect(database) as conn:
        return [r[0] for r in conn.execute("SELECT path FROM collection_items WHERE collection=? ORDER BY path",(name,))]
