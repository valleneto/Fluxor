from pathlib import Path
from datetime import datetime
import shutil
import zipfile
import re

pasta_zips = Path("/Volumes/SEAGATE/BKP GOOGLE FOTOS")
temp = Path.home() / "Projetos/GOOGLE_FOTOS_TEMP_EXTRACAO_VIDEO"
destino = Path.home() / "Projetos/GOOGLE_FOTOS_ORGANIZADO/_VIDEOS"
triagem = destino / "_TRIAGEM_VIDEO_SEM_DATA"

extensoes = [".mp4", ".mov", ".m4v", ".avi", ".MP4", ".MOV", ".M4V", ".AVI"]

def data_pelo_nome(nome):
    m = re.search(r'(20\d{6})[_-]?(\d{6})?', nome)
    if not m:
        return None
    data_txt = m.group(1)
    hora_txt = m.group(2) or "000000"
    try:
        return datetime.strptime(data_txt + hora_txt[:6], "%Y%m%d%H%M%S")
    except Exception:
        return None

def copiar_sem_sobrescrever(origem, pasta_destino):
    pasta_destino.mkdir(parents=True, exist_ok=True)
    final = pasta_destino / origem.name
    contador = 1
    while final.exists():
        final = pasta_destino / f"{origem.stem}_{contador}{origem.suffix}"
        contador += 1
    shutil.copy2(origem, final)

for zip_path in sorted(pasta_zips.glob("*.zip")):
    print(f"\nPROCESSANDO VÍDEOS: {zip_path.name}")

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
        continue

    for arquivo in origem.rglob("*"):
        if arquivo.is_file() and arquivo.suffix in extensoes:
            data = data_pelo_nome(arquivo.name)

            if data:
                ano = str(data.year)
                mes = f"{data.month:02d}"
                pasta_destino = destino / ano / f"{ano}-{mes}"
                copiar_sem_sobrescrever(arquivo, pasta_destino)
                print(f"VIDEO: {arquivo.name}")
            else:
                copiar_sem_sobrescrever(arquivo, triagem)
                print(f"TRIAGEM VIDEO: {arquivo.name}")

    shutil.rmtree(temp)

print("\nFINALIZADO.")
