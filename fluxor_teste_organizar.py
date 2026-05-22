from pathlib import Path
import shutil
import time

print("\nFLUXOR — TESTE DE ORGANIZAÇÃO SEGURA\n")

origem_txt = input("Pasta de origem: ").strip()
destino_txt = input("Pasta de destino: ").strip()

origem = Path(origem_txt)
destino_base = Path(destino_txt) / "Fluxor_Organizado_Teste"

LIMITE = 300

categorias = {
    "Fotos": [".jpg", ".jpeg", ".png", ".heic", ".webp"],
    "Videos": [".mp4", ".mov", ".avi", ".m4v", ".mkv"],
    "Audio": [".mp3", ".wav", ".aiff", ".flac", ".m4a"],
    "Documentos": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".xls", ".xlsx"],
}

def categoria_do_arquivo(arquivo):
    ext = arquivo.suffix.lower()

    for categoria, exts in categorias.items():
        if ext in exts:
            return categoria

    return "Outros"

def copiar_sem_sobrescrever(origem_arquivo, pasta_destino):

    pasta_destino.mkdir(parents=True, exist_ok=True)

    final = pasta_destino / origem_arquivo.name

    contador = 1

    while final.exists():

        final = (
            pasta_destino /
            f"{origem_arquivo.stem}_{contador}{origem_arquivo.suffix}"
        )

        contador += 1

    shutil.copy2(origem_arquivo, final)

    if origem_arquivo.stat().st_size != final.stat().st_size:

        raise Exception(
            f"Falha validação: {origem_arquivo.name}"
        )

    return final

if not origem.exists():

    print("ERRO: origem não existe.")
    raise SystemExit

destino_base.mkdir(parents=True, exist_ok=True)

arquivos = [
    f for f in origem.rglob("*")
    if f.is_file()
]

arquivos = arquivos[:LIMITE]

print(f"\nArquivos encontrados: {len(arquivos)}")
print(f"Destino: {destino_base}\n")

inicio = time.time()

copiados = 0
erros = 0

for i, arquivo in enumerate(arquivos, start=1):

    try:

        categoria = categoria_do_arquivo(arquivo)

        pasta_destino = destino_base / categoria

        copiar_sem_sobrescrever(
            arquivo,
            pasta_destino
        )

        copiados += 1

        print(
            f"[{i}/{len(arquivos)}] "
            f"OK → {categoria}: {arquivo.name}"
        )

    except Exception as e:

        erros += 1

        print(
            f"[{i}/{len(arquivos)}] "
            f"ERRO → {arquivo.name}: {e}"
        )

duracao = round(time.time() - inicio, 2)

print("\nFINALIZADO")
print(f"Copiados: {copiados}")
print(f"Erros: {erros}")
print(f"Duração: {duracao}s")
print(f"Pasta criada em: {destino_base}")
