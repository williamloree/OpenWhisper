"""Indicateurs sonores pour OpenWhisper"""
import winsound
import threading
import sys
import os


def _get_sound_path(filename):
    """Retourne le chemin du fichier son"""
    if getattr(sys, 'frozen', False):
        # Mode exe: fichier dans le dossier temporaire PyInstaller
        return os.path.join(sys._MEIPASS, filename)
    else:
        # Mode dev: fichier a la racine du projet
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)


def play_start_recording():
    """Son de debut d'enregistrement"""
    def _play():
        path = _get_sound_path("open.wav")
        if os.path.exists(path):
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    threading.Thread(target=_play, daemon=True).start()


def play_start_transcription():
    """Son de debut de transcription"""
    def _play():
        path = _get_sound_path("open.wav")
        if os.path.exists(path):
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    threading.Thread(target=_play, daemon=True).start()


def play_done():
    """Son de fin (desactive)"""
    pass
