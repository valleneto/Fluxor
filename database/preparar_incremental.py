import sqlite3
import time
from pathlib import Path
import os

origem = Path("/Volumes/SAMSUNG/NETO/FOTOS")

conn = sqlite3.connect("fluxor.db")
cursor = conn.cursor()

contador = 0

for arquivo in origem.rglob("*"):

    if not arquivo.is_file():
        continue

    try:
        stat = arquivo.stat()

        cursor.execute("""
        INSERT OR IGNORE INTO arquivos (
            caminho,
            tamanho,
            modificado_em,
            escaneado_em
        )
        VALUES (?, ?, ?, ?)
        """, (
            str(arquivo),
            stat.st_size,
            stat.st_mtime,
            time.time()
        ))

        contador += 1

        if contador % 500 == 0:

            conn.commit()

            print(f"{contador} arquivos catalogados...")

            time.sleep(2)

    except Exception:
        continue

conn.commit()
conn.close()

print(f"\nFINALIZADO: {contador} arquivos catalogados.")
