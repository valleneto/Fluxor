import csv
from pathlib import Path

csv_path = Path.home() / "Projetos/INVENTARIOS/exclusivos_samsung.csv"

total_mb = 0

with open(csv_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            total_mb += float(row["tamanho_mb"])
        except:
            pass

print(f"Total aproximado: {total_mb:.2f} MB")
print(f"Total aproximado: {total_mb/1024:.2f} GB")
