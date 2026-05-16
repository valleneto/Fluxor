from pathlib import Path
import shutil

origem = Path.home() / "Projetos/GOOGLE_FOTOS_ORGANIZADO"
videos = origem / "_VIDEOS"

extensoes_video = [".mp4", ".mov", ".avi", ".m4v", ".MP4", ".MOV", ".AVI", ".M4V"]

def mover_sem_sobrescrever(arquivo, destino):
    destino.mkdir(parents=True, exist_ok=True)
    final = destino / arquivo.name
    contador = 1

    while final.exists():
        final = destino / f"{arquivo.stem}_{contador}{arquivo.suffix}"
        contador += 1

    shutil.move(str(arquivo), str(final))

for arquivo in origem.rglob("*"):
    if not arquivo.is_file():
        continue

    if "_VIDEOS" in str(arquivo):
        continue

    if arquivo.suffix in extensoes_video:
        mover_sem_sobrescrever(arquivo, videos)
        print(f"VIDEO: {arquivo.name}")

print("\nFINALIZADO.")
