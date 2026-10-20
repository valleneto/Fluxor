#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Este build exige macOS" >&2
  exit 1
fi
if [[ ! -d ".venv" ]]; then
  echo "Crie o .venv e instale PySide6 primeiro" >&2
  exit 1
fi
source .venv/bin/activate
python3 -c 'import PySide6; print("PySide6 OK")'
python3 -m pip show pyinstaller >/dev/null || {
  echo "Instale PyInstaller no ambiente virtual: python3 -m pip install pyinstaller" >&2
  exit 1
}
python3 -m PyInstaller --noconfirm --clean --windowed --name "Fluxor Control" \
  --collect-submodules fluxor_core \
  fluxor_iniciar.py
echo "Build criado em dist/Fluxor Control.app (ainda nao assinado)."
