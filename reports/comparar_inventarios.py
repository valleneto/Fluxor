import csv
from pathlib import Path

base = Path.home() / "Projetos/INVENTARIOS"

samsung_csv = base / "fotos_samsung.csv"
google_csv = base / "google_organizado.csv"

saida = base / "exclusivos_samsung.csv"

hashes_google = set()

with open(google_csv, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        hashes_google.add(row["hash"])

exclusivos = []

with open(samsung_csv, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["hash"] not in hashes_google and row["hash"] != "ERRO_HASH":
            exclusivos.append(row)

with open(saida, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["arquivo", "tamanho_mb", "hash", "caminho"])
    writer.writeheader()
    writer.writerows(exclusivos)

print(f"Arquivos exclusivos no SAMSUNG: {len(exclusivos)}")
print(f"Relatório criado em: {saida}")
