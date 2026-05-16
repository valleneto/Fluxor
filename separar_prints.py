from pathlib import Path
import shutil

origem = Path.home() / "Projetos/GOOGLE_FOTOS_ORGANIZADO"
prints = origem / "_PRINTS"

padroes = [
    "Screenshot",
    "Captura de Tela",
    "Screen Shot",
    "IMG_",
]

extensoes_print = [".png", ".PNG"]

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

    if "_PRINTS" in str(arquivo):
        continue

    nome = arquivo.name

    eh_print = False

    for padrao in padroes:
        if padrao.lower() in nome.lower():
            eh_print = True

    if arquivo.suffix in extensoes_print and nome.startswith("IMG_"):
        eh_print = True

    if eh_print:
        mover_sem_sobrescrever(arquivo, prints)
        print(f"PRINT: {arquivo.name}")

print("\nFINALIZADO.")
