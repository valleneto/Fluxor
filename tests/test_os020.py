"""OS020: category/date composites and safe handling of cyclic/inaccessible folders."""
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os

from fluxor_core.plan import planejar, executar_plano, sha256_arquivo
from fluxor_core.classifier import classificar_arquivo


def main():
    with TemporaryDirectory() as td:
        root = Path(td)
        source = root / "source"
        target = root / "target"
        source.mkdir()
        target.mkdir()
        (source / "nested").mkdir()
        originals = [
            source / "photo.jpg",
            source / "nested" / "clip.mp4",
            source / "nested" / "memo.txt",
        ]
        for i, path in enumerate(originals):
            path.write_bytes(f"original-byte-content-{i}".encode())
            stamp = datetime(2024, 5, 16, 12, 0).timestamp()
            os.utime(path, (stamp, stamp))
        (source / "nested" / "back_to_source").symlink_to(
            source, target_is_directory=True
        )

        for mode, suffix in [
            ("Por tipo e ano", ("2024",)),
            ("Por tipo, ano e mês", ("2024", "05")),
        ]:
            plan = planejar(source, target, modo=mode)
            assert plan["total_arquivos"] == 3, plan
            assert not plan["avisos"], plan["avisos"]
            for item in plan["arquivos"]:
                filename = Path(item["origem"])
                assert Path(item["destino_relativo"]).parts == (
                    classificar_arquivo(filename), *suffix, filename.name
                )
            copies = executar_plano(plan)
            assert copies["total_copiados"] == 3, copies
            assert not copies["total_erros"]
            for item in plan["arquivos"]:
                src = Path(item["origem"])
                output = Path(plan["destino_base"]) / item["destino_relativo"]
                assert sha256_arquivo(src) == sha256_arquivo(output)
        # Content copies to the SAME group are skipped when appending.
        existing = target / "Fluxor_Organizado"
        second = root / "another_source"
        second.mkdir()
        (second / "new.mp4").write_bytes(b"a-second-video")
        os.utime(second / "new.mp4", (stamp, stamp))
        again = planejar(second, existing, "Por tipo, ano e mês", acrescentar=True)
        assert again["arquivos"][0]["destino_relativo"] == "Videos/2024/05/new.mp4"
        done = executar_plano(again)
        assert done["total_copiados"] == 1
        assert (existing / "Videos" / "2024" / "05" / "new.mp4").exists()

        # Restricted folders must report an error instead of silently returning 0.
        def fake_walk(root_path, followlinks, onerror):
            onerror(PermissionError(13, "Permission denied", str(source / "blocked")))
            yield str(source), [], ["photo.jpg"]
        with patch("fluxor_core.plan.os.walk", side_effect=fake_walk):
            partial = planejar(source, root / "another", "Por tipo e ano")
            assert partial["total_arquivos"] == 1
            assert any("blocked" in note and "inacessível" in note for note in partial["avisos"])

        # Symlink traversal is prevented; no duplicates from folder cycles.
        plan = planejar(source, root / "another2", "Por tipo, ano e mês")
        assert plan["total_arquivos"] == 3

    print("OS020 composite type/date layout, merge, integrity, symlink cycle and network errors passed")


if __name__ == "__main__":
    main()
