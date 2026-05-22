import tkinter as tk
from tkinter import filedialog, messagebox
from core.safe_copy import safe_copy

arquivo_origem = ""
pasta_destino = ""

def escolher_arquivo():
    global arquivo_origem
    arquivo_origem = filedialog.askopenfilename(title="Escolha o arquivo para copiar")
    origem_label.config(text=arquivo_origem or "Nenhum arquivo escolhido")

def escolher_destino():
    global pasta_destino
    pasta_destino = filedialog.askdirectory(title="Escolha a pasta de destino")
    destino_label.config(text=pasta_destino or "Nenhuma pasta escolhida")

def copiar():
    if not arquivo_origem:
        messagebox.showerror("Erro", "Escolha um arquivo de origem.")
        return

    if not pasta_destino:
        messagebox.showerror("Erro", "Escolha uma pasta de destino.")
        return

    try:
        resultado = safe_copy(arquivo_origem, pasta_destino)
        messagebox.showinfo("Fluxor", f"Cópia segura concluída:\n{resultado}")
    except Exception as e:
        messagebox.showerror("Erro na cópia", str(e))

janela = tk.Tk()
janela.title("Fluxor")
janela.geometry("650x320")

titulo = tk.Label(janela, text="Fluxor Safe Copy", font=("Arial", 22, "bold"))
titulo.pack(pady=20)

btn_origem = tk.Button(janela, text="Escolher arquivo de origem", command=escolher_arquivo, height=2)
btn_origem.pack(pady=5)

origem_label = tk.Label(janela, text="Nenhum arquivo escolhido", wraplength=600)
origem_label.pack(pady=5)

btn_destino = tk.Button(janela, text="Escolher pasta de destino", command=escolher_destino, height=2)
btn_destino.pack(pady=5)

destino_label = tk.Label(janela, text="Nenhuma pasta escolhida", wraplength=600)
destino_label.pack(pady=5)

btn_copiar = tk.Button(janela, text="Copiar com segurança", command=copiar, height=2)
btn_copiar.pack(pady=20)

janela.mainloop()
