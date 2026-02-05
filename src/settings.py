"""Gestion des parametres persistants"""
import json
import os
import platform
from pathlib import Path
from src import config


def get_settings_dir() -> Path:
    """Retourne le dossier de configuration selon la plateforme"""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:  # Linux
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))

    settings_dir = Path(base) / "OpenWhisper"
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir


class Settings:
    """Gestionnaire de parametres avec persistence JSON"""

    DEFAULTS = {
        "whisper_model": config.WHISPER_MODEL,
        "language": config.LANGUAGE,
        "device": config.DEVICE,
        "compute_type": config.COMPUTE_TYPE,
        "hotkey": config.HOTKEY,
        "overlay_position": None,  # (x, y) ou None pour auto
    }

    def __init__(self):
        self._settings_path = get_settings_dir() / "settings.json"
        self._settings = {}
        self.load()

    def load(self) -> None:
        """Charge les parametres depuis le fichier JSON"""
        self._settings = self.DEFAULTS.copy()

        if self._settings_path.exists():
            try:
                with open(self._settings_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    # Merge avec les defaults (pour nouvelles options)
                    for key, value in saved.items():
                        if key in self.DEFAULTS:
                            self._settings[key] = value
                print(f"[Settings] Charge depuis: {self._settings_path}")
            except Exception as e:
                print(f"[Settings] Erreur chargement: {e}")

    def save(self) -> None:
        """Sauvegarde les parametres dans le fichier JSON"""
        try:
            with open(self._settings_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            print(f"[Settings] Sauvegarde dans: {self._settings_path}")
        except Exception as e:
            print(f"[Settings] Erreur sauvegarde: {e}")

    def get(self, key: str, default=None):
        """Recupere une valeur"""
        return self._settings.get(key, default)

    def set(self, key: str, value) -> None:
        """Definit une valeur (ne sauvegarde pas automatiquement)"""
        self._settings[key] = value

    def get_all(self) -> dict:
        """Retourne une copie de tous les parametres"""
        return self._settings.copy()

    # Proprietes pour acces direct
    @property
    def whisper_model(self) -> str:
        return self._settings["whisper_model"]

    @property
    def language(self) -> str:
        return self._settings["language"]

    @property
    def device(self) -> str:
        return self._settings["device"]

    @property
    def compute_type(self) -> str:
        return self._settings["compute_type"]

    @property
    def hotkey(self) -> str:
        return self._settings["hotkey"]

    @property
    def overlay_position(self):
        return self._settings["overlay_position"]
