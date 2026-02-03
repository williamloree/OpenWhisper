"""Injection du texte transcrit a la position du curseur (cross-platform)"""
import pyperclip
import keyboard
import time
import platform


class TextInjector:
    @staticmethod
    def inject(text: str):
        """
        Injecte le texte a la position du curseur
        via clipboard + Ctrl+V (ou Cmd+V sur macOS)
        """
        if not text:
            return

        # Sauvegarde du clipboard actuel
        original_clipboard = ""
        try:
            original_clipboard = pyperclip.paste()
        except Exception:
            pass

        # Copie du nouveau texte
        pyperclip.copy(text)

        # Petite pause pour s'assurer que le clipboard est a jour
        time.sleep(0.05)

        # Simulation de Ctrl+V (ou Cmd+V sur macOS)
        if platform.system() == 'Darwin':
            keyboard.press_and_release('command+v')
        else:
            keyboard.press_and_release('ctrl+v')

        # Attente puis restauration du clipboard original
        time.sleep(0.1)
        try:
            pyperclip.copy(original_clipboard)
        except Exception:
            pass
