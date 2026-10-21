from pathlib import Path
from tempfile import TemporaryDirectory

from fluxor_core.organizer import organizar_por_tipo


def main():
    with TemporaryDirectory(prefix="fluxor_test_") as temp:
        origem = Path(temp) / "origem"
        destino = Path(temp) / "destino"
        origem.mkdir()
        destino.mkdir()
        arquivos = {
            "foto.png": "imagem fake",
            "video.mp4": "video fake",
            "contrato.pdf": "pdf fake",
            "backup.zip": "zip fake",
            "arquivo.xyz": "arquivo desconhecido",
        }
        for nome, conteudo in arquivos.items():
            (origem / nome).write_text(conteudo, encoding="utf-8")
        resultado = organizar_por_tipo(origem, destino)
        assert resultado["total_copiados"] == 5
        assert resultado["total_erros"] == 0
        base = Path(resultado["destino_base"])
        for categoria, nome in (
            ("Imagens", "foto.png"), ("Videos", "video.mp4"),
            ("PDFs", "contrato.pdf"), ("Compactados", "backup.zip"),
            ("Outros", "arquivo.xyz"),
        ):
            assert (base / categoria / nome).read_text(encoding="utf-8") == arquivos[nome]
            assert (origem / nome).read_text(encoding="utf-8") == arquivos[nome]
        print("Teste do organizer passou com sucesso.")


if __name__ == "__main__":
    main()
