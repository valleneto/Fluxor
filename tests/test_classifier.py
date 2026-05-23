from pathlib import Path

from fluxor_core.classifier import classificar_arquivo, obter_extensao


def main():
    arquivos = [
        "foto.png",
        "video.mp4",
        "musica.mp3",
        "contrato.pdf",
        "texto.docx",
        "planilha.xlsx",
        "backup.zip",
        "instalador.dmg",
        "arquivo_misterioso.xyz",
        "arquivo_sem_extensao",
    ]

    for arquivo in arquivos:
        categoria = classificar_arquivo(Path(arquivo))
        extensao = obter_extensao(Path(arquivo))

        print(f"{arquivo} -> {categoria} / {extensao}")


if __name__ == "__main__":
    main()
