import sys
from tkinter import ttk

CORES = {
    "fundo": "#f4f5f7",
    "painel": "#ffffff",
    "primaria": "#1f4e79",
    "primaria_hover": "#2b6aa3",
    "texto": "#222222",
    "texto_suave": "#666666",
    "borda": "#d0d4da",
    "cabecalho_tabela": "#e3e8ef",
    "destaque_linha": "#fff4cc",
    "destaque_pivo": "#f4b183",
    "linha_objetivo": "#eef3f8",
    "sucesso": "#2e7d32",
    "alerta": "#c77700",
    "erro": "#c62828",
}

# No Windows usamos as fontes padrão do sistema; no Linux, as DejaVu.
FAMILIA = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"
FAMILIA_MONO = "Consolas" if sys.platform == "win32" else "DejaVu Sans Mono"

FONTE_PADRAO = (FAMILIA, 10)
FONTE_NEGRITO = (FAMILIA, 10, "bold")
FONTE_TITULO = (FAMILIA, 18, "bold")
FONTE_SUBTITULO = (FAMILIA, 10)
FONTE_SECAO = (FAMILIA, 12, "bold")
FONTE_MONO = (FAMILIA_MONO, 11)


# Configura os estilos ttk usados pelos componentes da aplicação.
def aplicar_estilos(raiz):
    raiz.configure(bg=CORES["fundo"])
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")

    estilo.configure(".", font=FONTE_PADRAO, background=CORES["fundo"], foreground=CORES["texto"])
    estilo.configure("TFrame", background=CORES["fundo"])
    estilo.configure("Painel.TFrame", background=CORES["painel"])
    estilo.configure("TLabel", background=CORES["fundo"])
    estilo.configure("Painel.TLabel", background=CORES["painel"])
    estilo.configure("Dica.TLabel", background=CORES["fundo"], foreground=CORES["texto_suave"])
    estilo.configure("Secao.TLabel", font=FONTE_SECAO, background=CORES["fundo"])

    estilo.configure("TLabelframe", background=CORES["fundo"], bordercolor=CORES["borda"])
    estilo.configure("TLabelframe.Label", font=FONTE_NEGRITO, background=CORES["fundo"],
                     foreground=CORES["primaria"])
    estilo.configure("TRadiobutton", background=CORES["fundo"])

    estilo.configure("Cabecalho.TFrame", background=CORES["primaria"])
    estilo.configure("Titulo.TLabel", font=FONTE_TITULO, background=CORES["primaria"],
                     foreground="white")
    estilo.configure("Subtitulo.TLabel", font=FONTE_SUBTITULO, background=CORES["primaria"],
                     foreground="#d6e4f0")

    estilo.configure("Primario.TButton", font=FONTE_NEGRITO, background=CORES["primaria"],
                     foreground="white", padding=(14, 6))
    estilo.map("Primario.TButton", background=[("active", CORES["primaria_hover"])])
    estilo.configure("TButton", padding=(10, 5))

    estilo.configure("TNotebook", background=CORES["fundo"])
    estilo.configure("TNotebook.Tab", padding=(14, 6))
    estilo.configure("Treeview", rowheight=24)
    estilo.configure("Treeview.Heading", font=FONTE_NEGRITO)
