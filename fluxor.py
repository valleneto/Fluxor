import sys
import json
import subprocess
from pathlib import Path

CONFIG_PATH = Path("config.json")

def carregar_config():
    if not CONFIG_PATH.exists():
        print("config.json não encontrado.")
        return None

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def banner():
    print("""
========================
 FLUXOR MEMORY ENGINE
========================
""")

def rodar(script):
    print(f"\n▶ Rodando: {script}\n")
    subprocess.run(["python3", script])

def help_menu():
    print("""
Comandos:

config
scan
dedupe
classify
reports
run
""")

def main():

    banner()

    config = carregar_config()

    if len(sys.argv) < 2:
        help_menu()
        return

    comando = sys.argv[1]

    if comando == "config":

        print(json.dumps(config, indent=2, ensure_ascii=False))

    elif comando == "scan":

        print("Fluxor scan iniciado.")
        rodar("scanners/scanner_fotos.py")

    elif comando == "dedupe":

        rodar("dedupe/detectar_duplicadas.py")

    elif comando == "classify":

        rodar("classifiers/classificar_referencias.py")

    elif comando == "reports":

        rodar("reports/somar_exclusivos_por_tipo.py")

    elif comando == "run":

        print("Fluxor RUN iniciado.\n")

        rodar("scanners/scanner_fotos.py")
        rodar("dedupe/detectar_duplicadas.py")
        rodar("classifiers/classificar_referencias.py")
        rodar("reports/somar_exclusivos_por_tipo.py")

        print("\nFluxor RUN finalizado.")

    else:

        print("Comando desconhecido.")

if __name__ == "__main__":
    main()
