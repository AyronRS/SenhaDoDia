import requests
import os
import sys
import re
from tkinter import messagebox
import subprocess


def get_latest_release():
    repo_url = "https://api.github.com/repos/AyronGPT/SenhaDoDia_4.0/releases/latest"
    try:
        response = requests.get(repo_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao verificar atualizações: {e}")
        return None


def version_to_tuple(version):
    match = re.match(r"v(\d+)\.(\d+)\.(\d+)", version)
    return tuple(map(int, match.groups())) if match else (0, 0, 0)


def download_file(asset_url, dest_path):
    try:
        response = requests.get(asset_url, stream=True, timeout=30)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Erro ao baixar: {e}")
        return False


def check_for_update(current_version):
    current_exe_name = "SenhaDoDia_4.0.exe"
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", current_exe_name)

    release_info = get_latest_release()
    if not release_info:
        return

    latest_version = release_info.get("tag_name", "v0.0.0")
    if version_to_tuple(latest_version) <= version_to_tuple(current_version):
        return

    assets = release_info.get("assets", [])
    for asset in assets:
        if asset.get("name") == current_exe_name:
            if messagebox.askyesno("Atualização", f"Nova versão {latest_version} disponível. Baixar?"):
                ok = download_file(asset.get("browser_download_url", ""), downloads_path)
                if ok:
                    messagebox.showinfo("Sucesso", "Download concluído na pasta Downloads.")
                    subprocess.Popen(f'explorer /select,"{downloads_path}"')
                    sys.exit(0)
            return
