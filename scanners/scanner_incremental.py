import sqlite3
import time
from pathlib import Path

ORIGEM = Path("/Volumes/SAMSUNG/NETO/FOTOS")

conn = sqlite3.connect("fluxor.db")
cursor = conn.cursor()

novos = 0
ignorados = 0

for arquivo in ORIGEM.rglob("*"):

    if not arquivo.is_file():
        continue

    try:

        stat = arquivo.stat()

        caminho = str(arquivo)
        tamanho = stat.st_size
        modificado = stat.st_mtime

        cursor.execute("""
        SELECT tamanho, modificado_em
        FROM arquivos
        WHERE caminho = ?
        """, (caminho,))

        resultado = cursor.fetchone()

        if resultado:

            tamanho_db, modificado_db = resultado

            if tamanho_db == tamanho and modificado_db == modificado:

                ignorados += 1
                continue

        cursor.execute("""
        INSERT OR REPLACE INTO arquivos (
            caminho,
            tamanho,
            modificado_em,
            escaneado_em
        )
        VALUES (?, ?, ?, ?)
        """, (
            caminho,
            tamanho,
            modificado,
            time.time()
        ))

        novos += 1

        if novos % 200 == 0:

            conn.commit()

            print(f"{novos} arquivos atualizados...")

            time.sleep(1)

    except Exception:
        continue

conn.commit()
conn.close()

print(f"\nNovos/modificados: {novos}")
print(f"Ignorados: {ignorados}")
