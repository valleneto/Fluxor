import sqlite3
from pathlib import Path
from datetime import datetime

db = Path("fluxor.db")
log = Path("logs/summary.txt")
log.parent.mkdir(exist_ok=True)

conn = sqlite3.connect(db)
cursor = conn.cursor()

total = cursor.execute("SELECT COUNT(*) FROM arquivos").fetchone()[0]
peso = cursor.execute("SELECT SUM(tamanho) FROM arquivos").fetchone()[0] or 0

tipos = [
    ("jpg", "%.jpg"),
    ("jpeg", "%.jpeg"),
    ("png", "%.png"),
    ("mp4", "%.mp4"),
    ("mov", "%.mov"),
    ("pdf", "%.pdf"),
    ("mp3", "%.mp3"),
]

with open(log, "w", encoding="utf-8") as f:
    f.write("FLUXOR SUMMARY\n")
    f.write(f"Gerado em: {datetime.now()}\n\n")
    f.write(f"Arquivos catalogados: {total}\n")
    f.write(f"Tamanho total: {peso/1024/1024/1024:.2f} GB\n\n")
    f.write("Por tipo:\n")

    for nome, padrao in tipos:
        qtd, soma = cursor.execute(
            "SELECT COUNT(*), SUM(tamanho) FROM arquivos WHERE lower(caminho) LIKE ?",
            (padrao,)
        ).fetchone()
        f.write(f"- {nome}: {qtd} arquivos / {(soma or 0)/1024/1024/1024:.2f} GB\n")

conn.close()

print(f"Resumo criado em: {log}")
