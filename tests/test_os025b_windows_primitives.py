"""OS025-B: synthetic NTFS primitives probe, not a product durability claim."""
import ctypes
import os
from pathlib import Path
import platform
import stat
from tempfile import TemporaryDirectory


def test_exclusive_hardlink(folder):
    source = folder / "verified.tmp"
    final = folder / "verified.txt"
    source.write_bytes(b"safe-checksum-payload")
    os.link(str(source), str(final), follow_symlinks=False)
    assert final.read_bytes() == b"safe-checksum-payload"
    different = folder / "other.tmp"
    different.write_bytes(b"never-overwrite")
    try:
        os.link(str(different), str(final), follow_symlinks=False)
    except FileExistsError:
        pass
    else:
        raise AssertionError("Existing destination was unexpectedly overwritten")
    assert final.read_bytes() == b"safe-checksum-payload"
    assert different.read_bytes() == b"never-overwrite"
    assert source.stat().st_ino == final.stat().st_ino
    print("NTFS_EXCLUSIVE_HARDLINK PASS")


def test_directory_flush(folder):
    # Conservative Windows Win32 probe: no fallback to a no-op fsync.
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
    INVALID_HANDLE = ctypes.c_void_p(-1).value
    GENERIC_WRITE = 0x40000000
    FILE_SHARE_READ_WRITE_DELETE = 7
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    handle = kernel.CreateFileW(
        str(folder), GENERIC_WRITE, FILE_SHARE_READ_WRITE_DELETE, None,
        OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, None
    )
    if handle == INVALID_HANDLE:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not kernel.FlushFileBuffers(handle):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        if not kernel.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())
    print("NTFS_DIRECTORY_FLUSH_CALL PASS (not power-loss guarantee)")


def main():
    assert os.name == "nt", "Windows-only diagnostic"
    print("WINDOWS", platform.platform())
    with TemporaryDirectory(prefix="fluxor-os025b-primitives-") as temp:
        root = Path(temp)
        test_exclusive_hardlink(root)
        test_directory_flush(root)
        print("NTFS_SYNTHETIC_PRIMITIVES PASS")


if __name__ == "__main__":
    main()
