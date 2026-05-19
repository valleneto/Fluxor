from pathlib import Path
import shutil
import hashlib

def hash_file(path):
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            sha.update(block)
    return sha.hexdigest()

def safe_copy(source, destination_folder):
    source = Path(source)
    destination_folder = Path(destination_folder)
    destination_folder.mkdir(parents=True, exist_ok=True)

    destination = destination_folder / source.name

    counter = 1
    while destination.exists():
        destination = destination_folder / f"{source.stem}_{counter}{source.suffix}"
        counter += 1

    shutil.copy2(source, destination)

    if source.stat().st_size != destination.stat().st_size:
        raise Exception("Falha: tamanho diferente após cópia.")

    if hash_file(source) != hash_file(destination):
        raise Exception("Falha: hash diferente após cópia.")

    print(f"Cópia segura OK: {destination}")
    return destination
