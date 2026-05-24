from pathlib import Path

from fluxor_core.classifier import classificar_arquivo


def escanear_pasta(caminho_pasta):
    pasta = Path(caminho_pasta)

    if not pasta.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {pasta}")

    if not pasta.is_dir():
        raise NotADirectoryError(f"O caminho não é uma pasta: {pasta}")

    arquivos = []
    resumo = {}
    tamanho_total = 0

    for item in pasta.iterdir():
        if not item.is_file():
            continue

        categoria = classificar_arquivo(item)
        tamanho = item.stat().st_size

        arquivos.append({
            "nome": item.name,
            "caminho": str(item),
            "categoria": categoria,
            "extensao": item.suffix.lower(),
            "tamanho": tamanho,
        })

        resumo[categoria] = resumo.get(categoria, 0) + 1
        tamanho_total += tamanho

    return {
        "pasta": str(pasta),
        "total_arquivos": len(arquivos),
        "tamanho_total": tamanho_total,
        "resumo": resumo,
        "arquivos": arquivos,
    }
