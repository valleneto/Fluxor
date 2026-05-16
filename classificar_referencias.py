from pathlib import Path
from PIL import Image
import shutil

origem = Path("/Volumes/SAMSUNG/NETO/FOTOS")
destino = Path.home() / "Projetos/_REFERENCIAS_INTERNET"

extensoes = [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]

limite_largura = 900
limite_altura = 900

def copiar_sem_sobrescrever(origem_arquivo, pasta_destino):
    pasta_destino.mkdir(parents=True, exist_ok=True)

    final = pasta_destino / origem_arquivo.name
    contador = 1

    while final.exists():
        final = pasta_destino / f"{origem_arquivo.stem}_{contador}{origem_arquivo.suffix}"
        contador += 1

    shutil.copy2(origem_arquivo, final)

contador = 0

for arquivo in origem.rglob("*"):

    if not arquivo.is_file():
        continue

    if arquivo.suffix not in extensoes:
        continue

    try:
        with Image.open(arquivo) as img:

            largura, altura = img.size

            if largura < limite_largura or altura < limite_altura:

                copiar_sem_sobrescrever(arquivo, destino)

                contador += 1

                print(f"REFERENCIA: {arquivo.name} ({largura}x{altura})")

    except:
        continue

print(f"\nFINALIZADO. {contador} imagens suspeitas copiadas.")
