from pathlib import Path
import hashlib

pasta = Path.home() / "Projetos/google-fotos-lab/ORGANIZADO_TESTE"
relatorio = Path.home() / "Projetos/google-fotos-lab/duplicadas_relatorio.txt"

hashes = {}
duplicadas = []

def hash_arquivo(caminho):
    sha = hashlib.sha256()
    with open(caminho, "rb") as f:
        while True:
            bloco = f.read(1024 * 1024)
            if not bloco:
                break
            sha.update(bloco)
    return sha.hexdigest()

for arquivo in pasta.rglob("*"):
    if arquivo.is_file():
        try:
            h = hash_arquivo(arquivo)
            if h in hashes:
                duplicadas.append((arquivo, hashes[h]))
            else:
                hashes[h] = arquivo
        except Exception as e:
            print(f"ERRO: {arquivo} -> {e}")

with open(relatorio, "w", encoding="utf-8") as f:
    f.write("RELATÓRIO DE DUPLICADAS EXATAS\n\n")
    f.write(f"Pasta analisada: {pasta}\n")
    f.write(f"Arquivos únicos: {len(hashes)}\n")
    f.write(f"Duplicadas encontradas: {len(duplicadas)}\n\n")

    for dup, original in duplicadas:
        f.write(f"DUPLICADA: {dup}\n")
        f.write(f"ORIGINAL : {original}\n")
        f.write("-" * 80 + "\n")

print(f"Relatório criado em: {relatorio}")
print(f"Duplicadas encontradas: {len(duplicadas)}")
