"""Composição ordenável e política de organização FLUXOR (OS021).
A data reflete a última modificação do sistema de arquivos, não EXIF/QuickTime.
"""
from datetime import datetime
import json
from pathlib import Path

from fluxor_core.classifier import classificar_arquivo, obter_extensao

CRITERIOS = ("Tipo", "Extensão", "Ano", "Ano/mês", "Ano/mês/dia")
MODOS_LEGADOS = (
    "Por tipo", "Por extensão", "Por ano", "Por ano e mês",
    "Por tipo e ano", "Por tipo, ano e mês", "Por ano, mês e dia",
)
_TRADUCAO = {
    "Por tipo": ("Tipo",),
    "Por extensão": ("Extensão",),
    "Por ano": ("Ano",),
    "Por ano e mês": ("Ano/mês",),
    "Por tipo e ano": ("Tipo", "Ano"),
    "Por tipo, ano e mês": ("Tipo", "Ano/mês"),
    "Por ano, mês e dia": ("Ano/mês/dia",),
}
MARCADOR = ".fluxor-organizacao.json"


def normalizar_modo(modo):
    """Valida uma sequência em ordem, rejeitando critérios repetidos/ambíguos."""
    if isinstance(modo, str):
        if modo in _TRADUCAO:
            partes = _TRADUCAO[modo]
        elif modo.startswith("Combinar: "):
            partes = tuple(modo[len("Combinar: "):].split(" > "))
        else:
            raise ValueError("Modo de organização desconhecido.")
    elif isinstance(modo, (tuple, list)):
        partes = tuple(modo)
    else:
        raise ValueError("Critérios inválidos.")
    if not (1 <= len(partes) <= 3):
        raise ValueError("Escolha de um a três critérios.")
    if any(not isinstance(p, str) or p not in CRITERIOS for p in partes):
        raise ValueError("Critério de organização desconhecido.")
    if len(set(partes)) != len(partes):
        raise ValueError("Um critério não pode aparecer duas vezes.")
    if sum(p.startswith("Ano") for p in partes) > 1:
        raise ValueError("Selecione somente uma granularidade de data.")
    return partes


def categoria_para(item, modo):
    partes = normalizar_modo(modo)
    data = datetime.fromtimestamp(item.stat().st_mtime) if any(
        p.startswith("Ano") for p in partes
    ) else None
    segmentos = []
    for criterio in partes:
        if criterio == "Tipo":
            segmentos.append(classificar_arquivo(item))
        elif criterio == "Extensão":
            segmentos.append(obter_extensao(item))
        elif criterio == "Ano":
            segmentos.append(str(data.year))
        elif criterio == "Ano/mês":
            segmentos.extend((str(data.year), f"{data.month:02d}"))
        elif criterio == "Ano/mês/dia":
            segmentos.extend((str(data.year), f"{data.month:02d}", f"{data.day:02d}"))
    return str(Path(*segmentos))


def conferir_politica(base, modo):
    """Nunca mistura silenciosamente estruturas quando existe registro do critério."""
    marcador = Path(base) / MARCADOR
    if marcador.is_symlink():
        raise ValueError("Registro da organização é um link simbólico.")
    if not marcador.exists():
        return False  # Coleção legada: revisão manual ainda é necessária.
    try:
        registro = json.loads(marcador.read_text(encoding="utf-8"))
        partes = tuple(registro["criterios"])
        if registro["versao"] != 1 or normalizar_modo(partes) != normalizar_modo(modo):
            raise ValueError("Esta coleção usa outra ordem de critérios. Não misture hierarquias.")
    except (OSError, UnicodeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Registro de critérios ilegível; bloqueada a escrita: {exc}") from exc
    return True


def registrar_politica(base, modo):
    """Grava a política uma só vez; nunca sobrescreve um registro existente."""
    base = Path(base)
    if conferir_politica(base, modo):
        return
    marcador = base / MARCADOR
    conteudo = json.dumps(
        {"versao": 1, "criterios": list(normalizar_modo(modo)),
         "data": "ultima_modificacao"}, ensure_ascii=False, indent=2
    )
    try:
        with marcador.open("x", encoding="utf-8") as arquivo:
            arquivo.write(conteudo + "\n")
    except FileExistsError:
        conferir_politica(base, modo)
