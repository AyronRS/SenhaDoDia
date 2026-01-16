import os
from cryptography.fernet import Fernet
from tkinter import messagebox

APP_NAME = "SenhaDoDia"
APPDATA = os.getenv("APPDATA") or os.path.expanduser("~")
BASE_DIR = os.path.join(APPDATA, APP_NAME)

CHAVE_PATH = os.path.join(BASE_DIR, "chave.key")
DADOS_PATH = os.path.join(BASE_DIR, "dados_usuario.dat")

# Caminhos antigos (migração)
PASTA_ANTIGA_ROOT = "C:\\"
CHAVE_ANTIGA = os.path.join(PASTA_ANTIGA_ROOT, "chave.key")
DADOS_ANTIGO = os.path.join(PASTA_ANTIGA_ROOT, "dados_usuario.txt")

PASTA_ANTIGA_2 = "C:\\App Senha"
CHAVE_ANTIGA_2 = os.path.join(PASTA_ANTIGA_2, "chave.key")
DADOS_ANTIGO_2 = os.path.join(PASTA_ANTIGA_2, "dados_usuario.txt")


def _ensure_dir():
    os.makedirs(BASE_DIR, exist_ok=True)


def _migrar_se_existir():
    """
    Migra arquivos antigos para o novo local do AppData.
    """
    _ensure_dir()

    candidatos = [
        (CHAVE_ANTIGA, DADOS_ANTIGO),
        (CHAVE_ANTIGA_2, DADOS_ANTIGO_2),
    ]

    # Se já existe no novo local, não mexe
    if os.path.exists(CHAVE_PATH) and os.path.exists(DADOS_PATH):
        return

    for chave_old, dados_old in candidatos:
        try:
            if os.path.exists(chave_old) and not os.path.exists(CHAVE_PATH):
                os.replace(chave_old, CHAVE_PATH)
            if os.path.exists(dados_old) and not os.path.exists(DADOS_PATH):
                os.replace(dados_old, DADOS_PATH)
        except Exception:
            # Se falhar, não bloqueia o app
            pass


def _get_fernet() -> Fernet:
    _migrar_se_existir()
    _ensure_dir()

    if not os.path.exists(CHAVE_PATH):
        with open(CHAVE_PATH, "wb") as f:
            f.write(Fernet.generate_key())

    with open(CHAVE_PATH, "rb") as f:
        chave = f.read()

    return Fernet(chave)


def salvar_dados(
    usuario: str,
    senha: str,
    ultima_senha_capturada: str | None = None,
    tema_escuro: bool = False
):
    """
    Formato (linhas):
    1) usuario
    2) senha
    3) ultima_senha
    4) tema_escuro (1/0)  <-- novo
    """
    try:
        fernet = _get_fernet()

        ultima = ultima_senha_capturada or ""
        tema = "1" if tema_escuro else "0"

        dados = f"{usuario}\n{senha}\n{ultima}\n{tema}"
        cript = fernet.encrypt(dados.encode("utf-8"))

        with open(DADOS_PATH, "wb") as f:
            f.write(cript)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar os dados: {e}")


def carregar_dados():
    """
    Retorna: (usuario, senha, ultima_senha, tema_escuro)
    Compatível com versões antigas (sem a 4ª linha).
    """
    try:
        fernet = _get_fernet()
        if not os.path.exists(DADOS_PATH):
            return None, None, None, False

        with open(DADOS_PATH, "rb") as f:
            cript = f.read()

        dados = fernet.decrypt(cript).decode("utf-8", errors="replace")
        linhas = dados.split("\n")

        usuario = (linhas[0].strip() if len(linhas) > 0 else None) or None
        senha = (linhas[1].strip() if len(linhas) > 1 else None) or None
        ultima = (linhas[2].strip() if len(linhas) > 2 else None) or None

        tema_escuro = False
        if len(linhas) > 3:
            tema_escuro = linhas[3].strip() == "1"

        return usuario, senha, ultima, tema_escuro
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar os dados: {e}")
        return None, None, None, False
