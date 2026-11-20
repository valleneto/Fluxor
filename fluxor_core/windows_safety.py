"""OS025-C: conservative Windows reparse/volume gate (synthetic CI).

Blocks paths through junctions, symlinks and reparse points on Windows.
For beta writing, only fixed local NTFS volumes are eligible. SMB, removable
drives and other filesystems stay out of scope pending separate validation.
This is NOT a proof against hostile concurrent filesystem mutations / TOCTOU.
POSIX behavior remains unchanged.
"""
import ctypes
import os
from pathlib import Path
import stat


def reject_windows_reparse(path):
    """Fail closed on an existing reparse component, including NTFS junctions."""
    if os.name != "nt":
        return
    item = Path(path).absolute()
    # Check the user-supplied spelling BEFORE calling Path.resolve(); that
    # would otherwise erase evidence of a junction path.
    for component in (item, *item.parents):
        try:
            metadata = component.lstat()
        except FileNotFoundError:
            continue
        flags = getattr(metadata, "st_file_attributes", 0)
        if flags & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            raise OSError("Windows reparse point/junction bloqueado: " + str(component))


def require_local_ntfs(path):
    """Only allow local, fixed NTFS in the Windows pre-release write pipeline."""
    if os.name != "nt":
        return
    target = Path(path)
    original = str(target)
    if original.startswith("\\\\") or not target.is_absolute():
        raise OSError("Beta Windows: UNC/rede ou caminho relativo bloqueado.")
    root = target.anchor
    if not root or root.startswith("\\\\"):
        raise OSError("Beta Windows: volume remoto não homologado.")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
    kernel.GetDriveTypeW.restype = ctypes.c_uint32
    if kernel.GetDriveTypeW(root) != 3:  # DRIVE_FIXED only
        raise OSError("Beta Windows: apenas disco local fixo NTFS homologado.")
    kernel.GetVolumeInformationW.argtypes = [
        ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_wchar_p, ctypes.c_uint32,
    ]
    kernel.GetVolumeInformationW.restype = ctypes.c_int
    fs = ctypes.create_unicode_buffer(32)
    ok = kernel.GetVolumeInformationW(root, None, 0, None, None, None,
                                      fs, len(fs))
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    if fs.value.upper() != "NTFS":
        raise OSError("Beta Windows: filesystem não-NTFS bloqueado: " + fs.value)
    reject_windows_reparse(target)
