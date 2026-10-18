from pathlib import Path
from tempfile import TemporaryDirectory

from fluxor_core.organizer import organizar_por_tipo


def testar_destino_interno():
    with TemporaryDirectory() as temp:
        origem = Path(temp) / "origem"
        origem.mkdir()
        (origem / "foto.png").write_bytes(b"original")
        destino = origem / "saida"

        try:
            organizar_por_tipo(origem, destino)
        except ValueError:
            assert not destino.exists()
        else:
            raise AssertionError("Destino dentro da origem foi permitido")


def testar_origem_dentro_do_destino():
    with TemporaryDirectory() as temp:
        raiz = Path(temp)
        destino = raiz / "arquivos"
        origem = destino / "entrada"
        origem.mkdir(parents=True)
        (origem / "foto.png").write_bytes(b"original")
        try:
            organizar_por_tipo(origem, destino)
        except ValueError:
            pass
        else:
            raise AssertionError("Origem dentro do destino foi permitida")


def testar_copia_sem_sobrescrita():
    with TemporaryDirectory() as temp:
        raiz = Path(temp)
        origem = raiz / "origem"
        destino = raiz / "destino"
        origem.mkdir()
        destino.mkdir()
        (origem / "foto.png").write_bytes(b"original")

        organizar_por_tipo(origem, destino)
        organizar_por_tipo(origem, destino)

        pasta = destino / "Fluxor_Organizado" / "Imagens"
        assert (pasta / "foto.png").read_bytes() == b"original"
        assert (pasta / "foto (1).png").read_bytes() == b"original"
        assert (origem / "foto.png").read_bytes() == b"original"


def testar_arquivo_inexistente():
    with TemporaryDirectory() as temp:
        raiz = Path(temp)
        try:
            organizar_por_tipo(raiz / "inexistente", raiz / "destino")
        except ValueError:
            assert not (raiz / "destino").exists()
        else:
            raise AssertionError("Origem inexistente foi permitida")


if __name__ == "__main__":
    for teste in (
        testar_destino_interno,
        testar_origem_dentro_do_destino,
        testar_copia_sem_sobrescrita,
        testar_arquivo_inexistente,
    ):
        teste()
        print("OK:", teste.__name__)
    print("TESTES DE SEGURANCA APROVADOS")
