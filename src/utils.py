import sys
import os


def resource_path(relative_path):
    """
    Retorna o caminho absoluto para recursos,
    considerando PyInstaller ou execução normal.
    """
    try:
        base_path = sys._MEIPASS  # type: ignore
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


