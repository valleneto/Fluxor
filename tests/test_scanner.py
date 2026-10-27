from pathlib import Path
from tempfile import TemporaryDirectory

from fluxor_core.scanner import escanear_pasta


def main():
    with TemporaryDirectory(prefix="fluxor_scan_") as temp:
        origem = Path(temp) / "origem"
        origem.mkdir()
        (origem / "foto.png").write_bytes(b"abc")
        (origem / "contrato.pdf").write_bytes(b"de")
        (origem / "subpasta").mkdir()
        (origem / "subpasta" / "ignorar.mp3").write_bytes(b"x")

        resultado = escanear_pasta(origem)
        assert resultado["total_arquivos"] == 2
        assert resultado["tamanho_total"] == 5
        assert resultado["resumo"] == {"Imagens": 1, "PDFs": 1}
        assert {a["nome"] for a in resultado["arquivos"]} == {"foto.png", "contrato.pdf"}
        print("Teste do scanner passou com sucesso.")


if __name__ == "__main__":
    main()
