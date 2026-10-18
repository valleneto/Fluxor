from pathlib import Path
import shutil

from fluxor_core.classifier import classificar_arquivo


def validar_pastas(pasta_origem, pasta_destino):
    """Reject overlapping roots before creating or copying any files."""
    origem = Path(pasta_origem).expanduser().resolve()
    destino = Path(pasta_destino).expanduser().resolve()

    if not origem.is_dir():
        raise ValueError(f"Origem invalida ou inexistente: {origem}")

    if origem == destino or origem in destino.parents or destino in origem.parents:
        raise ValueError("Origem e destino nao podem estar dentro um do outro.")

    return origem, destino


def criar_destino_seguro(pasta_destino, nome_arquivo):
    pasta = Path(pasta_destino)
    destino = pasta / nome_arquivo
    contador = 1

    while destino.exists() or destino.is_symlink():
        original = Path(nome_arquivo)
        destino = pasta / f"{original.stem} ({contador}){original.suffix}"
        contador += 1

    return destino


def organizar_por_tipo(pasta_origem, pasta_destino):
    origem, destino = validar_pastas(pasta_origem, pasta_destino)
    destino_base = destino / "Fluxor_Organizado"

    destino_base.mkdir(parents=True, exist_ok=True)
    relatorio = []

    # MVP: files immediately inside the source folder, not recursive.
    for item in origem.iterdir():
        if item.is_symlink() or not item.is_file():
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
