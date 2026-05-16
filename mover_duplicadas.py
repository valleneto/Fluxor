from pathlib import Path
import hashlib
import shutil

pasta = Path.home() / "Projetos/google-fotos-lab/ORGANIZADO_TESTE"
destino = pasta / "_DUPLICADAS_REVISAR"

hashes = {}
movidas = 0

def hash_arquivo(caminho):
    sha = hashlib.sha256()
    with open(caminho, "rb") as f:
        while True:
            bloco = f.read(1024 * 1024)
            if not bloco:
                break
            sha.update(bloco)
    return sha.hexdigest()

def mover_sem_sobrescrever(arquivo, destino_pasta):
    destino_pasta.mkdir(parents=True, exist_ok=True)
    destino_final = destino_pasta / arquivo.name

    contador = 1
    while destino_final.exists():
        destino_final = destino_pasta / f"{arquivo.stem}_{contador}{arquivo.suffix}"
        contador += 1

    shutil.move(str(arquivo), str(destino_final))

for arquivo in pasta.rglob("*"):
    if arquivo.is_file() and "_DUPLICADAS_REVISAR" not in str(arquivo):
        h = hash_arquivo(arquivo)

        if h in hashes:
            mover_sem_sobrescrever(arquivo, destino)
            movidas += 1
        else:
            hashes[h] = arquivo

print(f"Duplicadas movidas para revisão: {movidas}")
