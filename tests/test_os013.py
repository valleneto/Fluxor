"""OS013 Zen visual state invariants; Qt-independent design policy checks."""
from pathlib import Path

def main():
    code = (Path(__file__).parents[1] / "fluxor_zen.py").read_text()
    assert "QPainter" in code and "QTimer" in code
    assert 'self.timer.setInterval(50)' in code
    assert "self.timer.stop()" in code
    assert 'self.reduced_motion = bool(enabled)' in code
    assert "QMovie" not in code and "QWebEngine" not in code
    assert "paintEvent" in code
    print("OS013 animation policy checks passed")

if __name__ == "__main__":
    main()
