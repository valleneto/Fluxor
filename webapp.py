from flask import Flask, render_template, request
from pathlib import Path
import subprocess
import shutil

app = Flask(__name__)

def gb(n):
    return round(n / 1024 / 1024 / 1024, 2)

@app.route("/", methods=["GET", "POST"])
def index():

    mensagem = ""

    origem = request.form.get("origem", "")
    destino = request.form.get("destino", "")

    volumes = [str(p) for p in Path("/Volumes").iterdir() if p.is_dir()]

    atalhos = [
        str(Path.home() / "Projetos"),
        str(Path.home() / "Desktop"),
        str(Path.home() / "Downloads"),
    ] + volumes

    if request.method == "POST":

        acao = request.form.get("acao")

        if acao == "analisar":

            try:

                origem_path = Path(origem)
                destino_path = Path(destino)

                total = 0

                for f in origem_path.rglob("*"):

                    if f.is_file():

                        try:
                            total += f.stat().st_size
                        except:
                            pass

                livre = shutil.disk_usage(destino_path).free

                if livre >= total:

                    mensagem = f"""
OK:
Origem: {gb(total)} GB
Destino livre: {gb(livre)} GB
"""

                else:

                    mensagem = f"""
INSUFICIENTE:
Origem: {gb(total)} GB
Destino livre: {gb(livre)} GB
Faltam: {gb(total-livre)} GB
"""

            except Exception as e:

                mensagem = f"Erro ao analisar: {e}"

        elif acao == "organizar":

            try:

                resultado = subprocess.run(
                    ["python3", "organize.py"],
                    capture_output=True,
                    text=True
                )

                mensagem = "Fluxor organize finalizado."

            except Exception as e:

                mensagem = f"Erro: {e}"

        elif acao == "abrir_origem":

            subprocess.run(["open", origem])

            mensagem = "Origem aberta no Finder."

        elif acao == "abrir_destino":

            subprocess.run(["open", destino])

            mensagem = "Destino aberto no Finder."

    return render_template(
        "index.html",
        mensagem=mensagem,
        origem=origem,
        destino=destino,
        atalhos=atalhos
    )

if __name__ == "__main__":
    app.run(debug=True)
