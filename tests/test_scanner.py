from pathlib import Path

from fluxor_core.scanner import escanear_pasta


def main():
    resultado = escanear_pasta(Path("sandbox/origem"))

    print("Pasta analisada:", resultado["pasta"])
    print("Total de arquivos:", resultado["total_arquivos"])
    print("Tamanho total:", resultado["tamanho_total"], "bytes")
    print()

    print("Resumo por categoria:")
    for categoria, quantidade in resultado["resumo"].items():
        print(f"- {categoria}: {quantidade}")

    print()
    print("Arquivos encontrados:")
    for arquivo in resultado["arquivos"]:
        print(f"- {arquivo['nome']} -> {arquivo['categoria']}")


if __name__ == "__main__":
    main()
