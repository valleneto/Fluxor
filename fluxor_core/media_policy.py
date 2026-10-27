"""Conservative, local-only policies for on-demand visual previews."""
from pathlib import Path

VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"})
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".heic"})
DOCUMENT_EXTENSIONS = frozenset({".pdf", ".doc", ".docx", ".rtf", ".odt", ".pages"})


def media_kind(path):
    suffix = Path(path).suffix.casefold()
    return ("video" if suffix in VIDEO_EXTENSIONS else
            "image" if suffix in IMAGE_EXTENSIONS else
            "document" if suffix in DOCUMENT_EXTENSIONS else "other")


def cloud_risk(path):
    """Conservative heuristic, not an OS-level guarantee of local availability."""
    parts = set(Path(path).expanduser().parts)
    return bool(parts & {"CloudStorage", "Mobile Documents", "File Provider Storage"})


def preview_allowed(path):
    """Do not resolve or read content here; local file validation in UI on demand."""
    item = Path(path).expanduser()
    return media_kind(item) != "other" and not cloud_risk(item) and not item.is_symlink() and item.is_file()
