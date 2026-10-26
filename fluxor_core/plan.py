"""Preview and copy engine for Fluxor beta. No source file is deleted."""
from datetime import datetime
import hashlib
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


def planejar(origem, destino, modo="Por tipo", recursivo=True, cancelar=None):
    if modo not in MODOS:
        raise ValueError("Modo de organizacao invalido.")
    origem, destino = validar_pastas(origem, destino)
    arquivos = []
    avisos = []
    # No symlink folders and no symlink files; avoid copying macOS packages.
    for pasta, subpastas, nomes in os.walk(origem, followlinks=False):
        if cancelar and cancelar():
            raise InterruptedError("Prévia interrompida pelo usuário.")
        subpastas[:] = sorted(
            d for d in subpastas
            if not (Path(pasta) / d).is_symlink()
            and not d.lower().endswith((".app", ".bundle", ".photoslibrary", ".pkg"))
        ) if recursivo else []
        for nome in sorted(nomes):
            if cancelar and cancelar():
                raise InterruptedError("Prévia interrompida pelo usuário.")
            item = Path(pasta) / nome
            if item.is_symlink() or not item.is_file():
                continue
            try:
                categoria = _categoria(item, modo)
                info = item.stat()
                tamanho = info.st_size
            except OSError as erro:
                avisos.append(f"{item}: {erro}")
                continue
            arquivos.append({
                "origem": str(item),
                "categoria": categoria,
                "destino_relativo": str(Path(categoria) / item.name),
                "tamanho": tamanho,
                "modified_ns": info.st_mtime_ns,
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


def sha256_arquivo(arquivo):
    digest = hashlib.sha256()
    with Path(arquivo).open("rb") as fonte:
        for bloco in iter(lambda: fonte.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def verificar_espaco(plano):
    """Conservative free-space check before copying."""
    destino = Path(plano["destino"]).expanduser().resolve()
    ancora = destino
    while not ancora.exists() and ancora != ancora.parent:
        ancora = ancora.parent
    if not ancora.is_dir():
        raise ValueError("Destino indisponivel.")
    livres = shutil.disk_usage(ancora).free
    necessario = sum(int(x["tamanho"]) for x in plano["arquivos"])
    if livres < necessario:
        raise OSError(f"Espaco insuficiente: necessario {necessario}, livre {livres} bytes")
    return {"livres": livres, "necessario": necessario}


def executar_plano(plano, progresso=None, cancelar=None):
    origem, destino = validar_pastas(plano["origem"], plano["destino"])
    verificar_espaco(plano)
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
            if base.resolve() != base or pasta.resolve() != pasta:
                raise ValueError("Destino contem link simbolico.")
            if pasta != base and base not in pasta.parents:
                raise ValueError("Destino fora da pasta organizada.")
            before = arquivo.stat()
            if before.st_size != int(entrada["tamanho"]) or (entrada.get("modified_ns") is not None and before.st_mtime_ns != int(entrada["modified_ns"])):
                raise OSError("Origem mudou desde a previa; planeje novamente.")
            # Exclusively create names; never overwrite on collisions.
            tentativas = 0
            while True:
                nome = arquivo.name if tentativas == 0 else f"{arquivo.stem} ({tentativas}){arquivo.suffix}"
                saida = pasta / nome
                try:
                    with arquivo.open("rb") as fonte, saida.open("xb") as alvo:
                        criado = True
                        while True:
                            if cancelar and cancelar():
                                raise InterruptedError("Copia interrompida.")
                            bloco = fonte.read(1024 * 1024)
                            if not bloco:
                                break
                            alvo.write(bloco)
                    break
                except FileExistsError:
                    tentativas += 1
                    if tentativas > 10000:
                        raise OSError("Muitos arquivos com nome repetido.")
            shutil.copystat(arquivo, saida)
            after = arquivo.stat()
            if (after.st_size, after.st_mtime_ns, after.st_ino) != (before.st_size, before.st_mtime_ns, before.st_ino):
                raise OSError("Origem mudou durante a cópia; resultado descartado.")
            if after.st_size != saida.stat().st_size:
                raise OSError("Tamanho copiado diferente do original.")
            if sha256_arquivo(arquivo) != sha256_arquivo(saida):
                raise OSError("SHA-256 da copia diferente do original.")
            copiados += 1
            relatorio.append({"origem": str(arquivo), "destino": str(saida), "status": "copiado"})
        except (OSError, ValueError, InterruptedError) as erro:
            if criado and saida is not None:
                try:
                    saida.unlink()
                except OSError:
                    pass
            if isinstance(erro, InterruptedError):
                cancelado = True
            else:
                erros.append({"origem": str(arquivo), "erro": str(erro)})
            relatorio.append({"origem": str(arquivo), "status": "interrompido" if cancelado else "erro", "erro": str(erro)})
            if cancelado:
                break
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
