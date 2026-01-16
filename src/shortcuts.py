import os
from tkinter import messagebox
import win32com.client


def _desktop_paths() -> list[str]:
    user = os.path.expanduser("~")
    paths = [
        os.path.join(user, "Desktop"),
        os.path.join(user, "OneDrive", "Desktop"),
    ]
    return [p for p in paths if os.path.isdir(p)]


def _find_shortcut(nome_atalho: str) -> str | None:
    for d in _desktop_paths():
        p = os.path.join(d, nome_atalho)
        if os.path.exists(p):
            return p
    return None


def _set_shortcut_args(caminho_atalho: str, args: str) -> None:
    shell = win32com.client.Dispatch("WScript.Shell")
    sc = shell.CreateShortcut(caminho_atalho)

    if not sc.TargetPath:
        raise RuntimeError("Atalho sem destino (TargetPath).")

    sc.Arguments = args
    sc.Save()


def modificar_atalhos(senha: str, nomes_atalhos: list[str]) -> None:
    if not senha:
        messagebox.showwarning("Aviso", "Senha vazia. Capture a senha antes de atualizar.")
        return

    atualizados = []
    nao_encontrados = []

    for nome in nomes_atalhos:
        caminho = _find_shortcut(nome)
        if not caminho:
            nao_encontrados.append(nome)
            continue

        try:
            _set_shortcut_args(caminho, senha)
            atualizados.append(nome)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar '{nome}': {e}")
            return

    if atualizados and nao_encontrados:
        messagebox.showwarning(
            "Atualização parcial",
            "Atualizei:\n- " + "\n- ".join(atualizados) +
            "\n\nNão encontrei:\n- " + "\n- ".join(nao_encontrados)
        )
        return

    if atualizados:
        messagebox.showinfo(
            "Sucesso",
            "Senha aplicada nos atalhos:\n- " + "\n- ".join(atualizados)
        )
        return

    messagebox.showerror(
        "Erro",
        "Não encontrei nenhum dos atalhos informados no Desktop (local/OneDrive)."
    )
