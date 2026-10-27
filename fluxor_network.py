"""Explicit network-volume selection for FLUXOR.

The app indexes mounted filesystem paths. SMB URLs are handed to the operating
system for mounting; FLUXOR never stores network credentials.
"""
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox


def select_network_folder(parent, caption="Escolher pasta na rede"):
    # macOS mounts SMB volumes beneath /Volumes; scan a *selected subfolder*,
    # never the entire /Volumes directory by accident.
    initial = "/Volumes" if sys.platform == "darwin" else str(Path.home())
    folder = QFileDialog.getExistingDirectory(parent, caption, initial)
    if sys.platform == "darwin" and folder and Path(folder).resolve() == Path("/Volumes"):
        QMessageBox.warning(parent, "Escolha uma unidade", "Selecione uma pasta dentro de um volume montado, não a pasta /Volumes inteira.")
        return ""
    return folder


def connect_smb(parent):
    """Ask Finder to mount an SMB server; authentication stays with macOS."""
    if sys.platform != "darwin":
        QMessageBox.information(parent, "Conexão SMB", "No Windows, conecte a pasta compartilhada pelo Explorador e selecione-a no FLUXOR.")
        return False
    value, ok = QInputDialog.getText(parent, "Conectar à rede", "Servidor SMB (ex.: smb://192.168.0.27):")
    if not ok or not value.strip():
        return False
    url = value.strip()
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "smb" or not parsed.hostname or parsed.username or parsed.password:
        QMessageBox.warning(parent, "Endereço inválido", "Use smb://servidor/compartilhamento, sem usuário ou senha no endereço.")
        return False
    try:
        subprocess.Popen(["open", url])
    except OSError as error:
        QMessageBox.warning(parent, "Não foi possível abrir o servidor", str(error))
        return False
    QMessageBox.information(parent, "Conexão no Finder", "Depois de montar o compartilhamento no Finder, use 'Pasta da rede' e selecione a unidade em /Volumes.")
    return True
