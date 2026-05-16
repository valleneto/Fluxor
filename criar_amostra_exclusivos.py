import csv
import shutil
from pathlib import Path

csv_path = Path.home() / "Projetos/INVENTARIOS/exclusivos_samsung.csv"
destino = Path.home() / "Projetos/AMOSTRA_EXCLUSIVOS_SAMSUNG"

limite = 300
copiados = 0

with open(csv_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if copiados >= limite:
            break

        caminho = Path(row["caminho"])

        if caminho.exists() and caminho.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            final = destino / caminho.name
            contador = 1

            while final.exists():
                final = destino / f"{caminho.stem}_{contador}{caminho.suffix}"
                contador += 1

            shutil.copy2(caminho, final)
            copiados += 1

print(f"Amostra criada com {copiados} imagens em: {destino}")
