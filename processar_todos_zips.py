from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
import shutil
import zipfile

pasta_zips = Path("/Volumes/SEAGATE/BKP GOOGLE FOTOS")

temp = Path.home() / "Projetos/GOOGLE_FOTOS_TEMP_EXTRACAO"
destino = Path.home() / "Projetos/GOOGLE_FOTOS_ORGANIZADO"

triagem = destino / "_TRIAGEM_SEM_EXIF"
revisao_data = destino / "_REVISAO_DATA_SUSPEITA"

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

def copiar_sem_sobrescrever(origem, pasta_destino):
    pasta_destino.mkdir(parents=True, exist_ok=True)

    destino_final = pasta_destino / origem.name

    contador = 1

    while destino_final.exists():
        destino_final = pasta_destino / f"{origem.stem}_{contador}{origem.suffix}"
        contador += 1

    shutil.copy2(origem, destino_final)

for zip_path in sorted(pasta_zips.glob("*.zip")):

    print(f"\nPROCESSANDO: {zip_path.name}")

    if temp.exists():
        shutil.rmtree(temp)

    temp.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(temp)

    except Exception as e:
        print(f"ERRO ZIP: {e}")
        continue

    origem = temp / "Takeout" / "Google Fotos"

    if not origem.exists():
        print("Google Fotos não encontrado.")
        continue

    for arquivo in origem.rglob("*"):

        if arquivo.is_file() and arquivo.suffix in extensoes:

            data = pegar_data_exif(arquivo)

            if not data:
                copiar_sem_sobrescrever(arquivo, triagem)
                print(f"TRIAGEM: {arquivo.name}")
                continue

            if data.year < 2007 or data.year > 2026:
                copiar_sem_sobrescrever(arquivo, revisao_data)
                print(f"DATA SUSPEITA: {arquivo.name}")
                continue

            ano = str(data.year)
            mes = f"{data.month:02d}"

            pasta_destino = destino / ano / f"{ano}-{mes}"

            copiar_sem_sobrescrever(arquivo, pasta_destino)

            print(f"COPIADO: {arquivo.name}")

    shutil.rmtree(temp)

print("\nFINALIZADO.")
