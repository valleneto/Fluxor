"""OS025-C: Windows executable startup check in an isolated synthetic profile.

Observed liveness is not certification, an installation test or proof of UI.
"""
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import time


def main():
    assert os.name == "nt"
    app = Path("dist/FLUXOR/FLUXOR.exe").resolve(strict=True)
    with TemporaryDirectory(prefix="fluxor-os025c-smoke-") as temp:
        env = os.environ.copy()
        env.update(USERPROFILE=temp, HOME=temp, QT_QPA_PLATFORM="offscreen",
                   PYTHONDONTWRITEBYTECODE="1")
        with open(Path(temp) / "stdout.txt", "wb") as out:
            with open(Path(temp) / "stderr.txt", "wb") as err:
                process = subprocess.Popen([str(app)], cwd=str(app.parent),
                                           env=env, stdout=out, stderr=err)
                try:
                    time.sleep(6)
                    if process.poll() is not None:
                        raise AssertionError(
                            "Premature FLUXOR.exe exit " + str(process.returncode))
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=8)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
    print("OS025-C EXE_STARTUP_LIVENESS_PASS (not a physical UI test)")


if __name__ == "__main__":
    main()
