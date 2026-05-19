import subprocess
import time
from datetime import datetime
from pathlib import Path

inicio = time.time()

log_path = Path("logs/ultimo_run.txt")

etapas = [
    "scanners/scanner_incremental.py",
    "dedupe/detectar_duplicadas.py",
    "classifiers/classificar_referencias.py"
]

with open(log_path, "w", encoding="utf-8") as log:

    log.write("FLUXOR ORGANIZE LOG\n")
    log.write(f"Início: {datetime.now()}\n\n")

    print("\nFLUXOR ORGANIZE\n")

    for etapa in etapas:

        print(f"\n▶ Executando: {etapa}\n")

        log.write(f"Executando: {etapa}\n")

        resultado = subprocess.run(
            ["python3", etapa],
            capture_output=True,
            text=True
        )

        log.write(resultado.stdout)
        log.write("\n")

        if resultado.stderr:
            log.write("ERROS:\n")
            log.write(resultado.stderr)
            log.write("\n")

    fim = time.time()

    duracao = round((fim - inicio) / 60, 2)

    log.write(f"\nDuração total: {duracao} minutos\n")

print("\nFluxor organize finalizado.")
print(f"Log salvo em: {log_path}\n")
