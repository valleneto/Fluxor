"""OS025-B Windows-only synthetic crash, recovery and no-overwrite tests.

All filesystem operations run beneath TemporaryDirectory. No SMB or user files.
"""
import errno
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fluxor_core.atomic_copy import (
    copy_verified, recover_transactions, JOURNAL_DIR, TEMP_PREFIX,
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def new_files(root, data=b"only-synthetic-data"):
    root = Path(root).resolve()
    source = root / "source"
    folder = root / "output" / "Fluxor_Organizado" / "Videos"
    source.mkdir()
    folder.mkdir(parents=True)
    original = source / "sample.mp4"
    original.write_bytes(data)
    return original, folder.parent, folder


def test_verified_copy():
    with TemporaryDirectory() as temp:
        source, base, folder = new_files(temp)
        before = sha(source)
        final = copy_verified(base, source, folder, source.name, source.stat(), "Por tipo")
        assert final.read_bytes() == source.read_bytes() and sha(final) == before
        assert recover_transactions(base)[0]["status"] == "confirmed"
        assert not list(folder.glob(TEMP_PREFIX + "*"))
        assert sha(source) == before


def test_collision_never_overwrites():
    with TemporaryDirectory() as temp:
        source, base, folder = new_files(temp, b"new-version")
        occupied = folder / source.name
        occupied.write_bytes(b"existing-protected")
        final = copy_verified(base, source, folder, source.name, source.stat(), "Por tipo")
        assert final != occupied and final.name == "sample (1).mp4"
        assert occupied.read_bytes() == b"existing-protected"
        assert final.read_bytes() == b"new-version"
        assert source.read_bytes() == b"new-version"


def test_cancel_incomplete():
    with TemporaryDirectory() as temp:
        source, base, folder = new_files(temp, b"x" * (3 * 1024 * 1024))
        calls = [0]
        def cancel():
            calls[0] += 1
            return calls[0] > 1
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", cancel=cancel)
        except InterruptedError:
            pass
        else:
            raise AssertionError("Cancellation not observed")
        assert not (folder / source.name).exists()
        assert recover_transactions(base)[0]["status"] == "incomplete"
        assert source.stat().st_size == 3 * 1024 * 1024


def fail_at(point):
    def fault(where):
        if where == point:
            raise OSError("synthetic injection: " + point)
    return fault


def test_recover_verified():
    with TemporaryDirectory() as temp:
        source, base, folder = new_files(temp)
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", fault=fail_at("after_verified"))
        except OSError:
            pass
        else:
            raise AssertionError("After-verified fault missing")
        assert not (folder / source.name).exists()
        recovered = recover_transactions(base)
        assert recovered[0]["status"] == "recovered", recovered
        assert (folder / source.name).read_bytes() == source.read_bytes()
        assert recover_transactions(base)[0]["status"] == "confirmed"
        assert not list(folder.glob(TEMP_PREFIX + "*"))


def test_recover_after_link():
    with TemporaryDirectory() as temp:
        source, base, folder = new_files(temp)
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", fault=fail_at("after_link"))
        except OSError:
            pass
        else:
            raise AssertionError("After-link fault missing")
        final = folder / source.name
        assert final.read_bytes() == source.read_bytes()
        assert recover_transactions(base)[0]["status"] == "recovered"
        assert not list(folder.glob(TEMP_PREFIX + "*"))


def test_tampered_temp_blocks():
    with TemporaryDirectory() as temp:
        source, base, folder = new_files(temp)
        try:
            copy_verified(base, source, folder, source.name, source.stat(),
                          "Por tipo", fault=fail_at("after_verified"))
        except OSError:
            pass
        else:
            raise AssertionError("Fault not injected")
        stage = next(folder.glob(TEMP_PREFIX + "*"))
        stage.write_bytes(b"tampered")
        assert recover_transactions(base)[0]["status"] == "blocked"
        assert not (folder / source.name).exists()


def test_concurrent_collision():
    with TemporaryDirectory() as temp:
        source, base, folder = new_files(temp, b"first")
        alt = Path(temp).resolve() / "second" / "sample.mp4"
        alt.parent.mkdir()
        alt.write_bytes(b"second")
        def task(item):
            return copy_verified(base, item, folder, "sample.mp4", item.stat(), "Por tipo")
        with ThreadPoolExecutor(max_workers=2) as pool:
            one, two = list(pool.map(task, (source, alt)))
        assert one != two and {one.name, two.name} == {"sample.mp4", "sample (1).mp4"}
        assert {one.read_bytes(), two.read_bytes()} == {b"first", b"second"}
        assert recover_transactions(base)
        assert all(x["status"] == "confirmed" for x in recover_transactions(base))


def test_unsupported_hardlink_blocks():
    import fluxor_core.atomic_copy as atomic
    with TemporaryDirectory() as temp:
        source, base, folder = new_files(temp)
        with patch.object(atomic.os, "link",
                          side_effect=OSError(errno.EOPNOTSUPP, "not supported")):
            try:
                copy_verified(base, source, folder, source.name, source.stat(),
                              "Por tipo")
            except OSError as exc:
                assert exc.errno == errno.EOPNOTSUPP
            else:
                raise AssertionError("Unsafe fallback was used")
        assert not (folder / source.name).exists()
        assert source.read_bytes() == b"only-synthetic-data"


def main():
    assert os.name == "nt"
    for case in (
        test_verified_copy,
        test_collision_never_overwrites,
        test_cancel_incomplete,
        test_recover_verified,
        test_recover_after_link,
        test_tampered_temp_blocks,
        test_concurrent_collision,
        test_unsupported_hardlink_blocks,
    ):
        case()
        print(case.__name__ + " PASS", flush=True)
    print("OS025-B Windows synthetic recovery 8/8 PASS", flush=True)


if __name__ == "__main__":
    main()
