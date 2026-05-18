import sqlite3

conn = sqlite3.connect("fluxor.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS arquivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caminho TEXT UNIQUE,
    hash TEXT,
    tamanho INTEGER,
    modificado_em REAL,
    escaneado_em REAL
)
""")

conn.commit()
conn.close()

print("Banco Fluxor criado.")
