import os
import json
try:
    # prefer PyQt file dialog if available for GUI flows
    from PyQt6.QtWidgets import QFileDialog, QApplication
    _HAS_QT = True
except Exception:
    _HAS_QT = False

_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '.current_project')


def _read_stored():
    if not os.path.exists(_CONFIG_FILE):
        return None
    try:
        with open(_CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('project_file')
    except Exception:
        return None


def _write_stored(path: str):
    try:
        with open(_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'project_file': path}, f)
    except Exception:
        pass


def get_project_file(prompt_if_missing: bool = True) -> str | None:
    """Return stored project file path, prompting the user if missing and allowed.

    If Qt is not available and no stored path exists, returns None.
    """
    path = _read_stored()
    if path and os.path.exists(path):
        return path
    if not prompt_if_missing:
        return path
    # prompt using QFileDialog when Qt available
    if _HAS_QT:
        app = None
        try:
            app = QApplication.instance() or QApplication([])
        except Exception:
            app = None
        fname, _ = QFileDialog.getOpenFileName(None, 'Selecione o arquivo do projeto (teste.json)', os.getcwd(), 'JSON Files (*.json);;All Files (*)')
        if fname:
            _write_stored(fname)
            return fname
    return None


def set_project_file(path: str):
    _write_stored(path)
