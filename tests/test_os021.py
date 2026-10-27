"""OS021: critérios ordenáveis, bloqueio de prévia parcial e política persistida.
Apenas fixtures temporárias; nunca toca arquivos do usuário.
"""
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import os

from fluxor_core.criteria import normalizar_modo, conferir_politica, MARCADOR
from fluxor_core.plan import planejar, executar_plano, sha256_arquivo


def must_fail(action, label):
    try:
        action()
    except (ValueError, OSError):
        return
    raise AssertionError(label)


def main():
    assert normalizar_modo("Combinar: Tipo > Ano/mês") == ("Tipo", "Ano/mês")
    assert normalizar_modo("Combinar: Ano/mês > Tipo") == ("Ano/mês", "Tipo")
    for bad in ("Combinar: Tipo > Tipo", "Combinar: Ano > Ano/mês",
                "Combinar: Inexistente", "Combinar: ", "Combinar: Tipo > Extensão > Ano > Mês"):
        must_fail(lambda b=bad: normalizar_modo(b), bad)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "src"
        source.mkdir()
        photo = source / "foto.jpg"
        movie = source / "video.mp4"
        photo.write_bytes(b"foto-fixture")
        movie.write_bytes(b"video-fixture")
        ts = datetime(2024, 5, 16, 12).timestamp()
        os.utime(photo, (ts, ts))
        os.utime(movie, (ts, ts))

        for index, (mode, expected) in enumerate((
            ("Combinar: Tipo > Ano/mês", ("Imagens/2024/05/foto.jpg", "Videos/2024/05/video.mp4")),
            ("Combinar: Ano/mês > Tipo", ("2024/05/Imagens/foto.jpg", "2024/05/Videos/video.mp4")),
            ("Combinar: Extensão > Tipo > Ano", ("JPG/Imagens/2024/foto.jpg", "MP4/Videos/2024/video.mp4")),
        )):
            out = root / f"target_{index}"
            plan = planejar(source, out, mode)
            assert plan["completa"] and not plan["bloqueios"], plan
            assert {x["destino_relativo"] for x in plan["arquivos"]} == set(expected)
            result = executar_plano(plan)
            assert result["total_copiados"] == 2 and result["total_erros"] == 0, result
            base = Path(result["destino_base"])
            assert (base / MARCADOR).is_file()
            assert conferir_politica(base, mode)
            for input_file, expected_path in zip((photo, movie), expected):
                assert sha256_arquivo(input_file) == sha256_arquivo(base / expected_path)
            must_fail(lambda: planejar(source, out, "Por tipo"), "mixed modes accepted")
            must_fail(lambda: planejar(source, base, "Por tipo", acrescentar=True), "mixed append accepted")
            same = planejar(source, base, mode, acrescentar=True)
            assert same["resumo_acrescimo"]["ignorados_identicos"] == 2
            assert executar_plano(same)["total_ignorados"] == 2

        # A deliberately incomplete inventory is NEVER executable.
        deep = root / "very_deep"
        deep.mkdir()
        current = deep
        for i in range(45):
            current = current / f"level{i}"
            current.mkdir()
        (current / "hidden.mov").write_bytes(b"deep-fixture")
        blocked_target = root / "blocked_target"
        incomplete = planejar(deep, blocked_target)
        assert not incomplete["completa"] and incomplete["bloqueios"], incomplete
        must_fail(lambda: executar_plano(incomplete), "incomplete plan executed")
        assert not (blocked_target / "Fluxor_Organizado").exists()
        assert photo.read_bytes() == b"foto-fixture"
        assert movie.read_bytes() == b"video-fixture"
    print("OS021 ordered criteria, persistent mode, integrity and incomplete preview passed")


if __name__ == "__main__":
    main()
