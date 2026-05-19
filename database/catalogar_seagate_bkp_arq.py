import sqlite3
import time
from pathlib import Path

origem = Path("/Volumes/SEAGATE/BKP_ARQ")

conn = sqlite3.connect("fluxor.db")
cursor = conn.cursor()

contador = 0
novos = 0
ignorados = 0

for arquivo in origem.rglob("*"):
    if not arquivo.is_file():
        continue

    try:
        stat = arquivo.stat()
        caminho = str(arquivo)

        cursor.execute("SELECT tamanho, modificado_em FROM arquivos WHERE caminho = ?", (caminho,))
        existente = cursor.fetchone()

        if existente and existente[0] == stat.st_size and existente[1] == stat.st_mtime:
            ignorados += 1
        else:
            cursor.execute("""
            INSERT OR REPLACE INTO arquivos (
                caminho, tamanho, modificado_em, escaneado_em
            )
            VALUES (?, ?, ?, ?)
            """, (
                caminho,
                stat.st_size,
                stat.st_mtime,
                time.time()
            ))
            novos += 1

        contador += 1

        if contador % 500 == 0:
            conn.commit()
            print(f"{contador} verificados | {novos} novos/atualizados | {ignorados} ignorados")
            time.sleep(2)

    except Exception as e:
        continue

conn.commit()
conn.close()

print("\nFINALIZADO.")
print(f"Total verificado: {contador}")
print(f"Novos/atualizados: {novos}")
print(f"Ignorados: {ignorados}")
