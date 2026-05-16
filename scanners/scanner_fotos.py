from pathlib import Path
import hashlib
import csv
import os

origem = Path("/Volumes/SAMSUNG/NETO/FOTOS")
saida = Path.home() / "Projetos/INVENTARIOS/fotos_samsung.csv"

extensoes = [
    ".jpg", ".jpeg", ".png",
    ".mp4", ".mov", ".avi", ".m4v",
    ".JPG", ".JPEG", ".PNG",
    ".MP4", ".MOV", ".AVI", ".M4V"
]

def gerar_hash(arquivo):
    sha = hashlib.sha256()

    try:
        with open(arquivo, "rb") as f:
            while True:
                bloco = f.read(1024 * 1024)

                if not bloco:
                    break

                sha.update(bloco)

        return sha.hexdigest()

    except Exception:
        return "ERRO_HASH"

with open(saida, "w", newline="", encoding="utf-8") as csvfile:

    writer = csv.writer(csvfile)

    writer.writerow([
        "arquivo",
        "tamanho_mb",
        "hash",
        "caminho"
    ])

    for arquivo in origem.rglob("*"):

        if arquivo.is_file() and arquivo.suffix in extensoes:

            try:
                tamanho = round(os.path.getsize(arquivo) / (1024 * 1024), 2)

                h = gerar_hash(arquivo)

                writer.writerow([
                    arquivo.name,
                    tamanho,
                    h,
                    str(arquivo)
                ])

                print(f"SCAN: {arquivo.name}")

            except Exception as e:

                print(f"ERRO: {arquivo}")

print("\nINVENTÁRIO FINALIZADO.")
