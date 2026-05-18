import subprocess

print("\nFLUXOR ORGANIZE\n")

etapas = [
    "scanners/scanner_incremental.py",
    "dedupe/detectar_duplicadas.py",
    "classifiers/classificar_referencias.py"
]

for etapa in etapas:

    print(f"\n▶ Executando: {etapa}\n")

    subprocess.run(["python3", etapa])

print("\nFluxor organize finalizado.\n")
