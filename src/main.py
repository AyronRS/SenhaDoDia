import tkinter as tk
from tkinter import messagebox
import threading
import pyperclip

# Módulos internos
from src import file_manager, email_services, shortcuts, themes, sound

CURRENT_VERSION = "v4.0.5"

senha_capturada = None
tema_escuro = False

# --- ESTILO ---
BG_COLOR = "#f4f6f8"
CARD_COLOR = "#ffffff"
TEXT_COLOR = "#111827"
MUTED = "#6b7280"
SUCCESS = "#16a34a"

DARK_DEFAULT = "#3f3f3f"  # cor padrão de botões no modo escuro

PALETAS = {
    "Roxo": "#4f46e5",
    "Azul": "#2563eb",
    "Vermelho": "#FF0000",
    "Verde": "#16a34a",
    "Laranja": "#f97316",
    "Rosa": "#db2777",
}

PRIMARY_LIGHT = PALETAS["Roxo"]   # cor do modo claro (persistente)
PRIMARY_DARK = DARK_DEFAULT       # cor do modo escuro (por regra começa no padrão)
PRIMARY = PRIMARY_LIGHT           # cor atual usada nos botões principais
LAST_LIGHT_COLOR = PRIMARY_LIGHT

FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_SUB = ("Segoe UI", 10, "bold")
FONT_TEXT = ("Segoe UI", 9)
FONT_SMALL = ("Segoe UI", 8)
FONT_ICON = ("Segoe UI", 13)

PAD_Y = 2

# Update
import update
update.check_for_update(CURRENT_VERSION)


def ui(callable_):
    """Executa algo com segurança no thread do Tk."""
    janela.after(0, callable_)


def run_bg(task_fn):
    """Executa uma função em background."""
    threading.Thread(target=task_fn, daemon=True).start()


def salvar_dados(usuario, senha, ultima_senha=None):
    # salva também o tema e as cores do claro/escuro
    file_manager.salvar_dados(
        usuario,
        senha,
        ultima_senha,
        tema_escuro,
        PRIMARY_LIGHT,
        PRIMARY_DARK
    )


def carregar_dados():
    return file_manager.carregar_dados()


def atualizar_botao_tema(tema_escuro_local: bool):
    # sem espaços no texto (alinha melhor em diferentes PCs)
    if tema_escuro_local:
        btn_tema.config(text="     ☀️", padx=6, pady=1)
    else:
        btn_tema.config(text="🌙", padx=6, pady=1)


def set_loading(
    button: tk.Button,
    loading: bool,
    text_loading: str = "Buscando...",
    text_normal: str | None = None
):
    if loading:
        button.config(text=text_loading, state="disabled")
    else:
        if text_normal is not None:
            button.config(text=text_normal)
        button.config(state="normal")


def capturar_senha():
    global senha_capturada
    usuario = entry_usuario.get().strip()
    senha = entry_senha.get().strip()

    if not usuario or not senha:
        messagebox.showwarning("Aviso", "Preencha e-mail e senha do app.")
        return

    def tarefa():
        ui(lambda: set_loading(btn_capturar, True, "Buscando...", "Buscar Senha do Dia"))

        senha_res, erro = email_services.buscar_senha_gmail(usuario, senha)

        def finish():
            set_loading(btn_capturar, False, text_normal="Buscar Senha do Dia")

            if erro:
                messagebox.showwarning("Aviso", erro)
                return
            if not senha_res:
                messagebox.showwarning("Aviso", "Senha não encontrada.")
                return

            global senha_capturada
            senha_capturada = senha_res
            lbl_senha_capturada.config(text=f"Senha Capturada: {senha_capturada}")
            messagebox.showinfo("Sucesso", f"Senha capturada: {senha_capturada}")
            salvar_dados(usuario, senha, senha_capturada)

        ui(finish)

    run_bg(tarefa)


def atualizar_atalho():
    if not senha_capturada:
        messagebox.showwarning("Aviso", "Nenhuma senha capturada.")
        return

    shortcuts.modificar_atalhos(
        senha_capturada,
        ["VetorFarma.lnk", "VetorFiscal.lnk"]
    )


def copiar_para_clipboard():
    if not senha_capturada:
        messagebox.showwarning("Aviso", "Nenhuma senha capturada.")
        return

    pyperclip.copy(senha_capturada)

    notificacao = tk.Toplevel(janela)
    notificacao.overrideredirect(True)
    notificacao.configure(bg=PRIMARY)

    x = janela.winfo_rootx() + 80
    y = janela.winfo_rooty() + 380
    notificacao.geometry(f"170x35+{x}+{y}")

    tk.Label(
        notificacao,
        text="Senha copiada!",
        bg=PRIMARY,
        fg="white",
        font=FONT_TEXT
    ).pack(fill="both", expand=True)

    janela.after(1500, notificacao.destroy)


def toggle_senha_capturada():
    if lbl_senha_capturada.winfo_ismapped():
        lbl_senha_capturada.grid_remove()
        btn_toggle.config(text="Mostrar Senha")
    else:
        lbl_senha_capturada.grid()
        btn_toggle.config(text="Ocultar Senha")


def _reaplicar_cor_botoes_principais():
    for btn in [
        btn_capturar_token,
        btn_capturar_token_fiserv,
        btn_capturar,
        btn_toggle,
        btn_atualizar,
        btn_copiar
    ]:
        btn.config(bg=PRIMARY, activebackground=PRIMARY)


def aplicar_cor_app(nova_cor: str):
    """
    - Se estiver no claro: altera PRIMARY_LIGHT e aplica.
    - Se estiver no escuro: altera PRIMARY_DARK e aplica.
    - Sempre salva.
    """
    global PRIMARY, PRIMARY_LIGHT, PRIMARY_DARK,LAST_LIGHT_COLOR

    PRIMARY = nova_cor
    if tema_escuro:
        PRIMARY_DARK = nova_cor
    else:
        PRIMARY_LIGHT = nova_cor
        LAST_LIGHT_COLOR = nova_cor

    _reaplicar_cor_botoes_principais()
    salvar_dados(entry_usuario.get().strip(), entry_senha.get().strip(), senha_capturada)


def escolher_cor():
    popup = tk.Toplevel(janela)
    popup.title("Escolher cor")
    popup.resizable(False, False)
    popup.configure(bg=CARD_COLOR)

    popup.transient(janela)
    popup.grab_set()

    tk.Label(
        popup,
        text="Selecione uma cor:",
        bg=CARD_COLOR,
        fg=TEXT_COLOR,
        font=FONT_SUB
    ).pack(padx=12, pady=(12, 8))

    frame = tk.Frame(popup, bg=CARD_COLOR)
    frame.pack(padx=12, pady=(0, 12))

    for nome, cor in PALETAS.items():
        def on_click(c=cor):
            aplicar_cor_app(c)
            popup.destroy()

        b = tk.Button(
            frame,
            text=nome,
            command=on_click,
            bg=cor,
            fg="white",
            relief="flat",
            width=16,
            height=1,
            cursor="hand2"
        )
        b.pack(pady=4)

    # Centraliza o popup na janela
    popup.update_idletasks()
    w = popup.winfo_width()
    h = popup.winfo_height()
    x_j = janela.winfo_rootx()
    y_j = janela.winfo_rooty()
    w_j = janela.winfo_width()
    h_j = janela.winfo_height()

    x = x_j + (w_j // 2) - (w // 2)
    y = y_j + (h_j // 2) - (h // 2)

    # ajuste fino para esquerda (mude -20 conforme preferir)
    popup.geometry(f"+{x - 230}+{y}")


def alternar_tema_interface():
    global tema_escuro, PRIMARY, PRIMARY_LIGHT, PRIMARY_DARK, LAST_LIGHT_COLOR

    # guarda a cor atual do claro antes de entrar no escuro
    if not tema_escuro:
        LAST_LIGHT_COLOR = PRIMARY_LIGHT

    novo_tema = themes.alternar_tema(
        janela, container, card,
        labels, entries, botoes,
        tema_escuro
    )

    if novo_tema:  # indo para escuro
        sound.tocar_som_tema_escuro_async()

        # sempre começa o escuro com o padrão
        PRIMARY_DARK = DARK_DEFAULT
        PRIMARY = PRIMARY_DARK

    else:  # indo para claro
        sound.tocar_som_tema_claro_async()

        # ✅ se o escuro foi customizado, herda
        if (PRIMARY_DARK or "").strip().lower() != DARK_DEFAULT.lower():
            PRIMARY_LIGHT = PRIMARY_DARK
        else:
            # ✅ se não customizou no escuro, volta exatamente ao que era no claro
            PRIMARY_LIGHT = LAST_LIGHT_COLOR

        PRIMARY = PRIMARY_LIGHT

    tema_escuro = novo_tema
    atualizar_botao_tema(tema_escuro)

    _reaplicar_cor_botoes_principais()

    salvar_dados(entry_usuario.get().strip(), entry_senha.get().strip(), senha_capturada)



def capturar_token_getcard():
    usuario = entry_usuario.get().strip()
    senha = entry_senha.get().strip()

    if not usuario or not senha:
        messagebox.showwarning("Aviso", "Preencha e-mail e senha do app.")
        return

    def tarefa():
        ui(lambda: set_loading(btn_capturar_token, True, "Buscando...", "Buscar Token GetCard"))

        try:
            token, erro = email_services.buscar_token_getcard(usuario, senha)
        except Exception as e:
            token, erro = None, f"Erro inesperado: {e}"

        def finish():
            set_loading(btn_capturar_token, False, text_normal="Buscar Token GetCard")

            if erro:
                messagebox.showwarning("Token não encontrado", erro)
                return

            pyperclip.copy(token)
            messagebox.showinfo(
                "Token Capturado",
                f"{'✅ Token capturado e copiado para a área de transferência:':^50}\n\n"
                f"{'* ' + token + ' *':^50}\n\n"
            )

        ui(finish)

    run_bg(tarefa)


def capturar_token_fiserv():
    usuario = entry_usuario.get().strip()
    senha = entry_senha.get().strip()

    if not usuario or not senha:
        messagebox.showwarning("Aviso", "Preencha e-mail e senha do app.")
        return

    def tarefa():
        ui(lambda: set_loading(btn_capturar_token_fiserv, True, "Buscando...", "Buscar Token Fiserv"))

        try:
            token, erro = email_services.buscar_token_fiserv(usuario, senha)
        except Exception as e:
            token, erro = None, f"Erro inesperado: {e}"

        def finish():
            set_loading(btn_capturar_token_fiserv, False, text_normal="Buscar Token Fiserv")

            if erro:
                messagebox.showwarning("Token não encontrado", erro)
                return

            pyperclip.copy(token)
            messagebox.showinfo(
                "Token Capturado",
                f"{'✅ Token Fiserv capturado e copiado para a área de transferência:':^50}\n\n"
                f"{'* ' + token + ' *':^50}\n\n"
            )

        ui(finish)

    run_bg(tarefa)


# --- JANELA ---
janela = tk.Tk()
janela.title("Gestão de Senha")
janela.configure(bg=BG_COLOR)

largura, altura = 340, 580
x = (janela.winfo_screenwidth() // 2) - (largura // 2)
y = (janela.winfo_screenheight() // 2) - (altura // 2)
janela.geometry(f"{largura}x{altura}+{x}+{y}")
janela.resizable(False, False)

container = tk.Frame(janela, bg=BG_COLOR)
container.pack(fill="both", expand=True)

card = tk.Frame(
    container,
    bg=CARD_COLOR,
    padx=20,
    pady=15,
    bd=1,
    relief="solid"
)
card.pack(padx=15, pady=15, fill="both", expand=True)

card.grid_columnconfigure(0, weight=1)
card.grid_columnconfigure(1, weight=1)

lbl_titulo = tk.Label(card, text="Gestão de Senha", font=FONT_TITLE, bg=CARD_COLOR, fg=TEXT_COLOR)
lbl_titulo.grid(row=0, column=0, columnspan=2, pady=(0, 10))

btn_tema = tk.Button(
    card,
    text="🌙",
    command=alternar_tema_interface,
    relief="flat",
    font=("Segoe UI Symbol", 12),
    bg=CARD_COLOR,
    width=1,
    height=1,
    padx=3,
    pady=1,
    anchor="center",
    cursor="hand2",
    activebackground=CARD_COLOR,
    highlightthickness=0,
    bd=0
)
btn_tema.place(x=-6, y=-6)

btn_cores = tk.Button(
    card,
    text="🎨",
    command=escolher_cor,
    relief="flat",
    font=("Segoe UI Symbol", 12),
    bg=CARD_COLOR,
    width=1,
    height=1,
    padx=3,
    pady=1,
    anchor="center",
    cursor="hand2",
    activebackground=CARD_COLOR,
    highlightthickness=0,
    bd=0
)
btn_cores.place(x=22, y=-6)

lbl_usuario = tk.Label(card, text="E-mail", bg=CARD_COLOR, fg=MUTED, font=FONT_TEXT)
lbl_usuario.grid(row=1, column=0, columnspan=2, pady=(2, 0))

entry_usuario = tk.Entry(card, font=FONT_TEXT, width=28)
entry_usuario.grid(row=2, column=0, columnspan=2, pady=PAD_Y, padx=10)

lbl_senha = tk.Label(card, text="Senha do App", bg=CARD_COLOR, fg=MUTED, font=FONT_TEXT)
lbl_senha.grid(row=3, column=0, columnspan=2, pady=(5, 0))

entry_senha = tk.Entry(card, show="*", font=FONT_TEXT, width=28)
entry_senha.grid(row=4, column=0, columnspan=2, pady=PAD_Y, padx=10)


def criar_botao(texto, comando, linha):
    b = tk.Button(
        card,
        text=texto,
        command=comando,
        bg=PRIMARY,
        fg="white",
        relief="flat",
        height=2,
        cursor="hand2",
        width=28
    )
    b.grid(row=linha, column=0, columnspan=2, pady=3)
    return b


btn_capturar_token = criar_botao("Buscar Token GetCard", capturar_token_getcard, 5)
btn_capturar_token_fiserv = criar_botao("Buscar Token Fiserv", capturar_token_fiserv, 6)
btn_capturar = criar_botao("Buscar Senha do Dia", capturar_senha, 7)
btn_toggle = criar_botao("Ocultar Senha", toggle_senha_capturada, 8)
btn_atualizar = criar_botao("Atualizar Atalho", atualizar_atalho, 9)
btn_copiar = criar_botao("Copiar Senha", copiar_para_clipboard, 10)

lbl_senha_capturada = tk.Label(
    card,
    text="Senha Capturada: Nenhuma",
    fg=SUCCESS,
    bg=CARD_COLOR,
    font=FONT_SUB
)
lbl_senha_capturada.grid(row=11, column=0, columnspan=2, pady=5)

lbl_version = tk.Label(
    card,
    text=f"Versão {CURRENT_VERSION} - Áyron.ZettiTech",
    bg=CARD_COLOR,
    fg=MUTED,
    font=FONT_SMALL
)
lbl_version.grid(row=12, column=0, columnspan=2, pady=(2, 0))

labels = [lbl_titulo, lbl_usuario, lbl_senha, lbl_senha_capturada, lbl_version]
entries = [entry_usuario, entry_senha]
botoes = [
    btn_capturar_token, btn_capturar_token_fiserv, btn_capturar,
    btn_atualizar, btn_copiar, btn_toggle, btn_tema, btn_cores
]

# --- CARREGAR DADOS (1x só) ---
usuario_salvo, senha_salva, ultima_senha, tema_salvo, primary_light_salvo, primary_dark_salvo = carregar_dados()

if usuario_salvo:
    entry_usuario.insert(0, usuario_salvo)

if senha_salva:
    entry_senha.insert(0, senha_salva)

if ultima_senha:
    senha_capturada = ultima_senha
    lbl_senha_capturada.config(text=f"Senha Capturada: {ultima_senha}")

# restaura cores salvas (se existirem)
if primary_light_salvo:
    PRIMARY_LIGHT = primary_light_salvo

if primary_dark_salvo:
    PRIMARY_DARK = primary_dark_salvo

# aplica tema salvo
tema_escuro = bool(tema_salvo)
themes.aplicar_tema(janela, container, card, labels, entries, botoes, tema_escuro)

# escolhe PRIMARY correto conforme tema inicial
PRIMARY = PRIMARY_DARK if tema_escuro else PRIMARY_LIGHT

# reaplica cor nos botões principais
_reaplicar_cor_botoes_principais()
atualizar_botao_tema(tema_escuro)

janela.mainloop()
