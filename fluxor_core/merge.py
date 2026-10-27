"""Read-only collision and SHA-256 policy for incremental Fluxor collections.

Only checks the matching output category; never scans or modifies the whole
destination tree. All decisions are revalidated at copy time by plan.py.
"""
from pathlib import Path

FOLDER_NAME = "Fluxor_Organizado"


def require_safe_target(root):
    """An existing Fluxor-organized folder, never a link or arbitrary parent."""
    path = Path(root).expanduser()
    if path.name != FOLDER_NAME or not path.is_dir() or path.is_symlink():
        raise ValueError("Selecione diretamente uma pasta Fluxor_Organizado existente.")
    if path.resolve() != path:
        raise ValueError("A pasta organizada não pode ser um atalho simbólico.")
    return path


def ensure_no_links(root, relative_parent):
    """Refuse existing symlinked directory components before any read/write."""
    base = Path(root)
    if base.is_symlink():
        raise ValueError("Destino contém link simbólico na pasta principal.")
    folder = base
    for name in Path(relative_parent).parts:
        if name in ("", "."):
            continue
        if name == "..":
            raise ValueError("Categoria de destino inválida.")
        folder = folder / name
        if folder.is_symlink():
            raise ValueError(f"Pasta de destino contém link simbólico: {folder}")
        if folder.exists() and not folder.is_dir():
            raise ValueError(f"Há um arquivo ocupando o lugar de uma pasta: {folder}")
    return folder


def candidates(root, relative_parent, cancel=None):
    """Return file metadata, no content read. Symlinks reserve their own names."""
    folder = ensure_no_links(root, relative_parent)
    if not folder.is_dir():
        return [], set()
    existing = []
    reserved = set()
    for entry in sorted(folder.iterdir(), key=lambda p: p.name.casefold()):
        if cancel and cancel():
            raise InterruptedError("Prévia interrompida.")
        reserved.add(entry.name.casefold())
        if entry.is_symlink() or not entry.is_file():
            continue
        try:
            existing.append((entry, entry.stat().st_size))
        except OSError:
            continue
    return existing, reserved


def next_name(filename, reserved):
    """Predict an available name while preserving the suffix, case insensitive."""
    file = Path(filename)
    name = file.name
    idx = 0
    while name.casefold() in reserved:
        idx += 1
        if idx > 10000:
            raise ValueError("Muitos arquivos com nomes repetidos.")
        name = f"{file.stem} ({idx}){file.suffix}"
    reserved.add(name.casefold())
    return name


def matching_content(source, source_size, existing, checksum, cancel=None):
    """Full SHA-256 comparison only when a size matches, no partial-hash guesses."""
    possible = [path for path, size in existing if size == source_size]
    if not possible:
        return None
    if cancel and cancel():
        raise InterruptedError("Prévia interrompida.")
    source_sha = checksum(source)
    for path in possible:
        if cancel and cancel():
            raise InterruptedError("Prévia interrompida.")
        try:
            if checksum(path) == source_sha:
                return path
        except OSError:
            continue
    return None


def preview_entries(entries, base, checksum, cancel=None):
    """Annotate files for safe additions without touching destination content."""
    cache = {}
    added = skipped = renamed = 0
    for entry in entries:
        if cancel and cancel():
            raise InterruptedError("Prévia interrompida.")
        parent = Path(entry["destino_relativo"]).parent
        key = str(parent)
        if key not in cache:
            cache[key] = candidates(base, parent, cancel=cancel)
        existing, reserved = cache[key]
        duplicate = matching_content(
            entry["origem"], entry["tamanho"], existing, checksum, cancel=cancel)
        if duplicate is not None:
            entry["acao"] = "ignorar_identico"
            entry["identico_a"] = str(duplicate)
            entry["destino_previsto"] = str(duplicate)
            skipped += 1
            continue
        name = next_name(Path(entry["origem"]).name, reserved)
        entry["acao"] = "copiar"
        entry["destino_relativo"] = str(parent / name)
        entry["destino_previsto"] = str(Path(base) / parent / name)
        entry["renomear"] = name != Path(entry["origem"]).name
        added += 1
        renamed += int(entry["renomear"])
    return {"novos": added, "ignorados_identicos": skipped,
            "nomes_alternativos": renamed}
