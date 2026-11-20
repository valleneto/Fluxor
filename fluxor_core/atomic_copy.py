"""OS024-A: verified, no-clobber publication and conservative idempotent recovery.

A definitive filename is *never* opened for writing. The source streams into a
hidden exclusive temporary inode in the destination directory; after fsync and
SHA-256 verification, POSIX link(2) exclusively publishes the completed inode.
An existing final filename always causes EEXIST; os.replace/rename are not used.

Each transaction has an append-only, fsync'd JSONL journal in its collection.
Recovery never deletes unknown data or overwrites a destination. Not a claim
of APFS/SMB power-loss durability until real Ventura volume tests have passed.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import uuid

JOURNAL_DIR = ".fluxor-journal"
TEMP_PREFIX = ".fluxor-tmp-"
TEMP_SUFFIX = ".part"
VERSION = 1
_CHUNK = 1024 * 1024
_JOURNAL_MAX = 1024 * 1024
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
_STATES = {"planned", "transferring", "verified", "collision", "published", "confirmed", "blocked"}
_JOURNAL_RE = re.compile(r"^[a-f0-9]{32}\.jsonl$")

_MANAGED_TEMP_RE = re.compile(
    "^" + re.escape(TEMP_PREFIX) + "[a-f0-9]{32}" + re.escape(TEMP_SUFFIX) + "$"
)


def is_managed_temp_name(name):
    """Only files with our exact UUID-based temporary naming convention."""
    return bool(_MANAGED_TEMP_RE.fullmatch(name))



def _flush_directory_windows(folder):
    """Call the tested Win32 directory flush; fail closed on every API error.

    This does NOT establish power-loss durability on NTFS, SMB or any drive.
    """
    import ctypes

    directory = Path(folder)
    if not directory.is_dir() or directory.is_symlink():
        raise OSError("Pasta de sincronização inválida.")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    ]
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.FlushFileBuffers.argtypes = [ctypes.c_void_p]
    kernel.FlushFileBuffers.restype = ctypes.c_int
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = ctypes.c_int
    handle = kernel.CreateFileW(
        str(directory), 0x40000000, 0x00000007, None, 3, 0x02000000, None
    )
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not kernel.FlushFileBuffers(handle):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        if not kernel.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())


def _fsync_dir(folder):
    """Fail closed on both POSIX and Windows; no silent durability downgrade."""
    if os.name == "nt":
        _flush_directory_windows(folder)
        return
    fd = os.open(str(folder), os.O_RDONLY | _NOFOLLOW | _DIRECTORY)
    try:
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("Pasta de sincronização inválida.")
        os.fsync(fd)
    finally:
        os.close(fd)


def _safe_base(base):
    base = Path(base)
    if not base.is_dir() or base.is_symlink() or base.resolve() != base:
        raise ValueError("Raiz da coleção indisponível, relativa ou simbólica.")
    return base


def _safe_category(base, folder):
    base = _safe_base(base)
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir() or folder.resolve() != folder:
        raise ValueError("Pasta de publicação indisponível ou simbólica.")
    if folder != base and base not in folder.parents:
        raise ValueError("Pasta de publicação fora da coleção.")
    return folder


def _journal_directory(base):
    base = _safe_base(base)
    folder = base / JOURNAL_DIR
    if folder.is_symlink():
        raise ValueError("Journal simbólico: escrita bloqueada.")
    folder.mkdir(exist_ok=True)
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Journal inválido: escrita bloqueada.")
    _fsync_dir(base)
    return folder


def _append(journal, state, seq, **fields):
    if state not in _STATES:
        raise ValueError("Estado desconhecido no journal.")
    event = {"seq": seq, "state": state, **fields}
    line = (json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    fd = os.open(str(journal), os.O_WRONLY | os.O_APPEND | _NOFOLLOW)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("Registro de transação não é arquivo regular.")
        view = memoryview(line)
        while view:
            n = os.write(fd, view)
            if n <= 0:
                raise OSError("Falha ao persistir journal.")
            view = view[n:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _new_journal(base, operation, initial):
    directory = _journal_directory(base)
    journal = directory / (operation + ".jsonl")
    fd = os.open(str(journal), os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW, 0o600)
    try:
        data = (json.dumps({"seq": 0, "state": "planned", "version": VERSION,
                            "id": operation, **initial}, ensure_ascii=False,
                           sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        while data:
            n = os.write(fd, data)
            if n <= 0:
                raise OSError("Falha criando journal.")
            data = data[n:]
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_dir(directory)
    return journal


def _source_identity(file_stat):
    return {"size": file_stat.st_size, "mtime_ns": file_stat.st_mtime_ns,
            "ino": file_stat.st_ino, "dev": file_stat.st_dev}


def _assert_source(source, expected):
    if source.is_symlink():
        raise OSError("Origem virou um link simbólico.")
    current = source.stat()
    if _source_identity(current) != expected or not stat.S_ISREG(current.st_mode):
        raise OSError("Origem alterada desde a prévia.")
    return current


def _hash_file(path, cancel=None):
    sha = hashlib.sha256()
    fd = os.open(str(path), os.O_RDONLY | _NOFOLLOW)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("SHA-256 exige arquivo regular.")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            while True:
                if cancel and cancel():
                    raise InterruptedError("Verificação interrompida.")
                block = handle.read(_CHUNK)
                if not block:
                    break
                sha.update(block)
    finally:
        if fd >= 0:
            os.close(fd)
    return sha.hexdigest()


def _final_name(folder, requested, counter):
    src = Path(requested)
    if not requested or requested != src.name:
        raise ValueError("Nome definitivo inválido.")
    return folder / (requested if counter == 0 else
                     "{} ({}){}".format(src.stem, counter, src.suffix))


def _stage_matches(path, expected_size, expected_sha, cancel=None):
    if path.is_symlink() or not path.is_file():
        return False
    before = path.stat()
    if before.st_size != expected_size or not stat.S_ISREG(before.st_mode):
        return False
    digest = _hash_file(path, cancel=cancel)
    after = path.stat()
    return (_source_identity(before) == _source_identity(after)
            and digest == expected_sha)


def _owned_stage_cleanup(stage, final, ident):
    """Only unlink the journal-owned temp inode after proven hard-link publication."""
    if not stage.exists():
        return
    if stage.is_symlink() or final.is_symlink() or not final.is_file():
        raise OSError("Recuperação: temporário ou destino simbólico.")
    a, b = stage.stat(), final.stat()
    if not (a.st_dev == b.st_dev and a.st_ino == b.st_ino
            and _source_identity(a)["ino"] == ident["ino"]
            and a.st_dev == ident["dev"]):
        raise OSError("Inodes divergentes; temporário preservado para revisão.")
    stage.unlink()
    _fsync_dir(stage.parent)


def copy_verified(base, source, folder, requested, before, mode, cancel=None,
                  fault=None):
    """Publish a new complete file without clobber; return actual final Path.

    'fault' is for isolated synthetic fault injection only (not used by UI).
    """
    base = _safe_base(base)
    folder = _safe_category(base, folder)
    source = Path(source)
    before_id = _source_identity(before)
    _assert_source(source, before_id)
    op = uuid.uuid4().hex
    temporary = folder / (TEMP_PREFIX + op + TEMP_SUFFIX)
    final = _final_name(folder, requested, 0)
    record = {"source": str(source), "destination": str(final),
              "temporary": str(temporary), "mode": mode,
              "expected": before_id}
    journal = _new_journal(base, op, record)
    seq = 1

    def event(state, **kwargs):
        nonlocal seq
        _append(journal, state, seq, **kwargs)
        seq += 1

    def point(name):
        if fault:
            fault(name)

    event("transferring")
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb") as target:
            fd = -1
            sourcefd = os.open(str(source), os.O_RDONLY | _NOFOLLOW)
            with os.fdopen(sourcefd, "rb") as incoming:
                if _source_identity(os.fstat(incoming.fileno())) != before_id:
                    raise OSError("Identidade da origem mudou antes da transferência.")
                point("after_temp_create")
                while True:
                    if cancel and cancel():
                        raise InterruptedError("Cópia interrompida.")
                    block = incoming.read(_CHUNK)
                    if not block:
                        break
                    target.write(block)
                    point("during_copy")
                target.flush()
                os.fsync(target.fileno())
        point("after_transfer")
        _assert_source(source, before_id)
        shutil.copystat(source, temporary, follow_symlinks=False)
        with temporary.open("r+b" if os.name == "nt" else "rb") as staged:
            os.fsync(staged.fileno())
        _fsync_dir(folder)
        source_sha = _hash_file(source, cancel=cancel)
        stage_sha = _hash_file(temporary, cancel=cancel)
        _assert_source(source, before_id)
        if (source_sha != stage_sha or temporary.stat().st_size != before_id["size"]):
            raise OSError("SHA-256/tamanho da cópia provisória divergente.")
        event("verified", sha256=source_sha, size=before_id["size"])
        point("after_verified")
        for count in range(10001):
            if cancel and cancel():
                raise InterruptedError("Publicação interrompida.")
            _safe_category(base, folder)
            target_path = _final_name(folder, requested, count)
            if count:
                event("collision", destination=str(target_path))
            try:
                os.link(str(temporary), str(target_path), follow_symlinks=False)
                final = target_path
                break
            except FileExistsError:
                continue
        else:
            raise OSError("Muitos nomes ocupados; nenhuma cópia publicada.")
        point("after_link")
        _fsync_dir(folder)
        event("published", destination=str(final))
        point("after_published")
        if not _stage_matches(final, before_id["size"], source_sha):
            raise OSError("Publicação não corresponde à cópia verificada.")
        _owned_stage_cleanup(temporary, final, _source_identity(temporary.stat()))
        event("confirmed", destination=str(final))
        point("after_confirmed")
        return final
    finally:
        if fd >= 0:
            os.close(fd)
        # Never delete an incomplete stage here. Recovery inspects its owner,
        # content and journal. Unknown or unfinished artifacts remain quarantined.


def _read_journal(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > _JOURNAL_MAX:
        raise ValueError("Journal inválido, simbólico ou excessivo.")
    content = path.read_bytes()
    if not content.endswith(b"\n"):
        raise ValueError("Journal truncado: não executar recuperação.")
    try:
        records = [json.loads(x) for x in content.decode("utf-8").splitlines()]
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Journal corrompido.") from exc
    if not records or any(not isinstance(r, dict) or r.get("seq") != i
                          or r.get("state") not in _STATES for i, r in enumerate(records)):
        raise ValueError("Sequência de journal inconsistente.")
    initial = records[0]
    if (initial.get("version") != VERSION or initial["state"] != "planned"
            or not re.fullmatch("[a-f0-9]{32}", str(initial.get("id", "")))
            or path.name != initial["id"] + ".jsonl"):
        raise ValueError("Identidade/versionamento de journal inválidos.")
    return records


def _recover_one(base, journal, cancel=None):
    records = _read_journal(journal)
    initial = records[0]
    operation = initial["id"]
    stage = Path(initial["temporary"])
    destination = Path(initial["destination"])
    source = Path(initial["source"])
    expected = initial["expected"]
    if (not isinstance(expected, dict) or
            set(expected) != {"size", "mtime_ns", "ino", "dev"} or
            any(not isinstance(n, int) for n in expected.values())):
        raise ValueError("Identidade da origem inválida.")
    for r in records[1:]:
        if "destination" in r:
            destination = Path(r["destination"])
    if (stage.name != TEMP_PREFIX + operation + TEMP_SUFFIX
            or stage.parent != destination.parent
            or str(stage) != str(stage.absolute())
            or str(destination) != str(destination.absolute())
            or destination.name.startswith(TEMP_PREFIX)):
        raise ValueError("Journal aponta para caminho não autorizado.")
    folder = _safe_category(base, destination.parent)
    if stage.is_symlink() or destination.is_symlink():
        raise ValueError("Journal aponta para link simbólico.")
    state = records[-1]["state"]
    hashes = [r for r in records if r["state"] == "verified"]
    if not hashes:
        return {"id": operation, "status": "incomplete", "state": state}
    verified = hashes[-1]
    digest, size = verified.get("sha256"), verified.get("size")
    if (not isinstance(digest, str) or not re.fullmatch("[a-f0-9]{64}", digest)
            or size != expected["size"]):
        raise ValueError("Verificação registrada inválida.")

    if state == "confirmed":
        # Already-committed journals are terminal: nothing remains to recover.
        # Avoid rehashing the entire existing collection on every future copy.
        return {"id": operation, "status": "confirmed"}
    if state not in ("verified", "collision", "published"):
        return {"id": operation, "status": "incomplete", "state": state}

    stage_exists = stage.exists()
    final_exists = destination.exists()
    if stage_exists and not _stage_matches(stage, size, digest, cancel):
        raise ValueError("Temporário alterado ou incompleto: bloqueado.")
    if final_exists:
        if destination.is_symlink() or not _stage_matches(destination, size, digest, cancel):
            raise ValueError("Destino ocupado com conteúdo divergente.")
        if stage_exists:
            a, b = stage.stat(), destination.stat()
            if (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino):
                raise ValueError("Destino ocupado por inode alheio.")
        elif state != "published":
            raise ValueError("Sem temporário para provar propriedade do destino.")
    elif state != "published":
        if not stage_exists:
            raise ValueError("Temporário verificado desapareceu.")
        _assert_source(source, expected)
        if _hash_file(source, cancel) != digest:
            raise ValueError("Origem alterada antes de recuperar publicação.")
        try:
            os.link(str(stage), str(destination), follow_symlinks=False)
        except FileExistsError as exc:
            raise ValueError("Colisão durante recuperação; destino preservado.") from exc
        _fsync_dir(folder)
        final_exists = True
    else:
        raise ValueError("Destino publicado desapareceu; revisão manual.")

    if state != "published":
        _append(journal, "published", len(records), destination=str(destination))
        records.append({"state": "published"})
    if stage_exists:
        _owned_stage_cleanup(stage, destination, _source_identity(stage.stat()))
    _append(journal, "confirmed", len(records), destination=str(destination))
    return {"id": operation, "status": "recovered", "destination": str(destination)}


def recover_transactions(base, cancel=None):
    """Conservative idempotent recovery. Never removes uncertain leftovers.

    Returns per-transaction statuses. Blocked journal files remain unchanged.
    """
    base = _safe_base(base)
    directory = base / JOURNAL_DIR
    if not directory.exists():
        return []
    if directory.is_symlink() or not directory.is_dir():
        return [{"status": "blocked", "reason": "Diretório journal não confiável."}]
    results = []
    for path in sorted(directory.iterdir()):
        if cancel and cancel():
            raise InterruptedError("Recuperação cancelada.")
        if not _JOURNAL_RE.fullmatch(path.name):
            results.append({"status": "blocked", "journal": str(path),
                            "reason": "Entrada estranha no diretório de journal."})
            continue
        try:
            results.append(_recover_one(base, path, cancel))
        except (OSError, ValueError, InterruptedError) as exc:
            if isinstance(exc, InterruptedError):
                raise
            results.append({"status": "blocked", "journal": str(path),
                            "reason": str(exc)})
    return results
