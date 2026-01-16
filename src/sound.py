import winsound
import threading
import os
from src.utils import resource_path


def _tocar_som_async(nome_arquivo):
    som_path = resource_path(os.path.join("assets", nome_arquivo))
    if not os.path.exists(som_path):
        print(f"Som não encontrado: {som_path}")
        return

    threading.Thread(
        target=lambda: winsound.PlaySound(
            som_path,
            winsound.SND_FILENAME | winsound.SND_ASYNC
        ),
        daemon=True
    ).start()


def tocar_som_tema_claro_async():
    _tocar_som_async("track.wav")


def tocar_som_tema_escuro_async():
    _tocar_som_async("track.wav")
