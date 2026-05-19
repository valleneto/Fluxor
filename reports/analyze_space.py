from pathlib import Path
import shutil
import json

CONFIG = Path("config.json")

with open(CONFIG, "r", encoding="utf-8") as f:
    config = json.load(f)

source = Path(config["source"])
destination = Path(config["destination"])

def tamanho_pasta(path):
    total = 0
    for arquivo in path.rglob("*"):
        if arquivo.is_file():
            try:
                total += arquivo.stat().st_size
            except:
                pass
    return total

def gb(bytes_value):
    return round(bytes_value / 1024 / 1024 / 1024, 2)

source_size = tamanho_pasta(source)

destino_base = destination.parent
free_space = shutil.disk_usage(destino_base).free

print("\nFLUXOR SPACE REPORT")
print("-------------------")
print(f"Origem: {source}")
print(f"Destino: {destination}")
print(f"Tamanho da origem: {gb(source_size)} GB")
print(f"Espaço livre no destino: {gb(free_space)} GB")

if free_space > source_size:
    print("Status: OK — há espaço suficiente.")
else:
    falta = source_size - free_space
    print(f"Status: INSUFICIENTE — faltam {gb(falta)} GB.")
    print("Sugestão: conectar HD externo com mais espaço livre.")
