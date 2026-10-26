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
python3 -c 'import PySide6; from PySide6.QtMultimedia import QMediaPlayer; from PySide6.QtMultimediaWidgets import QVideoWidget; print("PySide6 + Qt Multimedia OK")' || {
  echo "Qt Multimedia incompleto: verifique a instalação do PySide6 no ambiente virtual." >&2
  exit 1
}
python3 -m pip show pyinstaller >/dev/null || {
  echo "Instale PyInstaller no ambiente virtual: python3 -m pip install pyinstaller" >&2
  exit 1
}
python3 -m PyInstaller --noconfirm --clean --windowed --name "Fluxor Control" \
  --hidden-import PySide6.QtMultimedia \
  --hidden-import PySide6.QtMultimediaWidgets \
  --add-data "assets/fluxor_logo.png:assets" \
  --collect-submodules fluxor_core \
  fluxor_iniciar.py
echo "Build local gerado em dist/Fluxor Control.app"
echo "Ainda não assinado com Developer ID nem notarizado. Não distribuir publicamente."
