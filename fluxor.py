import sys
import subprocess

def banner():
    print("""
========================
 FLUXOR MEMORY ENGINE
========================
""")

def rodar(script):
    print(f"\n▶ Rodando: {script}\n")
    subprocess.run(["python3", script])

def main():
    banner()

    if len(sys.argv) < 2:
        print("Comandos disponíveis:")
        print("scan")
        print("dedupe")
        print("classify")
        print("reports")
        print("summary")
        print("space")
        print("organize")
        print("run")
        return

    comando = sys.argv[1]

    if comando == "scan":
        rodar("scanners/scanner_incremental.py")
    elif comando == "dedupe":
        rodar("dedupe/detectar_duplicadas.py")
    elif comando == "classify":
        rodar("classifiers/classificar_referencias.py")
    elif comando == "reports":
        rodar("reports/somar_exclusivos_por_tipo.py")
    elif comando == "summary":
        rodar("reports/summary.py")
    elif comando == "space":
        rodar("reports/analyze_space.py")
    elif comando == "organize":
        rodar("organize.py")
    elif comando == "run":
        rodar("organize.py")
    else:
        print("Comando desconhecido.")

if __name__ == "__main__":
    main()
