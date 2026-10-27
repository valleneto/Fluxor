"""OS020: type+date categories, existing collection, cyclic links and large walks."""
import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from fluxor_core.plan import MODOS, planejar, executar_plano
from fluxor_core.library import index_folder


def set_date(file, year, month):
    t = datetime(year, month, 15, 12).timestamp()
    os.utime(file, (t, t))


def main():
    assert "Por tipo e ano" in MODOS
    assert "Por tipo, ano e mês" in MODOS
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        origin = root / "incoming"
        target = root / "target"
        (origin / "sub").mkdir(parents=True)
        target.mkdir()
        examples = [
            ("photo.jpg", "Imagens/2024/06/photo.jpg", 2024, 6),
            ("movie.mp4", "Videos/2024/06/movie.mp4", 2024, 6),
            ("song.wav", "Audio/2023/01/song.wav", 2023, 1),
            ("sheet.xlsx", "Planilhas/2025/12/sheet.xlsx", 2025, 12),
        ]
        for name, _, year, month in examples:
            p = origin / "sub" / name
            p.write_bytes(("content-" + name).encode())
            set_date(p, year, month)
        (origin / "sub" / "recursive").symlink_to(origin, target_is_directory=True)
        (origin / "Photos.app").mkdir()
        (origin / "Photos.app" / "hidden.jpg").write_bytes(b"skip app")
        plan = planejar(origin, target, "Por tipo, ano e mês")
        assert plan["total_arquivos"] == 4, plan
        assert {e["destino_relativo"] for e in plan["arquivos"]} == {
            dest for _, dest, _, _ in examples
        }
        report = executar_plano(plan)
        assert report["total_copiados"] == 4, report
        collection = Path(report["destino_base"])
        for name, expected, _, _ in examples:
            assert (collection / expected).read_bytes() == ("content-" + name).encode()
        yearly = planejar(origin, root / "other", "Por tipo e ano")
        assert {e["destino_relativo"] for e in yearly["arquivos"]} == {
            "Imagens/2024/photo.jpg", "Videos/2024/movie.mp4",
            "Audio/2023/song.wav", "Planilhas/2025/sheet.xlsx",
        }
        next_batch = root / "next"
        next_batch.mkdir()
        more_video = next_batch / "new.mov"
        more_video.write_bytes(b"extra video")
        set_date(more_video, 2024, 6)
        merge = planejar(next_batch, collection, "Por tipo, ano e mês", acrescentar=True)
        assert merge["resumo_acrescimo"]["novos"] == 1
        assert executar_plano(merge)["total_copiados"] == 1
        assert (collection / "Videos/2024/06/new.mov").exists()

        folder = root / "large"
        folder.mkdir()
        for n in range(84):
            (folder / f"{n:03d}.mp4").write_bytes(str(n).encode())
        progress = []
        p = planejar(folder, root / "large-output", "Por tipo e ano",
                     progresso=lambda number, total: progress.append((number, total)))
        assert p["total_arquivos"] == 84
        assert progress == [(40, 0), (80, 0)], progress

        db = root / "library.db"
        indexed = index_folder(origin, db)
        assert indexed["total"] == 4, indexed
        assert (origin / "sub" / "movie.mp4").read_bytes() == b"content-movie.mp4"

        deep = root / "deep"
        deep.mkdir()
        current = deep
        for i in range(45):
            current = current / f"d{i}"
            current.mkdir()
        (current / "hidden.mov").write_bytes(b"far away")
        limited = planejar(deep, root / "deep-output")
        assert limited["total_arquivos"] == 0
        assert any("Profundidade" in warning for warning in limited["avisos"])
    print("OS020 combined type/date, append, safe progress and cycles passed")


if __name__ == "__main__":
    main()
