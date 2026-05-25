from pathlib import Path
import shutil

from fluxor_core.organizer import organizar_por_tipo


def preparar_arquivos_teste():
    origem = Path("sandbox/origem")
    destino = Path("sandbox/destino")

    if origem.exists():
        shutil.rmtree(origem)

    if destino.exists():
        shutil.rmtree(destino)

    origem.mkdir(parents=True, exist_ok=True)
    destino.mkdir(parents=True, exist_ok=True)

    arquivos = {
        "foto.png": "imagem fake",
        "video.mp4": "video fake",
        "contrato.pdf": "pdf fake",
        "backup.zip": "zip fake",
        "arquivo.xyz": "arquivo desconhecido",
    }

    for nome, conteudo in arquivos.items():
        caminho = origem / nome
        caminho.write_text(conteudo, encoding="utf-8")

    return origem, destino


def main():
    origem, destino = preparar_arquivos_teste()

    resultado = organizar_por_tipo(origem, destino)

    print("Destino base:", resultado["destino_base"])
    print("Total copiados:", resultado["total_copiados"])
    print()

    for item in resultado["arquivos"]:
        print(f"{item['origem']} -> {item['destino']} [{item['categoria']}]")

    assert resultado["total_copiados"] == 5

    destino_base = Path(resultado["destino_base"])

    assert (destino_base / "Imagens" / "foto.png").exists()
    assert (destino_base / "Videos" / "video.mp4").exists()
    assert (destino_base / "PDFs" / "contrato.pdf").exists()
    assert (destino_base / "Compactados" / "backup.zip").exists()
    assert (destino_base / "Outros" / "arquivo.xyz").exists()

    print()
    print("Teste do organizer passou com sucesso.")


if __name__ == "__main__":
    main()
