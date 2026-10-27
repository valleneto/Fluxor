"""Preview and copy engine for Fluxor beta. No source file is deleted."""
from datetime import datetime
import hashlib
from pathlib import Path
import os
import shutil
import stat

from fluxor_core.criteria import (MODOS_LEGADOS, normalizar_modo, categoria_para,
                                  conferir_politica, registrar_politica)
from fluxor_core.organizer import validar_pastas
from fluxor_core.merge import require_safe_target, ensure_no_links, candidates, matching_content, preview_entries

MODOS = MODOS_LEGADOS


def _categoria(item, modo):
    return categoria_para(item, modo)


def planejar(origem, destino, modo="Por tipo", recursivo=True, cancelar=None, acrescentar=False, progresso=None):
    normalizar_modo(modo)
    if acrescentar:
        require_safe_target(destino)
    elif Path(destino).expanduser().name == "Fluxor_Organizado":
        raise ValueError(
            "Você selecionou a pasta já organizada. Use "
            "'Acrescentar a uma organização existente' para evitar subpastas duplicadas."
        )
    origem, destino = validar_pastas(origem, destino)
    base = destino if acrescentar else destino / "Fluxor_Organizado"
    if base.is_symlink():
        raise ValueError("O destino organizado não pode ser um link simbólico.")
    arquivos = []
    avisos = []
    bloqueios = []
    if base.exists() and not conferir_politica(base, modo):
        avisos.append("Coleção anterior sem registro de critérios: revise a hierarquia antes de acrescentar.")
    # Avoid recursive loops and report network permission/access failures.
    seen_dirs = set()
    max_depth = 42
    def walk_error(error):
        # A disconnected remote share must abort the preview. Never suggest
        # copying a partial directory listing as if scanning had completed.
        raise OSError(f"Falha ao ler pasta/rede: {error}")
    for pasta, subpastas, nomes in os.walk(
        origem, topdown=True, followlinks=False, onerror=walk_error
    ):
        if cancelar and cancelar():
            raise InterruptedError("Prévia interrompida pelo usuário.")
        current = Path(pasta)
        depth = len(current.relative_to(origem).parts)
        if depth > max_depth:
            subpastas[:] = []
            bloqueios.append(f"Profundidade limitada em {max_depth} níveis: {current}")
            continue
        try:
            stat = current.stat()
            identity = (stat.st_dev, stat.st_ino)
        except OSError as error:
            subpastas[:] = []
            bloqueios.append(f"Erro ao ler {current}: {error}")
            continue
        if stat.st_ino > 0:
            if identity in seen_dirs:
                subpastas[:] = []
                bloqueios.append(f"Possível ciclo de pasta/atalho evitado: {current}")
                continue
            seen_dirs.add(identity)
        subpastas[:] = sorted(
            d for d in subpastas
            if not (Path(pasta) / d).is_symlink()
            and not d.lower().endswith((".app", ".bundle", ".photoslibrary", ".pkg"))
        ) if recursivo else []
        for nome in sorted(nomes):
            if cancelar and cancelar():
                raise InterruptedError("Prévia interrompida pelo usuário.")
            item = Path(pasta) / nome
            if item.is_symlink():
                continue
            try:
                info = item.stat()
                if not stat.S_ISREG(info.st_mode):
                    continue
                categoria = _categoria(item, modo)
                tamanho = info.st_size
            except OSError as erro:
                bloqueios.append(f"{item}: {erro}")
                continue
            arquivos.append({
                "origem": str(item),
                "categoria": categoria,
                "destino_relativo": str(Path(categoria) / item.name),
                "tamanho": tamanho,
                "modified_ns": info.st_mtime_ns,
            })
            if progresso and len(arquivos) % 40 == 0:
                progresso(len(arquivos), 0)
    resumo_acrescimo = (
        preview_entries(arquivos, base, sha256_arquivo, cancelar)
        if acrescentar and not bloqueios else {"novos": len(arquivos), "ignorados_identicos": 0, "nomes_alternativos": 0}
    )
    return {
        "origem": str(origem),
        "destino": str(destino),
        "destino_base": str(base),
        "acrescentar": bool(acrescentar),
        "resumo_acrescimo": resumo_acrescimo,
        "modo": modo,
        "recursivo": recursivo,
        "arquivos": arquivos,
        "total_arquivos": len(arquivos),
        "tamanho_total": sum(a["tamanho"] for a in arquivos),
        "avisos": avisos,
        "bloqueios": bloqueios,
        "completa": not bloqueios,
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
    try:
        readonly_flag = getattr(os, "ST_RDONLY", 1)
        if os.statvfs(ancora).f_flag & readonly_flag:
            raise PermissionError(
                "O disco/pasta de destino é somente leitura. "
                "Escolha uma pasta gravável; o Samsung NTFS pode estar "
                "montado apenas para leitura no macOS."
            )
    except AttributeError:
        # On an unusual platform without statvfs, exclusive creation still
        # protects all originals and fails safely if the target is read-only.
        pass
    livres = shutil.disk_usage(ancora).free
    necessario = sum(int(x["tamanho"]) for x in plano["arquivos"] if x.get("acao") != "ignorar_identico")
    if livres < necessario:
        raise OSError(f"Espaco insuficiente: necessario {necessario}, livre {livres} bytes")
    return {"livres": livres, "necessario": necessario}


def executar_plano(plano, progresso=None, cancelar=None):
    if not plano.get("completa", True) or plano.get("bloqueios"):
        raise ValueError("Prévia incompleta: nenhuma cópia foi autorizada. Corrija os erros e refaça a leitura.")
    normalizar_modo(plano.get("modo", "Por tipo"))
    acrescentar = bool(plano.get("acrescentar", False))
    if acrescentar:
        require_safe_target(plano["destino"])
    origem, destino = validar_pastas(plano["origem"], plano["destino"])
    base = destino if acrescentar else destino / "Fluxor_Organizado"
    if base.is_symlink() or (base.exists() and base.resolve() != base):
        raise ValueError("Pasta organizada não pode ser um link simbólico.")
    if Path(plano["destino_base"]) != base:
        raise ValueError("Destino mudou desde a prévia; refaça a análise.")
    conferir_politica(base, plano.get("modo", "Por tipo"))
    verificar_espaco(plano)
    copiados = 0
    ignorados = 0
    renomeados = 0
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
            # Refuse symlink folders BEFORE mkdir to avoid traversal while writing.
            pasta = ensure_no_links(base, relativo.parent)
            pasta.mkdir(parents=True, exist_ok=True)
            ensure_no_links(base, relativo.parent)
            if base.resolve() != base or pasta.resolve() != pasta:
                raise ValueError("Destino contem link simbolico.")
            if pasta != base and base not in pasta.parents:
                raise ValueError("Destino fora da pasta organizada.")
            before = arquivo.stat()
            if before.st_size != int(entrada["tamanho"]) or (entrada.get("modified_ns") is not None and before.st_mtime_ns != int(entrada["modified_ns"])):
                raise OSError("Origem mudou desde a previa; planeje novamente.")
            if acrescentar:
                # Re-check content and category at commit time. Plans may be stale,
                # and a duplicate may have arrived since the preview.
                existentes, _ = candidates(base, relativo.parent, cancel=cancelar)
                duplicado = matching_content(
                    arquivo, before.st_size, existentes, sha256_arquivo, cancelar)
                if entrada.get("acao") == "ignorar_identico":
                    if duplicado is None:
                        raise OSError("Arquivo idêntico não existe mais; refaça a prévia.")
                if duplicado is not None:
                    ignored_path = str(duplicado)
                    if entrada.get("acao") == "ignorar_identico" and (
                        ignored_path != entrada.get("identico_a")
                    ):
                        raise OSError("O arquivo de referência mudou desde a prévia.")
                    # Check stale-source metadata even when we skip a copy.
                    after_skip = arquivo.stat()
                    if (after_skip.st_size, after_skip.st_mtime_ns, after_skip.st_ino) != (
                        before.st_size, before.st_mtime_ns, before.st_ino
                    ):
                        raise OSError("Origem mudou durante a verificação.")
                    ignorados += 1
                    relatorio.append({
                        "origem": str(arquivo),
                        "destino": ignored_path,
                        "status": "ignorado_identico",
                    })
                    if progresso:
                        progresso(indice, total)
                    continue
            # Exclusively create names; never overwrite on collisions.
            tentativas = 0
            while True:
                requested = relativo.name if acrescentar else arquivo.name
                planned = Path(requested)
                nome = requested if tentativas == 0 else f"{planned.stem} ({tentativas}){planned.suffix}"
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
            different_name = saida.name != arquivo.name
            renomeados += int(different_name)
            relatorio.append({
                "origem": str(arquivo), "destino": str(saida),
                "status": "copiado_renomeado" if different_name else "copiado",
            })
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
    if copiados and not cancelado and not erros:
        try:
            registrar_politica(base, plano.get("modo", "Por tipo"))
        except (OSError, ValueError) as exc:
            erros.append({"origem": "", "erro": f"Não foi possível registrar os critérios: {exc}"})
    return {
        "destino_base": str(base),
        "acrescentar": acrescentar,
        "total_encontrados": total,
        "total_copiados": copiados,
        "total_ignorados": ignorados,
        "total_renomeados": renomeados,
        "total_erros": len(erros),
        "cancelado": cancelado,
        "erros": erros,
        "arquivos": relatorio,
    }
