"""OS019 incremental organization: isolated copy, conflict, duplicate and safety tests."""
from pathlib import Path
from tempfile import TemporaryDirectory

from fluxor_core.plan import planejar, executar_plano, sha256_arquivo


def main():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = root / "first"
        incoming = root / "incoming"
        parent = root / "output"
        first.mkdir()
        incoming.mkdir()
        parent.mkdir()
        (first / "clip.mp4").write_bytes(b"original-video-A")
        (first / "memo.txt").write_bytes(b"keep-old-note")

        original_plan = planejar(first, parent, "Por tipo")
        original = executar_plano(original_plan)
        assert original["total_copiados"] == 2, original
        base = Path(original["destino_base"])
        assert base.is_dir()
        old_path = base / original_plan["arquivos"][0]["destino_relativo"]
        old_digest = sha256_arquivo(old_path)
        assert old_path.exists()

        # Same content with equal and different filenames must be ignored.
        (incoming / "clip.mp4").write_bytes(b"original-video-A")
        (incoming / "another.mp4").write_bytes(b"original-video-A")
        (incoming / "fresh.mp4").write_bytes(b"brand-new-video-B")
        preview = planejar(incoming, base, "Por tipo", acrescentar=True)
        assert preview["destino_base"] == str(base)
        assert preview["resumo_acrescimo"] == {
            "novos": 1, "ignorados_identicos": 2, "nomes_alternativos": 0
        }, preview["resumo_acrescimo"]
        assert [x["acao"] for x in preview["arquivos"]].count("ignorar_identico") == 2
        result = executar_plano(preview)
        assert result["total_copiados"] == 1, result
        assert result["total_ignorados"] == 2, result
        assert result["total_renomeados"] == 0
        assert sha256_arquivo(old_path) == old_digest
        assert not (base / "Fluxor_Organizado").exists(), "must not nest another output root"

        # A second import of the same folder is idempotent.
        again = planejar(incoming, base, "Por tipo", acrescentar=True)
        assert again["resumo_acrescimo"]["novos"] == 0
        again_result = executar_plano(again)
        assert again_result["total_copiados"] == 0
        assert again_result["total_ignorados"] == 3

        # Name collision but different bytes: preserve BOTH via suffix.
        (incoming / "clip.mp4").write_bytes(b"different-video-C")
        collision = planejar(incoming, base, "Por tipo", acrescentar=True)
        item = next(x for x in collision["arquivos"] if Path(x["origem"]).name == "clip.mp4")
        assert item["acao"] == "copiar"
        assert item["renomear"]
        assert "clip (1).mp4" in item["destino_previsto"]
        done = executar_plano(collision)
        assert done["total_copiados"] == 1
        assert done["total_renomeados"] == 1
        alt = Path(next(x["destino"] for x in done["arquivos"] if x["status"] == "copiado_renomeado"))
        assert alt.read_bytes() == b"different-video-C"
        assert sha256_arquivo(old_path) == old_digest

        # Two incoming names containing the same NEW bytes produce only one copy.
        batch = root / "batch"
        batch.mkdir()
        (batch / "sample-a.mp4").write_bytes(b"new-same-content-in-batch")
        (batch / "sample-b.mp4").write_bytes(b"new-same-content-in-batch")
        batch_preview = planejar(batch, base, "Por tipo", acrescentar=True)
        assert batch_preview["resumo_acrescimo"]["novos"] == 1, batch_preview
        assert batch_preview["resumo_acrescimo"]["ignorados_identicos"] == 1
        batch_result = executar_plano(batch_preview)
        assert batch_result["total_copiados"] == 1
        assert batch_result["total_ignorados"] == 1
        assert sha256_arquivo(old_path) == old_digest

        # Stale source snapshots must not be copied.
        (incoming / "newer.mov").write_bytes(b"timestamp-A")
        stale = planejar(incoming, base, "Por tipo", acrescentar=True)
        (incoming / "newer.mov").write_bytes(b"timestamp-B-new")
        fail = executar_plano(stale)
        assert fail["total_erros"] >= 1, fail
        assert not any(
            Path(x.get("destino", "")).name == "newer.mov"
            for x in fail["arquivos"] if x["status"].startswith("copiado")
        )

        # Reject wrong destination folder, overlap and linked category directories.
        try:
            planejar(incoming, parent, "Por tipo", acrescentar=True)
        except ValueError:
            pass
        else:
            raise AssertionError("must choose Fluxor_Organizado itself")
        try:
            planejar(incoming, base, "Por tipo", acrescentar=False)
        except ValueError:
            pass
        else:
            raise AssertionError("must reject nested Fluxor_Organizado")
        try:
            planejar(base, base, "Por tipo", acrescentar=True)
        except ValueError:
            pass
        else:
            raise AssertionError("source/destination overlap was allowed")

        external = root / "external-protected"
        external.mkdir()
        external_file = external / "untouched.txt"
        external_file.write_bytes(b"no-writes-here")
        special = root / "other-output" / "Fluxor_Organizado"
        special.mkdir(parents=True)
        # A category symlink should not be followed or copied into.
        txt_src = root / "txt"
        txt_src.mkdir()
        (txt_src / "new.txt").write_bytes(b"data")
        category = Path(planejar(txt_src, root / "another-parent", "Por tipo")["arquivos"][0]["destino_relativo"]).parent
        (special / category).symlink_to(external, target_is_directory=True)
        try:
            planejar(txt_src, special, "Por tipo", acrescentar=True)
        except ValueError:
            pass
        else:
            raise AssertionError("symlink destination category accepted")
        assert external_file.read_bytes() == b"no-writes-here"
        assert not (external / "new.txt").exists()

        # An invalid plan must not silently switch destination trees.
        bad = planejar(incoming, base, "Por tipo", acrescentar=True)
        bad["destino_base"] = str(parent)
        try:
            executar_plano(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("tampered output root accepted")

    print("OS019 incremental merge, SHA-256, collisions, stale plans and symlink safety passed")


if __name__ == "__main__":
    main()
