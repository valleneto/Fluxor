from pathlib import Path
import shutil

from fluxor_core.classifier import classificar_arquivo


def validar_pastas(pasta_origem, pasta_destino):
    """Rejeita pastas sobrepostas antes de criar qualquer destino."""
    origem = Path(pasta_origem).expanduser().resolve()
    destino = Path(pasta_destino).expanduser().resolve()

    if not origem.is_dir():
        raise ValueError(f"Origem invalida ou inexistente: {origem}")
    if origem == destino or origem in destino.parents or destino in origem.parents:
        raise ValueError("Origem e destino nao podem estar dentro um do outro.")
    return origem, destino


def criar_destino_seguro(pasta_destino, nome_arquivo):
    arquivo = Path(nome_arquivo)
    if not nome_arquivo or arquivo.name != nome_arquivo:
        raise ValueError("Nome de arquivo invalido.")
    destino = Path(pasta_destino) / nome_arquivo
    contador = 1
    while destino.exists() or destino.is_symlink():
        destino = Path(pasta_destino) / f"{arquivo.stem} ({contador}){arquivo.suffix}"
        contador += 1
    return destino


def organizar_por_tipo(pasta_origem, pasta_destino, progresso=None, cancelar=None):
    """Copia arquivos do primeiro nivel, sem remover originais.

    progresso(processados, total) e cancelar() sao callbacks opcionais.
    """
    origem, destino = validar_pastas(pasta_origem, pasta_destino)
    destino_base = destino / "Fluxor_Organizado"
    itens = sorted(
        (item for item in origem.iterdir()
         if not item.is_symlink() and item.is_file()),
        key=lambda item: item.name.lower(),
    )

    relatorio = []
    copiados = 0
    erros = []
    cancelado = False
    total = len(itens)

    for indice, item in enumerate(itens, start=1):
        if cancelar is not None and cancelar():
            cancelado = True
            break

        arquivo_saida = None
        criado = False
        try:
            categoria = classificar_arquivo(item)
            pasta_categoria = destino_base / categoria
            pasta_categoria.mkdir(parents=True, exist_ok=True)
            arquivo_saida = criar_destino_seguro(pasta_categoria, item.name)

            with item.open("rb") as entrada:
                # "xb" evita sobrescrever mesmo se outro processo criar
                # um destino com o mesmo nome enquanto organizamos.
                with arquivo_saida.open("xb") as saida:
                    criado = True
                    shutil.copyfileobj(entrada, saida, length=1024 * 1024)
            shutil.copystat(item, arquivo_saida)
            if item.stat().st_size != arquivo_saida.stat().st_size:
                raise OSError("Tamanho da copia diferente do original")

            copiados += 1
            relatorio.append({
                "origem": str(item),
                "destino": str(arquivo_saida),
                "categoria": categoria,
                "status": "copiado",
            })
        except (OSError, ValueError) as erro:
            if criado and arquivo_saida is not None:
                try:
                    arquivo_saida.unlink()
                except OSError:
                    pass
            erros.append({"origem": str(item), "erro": str(erro)})
            relatorio.append({
                "origem": str(item),
                "destino": str(arquivo_saida) if arquivo_saida else None,
                "status": "erro",
                "erro": str(erro),
            })

        if progresso is not None:
            progresso(indice, total)

    return {
        "destino_base": str(destino_base),
        "total_copiados": copiados,
        "total_erros": len(erros),
        "total_encontrados": total,
        "cancelado": cancelado,
        "erros": erros,
        "arquivos": relatorio,
    }
