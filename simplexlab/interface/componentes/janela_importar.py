import queue
import shutil
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from PIL import Image, ImageGrab, ImageTk

from simplexlab.gerador_pl import ErroIA, gerar_pl
from simplexlab.interface.estilos import CORES, FONTE_MONO

DICA = (
    "Cole o enunciado completo: texto, imagem (print da questão) ou os dois.\n"
    "Ctrl+V na caixa cola texto ou imagem. O PL é gerado pelo Codex da sua conta do ChatGPT."
)
TIPOS_IMAGEM = [("Imagens", "*.png *.jpg *.jpeg *.webp *.gif *.bmp"), ("Todos os arquivos", "*")]
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
TAMANHO_MINIATURA = (160, 110)


# Janela para importar um enunciado e gerar o modelo de PL com IA. Quando o
# modelo fica pronto, chama ao_gerar(ModeloGerado) e fecha.
# A chamada ao Codex roda em outra thread para a tela não travar.
class JanelaImportar(tk.Toplevel):

    def __init__(self, mestre, ao_gerar):
        super().__init__(mestre)
        self._ao_gerar = ao_gerar
        self._imagens = []
        self._miniaturas = []
        self._pasta = Path(tempfile.mkdtemp(prefix="simplexlab_imagens_"))
        self._fila = queue.Queue()
        self._processo = None
        self._gerando = False

        self.title("Importar enunciado com IA")
        self.configure(bg=CORES["fundo"])
        self._centralizar(mestre, 720, 560)
        self.minsize(560, 440)
        self.transient(mestre)
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

        self._montar_layout()
        self.texto.focus_set()
        self.grab_set()

    # Abre a janela no meio da janela principal.
    def _centralizar(self, mestre, largura, altura):
        mestre.update_idletasks()
        x = mestre.winfo_rootx() + max(0, (mestre.winfo_width() - largura) // 2)
        y = mestre.winfo_rooty() + max(0, (mestre.winfo_height() - altura) // 2)
        self.geometry(f"{largura}x{altura}+{x}+{y}")

    # Cria a caixa de texto, a área das imagens e os botões.
    def _montar_layout(self):
        corpo = ttk.Frame(self, padding=14)
        corpo.pack(fill="both", expand=True)

        ttk.Label(corpo, text=DICA, style="Dica.TLabel", justify="left").pack(anchor="w")

        self.texto = tk.Text(
            corpo, font=FONTE_MONO, height=10, wrap="word", undo=True, relief="solid",
            borderwidth=1, highlightthickness=0, bg=CORES["painel"], padx=8, pady=6,
        )
        self.texto.pack(fill="both", expand=True, pady=(8, 8))
        self.texto.bind("<<Paste>>", self._ao_colar)

        barra_imagens = ttk.Frame(corpo)
        barra_imagens.pack(fill="x")
        ttk.Button(barra_imagens, text="Colar imagem", command=self._colar_imagem).pack(side="left")
        ttk.Button(barra_imagens, text="Escolher imagem...", command=self._escolher_imagem).pack(
            side="left", padx=(8, 0)
        )
        self.botao_remover = ttk.Button(barra_imagens, text="Remover imagens",
                                        command=self._remover_imagens)
        self.botao_remover.pack(side="left", padx=(8, 0))

        self.area_miniaturas = ttk.Frame(corpo)
        self.area_miniaturas.pack(fill="x", pady=(8, 0))

        self.progresso = ttk.Progressbar(corpo, mode="indeterminate")
        self.status = ttk.Label(corpo, text="", style="Dica.TLabel", wraplength=660, justify="left")
        self.status.pack(anchor="w", pady=(8, 0))

        botoes = ttk.Frame(corpo)
        botoes.pack(fill="x", side="bottom", pady=(10, 0))
        self.botao_gerar = ttk.Button(botoes, text="Gerar PL", style="Primario.TButton",
                                      command=self._gerar)
        self.botao_gerar.pack(side="right")
        ttk.Button(botoes, text="Cancelar", command=self._cancelar).pack(side="right", padx=(0, 8))

        self._atualizar_miniaturas()

    # Ctrl+V: se a área de transferência tiver imagem, anexa a imagem;
    # se tiver texto, deixa o Tkinter colar normalmente.
    def _ao_colar(self, _evento):
        if self._anexar_da_area_de_transferencia():
            return "break"
        return None

    # Botão "Colar imagem".
    def _colar_imagem(self):
        if not self._anexar_da_area_de_transferencia():
            self._informar("Não há imagem na área de transferência. Copie o print da questão "
                           "ou use 'Escolher imagem...'.", erro=True)

    # Lê a área de transferência. Pode vir uma imagem (print) ou uma lista de
    # arquivos (quando o arquivo foi copiado no gerenciador de arquivos).
    def _anexar_da_area_de_transferencia(self):
        try:
            conteudo = ImageGrab.grabclipboard()
        except Exception:
            return False

        if isinstance(conteudo, Image.Image):
            caminho = self._pasta / f"imagem_{len(self._imagens) + 1}.png"
            conteudo.save(caminho)
            self._adicionar_imagem(caminho)
            return True
        if isinstance(conteudo, list):
            arquivos = [Path(c) for c in conteudo if Path(c).suffix.lower() in EXTENSOES_IMAGEM]
            for arquivo in arquivos:
                self._adicionar_imagem(arquivo)
            return bool(arquivos)
        return False

    # Botão "Escolher imagem...".
    def _escolher_imagem(self):
        caminhos = filedialog.askopenfilenames(parent=self, title="Escolher imagem do enunciado",
                                               filetypes=TIPOS_IMAGEM)
        for caminho in caminhos:
            self._adicionar_imagem(Path(caminho))

    def _adicionar_imagem(self, caminho):
        self._imagens.append(caminho)
        self._atualizar_miniaturas()
        self._informar(f"Imagem anexada: {caminho.name}")

    def _remover_imagens(self):
        self._imagens.clear()
        self._atualizar_miniaturas()
        self._informar("")

    # Mostra uma miniatura de cada imagem anexada.
    def _atualizar_miniaturas(self):
        for filho in self.area_miniaturas.winfo_children():
            filho.destroy()
        self._miniaturas.clear()

        for caminho in self._imagens:
            try:
                with Image.open(caminho) as imagem:
                    imagem.thumbnail(TAMANHO_MINIATURA)
                    miniatura = ImageTk.PhotoImage(imagem, master=self)
            except OSError:
                ttk.Label(self.area_miniaturas, text=caminho.name).pack(side="left", padx=(0, 8))
                continue
            self._miniaturas.append(miniatura)
            tk.Label(self.area_miniaturas, image=miniatura, relief="solid", borderwidth=1,
                     bg=CORES["painel"]).pack(side="left", padx=(0, 8))

        self.botao_remover.configure(state="normal" if self._imagens else "disabled")

    # Botão "Gerar PL": chama o Codex em outra thread.
    def _gerar(self):
        texto = self.texto.get("1.0", "end").strip()
        if not texto and not self._imagens:
            self._informar("Cole o texto do enunciado ou uma imagem antes de gerar.", erro=True)
            return

        self._gerando = True
        self.botao_gerar.configure(state="disabled")
        self.progresso.pack(fill="x", pady=(8, 0), before=self.status)
        self.progresso.start(12)
        self._informar("Gerando o PL com o Codex... isso pode levar alguns segundos.")

        imagens = list(self._imagens)
        threading.Thread(target=self._chamar_ia, args=(texto, imagens), daemon=True).start()
        self.after(200, self._verificar_resposta)

    # Executa na thread secundária: não mexe na tela, só coloca o resultado na fila.
    def _chamar_ia(self, texto, imagens):
        try:
            resultado = gerar_pl(texto, imagens, processo_iniciado=self._guardar_processo)
            self._fila.put(("ok", resultado))
        except ErroIA as erro:
            self._fila.put(("erro", str(erro)))
        except Exception as erro:
            self._fila.put(("erro", f"Erro inesperado: {erro}"))

    def _guardar_processo(self, processo):
        self._processo = processo

    # Confere de tempos em tempos se a thread terminou.
    def _verificar_resposta(self):
        if not self._gerando:
            return
        try:
            tipo, valor = self._fila.get_nowait()
        except queue.Empty:
            self.after(200, self._verificar_resposta)
            return

        self._gerando = False
        self.progresso.stop()
        self.progresso.pack_forget()
        self.botao_gerar.configure(state="normal")

        if tipo == "erro":
            self._informar(valor, erro=True)
            return
        self._ao_gerar(valor)
        self._fechar()

    def _informar(self, mensagem, erro=False):
        self.status.configure(text=mensagem,
                              foreground=CORES["erro"] if erro else CORES["texto_suave"])

    # Fecha a janela; se o Codex ainda estiver rodando, encerra o processo.
    def _cancelar(self):
        if self._gerando and self._processo is not None and self._processo.poll() is None:
            self._processo.kill()
        self._gerando = False
        self._fechar()

    def _fechar(self):
        self.grab_release()
        self.destroy()
        shutil.rmtree(self._pasta, ignore_errors=True)
