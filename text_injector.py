"""Injection du texte transcrit à la position du curseur"""
import pyperclip
import keyboard
import time


class TextInjector:
    @staticmethod
    def inject(text: str):
        """
        Injecte le texte à la position du curseur
        via clipboard + Ctrl+V simulé
        """
        if not text:
            return
        
        # Sauvegarde du clipboard actuel
        original_clipboard = ""
        try:
            original_clipboard = pyperclip.paste()
        except:
            pass
        
        # Copie du nouveau texte
        pyperclip.copy(text)
        
        # Petite pause pour s'assurer que le clipboard est à jour
        time.sleep(0.05)
        
        # Simulation de Ctrl+V
        keyboard.press_and_release('ctrl+v')
        
        # Attente puis restauration du clipboard original
        time.sleep(0.1)
        try:
            pyperclip.copy(original_clipboard)
        except:
            pass
