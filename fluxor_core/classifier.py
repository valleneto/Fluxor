from pathlib import Path


CATEGORIAS = {
    "Imagens": [".jpg", ".jpeg", ".png", ".heic", ".webp", ".gif", ".bmp"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".m4a"],
    "PDFs": [".pdf"],
    "Documentos": [".doc", ".docx", ".txt", ".rtf", ".pages"],
    "Planilhas": [".xls", ".xlsx", ".csv"],
    "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Apps": [".dmg", ".pkg", ".app"],
}


def classificar_arquivo(caminho_arquivo):
    caminho = Path(caminho_arquivo)
    extensao = caminho.suffix.lower()

    for categoria, extensoes in CATEGORIAS.items():
        if extensao in extensoes:
            return categoria

    return "Outros"


def obter_extensao(caminho_arquivo):
    caminho = Path(caminho_arquivo)
    extensao = caminho.suffix.lower().replace(".", "")

    if not extensao:
        return "Sem_Extensao"

    return extensao.upper()
