from pathlib import Path
import shutil

from fluxor_core.classifier import classificar_arquivo


def criar_destino_seguro(pasta_destino, nome_arquivo):
    destino = Path(pasta_destino) / nome_arquivo

    if not destino.exists():
        return destino

    contador = 1
    nome_base = destino.stem
    extensao = destino.suffix

    while destino.exists():
        novo_nome = f"{nome_base} ({contador}){extensao}"
        destino = Path(pasta_destino) / novo_nome
        contador += 1

    return destino


def organizar_por_tipo(pasta_origem, pasta_destino):
    origem = Path(pasta_origem)
    destino_base = Path(pasta_destino) / "Fluxor_Organizado"

    if not origem.exists():
        raise FileNotFoundError(f"Pasta de origem não encontrada: {origem}")

    if not origem.is_dir():
        raise NotADirectoryError(f"Origem não é uma pasta: {origem}")

    destino_base.mkdir(parents=True, exist_ok=True)

    relatorio = []

    for item in origem.iterdir():
        if not item.is_file():
            continue

        categoria = classificar_arquivo(item)
        pasta_categoria = destino_base / categoria
        pasta_categoria.mkdir(parents=True, exist_ok=True)

        destino_arquivo = criar_destino_seguro(pasta_categoria, item.name)

        shutil.copy2(item, destino_arquivo)

        relatorio.append({
            "origem": str(item),
            "destino": str(destino_arquivo),
            "categoria": categoria,
            "status": "copiado",
        })

    return {
        "destino_base": str(destino_base),
        "total_copiados": len(relatorio),
        "arquivos": relatorio,
    }
