from pathlib import Path
from tempfile import TemporaryDirectory

from fluxor_core.plan import planejar, executar_plano


def executar_testes():
    with TemporaryDirectory() as temp:
        raiz = Path(temp)
        origem = raiz / "origem"
        destino = raiz / "destino"
        (origem / "sub").mkdir(parents=True)
        (origem / "foto.png").write_bytes(b"1234")
        (origem / "sub" / "foto.png").write_bytes(b"5678")
        (origem / "sub" / "notas.txt").write_bytes(b"texto")
        (origem / "sub" / "atalho.png").symlink_to(origem / "foto.png")
        (origem / "Photos.app").mkdir()
        (origem / "Photos.app" / "interno.txt").write_bytes(b"ignorar")

        for modo in ("Por tipo", "Por extensão", "Por ano", "Por ano e mês"):
            plano = planejar(origem, destino, modo)
            assert plano["total_arquivos"] == 3, (modo, plano)
            assert plano["tamanho_total"] == 13
            assert len(plano["arquivos"]) == 3
            resultado = executar_plano(plano)
            assert resultado["total_copiados"] == 3, resultado
            assert resultado["total_erros"] == 0, resultado
            for item in plano["arquivos"]:
                assert Path(item["origem"]).exists()
            print("OK:", modo)

        plano = planejar(origem, destino, "Por tipo", recursivo=False)
        assert plano["total_arquivos"] == 1
        assert len(plano["arquivos"]) == 1
        cancelamentos = []
        plano = planejar(origem, destino)
        parcial = executar_plano(
            plano,
            progresso=lambda atual, total: cancelamentos.append(atual),
            cancelar=lambda: len(cancelamentos) >= 1,
        )
        assert parcial["cancelado"] and parcial["total_copiados"] == 1
        print("OK: recursividade opcional e cancelamento")

        try:
            planejar(origem, origem / "saida")
        except ValueError:
            print("OK: bloqueio de destino interno")
        else:
            raise AssertionError("Destino dentro da origem permitido")

        print("TESTES DO PLANO APROVADOS")


if __name__ == "__main__":
    executar_testes()
