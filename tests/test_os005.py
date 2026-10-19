"""OS005 safety tests with synthetic files only."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from fluxor_core.plan import planejar, executar_plano, verificar_espaco, sha256_arquivo


def main():
    with TemporaryDirectory() as temp:
        p = Path(temp)
        origin, destination = p / "origin", p / "destination"
        origin.mkdir()
        destination.mkdir()
        (origin / "foto.jpg").write_bytes(b"payload")
        plan = planejar(origin, destination)
        assert verificar_espaco(plan)["necessario"] == 7
        result = executar_plano(plan)
        assert result["total_copiados"] == 1 and result["total_erros"] == 0
        copy = destination / "Fluxor_Organizado" / "Imagens" / "foto.jpg"
        assert sha256_arquivo(copy) == sha256_arquivo(origin / "foto.jpg")
        with patch("fluxor_core.plan.shutil.disk_usage") as disk:
            disk.return_value.free = 0
            try:
                verificar_espaco(plan)
            except OSError:
                pass
            else:
                raise AssertionError("Low capacity should reject")
        # Same size but different bytes must fail SHA integrity check.
        from unittest.mock import patch as patcher
        original_hash = sha256_arquivo
        with patcher("fluxor_core.plan.sha256_arquivo", side_effect=["a", "b"]):
            altered = executar_plano(plan)
        assert altered["total_copiados"] == 0
        assert altered["total_erros"] == 1
        assert not (destination / "Fluxor_Organizado" / "Imagens" / "foto (1).jpg").exists()
        assert (origin / "foto.jpg").read_bytes() == b"payload"
    print("OS005 safety tests passed")


if __name__ == "__main__":
    main()
