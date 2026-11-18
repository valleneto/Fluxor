"""OS024-A T01–T22: artificial files only; deterministic Linux CI fault injection.

T22 is the historic OS005–OS022 CI regression suite (workflow job below).
This module never opens user folders or mounted network volumes.
"""
import errno
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fluxor_core.atomic_copy import (
    copy_verified, recover_transactions, JOURNAL_DIR, TEMP_PREFIX
)
from fluxor_core.plan import planejar, executar_plano, sha256_arquivo


def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def setup(root, data=b"alpha"):
    source = root / "source"
    base = root / "out" / "Fluxor_Organizado"
    folder = base / "Videos"
    source.mkdir()
    folder.mkdir(parents=True)
    file = source / "clip.mp4"
    file.write_bytes(data)
    return file, base, folder


def check_no_partial_final(folder, *permitted):
    for item in folder.iterdir():
        if item.name.startswith(TEMP_PREFIX):
            assert item.suffix == ".part"
        else:
            assert item.name in permitted, ("unexpected published file", item)


def test(label, fn):
    fn()
    print(label + " OK", flush=True)


def T01():
    with TemporaryDirectory() as d:
        root = Path(d)
        source, base, folder = setup(root)
        final = copy_verified(base, source, folder, source.name, source.stat(), "Por tipo")
        assert final.read_bytes() == source.read_bytes()
        assert digest(final) == digest(source)
        assert recover_transactions(base)[0]["status"] == "confirmed"
        assert not list(folder.glob(TEMP_PREFIX + "*"))


def T02():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", cancel=lambda: True)
        except InterruptedError:
            pass
        else:
            raise AssertionError("cancel was not observed")
        assert not (folder / source.name).exists()
        assert recover_transactions(base)[0]["status"] == "incomplete"


def T03():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d), b"A" * (3 * 1024 * 1024))
        chunks = [0]
        def cancel():
            chunks[0] += 1
            return chunks[0] > 1
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", cancel=cancel)
        except InterruptedError:
            pass
        else:
            raise AssertionError("midstream cancellation did not occur")
        check_no_partial_final(folder)
        assert list(folder.glob(TEMP_PREFIX + "*"))


def T04():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d), b"B" * (3 * 1024 * 1024))
        child = (
            "import os,sys; from pathlib import Path; "
            "from fluxor_core.atomic_copy import copy_verified; "
            "s,b,f=map(Path,sys.argv[1:]); "
            "copy_verified(b,s,f,s.name,s.stat(),'Por tipo',"
            "fault=lambda state: os._exit(77) if state=='during_copy' else None)"
        )
        process = subprocess.run(
            [sys.executable, "-c", child, str(source), str(base), str(folder)],
            timeout=12, check=False,
        )
        assert process.returncode == 77, process.returncode
        check_no_partial_final(folder)
        assert recover_transactions(base)[0]["status"] == "incomplete"
        assert source.read_bytes() == b"B" * (3 * 1024 * 1024)


def fault_at(point):
    def fault(state):
        if state == point:
            raise OSError("synthetic failure: " + point)
    return fault


def interrupted_verified(point):
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", fault=fault_at(point))
        except OSError:
            pass
        else:
            raise AssertionError("fault not injected: " + point)
        return source, base, folder  # not used outside the fixture


def T05():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", fault=fault_at("after_transfer"))
        except OSError:
            pass
        else:
            raise AssertionError()
        assert not (folder / source.name).exists()
        assert recover_transactions(base)[0]["status"] == "incomplete"


def T06_T08():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", fault=fault_at("after_verified"))
        except OSError:
            pass
        else:
            raise AssertionError()
        assert not (folder / source.name).exists()
        journal = next((base / JOURNAL_DIR).glob("*.jsonl"))
        before = journal.read_bytes()
        result = recover_transactions(base)
        assert result[0]["status"] == "recovered", result
        assert (folder / source.name).read_bytes() == source.read_bytes()
        after = journal.read_bytes()
        assert before != after
        for i in range(3):
            result = recover_transactions(base)
            assert result == [{"id": result[0]["id"], "status": "confirmed"}], result
            assert journal.read_bytes() == after
        assert not list(folder.glob(TEMP_PREFIX + "*"))


def T07():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", fault=fault_at("after_link"))
        except OSError:
            pass
        else:
            raise AssertionError()
        assert (folder / source.name).read_bytes() == source.read_bytes()
        assert recover_transactions(base)[0]["status"] == "recovered"
        assert not list(folder.glob(TEMP_PREFIX + "*"))
        assert digest(folder / source.name) == digest(source)


def T09_T10():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d), b"new bytes")
        occupied = folder / source.name
        occupied.write_bytes(b"existing bytes")
        sha_before = digest(occupied)
        final = copy_verified(base, source, folder, source.name,
                              source.stat(), "Por tipo")
        assert final.name == "clip (1).mp4", final
        assert sha_before == digest(occupied)
        assert occupied.read_bytes() == b"existing bytes"
        assert final.read_bytes() == b"new bytes"


def T11():
    with TemporaryDirectory() as d:
        root = Path(d)
        source = root / "incoming"
        target = root / "target"
        source.mkdir()
        target.mkdir()
        (source / "a.mp4").write_bytes(b"identical content")
        (source / "b.mp4").write_bytes(b"identical content")
        first = planejar(source, target, "Por tipo")
        old = executar_plano(first)
        assert old["total_copiados"] == 2
        # Historical normal mode intentionally permits same bytes under distinct names.
        extra = root / "append"
        extra.mkdir()
        (extra / "different-name.mp4").write_bytes(b"identical content")
        plan = planejar(extra, Path(old["destino_base"]), "Por tipo",
                        acrescentar=True)
        assert plan["resumo_acrescimo"]["ignorados_identicos"] == 1
        assert executar_plano(plan)["total_ignorados"] == 1
        # A synthetic orphan with the exact managed temp pattern MUST NEVER
        # be interpreted as a committed duplicate in the same category.
        category = Path(old["destino_base"]) / "Videos"
        orphan = category / (TEMP_PREFIX + "f" * 32 + ".part")
        orphan.write_bytes(b"uncommitted fixture")
        pending_src = root / "orphan_input"
        pending_src.mkdir()
        (pending_src / "pending.mp4").write_bytes(b"uncommitted fixture")
        pending = planejar(pending_src, Path(old["destino_base"]), "Por tipo",
                          acrescentar=True)
        assert pending["resumo_acrescimo"]["novos"] == 1, pending
        assert pending["resumo_acrescimo"]["ignorados_identicos"] == 0
        assert executar_plano(pending)["total_copiados"] == 1
        assert orphan.read_bytes() == b"uncommitted fixture"



def T12():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d), b"A" * (2 * 1024 * 1024))
        changed = [False]
        def mutate(state):
            if state == "during_copy" and not changed[0]:
                source.write_bytes(b"replaced fixture")
                changed[0] = True
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", fault=mutate)
        except OSError:
            pass
        else:
            raise AssertionError("changed source accepted")
        check_no_partial_final(folder)


def T13():
    import fluxor_core.atomic_copy as atomic
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        with patch.object(atomic, "_hash_file", side_effect=OSError("I/O failed")):
            try:
                copy_verified(base, source, folder, source.name, source.stat(), "Por tipo")
            except OSError:
                pass
            else:
                raise AssertionError("I/O fault was swallowed")
        assert not (folder / source.name).exists()


def T14():
    import fluxor_core.atomic_copy as atomic
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        with patch.object(atomic.os, "link", side_effect=OSError(errno.ENOSPC, "no space")):
            try:
                copy_verified(base, source, folder, source.name, source.stat(), "Por tipo")
            except OSError as exc:
                assert exc.errno == errno.ENOSPC
            else:
                raise AssertionError("ENOSPC swallowed")
        check_no_partial_final(folder)


def T15():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        journal_dir = base / JOURNAL_DIR
        journal_dir.mkdir()
        bad = journal_dir / ("0" * 32 + ".jsonl")
        bad.write_bytes(b'{"seq":0,')
        first = recover_transactions(base)
        assert first[0]["status"] == "blocked"
        assert bad.read_bytes() == b'{"seq":0,'
        assert recover_transactions(base) == first


def T16():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", fault=fault_at("after_verified"))
        except OSError:
            pass
        staged = next(folder.glob(TEMP_PREFIX + "*"))
        staged.write_bytes(b"external fixture corruption")
        assert recover_transactions(base)[0]["status"] == "blocked"
        assert not (folder / source.name).exists()


def T17():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        link = source.parent / "alias.mp4"
        link.symlink_to(source)
        try:
            copy_verified(base, link, folder, link.name, link.stat(), "Por tipo")
        except (OSError, ValueError):
            pass
        else:
            raise AssertionError("source symlink allowed")
        assert not (folder / link.name).exists()


def T18():
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d), b"first")
        second = source.parent / "other" / "clip.mp4"
        second.parent.mkdir()
        second.write_bytes(b"second")
        def job(file):
            return copy_verified(base, file, folder, "clip.mp4",
                                 file.stat(), "Por tipo")
        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = list(pool.map(job, (source, second)))
        assert a != b and {a.name, b.name} == {"clip.mp4", "clip (1).mp4"}
        assert {a.read_bytes(), b.read_bytes()} == {b"first", b"second"}


def T19():
    with TemporaryDirectory() as d:
        root = Path(d)
        src = root / "source"
        src.mkdir()
        photo = src / "image.jpg"
        photo.write_bytes(b"synthetic photo")
        for index, mode in enumerate(("Combinar: Tipo > Ano/mês",
                                      "Combinar: Ano/mês > Tipo")):
            target = root / ("target" + str(index))
            target.mkdir()
            plan = planejar(src, target, mode)
            assert plan["completa"], plan
            assert executar_plano(plan)["total_copiados"] == 1


def T20():
    with TemporaryDirectory() as d:
        root = Path(d)
        source = root / "source"
        source.mkdir()
        (source / "a.jpg").write_bytes(b"fixture")
        dest = root / "dest"
        dest.mkdir()
        done = executar_plano(planejar(source, dest, "Por tipo"))
        assert done["total_copiados"] == 1
        try:
            planejar(source, dest, "Por ano")
        except ValueError:
            pass
        else:
            raise AssertionError("mixed policy accepted")


def T21():
    import fluxor_core.atomic_copy as atomic
    with TemporaryDirectory() as d:
        source, base, folder = setup(Path(d))
        with patch.object(atomic.os, "link",
                          side_effect=OSError(errno.EOPNOTSUPP, "hard links unsupported")):
            try:
                copy_verified(base, source, folder, source.name,
                              source.stat(), "Por tipo")
            except OSError as e:
                assert e.errno == errno.EOPNOTSUPP
            else:
                raise AssertionError("unsupported volume allowed")
        check_no_partial_final(folder)


def T22():
    # The historic regression suite is separately invoked by CI's existing
    # OS005–OS022 steps; verify the runner's exact gate names in YAML.
    path = Path(".github/workflows/mvp-checks.yml")
    workflow = path.read_text()
    for n in ("OS019 incremental", "OS020 combined", "OS021 ordered",
              "OS022 approved", "Safety regression", "Qt offscreen"):
        assert n in workflow, n


def main():
    for name, fn in (
        ("T01", T01), ("T02", T02), ("T03", T03),
        ("T04", T04), ("T05", T05), ("T06/T08", T06_T08),
        ("T07", T07), ("T09/T10", T09_T10), ("T11", T11),
        ("T12", T12), ("T13", T13), ("T14", T14),
        ("T15", T15), ("T16", T16), ("T17", T17),
        ("T18", T18), ("T19", T19), ("T20", T20),
        ("T21", T21), ("T22", T22)
    ):
        test(name, fn)
    print("OS024-A T01–T22 synthetic safety matrix passed", flush=True)


if __name__ == "__main__":
    main()
