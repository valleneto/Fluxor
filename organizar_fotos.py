from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import shutil
from datetime import datetime

origem = Path.home() / "Projetos/google-fotos-lab/Takeout/Google Fotos"
destino = Path.home() / "Projetos/google-fotos-lab/ORGANIZADO_TESTE"
triagem = destino / "_TRIAGEM_SEM_EXIF"

extensoes = [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]

def pegar_data_exif(caminho):
    try:
        imagem = Image.open(caminho)
        exif = imagem._getexif()

        if not exif:
            return None

        for tag_id, valor in exif.items():
            tag = TAGS.get(tag_id, tag_id)

            if tag == "DateTimeOriginal":
                return datetime.strptime(valor, "%Y:%m:%d %H:%M:%S")

    except Exception:
        return None

    return None

def copiar_sem_sobrescrever(origem_arquivo, destino_pasta):
    destino_pasta.mkdir(parents=True, exist_ok=True)
    destino_arquivo = destino_pasta / origem_arquivo.name

    contador = 1
    while destino_arquivo.exists():
        destino_arquivo = destino_pasta / f"{origem_arquivo.stem}_{contador}{origem_arquivo.suffix}"
        contador += 1

    shutil.copy2(origem_arquivo, destino_arquivo)

for arquivo in origem.rglob("*"):
    if arquivo.suffix in extensoes:

        data = pegar_data_exif(arquivo)

        if data:
            ano = str(data.year)
            mes = f"{data.month:02d}"
            pasta_destino = destino / ano / f"{ano}-{mes}"

            copiar_sem_sobrescrever(arquivo, pasta_destino)
            print(f"COPIADO: {arquivo.name}")

        else:
            copiar_sem_sobrescrever(arquivo, triagem)
            print(f"TRIAGEM: {arquivo.name}")
