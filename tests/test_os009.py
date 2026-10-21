"""OS009 tests use only isolated synthetic paths."""
from pathlib import Path
from tempfile import TemporaryDirectory
from fluxor_core.plan import planejar, executar_plano

def main():
    with TemporaryDirectory() as temp:
        p = Path(temp)
        source, target = p/"source", p/"target"
        source.mkdir()
        target.mkdir()
        file = source/"big.txt"
        file.write_bytes(b"a" * (3 * 1024 * 1024))
        plan = planejar(source, target)
        count = [0]
        def cancel():
            count[0] += 1
            return count[0] >= 3
        result = executar_plano(plan, cancelar=cancel)
        assert result["cancelado"]
        assert result["total_copiados"] == 0
        assert file.exists()
        assert not (target/"Fluxor_Organizado"/"Textos"/"big.txt").exists()
        plan = planejar(source, target)
        file.write_bytes(b"changed")
        result = executar_plano(plan)
        assert result["total_erros"] == 1
        assert result["total_copiados"] == 0
        assert file.read_bytes() == b"changed"
    print("OS009 cancellation and stale plan safety passed")

if __name__ == "__main__":
    main()
