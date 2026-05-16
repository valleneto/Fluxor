import csv
from pathlib import Path

csv_path = Path.home() / "Projetos/INVENTARIOS/exclusivos_samsung.csv"

video_ext = (".mp4", ".mov", ".avi", ".m4v")
imagem_ext = (".jpg", ".jpeg", ".png")

total_video = 0
total_imagem = 0
qtd_video = 0
qtd_imagem = 0

with open(csv_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        nome = row["arquivo"].lower()
        try:
            tamanho = float(row["tamanho_mb"])
        except:
            tamanho = 0

        if nome.endswith(video_ext):
            total_video += tamanho
            qtd_video += 1
        elif nome.endswith(imagem_ext):
            total_imagem += tamanho
            qtd_imagem += 1

print(f"Imagens: {qtd_imagem} arquivos / {total_imagem/1024:.2f} GB")
print(f"Vídeos: {qtd_video} arquivos / {total_video/1024:.2f} GB")
