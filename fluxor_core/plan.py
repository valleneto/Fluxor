"""Preview and copy engine for Fluxor beta. No source file is deleted."""
from datetime import datetime
from pathlib import Path
import os
import shutil

from fluxor_core.classifier import classificar_arquivo, obter_extensao
from fluxor_core.organizer import validar_pastas

MODOS = ("Por tipo", "Por extensão", "Por ano", "Por ano e mês")


def _categoria(item, modo):
    if modo == "Por tipo":
        return classificar_arquivo(item)
    if modo == "Por extensão":
        return obter_extensao(item)
    data = datetime.fromtimestamp(item.stat().st_mtime)
    if modo == "Por ano":
        return str(data.year)
    return f"{data.year}/{data.month:02d}"


def planejar(origem, destino, modo="Por tipo", recursivo=True):
    if modo not in MODOS:
        raise ValueError("Modo de organizacao invalido.")
    origem, destino = validar_pastas(origem, destino)
    arquivos = []
    avisos = []
    # No symlink folders and no symlink files; avoid copying macOS packages.
    for pasta, subpastas, nomes in os.walk(origem, followlinks=False):
        subpastas[:] = sorted(
            d for d in subpastas
            if not (Path(pasta) / d).is_symlink()
            and not d.lower().endswith((".app", ".bundle", ".photoslibrary", ".pkg"))
        ) if recursivo else []
        for nome in sorted(nomes):
            item = Path(pasta) / nome
            if item.is_symlink() or not item.is_file():
                continue
            try:
                categoria = _categoria(item, modo)
                tamanho = item.stat().st_size
            except OSError as erro:
                avisos.append(f"{item}: {erro}")
                continue
            arquivos.append({
                "origem": str(item),
                "categoria": categoria,
                "destino_relativo": str(Path(categoria) / item.name),
                "tamanho": tamanho,
            })
    return {
        "origem": str(origem),
        "destino": str(destino),
        "destino_base": str(destino / "Fluxor_Organizado"),
        "modo": modo,
        "recursivo": recursivo,
        "arquivos": arquivos,
        "total_arquivos": len(arquivos),
        "tamanho_total": sum(a["tamanho"] for a in arquivos),
        "avisos": avisos,
    }


def executar_plano(plano, progresso=None, cancelar=None):
    origem, destino = validar_pastas(plano["origem"], plano["destino"])
    base = destino / "Fluxor_Organizado"
    copiados = 0
    erros = []
    relatorio = []
    cancelado = False
    total = len(plano["arquivos"])
    for indice, entrada in enumerate(plano["arquivos"], 1):
        if cancelar and cancelar():
            cancelado = True
            break
        arquivo = Path(entrada["origem"])
        saida = None
        criado = False
        try:
            # Revalidate every source to prevent copying outside the scanned tree.
            real = arquivo.resolve()
            if real != origem and origem not in real.parents:
                raise ValueError("Arquivo fora da origem.")
            if arquivo.is_symlink() or not arquivo.is_file():
                raise OSError("Arquivo indisponivel ou link simbolico.")
            relativo = Path(entrada["destino_relativo"])
            if relativo.is_absolute() or ".." in relativo.parts:
                raise ValueError("Destino relativo invalido.")
            pasta = base / relativo.parent
            pasta.mkdir(parents=True, exist_ok=True)
            # Exclusively create names; never overwrite on collisions.
            tentativas = 0
            while True:
                nome = arquivo.name if tentativas == 0 else f"{arquivo.stem} ({tentativas}){arquivo.suffix}"
                saida = pasta / nome
                try:
                    with arquivo.open("rb") as fonte, saida.open("xb") as alvo:
                        criado = True
                        shutil.copyfileobj(fonte, alvo, length=1024 * 1024)
                    break
                except FileExistsError:
                    tentativas += 1
                    if tentativas > 10000:
                        raise OSError("Muitos arquivos com nome repetido.")
            shutil.copystat(arquivo, saida)
            if arquivo.stat().st_size != saida.stat().st_size:
                raise OSError("Tamanho copiado diferente do original.")
            copiados += 1
            relatorio.append({"origem": str(arquivo), "destino": str(saida), "status": "copiado"})
        except (OSError, ValueError) as erro:
            if criado and saida is not None:
                try:
                    saida.unlink()
                except OSError:
                    pass
            erros.append({"origem": str(arquivo), "erro": str(erro)})
            relatorio.append({"origem": str(arquivo), "status": "erro", "erro": str(erro)})
        if progresso:
            progresso(indice, total)
    return {
        "destino_base": str(base),
        "total_encontrados": total,
        "total_copiados": copiados,
        "total_erros": len(erros),
        "cancelado": cancelado,
        "erros": erros,
        "arquivos": relatorio,
    }
