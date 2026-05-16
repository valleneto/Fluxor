import sys

def banner():
    print("""
========================
 FLUXOR MEMORY ENGINE
========================
""")

def help_menu():
    print("""
Comandos disponíveis:

scan        -> scanners
dedupe      -> detectar duplicadas
classify    -> classificar imagens
reports     -> relatórios
archive     -> processamento bruto
""")

def main():

    banner()

    if len(sys.argv) < 2:
        help_menu()
        return

    comando = sys.argv[1]

    if comando == "scan":
        print("Fluxor scan iniciado.")

    elif comando == "dedupe":
        print("Fluxor dedupe iniciado.")

    elif comando == "classify":
        print("Fluxor classify iniciado.")

    elif comando == "reports":
        print("Fluxor reports iniciado.")

    elif comando == "archive":
        print("Fluxor archive iniciado.")

    else:
        print("Comando desconhecido.")

if __name__ == "__main__":
    main()
